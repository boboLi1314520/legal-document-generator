@echo off
chcp 65001 >nul
title 法律文书自动生成系统
setlocal enabledelayedexpansion

echo ========================================
echo    法律文书自动生成系统 v1.0
echo ========================================
echo.

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: ========== 第一步：检查 Python ==========
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo.
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo       已检测到 Python %%v
echo.

:: ========== 第二步：安装依赖 ==========
echo [2/4] 检查后端依赖...
cd /d "%SCRIPT_DIR%backend"

:: 检查关键依赖是否已安装
python -c "import fastapi, uvicorn, fitz, docx, openpyxl, pandas, httpx" >nul 2>&1
if errorlevel 1 (
    echo       首次运行，正在安装依赖包（需要几分钟，请耐心等待）...
    echo.
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo.
        echo       [重试] 使用默认源安装...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo.
            echo [错误] 依赖安装失败，请检查网络连接后重试
            pause
            exit /b 1
        )
    )
    echo.
    echo       依赖安装完成！
) else (
    echo       后端依赖已就绪
)
echo.

:: ========== 第三步：配置 API Key ==========
echo [3/4] 配置检查...
cd /d "%SCRIPT_DIR%backend"

if not exist ".env" (
    echo.
    echo       首次运行，需要配置 DeepSeek API Key
    echo       ---------------------------------------------------------------
    echo       如果没有 API Key，请前往 https://platform.deepseek.com 注册获取
    echo       ---------------------------------------------------------------
    echo.
    set /p USER_API_KEY="请输入 DeepSeek API Key: "
    if "!USER_API_KEY!"=="" (
        echo.
        echo [警告] 未输入 API Key，将创建配置文件，请稍后手动编辑 backend\.env
        echo DEEPSEEK_API_KEY=请在此输入您的APIKey > ".env"
    ) else (
        echo DEEPSEEK_API_KEY=!USER_API_KEY! > ".env"
        echo       API Key 已保存
    )
) else (
    echo       配置文件已存在
)
echo.

:: 创建运行时目录
if not exist "outputs" mkdir "outputs"
if not exist "outputs\cases" mkdir "outputs\cases"
if not exist "uploads" mkdir "uploads"

:: ========== 第四步：启动服务 ==========
echo [4/4] 启动服务...
echo.
echo ========================================
echo    服务启动中，请稍候...
echo ========================================
echo.

:: 用 Python 直接启动
cd /d "%SCRIPT_DIR%backend"
start "" http://localhost:8002
python main.py

pause
