# 🎮 精灵表转 GIF 动画工具

将网格排列的精灵表（Sprite Sheet）自动切分并合成 GIF 动画。

![示例](https://img.shields.io/badge/Python-3.7+-blue.svg)
![许可](https://img.shields.io/badge/License-MIT-green.svg)

---

## ✨ 功能特点

- 🔍 **智能识别** - 自动检测网格行列数和黑线宽度，无需手动计算
- 🎯 **一键转换** - 交互式引导，按提示操作即可
- 🖼️ **格式支持** - 支持 PNG、JPG、JPEG、GIF、BMP、WebP 等常见格式
- ⚡ **快速处理** - 大图自动优化，处理速度快

---

## 🚀 快速开始

### 方式一：双击运行（推荐新手）

#### macOS 用户

1. 将你的精灵表图片放到此文件夹
2. 双击 `start.command` 文件
3. 首次运行会自动安装依赖，请耐心等待
4. 按照屏幕提示操作即可

> ⚠️ 如果提示"无法打开"，请右键点击 → 打开，或在终端执行：`chmod +x start.command`

#### Windows 用户

1. 将你的精灵表图片放到此文件夹
2. 双击 `start.bat` 文件
3. 首次运行会自动安装依赖，请耐心等待
4. 按照屏幕提示操作即可

---

### 方式二：命令行使用

#### 1. 安装依赖

```bash
# macOS / Linux
bash setup.sh

# Windows
setup.bat

# 或手动安装
pip install Pillow
```

#### 2. 运行交互式工具

```bash
# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 运行引导程序
python run.py
```

#### 3. 或使用命令行参数

```bash
# 自动检测模式（推荐）
python slice_spritesheet.py -i 你的图片.jpg --auto

# 手动指定参数
python slice_spritesheet.py -i 你的图片.jpg -r 6 -c 6 -m 3

# 合成 GIF
python make_gif.py -i frames -o output.gif -d 80
```

---

## 📖 详细说明

### 什么是精灵表？

精灵表是游戏和动画中常用的图片格式，将动画的多个帧按网格排列在一张大图中：

```
┌─────┬─────┬─────┬─────┐
│ 帧1 │ 帧2 │ 帧3 │ 帧4 │
├─────┼─────┼─────┼─────┤
│ 帧5 │ 帧6 │ 帧7 │ 帧8 │
├─────┼─────┼─────┼─────┤
│ 帧9 │帧10 │帧11 │帧12 │
└─────┴─────┴─────┴─────┘
```

本工具可以自动识别这种网格结构，将其切分成独立的帧，然后合成 GIF 动画。

---

### 命令行参数说明

#### slice_spritesheet.py - 切片工具

| 参数 | 说明 | 示例 |
|------|------|------|
| `-i, --input` | 输入图片路径 | `-i sprite.png` |
| `-o, --output` | 输出文件夹 | `-o my_frames` |
| `-a, --auto` | 自动检测模式 | `--auto` |
| `-r, --rows` | 网格行数 | `-r 6` |
| `-c, --cols` | 网格列数 | `-c 6` |
| `-m, --margin` | 边距像素 | `-m 3` |

#### make_gif.py - GIF 合成工具

| 参数 | 说明 | 示例 |
|------|------|------|
| `-i, --input` | 帧文件夹 | `-i frames` |
| `-o, --output` | 输出 GIF 文件 | `-o anim.gif` |
| `-d, --duration` | 帧间隔(毫秒) | `-d 80` |

> 💡 duration 数值越小动画越快：50=快速, 80=正常, 150=慢速

---

## ❓ 常见问题

### Q: 自动检测的行列数不准确怎么办？

A: 可以使用手动模式指定正确的参数：
```bash
python slice_spritesheet.py -i 图片.jpg -r 正确行数 -c 正确列数
```

### Q: 切出来的图片边缘有黑线怎么办？

A: 增加边距参数：
```bash
python slice_spritesheet.py -i 图片.jpg --auto -m 5
```

### Q: 切出来的图片内容被切掉一部分怎么办？

A: 减小边距参数：
```bash
python slice_spritesheet.py -i 图片.jpg --auto -m 1
```

### Q: GIF 动画太快或太慢怎么办？

A: 调整 duration 参数：
```bash
python make_gif.py -i frames -o output.gif -d 100  # 改大变慢
python make_gif.py -i frames -o output.gif -d 50   # 改小变快
```

### Q: 提示找不到 Python 怎么办？

A: 请先安装 Python 3：
- **macOS**: `brew install python3` 或从 [python.org](https://www.python.org/downloads/) 下载
- **Windows**: 从 [python.org](https://www.python.org/downloads/) 下载，安装时勾选 "Add Python to PATH"

### Q: macOS 提示无法打开应用怎么办？

A: 在终端中执行：
```bash
chmod +x start.command setup.sh
```
然后右键点击 `start.command` → 打开

---

## 📁 文件结构

```
gif-grid-split/
├── run.py                 # 交互式引导程序（推荐使用）
├── slice_spritesheet.py   # 切片工具
├── make_gif.py            # GIF 合成工具
├── auto_detect.py         # 自动检测模块
├── start.command          # macOS 启动脚本
├── start.bat              # Windows 启动脚本
├── setup.sh               # macOS 安装脚本
├── setup.bat              # Windows 安装脚本
├── requirements.txt       # 依赖列表
└── README.md              # 本文档
```

---

## 🛠️ 技术原理

### 自动检测算法

1. **图像投影分析**：将图像在水平/垂直方向投影，计算每行/列的平均亮度
2. **黑线检测**：黑线区域的亮度显著低于内容区域，形成"低谷"
3. **周期性分析**：检测这些低谷的周期性，推断网格结构
4. **宽度测量**：测量黑线宽度，自动计算最佳裁剪边距

---

## 📄 许可证

MIT License - 可自由使用、修改和分发

---

## 🙏 致谢

- [Pillow](https://pillow.readthedocs.io/) - Python 图像处理库

