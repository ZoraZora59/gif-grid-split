"""Gemini (ZenMux) 客户端封装，确保密钥从环境变量读取。"""
from __future__ import annotations

import os
from typing import Optional

from google import genai
from google.genai import types

DEFAULT_MODEL = os.environ.get("ZENMUX_GEMINI_MODEL", "google/gemini-3-pro-image-preview")
DEFAULT_BASE_URL = os.environ.get("ZENMUX_BASE_URL", "https://zenmux.ai/api/vertex-ai")


def _get_api_key() -> str:
    api_key = os.environ.get("ZENMUX_API_KEY")
    if not api_key:
        raise RuntimeError("未检测到 ZENMUX_API_KEY 环境变量，无法调用 Gemini 服务。")
    return api_key


def create_gemini_client() -> genai.Client:
    """使用 ZenMux 代理创建 Gemini 客户端。

    - 读取 `ZENMUX_API_KEY`，避免在代码中硬编码密钥；
    - 支持通过 `ZENMUX_BASE_URL` 和 `ZENMUX_GEMINI_MODEL` 覆盖默认配置。
    """

    api_key = _get_api_key()
    return genai.Client(
        api_key=api_key,
        vertexai=True,
        http_options=types.HttpOptions(api_version="v1", base_url=DEFAULT_BASE_URL),
    )


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

    response = client.models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=prompt,
        generation_config=generation_config,
    )
    return response.text
