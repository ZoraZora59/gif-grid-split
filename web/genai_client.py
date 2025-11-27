"""Gemini (ZenMux) 客户端封装，确保密钥从环境变量读取。"""
from __future__ import annotations

import json
import os
import logging
from typing import Any, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("ZENMUX_GEMINI_MODEL", "google/gemini-3-pro-image-preview")
DEFAULT_BASE_URL = os.environ.get("ZENMUX_BASE_URL", "https://zenmux.ai/api/vertex-ai")


def _build_http_options() -> object:
    """Return http_options for the GenAI client with graceful fallbacks."""
    options = {"api_version": "v1", "base_url": DEFAULT_BASE_URL}
    http_options_cls = getattr(types, "HttpOptions", None)
    if http_options_cls is None:
        logger.debug("google.genai.types.HttpOptions 不可用，使用字典形式的 http_options")
        return options

    try:
        return http_options_cls(**options)
    except Exception as exc:  # noqa: BLE001
        logger.warning("构造 HttpOptions 失败，回退为字典: %s", exc)
        return options


def _get_api_key() -> str:
    api_key = os.environ.get("ZENMUX_API_KEY")
    if not api_key:
        logger.error("未检测到 ZENMUX_API_KEY 环境变量")
        raise RuntimeError("未检测到 ZENMUX_API_KEY 环境变量，无法调用 Gemini 服务。")
    logger.info(f"API Key 已加载 (长度: {len(api_key)} 字符)")
    return api_key


def _config_to_dict(config: Any) -> Any:
    if config is None:
        return None
    if hasattr(config, "model_dump"):
        try:
            return config.model_dump()
        except Exception:  # noqa: BLE001
            pass
    if hasattr(config, "__dict__"):
        return {k: v for k, v in config.__dict__.items() if not k.startswith("_")}
    return str(config)


def _api_key_preview() -> str:
    api_key = os.environ.get("ZENMUX_API_KEY", "")
    if not api_key:
        return "<MISSING>"
    if len(api_key) <= 10:
        return "<REDACTED>"
    return f"{api_key[:6]}...{api_key[-4:]} (len={len(api_key)})"


def build_curl_preview(
    model: str,
    contents: Any,
    config: Any = None,
    *,
    config_key: str = "generation_config",
    safety_settings: Any = None,
) -> str:
    """构造一条可读的 curl 预览，便于和服务端抓包对比。"""
    endpoint = f"{DEFAULT_BASE_URL.rstrip('/')}/v1/models/{model}:generateContent"

    body: dict[str, Any] = {"contents": contents}
    config_dict = _config_to_dict(config)
    if config_dict:
        body[config_key] = config_dict
    if safety_settings:
        body["safety_settings"] = safety_settings

    body_json = json.dumps(body, ensure_ascii=False)
    return (
        "curl --location "
        f"'{endpoint}' \\\n"
        "  --header 'Content-Type: application/json' \\\n"
        f"  --header 'Authorization: Bearer {_api_key_preview()}' \\\n"
        f"  --data '{body_json}'"
    )


def create_gemini_client() -> genai.Client:
    """使用 ZenMux 代理创建 Gemini 客户端。

    - 读取 `ZENMUX_API_KEY`，避免在代码中硬编码密钥；
    - 支持通过 `ZENMUX_BASE_URL` 和 `ZENMUX_GEMINI_MODEL` 覆盖默认配置。
    """
    logger.info(f"创建 Gemini 客户端，Base URL: {DEFAULT_BASE_URL}")
    logger.info("google-genai 版本: %s", getattr(genai, "__version__", "unknown"))
    api_key = _get_api_key()

    http_options = _build_http_options()
    logger.info("http_options: %s", http_options)

    # 先通过 configure 写入 base_url，避免 Client 参数兼容性导致 base_url 丢失
    try:
        genai.configure(api_key=api_key, base_url=DEFAULT_BASE_URL, vertexai=True)
        logger.info("已通过 genai.configure 设置 base_url 和 api_key")
    except TypeError as conf_err:
        logger.warning("genai.configure 不支持 base_url/vertexai 参数: %s", conf_err)
        try:
            genai.configure(api_key=api_key)
            logger.info("已通过 genai.configure 设置 api_key（无 base_url）")
        except Exception as conf_final:  # noqa: BLE001
            logger.warning("genai.configure 设置失败: %s", conf_final)

    client_kwargs = dict(
        api_key=api_key,
        vertexai=True,
        base_url=DEFAULT_BASE_URL,  # 某些版本直接支持 base_url
        http_options=http_options,  # 兼容旧版本使用 http_options 传递 base_url
    )

    try:
        client = genai.Client(**client_kwargs)
        logger.info("Gemini 客户端创建成功")
        return client
    except TypeError as e:
        # 兼容 google-genai 较旧签名，依次尝试不同组合
        logger.warning("Client 参数不兼容，移除 base_url 重试: %s", e)
        try:
            client_kwargs.pop("base_url", None)
            client = genai.Client(**client_kwargs)
            logger.info("Gemini 客户端创建成功（兼容模式）")
            return client
        except TypeError as http_only_exc:
            logger.warning("Client 仍然不兼容 http_options，尝试仅 base_url: %s", http_only_exc)
            try:
                client = genai.Client(
                    api_key=api_key,
                    vertexai=True,
                    base_url=DEFAULT_BASE_URL,
                )
                logger.info("Gemini 客户端创建成功（base_url 兼容模式）")
                return client
            except Exception as final_exc:  # noqa: BLE001
                logger.error(f"创建 Gemini 客户端失败（仅 base_url 模式）: {final_exc}")
                raise
        except Exception as retry_exc:  # noqa: BLE001
            logger.error(f"创建 Gemini 客户端失败（兼容模式）: {retry_exc}")
            raise
    except Exception as e:
        logger.error(f"创建 Gemini 客户端失败: {str(e)}")
        raise


def generate_text(
    prompt: str,
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> str:
    """调用 Gemini 生成文本内容，返回纯文本结果。

    参数:
        prompt: 提示词文本。
        model: 覆盖默认模型名称。
        temperature: 可选，控制生成随机度。
    """

    client = create_gemini_client()
    generation_config = None
    if temperature is not None:
        generation_config = types.GenerationConfig(temperature=temperature)

    prompt_preview = prompt if len(prompt) <= 1000 else f"{prompt[:1000]}... (total {len(prompt)} chars)"
    logger.info(
        "调用 Gemini generate_content，model=%s, prompt_length=%s, preview=%s",
        model or DEFAULT_MODEL,
        len(prompt),
        prompt_preview,
    )
    if generation_config:
        logger.info("使用 generation_config: %s", generation_config)

    curl_preview = build_curl_preview(
        model=model or DEFAULT_MODEL,
        contents=prompt,
        config=generation_config,
        config_key="generation_config",
    )
    logger.info("Curl 请求预览:\n%s", curl_preview)

    response = client.models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=prompt,
        generation_config=generation_config,
    )
    return response.text
