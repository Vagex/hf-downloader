@echo off
chcp 65001 >nul
title 🚀 一键发布项目到 Hugging Face
cd /d "%~dp0"
python publish_to_hf.py
pause
