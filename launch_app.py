import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

APP_DIR = os.path.dirname(os.path.abspath(__file__))
FLET_APP_SCRIPT = os.path.join(APP_DIR, "hf_downloader_flet.py")

REQUIRED_PACKAGES = ["flet", "requests"]

def is_env_ready():
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except Exception:
            return False
    return True

def run_flet_directly():
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    subprocess.Popen([sys.executable, FLET_APP_SCRIPT], creationflags=creationflags)
    sys.exit(0)

class PreLaunchInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🚀 Hugging Face 极速下载器 - 运行环境自动部署")
        self.geometry("520x360")
        self.resizable(False, False)
        
        # Center window
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"520x360+{(sw-520)//2}+{(sh-360)//2}")
        
        self.configure(bg="#18181b")
        self._build_ui()
        self.after(500, self.start_auto_install)

    def _build_ui(self):
        container = tk.Frame(self, bg="#18181b", padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        lbl_title = tk.Label(
            container, 
            text="🚀 正在为您自动安装并配置 Flet 极速运行环境",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg="#18181b", fg="#38bdf8"
        )
        lbl_title.pack(anchor=tk.W, pady=(0, 6))

        lbl_desc = tk.Label(
            container,
            text="检测到首次运行或环境缺失必要依赖，正在全自动下载部署中，请稍候...",
            font=("Microsoft YaHei UI", 9),
            bg="#18181b", fg="#a1a1aa"
        )
        lbl_desc.pack(anchor=tk.W, pady=(0, 12))

        self.progress = ttk.Progressbar(container, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(0, 10))
        self.progress.start(10)

        self.log_text = tk.Text(container, height=8, font=("Consolas", 9), bg="#09090b", fg="#e4e4e7", relief=tk.FLAT)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.lbl_status = tk.Label(container, text="状态: 正在连接国内镜像源并安装依赖...", font=("Microsoft YaHei UI", 9), bg="#18181b", fg="#4ade80")
        self.lbl_status.pack(anchor=tk.W)

    def log(self, text):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def start_auto_install(self):
        import threading
        def _worker():
            mirrors = [
                "https://pypi.org/simple",
                "https://pypi.tuna.tsinghua.edu.cn/simple",
                "https://mirrors.aliyun.com/pypi/simple/"
            ]
            
            success = False
            for m in mirrors:
                self.log(f"[*] 正在尝试安装: {', '.join(REQUIRED_PACKAGES)} -> 源: {m}")
                cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "-i", m] + REQUIRED_PACKAGES
                try:
                    proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                    for line in proc.stdout:
                        s = line.strip()
                        if s:
                            self.log(f"  {s}")
                    proc.wait()
                    if proc.returncode == 0:
                        success = True
                        break
                except Exception as err:
                    self.log(f"[!] 尝试出错: {err}")

            if success:
                self.log("\n[✓] 部署成功！正在为您拉起 Flet 极速客户端...")
                self.lbl_status.config(text="状态: 部署完成，正在启动...", fg="#22c55e")
                self.after(1000, self._launch_and_exit)
            else:
                self.log("\n[✗] 自动安装遇到问题，请检查网络后重试。")
                self.lbl_status.config(text="状态: 安装失败", fg="#ef4444")
                messagebox.showerror("安装失败", "自动部署依赖失败，请检查网络连接！")

        threading.Thread(target=_worker, daemon=True).start()

    def _launch_and_exit(self):
        self.destroy()
        run_flet_directly()

if __name__ == "__main__":
    if is_env_ready():
        run_flet_directly()
    else:
        app = PreLaunchInstaller()
        app.mainloop()
