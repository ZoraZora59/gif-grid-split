"""
自动检测精灵表网格结构的模块
通过图像投影分析自动识别行列数和黑线宽度

支持多种检测策略：
1. 暗线检测 - 检测黑色/深色分隔线
2. 亮线检测 - 检测白色/浅色分隔线  
3. 边缘变化检测 - 检测颜色突变边界
4. 均匀分割推测 - 基于常见网格尺寸推测
"""

from PIL import Image, ImageFilter
from typing import Tuple, List, Union, Optional
from statistics import mean, median, stdev
from io import BytesIO
from collections import Counter


def detect_grid_lines(projection: List[float], 
                      threshold_ratio: float = 0.3,
                      min_line_width: int = 1,
                      detect_dark: bool = True) -> List[Tuple[int, int]]:
    """
    从投影数据中检测分隔线位置
    
    Args:
        projection: 投影数据
        threshold_ratio: 阈值比例
        min_line_width: 最小线宽
        detect_dark: True检测暗线，False检测亮线
    """
    avg = mean(projection)
    
    if detect_dark:
        threshold = avg * threshold_ratio
        is_line = lambda val: val < threshold
    else:
        threshold = avg + (255 - avg) * (1 - threshold_ratio)
        is_line = lambda val: val > threshold
    
    lines = []
    in_line = False
    start = 0
    
    for i, val in enumerate(projection):
        if is_line(val) and not in_line:
            start = i
            in_line = True
        elif not is_line(val) and in_line:
            if i - start >= min_line_width:
                lines.append((start, i))
            in_line = False
    
    if in_line and len(projection) - start >= min_line_width:
        lines.append((start, len(projection)))
    
    return lines


def detect_edges(projection: List[float], 
                 min_edge_strength: float = 30,
                 min_gap: int = 10) -> List[int]:
    """
    检测投影数据中的边缘（颜色突变点）
    
    Args:
        projection: 投影数据
        min_edge_strength: 最小边缘强度
        min_gap: 边缘之间的最小间隔
    """
    # 计算梯度
    gradients = []
    for i in range(1, len(projection)):
        gradients.append(abs(projection[i] - projection[i-1]))
    
    # 找到显著的边缘
    edges = []
    for i, grad in enumerate(gradients):
        if grad >= min_edge_strength:
            # 检查是否与前一个边缘距离足够
            if not edges or (i - edges[-1]) >= min_gap:
                edges.append(i)
    
    return edges


def find_periodic_lines(lines: List[Tuple[int, int]], 
                        total_size: int,
                        tolerance: float = 0.25) -> Tuple[List[Tuple[int, int]], int]:
    """从检测到的线中找出周期性的网格线"""
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
            if (1 - tolerance) * median_gap <= gap <= (1 + tolerance) * median_gap:
                filtered_lines.append(line)
    
    num_cells = len(filtered_lines) + 1
    return filtered_lines, num_cells


def find_periodic_edges(edges: List[int], 
                        total_size: int,
                        tolerance: float = 0.2) -> Tuple[List[int], int]:
    """从边缘点中找出周期性的网格边界"""
    if len(edges) < 3:
        return edges, len(edges) + 1
    
    gaps = [edges[i+1] - edges[i] for i in range(len(edges) - 1)]
    
    if not gaps:
        return edges, 1
    
    # 找最常见的间隔
    gap_rounded = [round(g / 5) * 5 for g in gaps]  # 四舍五入到5的倍数
    gap_counter = Counter(gap_rounded)
    most_common_gap = gap_counter.most_common(1)[0][0]
    
    # 过滤出符合周期的边缘
    filtered_edges = [edges[0]]
    for i in range(1, len(edges)):
        gap = edges[i] - filtered_edges[-1]
        if (1 - tolerance) * most_common_gap <= gap <= (1 + tolerance) * most_common_gap:
            filtered_edges.append(edges[i])
    
    num_cells = len(filtered_edges)
    return filtered_edges, num_cells


def guess_grid_from_size(width: int, height: int) -> List[Tuple[int, int]]:
    """
    根据图片尺寸猜测可能的网格大小
    常见的精灵表尺寸：2x2, 3x3, 4x4, 5x5, 6x6, 8x8, 4x8, 8x4 等
    """
    candidates = []
    
    # 常见的网格配置
    common_grids = [
        (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8),
        (2, 4), (4, 2), (3, 4), (4, 3), (4, 6), (6, 4),
        (4, 8), (8, 4), (3, 6), (6, 3), (5, 10), (10, 5),
        (2, 8), (8, 2), (3, 9), (9, 3), (4, 12), (12, 4)
    ]
    
    for rows, cols in common_grids:
        cell_w = width / cols
        cell_h = height / rows
        
        # 检查单元格是否接近正方形或合理比例
        ratio = cell_w / cell_h if cell_h > 0 else 0
        if 0.5 <= ratio <= 2.0:
            # 检查是否整除（允许小误差）
            w_remainder = width % cols
            h_remainder = height % rows
            score = 1.0 - (w_remainder / width + h_remainder / height) / 2
            candidates.append((rows, cols, score))
    
    # 按分数排序
    candidates.sort(key=lambda x: x[2], reverse=True)
    return candidates[:5]


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


def analyze_spritesheet(image_input: Union[str, bytes, BytesIO, Image.Image],
                        detection_mode: str = 'auto') -> dict:
    """
    分析精灵表图片，自动检测网格结构
    
    Args:
        image_input: 图片路径、字节数据、BytesIO对象或PIL Image对象
        detection_mode: 检测模式
            - 'auto': 自动选择最佳策略
            - 'dark_lines': 只检测暗色分隔线
            - 'light_lines': 只检测亮色分隔线
            - 'edges': 使用边缘检测
            - 'guess': 基于尺寸猜测
    
    Returns:
        包含检测结果的字典
    """
    # 支持多种输入类型
    if isinstance(image_input, Image.Image):
        img = image_input.copy()
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
    
    # 计算水平投影（每行平均亮度）
    horizontal_projection = []
    for y in range(height):
        row_sum = sum(img_gray.getpixel((x, y)) for x in range(width))
        horizontal_projection.append(row_sum / width)
    
    # 计算垂直投影（每列平均亮度）
    vertical_projection = []
    for x in range(width):
        col_sum = sum(img_gray.getpixel((x, y)) for y in range(height))
        vertical_projection.append(col_sum / height)
    
    best_result = None
    best_confidence = 0
    
    # 策略1：暗线检测（多阈值）
    if detection_mode in ['auto', 'dark_lines']:
        for threshold in [0.2, 0.3, 0.4, 0.5]:
            h_lines = detect_grid_lines(horizontal_projection, threshold, detect_dark=True)
            v_lines = detect_grid_lines(vertical_projection, threshold, detect_dark=True)
            
            h_filtered, num_rows = find_periodic_lines(h_lines, height)
            v_filtered, num_cols = find_periodic_lines(v_lines, width)
            
            if num_rows > 1 and num_cols > 1:
                conf = calculate_confidence(h_filtered, v_filtered, num_rows, num_cols, height, width)
                if conf > best_confidence:
                    best_confidence = conf
                    best_result = {
                        'h_lines': h_filtered,
                        'v_lines': v_filtered,
                        'rows': num_rows,
                        'cols': num_cols,
                        'method': 'dark_lines'
                    }
    
    # 策略2：亮线检测
    if detection_mode in ['auto', 'light_lines']:
        for threshold in [0.3, 0.4, 0.5]:
            h_lines = detect_grid_lines(horizontal_projection, threshold, detect_dark=False)
            v_lines = detect_grid_lines(vertical_projection, threshold, detect_dark=False)
            
            h_filtered, num_rows = find_periodic_lines(h_lines, height)
            v_filtered, num_cols = find_periodic_lines(v_lines, width)
            
            if num_rows > 1 and num_cols > 1:
                conf = calculate_confidence(h_filtered, v_filtered, num_rows, num_cols, height, width)
                if conf > best_confidence:
                    best_confidence = conf
                    best_result = {
                        'h_lines': h_filtered,
                        'v_lines': v_filtered,
                        'rows': num_rows,
                        'cols': num_cols,
                        'method': 'light_lines'
                    }
    
    # 策略3：边缘检测
    if detection_mode in ['auto', 'edges']:
        for edge_strength in [20, 30, 40]:
            h_edges = detect_edges(horizontal_projection, edge_strength, min_gap=height//20)
            v_edges = detect_edges(vertical_projection, edge_strength, min_gap=width//20)
            
            h_periodic, num_rows = find_periodic_edges(h_edges, height)
            v_periodic, num_cols = find_periodic_edges(v_edges, width)
            
            if num_rows > 1 and num_cols > 1:
                # 将边缘转换为线的格式
                h_lines = [(e, e+1) for e in h_periodic]
                v_lines = [(e, e+1) for e in v_periodic]
                
                conf = calculate_confidence(h_lines, v_lines, num_rows, num_cols, height, width) * 0.9
                if conf > best_confidence:
                    best_confidence = conf
                    best_result = {
                        'h_lines': h_lines,
                        'v_lines': v_lines,
                        'rows': num_rows,
                        'cols': num_cols,
                        'method': 'edges'
                    }
    
    # 策略4：基于尺寸猜测（作为后备）
    if detection_mode in ['auto', 'guess'] and best_confidence < 0.5:
        guesses = guess_grid_from_size(original_size[0], original_size[1])
        if guesses:
            rows, cols, score = guesses[0]
            if score > 0.8:  # 高分猜测
                best_result = {
                    'h_lines': [],
                    'v_lines': [],
                    'rows': rows,
                    'cols': cols,
                    'method': 'guess'
                }
                best_confidence = score * 0.7  # 降低猜测的置信度
    
    # 如果没有检测到，返回默认值
    if best_result is None:
        best_result = {
            'h_lines': [],
            'v_lines': [],
            'rows': 1,
            'cols': 1,
            'method': 'none'
        }
        best_confidence = 0
    
    # 缩放回原图尺寸
    h_lines_scaled = best_result['h_lines']
    v_lines_scaled = best_result['v_lines']
    if scale_factor != 1:
        h_lines_scaled = [(int(s * scale_factor), int(e * scale_factor)) 
                         for s, e in best_result['h_lines']]
        v_lines_scaled = [(int(s * scale_factor), int(e * scale_factor)) 
                         for s, e in best_result['v_lines']]
    
    # 计算建议的 margin
    all_widths = [e - s for s, e in h_lines_scaled + v_lines_scaled]
    avg_line_width = mean(all_widths) if all_widths else 2
    suggested_margin = max(1, int(avg_line_width / 2 + 1))
    
    return {
        'rows': best_result['rows'],
        'cols': best_result['cols'],
        'horizontal_lines': h_lines_scaled,
        'vertical_lines': v_lines_scaled,
        'margin': suggested_margin,
        'line_width': round(avg_line_width, 1),
        'confidence': best_confidence,
        'image_size': original_size,
        'detection_method': best_result['method']
    }
