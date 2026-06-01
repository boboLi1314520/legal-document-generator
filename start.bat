@echo off
echo ========================================
echo 法律文书自动生成系统 - 启动脚本
echo ========================================

echo.
echo [1] 启动后端服务 (FastAPI)...
cd /d %~dp0backend
start "Backend" cmd /k "python main.py"

timeout /t 3 /nobreak >nul

echo.
echo [2] 启动前端服务 (Vue)...
cd /d %~dp0frontend
start "Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo 服务已启动！
echo 前端地址: http://localhost:3000
echo 后端地址: http://localhost:8002
echo ========================================
pause
