"""
精灵表处理核心模块
提供自动检测、切片、GIF合成功能
"""

from .detector import analyze_spritesheet
from .slicer import slice_spritesheet, slice_spritesheet_to_frames
from .gif_maker import create_gif, create_gif_from_frames

__all__ = [
    'analyze_spritesheet',
    'slice_spritesheet',
    'slice_spritesheet_to_frames',
    'create_gif',
    'create_gif_from_frames',
]

