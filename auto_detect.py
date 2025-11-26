"""
自动检测精灵表网格结构的模块
通过图像投影分析自动识别行列数和黑线宽度

纯 Python + Pillow 实现，无需 numpy/scipy
"""

from PIL import Image
from typing import Tuple, List
from statistics import mean, median, stdev


def detect_grid_lines(projection: List[float], min_line_width: int = 1) -> List[Tuple[int, int]]:
    """
    从投影数据中检测黑线位置
    
    Args:
        projection: 一维投影列表（平均亮度值）
        min_line_width: 最小黑线宽度
    
    Returns:
        黑线区间列表 [(start, end), ...]
    """
    # 计算阈值：低于平均值30%视为黑线
    avg = mean(projection)
    threshold = avg * 0.3
    
    # 找到连续的黑色区域
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
    
    # 处理末尾的黑线
    if in_line and len(projection) - start >= min_line_width:
        lines.append((start, len(projection)))
    
    return lines


def find_periodic_lines(lines: List[Tuple[int, int]], total_size: int) -> Tuple[List[Tuple[int, int]], int]:
    """
    从检测到的黑线中找出周期性的网格线
    
    Args:
        lines: 检测到的黑线列表
        total_size: 图像在该方向的总尺寸
    
    Returns:
        (过滤后的网格线列表, 估计的格子数)
    """
    if len(lines) < 2:
        return lines, len(lines) + 1
    
    # 计算相邻黑线的间距
    centers = [(s + e) / 2 for s, e in lines]
    gaps = [centers[i+1] - centers[i] for i in range(len(centers) - 1)]
    
    if not gaps:
        return lines, len(lines) + 1
    
    # 找到最常见的间距（使用中位数更稳健）
    median_gap = median(gaps)
    
    # 过滤掉偏离太多的线（可能是噪声）
    filtered_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            filtered_lines.append(line)
        else:
            gap = centers[i] - centers[i-1]
            # 允许25%的误差
            if 0.75 * median_gap <= gap <= 1.25 * median_gap:
                filtered_lines.append(line)
    
    # 估计格子数
    num_cells = len(filtered_lines) + 1
    
    return filtered_lines, num_cells


def get_row_average(img, row: int) -> float:
    """计算某一行的平均亮度"""
    width = img.width
    total = 0
    for x in range(width):
        pixel = img.getpixel((x, row))
        if isinstance(pixel, tuple):
            # RGB 或 RGBA
            total += sum(pixel[:3]) / 3
        else:
            total += pixel
    return total / width


def get_col_average(img, col: int) -> float:
    """计算某一列的平均亮度"""
    height = img.height
    total = 0
    for y in range(height):
        pixel = img.getpixel((col, y))
        if isinstance(pixel, tuple):
            total += sum(pixel[:3]) / 3
        else:
            total += pixel
    return total / height


def analyze_spritesheet(image_path: str) -> dict:
    """
    分析精灵表图片，自动检测网格结构
    
    Args:
        image_path: 图片路径
    
    Returns:
        包含检测结果的字典
    """
    # 加载图片
    img = Image.open(image_path)
    
    # 如果图片太大，先缩小以加快分析速度
    max_size = 1000
    if img.width > max_size or img.height > max_size:
        ratio = min(max_size / img.width, max_size / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img_small = img.resize(new_size, Image.Resampling.LANCZOS)
        scale_factor = 1 / ratio
    else:
        img_small = img
        scale_factor = 1
    
    # 转为灰度图加速处理
    if img_small.mode != 'L':
        img_gray = img_small.convert('L')
    else:
        img_gray = img_small
    
    width, height = img_gray.size
    
    print("  正在分析水平方向...")
    # 计算水平投影（每行的平均亮度）
    horizontal_projection = []
    for y in range(height):
        row_sum = 0
        for x in range(width):
            row_sum += img_gray.getpixel((x, y))
        horizontal_projection.append(row_sum / width)
    
    print("  正在分析垂直方向...")
    # 计算垂直投影（每列的平均亮度）
    vertical_projection = []
    for x in range(width):
        col_sum = 0
        for y in range(height):
            col_sum += img_gray.getpixel((x, y))
        vertical_projection.append(col_sum / height)
    
    # 检测黑线
    h_lines = detect_grid_lines(horizontal_projection)
    v_lines = detect_grid_lines(vertical_projection)
    
    # 找出周期性的网格线
    h_lines_filtered, num_rows = find_periodic_lines(h_lines, height)
    v_lines_filtered, num_cols = find_periodic_lines(v_lines, width)
    
    # 将坐标缩放回原图尺寸
    if scale_factor != 1:
        h_lines_filtered = [(int(s * scale_factor), int(e * scale_factor)) 
                           for s, e in h_lines_filtered]
        v_lines_filtered = [(int(s * scale_factor), int(e * scale_factor)) 
                           for s, e in v_lines_filtered]
    
    # 计算黑线平均宽度作为建议的 margin
    all_widths = [e - s for s, e in h_lines_filtered + v_lines_filtered]
    avg_line_width = mean(all_widths) if all_widths else 2
    suggested_margin = max(1, int(avg_line_width / 2 + 1))
    
    # 计算置信度
    confidence = calculate_confidence(h_lines_filtered, v_lines_filtered, 
                                       num_rows, num_cols, img.height, img.width)
    
    return {
        'rows': num_rows,
        'cols': num_cols,
        'horizontal_lines': h_lines_filtered,
        'vertical_lines': v_lines_filtered,
        'margin': suggested_margin,
        'line_width': avg_line_width,
        'confidence': confidence,
        'image_size': (img.width, img.height)
    }


def calculate_confidence(h_lines, v_lines, rows, cols, height, width) -> float:
    """计算检测结果的置信度"""
    confidence = 1.0
    
    # 如果没有检测到足够的线，降低置信度
    expected_h_lines = rows - 1
    expected_v_lines = cols - 1
    
    if len(h_lines) < expected_h_lines:
        confidence *= 0.7
    if len(v_lines) < expected_v_lines:
        confidence *= 0.7
    
    # 检查间距的一致性
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


def print_analysis_result(result: dict):
    """打印分析结果"""
    print("\n" + "=" * 50)
    print("🔍 精灵表自动分析结果")
    print("=" * 50)
    print(f"📐 图片尺寸: {result['image_size'][0]} x {result['image_size'][1]}")
    print(f"📊 检测到网格: {result['rows']} 行 x {result['cols']} 列")
    print(f"📏 黑线平均宽度: {result['line_width']:.1f} 像素")
    print(f"✂️  建议边距 (margin): {result['margin']} 像素")
    print(f"🎯 置信度: {result['confidence'] * 100:.0f}%")
    print("-" * 50)
    
    if result['confidence'] < 0.5:
        print("⚠️  置信度较低，建议手动确认网格参数")
    elif result['confidence'] < 0.8:
        print("💡 置信度中等，结果可能需要微调")
    else:
        print("✅ 检测结果可信度高")
    
    print("=" * 50)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="自动分析精灵表网格结构")
    parser.add_argument("image", help="输入图片路径")
    args = parser.parse_args()
    
    result = analyze_spritesheet(args.image)
    print_analysis_result(result)
    
    print(f"\n💡 推荐命令:")
    print(f"   python slice_spritesheet.py -i {args.image} -r {result['rows']} -c {result['cols']} -m {result['margin']}")
