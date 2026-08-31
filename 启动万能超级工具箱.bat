@echo off
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Python\pythoncore-3.14-64\pythonw.exe" main.pyw
    exit
)
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw main.pyw
    exit
)
start "" python main.py
exit
