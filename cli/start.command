#!/bin/bash
# macOS 双击启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "⚠️  首次运行，需要安装环境..."
    echo ""
    bash setup.sh
fi

# 激活虚拟环境并运行
source .venv/bin/activate
python run.py

