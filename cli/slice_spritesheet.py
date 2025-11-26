import os
import argparse
from PIL import Image


def slice_spritesheet(image_path, output_folder, rows, cols, margin=2):
    """
    切分网格图片并保存为单独的帧。

    Args:
        image_path (str): 原始大图的路径。
        output_folder (str): 输出小图的文件夹路径。
        rows (int): 网格的行数。
        cols (int): 网格的列数。
        margin (int): 向内裁剪的边距像素，用于去除网格黑线。默认为2像素。
    """
    # 1. 检查图片是否存在
    if not os.path.exists(image_path):
        print(f"错误：找不到文件 {image_path}")
        return

    # 2. 创建输出文件夹（如果不存在）
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"已创建输出文件夹: {output_folder}")

    try:
        # 3. 打开图片
        img = Image.open(image_path)
        img_width, img_height = img.size
        print(f"成功打开图片，尺寸: {img_width}x{img_height}")

        # 4. 计算每个单元格的理论宽度和高度
        # 使用浮点除法确保精度，稍后在坐标计算时转为整数
        cell_width = img_width / cols
        cell_height = img_height / rows

        count = 1
        print("开始切分...")

        # 5. 双重循环遍历网格 (先行后列)
        for r in range(rows):
            for c in range(cols):
                # 计算当前单元格的理论左上角和右下角坐标
                left = c * cell_width
                upper = r * cell_height
                right = left + cell_width
                lower = upper + cell_height

                # 6. 应用边距 (Margin) 进行向内裁剪
                # 这一步是为了去掉格子之间的黑线边框
                # int() 确保坐标是整数
                crop_box = (
                    int(left + margin),
                    int(upper + margin),
                    int(right - margin),
                    int(lower - margin)
                )

                # 执行裁剪
                frame = img.crop(crop_box)

                # 7. 生成文件名并保存
                # 使用 :02d 确保文件名是两位数对齐的 (frame_01.png, frame_02.png...)
                # 这对于后续按顺序合成 GIF 至关重要
                filename = f"frame_{count:02d}.png"
                save_path = os.path.join(output_folder, filename)
                
                # 保存为PNG以保留透明度和质量
                frame.save(save_path, "PNG")
                print(f"已保存: {filename}")
                
                count += 1
        
        print(f"\n完成！共切分出 {count-1} 张图片存放到 '{output_folder}' 文件夹中。")
        print("现在你可以使用这些图片去合成 GIF 了。")

    except Exception as e:
        print(f"发生错误: {e}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="切分网格精灵表图片为单独的帧",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 自动检测模式（推荐）
  python slice_spritesheet.py -i 柯南攻击图片.jpg --auto
  
  # 手动指定参数
  python slice_spritesheet.py -i 柯南攻击图片.jpg -r 6 -c 6
  python slice_spritesheet.py -i sprite.png -r 4 -c 8 -o frames -m 3
        """
    )
    parser.add_argument("-i", "--input", required=True, help="输入图片路径")
    parser.add_argument("-o", "--output", default="frames", help="输出文件夹 (默认: frames)")
    parser.add_argument("-a", "--auto", action="store_true", 
                        help="自动检测网格结构（行列数和黑线宽度）")
    parser.add_argument("-r", "--rows", type=int, help="网格行数（手动模式必填）")
    parser.add_argument("-c", "--cols", type=int, help="网格列数（手动模式必填）")
    parser.add_argument("-m", "--margin", type=int, 
                        help="边距像素，用于去除格子间黑线 (自动模式会自动计算)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    if args.auto:
        # 自动检测模式
        try:
            from auto_detect import analyze_spritesheet, print_analysis_result
        except ImportError as e:
            print(f"错误：无法导入 auto_detect 模块: {e}")
            print("请确保 auto_detect.py 在同一目录下，并安装依赖: pip install numpy Pillow")
            exit(1)
        
        print("🔍 正在自动分析图片...")
        result = analyze_spritesheet(args.input)
        print_analysis_result(result)
        
        rows = result['rows']
        cols = result['cols']
        margin = args.margin if args.margin is not None else result['margin']
        
        if result['confidence'] < 0.5:
            confirm = input("\n⚠️ 置信度较低，是否继续切分？(y/n): ")
            if confirm.lower() != 'y':
                print("已取消")
                exit(0)
        
        print(f"\n📌 使用参数: {rows}行 x {cols}列, 边距={margin}px")
        slice_spritesheet(args.input, args.output, rows, cols, margin)
    else:
        # 手动模式
        if args.rows is None or args.cols is None:
            print("错误：手动模式下必须指定 -r/--rows 和 -c/--cols")
            print("提示：使用 --auto 可自动检测网格结构")
            exit(1)
        
        margin = args.margin if args.margin is not None else 2
        slice_spritesheet(args.input, args.output, args.rows, args.cols, margin)