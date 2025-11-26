#!/usr/bin/env python3
"""
精灵表转 GIF 动画 - 交互式引导脚本
无需代码基础，按提示操作即可
"""

import os
import sys
import glob


def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """打印欢迎横幅"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        🎮 精灵表 → GIF 动画转换工具 🎬                         ║
║                                                               ║
║   将网格排列的动画帧图片自动切分并合成 GIF 动画                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def check_dependencies():
    """检查依赖是否已安装"""
    try:
        from PIL import Image
        return True
    except ImportError:
        return False


def install_dependencies():
    """安装依赖"""
    print("\n📦 正在安装必要的依赖...")
    
    # 尝试多种安装方式
    commands = [
        [sys.executable, "-m", "pip", "install", "Pillow", "-q"],
        ["pip3", "install", "Pillow", "-q"],
        ["pip", "install", "Pillow", "-q"],
    ]
    
    import subprocess
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ 依赖安装成功！")
                return True
        except Exception:
            continue
    
    print("❌ 自动安装失败，请手动运行: pip install Pillow")
    return False


def find_images():
    """查找当前目录下的图片文件"""
    extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp']
    images = []
    for ext in extensions:
        images.extend(glob.glob(ext))
        images.extend(glob.glob(ext.upper()))
    
    # 排除可能是输出文件的图片
    exclude_patterns = ['_output', '_frames', 'frame_']
    filtered = []
    for img in images:
        if not any(p in img.lower() for p in exclude_patterns):
            filtered.append(img)
    
    return sorted(set(filtered))


def select_image(images):
    """让用户选择图片"""
    print("\n📁 在当前目录找到以下图片：\n")
    for i, img in enumerate(images, 1):
        print(f"   [{i}] {img}")
    
    print(f"\n   [0] 手动输入路径")
    
    while True:
        try:
            choice = input("\n👉 请输入图片编号 (直接回车选择第一个): ").strip()
            
            if choice == "":
                return images[0]
            
            choice = int(choice)
            
            if choice == 0:
                path = input("👉 请输入图片完整路径: ").strip()
                if os.path.exists(path):
                    return path
                else:
                    print("❌ 文件不存在，请重新输入")
            elif 1 <= choice <= len(images):
                return images[choice - 1]
            else:
                print("❌ 无效选择，请重新输入")
        except ValueError:
            print("❌ 请输入有效数字")


def get_output_name(input_image):
    """生成输出文件名"""
    base = os.path.splitext(input_image)[0]
    return f"{base}_output.gif"


def run_auto_detection(image_path):
    """运行自动检测"""
    from auto_detect import analyze_spritesheet, print_analysis_result
    
    print("\n🔍 正在自动分析图片结构...")
    result = analyze_spritesheet(image_path)
    print_analysis_result(result)
    
    return result


def run_slice(image_path, output_folder, rows, cols, margin):
    """运行切片"""
    from slice_spritesheet import slice_spritesheet
    slice_spritesheet(image_path, output_folder, rows, cols, margin)


def run_gif_creation(frames_folder, output_gif, duration):
    """运行 GIF 合成"""
    from make_gif import create_gif
    create_gif(frames_folder, output_gif, duration)


def ask_yes_no(prompt, default=True):
    """询问是/否问题"""
    suffix = " [Y/n]: " if default else " [y/N]: "
    answer = input(prompt + suffix).strip().lower()
    
    if answer == "":
        return default
    return answer in ['y', 'yes', '是', '好', 'ok']


def ask_number(prompt, default, min_val=1, max_val=1000):
    """询问数字"""
    while True:
        answer = input(f"{prompt} (默认 {default}): ").strip()
        if answer == "":
            return default
        try:
            num = int(answer)
            if min_val <= num <= max_val:
                return num
            print(f"❌ 请输入 {min_val} 到 {max_val} 之间的数字")
        except ValueError:
            print("❌ 请输入有效数字")


def main():
    """主函数"""
    clear_screen()
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("⚠️  检测到缺少必要的依赖库 (Pillow)")
        if ask_yes_no("是否自动安装"):
            if not install_dependencies():
                input("\n按回车键退出...")
                return
        else:
            print("\n请手动安装依赖后重试: pip install Pillow")
            input("按回车键退出...")
            return
    
    # 查找图片
    images = find_images()
    
    if not images:
        print("\n❌ 当前目录下没有找到图片文件")
        print("   请将精灵表图片放到此脚本所在目录，然后重新运行")
        input("\n按回车键退出...")
        return
    
    # 选择图片
    image_path = select_image(images)
    print(f"\n✅ 已选择: {image_path}")
    
    # 自动检测
    print("\n" + "=" * 50)
    result = run_auto_detection(image_path)
    
    # 确认参数
    print("\n" + "=" * 50)
    print("📝 参数确认")
    print("=" * 50)
    
    if result['confidence'] >= 0.8:
        if ask_yes_no("自动检测结果可信度高，是否使用自动检测的参数"):
            rows = result['rows']
            cols = result['cols']
            margin = result['margin']
        else:
            rows = ask_number("请输入行数", result['rows'])
            cols = ask_number("请输入列数", result['cols'])
            margin = ask_number("请输入边距像素", result['margin'], 0, 50)
    else:
        print("⚠️  自动检测置信度较低，建议手动确认参数")
        rows = ask_number("请输入行数", result['rows'])
        cols = ask_number("请输入列数", result['cols'])
        margin = ask_number("请输入边距像素", result['margin'], 0, 50)
    
    # GIF 速度
    print("\n💨 动画速度设置")
    print("   数值越小动画越快: 50=快速, 80=正常, 150=慢速")
    duration = ask_number("每帧持续时间(毫秒)", 80, 10, 1000)
    
    # 输出文件名
    output_gif = get_output_name(image_path)
    frames_folder = "_temp_frames"
    
    # 开始处理
    print("\n" + "=" * 50)
    print("🚀 开始处理")
    print("=" * 50)
    
    print(f"\n📌 使用参数:")
    print(f"   • 网格: {rows} 行 × {cols} 列")
    print(f"   • 边距: {margin} 像素")
    print(f"   • 帧速度: {duration} 毫秒")
    print(f"   • 输出文件: {output_gif}")
    
    # 切片
    print("\n" + "-" * 50)
    run_slice(image_path, frames_folder, rows, cols, margin)
    
    # 合成 GIF
    print("\n" + "-" * 50)
    run_gif_creation(frames_folder, output_gif, duration)
    
    # 清理临时文件
    if ask_yes_no("\n🗑️  是否删除临时帧文件"):
        import shutil
        try:
            shutil.rmtree(frames_folder)
            print("✅ 临时文件已清理")
        except Exception as e:
            print(f"⚠️  清理失败: {e}")
    
    # 完成
    print("\n" + "=" * 50)
    print("🎉 处理完成！")
    print("=" * 50)
    print(f"\n✅ GIF 动画已保存为: {output_gif}")
    print("\n   你可以用浏览器或图片查看器打开它查看效果")
    
    # 询问是否继续处理其他图片
    if len(images) > 1 and ask_yes_no("\n是否继续处理其他图片"):
        main()
    else:
        input("\n按回车键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        input("\n按回车键退出...")

