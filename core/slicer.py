"""
精灵表切片模块
将网格图片切分为独立的帧
"""

import os
from PIL import Image
from typing import List, Union
from io import BytesIO


def slice_spritesheet(image_input: Union[str, bytes, BytesIO, Image.Image],
                      output_folder: str,
                      rows: int,
                      cols: int,
                      margin: int = 2) -> List[str]:
    """
    切分网格图片并保存为单独的帧文件
    
    Args:
        image_input: 图片路径、字节数据、BytesIO对象或PIL Image对象
        output_folder: 输出文件夹路径
        rows: 网格行数
        cols: 网格列数
        margin: 向内裁剪的边距像素
    
    Returns:
        保存的文件路径列表
    """
    # 支持多种输入类型
    if isinstance(image_input, Image.Image):
        img = image_input
    elif isinstance(image_input, bytes):
        img = Image.open(BytesIO(image_input))
    elif isinstance(image_input, BytesIO):
        img = Image.open(image_input)
    else:
        img = Image.open(image_input)
    
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    img_width, img_height = img.size
    cell_width = img_width / cols
    cell_height = img_height / rows
    
    saved_files = []
    count = 1
    
    for r in range(rows):
        for c in range(cols):
            left = c * cell_width
            upper = r * cell_height
            right = left + cell_width
            lower = upper + cell_height
            
            crop_box = (
                int(left + margin),
                int(upper + margin),
                int(right - margin),
                int(lower - margin)
            )
            
            frame = img.crop(crop_box)
            filename = f"frame_{count:03d}.png"
            save_path = os.path.join(output_folder, filename)
            frame.save(save_path, "PNG")
            saved_files.append(save_path)
            count += 1
    
    return saved_files


def slice_spritesheet_to_frames(image_input: Union[str, bytes, BytesIO, Image.Image],
                                 rows: int,
                                 cols: int,
                                 margin: int = 2) -> List[Image.Image]:
    """
    切分网格图片并返回帧图像列表（不保存文件）
    
    Args:
        image_input: 图片路径、字节数据、BytesIO对象或PIL Image对象
        rows: 网格行数
        cols: 网格列数
        margin: 向内裁剪的边距像素
    
    Returns:
        PIL Image对象列表
    """
    # 支持多种输入类型
    if isinstance(image_input, Image.Image):
        img = image_input
    elif isinstance(image_input, bytes):
        img = Image.open(BytesIO(image_input))
    elif isinstance(image_input, BytesIO):
        img = Image.open(image_input)
    else:
        img = Image.open(image_input)
    
    img_width, img_height = img.size
    cell_width = img_width / cols
    cell_height = img_height / rows
    
    frames = []
    
    for r in range(rows):
        for c in range(cols):
            left = c * cell_width
            upper = r * cell_height
            right = left + cell_width
            lower = upper + cell_height
            
            crop_box = (
                int(left + margin),
                int(upper + margin),
                int(right - margin),
                int(lower - margin)
            )
            
            frame = img.crop(crop_box)
            frames.append(frame)
    
    return frames

