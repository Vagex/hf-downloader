@echo off
chcp 65001 >nul
title AI 图像反推与精准 Prompt 工作台
echo ========================================================
echo   ⚡ 正在启动 AI 图像反推与精准 Prompt 提取系统...
echo   🎯 支持 7 大专业反推模式 (通用/字体Logo/风景/摄影/插画/3D/IP潮玩)
echo ========================================================
echo.

cd /d "%~dp0"

if not exist node_modules (
    echo [提示] 正在安装依赖包，请稍候...
    call npm install
)

if not exist dist (
    echo [提示] 正在构建前端资源...
    call npm run build
)

echo [提示] 启动本地服务并打开浏览器...
start http://localhost:3005

node server.js
pause
