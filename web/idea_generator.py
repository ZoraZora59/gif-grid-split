"""将用户创意转为精灵表生成计划的服务。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .genai_client import DEFAULT_MODEL, generate_text

PLAN_PROMPT_TEMPLATE = """
你是像素风游戏美术顾问，请把玩家的创意转换为**生成精灵表**的结构化计划。
请严格输出 JSON，字段含义如下：
{
  "title": "一句话概括角色/场景",
  "image_prompt": "可直接投喂文生图/图生图的英文提示词，包含角色、动作、一致的视角、背景纯色或透明",
  "grid": {"rows": 4, "cols": 4, "cell_size": 256},
  "actions": ["待机", "走路", "攻击"],
  "style_notes": "像素风/赛博/魔法等风格强调",
  "constraints": "需要保持帧间一致、背景纯色或透明、角色居中等",
  "usage": "生成 NxN 网格后可直接送入精灵表切割逻辑生成 GIF"
}

玩家输入：{idea}
如果提供了风格偏好：{style_hint}
"""


def _extract_json_block(text: str) -> Dict[str, Any]:
    """从模型输出中提取 JSON。"""

    candidates: List[str] = []
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        candidates.append(text)

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidates.append(match.group(0))

    for item in candidates:
        try:
            return json.loads(item)
        except json.JSONDecodeError:
            continue

    raise ValueError("未能从模型输出中解析出 JSON 计划，请调整提示词后重试。")


def generate_idea_plan(
    idea: str,
    *,
    style: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.6,
) -> Dict[str, Any]:
    """调用 Gemini，将创意转换为精灵表生成计划。"""

    style_hint = style or "未指定"
    prompt = PLAN_PROMPT_TEMPLATE.format(idea=idea, style_hint=style_hint)
    response_text = generate_text(prompt, model=model or DEFAULT_MODEL, temperature=temperature)
    plan = _extract_json_block(response_text)

    plan.setdefault("title", idea.strip()[:20] or "创意计划")
    plan.setdefault("image_prompt", idea)
    plan.setdefault("grid", {"rows": 4, "cols": 4, "cell_size": 256})
    plan.setdefault("actions", [])
    plan["raw"] = response_text
    return plan
