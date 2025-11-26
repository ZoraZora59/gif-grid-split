@echo off
chcp 65001 >nul
title 精灵表转 GIF 工具 - 环境安装

echo ╔═══════════════════════════════════════════════════════════════╗
echo ║        🎮 精灵表转 GIF 工具 - 环境安装脚本                     ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"
echo 📁 工作目录: %cd%
echo.

:: 检查 Python
echo 🔍 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python，请先安装 Python 3
    echo    下载地址: https://www.python.org/downloads/
    echo    安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
echo ✅ 找到 Python
python --version
echo.

:: 创建虚拟环境
if not exist ".venv" (
    echo 📦 创建虚拟环境...
    python -m venv .venv
    echo ✅ 虚拟环境创建成功
) else (
    echo ✅ 虚拟环境已存在
)

:: 激活虚拟环境并安装依赖
echo.
echo 📦 安装依赖...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install Pillow -q
echo ✅ 依赖安装完成

echo.
echo ═══════════════════════════════════════════════════════════════
echo 🎉 安装完成！
echo.
echo 使用方法：
echo    1. 将精灵表图片放到此文件夹
echo    2. 双击运行 start.bat
echo.
echo ═══════════════════════════════════════════════════════════════
echo.
pause

