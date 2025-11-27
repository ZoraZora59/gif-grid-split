"""使用 Gemini 生成精灵表图片的服务。"""
from __future__ import annotations

import base64
import os
import logging
from io import BytesIO
from typing import Optional, Tuple

from PIL import Image

from .genai_client import create_gemini_client, DEFAULT_MODEL

logger = logging.getLogger(__name__)

# 图片生成模型（支持图像输出的模型）
# 使用 google/gemini-3-pro-image-preview，它支持多模态输出包括图片
IMAGE_GEN_MODEL = os.environ.get("ZENMUX_IMAGE_MODEL", "google/gemini-3-pro-image-preview")


def generate_spritesheet(
    prompt: str,
    reference_image: Optional[bytes] = None,
    model: Optional[str] = None,
) -> Tuple[bytes, str]:
    """调用 Gemini 生成精灵表图片。

    参数:
        prompt: 生成提示词
        reference_image: 可选的参考图片（bytes 格式）
        model: 覆盖默认模型名称

    返回:
        (image_bytes, mime_type) 元组
    """
    logger.info("开始创建 Gemini 客户端...")
    client = create_gemini_client()
    use_model = model or IMAGE_GEN_MODEL
    logger.info(f"使用模型: {use_model}")

    # 构建请求内容
    contents = []
    
    if reference_image:
        logger.info("检测到参考图，正在处理...")
        # 如果有参考图，先添加参考图
        # 检测图片格式
        img = Image.open(BytesIO(reference_image))
        mime_type = f"image/{img.format.lower()}" if img.format else "image/png"
        logger.info(f"参考图格式: {mime_type}, 尺寸: {img.size}")
        
        # 将图片转为 base64
        img_base64 = base64.b64encode(reference_image).decode('utf-8')
        
        contents.append({
            "role": "user",
            "parts": [
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": img_base64
                    }
                },
                {"text": prompt}
            ]
        })
    else:
        logger.info("无参考图，仅使用文本提示词")
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

    # 配置生成参数
    from google.genai import types
    config = types.GenerateContentConfig(
        response_modalities=["image", "text"],
        temperature=0.8,
    )
    logger.info("生成配置: response_modalities=['image', 'text'], temperature=0.8")

    contents_preview = []
    for entry in contents:
        parts_preview = []
        for part in entry.get("parts", []):
            if "text" in part:
                text = part["text"]
                preview = text if len(text) <= 200 else f"{text[:200]}... (total {len(text)} chars)"
                parts_preview.append({"text_preview": preview, "text_length": len(text)})
            elif "inline_data" in part:
                inline_data = part["inline_data"]
                data = inline_data.get("data", "")
                parts_preview.append(
                    {
                        "inline_data": {
                            "mime_type": inline_data.get("mime_type"),
                            "data_length": len(data) if hasattr(data, "__len__") else "unknown",
                        }
                    }
                )
        contents_preview.append({"role": entry.get("role"), "parts": parts_preview})

    logger.info("Gemini 请求内容: model=%s, contents_preview=%s, config=%s", use_model, contents_preview, config)

    # 调用模型生成
    logger.info("正在调用 Gemini API...")
    try:
        response = client.models.generate_content(
            model=use_model,
            contents=contents,
            config=config,
        )
        logger.info("Gemini API 调用成功")
    except Exception as e:
        logger.error(f"Gemini API 调用失败: {str(e)}")
        raise

    # 检查响应
    if not response.candidates:
        logger.error("Gemini 返回空的 candidates")
        raise ValueError("模型未返回有效响应")
    
    logger.info(f"响应包含 {len(response.candidates)} 个 candidate")
    
    # 从响应中提取图片
    for i, part in enumerate(response.candidates[0].content.parts):
        logger.info(f"检查 part {i}: type={type(part).__name__}")
        if hasattr(part, 'inline_data') and part.inline_data:
            image_data = part.inline_data.data
            mime_type = part.inline_data.mime_type or "image/png"
            logger.info(f"找到图片数据，类型: {mime_type}")
            
            # 解码 base64 图片数据
            if isinstance(image_data, str):
                logger.info("图片数据是 base64 字符串，正在解码...")
                image_bytes = base64.b64decode(image_data)
            else:
                logger.info("图片数据是字节流")
                image_bytes = image_data
            
            logger.info(f"图片解码成功，大小: {len(image_bytes)} 字节")
            return image_bytes, mime_type
        elif hasattr(part, 'text') and part.text:
            logger.info(f"part {i} 是文本: {part.text[:100]}...")

    logger.error("响应中未找到图片数据")
    raise ValueError("模型未返回图片，请检查提示词或重试。")


def save_generated_image(image_bytes: bytes, output_path: str) -> str:
    """保存生成的图片到文件。

    参数:
        image_bytes: 图片字节数据
        output_path: 输出路径

    返回:
        保存的文件路径
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 使用 PIL 处理图片，确保格式正确
    img = Image.open(BytesIO(image_bytes))
    
    # 转换为 RGB（如果需要）
    if img.mode in ('RGBA', 'P'):
        # 保持透明度或转换
        pass
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 保存图片
    img.save(output_path, format='PNG')
    
    return output_path
