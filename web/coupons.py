"""券码校验与消费逻辑，依赖 MySQL 存储。

表结构见 docs/coupons.sql。
"""

from __future__ import annotations

import os
import re
import logging
from datetime import datetime, timezone
from typing import Dict

import pymysql

logger = logging.getLogger(__name__)


class CouponError(Exception):
    """券码校验或状态错误。"""


class CouponConfigError(CouponError):
    """数据库配置错误。"""


def _db_config() -> Dict[str, str]:
    host = os.environ.get("MYSQL_HOST")
    user = os.environ.get("MYSQL_USER")
    password = os.environ.get("MYSQL_PASSWORD")
    database = os.environ.get("MYSQL_DB")
    port = int(os.environ.get("MYSQL_PORT", 3306))
    table = os.environ.get("COUPON_TABLE", "ai_coupons")

    if not all([host, user, password, database]):
        raise CouponConfigError("缺少 MYSQL_HOST/MYSQL_USER/MYSQL_PASSWORD/MYSQL_DB 环境变量")

    if not re.match(r"^[A-Za-z0-9_]+$", table):
        raise CouponConfigError("券码表名仅支持字母、数字和下划线")

    return {
        "host": host,
        "user": user,
        "password": password,
        "database": database,
        "port": port,
        "table": table,
    }


def _connect():
    cfg = _db_config()
    return pymysql.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        port=cfg["port"],
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=int(os.environ.get("MYSQL_CONNECT_TIMEOUT", 5)),
        read_timeout=int(os.environ.get("MYSQL_READ_TIMEOUT", 10)),
        write_timeout=int(os.environ.get("MYSQL_WRITE_TIMEOUT", 10)),
    )


def _table_name() -> str:
    return _db_config()["table"]


def _utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def consume_coupon(code: str) -> Dict:
    """校验并消费一次券码使用次数。

    返回券码行的关键字段，失败抛出 CouponError。
    """
    code = (code or "").strip()
    if not code:
        raise CouponError("请提供券码")

    table = _table_name()
    now = _utc_now()

    with _connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT id, code, status, usage_limit, usage_count, expires_at
                FROM {table}
                WHERE code=%s
                """,
                (code,),
            )
            row = cursor.fetchone()

            if not row:
                raise CouponError("券码不存在")
            if row["status"] != "active":
                raise CouponError("券码已停用")
            if row["expires_at"] and row["expires_at"] <= now:
                raise CouponError("券码已过期")
            if row["usage_count"] >= row["usage_limit"]:
                raise CouponError("券码已用完")

            cursor.execute(
                f"""
                UPDATE {table}
                SET usage_count = usage_count + 1,
                    last_used_at = %s,
                    updated_at = %s
                WHERE id = %s
                  AND usage_count < usage_limit
                """,
                (now, now, row["id"]),
            )

            if cursor.rowcount == 0:
                raise CouponError("券码已用完")

            row["usage_count"] += 1
            row["last_used_at"] = now
            return row


def refund_coupon_usage(coupon_id: int):
    """在后续流程失败时回滚一次使用（尽力而为）。"""
    if not coupon_id:
        return

    table = _table_name()
    now = _utc_now()

    try:
        with _connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE {table}
                    SET usage_count = GREATEST(usage_count - 1, 0),
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (now, coupon_id),
                )
    except Exception as exc:  # noqa: BLE001
        logger.error("券码回滚失败: %s", exc)
