@echo off
chcp 65001 >nul
title 法律文书自动生成系统

echo ========================================
echo    法律文书自动生成系统 - 开发者启动器
echo ========================================
echo.
echo    给同事/客户使用？直接用"启动.bat"即可（仅需Python，无需Node.js）
echo.

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js 18+
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] 检查后端依赖...
cd /d "%SCRIPT_DIR%backend"
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo     安装后端依赖中...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo [错误] 后端依赖安装失败
        pause
        exit /b 1
    )
)
echo     后端依赖就绪

echo.
echo [2/4] 检查前端依赖...
cd /d "%SCRIPT_DIR%frontend"
if not exist "node_modules" (
    echo     安装前端依赖中...
    npm install --silent
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败
        pause
        exit /b 1
    )
)
echo     前端依赖就绪

echo.
echo [3/4] 配置检查...
if not exist "%SCRIPT_DIR%backend\.env" (
    echo     首次运行，请配置 API Key...
    echo     请编辑 backend\.env 文件，输入您的 DeepSeek API Key
    echo DEEPSEEK_API_KEY=您的key > "%SCRIPT_DIR%backend\.env"
    start notepad "%SCRIPT_DIR%backend\.env"
    echo.
    set /p API_KEY="请输入 DeepSeek API Key: "
    if not "%API_KEY%"=="" (
        echo DEEPSEEK_API_KEY=%API_KEY% > "%SCRIPT_DIR%backend\.env"
    )
)

echo.
echo [4/4] 启动服务...

:: 启动后端
start "后端服务" cmd /k "cd /d %SCRIPT_DIR%backend && python main.py"
timeout /t 3 /nobreak >nul

:: 启动前端
start "前端服务" cmd /k "cd /d %SCRIPT_DIR%frontend && npm run dev"

:: 等待服务启动
echo.
echo 正在启动服务，请稍候...
timeout /t 5 /nobreak >nul

:: 检查服务状态
curl -s http://localhost:8002/api/status >nul 2>&1
if errorlevel 1 (
    echo.
    echo [警告] 后端服务启动可能有问题，请检查窗口
)

echo.
echo ========================================
echo    启动完成！
echo ========================================
echo.
echo   前端地址: http://localhost:3000
echo   后端地址: http://localhost:8002
echo.
echo   关闭此窗口不会停止服务
echo   如需停止服务，请关闭 "后端服务" 和 "前端服务" 窗口
echo ========================================
echo.

:: 打开浏览器
start http://localhost:3000

pause
