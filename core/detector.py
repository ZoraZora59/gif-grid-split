"""
自动检测精灵表网格结构的模块
通过图像投影分析自动识别行列数和黑线宽度
"""

from PIL import Image
from typing import Tuple, List, Union
from statistics import mean, median, stdev
from io import BytesIO


def detect_grid_lines(projection: List[float], min_line_width: int = 1) -> List[Tuple[int, int]]:
    """从投影数据中检测黑线位置"""
    avg = mean(projection)
    threshold = avg * 0.3
    
    lines = []
    in_line = False
    start = 0
    
    for i, val in enumerate(projection):
        is_dark = val < threshold
        if is_dark and not in_line:
            start = i
            in_line = True
        elif not is_dark and in_line:
            if i - start >= min_line_width:
                lines.append((start, i))
            in_line = False
    
    if in_line and len(projection) - start >= min_line_width:
        lines.append((start, len(projection)))
    
    return lines


def find_periodic_lines(lines: List[Tuple[int, int]], total_size: int) -> Tuple[List[Tuple[int, int]], int]:
    """从检测到的黑线中找出周期性的网格线"""
    if len(lines) < 2:
        return lines, len(lines) + 1
    
    centers = [(s + e) / 2 for s, e in lines]
    gaps = [centers[i+1] - centers[i] for i in range(len(centers) - 1)]
    
    if not gaps:
        return lines, len(lines) + 1
    
    median_gap = median(gaps)
    
    filtered_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            filtered_lines.append(line)
        else:
            gap = centers[i] - centers[i-1]
            if 0.75 * median_gap <= gap <= 1.25 * median_gap:
                filtered_lines.append(line)
    
    num_cells = len(filtered_lines) + 1
    return filtered_lines, num_cells


def calculate_confidence(h_lines, v_lines, rows, cols, height, width) -> float:
    """计算检测结果的置信度"""
    confidence = 1.0
    
    expected_h_lines = rows - 1
    expected_v_lines = cols - 1
    
    if len(h_lines) < expected_h_lines:
        confidence *= 0.7
    if len(v_lines) < expected_v_lines:
        confidence *= 0.7
    
    if len(h_lines) >= 2:
        h_centers = [(s + e) / 2 for s, e in h_lines]
        h_gaps = [h_centers[i+1] - h_centers[i] for i in range(len(h_centers) - 1)]
        if h_gaps and len(h_gaps) > 1:
            try:
                h_std = stdev(h_gaps) / mean(h_gaps) if mean(h_gaps) > 0 else 1
                confidence *= max(0.5, 1 - h_std)
            except Exception:
                pass
    
    if len(v_lines) >= 2:
        v_centers = [(s + e) / 2 for s, e in v_lines]
        v_gaps = [v_centers[i+1] - v_centers[i] for i in range(len(v_centers) - 1)]
        if v_gaps and len(v_gaps) > 1:
            try:
                v_std = stdev(v_gaps) / mean(v_gaps) if mean(v_gaps) > 0 else 1
                confidence *= max(0.5, 1 - v_std)
            except Exception:
                pass
    
    return round(confidence, 2)


def analyze_spritesheet(image_input: Union[str, bytes, BytesIO, Image.Image]) -> dict:
    """
    分析精灵表图片，自动检测网格结构
    
    Args:
        image_input: 图片路径、字节数据、BytesIO对象或PIL Image对象
    
    Returns:
        包含检测结果的字典
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
    
    original_size = (img.width, img.height)
    
    # 缩小图片加速分析
    max_size = 1000
    if img.width > max_size or img.height > max_size:
        ratio = min(max_size / img.width, max_size / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img_small = img.resize(new_size, Image.Resampling.LANCZOS)
        scale_factor = 1 / ratio
    else:
        img_small = img
        scale_factor = 1
    
    # 转为灰度图
    img_gray = img_small.convert('L') if img_small.mode != 'L' else img_small
    width, height = img_gray.size
    
    # 计算水平投影
    horizontal_projection = []
    for y in range(height):
        row_sum = sum(img_gray.getpixel((x, y)) for x in range(width))
        horizontal_projection.append(row_sum / width)
    
    # 计算垂直投影
    vertical_projection = []
    for x in range(width):
        col_sum = sum(img_gray.getpixel((x, y)) for y in range(height))
        vertical_projection.append(col_sum / height)
    
    # 检测黑线
    h_lines = detect_grid_lines(horizontal_projection)
    v_lines = detect_grid_lines(vertical_projection)
    
    # 找出周期性的网格线
    h_lines_filtered, num_rows = find_periodic_lines(h_lines, height)
    v_lines_filtered, num_cols = find_periodic_lines(v_lines, width)
    
    # 缩放回原图尺寸
    if scale_factor != 1:
        h_lines_filtered = [(int(s * scale_factor), int(e * scale_factor)) 
                           for s, e in h_lines_filtered]
        v_lines_filtered = [(int(s * scale_factor), int(e * scale_factor)) 
                           for s, e in v_lines_filtered]
    
    # 计算建议的 margin
    all_widths = [e - s for s, e in h_lines_filtered + v_lines_filtered]
    avg_line_width = mean(all_widths) if all_widths else 2
    suggested_margin = max(1, int(avg_line_width / 2 + 1))
    
    # 计算置信度
    confidence = calculate_confidence(
        h_lines_filtered, v_lines_filtered,
        num_rows, num_cols, original_size[1], original_size[0]
    )
    
    return {
        'rows': num_rows,
        'cols': num_cols,
        'horizontal_lines': h_lines_filtered,
        'vertical_lines': v_lines_filtered,
        'margin': suggested_margin,
        'line_width': round(avg_line_width, 1),
        'confidence': confidence,
        'image_size': original_size
    }

