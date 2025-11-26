"""
GIF 合成模块
将序列帧合成为 GIF 动画
"""

import os
from PIL import Image
from typing import List, Union
from io import BytesIO


def create_gif(frames_folder: str,
               output_path: str,
               duration: int = 100) -> str:
    """
    从文件夹中的帧图片合成 GIF
    
    Args:
        frames_folder: 存放序列帧的文件夹
        output_path: 输出 GIF 的文件路径
        duration: 每帧的持续时间（毫秒）
    
    Returns:
        输出文件路径
    """
    filenames = sorted([f for f in os.listdir(frames_folder) if f.endswith(".png")])
    
    if not filenames:
        raise ValueError(f"在 {frames_folder} 中没有找到 PNG 图片")
    
    images = []
    for filename in filenames:
        filepath = os.path.join(frames_folder, filename)
        images.append(Image.open(filepath))
    
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        disposal=2
    )
    
    return output_path


def create_gif_from_frames(frames: List[Image.Image],
                           duration: int = 100,
                           output_path: str = None) -> Union[str, bytes]:
    """
    从 PIL Image 列表合成 GIF
    
    Args:
        frames: PIL Image 对象列表
        duration: 每帧的持续时间（毫秒）
        output_path: 输出路径（如果为None则返回字节数据）
    
    Returns:
        如果指定了 output_path，返回路径；否则返回 GIF 字节数据
    """
    if not frames:
        raise ValueError("帧列表为空")
    
    if output_path:
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            disposal=2
        )
        return output_path
    else:
        buffer = BytesIO()
        frames[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            disposal=2
        )
        buffer.seek(0)
        return buffer.getvalue()

