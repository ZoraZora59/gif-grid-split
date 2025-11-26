import os
import argparse
from PIL import Image


def create_gif(frames_folder, output_gif_name, duration=100):
    """
    读取文件夹中的序列帧并合成 GIF。
    Args:
        frames_folder (str): 存放序列帧的文件夹。
        output_gif_name (str): 输出 GIF 的文件名。
        duration (int): 每帧的持续时间（毫秒）。数值越小速度越快。
    """
    images = []
    # 获取文件夹内所有 png 文件，并排序确保顺序正确
    filenames = sorted([f for f in os.listdir(frames_folder) if f.endswith(".png")])
    
    if not filenames:
        print(f"在 {frames_folder} 中没有找到 PNG 图片。")
        return

    print(f"找到 {len(filenames)} 帧，开始合成 GIF...")

    for filename in filenames:
        filepath = os.path.join(frames_folder, filename)
        images.append(Image.open(filepath))

    # 保存为 GIF
    # save_all=True: 保存所有帧
    # append_images: 后续的帧列表
    # duration: 每帧持续毫秒数
    # loop=0: 无限循环
    # transparency=0 和 disposal=2 用于处理透明背景的叠加问题，让上一帧清除干净
    images[0].save(
        output_gif_name,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0, 
        disposal=2 
    )
    print(f"GIF 合成成功！已保存为: {output_gif_name}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="将序列帧合成为 GIF 动画",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python make_gif.py -i frames -o animation.gif
  python make_gif.py -i frames -o animation.gif -d 50
        """
    )
    parser.add_argument("-i", "--input", default="frames", help="输入帧文件夹 (默认: frames)")
    parser.add_argument("-o", "--output", default="output.gif", help="输出 GIF 文件名 (默认: output.gif)")
    parser.add_argument("-d", "--duration", type=int, default=80, 
                        help="每帧持续时间(毫秒)，数值越小速度越快 (默认: 80)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if os.path.exists(args.input):
        create_gif(args.input, args.output, args.duration)
    else:
        print(f"找不到文件夹: {args.input}，请先运行切片脚本。")