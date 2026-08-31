@echo off
chcp 65001 >nul
title PromptHub - AI 灵感词舱

echo ===================================================
echo     PromptHub - 专属 AI Prompt 视觉管理系统
echo ===================================================
echo.
echo 正在检查并启动服务...
echo 本地访问地址: http://localhost:3000
echo 局域网/远程可通过本机 IP:3000 进行访问
echo.

cd /d "%~dp0"

REM Check if dist exists, if not build it
if not exist "dist" (
    echo 正在首次构建前端资源，请稍候...
    call npm run build
)

start http://localhost:3000
node server.js

pause
