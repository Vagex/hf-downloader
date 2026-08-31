import os
import sys
import ctypes

# 🛡️ 彻底隐藏 CMD 控制台黑窗口 (Win32 SW_HIDE)
if sys.platform == "win32":
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules to register them with ModuleManager
import app.modules.downloader.module
import app.modules.media_tools.module
import app.modules.settings.module

from app.ui.main_window import MainWindow

def main():
    print("=======================================================")
    print(" 🌟 启动万能超级工具箱平台 (Universal Super App v2.0)")
    print("=======================================================")
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
