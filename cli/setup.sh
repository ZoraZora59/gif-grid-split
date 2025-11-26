#!/bin/bash
# macOS / Linux 一键安装脚本

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        🎮 精灵表转 GIF 工具 - 环境安装脚本                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📁 工作目录: $SCRIPT_DIR"
echo ""

# 检查 Python
echo "🔍 检查 Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✅ 找到 Python3: $(python3 --version)"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✅ 找到 Python: $(python --version)"
else
    echo "❌ 未找到 Python，请先安装 Python 3"
    echo "   macOS: brew install python3"
    echo "   Ubuntu: sudo apt install python3"
    exit 1
fi

echo ""

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    $PYTHON_CMD -m venv .venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境并安装依赖
echo ""
echo "📦 安装依赖..."
source .venv/bin/activate
pip install --upgrade pip -q
pip install Pillow -q
echo "✅ 依赖安装完成"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎉 安装完成！"
echo ""
echo "使用方法："
echo "   1. 将精灵表图片放到此文件夹"
echo "   2. 双击运行 start.command (macOS) 或执行以下命令:"
echo ""
echo "      source .venv/bin/activate"
echo "      python run.py"
echo ""
echo "═══════════════════════════════════════════════════════════════"

