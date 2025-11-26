@echo off
chcp 65001 >nul
title 精灵表转 GIF 工具

cd /d "%~dp0"

:: 检查虚拟环境
if not exist ".venv" (
    echo ⚠️  首次运行，需要安装环境...
    echo.
    call setup.bat
)

:: 激活虚拟环境并运行
call .venv\Scripts\activate.bat
python run.py
pause

