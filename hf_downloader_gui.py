import os
import sys
import time
import json
import datetime
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional, Dict, Any, Tuple, Set

# Set default mirror before other HF imports
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import requests
from PIL import Image, ImageDraw, ImageTk

try:
    from huggingface_hub import HfApi
except ImportError:
    HfApi = None

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DB_FILE = os.path.join(CONFIG_DIR, "hf_download_tasks.json")
LOCK_FILE = os.path.join(CONFIG_DIR, "hf_downloader_active.lock")
MIRRORS_CONFIG_FILE = os.path.join(CONFIG_DIR, "hf_downloader_mirrors.json")
PROXIES_CONFIG_FILE = os.path.join(CONFIG_DIR, "hf_downloader_proxies.json")
APP_CONFIG_FILE = os.path.join(CONFIG_DIR, "hf_downloader_settings.json")

# Default Mirror Endpoints
DEFAULT_MIRRORS = [
    "https://hf-mirror.com",
    "https://huggingface.co"
]

# Default Common Proxies
DEFAULT_PROXIES = [
    "不使用代理 (直连)",
    "http://127.0.0.1:7890",
    "http://127.0.0.1:10809",
    "http://127.0.0.1:1080",
    "socks5://127.0.0.1:7890",
    "socks5://127.0.0.1:10808"
]

# Common PyPI Mirrors for fast environment setup
PYPI_MIRRORS = {
    "清华大学镜像源 (推荐)": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "阿里云镜像源": "https://mirrors.aliyun.com/pypi/simple/",
    "腾讯云镜像源": "https://mirrors.cloud.tencent.com/pypi/simple/",
    "官方官方源 (PyPI.org)": "https://pypi.org/simple"
}

# Core packages needed for optimal download experience
CORE_PACKAGES = [
    ("huggingface_hub", "Hugging Face 官方核心客户端与 CLI 命令行工具"),
    ("hf_transfer", "HF 官方 Rust 极速并发下载引擎 (速度提升数倍)"),
    ("requests", "网络通信与大文件流式断点续传引擎"),
    ("PySocks", "SOCKS5 / SOCKS4 高级代理协议支持"),
    ("tqdm", "高精度终端与图形下载进度指示器"),
    ("certifi", "Mozilla CA 根证书集 (保障 SSL/TLS 下载安全)")
]

# Global Font Settings (Enlarged and Clear)
FONT_FAMILY = "Microsoft YaHei UI" if sys.platform == "win32" else "Segoe UI"
FONT_NORMAL = (FONT_FAMILY, 10)
FONT_BOLD = (FONT_FAMILY, 10, "bold")
FONT_TITLE = (FONT_FAMILY, 10, "bold")
FONT_TABLE = (FONT_FAMILY, 10)
FONT_TABLE_BOLD = (FONT_FAMILY, 10, "bold")
FONT_CHECKBOX = (FONT_FAMILY, 11, "bold")
FONT_LOG = ("Consolas", 10)
FONT_SMALL = (FONT_FAMILY, 9)

# Default GitHub Accelerators (High-speed reverse proxies)
DEFAULT_GITHUB_ACCELERATORS = [
    "https://ghproxy.net/",
    "https://github.moeyy.xyz/",
    "https://mirror.ghproxy.com/",
    "https://ghfast.top/",
    "不使用加速 (官方直连)"
]

# Preset Directory Mappings: Display Label -> Absolute Path
DEFAULT_COMFYUI_ROOT = r"F:\ComfyUI-aki-v3\ComfyUI\models"
DEFAULT_CUSTOM_NODES_DIR = os.path.normpath(os.path.join(DEFAULT_COMFYUI_ROOT, "..", "custom_nodes"))
PRESET_DIRS_MAP = {
    "🧩 ComfyUI 插件目录 (custom_nodes)": DEFAULT_CUSTOM_NODES_DIR,
    "🎨 扩散模型 (diffusion_models)": os.path.join(DEFAULT_COMFYUI_ROOT, "diffusion_models"),
    "🎮 控制网络 (controlnet)": os.path.join(DEFAULT_COMFYUI_ROOT, "controlnet"),
    "💾 大模型底模 (checkpoints)": os.path.join(DEFAULT_COMFYUI_ROOT, "checkpoints"),
    "⚡ 微调模型 (loras)": os.path.join(DEFAULT_COMFYUI_ROOT, "loras"),
    "🔍 变分自编码 (vae)": os.path.join(DEFAULT_COMFYUI_ROOT, "vae"),
    "🧠 UNet 主干 (unet)": os.path.join(DEFAULT_COMFYUI_ROOT, "unet"),
    "🔤 文本编码器 (clip)": os.path.join(DEFAULT_COMFYUI_ROOT, "clip"),
}


class ColorIconFactory:
    """Generates high-definition, anti-aliased 32-bit RGBA full-color icons directly in memory."""
    @staticmethod
    def get_all_icons() -> Dict[str, ImageTk.PhotoImage]:
        icons_pil = {}

        # 1. Eye Open (Vibrant Ocean Blue Eye with Sclera and Highlights)
        img_eye = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_eye)
        d.pieslice([1, 2, 16, 15], 25, 155, fill="#ffffff", outline="#64748b", width=1)
        d.pieslice([1, 2, 16, 15], 205, 335, fill="#ffffff", outline="#64748b", width=1)
        d.ellipse([5, 5, 12, 12], fill="#0284c7", outline="#0369a1")
        d.ellipse([7, 7, 10, 10], fill="#0f172a")
        d.ellipse([6, 6, 7, 7], fill="#ffffff")
        icons_pil["eye_open"] = img_eye

        # 2. Eye Lock (Vibrant Golden Brass Lock)
        img_lock = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_lock)
        d.arc([4, 1, 13, 11], 180, 0, fill="#94a3b8", width=2)
        d.rounded_rectangle([3, 7, 14, 16], radius=2, fill="#eab308", outline="#ca8a04", width=1)
        d.ellipse([7, 9, 10, 12], fill="#451a03")
        d.line([8, 11, 8, 14], fill="#451a03", width=1)
        icons_pil["eye_lock"] = img_lock

        # 3. Rocket (Vibrant Red & Orange Fire Engine)
        img_rocket = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_rocket)
        d.polygon([(4, 14), (2, 17), (7, 15)], fill="#f97316")
        d.polygon([(3, 15), (1, 18), (5, 16)], fill="#ef4444")
        d.polygon([(15, 2), (16, 3), (12, 11), (7, 12)], fill="#3b82f6")
        d.polygon([(15, 2), (16, 3), (10, 8)], fill="#ef4444")
        d.polygon([(6, 13), (4, 16), (9, 14)], fill="#dc2626")
        d.polygon([(13, 6), (16, 4), (14, 9)], fill="#dc2626")
        d.ellipse([10, 5, 12, 7], fill="#ffffff", outline="#1d4ed8")
        icons_pil["rocket"] = img_rocket

        # 4. Search (Deep Blue Magnifier with Glare)
        img_search = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_search)
        d.ellipse([2, 2, 12, 12], fill="#e0f2fe", outline="#0284c7", width=2)
        d.ellipse([4, 4, 7, 7], fill="#bae6fd")
        d.line([11, 11, 16, 16], fill="#d97706", width=3)
        d.line([11, 11, 16, 16], fill="#78350f", width=1)
        icons_pil["search"] = img_search

        # 5. Globe / Mirror (Cyan Planet with Longitude Grids)
        img_globe = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_globe)
        d.ellipse([1, 1, 16, 16], fill="#0284c7", outline="#0369a1")
        d.ellipse([4, 1, 13, 16], outline="#bae6fd", width=1)
        d.line([1, 8, 16, 8], fill="#bae6fd", width=1)
        d.line([3, 4, 14, 4], fill="#bae6fd", width=1)
        d.line([3, 12, 14, 12], fill="#bae6fd", width=1)
        icons_pil["globe"] = img_globe

        # 6. Shield / Proxy (Emerald Guard Shield)
        img_shield = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_shield)
        d.polygon([(9, 1), (15, 3), (15, 9), (9, 16), (3, 9), (3, 3)], fill="#10b981", outline="#047857", width=1)
        d.polygon([(9, 3), (13, 5), (13, 9), (9, 14), (9, 3)], fill="#34d399")
        icons_pil["shield"] = img_shield

        # 7. Lightning / Test (Golden Electric Bolt)
        img_bolt = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_bolt)
        d.polygon([(11, 1), (4, 9), (8, 9), (6, 17), (14, 8), (10, 8)], fill="#eab308", outline="#ca8a04", width=1)
        icons_pil["bolt"] = img_bolt

        # 8. Folder (Warm Amber Gold Folder)
        img_folder = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_folder)
        d.polygon([(2, 3), (7, 3), (9, 5), (15, 5), (15, 14), (2, 14)], fill="#f59e0b", outline="#d97706", width=1)
        d.rectangle([2, 6, 15, 14], fill="#fbbf24", outline="#d97706", width=1)
        icons_pil["folder"] = img_folder

        # 9. Download (Vibrant Green Down Arrow)
        img_dl = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_dl)
        d.rectangle([7, 1, 10, 8], fill="#22c55e", outline="#16a34a")
        d.polygon([(4, 8), (13, 8), (8, 13)], fill="#22c55e", outline="#16a34a")
        d.rectangle([2, 14, 15, 16], fill="#16a34a")
        icons_pil["download"] = img_dl

        # 10. Play (Emerald Green Triangle)
        img_play = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_play)
        d.polygon([(4, 2), (15, 9), (4, 16)], fill="#22c55e", outline="#16a34a")
        icons_pil["play"] = img_play

        # 11. Pause (Amber Pause Bars)
        img_pause = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_pause)
        d.rounded_rectangle([4, 2, 7, 15], radius=1, fill="#f59e0b", outline="#d97706")
        d.rounded_rectangle([10, 2, 13, 15], radius=1, fill="#f59e0b", outline="#d97706")
        icons_pil["pause"] = img_pause

        # 12. Trash (Crimson Red Bin)
        img_trash = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_trash)
        d.rectangle([5, 1, 12, 3], fill="#ef4444")
        d.rectangle([3, 3, 14, 5], fill="#dc2626")
        d.polygon([(4, 5), (13, 5), (12, 16), (5, 16)], fill="#ef4444", outline="#b91c1c")
        d.line([7, 7, 7, 14], fill="#ffffff", width=1)
        d.line([10, 7, 10, 14], fill="#ffffff", width=1)
        icons_pil["trash"] = img_trash

        # 13. Clean / Sparkles (Cyan / Gold Stars)
        img_clean = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_clean)
        d.polygon([(8, 1), (10, 6), (15, 8), (10, 10), (8, 15), (6, 10), (1, 8), (6, 6)], fill="#38bdf8", outline="#0284c7")
        d.polygon([(14, 1), (15, 3), (17, 4), (15, 5), (14, 7), (13, 5), (11, 4), (13, 3)], fill="#fbbf24")
        icons_pil["clean"] = img_clean

        # Convert all to ImageTk.PhotoImage
        icons_tk = {}
        for k, v in icons_pil.items():
            icons_tk[k] = ImageTk.PhotoImage(v)

        return icons_tk


class ToolTip:
    """Creates a floating tooltip for a widget on hover."""
    def __init__(self, widget, text_provider):
        self.widget = widget
        self.text_provider = text_provider
        self.tip_window = None
        self.after_id = None
        self.widget.bind("<Enter>", self._schedule_tip)
        self.widget.bind("<Leave>", self._hide_tip)
        self.widget.bind("<ButtonPress>", self._hide_tip)

    def _schedule_tip(self, event=None):
        self._unschedule()
        self.after_id = self.widget.after(350, self._show_tip)

    def _unschedule(self):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

    def _show_tip(self):
        text = self.text_provider() if callable(self.text_provider) else self.text_provider
        if not text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)

        label = tk.Label(
            tw, text=text, justify=tk.LEFT,
            background="#212529", foreground="#ffffff",
            relief=tk.SOLID, borderwidth=1,
            font=(FONT_FAMILY, 9), padx=10, pady=5
        )
        label.pack(ipadx=1)

    def _hide_tip(self, event=None):
        self._unschedule()
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class ComboboxItemToolTip:
    """Provides real-time floating tooltip when hovering over individual items inside a ttk.Combobox drop-down list."""
    def __init__(self, combobox: ttk.Combobox, label_to_path_map: Dict[str, str]):
        self.combobox = combobox
        self.label_to_path_map = label_to_path_map
        self.tip_window = None
        self.last_index = None

        self.combobox.bind("<Button-1>", self._on_combobox_open, add="+")
        self.combobox.bind("<Down>", self._on_combobox_open, add="+")
        ToolTip(self.combobox, self._get_current_tip_text)

    def _get_current_tip_text(self) -> str:
        val = self.combobox.get()
        if val in self.label_to_path_map:
            return f"📂 {val}\n对应保存全路径:\n{self.label_to_path_map[val]}"
        return "点击选择常用的模型分类保存预设目录"

    def _on_combobox_open(self, event=None):
        self.combobox.after(100, self._bind_popdown_listbox)

    def _bind_popdown_listbox(self):
        try:
            popdown_name = self.combobox.tk.eval(f"ttk::combobox::PopdownWindow {self.combobox}")
            listbox_widget = self.combobox._nametowidget(f"{popdown_name}.f.l")
            
            listbox_widget.bind("<Motion>", self._on_listbox_motion)
            listbox_widget.bind("<Leave>", self._hide_tip)
            listbox_widget.bind("<ButtonRelease-1>", self._hide_tip)
        except Exception:
            pass

    def _on_listbox_motion(self, event):
        listbox = event.widget
        index = listbox.nearest(event.y)
        if index is not None and index >= 0:
            if index != self.last_index:
                self.last_index = index
                item_label = listbox.get(index)
                real_path = self.label_to_path_map.get(item_label, item_label)
                self._schedule_show(event.x_root + 18, event.y_root + 12, item_label, real_path)

    def _schedule_show(self, x, y, label_text, path_text):
        self._hide_tip()
        if not label_text or label_text.startswith("--"):
            return
        
        self.tip_window = tw = tk.Toplevel(self.combobox)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)

        tip_msg = f"📁 分类: {label_text}\n────────────────────────\n💾 完整目标路径:\n{path_text}"

        label = tk.Label(
            tw, text=tip_msg, justify=tk.LEFT,
            background="#1e293b", foreground="#f8fafc",
            relief=tk.SOLID, borderwidth=1,
            font=(FONT_FAMILY, 9), padx=10, pady=6
        )
        label.pack()

    def _hide_tip(self, event=None):
        self.last_index = None
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except:
                pass
            self.tip_window = None


class EnvironmentSetupDialog(tk.Toplevel):
    """Modal dialog to inspect, auto-install, and deploy download dependencies like huggingface_hub, hf_transfer, requests, etc."""
    def __init__(self, parent, on_complete_callback=None):
        super().__init__(parent)
        self.title("🚀 运行环境与加速组件一键部署")
        self.geometry("720x560")
        self.minsize(620, 460)
        self.transient(parent)
        self.grab_set()

        self.parent = parent
        self.on_complete_callback = on_complete_callback
        self.is_installing = False

        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - 720) // 2
        y = parent_y + (parent_h - 560) // 2
        self.geometry(f"+{max(50, x)}+{max(50, y)}")

        self._build_ui()
        self._check_all_env_status()

    def _build_ui(self):
        frame = ttk.Frame(self, padding="14")
        frame.pack(fill=tk.BOTH, expand=True)

        # 1. Header info
        hdr_frame = ttk.Frame(frame)
        hdr_frame.pack(fill=tk.X, pady=(0, 10))

        lbl_title = ttk.Label(hdr_frame, text="🚀 Python 运行环境与 HuggingFace 下载组件部署", font=(FONT_FAMILY, 11, "bold"), foreground="#0d6efd")
        lbl_title.pack(anchor=tk.W)

        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        lbl_sub = ttk.Label(hdr_frame, text=f"当前解释器: {sys.executable} (Python {py_ver})", font=FONT_SMALL, foreground="#555555")
        lbl_sub.pack(anchor=tk.W, pady=(2, 0))

        # 2. Package Status Tree
        status_box = ttk.LabelFrame(frame, text=" 📦 核心依赖组件检测状态 ", padding="8")
        status_box.pack(fill=tk.X, pady=(0, 10))

        cols = ("pkg", "status", "version", "desc")
        self.tree_pkgs = ttk.Treeview(status_box, columns=cols, show="headings", height=6)
        self.tree_pkgs.heading("pkg", text="组件名称", anchor=tk.W)
        self.tree_pkgs.heading("status", text="安装状态", anchor=tk.CENTER)
        self.tree_pkgs.heading("version", text="当前版本", anchor=tk.CENTER)
        self.tree_pkgs.heading("desc", text="组件说明与作用", anchor=tk.W)

        self.tree_pkgs.column("pkg", width=140, minwidth=110, stretch=False, anchor=tk.W)
        self.tree_pkgs.column("status", width=95, minwidth=80, stretch=False, anchor=tk.CENTER)
        self.tree_pkgs.column("version", width=95, minwidth=75, stretch=False, anchor=tk.CENTER)
        self.tree_pkgs.column("desc", width=330, minwidth=180, stretch=True, anchor=tk.W)

        self.tree_pkgs.tag_configure("ok_tag", foreground="#198754", font=FONT_TABLE_BOLD)
        self.tree_pkgs.tag_configure("missing_tag", foreground="#dc3545", font=FONT_TABLE_BOLD)

        self.tree_pkgs.pack(fill=tk.X, expand=True)

        # 3. Mirror selection & Action Bar
        opt_frame = ttk.Frame(frame)
        opt_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(opt_frame, text="⚡ PyPI 加速下载源:").pack(side=tk.LEFT, padx=(0, 4))
        self.pypi_mirror_var = tk.StringVar(value=list(PYPI_MIRRORS.keys())[0])
        pypi_combo = ttk.Combobox(opt_frame, textvariable=self.pypi_mirror_var, values=list(PYPI_MIRRORS.keys()), width=24, state="readonly", font=FONT_NORMAL)
        pypi_combo.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_install_all = tk.Button(
            opt_frame,
            text="🚀 一键自动下载并安装部署全部依赖",
            font=FONT_BOLD,
            bg="#0d6efd",
            fg="#ffffff",
            activebackground="#0b5ed7",
            activeforeground="#ffffff",
            padx=12, pady=4,
            command=self.install_all_dependencies
        )
        self.btn_install_all.pack(side=tk.LEFT, padx=4)

        btn_recheck = ttk.Button(opt_frame, text="🔄 刷新检测", command=self._check_all_env_status)
        btn_recheck.pack(side=tk.RIGHT, padx=2)

        # 4. Realtime Console Log output
        log_box = ttk.LabelFrame(frame, text=" 📜 实时安装与部署终端日志 ", padding="6")
        log_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.log_text = tk.Text(log_box, font=FONT_LOG, bg="#1e1e1e", fg="#d4d4d4", wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(log_box, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 5. Bottom Close
        btn_close = ttk.Button(frame, text="关闭窗口", command=self.destroy)
        btn_close.pack(anchor=tk.E)

    def _log(self, text: str):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def _check_all_env_status(self):
        self.tree_pkgs.delete(*self.tree_pkgs.get_children())
        
        import importlib.metadata

        missing_count = 0
        for pkg_name, desc in CORE_PACKAGES:
            norm_name = pkg_name.replace("_", "-")
            version = None
            try:
                version = importlib.metadata.version(norm_name)
            except Exception:
                try:
                    version = importlib.metadata.version(pkg_name)
                except Exception:
                    pass

            if version:
                status_str = "✅ 已就绪"
                tag = "ok_tag"
                ver_str = f"v{version}"
            else:
                status_str = "❌ 未安装"
                tag = "missing_tag"
                ver_str = "--"
                missing_count += 1

            self.tree_pkgs.insert("", tk.END, values=(pkg_name, status_str, ver_str, desc), tags=(tag,))

        if missing_count == 0:
            self._log("[✓] 依赖检测完成：所有核心组件均已安装就绪，可全速稳定下载！")
        else:
            self._log(f"[!] 依赖检测提示：发现 {missing_count} 个未安装的加速/支持组件，点击上方【🚀 一键自动下载并安装部署全部依赖】即可一键自动补全。")

    def install_all_dependencies(self):
        if self.is_installing:
            return
        
        mirror_label = self.pypi_mirror_var.get()
        mirror_url = PYPI_MIRRORS.get(mirror_label, "https://pypi.tuna.tsinghua.edu.cn/simple")
        host = mirror_url.split("//")[-1].split("/")[0]

        pkg_list = [p[0] for p in CORE_PACKAGES]

        self.is_installing = True
        self.btn_install_all.config(state=tk.DISABLED, text="⏳ 正在下载并安装依赖中...")
        self._log(f"\n================ 开始自动下载并部署环境依赖 ================")
        self._log(f"[*] 使用加速镜像源: {mirror_url}")
        self._log(f"[*] 准备安装组件: {', '.join(pkg_list)}")

        def _worker():
            cmd = [
                sys.executable, "-m", "pip", "install", "--upgrade",
                "-i", mirror_url,
                "--trusted-host", host
            ] + pkg_list

            self.after(0, lambda: self._log(f"[*] 执行命令: {' '.join(cmd)}\n"))

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
                    line_str = line.rstrip()
                    if line_str:
                        self.after(0, lambda s=line_str: self._log(f"  {s}"))

                proc.wait()

                if proc.returncode == 0:
                    self.after(0, lambda: self._log("\n[✓] 恭喜！所有核心依赖组件已全部自动安装并部署成功！"))
                    self.after(0, lambda: messagebox.showinfo("部署成功", "所有核心依赖组件（含 huggingface_hub, hf_transfer, requests 等）已全部成功安装部署！"))
                    if self.on_complete_callback:
                        self.after(0, self.on_complete_callback)
                else:
                    self.after(0, lambda: self._log(f"\n[✗] 安装过程返回异常代码: {proc.returncode}，请检查网络或切换镜像源后重试。"))
                    self.after(0, lambda: messagebox.showerror("安装遇到问题", f"依赖安装未完全成功 (Code {proc.returncode})，请尝试切换上方不同的 PyPI 镜像源后重试。"))
            except Exception as e:
                self.after(0, lambda: self._log(f"\n[✗] 执行安装失败: {str(e)}"))
                self.after(0, lambda: messagebox.showerror("错误", f"启动安装进程失败: {str(e)}"))

            self.after(0, self._check_all_env_status)
            self.after(0, lambda: self.btn_install_all.config(state=tk.NORMAL, text="🚀 一键自动下载并安装部署全部依赖"))
            self.is_installing = False

        threading.Thread(target=_worker, daemon=True).start()


class MirrorManagerDialog(tk.Toplevel):
    """Modal dialog to add, view, and remove persistent custom HF mirror endpoints."""
    def __init__(self, parent, current_mirrors: List[str], on_update_callback):
        super().__init__(parent)
        self.title("🌐 下载镜像加速源管理")
        self.geometry("560x420")
        self.minsize(480, 360)
        self.transient(parent)
        self.grab_set()

        self.mirrors = list(current_mirrors)
        self.on_update_callback = on_update_callback

        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - 560) // 2
        y = parent_y + (parent_h - 420) // 2
        self.geometry(f"+{max(50, x)}+{max(50, y)}")

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self, padding="12")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="🌐 已保存的镜像加速源列表:", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 6))

        list_container = ttk.Frame(frame)
        list_container.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.listbox = tk.Listbox(list_container, font=FONT_NORMAL, selectmode=tk.SINGLE, height=7)
        list_scroll = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=list_scroll.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._refresh_listbox()

        add_frame = ttk.LabelFrame(frame, text=" ➕ 添加新的镜像源地址 ", padding="8")
        add_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(add_frame, text="URL:").pack(side=tk.LEFT, padx=(0, 4))
        self.new_mirror_var = tk.StringVar()
        self.entry_new = ttk.Entry(add_frame, textvariable=self.new_mirror_var, font=FONT_NORMAL)
        self.entry_new.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.entry_new.bind("<Return>", lambda e: self.add_mirror())

        btn_add = ttk.Button(add_frame, text="➕ 添加并保存", command=self.add_mirror)
        btn_add.pack(side=tk.RIGHT, padx=2)

        btn_box = ttk.Frame(frame)
        btn_box.pack(fill=tk.X)

        btn_del = ttk.Button(btn_box, text="🗑️ 删除选中项", command=self.delete_selected_mirror)
        btn_del.pack(side=tk.LEFT, padx=2)

        btn_reset = ttk.Button(btn_box, text="↺ 恢复默认源", command=self.reset_default_mirrors)
        btn_reset.pack(side=tk.LEFT, padx=6)

        btn_close = ttk.Button(btn_box, text="关闭完成", command=self.destroy)
        btn_close.pack(side=tk.RIGHT, padx=2)

    def _refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for m in self.mirrors:
            self.listbox.insert(tk.END, m)

    def add_mirror(self):
        url = self.new_mirror_var.get().strip().rstrip("/")
        if not url:
            messagebox.showwarning("提示", "请输入镜像源 URL 地址！")
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url

        if url in self.mirrors:
            messagebox.showinfo("提示", "该镜像源已在列表中。")
            return

        self.mirrors.append(url)
        self._refresh_listbox()
        self.new_mirror_var.set("")
        self.on_update_callback(self.mirrors, selected=url)

    def delete_selected_mirror(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("提示", "请在上方列表中先选择要删除的镜像源。")
            return
        idx = sel[0]
        url = self.mirrors[idx]

        if messagebox.askyesno("确认删除", f"确定要永久删除以下镜像源吗？\n{url}"):
            self.mirrors.pop(idx)
            self._refresh_listbox()
            self.on_update_callback(self.mirrors)

    def reset_default_mirrors(self):
        if messagebox.askyesno("恢复默认", "确定要恢复为官方默认镜像源列表吗？"):
            self.mirrors = list(DEFAULT_MIRRORS)
            self._refresh_listbox()
            self.on_update_callback(self.mirrors)


class ProxyManagerDialog(tk.Toplevel):
    """Modal dialog to add, view, and remove persistent custom network proxies."""
    def __init__(self, parent, current_proxies: List[str], on_update_callback):
        super().__init__(parent)
        self.title("🛡️ 网络代理 (Proxy) 管理与配置")
        self.geometry("560x430")
        self.minsize(480, 360)
        self.transient(parent)
        self.grab_set()

        self.proxies = list(current_proxies)
        self.on_update_callback = on_update_callback

        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - 560) // 2
        y = parent_y + (parent_h - 430) // 2
        self.geometry(f"+{max(50, x)}+{max(50, y)}")

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self, padding="12")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="🛡️ 已保存的网络代理列表 (支持 HTTP / SOCKS5):", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 6))

        list_container = ttk.Frame(frame)
        list_container.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.listbox = tk.Listbox(list_container, font=FONT_NORMAL, selectmode=tk.SINGLE, height=7)
        list_scroll = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=list_scroll.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._refresh_listbox()

        add_frame = ttk.LabelFrame(frame, text=" ➕ 添加新的代理地址 (例: http://127.0.0.1:7890) ", padding="8")
        add_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(add_frame, text="代理地址:").pack(side=tk.LEFT, padx=(0, 4))
        self.new_proxy_var = tk.StringVar()
        self.entry_new = ttk.Entry(add_frame, textvariable=self.new_proxy_var, font=FONT_NORMAL)
        self.entry_new.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.entry_new.bind("<Return>", lambda e: self.add_proxy())

        btn_add = ttk.Button(add_frame, text="➕ 添加并保存", command=self.add_proxy)
        btn_add.pack(side=tk.RIGHT, padx=2)

        btn_box = ttk.Frame(frame)
        btn_box.pack(fill=tk.X)

        btn_del = ttk.Button(btn_box, text="🗑️ 删除选中项", command=self.delete_selected_proxy)
        btn_del.pack(side=tk.LEFT, padx=2)

        btn_reset = ttk.Button(btn_box, text="↺ 恢复默认常用代理", command=self.reset_default_proxies)
        btn_reset.pack(side=tk.LEFT, padx=6)

        btn_close = ttk.Button(btn_box, text="关闭完成", command=self.destroy)
        btn_close.pack(side=tk.RIGHT, padx=2)

    def _refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for p in self.proxies:
            self.listbox.insert(tk.END, p)

    def add_proxy(self):
        raw = self.new_proxy_var.get().strip().rstrip("/")
        if not raw:
            messagebox.showwarning("提示", "请输入代理地址！")
            return

        if "直连" not in raw and not (raw.startswith("http://") or raw.startswith("https://") or raw.startswith("socks5://") or raw.startswith("socks5h://")):
            raw = "http://" + raw

        if raw in self.proxies:
            messagebox.showinfo("提示", "该代理地址已在列表中。")
            return

        self.proxies.append(raw)
        self._refresh_listbox()
        self.new_proxy_var.set("")
        self.on_update_callback(self.proxies, selected=raw)

    def delete_selected_proxy(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("提示", "请在上方列表中先选择要删除的代理。")
            return
        idx = sel[0]
        val = self.proxies[idx]

        if "不使用代理" in val or "直连" in val:
            messagebox.showwarning("提示", "【不使用代理 (直连)】为核心基础项，不可删除。")
            return

        if messagebox.askyesno("确认删除", f"确定要永久删除以下代理地址吗？\n{val}"):
            self.proxies.pop(idx)
            self._refresh_listbox()
            self.on_update_callback(self.proxies)

    def reset_default_proxies(self):
        if messagebox.askyesno("恢复默认", "确定要恢复为默认常用代理列表吗？"):
            self.proxies = list(DEFAULT_PROXIES)
            self._refresh_listbox()
            self.on_update_callback(self.proxies)


class DeleteConfirmDialog(tk.Toplevel):
    """Custom modal dialog allowing user to choose deletion scope: queue only vs file+cache deletion."""
    def __init__(self, parent, task_count: int, file_names: List[str]):
        super().__init__(parent)
        self.title("⚠️ 确认移除下载任务")
        self.geometry("520x330")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result: Optional[str] = None

        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - 520) // 2
        y = parent_y + (parent_h - 330) // 2
        self.geometry(f"+{max(50, x)}+{max(50, y)}")

        self._build_ui(task_count, file_names)

    def _build_ui(self, task_count: int, file_names: List[str]):
        frame = ttk.Frame(self, padding="16")
        frame.pack(fill=tk.BOTH, expand=True)

        lbl_title = ttk.Label(
            frame, 
            text=f"⚠️ 准备从队列中移除 {task_count} 个任务", 
            font=(FONT_FAMILY, 11, "bold"),
            foreground="#d9534f"
        )
        lbl_title.pack(anchor=tk.W, pady=(0, 6))

        lbl_desc = ttk.Label(
            frame,
            text="请选择移除方式：\n如果任务未完成或已中断，建议彻底清理缓存，避免下次下载发生冲突。",
            font=FONT_NORMAL
        )
        lbl_desc.pack(anchor=tk.W, pady=(0, 8))

        preview_frame = ttk.LabelFrame(frame, text=" 📄 涉及的文件列表 ", padding="4")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        preview_text = tk.Text(preview_frame, height=4, font=FONT_SMALL, wrap=tk.NONE)
        preview_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=preview_text.yview)
        preview_text.configure(yscrollcommand=preview_scroll.set)

        for name in file_names:
            preview_text.insert(tk.END, f"• {name}\n")
        preview_text.config(state=tk.DISABLED)

        preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        btn_box = ttk.Frame(frame)
        btn_box.pack(fill=tk.X, pady=(4, 0))

        btn_delete_all = tk.Button(
            btn_box, 
            text="🗑️ 彻底删除 (移除任务 + 清理本地文件及缓存)", 
            font=FONT_BOLD,
            bg="#dc3545", 
            fg="#ffffff", 
            activebackground="#bb2d3b", 
            activeforeground="#ffffff",
            relief=tk.RAISED,
            padx=10, pady=4,
            command=self._choose_delete_all
        )
        btn_delete_all.pack(side=tk.LEFT, padx=(0, 6))

        btn_queue_only = ttk.Button(
            btn_box, 
            text="📋 仅移除任务 (保留本地文件)", 
            command=self._choose_queue_only
        )
        btn_queue_only.pack(side=tk.LEFT, padx=4)

        btn_cancel = ttk.Button(
            btn_box, 
            text="取消", 
            command=self.destroy
        )
        btn_cancel.pack(side=tk.RIGHT, padx=2)

    def _choose_delete_all(self):
        self.result = "delete_all"
        self.destroy()

    def _choose_queue_only(self):
        self.result = "queue_only"
        self.destroy()


class QueueTask:
    def __init__(self, task_id: int, repo_id: str, repo_type: str, branch: str, 
                 file_path: str, size_str: str, date_str: str, dest_dir: str, flatten: bool, 
                 endpoint: str, token: Optional[str], proxy: Optional[str] = None, 
                 status: str = "等待中", progress: float = 0.0, total_bytes: Optional[int] = None,
                 platform: str = "hf", direct_url: Optional[str] = None):
        self.task_id = task_id
        self.repo_id = repo_id
        self.repo_type = repo_type
        self.branch = branch
        self.file_path = file_path
        self.size_str = size_str
        self.date_str = date_str
        self.dest_dir = dest_dir
        self.flatten = flatten
        self.endpoint = endpoint
        self.token = token
        self.proxy = proxy
        self.platform = platform
        self.direct_url = direct_url
        
        self.status = status
        self.progress = progress
        self.speed_str = "--"
        self.error_msg = ""
        self.total_bytes = total_bytes

    def get_dest_file_path(self) -> str:
        if self.flatten:
            return os.path.join(self.dest_dir, os.path.basename(self.file_path))
        return os.path.join(self.dest_dir, os.path.normpath(self.file_path))

    def get_temp_file_path(self) -> str:
        return self.get_dest_file_path() + ".downloading"

    def check_local_status(self):
        dest_file = self.get_dest_file_path()
        temp_file = self.get_temp_file_path()

        if os.path.exists(dest_file):
            size = os.path.getsize(dest_file)
            self.status = "已完成"
            self.progress = 100.0
            if not self.total_bytes or self.total_bytes == 0:
                self.total_bytes = size
            return

        if os.path.exists(temp_file):
            temp_size = os.path.getsize(temp_file)
            if self.total_bytes and self.total_bytes > 0:
                self.progress = min(99.9, (temp_size / self.total_bytes) * 100.0)
            self.status = "已中断"
            return

        if self.status not in ("已完成", "下载中"):
            self.status = "等待中"
            self.progress = 0.0

    def clean_local_files_and_caches(self) -> List[str]:
        deleted_paths = []
        dest_file = self.get_dest_file_path()
        temp_file = self.get_temp_file_path()
        
        candidates = [
            dest_file,
            temp_file,
            dest_file + ".tmp",
            dest_file + ".part"
        ]

        for p in candidates:
            if os.path.exists(p):
                try:
                    os.remove(p)
                    deleted_paths.append(p)
                except Exception:
                    pass
        return deleted_paths

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "repo_id": self.repo_id,
            "repo_type": self.repo_type,
            "branch": self.branch,
            "file_path": self.file_path,
            "size_str": self.size_str,
            "date_str": self.date_str,
            "dest_dir": self.dest_dir,
            "flatten": self.flatten,
            "endpoint": self.endpoint,
            "token": self.token,
            "proxy": self.proxy,
            "platform": self.platform,
            "direct_url": self.direct_url,
            "status": "已中断" if self.status == "下载中" else self.status,
            "progress": self.progress,
            "total_bytes": self.total_bytes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueueTask":
        task = cls(
            task_id=data.get("task_id", 1),
            repo_id=data.get("repo_id", ""),
            repo_type=data.get("repo_type", "model"),
            branch=data.get("branch", "main"),
            file_path=data.get("file_path", ""),
            size_str=data.get("size_str", "未知"),
            date_str=data.get("date_str", "--"),
            dest_dir=data.get("dest_dir", ""),
            flatten=data.get("flatten", True),
            endpoint=data.get("endpoint", "https://hf-mirror.com"),
            token=data.get("token"),
            proxy=data.get("proxy"),
            platform=data.get("platform", "hf"),
            direct_url=data.get("direct_url"),
            status=data.get("status", "等待中"),
            progress=data.get("progress", 0.0),
            total_bytes=data.get("total_bytes")
        )
        task.check_local_status()
        return task


class HFDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🚀 Hugging Face 批量与断点续传极速下载器 (HF Explorer & Queue Manager)")
        self.geometry("1220x880")
        self.minsize(940, 680)

        # Style & Font configuration
        self.style = ttk.Style(self)
        if "vista" in self.style.theme_names():
            self.style.theme_use("vista")
        elif "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.style.configure(".", font=FONT_NORMAL)
        self.style.configure("TNotebook.Tab", font=FONT_BOLD, padding=[12, 6])
        self.style.configure("Treeview", font=FONT_TABLE, rowheight=28)
        self.style.configure("Treeview.Heading", font=FONT_BOLD)
        self.style.configure("TLabelframe.Label", font=FONT_TITLE)
        self.style.configure("TButton", font=FONT_NORMAL)

        # Generate True Color ARGB Image Icons
        self.icons = ColorIconFactory.get_all_icons()

        self.mirrors_list: List[str] = list(DEFAULT_MIRRORS)
        self.proxies_list: List[str] = list(DEFAULT_PROXIES)

        self.raw_files_dict: Dict[str, Dict[str, Any]] = {}
        self.current_selected_dir = ""
        self.checked_files: Set[str] = set()
        self.checked_tasks: Set[int] = set()

        self.tasks: List[QueueTask] = []
        self.task_counter = 1
        self.is_queue_running = False
        self.cancel_current_task = False
        self.stop_queue_requested = False
        self.active_task_id: Optional[int] = None

        self.protocol("WM_DELETE_WINDOW", self._on_window_closing)

        self._load_saved_settings()
        self._load_saved_mirrors()
        self._load_saved_proxies()
        self._build_ui()
        self._load_saved_tasks()
        self._check_background_active_tasks()
        self._check_dependency()

    # ------------------ Settings, Mirrors & Proxies Persistence ------------------
    def _load_saved_settings(self):
        self.saved_proxy = ""
        self.saved_token = ""
        if os.path.exists(APP_CONFIG_FILE):
            try:
                with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.saved_proxy = data.get("proxy", "")
                    self.saved_token = data.get("token", "")
            except Exception:
                pass

    def _save_settings(self):
        try:
            token_val = self.token_var.get().strip() if hasattr(self, "token_var") else self.saved_token
            with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "proxy": self._get_effective_proxy() if hasattr(self, "proxy_var") else self.saved_proxy,
                    "token": token_val
                }, f, ensure_ascii=False, indent=2)
            if token_val:
                os.environ["HF_TOKEN"] = token_val
        except Exception:
            pass

    def _load_saved_mirrors(self):
        if os.path.exists(MIRRORS_CONFIG_FILE):
            try:
                with open(MIRRORS_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved = data.get("mirrors", [])
                    if saved and isinstance(saved, list):
                        self.mirrors_list = [m for m in saved if m and isinstance(m, str)]
            except Exception:
                self.mirrors_list = list(DEFAULT_MIRRORS)
        else:
            self.mirrors_list = list(DEFAULT_MIRRORS)

    def _save_mirrors(self):
        try:
            with open(MIRRORS_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"mirrors": self.mirrors_list}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_saved_proxies(self):
        if os.path.exists(PROXIES_CONFIG_FILE):
            try:
                with open(PROXIES_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved = data.get("proxies", [])
                    if saved and isinstance(saved, list):
                        self.proxies_list = [p for p in saved if p and isinstance(p, str)]
            except Exception:
                self.proxies_list = list(DEFAULT_PROXIES)
        else:
            self.proxies_list = list(DEFAULT_PROXIES)

    def _save_proxies(self):
        try:
            with open(PROXIES_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"proxies": self.proxies_list}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _toggle_token_visibility(self):
        self.token_show_state = not self.token_show_state
        if self.token_show_state:
            self.token_entry.config(show="")
            self.btn_toggle_token.config(text=" 隐藏", image=self.icons["eye_lock"], compound=tk.LEFT)
        else:
            self.token_entry.config(show="*")
            self.btn_toggle_token.config(text=" 显示", image=self.icons["eye_open"], compound=tk.LEFT)

    def open_mirror_manager(self):
        MirrorManagerDialog(self, self.mirrors_list, self._on_mirrors_updated)

    def _on_mirrors_updated(self, new_mirrors: List[str], selected: Optional[str] = None):
        self.mirrors_list = new_mirrors
        self._save_mirrors()
        self.mirror_combo["values"] = self.mirrors_list
        if selected:
            self.mirror_var.set(selected)
        elif self.mirror_var.get() not in self.mirrors_list and self.mirrors_list:
            self.mirror_var.set(self.mirrors_list[0])
        self.log(f"[✓] 镜像源列表已更新并永久保存 (当前共有 {len(self.mirrors_list)} 个源)。")

    def open_proxy_manager(self):
        ProxyManagerDialog(self, self.proxies_list, self._on_proxies_updated)

    def _on_proxies_updated(self, new_proxies: List[str], selected: Optional[str] = None):
        self.proxies_list = new_proxies
        self._save_proxies()
        self.proxy_combo["values"] = self.proxies_list
        if selected:
            self.proxy_var.set(selected)
        elif self.proxy_var.get() not in self.proxies_list and self.proxies_list:
            self.proxy_var.set(self.proxies_list[0])
        self._save_settings()
        self.log(f"[✓] 网络代理列表已更新并永久保存 (当前共有 {len(self.proxies_list)} 个配置项)。")

    def open_env_setup(self):
        self.notebook.select(3)
        self._check_tab_env_status()
        self._refresh_tab_env_dirs()

    def _on_env_setup_completed(self):
        global HfApi
        try:
            from huggingface_hub import HfApi as NewHfApi
            HfApi = NewHfApi
            self.log("[✓] HuggingFace Hub 模块已实时加载就绪！")
        except Exception:
            pass
        self._check_dependency()

    def _get_effective_proxy(self) -> Optional[str]:
        val = self.proxy_var.get().strip()
        if not val or "不使用代理" in val or "直连" in val:
            return None
        if not (val.startswith("http://") or val.startswith("https://") or val.startswith("socks5://") or val.startswith("socks5h://")):
            val = "http://" + val
        return val

    def _get_request_proxies(self) -> Optional[Dict[str, str]]:
        p = self._get_effective_proxy()
        if p:
            return {
                "http": p,
                "https": p
            }
        return None

    def test_proxy_connectivity(self):
        proxy = self._get_effective_proxy()
        endpoint = self.mirror_var.get().strip().rstrip("/")
        test_url = f"{endpoint}/api/models"
        
        self.lbl_status.config(text="状态: 正在测试网络与代理连通性...", foreground="blue")
        self.log(f"[*] 正在测试网络连通性 -> 目标: {endpoint} | 代理: {proxy or '无 (直连)'}...")

        def _test_worker():
            proxies = {"http": proxy, "https": proxy} if proxy else None
            start_t = time.time()
            try:
                resp = requests.get(test_url, proxies=proxies, timeout=8, headers={"User-Agent": "HF-Downloader"})
                cost = (time.time() - start_t) * 1000
                if resp.status_code in (200, 401, 403):
                    msg = f"网络与代理连接畅通！\n\n• 目标站点: {endpoint}\n• 代理设置: {proxy or '直连'}\n• HTTP 状态码: {resp.status_code}\n• 响应延迟: {cost:.0f} ms"
                    self.after(0, lambda: messagebox.showinfo("连接成功", msg))
                    self.after(0, lambda: self.log(f"[✓] 连通性测试通过! 延迟: {cost:.0f} ms"))
                    self.after(0, lambda: self.lbl_status.config(text=f"状态: 网络连通正常 ({cost:.0f} ms)", foreground="green"))
                else:
                    msg = f"连接返回异常状态码: {resp.status_code}\n• 目标: {endpoint}\n• 代理: {proxy or '直连'}"
                    self.after(0, lambda: messagebox.showwarning("连接警告", msg))
                    self.after(0, lambda: self.log(f"[!] 连通性测试警告: HTTP {resp.status_code}"))
            except Exception as e:
                msg = f"无法通过当前配置连接到目标站点:\n\n• 目标: {endpoint}\n• 代理: {proxy or '直连'}\n• 错误详情: {str(e)}\n\n建议检查代理客户端是否开启 (如 Clash/v2rayN) 或切换镜像源！"
                self.after(0, lambda: messagebox.showerror("连接失败", msg))
                self.after(0, lambda: self.log(f"[✗] 代理/网络连接失败: {str(e)}"))
                self.after(0, lambda: self.lbl_status.config(text="状态: 连接失败", foreground="red"))

        threading.Thread(target=_test_worker, daemon=True).start()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Tab 1: Hugging Face Explorer
        self.tab_browse = ttk.Frame(self.notebook, padding="6")
        self.notebook.add(self.tab_browse, text=" 🤗 HuggingFace 浏览器 ")

        # Tab 2: GitHub Explorer
        self.tab_github = ttk.Frame(self.notebook, padding="6")
        self.notebook.add(self.tab_github, text=" 🐙 GitHub 资源浏览器 ")

        # Tab 3: Download Queue
        self.tab_queue = ttk.Frame(self.notebook, padding="6")
        self.notebook.add(self.tab_queue, text=" 📑 统一下载队列 (0) ")

        # Tab 4: Environment Setup & Directory Manager
        self.tab_env = ttk.Frame(self.notebook, padding="6")
        self.notebook.add(self.tab_env, text=" 🛠️ 一键部署环境 ")

        self._build_tab_browse()
        self._build_tab_github()
        self._build_tab_queue()
        self._build_tab_env()
        self._build_bottom_panel(main_frame)

    # ------------------ Tab 1: Dual-Pane File Browser with Checkbox UI ------------------
    def _build_tab_browse(self):
        self.browse_paned_v = ttk.PanedWindow(self.tab_browse, orient=tk.VERTICAL)
        self.browse_paned_v.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Upper Pane: Configuration Area
        self.browse_pane_upper = ttk.Frame(self.browse_paned_v)
        self.browse_paned_v.add(self.browse_pane_upper, weight=1)

        config_frame = ttk.LabelFrame(self.browse_pane_upper, text=" 🤗 Hugging Face 仓库、模型与网络加速配置 ", padding="6")
        config_frame.pack(fill=tk.X, pady=(0, 4))

        # Row 0: Repo ID, Type, Branch, Fetch button, Env button
        ttk.Label(config_frame, text="HF 仓库 (Repo ID):").grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        self.repo_id_var = tk.StringVar(value="Kijai/MiniMax-H3-experimental")
        repo_entry = ttk.Entry(config_frame, textvariable=self.repo_id_var, width=32, font=FONT_NORMAL)
        repo_entry.grid(row=0, column=1, sticky=tk.EW, padx=4, pady=3)

        ttk.Label(config_frame, text="类型:").grid(row=0, column=2, sticky=tk.W, padx=4, pady=3)
        self.repo_type_var = tk.StringVar(value="model")
        repo_type_combo = ttk.Combobox(config_frame, textvariable=self.repo_type_var, values=["model", "dataset", "space"], width=7, state="readonly", font=FONT_NORMAL)
        repo_type_combo.grid(row=0, column=3, sticky=tk.W, padx=4, pady=3)

        ttk.Label(config_frame, text="分支:").grid(row=0, column=4, sticky=tk.W, padx=4, pady=3)
        self.branch_var = tk.StringVar(value="main")
        branch_entry = ttk.Entry(config_frame, textvariable=self.branch_var, width=7, font=FONT_NORMAL)
        branch_entry.grid(row=0, column=5, sticky=tk.W, padx=4, pady=3)

        self.btn_fetch = ttk.Button(config_frame, text=" 获取文件列表", image=self.icons["search"], compound=tk.LEFT, command=self.start_fetch_files)
        self.btn_fetch.grid(row=0, column=6, padx=4, pady=3)

        # Row 1: Mirror selector with custom management button & Token input with visibility toggle
        ttk.Label(config_frame, text="下载镜像源:").grid(row=1, column=0, sticky=tk.W, padx=4, pady=3)
        
        mirror_subframe = ttk.Frame(config_frame)
        mirror_subframe.grid(row=1, column=1, sticky=tk.EW, padx=4, pady=3)

        self.mirror_var = tk.StringVar(value=self.mirrors_list[0] if self.mirrors_list else "https://hf-mirror.com")
        self.mirror_combo = ttk.Combobox(mirror_subframe, textvariable=self.mirror_var, values=self.mirrors_list, font=FONT_NORMAL)
        self.mirror_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_manage_mirror = ttk.Button(mirror_subframe, text=" 增删管理源...", image=self.icons["globe"], compound=tk.LEFT, width=13, command=self.open_mirror_manager)
        btn_manage_mirror.pack(side=tk.RIGHT, padx=(4, 0))

        ttk.Label(config_frame, text="HF Token:").grid(row=1, column=2, sticky=tk.W, padx=4, pady=3)
        
        token_subframe = ttk.Frame(config_frame)
        token_subframe.grid(row=1, column=3, columnspan=5, sticky=tk.EW, padx=4, pady=3)

        self.token_var = tk.StringVar(value=self.saved_token)
        self.token_show_state = False
        self.token_entry = ttk.Entry(token_subframe, textvariable=self.token_var, show="*", font=FONT_NORMAL)
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.token_entry.bind("<FocusOut>", lambda e: self._save_settings())
        self.token_entry.bind("<KeyRelease>", lambda e: self._save_settings())

        self.btn_toggle_token = ttk.Button(token_subframe, text=" 显示", image=self.icons["eye_open"], compound=tk.LEFT, width=7, command=self._toggle_token_visibility)
        self.btn_toggle_token.pack(side=tk.RIGHT, padx=(4, 0))

        ToolTip(self.token_entry, "用于访问 Gated (如 Llama/Flux) 或 Private 私有模型仓库的 Hugging Face Access Token，输入后自动永久保存")

        # Row 2: Proxy settings & management
        ttk.Label(config_frame, text="网络代理 (Proxy):").grid(row=2, column=0, sticky=tk.W, padx=4, pady=3)

        proxy_subframe = ttk.Frame(config_frame)
        proxy_subframe.grid(row=2, column=1, sticky=tk.EW, padx=4, pady=3)

        self.proxy_var = tk.StringVar(value=self.saved_proxy if self.saved_proxy in self.proxies_list else self.proxies_list[0])
        self.proxy_combo = ttk.Combobox(proxy_subframe, textvariable=self.proxy_var, values=self.proxies_list, font=FONT_NORMAL)
        self.proxy_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.proxy_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())
        self.proxy_combo.bind("<FocusOut>", lambda e: self._save_settings())

        btn_manage_proxy = ttk.Button(proxy_subframe, text=" 增删管理代理...", image=self.icons["shield"], compound=tk.LEFT, width=14, command=self.open_proxy_manager)
        btn_manage_proxy.pack(side=tk.RIGHT, padx=(4, 0))

        btn_test_proxy = ttk.Button(proxy_subframe, text=" 检测连通性", image=self.icons["bolt"], compound=tk.LEFT, width=12, command=self.test_proxy_connectivity)
        btn_test_proxy.pack(side=tk.RIGHT, padx=(4, 0))

        config_frame.columnconfigure(1, weight=1)

        # Target Directory Frame (Clear Category Presets + Absolute Path + Flatten Mode)
        dest_frame = ttk.LabelFrame(
            self.browse_pane_upper, 
            text=" 💾 当前文件的保存目标目录 (默认开启扁平化保存：直接存入目标目录，不生成多层嵌套子文件夹) ", 
            padding="6"
        )
        dest_frame.pack(fill=tk.X, pady=(0, 2))

        ttk.Label(dest_frame, text="常用预设分类:").grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        
        self.preset_labels = list(PRESET_DIRS_MAP.keys())
        self.preset_var = tk.StringVar(value=self.preset_labels[0])
        self.preset_combo = ttk.Combobox(
            dest_frame, 
            textvariable=self.preset_var, 
            values=self.preset_labels,
            width=26,
            state="readonly",
            font=FONT_BOLD
        )
        self.preset_combo.grid(row=0, column=1, sticky=tk.W, padx=4, pady=3)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)
        
        ComboboxItemToolTip(self.preset_combo, PRESET_DIRS_MAP)

        ttk.Label(dest_frame, text="完整路径:").grid(row=0, column=2, sticky=tk.W, padx=(8, 4), pady=3)
        self.dest_dir_var = tk.StringVar(value=PRESET_DIRS_MAP[self.preset_labels[0]])
        dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_dir_var, font=FONT_NORMAL)
        dest_entry.grid(row=0, column=3, sticky=tk.EW, padx=4, pady=3)

        ToolTip(dest_entry, lambda: f"目标保存目录完整绝对路径:\n{self.dest_dir_var.get()}")

        btn_browse = ttk.Button(dest_frame, text=" 浏览更改...", image=self.icons["folder"], compound=tk.LEFT, command=self.browse_dest_dir)
        btn_browse.grid(row=0, column=4, padx=4, pady=3)

        self.flatten_var = tk.BooleanVar(value=True)
        flatten_chk = ttk.Checkbutton(
            dest_frame, 
            text="扁平化保存", 
            variable=self.flatten_var
        )
        flatten_chk.grid(row=0, column=5, sticky=tk.W, padx=(6, 4), pady=3)
        ToolTip(flatten_chk, "勾选后将文件直接保存到目标目录，不创建多层子文件夹")

        dest_frame.columnconfigure(3, weight=1)

        # Lower Pane: Dual-Pane File Explorer
        self.browse_pane_lower = ttk.Frame(self.browse_paned_v)
        self.browse_paned_v.add(self.browse_pane_lower, weight=3)

        self.explorer_paned_h = ttk.PanedWindow(self.browse_pane_lower, orient=tk.HORIZONTAL)
        self.explorer_paned_h.pack(fill=tk.BOTH, expand=True)

        # 1. Left Directory Pane
        left_dir_pane = ttk.LabelFrame(self.explorer_paned_h, text=" 📁 模型目录层级导航 ", padding="6")
        self.explorer_paned_h.add(left_dir_pane, weight=1)

        dir_tool_bar = ttk.Frame(left_dir_pane)
        dir_tool_bar.pack(fill=tk.X, pady=(0, 4))

        self.lbl_dir_count = ttk.Label(dir_tool_bar, text="目录: 0 个", font=FONT_SMALL)
        self.lbl_dir_count.pack(side=tk.LEFT)

        btn_exp_dir = ttk.Button(dir_tool_bar, text="展开", width=5, command=self.expand_all_dirs)
        btn_exp_dir.pack(side=tk.RIGHT, padx=1)
        btn_col_dir = ttk.Button(dir_tool_bar, text="折叠", width=5, command=self.collapse_all_dirs)
        btn_col_dir.pack(side=tk.RIGHT, padx=1)

        dir_tree_container = ttk.Frame(left_dir_pane)
        dir_tree_container.pack(fill=tk.BOTH, expand=True)

        self.tree_dirs = ttk.Treeview(dir_tree_container, show="tree", selectmode="browse")
        self.tree_dirs.tag_configure("folder_node", foreground="#0d6efd", font=FONT_TABLE_BOLD)
        self.tree_dirs.tag_configure("root_node", foreground="#0b5ed7", font=FONT_TABLE_BOLD)

        dir_scroll_y = ttk.Scrollbar(dir_tree_container, orient=tk.VERTICAL, command=self.tree_dirs.yview)
        self.tree_dirs.configure(yscrollcommand=dir_scroll_y.set)

        self.tree_dirs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dir_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_dirs.bind("<<TreeviewSelect>>", self._on_dir_selected)

        # 2. Right File Details Pane with Checkboxes
        right_file_pane = ttk.LabelFrame(self.explorer_paned_h, text=" 📄 模型文件挑拣列表 (点击整行切换勾选) ", padding="6")
        self.explorer_paned_h.add(right_file_pane, weight=3)

        file_tool_bar = ttk.Frame(right_file_pane)
        file_tool_bar.pack(fill=tk.X, pady=(0, 4))

        self.lbl_current_path = ttk.Label(file_tool_bar, text="当前位置: / (根目录)", font=FONT_BOLD, foreground="#0d6efd")
        self.lbl_current_path.pack(side=tk.LEFT, padx=(0, 8))

        self.lbl_checked_count = ttk.Label(file_tool_bar, text="[已勾选: 0]", font=FONT_BOLD, foreground="#198754")
        self.lbl_checked_count.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(file_tool_bar, text="筛选:").pack(side=tk.LEFT, padx=(0, 4))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *args: self._apply_file_filter())
        filter_entry = ttk.Entry(file_tool_bar, textvariable=self.filter_var, width=16, font=FONT_NORMAL)
        filter_entry.pack(side=tk.LEFT, padx=(0, 6))

        btn_select_all = ttk.Button(file_tool_bar, text="☑ 全部勾选", width=9, command=self.check_all_current_files)
        btn_select_all.pack(side=tk.RIGHT, padx=2)
        btn_deselect_all = ttk.Button(file_tool_bar, text="☐ 全部取消", width=9, command=self.uncheck_all_current_files)
        btn_deselect_all.pack(side=tk.RIGHT, padx=2)

        file_tree_container = ttk.Frame(right_file_pane)
        file_tree_container.pack(fill=tk.BOTH, expand=True)

        columns = ("check", "name", "size", "date", "full_path")
        self.tree_files = ttk.Treeview(file_tree_container, columns=columns, show="headings", selectmode="extended")
        
        self.tree_files.heading("check", text="选择", anchor=tk.CENTER)
        self.tree_files.heading("name", text="文件名 (File Name)", anchor=tk.W)
        self.tree_files.heading("size", text="大小")
        self.tree_files.heading("date", text="更新日期")
        self.tree_files.heading("full_path", text="完整路径")
        
        self.tree_files.column("check", width=55, minwidth=45, stretch=False, anchor=tk.CENTER)
        self.tree_files.column("name", width=380, minwidth=180, stretch=True, anchor=tk.W)
        self.tree_files.column("size", width=115, minwidth=70, stretch=False, anchor=tk.E)
        self.tree_files.column("date", width=150, minwidth=110, stretch=False, anchor=tk.CENTER)
        self.tree_files.column("full_path", width=0, minwidth=0, stretch=False)

        # Style Tags
        self.tree_files.tag_configure("file_tag", foreground="#212529", font=FONT_TABLE)
        self.tree_files.tag_configure("checked_tag", foreground="#0d6efd", font=FONT_TABLE_BOLD)

        file_scroll_y = ttk.Scrollbar(file_tree_container, orient=tk.VERTICAL, command=self.tree_files.yview)
        self.tree_files.configure(yscrollcommand=file_scroll_y.set)

        self.tree_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_files.bind("<Button-1>", self._on_file_tree_click)
        self.tree_files.bind("<space>", self._on_file_tree_space)

        # Bottom Action Bar of Tab 1
        browse_act_frame = ttk.Frame(self.tab_browse)
        browse_act_frame.pack(fill=tk.X, pady=(4, 0))

        self.btn_add_to_queue = ttk.Button(
            browse_act_frame, 
            text=" 加入下载队列", 
            image=self.icons["download"],
            compound=tk.LEFT,
            command=self.add_selected_to_queue
        )
        self.btn_add_to_queue.pack(side=tk.LEFT, padx=4, ipady=3)

        btn_add_entire_dir = ttk.Button(
            browse_act_frame, 
            text=" 目录整包入队", 
            image=self.icons["folder"],
            compound=tk.LEFT,
            command=self.add_current_dir_to_queue
        )
        btn_add_entire_dir.pack(side=tk.LEFT, padx=4, ipady=3)

        btn_add_and_jump = ttk.Button(
            browse_act_frame, 
            text=" 入队并跳转", 
            image=self.icons["rocket"],
            compound=tk.LEFT,
            command=lambda: self.add_selected_to_queue(jump=True)
        )
        btn_add_and_jump.pack(side=tk.LEFT, padx=4, ipady=3)

    # ------------------ Tab 1 Checkbox Click & Toggle Events ------------------
    def _on_file_tree_click(self, event):
        region = self.tree_files.identify("region", event.x, event.y)
        if region == "heading":
            col = self.tree_files.identify_column(event.x)
            if col == "#1":
                self._toggle_check_all_visible()
                return "break"
        elif region in ("cell", "tree", "item"):
            item_id = self.tree_files.identify_row(event.y)
            if item_id:
                self._toggle_single_file_check(item_id)
                self.tree_files.selection_set(item_id)
                return "break"

    def _on_file_tree_space(self, event):
        selected_iids = self.tree_files.selection()
        if selected_iids:
            for iid in selected_iids:
                self._toggle_single_file_check(iid)
            return "break"

    def _toggle_single_file_check(self, fpath: str):
        if fpath in self.checked_files:
            self.checked_files.remove(fpath)
        else:
            self.checked_files.add(fpath)
        self._update_item_checkbox_display(fpath)
        self._update_checked_count_label()

    def _update_item_checkbox_display(self, fpath: str):
        if self.tree_files.exists(fpath):
            is_checked = fpath in self.checked_files
            check_symbol = "☑" if is_checked else "☐"
            cur_vals = list(self.tree_files.item(fpath, "values"))
            cur_vals[0] = check_symbol
            self.tree_files.item(fpath, values=cur_vals, tags=("checked_tag" if is_checked else "file_tag",))

    def _update_checked_count_label(self):
        cnt = len(self.checked_files)
        self.lbl_checked_count.config(text=f"[已勾选: {cnt} 个文件]")

    def check_all_current_files(self):
        for fpath in self.tree_files.get_children():
            self.checked_files.add(fpath)
            self._update_item_checkbox_display(fpath)
        self._update_checked_count_label()

    def uncheck_all_current_files(self):
        for fpath in self.tree_files.get_children():
            if fpath in self.checked_files:
                self.checked_files.remove(fpath)
            self._update_item_checkbox_display(fpath)
        self._update_checked_count_label()

    def _toggle_check_all_visible(self):
        all_visible = self.tree_files.get_children()
        if not all_visible:
            return
        all_checked = all(f in self.checked_files for f in all_visible)
        if all_checked:
            self.uncheck_all_current_files()
        else:
            self.check_all_current_files()

    # ------------------ Tab 2: GitHub Repository & Release Asset Explorer ------------------
    def _build_tab_github(self):
        self.gh_paned_v = ttk.PanedWindow(self.tab_github, orient=tk.VERTICAL)
        self.gh_paned_v.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Upper Pane: GitHub Configuration Card
        pane_upper = ttk.Frame(self.gh_paned_v)
        self.gh_paned_v.add(pane_upper, weight=1)

        config_frame = ttk.LabelFrame(pane_upper, text=" 🐙 GitHub 仓库、Release与网络加速配置 ", padding="6")
        config_frame.pack(fill=tk.X, pady=(0, 4))

        # Row 0: Repo ID, Mode (Release/SourceTree), Branch/Tag, Fetch Button
        ttk.Label(config_frame, text="GitHub 仓库 (owner/repo):").grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        self.gh_repo_var = tk.StringVar(value="comfyanonymous/ComfyUI")
        gh_repo_entry = ttk.Entry(config_frame, textvariable=self.gh_repo_var, width=30, font=FONT_NORMAL)
        gh_repo_entry.grid(row=0, column=1, sticky=tk.EW, padx=4, pady=3)

        ttk.Label(config_frame, text="资源模式:").grid(row=0, column=2, sticky=tk.W, padx=4, pady=3)
        self.gh_mode_var = tk.StringVar(value="📦 Release 发布包")
        gh_mode_combo = ttk.Combobox(config_frame, textvariable=self.gh_mode_var, values=["📦 Release 发布包", "🌲 源码目录树"], width=14, state="readonly", font=FONT_NORMAL)
        gh_mode_combo.grid(row=0, column=3, sticky=tk.W, padx=4, pady=3)

        ttk.Label(config_frame, text="分支/Tag:").grid(row=0, column=4, sticky=tk.W, padx=4, pady=3)
        self.gh_branch_var = tk.StringVar(value="master")
        gh_branch_entry = ttk.Entry(config_frame, textvariable=self.gh_branch_var, width=9, font=FONT_NORMAL)
        gh_branch_entry.grid(row=0, column=5, sticky=tk.W, padx=4, pady=3)

        self.btn_gh_fetch = ttk.Button(config_frame, text=" 获取 GitHub 资源", image=self.icons["search"], compound=tk.LEFT, command=self.start_fetch_github)
        self.btn_gh_fetch.grid(row=0, column=6, padx=4, pady=3)

        # Row 1: Accelerator Mirror & GitHub Token
        ttk.Label(config_frame, text="国内极速加速节点:").grid(row=1, column=0, sticky=tk.W, padx=4, pady=3)
        self.gh_mirror_var = tk.StringVar(value=DEFAULT_GITHUB_ACCELERATORS[0])
        gh_mirror_combo = ttk.Combobox(config_frame, textvariable=self.gh_mirror_var, values=DEFAULT_GITHUB_ACCELERATORS, font=FONT_NORMAL)
        gh_mirror_combo.grid(row=1, column=1, sticky=tk.EW, padx=4, pady=3)

        ttk.Label(config_frame, text="GitHub Token:").grid(row=1, column=2, sticky=tk.W, padx=4, pady=3)
        self.gh_token_var = tk.StringVar(value="")
        gh_token_entry = ttk.Entry(config_frame, textvariable=self.gh_token_var, show="*", font=FONT_NORMAL)
        gh_token_entry.grid(row=1, column=3, columnspan=2, sticky=tk.EW, padx=4, pady=3)

        btn_test_gh_node = ttk.Button(config_frame, text=" 检测加速节点", image=self.icons["bolt"], compound=tk.LEFT, command=self.test_github_accelerator)
        btn_test_gh_node.grid(row=1, column=5, columnspan=2, sticky=tk.EW, padx=4, pady=3)

        # Row 2: Destination path & ComfyUI Preset
        ttk.Label(config_frame, text="保存目标路径:").grid(row=2, column=0, sticky=tk.W, padx=4, pady=3)
        self.gh_dest_path_var = tk.StringVar(value=DEFAULT_CUSTOM_NODES_DIR)
        gh_dest_entry = ttk.Entry(config_frame, textvariable=self.gh_dest_path_var, font=FONT_NORMAL)
        gh_dest_entry.grid(row=2, column=1, sticky=tk.EW, padx=4, pady=3)

        ttk.Label(config_frame, text="分类预设:").grid(row=2, column=2, sticky=tk.W, padx=4, pady=3)
        preset_names = list(PRESET_DIRS_MAP.keys())
        self.gh_preset_var = tk.StringVar(value=preset_names[0])
        gh_preset_combo = ttk.Combobox(config_frame, textvariable=self.gh_preset_var, values=preset_names, state="readonly", font=FONT_NORMAL)
        gh_preset_combo.grid(row=2, column=3, columnspan=2, sticky=tk.EW, padx=4, pady=3)
        gh_preset_combo.bind("<<ComboboxSelected>>", self._on_gh_preset_changed)

        btn_browse_gh_dest = ttk.Button(config_frame, text=" 浏览...", image=self.icons["folder"], compound=tk.LEFT, width=8, command=self._browse_gh_dest)
        btn_browse_gh_dest.grid(row=2, column=5, padx=2, pady=3)

        self.gh_flatten_var = tk.BooleanVar(value=True)
        cb_gh_flatten = ttk.Checkbutton(config_frame, text="扁平化保存 (直接存入该目录)", variable=self.gh_flatten_var)
        cb_gh_flatten.grid(row=2, column=6, sticky=tk.W, padx=4, pady=3)

        config_frame.columnconfigure(1, weight=3)
        config_frame.columnconfigure(3, weight=2)

        # Lower Pane: Dual-pane Browser (Treeview on left, File/Asset list on right)
        pane_lower = ttk.Frame(self.gh_paned_v)
        self.gh_paned_v.add(pane_lower, weight=4)

        self.gh_paned_h = ttk.PanedWindow(pane_lower, orient=tk.HORIZONTAL)
        self.gh_paned_h.pack(fill=tk.BOTH, expand=True)

        # Left Column: Release / Directory list
        left_frame = ttk.LabelFrame(self.gh_paned_h, text=" 📁 Release版本 / 源码目录树 ", padding="4")
        self.gh_paned_h.add(left_frame, weight=1)

        self.tree_gh_nav = ttk.Treeview(left_frame, show="tree", selectmode="browse")
        nav_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree_gh_nav.yview)
        self.tree_gh_nav.configure(yscrollcommand=nav_scroll.set)

        self.tree_gh_nav.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        nav_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_gh_nav.bind("<<TreeviewSelect>>", self._on_gh_nav_selected)

        # Right Column: Asset / File Table
        right_frame = ttk.LabelFrame(self.gh_paned_h, text=" 📄 资源与文件挑拣列表 (点击整行切换勾选) ", padding="4")
        self.gh_paned_h.add(right_frame, weight=3)

        right_top_bar = ttk.Frame(right_frame)
        right_top_bar.pack(fill=tk.X, pady=(0, 4))

        self.lbl_gh_current_scope = ttk.Label(right_top_bar, text="当前位置: 未获取资源", font=FONT_BOLD, foreground="#0d6efd")
        self.lbl_gh_current_scope.pack(side=tk.LEFT)

        self.lbl_gh_checked_count = ttk.Label(right_top_bar, text="[已勾选: 0 项]", font=FONT_BOLD, foreground="#198754")
        self.lbl_gh_checked_count.pack(side=tk.LEFT, padx=(12, 0))

        btn_gh_check_all = ttk.Button(right_top_bar, text="☑ 全选可见", command=self.check_all_gh_files)
        btn_gh_check_all.pack(side=tk.RIGHT, padx=2)
        btn_gh_uncheck_all = ttk.Button(right_top_bar, text="☐ 取消勾选", command=self.uncheck_all_gh_files)
        btn_gh_uncheck_all.pack(side=tk.RIGHT, padx=2)

        # File List Treeview
        gh_file_container = ttk.Frame(right_frame)
        gh_file_container.pack(fill=tk.BOTH, expand=True)

        cols = ("check", "name", "size", "date", "downloads", "url")
        self.tree_gh_files = ttk.Treeview(gh_file_container, columns=cols, show="headings", selectmode="extended")
        self.tree_gh_files.heading("check", text="选择", anchor=tk.CENTER)
        self.tree_gh_files.heading("name", text="资源文件名 / 相对路径 (点击整行切换勾选)")
        self.tree_gh_files.heading("size", text="大小")
        self.tree_gh_files.heading("date", text="更新/发布日期")
        self.tree_gh_files.heading("downloads", text="下载量")
        self.tree_gh_files.heading("url", text="直链")

        self.tree_gh_files.column("check", width=50, minwidth=40, stretch=False, anchor=tk.CENTER)
        self.tree_gh_files.column("name", width=340, minwidth=180, stretch=True)
        self.tree_gh_files.column("size", width=100, minwidth=70, stretch=False, anchor=tk.E)
        self.tree_gh_files.column("date", width=140, minwidth=110, stretch=False, anchor=tk.CENTER)
        self.tree_gh_files.column("downloads", width=80, minwidth=60, stretch=False, anchor=tk.CENTER)
        self.tree_gh_files.column("url", width=100, stretch=False)

        self.tree_gh_files.tag_configure("checked_tag", background="#e0f2fe")
        self.tree_gh_files.tag_configure("file_tag", background="#ffffff")

        gh_scroll_y = ttk.Scrollbar(gh_file_container, orient=tk.VERTICAL, command=self.tree_gh_files.yview)
        self.tree_gh_files.configure(yscrollcommand=gh_scroll_y.set)

        self.tree_gh_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        gh_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_gh_files.bind("<Button-1>", self._on_gh_tree_click)
        self.tree_gh_files.bind("<space>", self._on_gh_tree_space)

        # Bottom Actions Bar
        gh_act_frame = ttk.Frame(self.tab_github)
        gh_act_frame.pack(fill=tk.X, pady=(4, 0))

        btn_gh_add_q = ttk.Button(
            gh_act_frame, text=" 加入统一下载队列", image=self.icons["download"], compound=tk.LEFT,
            command=lambda: self.add_github_to_queue(jump=False)
        )
        btn_gh_add_q.pack(side=tk.LEFT, padx=4, ipady=3)

        btn_gh_zip = ttk.Button(
            gh_act_frame, text=" 📦 下载整包源码 Zip (含加速)", image=self.icons["rocket"], compound=tk.LEFT,
            command=self.download_github_repo_zip
        )
        btn_gh_zip.pack(side=tk.LEFT, padx=4, ipady=3)

        btn_gh_add_jump = ttk.Button(
            gh_act_frame, text=" 入队并跳转到队列", image=self.icons["play"], compound=tk.LEFT,
            command=lambda: self.add_github_to_queue(jump=True)
        )
        btn_gh_add_jump.pack(side=tk.LEFT, padx=4, ipady=3)

        self.raw_gh_items = {}  # key -> item metadata
        self.checked_gh_items = set()

    def _on_gh_preset_changed(self, event=None):
        name = self.gh_preset_var.get()
        if name in PRESET_DIRS_MAP:
            repo_name = self.gh_repo_var.get().strip().split("/")[-1] or "download"
            base_dir = PRESET_DIRS_MAP[name]
            if name.startswith("🧩"):
                self.gh_dest_path_var.set(os.path.normpath(os.path.join(base_dir, repo_name)))
            else:
                self.gh_dest_path_var.set(base_dir)

    def _browse_gh_dest(self):
        d = filedialog.askdirectory(title="选择 GitHub 资源保存目标目录", initialdir=self.gh_dest_path_var.get())
        if d:
            self.gh_dest_path_var.set(os.path.normpath(d))

    def _get_accelerated_url(self, raw_url: str) -> str:
        accel = self.gh_mirror_var.get().strip()
        if not accel or "不使用" in accel or "直连" in accel:
            return raw_url
        accel = accel.rstrip("/") + "/"
        return accel + raw_url

    def test_github_accelerator(self):
        node = self.gh_mirror_var.get().strip()
        self.log(f"[*] 正在测试 GitHub 加速节点连通性: {node}...")
        self.lbl_status.config(text="状态: 正在测试 GitHub 加速节点...", foreground="blue")

        def _worker():
            test_url = self._get_accelerated_url("https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/README.md")
            proxies = self._get_request_proxies()
            try:
                t0 = time.time()
                resp = requests.head(test_url, proxies=proxies, timeout=8, allow_redirects=True)
                latency = int((time.time() - t0) * 1000)
                if resp.status_code in (200, 301, 302):
                    self.after(0, lambda: messagebox.showinfo("测试成功", f"GitHub 加速节点连通正常！\n节点: {node}\n响应延迟: {latency} ms"))
                    self.after(0, lambda: self.log(f"[✓] GitHub 加速节点测试成功: 延迟 {latency} ms"))
                    self.after(0, lambda: self.lbl_status.config(text=f"状态: GitHub 节点正常 ({latency} ms)", foreground="green"))
                else:
                    self.after(0, lambda: messagebox.showwarning("提示", f"节点返回状态码: HTTP {resp.status_code}\n建议更换其他加速源。"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("连接失败", f"节点连接超时/失败:\n{str(e)}"))
                self.after(0, lambda: self.log(f"[✗] GitHub 节点连接失败: {str(e)}"))
                self.after(0, lambda: self.lbl_status.config(text="状态: GitHub 节点连接失败", foreground="red"))

        threading.Thread(target=_worker, daemon=True).start()

    def start_fetch_github(self):
        repo_id = self.gh_repo_var.get().strip()
        if not repo_id or "/" not in repo_id:
            messagebox.showwarning("提示", "请输入有效的 GitHub 仓库名 (格式: owner/repo，例如 comfyanonymous/ComfyUI)！")
            return

        self._on_gh_preset_changed()
        self.btn_gh_fetch.config(state=tk.DISABLED)
        self.lbl_status.config(text=f"状态: 正在获取 GitHub [{repo_id}] 资源...", foreground="blue")
        self.log(f"\n[*] 正在查询 GitHub 仓库 '{repo_id}' 资源列表...")

        threading.Thread(target=self._fetch_github_worker, daemon=True).start()

    def _fetch_github_worker(self):
        repo_id = self.gh_repo_var.get().strip()
        mode = self.gh_mode_var.get().strip()
        branch = self.gh_branch_var.get().strip() or "main"
        token = self.gh_token_var.get().strip() or None
        proxies = self._get_request_proxies()

        headers = {"User-Agent": "HF-Downloader-GUI/1.0", "Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        items_map = {}
        nav_structure = {}
        err_msg = None

        if "Release" in mode:
            api_url = f"https://api.github.com/repos/{repo_id}/releases"
            try:
                resp = requests.get(api_url, headers=headers, proxies=proxies, timeout=12)
                if resp.status_code == 200:
                    releases = resp.json()
                    if not releases:
                        err_msg = "该仓库尚未发布任何 Release 版本。"
                    else:
                        for rel in releases:
                            tag_name = rel.get("tag_name", "未知Tag")
                            rel_name = rel.get("name") or tag_name
                            pub_date = (rel.get("published_at") or "--")[:16].replace("T", " ")
                            
                            nav_structure[tag_name] = f"📦 {tag_name} ({pub_date})"
                            
                            # Add release source code zip
                            zipball = rel.get("zipball_url") or f"https://github.com/{repo_id}/archive/refs/tags/{tag_name}.zip"
                            key_zip = f"{tag_name}/[Source code] {repo_id.split('/')[-1]}-{tag_name}.zip"
                            items_map[key_zip] = {
                                "name": f"[源码包] {repo_id.split('/')[-1]}-{tag_name}.zip",
                                "scope": tag_name,
                                "size_str": "整包Zip",
                                "raw_size": 0,
                                "date_str": pub_date,
                                "downloads": "--",
                                "url": zipball
                            }

                            for asset in rel.get("assets", []):
                                aname = asset.get("name")
                                asize = asset.get("size") or 0
                                adate = (asset.get("updated_at") or pub_date)[:16].replace("T", " ")
                                adls = str(asset.get("download_count", 0))
                                aurl = asset.get("browser_download_url")

                                key = f"{tag_name}/{aname}"
                                items_map[key] = {
                                    "name": aname,
                                    "scope": tag_name,
                                    "size_str": self._format_size(asize),
                                    "raw_size": asize,
                                    "date_str": adate,
                                    "downloads": adls,
                                    "url": aurl
                                }
                elif resp.status_code == 404:
                    err_msg = "未找到该仓库，请检查 owner/repo 拼写。"
                elif resp.status_code == 403:
                    err_msg = "GitHub API 调用频率受限，建议填入 GitHub Token！"
                else:
                    err_msg = f"HTTP {resp.status_code}: {resp.text[:120]}"
            except Exception as e:
                err_msg = str(e)
        else:
            # Source code tree mode
            api_url = f"https://api.github.com/repos/{repo_id}/git/trees/{branch}?recursive=1"
            try:
                resp = requests.get(api_url, headers=headers, proxies=proxies, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    tree = data.get("tree", [])
                    nav_structure["ROOT"] = "📁 全部源码 (根目录 /)"

                    for item in tree:
                        itype = item.get("type")
                        ipath = item.get("path")
                        if itype == "tree":
                            nav_structure[ipath] = f"📁 {ipath}"
                        elif itype == "blob":
                            isize = item.get("size") or 0
                            raw_url = f"https://raw.githubusercontent.com/{repo_id}/{branch}/{ipath}"
                            scope = os.path.dirname(ipath) if "/" in ipath else "ROOT"
                            items_map[ipath] = {
                                "name": ipath,
                                "scope": scope,
                                "size_str": self._format_size(isize),
                                "raw_size": isize,
                                "date_str": "--",
                                "downloads": "--",
                                "url": raw_url
                            }
                elif resp.status_code == 404:
                    err_msg = f"未找到仓库或分支 '{branch}'，请核对分支名称。"
                else:
                    err_msg = f"HTTP {resp.status_code}: {resp.text[:120]}"
            except Exception as e:
                err_msg = str(e)

        if items_map:
            self.raw_gh_items = items_map
            self.gh_nav_structure = nav_structure
            self.checked_gh_items.clear()
            self.after(0, self._populate_github_browser)
            self.after(0, lambda: self.log(f"[✓] 成功获取 GitHub {len(items_map)} 项资源。"))
            self.after(0, lambda: self.lbl_status.config(text=f"状态: 共检索到 {len(items_map)} 项 GitHub 资源", foreground="green"))
        else:
            self.after(0, lambda: self.log(f"[✗] 获取 GitHub 资源失败: {err_msg}"))
            self.after(0, lambda: self.lbl_status.config(text="状态: 获取 GitHub 资源失败", foreground="red"))
            self.after(0, lambda: messagebox.showerror("获取失败", f"无法获取 GitHub 资源:\n{err_msg}\n\n提示: 如遇 API 速率限制，可在上方输入 GitHub Token。"))

        self.after(0, lambda: self.btn_gh_fetch.config(state=tk.NORMAL))

    def _populate_github_browser(self):
        self.tree_gh_nav.delete(*self.tree_gh_nav.get_children())
        self.tree_gh_files.delete(*self.tree_gh_files.get_children())

        # Populate left navigation tree
        first_node = None
        for key, label in self.gh_nav_structure.items():
            iid = self.tree_gh_nav.insert("", tk.END, iid=key, text=label, open=True)
            if first_node is None:
                first_node = iid

        if first_node:
            self.tree_gh_nav.selection_set(first_node)
            self._render_gh_files_for_scope(first_node)

    def _on_gh_nav_selected(self, event=None):
        sel = self.tree_gh_nav.selection()
        if sel:
            scope = sel[0]
            self._render_gh_files_for_scope(scope)

    def _render_gh_files_for_scope(self, scope: str):
        self.tree_gh_files.delete(*self.tree_gh_files.get_children())
        self.lbl_gh_current_scope.config(text=f"当前位置: {scope}")

        for key, item in self.raw_gh_items.items():
            if item["scope"] == scope or scope == "ROOT":
                is_chk = key in self.checked_gh_items
                chk_sym = "☑" if is_chk else "☐"
                tag = "checked_tag" if is_chk else "file_tag"

                self.tree_gh_files.insert(
                    "", tk.END, iid=key,
                    values=(chk_sym, item["name"], item["size_str"], item["date_str"], item["downloads"], item["url"]),
                    tags=(tag,)
                )

        self._update_gh_checked_count_label()

    def _on_gh_tree_click(self, event):
        region = self.tree_gh_files.identify("region", event.x, event.y)
        if region == "heading":
            col = self.tree_gh_files.identify_column(event.x)
            if col == "#1":
                self.check_all_gh_files()
                return "break"
        elif region in ("cell", "tree", "item"):
            item_id = self.tree_gh_files.identify_row(event.y)
            if item_id:
                self._toggle_single_gh_check(item_id)
                self.tree_gh_files.selection_set(item_id)
                return "break"

    def _on_gh_tree_space(self, event):
        sel = self.tree_gh_files.selection()
        if sel:
            for iid in sel:
                self._toggle_single_gh_check(iid)
            return "break"

    def _toggle_single_gh_check(self, item_id: str):
        if item_id in self.checked_gh_items:
            self.checked_gh_items.remove(item_id)
        else:
            self.checked_gh_items.add(item_id)
        self._update_gh_checkbox_display(item_id)
        self._update_gh_checked_count_label()

    def _update_gh_checkbox_display(self, item_id: str):
        if self.tree_gh_files.exists(item_id):
            is_chk = item_id in self.checked_gh_items
            chk_sym = "☑" if is_chk else "☐"
            vals = list(self.tree_gh_files.item(item_id, "values"))
            vals[0] = chk_sym
            self.tree_gh_files.item(item_id, values=vals, tags=("checked_tag" if is_chk else "file_tag",))

    def _update_gh_checked_count_label(self):
        cnt = len(self.checked_gh_items)
        self.lbl_gh_checked_count.config(text=f"[已勾选: {cnt} 项]")

    def check_all_gh_files(self):
        for iid in self.tree_gh_files.get_children():
            self.checked_gh_items.add(iid)
            self._update_gh_checkbox_display(iid)
        self._update_gh_checked_count_label()

    def uncheck_all_gh_files(self):
        for iid in self.tree_gh_files.get_children():
            self.checked_gh_items.discard(iid)
            self._update_gh_checkbox_display(iid)
        self._update_gh_checked_count_label()

    def add_github_to_queue(self, jump: bool = False):
        if not self.checked_gh_items:
            messagebox.showwarning("提示", "请先在右侧列表中勾选需要下载的 GitHub 文件或资源！")
            return

        dest_dir = self.gh_dest_path_var.get().strip()
        if not dest_dir:
            messagebox.showwarning("提示", "请指定保存目标路径！")
            return

        os.makedirs(dest_dir, exist_ok=True)
        repo_id = self.gh_repo_var.get().strip()
        token = self.gh_token_var.get().strip() or None
        proxy = self._get_effective_proxy()
        flatten = self.gh_flatten_var.get()

        added_cnt = 0
        for key in list(self.checked_gh_items):
            item = self.raw_gh_items.get(key)
            if not item:
                continue

            raw_url = item["url"]
            accel_url = self._get_accelerated_url(raw_url)
            fname = os.path.basename(item["name"])

            # Check if task already in queue
            exists = any(t.platform == "github" and t.direct_url == accel_url and t.dest_dir == dest_dir for t in self.tasks)
            if exists:
                continue

            task_id = self._get_next_task_id()
            task = QueueTask(
                task_id=task_id,
                repo_id=f"🐙 {repo_id}",
                repo_type="github",
                branch=self.gh_branch_var.get().strip(),
                file_path=fname,
                size_str=item["size_str"],
                date_str=item["date_str"],
                dest_dir=dest_dir,
                flatten=flatten,
                endpoint=self.gh_mirror_var.get().strip(),
                token=token,
                proxy=proxy,
                status="等待中",
                progress=0.0,
                total_bytes=item["raw_size"] if item["raw_size"] > 0 else None,
                platform="github",
                direct_url=accel_url
            )
            self.tasks.append(task)
            added_cnt += 1

        self.rescan_all_tasks(silent=True)
        self.log(f"[✓] 成功将 {added_cnt} 个 GitHub 资源加入下载队列！")
        messagebox.showinfo("入队成功", f"成功将 {added_cnt} 个 GitHub 资源加入统一下载队列！")

        if jump:
            self.notebook.select(2)  # Switch to Queue tab

    def download_github_repo_zip(self):
        repo_id = self.gh_repo_var.get().strip()
        if not repo_id or "/" not in repo_id:
            messagebox.showwarning("提示", "请输入有效的 GitHub 仓库名！")
            return

        branch = self.gh_branch_var.get().strip() or "main"
        dest_dir = self.gh_dest_path_var.get().strip()
        os.makedirs(dest_dir, exist_ok=True)

        repo_name = repo_id.split("/")[-1]
        zip_name = f"{repo_name}-{branch}.zip"
        raw_url = f"https://github.com/{repo_id}/archive/refs/heads/{branch}.zip"
        accel_url = self._get_accelerated_url(raw_url)

        task_id = self._get_next_task_id()
        task = QueueTask(
            task_id=task_id,
            repo_id=f"🐙 {repo_id}",
            repo_type="github_zip",
            branch=branch,
            file_path=zip_name,
            size_str="整包源码Zip",
            date_str="最新",
            dest_dir=dest_dir,
            flatten=True,
            endpoint=self.gh_mirror_var.get().strip(),
            token=self.gh_token_var.get().strip() or None,
            proxy=self._get_effective_proxy(),
            status="等待中",
            progress=0.0,
            platform="github",
            direct_url=accel_url
        )
        self.tasks.append(task)
        self.rescan_all_tasks(silent=True)
        self.log(f"[✓] 已添加 GitHub 仓库整包源码 Zip 任务: {zip_name}")
        messagebox.showinfo("入队成功", f"已将 GitHub 整包源码 Zip 任务加入队列:\n{zip_name}\n保存到: {dest_dir}")
        self.notebook.select(2)

    # ------------------ Tab 3: Download Queue UI with Checkboxes ------------------
    def _build_tab_queue(self):
        self.queue_info_bar = ttk.Frame(self.tab_queue)
        self.queue_info_bar.pack(fill=tk.X, pady=(0, 4))

        self.lbl_queue_stats = ttk.Label(self.queue_info_bar, text="正在检测任务状态...", foreground="#333333", font=FONT_BOLD)
        self.lbl_queue_stats.pack(side=tk.LEFT)

        self.lbl_queue_checked = ttk.Label(self.queue_info_bar, text="[已勾选: 0 项]", foreground="#198754", font=FONT_BOLD)
        self.lbl_queue_checked.pack(side=tk.LEFT, padx=(12, 0))

        btn_check_bg = ttk.Button(self.queue_info_bar, text=" 检测后台活跃下载", image=self.icons["search"], compound=tk.LEFT, command=self.check_active_background_downloads)
        btn_check_bg.pack(side=tk.RIGHT, padx=(4, 0))

        btn_rescan = ttk.Button(self.queue_info_bar, text=" 重新扫描本地状态", image=self.icons["bolt"], compound=tk.LEFT, width=17, command=self.rescan_all_tasks)
        btn_rescan.pack(side=tk.RIGHT)

        # PanedWindow in Tab 2
        self.queue_paned = ttk.PanedWindow(self.tab_queue, orient=tk.VERTICAL)
        self.queue_paned.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Upper pane: Queue table frame
        self.queue_pane_upper = ttk.Frame(self.queue_paned)
        self.queue_paned.add(self.queue_pane_upper, weight=3)

        # Queue quick selection bar
        q_sel_bar = ttk.Frame(self.queue_pane_upper)
        q_sel_bar.pack(fill=tk.X, pady=(0, 2))

        ttk.Label(q_sel_bar, text="任务选择与批量维护:", font=FONT_SMALL).pack(side=tk.LEFT)

        btn_q_select_all = ttk.Button(q_sel_bar, text="☑ 全部勾选", width=9, command=self.check_all_tasks)
        btn_q_select_all.pack(side=tk.RIGHT, padx=2)
        btn_q_deselect_all = ttk.Button(q_sel_bar, text="☐ 全部取消", width=9, command=self.uncheck_all_tasks)
        btn_q_deselect_all.pack(side=tk.RIGHT, padx=2)

        tree_container = ttk.Frame(self.queue_pane_upper)
        tree_container.pack(fill=tk.BOTH, expand=True)

        q_cols = ("check", "id", "repo", "file", "size", "date", "dest", "status", "progress")
        self.tree_queue = ttk.Treeview(tree_container, columns=q_cols, show="headings", selectmode="extended")
        
        self.tree_queue.heading("check", text="选择", anchor=tk.CENTER)
        self.tree_queue.heading("id", text="#")
        self.tree_queue.heading("repo", text="仓库 (Repo ID)")
        self.tree_queue.heading("file", text="文件名 (File)")
        self.tree_queue.heading("size", text="大小")
        self.tree_queue.heading("date", text="日期")
        self.tree_queue.heading("dest", text="保存目标路径 (Destination)")
        self.tree_queue.heading("status", text="状态")
        self.tree_queue.heading("progress", text="进度")

        self.tree_queue.column("check", width=50, minwidth=40, stretch=False, anchor=tk.CENTER)
        self.tree_queue.column("id", width=38, minwidth=30, stretch=False, anchor=tk.CENTER)
        self.tree_queue.column("repo", width=180, minwidth=90, stretch=True, anchor=tk.W)
        self.tree_queue.column("file", width=220, minwidth=110, stretch=True, anchor=tk.W)
        self.tree_queue.column("size", width=85, minwidth=60, stretch=False, anchor=tk.E)
        self.tree_queue.column("date", width=130, minwidth=85, stretch=False, anchor=tk.CENTER)
        self.tree_queue.column("dest", width=260, minwidth=120, stretch=True, anchor=tk.W)
        self.tree_queue.column("status", width=90, minwidth=65, stretch=False, anchor=tk.CENTER)
        self.tree_queue.column("progress", width=65, minwidth=45, stretch=False, anchor=tk.CENTER)

        # Style Tags for Queue status
        self.tree_queue.tag_configure("status_done", foreground="#198754", font=FONT_TABLE_BOLD)
        self.tree_queue.tag_configure("status_downloading", foreground="#0d6efd", font=FONT_TABLE_BOLD)
        self.tree_queue.tag_configure("status_interrupted", foreground="#fd7e14", font=FONT_TABLE)
        self.tree_queue.tag_configure("status_failed", foreground="#dc3545", font=FONT_TABLE)
        self.tree_queue.tag_configure("status_pending", foreground="#6c757d", font=FONT_TABLE)

        q_scroll_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree_queue.yview)
        self.tree_queue.configure(yscrollcommand=q_scroll_y.set)

        self.tree_queue.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        q_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_queue.bind("<Button-1>", self._on_queue_tree_click)
        self.tree_queue.bind("<space>", self._on_queue_tree_space)
        self.tree_queue.bind("<Button-3>", self._show_context_menu)

        # Context Menu
        self.queue_menu = tk.Menu(self, tearoff=0, font=FONT_NORMAL)
        self.queue_menu.add_command(label="▶️ 恢复/下载选中的任务", command=self.action_resume_selected)
        self.queue_menu.add_command(label="⏸️ 暂停/终止选中的任务", command=self.action_pause_selected)
        self.queue_menu.add_command(label="🔄 重新下载 (从头下载)", command=self.action_restart_selected)
        self.queue_menu.add_separator()
        self.queue_menu.add_command(label="📂 打开保存目录", command=self.open_selected_task_folder)
        self.queue_menu.add_command(label="🗑️ 移除选中的任务 (可选清理缓存)", command=self.remove_selected_tasks)

        # Lower pane: Resizable log frame
        self.queue_pane_lower = ttk.LabelFrame(self.queue_paned, text=" 📜 实时运行日志 (拖动上方分割线可自由调节高度) ", padding="6")
        self.queue_paned.add(self.queue_pane_lower, weight=1)

        log_tool_bar = ttk.Frame(self.queue_pane_lower)
        log_tool_bar.pack(fill=tk.X, pady=(0, 2))

        btn_copy_log = ttk.Button(log_tool_bar, text=" 复制日志", image=self.icons["folder"], compound=tk.LEFT, command=self.copy_log_text)
        btn_copy_log.pack(side=tk.LEFT, padx=2)

        btn_clear_log = ttk.Button(log_tool_bar, text=" 清空日志", image=self.icons["trash"], compound=tk.LEFT, command=self.clear_log_text)
        btn_clear_log.pack(side=tk.LEFT, padx=2)

        self.log_text = tk.Text(self.queue_pane_lower, height=5, wrap=tk.WORD, font=FONT_LOG)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Queue control buttons bar
        q_btn_bar = ttk.Frame(self.tab_queue)
        q_btn_bar.pack(fill=tk.X, pady=(4, 0))

        self.btn_start_queue = ttk.Button(q_btn_bar, text=" 开始/恢复", image=self.icons["play"], compound=tk.LEFT, command=self.start_queue_download)
        self.btn_start_queue.pack(side=tk.LEFT, padx=3, ipady=3)

        self.btn_stop_queue = ttk.Button(q_btn_bar, text=" 暂停/终止", image=self.icons["pause"], compound=tk.LEFT, command=self.stop_queue_download, state=tk.DISABLED)
        self.btn_stop_queue.pack(side=tk.LEFT, padx=3, ipady=3)

        btn_hide_bg = ttk.Button(q_btn_bar, text=" 隐藏后台运行", image=self.icons["rocket"], compound=tk.LEFT, command=self.hide_to_background)
        btn_hide_bg.pack(side=tk.LEFT, padx=3, ipady=3)

        btn_remove_sel = ttk.Button(q_btn_bar, text=" 移除勾选任务", image=self.icons["trash"], compound=tk.LEFT, command=self.remove_selected_tasks)
        btn_remove_sel.pack(side=tk.LEFT, padx=3, ipady=3)

        btn_clear_done = ttk.Button(q_btn_bar, text=" 清理已完成", image=self.icons["clean"], compound=tk.LEFT, command=self.clear_completed_tasks)
        btn_clear_done.pack(side=tk.LEFT, padx=3, ipady=3)

        btn_clear_all = ttk.Button(q_btn_bar, text=" 清空全部", image=self.icons["trash"], compound=tk.LEFT, command=self.clear_all_tasks)
        btn_clear_all.pack(side=tk.LEFT, padx=3, ipady=3)

        self.show_log_var = tk.BooleanVar(value=True)
        chk_show_log = ttk.Checkbutton(
            q_btn_bar, 
            text="显示运行日志", 
            variable=self.show_log_var, 
            command=self._toggle_log_view
        )
        chk_show_log.pack(side=tk.LEFT, padx=10)

        btn_open_task_folder = ttk.Button(q_btn_bar, text=" 打开所在文件夹", image=self.icons["folder"], compound=tk.LEFT, command=self.open_selected_task_folder)
        btn_open_task_folder.pack(side=tk.RIGHT, padx=3, ipady=3)

    # ------------------ Tab 2 Checkbox Click & Toggle Events ------------------
    def _on_queue_tree_click(self, event):
        region = self.tree_queue.identify("region", event.x, event.y)
        if region == "heading":
            col = self.tree_queue.identify_column(event.x)
            if col == "#1":
                self._toggle_check_all_tasks()
                return "break"
        elif region in ("cell", "tree", "item"):
            item_id = self.tree_queue.identify_row(event.y)
            if item_id:
                try:
                    self._toggle_single_task_check(int(item_id))
                    self.tree_queue.selection_set(item_id)
                except Exception:
                    pass
                return "break"

    def _on_queue_tree_space(self, event):
        selected_iids = self.tree_queue.selection()
        if selected_iids:
            for iid in selected_iids:
                self._toggle_single_task_check(int(iid))
            return "break"

    def _toggle_single_task_check(self, task_id: int):
        if task_id in self.checked_tasks:
            self.checked_tasks.remove(task_id)
        else:
            self.checked_tasks.add(task_id)
        self._update_task_checkbox_display(task_id)
        self._update_queue_checked_label()

    def _update_task_checkbox_display(self, task_id: int):
        iid = str(task_id)
        if self.tree_queue.exists(iid):
            is_checked = task_id in self.checked_tasks
            check_symbol = "☑" if is_checked else "☐"
            cur_vals = list(self.tree_queue.item(iid, "values"))
            cur_vals[0] = check_symbol
            self.tree_queue.item(iid, values=cur_vals)

    def _update_queue_checked_label(self):
        cnt = len(self.checked_tasks)
        self.lbl_queue_checked.config(text=f"[已勾选: {cnt} 项]")

    def check_all_tasks(self):
        for task in self.tasks:
            self.checked_tasks.add(task.task_id)
            self._update_task_checkbox_display(task.task_id)
        self._update_queue_checked_label()

    def uncheck_all_tasks(self):
        self.checked_tasks.clear()
        for task in self.tasks:
            self._update_task_checkbox_display(task.task_id)
        self._update_queue_checked_label()

    def _toggle_check_all_tasks(self):
        if not self.tasks:
            return
        all_checked = all(t.task_id in self.checked_tasks for t in self.tasks)
        if all_checked:
            self.uncheck_all_tasks()
        else:
            self.check_all_tasks()

    def _toggle_log_view(self):
        if self.show_log_var.get():
            try:
                self.queue_paned.add(self.queue_pane_lower, weight=1)
            except Exception:
                pass
        else:
            try:
                self.queue_paned.forget(self.queue_pane_lower)
            except Exception:
                pass

    def copy_log_text(self):
        content = self.log_text.get("1.0", tk.END).strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            messagebox.showinfo("提示", "运行日志已复制到剪贴板。")

    def clear_log_text(self):
        self.log_text.delete("1.0", tk.END)

    # ------------------ Tab 3: Environment Setup & Directory Manager ------------------
    def _build_tab_env(self):
        paned_v = ttk.PanedWindow(self.tab_env, orient=tk.VERTICAL)
        paned_v.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Upper pane: ComfyUI Directory & Dependency Deploy Card
        pane_upper = ttk.Frame(paned_v)
        paned_v.add(pane_upper, weight=2)

        # 1. ComfyUI Directory Auto-Deploy Box
        comfy_box = ttk.LabelFrame(pane_upper, text=" 📁 ComfyUI 模型根目录与预设分类部署 ", padding="8")
        comfy_box.pack(fill=tk.X, pady=(0, 6))

        row_cf = ttk.Frame(comfy_box)
        row_cf.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(row_cf, text="ComfyUI 模型根路径:", font=FONT_BOLD).pack(side=tk.LEFT, padx=(0, 4))
        self.tab_env_comfy_var = tk.StringVar(value=DEFAULT_COMFYUI_ROOT)
        entry_cf = ttk.Entry(row_cf, textvariable=self.tab_env_comfy_var, font=FONT_NORMAL)
        entry_cf.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        btn_detect_cf = ttk.Button(row_cf, text=" 智能探测", image=self.icons["search"], compound=tk.LEFT, command=self._auto_detect_comfy_root)
        btn_detect_cf.pack(side=tk.LEFT, padx=2)

        btn_browse_cf = ttk.Button(row_cf, text=" 浏览目录...", command=self._browse_comfy_root)
        btn_browse_cf.pack(side=tk.LEFT, padx=2)

        btn_deploy_all = tk.Button(
            row_cf,
            text=" 📁 一键创建全部预设子目录 ",
            font=FONT_BOLD,
            bg="#198754",
            fg="#ffffff",
            activebackground="#157347",
            activeforeground="#ffffff",
            padx=8, pady=2,
            command=self._create_all_preset_dirs
        )
        btn_deploy_all.pack(side=tk.LEFT, padx=(4, 0))

        # Directory status tree
        cols_dir = ("name", "status", "path", "action")
        self.tree_tab_dirs = ttk.Treeview(comfy_box, columns=cols_dir, show="headings", height=5)
        self.tree_tab_dirs.heading("name", text="常用预设模型分类", anchor=tk.W)
        self.tree_tab_dirs.heading("status", text="状态", anchor=tk.CENTER)
        self.tree_tab_dirs.heading("path", text="完整物理保存路径", anchor=tk.W)
        self.tree_tab_dirs.heading("action", text="操作 (双击直接打开)", anchor=tk.CENTER)

        self.tree_tab_dirs.column("name", width=180, minwidth=140, stretch=False, anchor=tk.W)
        self.tree_tab_dirs.column("status", width=80, minwidth=70, stretch=False, anchor=tk.CENTER)
        self.tree_tab_dirs.column("path", width=380, minwidth=200, stretch=True, anchor=tk.W)
        self.tree_tab_dirs.column("action", width=140, minwidth=100, stretch=False, anchor=tk.CENTER)

        self.tree_tab_dirs.tag_configure("ok_tag", foreground="#198754", font=FONT_TABLE_BOLD)
        self.tree_tab_dirs.tag_configure("missing_tag", foreground="#dc3545", font=FONT_TABLE_BOLD)

        self.tree_tab_dirs.pack(fill=tk.X, expand=True, pady=(4, 0))
        self.tree_tab_dirs.bind("<Double-1>", self._on_tree_tab_dir_double_click)

        # 2. Python Packages Dependency Status Box
        dep_box = ttk.LabelFrame(pane_upper, text=" 📦 Python 核心依赖与加速组件检测 ", padding="8")
        dep_box.pack(fill=tk.X, pady=(0, 4))

        cols_pkg = ("pkg", "status", "version", "desc")
        self.tree_tab_pkgs = ttk.Treeview(dep_box, columns=cols_pkg, show="headings", height=4)
        self.tree_tab_pkgs.heading("pkg", text="组件名称", anchor=tk.W)
        self.tree_tab_pkgs.heading("status", text="安装状态", anchor=tk.CENTER)
        self.tree_tab_pkgs.heading("version", text="当前版本", anchor=tk.CENTER)
        self.tree_tab_pkgs.heading("desc", text="作用说明", anchor=tk.W)

        self.tree_tab_pkgs.column("pkg", width=140, minwidth=110, stretch=False, anchor=tk.W)
        self.tree_tab_pkgs.column("status", width=90, minwidth=70, stretch=False, anchor=tk.CENTER)
        self.tree_tab_pkgs.column("version", width=95, minwidth=75, stretch=False, anchor=tk.CENTER)
        self.tree_tab_pkgs.column("desc", width=340, minwidth=180, stretch=True, anchor=tk.W)

        self.tree_tab_pkgs.tag_configure("ok_tag", foreground="#198754", font=FONT_TABLE_BOLD)
        self.tree_tab_pkgs.tag_configure("missing_tag", foreground="#dc3545", font=FONT_TABLE_BOLD)

        self.tree_tab_pkgs.pack(fill=tk.X, expand=True, pady=(0, 4))

        opt_bar = ttk.Frame(dep_box)
        opt_bar.pack(fill=tk.X, pady=(2, 0))

        ttk.Label(opt_bar, text="⚡ PyPI 加速源:").pack(side=tk.LEFT, padx=(0, 4))
        self.tab_pypi_mirror_var = tk.StringVar(value=list(PYPI_MIRRORS.keys())[0])
        pypi_combo = ttk.Combobox(opt_bar, textvariable=self.tab_pypi_mirror_var, values=list(PYPI_MIRRORS.keys()), width=22, state="readonly", font=FONT_NORMAL)
        pypi_combo.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_tab_install_deps = tk.Button(
            opt_bar,
            text=" 🚀 一键极速下载并安装全部缺失依赖 ",
            font=FONT_BOLD,
            bg="#0d6efd",
            fg="#ffffff",
            activebackground="#0b5ed7",
            activeforeground="#ffffff",
            padx=10, pady=2,
            command=self._install_tab_env_dependencies
        )
        self.btn_tab_install_deps.pack(side=tk.LEFT, padx=4)

        btn_recheck_dep = ttk.Button(opt_bar, text=" 🔄 刷新依赖检测", command=self._check_tab_env_status)
        btn_recheck_dep.pack(side=tk.RIGHT)

        # Lower Pane: Realtime terminal log
        pane_lower = ttk.Frame(paned_v)
        paned_v.add(pane_lower, weight=1)

        log_box = ttk.LabelFrame(pane_lower, text=" 📜 依赖安装与环境部署终端输出 ", padding="6")
        log_box.pack(fill=tk.BOTH, expand=True)

        self.tab_env_log_text = tk.Text(log_box, font=FONT_LOG, bg="#1e1e1e", fg="#d4d4d4", wrap=tk.WORD, height=6)
        scroll = ttk.Scrollbar(log_box, orient=tk.VERTICAL, command=self.tab_env_log_text.yview)
        self.tab_env_log_text.configure(yscrollcommand=scroll.set)

        self.tab_env_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._refresh_tab_env_dirs()
        self._check_tab_env_status()

    def _browse_comfy_root(self):
        d = filedialog.askdirectory(title="选择 ComfyUI 模型根目录 (models)")
        if d:
            self.tab_env_comfy_var.set(os.path.normpath(d))
            self._refresh_tab_env_dirs()

    def _auto_detect_comfy_root(self):
        candidates = [
            r"F:\ComfyUI-aki-v3\ComfyUI\models",
            r"D:\ComfyUI-aki-v3\ComfyUI\models",
            r"E:\ComfyUI-aki-v3\ComfyUI\models",
            r"C:\ComfyUI-aki-v3\ComfyUI\models",
            r"D:\ComfyUI\models",
            r"E:\ComfyUI\models",
            r"F:\ComfyUI\models",
        ]
        for c in candidates:
            if os.path.exists(c):
                self.tab_env_comfy_var.set(c)
                self._refresh_tab_env_dirs()
                messagebox.showinfo("检测成功", f"成功探测到 ComfyUI 模型目录:\n{c}")
                return
        messagebox.showwarning("提示", "未能自动探测到 ComfyUI 路径，请点击【浏览目录...】手动选择。")

    def _refresh_tab_env_dirs(self):
        self.tree_tab_dirs.delete(*self.tree_tab_dirs.get_children())
        base = self.tab_env_comfy_var.get().strip()
        for label, rel_or_abs in PRESET_DIRS_MAP.items():
            folder_name = label.split("(")[-1].rstrip(")")
            target_path = os.path.join(base, folder_name) if not os.path.isabs(rel_or_abs) else rel_or_abs
            exists = os.path.exists(target_path)
            status_text = "✓ 已就绪" if exists else "✗ 未创建"
            tag = "ok_tag" if exists else "missing_tag"
            action_text = "📂 点击打开" if exists else "➕ 待创建"
            self.tree_tab_dirs.insert("", tk.END, values=(label, status_text, target_path, action_text), tags=(tag,))

    def _on_tree_tab_dir_double_click(self, event):
        item_id = self.tree_tab_dirs.focus()
        if not item_id:
            return
        vals = self.tree_tab_dirs.item(item_id, "values")
        if vals and len(vals) >= 3:
            path = vals[2]
            if os.path.exists(path):
                os.startfile(path)
            else:
                if messagebox.askyesno("创建目录", f"目录不存在，是否立即创建？\n{path}"):
                    try:
                        os.makedirs(path, exist_ok=True)
                        self._refresh_tab_env_dirs()
                        messagebox.showinfo("成功", f"目录已成功创建:\n{path}")
                    except Exception as err:
                        messagebox.showerror("错误", f"创建失败: {str(err)}")

    def _create_all_preset_dirs(self):
        base = self.tab_env_comfy_var.get().strip()
        created = 0
        for label, rel_or_abs in PRESET_DIRS_MAP.items():
            folder_name = label.split("(")[-1].rstrip(")")
            target_path = os.path.join(base, folder_name) if not os.path.isabs(rel_or_abs) else rel_or_abs
            if not os.path.exists(target_path):
                try:
                    os.makedirs(target_path, exist_ok=True)
                    created += 1
                except Exception:
                    pass
        self._refresh_tab_env_dirs()
        messagebox.showinfo("完成", f"一键环境部署完成！共补齐/创建 {created} 个模型分类目录。")

    def _check_tab_env_status(self):
        self.tree_tab_pkgs.delete(*self.tree_tab_pkgs.get_children())
        import importlib.metadata
        for pkg_name, desc in CORE_PACKAGES:
            norm_name = pkg_name.replace("_", "-")
            installed = False
            ver_str = "--"
            for test_name in (pkg_name, norm_name):
                try:
                    ver_str = importlib.metadata.version(test_name)
                    installed = True
                    break
                except Exception:
                    pass
            if installed:
                self.tree_tab_pkgs.insert("", tk.END, values=(pkg_name, "✓ 已安装", ver_str, desc), tags=("ok_tag",))
            else:
                self.tree_tab_pkgs.insert("", tk.END, values=(pkg_name, "✗ 缺失", "--", desc), tags=("missing_tag",))

    def _install_tab_env_dependencies(self):
        self.btn_tab_install_deps.config(state=tk.DISABLED, text=" 正在下载与安装部署中... ")
        mirror_name = self.tab_pypi_mirror_var.get()
        mirror_url = PYPI_MIRRORS.get(mirror_name, "https://pypi.tuna.tsinghua.edu.cn/simple")

        self.tab_env_log_text.insert(tk.END, f"\n[INFO] 开始通过加速源 {mirror_name} ({mirror_url}) 一键部署依赖...\n")
        self.tab_env_log_text.see(tk.END)

        def _worker():
            pkgs = [p[0] for p in CORE_PACKAGES]
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + pkgs + ["-i", mirror_url]
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8", errors="replace")
                for line in proc.stdout:
                    self.after(0, lambda l=line: (self.tab_env_log_text.insert(tk.END, l), self.tab_env_log_text.see(tk.END)))
                proc.wait()
                if proc.returncode == 0:
                    self.after(0, lambda: messagebox.showinfo("成功", "所有核心依赖已成功安装并部署完成！"))
                    self.after(0, self._on_env_setup_completed)
                else:
                    self.after(0, lambda: messagebox.showwarning("提示", "安装过程已结束，部分依赖可能有提示，请检查日志。"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("错误", f"执行异常: {str(e)}"))
            finally:
                self.after(0, lambda: self.btn_tab_install_deps.config(state=tk.NORMAL, text=" 🚀 一键极速下载并安装全部缺失依赖 "))
                self.after(0, self._check_tab_env_status)

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------ Bottom Global Progress Panel ------------------
    def _build_bottom_panel(self, parent):
        prog_frame = ttk.LabelFrame(parent, text=" 实时下载进度 ", padding="8")
        prog_frame.pack(fill=tk.X, pady=(0, 2))

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(prog_frame, variable=self.progress_var, maximum=100.0)
        self.progress_bar.pack(fill=tk.X, pady=(2, 4))

        detail_frame = ttk.Frame(prog_frame)
        detail_frame.pack(fill=tk.X)

        self.lbl_progress_text = ttk.Label(detail_frame, text="进度: 0%", font=FONT_NORMAL)
        self.lbl_progress_text.pack(side=tk.LEFT)

        self.lbl_speed_text = ttk.Label(detail_frame, text="速度: 0 KB/s", font=FONT_NORMAL)
        self.lbl_speed_text.pack(side=tk.RIGHT)

        self.lbl_status = ttk.Label(prog_frame, text="状态: 就绪", foreground="#555555", font=FONT_NORMAL)
        self.lbl_status.pack(anchor=tk.W, pady=(2, 0))

    def _show_context_menu(self, event):
        item = self.tree_queue.identify_row(event.y)
        if item:
            if item not in self.tree_queue.selection():
                self.tree_queue.selection_set(item)
            self.queue_menu.post(event.x_root, event.y_root)

    # ------------------ Background Active Check & Lock ------------------
    def _check_background_active_tasks(self):
        if os.path.exists(LOCK_FILE):
            try:
                with open(LOCK_FILE, "r") as f:
                    data = json.load(f)
                    pid = data.get("pid")
                    started = data.get("started_at", "未知")
                    if pid and self._is_pid_running(pid) and pid != os.getpid():
                        self.log(f"[提示] 检测到另一个下载器后台进程正在运行 (PID: {pid}, 启动于: {started})。")
            except Exception:
                pass

    def _is_pid_running(self, pid: int) -> bool:
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x00100000
            process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if process:
                kernel32.CloseHandle(process)
                return True
            return False
        except Exception:
            return False

    def _update_lock_file(self, active: bool):
        if active:
            try:
                with open(LOCK_FILE, "w") as f:
                    json.dump({
                        "pid": os.getpid(),
                        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "active_task": self.active_task_id
                    }, f)
            except Exception:
                pass
        else:
            if os.path.exists(LOCK_FILE):
                try:
                    os.remove(LOCK_FILE)
                except Exception:
                    pass

    def check_active_background_downloads(self):
        self.lbl_status.config(text="状态: 正在检测本地未完成任务是否有后台写入...", foreground="blue")
        self.log("[*] 正在扫描检测未完成文件的实时传输状态...")

        threading.Thread(target=self._check_active_downloads_worker, daemon=True).start()

    def _check_active_downloads_worker(self):
        temp_files: List[Tuple[QueueTask, str, int]] = []
        for t in self.tasks:
            temp_path = t.get_temp_file_path()
            if os.path.exists(temp_path):
                temp_files.append((t, temp_path, os.path.getsize(temp_path)))

        if not temp_files:
            self.after(0, lambda: self.log("[✓] 未发现任何正在传输的后台临时文件。"))
            self.after(0, lambda: self.lbl_status.config(text="状态: 未检测到后台活跃下载", foreground="#555555"))
            self.after(0, lambda: messagebox.showinfo("检测结果", "未发现任何正在下载或中断的临时文件。"))
            return

        time.sleep(0.8)
        active_list = []
        stopped_list = []

        for task, path, initial_size in temp_files:
            if os.path.exists(path):
                cur_size = os.path.getsize(path)
                diff = cur_size - initial_size
                if diff > 0:
                    speed = diff / 0.8
                    active_list.append((task, speed))
                else:
                    stopped_list.append(task)

        def update_ui_result():
            if active_list:
                msg = f"检测到 {len(active_list)} 个任务正在被后台进程活跃下载中:\n"
                for t, spd in active_list:
                    msg += f"• [{t.task_id}] {os.path.basename(t.file_path)} (写入速率: {self._format_size(int(spd))}/s)\n"
                self.log("[🔴 活跃后台任务]\n" + msg)
                messagebox.showinfo("后台任务检测", msg)
            else:
                self.log(f"[✓] 检测到 {len(stopped_list)} 个中断/静止文件，当前无后台进程在写入，可安全点击【开始/恢复】接续下载。")
                messagebox.showinfo("后台任务检测", f"检测到 {len(stopped_list)} 个未完成的缓存文件，当前没有活跃的后台下载进程，您可以随时点击【恢复下载】继续。")
            self.lbl_status.config(text="状态: 检测完成", foreground="green")

        self.after(0, update_ui_result)

    # ------------------ Safe Exit & Minimize to Background ------------------
    def hide_to_background(self):
        if not self.is_queue_running:
            if messagebox.askyesno("提示", "当前没有正在进行的下载任务，确定要最小化隐藏到后台吗？"):
                self.iconify()
        else:
            messagebox.showinfo("后台静默运行", "下载器已在后台全速下载。\n您可以通过任务栏或重新运行启动器随时切回窗口。")
            self.iconify()

    def _on_window_closing(self):
        if self.is_queue_running:
            choice = messagebox.askyesnocancel(
                "下载正在进行中",
                "当前有任务正在下载中！\n\n"
                "• 点击【是 (Yes)】：最小化到后台继续静默下载\n"
                "• 点击【否 (No)】：暂停当前下载并保存进度后退出\n"
                "• 点击【取消 (Cancel)】：留在此页面"
            )
            if choice is True:
                self.iconify()
                return
            elif choice is False:
                self.stop_queue_requested = True
                self.cancel_current_task = True
                self._save_tasks()
                self._save_settings()
                self._update_lock_file(False)
                self.destroy()
            else:
                return
        else:
            self._save_tasks()
            self._save_settings()
            self._update_lock_file(False)
            self.destroy()

    # ------------------ Task Persistence & Rescan ------------------
    def _load_saved_tasks(self):
        if os.path.exists(TASKS_DB_FILE):
            try:
                with open(TASKS_DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    task_list = data.get("tasks", [])
                    max_id = 0
                    self.tasks = []
                    for t_dict in task_list:
                        task = QueueTask.from_dict(t_dict)
                        self.tasks.append(task)
                        if task.task_id > max_id:
                            max_id = task.task_id
                    self.task_counter = max_id + 1
                    self.log(f"[*] 已自动从本地记录恢复 {len(self.tasks)} 个任务。")
            except Exception as e:
                self.log(f"[警告] 读取历史任务失败: {str(e)}")

        self.rescan_all_tasks(silent=True)

    def _save_tasks(self):
        try:
            data = {
                "tasks": [t.to_dict() for t in self.tasks]
            }
            with open(TASKS_DB_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"[警告] 保存任务列表失败: {str(e)}")

    def rescan_all_tasks(self, silent=False):
        interrupted_count = 0
        done_count = 0
        pending_count = 0

        for t in self.tasks:
            if t.status != "下载中":
                t.check_local_status()
            if t.status == "已中断":
                interrupted_count += 1
            elif t.status == "已完成":
                done_count += 1
            elif t.status in ("等待中", "已暂停"):
                pending_count += 1

        self._refresh_queue_tree()
        self._save_tasks()

        stats_text = f"任务统计: 共 {len(self.tasks)} 项 | 已完成 {done_count} | 已中断(可续传) {interrupted_count} | 等待中 {pending_count}"
        self.lbl_queue_stats.config(text=stats_text)
        self._update_queue_checked_label()

        if not silent:
            self.log(f"[✓] 重新扫描完成: {stats_text}")
            if interrupted_count > 0:
                self.log(f"提示: 检测到 {interrupted_count} 个中断任务，点击【开始/恢复下载队列】即可自动断点续传。")

    def _check_dependency(self):
        global HfApi
        if HfApi is None:
            self.log("⚠️ [重要提示] 尚未检测到 huggingface_hub 依赖库！建议点击右上角【🚀 一键部署环境...】一键自动安装。")
        else:
            self.log("✨ [就绪] 核心下载环境与依赖检测正常，支持断点续传与极速镜像加速！")

    def log(self, text: str):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def _on_preset_selected(self, event=None):
        selected_label = self.preset_var.get()
        if selected_label in PRESET_DIRS_MAP:
            self.dest_dir_var.set(PRESET_DIRS_MAP[selected_label])

    def browse_dest_dir(self):
        cur_dir = self.dest_dir_var.get()
        selected = filedialog.askdirectory(initialdir=cur_dir if os.path.exists(cur_dir) else None)
        if selected:
            norm_dir = os.path.normpath(selected)
            self.dest_dir_var.set(norm_dir)
            found = False
            for label, p in PRESET_DIRS_MAP.items():
                if os.path.normpath(p).lower() == norm_dir.lower():
                    self.preset_var.set(label)
                    found = True
                    break
            if not found:
                self.preset_var.set("-- 自定义目录 --")

    def _format_size(self, size_bytes: Optional[int]) -> str:
        if size_bytes is None:
            return "--"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _format_date(self, dt: Any) -> str:
        if not dt:
            return "--"
        if isinstance(dt, datetime.datetime):
            return dt.strftime("%Y-%m-%d %H:%M")
        if isinstance(dt, str):
            try:
                clean_str = dt.replace("Z", "+00:00")
                parsed = datetime.datetime.fromisoformat(clean_str)
                return parsed.strftime("%Y-%m-%d %H:%M")
            except:
                return dt[:16] if len(dt) >= 16 else dt
        return str(dt)

    # ------------------ Tab 1 Actions & Population ------------------
    def start_fetch_files(self):
        repo_id = self.repo_id_var.get().strip()
        if not repo_id:
            messagebox.showwarning("提示", "请输入有效的 Repo ID！")
            return

        endpoint = self.mirror_var.get().strip().rstrip("/")
        if endpoint and endpoint not in self.mirrors_list:
            self.mirrors_list.append(endpoint)
            self._save_mirrors()
            self.mirror_combo["values"] = self.mirrors_list

        self._save_settings()

        self.btn_fetch.config(state=tk.DISABLED)
        self.lbl_status.config(text="状态: 正在获取文件列表与目录树...", foreground="blue")
        proxy_info = self._get_effective_proxy()
        self.log(f"[*] 正在从 {endpoint} (代理: {proxy_info or '直连'}) 查询仓库 '{repo_id}' 的目录结构与文件...")

        threading.Thread(target=self._fetch_files_worker, daemon=True).start()

    def _fetch_files_worker(self):
        repo_id = self.repo_id_var.get().strip()
        repo_type = self.repo_type_var.get().strip()
        branch = self.branch_var.get().strip() or "main"
        endpoint = self.mirror_var.get().strip().rstrip("/")
        token = self.token_var.get().strip() or None
        proxies = self._get_request_proxies()

        files_map = {}
        err_msg = None

        try:
            api = HfApi(endpoint=endpoint, token=token, proxies=proxies)
            tree = list(api.list_repo_tree(repo_id, repo_type=repo_type, revision=branch, recursive=True, expand=True))
            for item in tree:
                type_name = type(item).__name__
                if type_name == "RepoFolder" or getattr(item, "type", None) == "directory":
                    continue
                
                if type_name == "RepoFile" or getattr(item, "size", None) is not None or getattr(item, "lfs", None) is not None:
                    rfilename = item.path
                    raw_size = getattr(item, "size", None)
                    lfs_info = getattr(item, "lfs", None)
                    if lfs_info:
                        lfs_size = getattr(lfs_info, "size", None) if not isinstance(lfs_info, dict) else lfs_info.get("size")
                        if lfs_size is not None and lfs_size > 0:
                            raw_size = lfs_size
                    
                    size_str = self._format_size(raw_size)
                    
                    last_commit = getattr(item, "last_commit", None)
                    raw_date = getattr(last_commit, "date", None) if last_commit else None
                    date_str = self._format_date(raw_date)

                    files_map[rfilename] = {
                        "path": rfilename,
                        "size_str": size_str,
                        "date_str": date_str,
                        "raw_size": raw_size or 0,
                        "raw_date": raw_date
                    }
        except Exception as e:
            err_msg = str(e)

        # Fallback 1: Direct High-Performance REST API /tree/ query
        if not files_map:
            try:
                base_type = "models" if repo_type == "model" else (repo_type + "s" if not repo_type.endswith("s") else repo_type)
                api_url = f"{endpoint}/api/{base_type}/{repo_id}/tree/{branch}?recursive=True"
                headers = {"User-Agent": "HF-Downloader-GUI/1.0"}
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                resp = requests.get(api_url, headers=headers, proxies=proxies, timeout=12)
                if resp.status_code == 200:
                    tree_data = resp.json()
                    if isinstance(tree_data, list):
                        for item in tree_data:
                            if item.get("type") == "directory":
                                continue
                            rfilename = item.get("path")
                            if rfilename:
                                raw_size = item.get("size")
                                lfs = item.get("lfs")
                                if isinstance(lfs, dict) and lfs.get("size"):
                                    raw_size = lfs.get("size")
                                
                                size_str = self._format_size(raw_size)
                                last_mod = item.get("lastModified")
                                date_str = self._format_date(last_mod)
                                files_map[rfilename] = {
                                    "path": rfilename,
                                    "size_str": size_str,
                                    "date_str": date_str,
                                    "raw_size": raw_size or 0,
                                    "raw_date": last_mod
                                }
                        err_msg = None
            except Exception as e2:
                err_msg = str(e2)

        # Fallback 2: Repo info
        if not files_map:
            try:
                api = HfApi(endpoint=endpoint, token=token, proxies=proxies)
                info = api.model_info(repo_id, files_metadata=True) if repo_type == "model" else api.repo_info(repo_id, repo_type=repo_type, files_metadata=True)
                global_date_str = self._format_date(getattr(info, "lastModified", None))
                
                for item in info.siblings:
                    rfilename = getattr(item, "rfilename", None) or getattr(item, "path", None)
                    if rfilename:
                        raw_size = getattr(item, "size", None)
                        lfs = getattr(item, "lfs", None)
                        if lfs:
                            lfs_size = getattr(lfs, "size", None) if not isinstance(lfs, dict) else lfs.get("size")
                            if lfs_size:
                                raw_size = lfs_size
                        size_str = self._format_size(raw_size)
                        files_map[rfilename] = {
                            "path": rfilename,
                            "size_str": size_str,
                            "date_str": global_date_str,
                            "raw_size": raw_size or 0,
                            "raw_date": None
                        }
                err_msg = None
            except Exception as e3:
                err_msg = str(e3)

        if files_map:
            self.raw_files_dict = files_map
            self.checked_files.clear()
            self.after(0, self._populate_dual_pane_browser)
            self.after(0, lambda: self.log(f"[✓] 成功获取到 {len(files_map)} 个文件，已按双栏文件浏览器组织。"))
            self.after(0, lambda: self.lbl_status.config(text=f"状态: 共获取到 {len(files_map)} 个文件", foreground="green"))
        else:
            self.after(0, lambda: self.log(f"[错误] 获取文件列表失败: {err_msg}"))
            self.after(0, lambda: self.lbl_status.config(text="状态: 获取失败", foreground="red"))
            self.after(0, lambda: messagebox.showerror("获取失败", f"无法获取仓库文件列表:\n{err_msg}\n\n提示: 如遇网络连接超时，可尝试切换镜像源或在上方设置网络代理 (Proxy)。"))

        self.after(0, lambda: self.btn_fetch.config(state=tk.NORMAL))

    def _populate_dual_pane_browser(self):
        self.tree_dirs.delete(*self.tree_dirs.get_children())
        
        all_dirs = set()
        for fpath in self.raw_files_dict.keys():
            parts = fpath.split("/")
            for i in range(1, len(parts)):
                all_dirs.add("/".join(parts[:i]))

        sorted_dirs = sorted(list(all_dirs))
        self.lbl_dir_count.config(text=f"目录: {len(sorted_dirs) + 1} 个")

        root_iid = self.tree_dirs.insert("", tk.END, iid="ROOT", text="📁 全部文件 (根目录 /)", open=True, tags=("root_node",))

        dir_nodes = {"": root_iid}
        for dpath in sorted_dirs:
            parts = dpath.split("/")
            parent_path = "/".join(parts[:-1]) if len(parts) > 1 else ""
            parent_id = dir_nodes.get(parent_path, root_iid)
            
            node_id = self.tree_dirs.insert(
                parent_id, tk.END,
                iid=dpath,
                text=f"📁 {parts[-1]}",
                open=True,
                tags=("folder_node",)
            )
            dir_nodes[dpath] = node_id

        if "controlnet" in dir_nodes:
            self.tree_dirs.selection_set("controlnet")
            self.tree_dirs.see("controlnet")
            self.current_selected_dir = "controlnet"
        else:
            self.tree_dirs.selection_set(root_iid)
            self.current_selected_dir = ""

        self._refresh_right_file_table()

    def _on_dir_selected(self, event=None):
        selected = self.tree_dirs.selection()
        if not selected:
            return
        node_id = selected[0]
        self.current_selected_dir = "" if node_id == "ROOT" else node_id
        self._refresh_right_file_table()

    def _refresh_right_file_table(self):
        self.tree_files.delete(*self.tree_files.get_children())
        
        cur_dir = self.current_selected_dir
        if not cur_dir:
            self.lbl_current_path.config(text="当前位置: / (根目录)")
        else:
            self.lbl_current_path.config(text=f"当前位置: /{cur_dir}")

        filter_kw = self.filter_var.get().lower().strip()

        matched_items = []
        for fpath, meta in self.raw_files_dict.items():
            if not cur_dir:
                if "/" in fpath:
                    continue
            else:
                prefix = cur_dir + "/"
                if not fpath.startswith(prefix):
                    continue
                rel_path = fpath[len(prefix):]
                if "/" in rel_path:
                    continue

            if filter_kw and filter_kw not in fpath.lower():
                continue

            matched_items.append((fpath, meta))

        matched_items.sort(key=lambda x: x[0])

        target_sel_iid = None
        for fpath, meta in matched_items:
            fname = os.path.basename(fpath)
            ext = os.path.splitext(fname)[1].lower()
            
            if ext in (".safetensors", ".bin", ".pt", ".pth", ".onnx", ".ckpt", ".gguf"):
                icon = "📦 "
            else:
                icon = "📄 "

            display_name = icon + fname
            is_checked = fpath in self.checked_files
            check_symbol = "☑" if is_checked else "☐"

            iid = self.tree_files.insert(
                "", tk.END,
                iid=fpath,
                values=(check_symbol, display_name, meta["size_str"], meta["date_str"], fpath),
                tags=("checked_tag" if is_checked else "file_tag",)
            )

            if "minimax_h3_fun_controlnet" in fpath:
                target_sel_iid = iid

        if target_sel_iid:
            self.tree_files.selection_set(target_sel_iid)
            self.tree_files.see(target_sel_iid)

        self._update_checked_count_label()

    def _apply_file_filter(self):
        self._refresh_right_file_table()

    def expand_all_dirs(self):
        def _open_all(item):
            self.tree_dirs.item(item, open=True)
            for child in self.tree_dirs.get_children(item):
                _open_all(child)
        for root_item in self.tree_dirs.get_children():
            _open_all(root_item)

    def collapse_all_dirs(self):
        def _close_all(item):
            self.tree_dirs.item(item, open=False)
            for child in self.tree_dirs.get_children(item):
                _close_all(child)
        for root_item in self.tree_dirs.get_children():
            _close_all(root_item)

    # ------------------ Queue Management (Dual-Pane Checkbox Actions) ------------------
    def add_selected_to_queue(self, jump=False):
        target_fpaths = list(self.checked_files)
        if not target_fpaths:
            selected_rows = self.tree_files.selection()
            if selected_rows:
                target_fpaths = list(selected_rows)

        if not target_fpaths:
            messagebox.showwarning("提示", "请先在右侧文件列表中勾选复选框 ☑ 或高亮选择要下载的文件！\n（或点击【将当前左侧目录全部文件加入下载队列】）")
            return

        dest_dir = self.dest_dir_var.get().strip()
        if not dest_dir:
            messagebox.showwarning("提示", "请设置目标保存目录！")
            return

        repo_id = self.repo_id_var.get().strip()
        repo_type = self.repo_type_var.get().strip()
        branch = self.branch_var.get().strip() or "main"
        endpoint = self.mirror_var.get().strip().rstrip("/")
        token = self.token_var.get().strip() or None
        proxy = self._get_effective_proxy()
        flatten = self.flatten_var.get()

        added_count = 0
        for fpath in sorted(target_fpaths):
            item_meta = self.raw_files_dict.get(fpath, {})
            size_str = item_meta.get("size_str", "--")
            date_str = item_meta.get("date_str", "--")
            raw_size = item_meta.get("raw_size")

            exists = False
            for t in self.tasks:
                if t.repo_id == repo_id and t.file_path == fpath and t.dest_dir == dest_dir:
                    exists = True
                    break
            if exists:
                continue

            task = QueueTask(
                task_id=self.task_counter,
                repo_id=repo_id,
                repo_type=repo_type,
                branch=branch,
                file_path=fpath,
                size_str=size_str,
                date_str=date_str,
                dest_dir=dest_dir,
                flatten=flatten,
                endpoint=endpoint,
                token=token,
                proxy=proxy,
                total_bytes=raw_size
            )
            task.check_local_status()
            self.tasks.append(task)
            self.task_counter += 1
            added_count += 1

        self.rescan_all_tasks(silent=True)
        self.log(f"[+] 已将 {added_count} 个文件加入下载队列 -> 保存至: {dest_dir}")

        if jump:
            self.notebook.select(2)

    def add_current_dir_to_queue(self):
        cur_dir = self.current_selected_dir
        matched_files = []
        for fpath in self.raw_files_dict.keys():
            if cur_dir:
                if fpath == cur_dir or fpath.startswith(cur_dir + "/"):
                    matched_files.append(fpath)
            else:
                matched_files.append(fpath)

        if not matched_files:
            messagebox.showinfo("提示", "当前目录下没有文件。")
            return

        dest_dir = self.dest_dir_var.get().strip()
        if not dest_dir:
            messagebox.showwarning("提示", "请设置目标保存目录！")
            return

        repo_id = self.repo_id_var.get().strip()
        repo_type = self.repo_type_var.get().strip()
        branch = self.branch_var.get().strip() or "main"
        endpoint = self.mirror_var.get().strip().rstrip("/")
        token = self.token_var.get().strip() or None
        proxy = self._get_effective_proxy()
        flatten = self.flatten_var.get()

        added_count = 0
        for fpath in matched_files:
            item_meta = self.raw_files_dict.get(fpath, {})
            size_str = item_meta.get("size_str", "--")
            date_str = item_meta.get("date_str", "--")
            raw_size = item_meta.get("raw_size")

            exists = False
            for t in self.tasks:
                if t.repo_id == repo_id and t.file_path == fpath and t.dest_dir == dest_dir:
                    exists = True
                    break
            if exists:
                continue

            task = QueueTask(
                task_id=self.task_counter,
                repo_id=repo_id,
                repo_type=repo_type,
                branch=branch,
                file_path=fpath,
                size_str=size_str,
                date_str=date_str,
                dest_dir=dest_dir,
                flatten=flatten,
                endpoint=endpoint,
                token=token,
                proxy=proxy,
                total_bytes=raw_size
            )
            task.check_local_status()
            self.tasks.append(task)
            self.task_counter += 1
            added_count += 1

        self.rescan_all_tasks(silent=True)
        dir_name = cur_dir if cur_dir else "根目录"
        self.log(f"[+] 已将目录 '{dir_name}' 下的 {added_count} 个文件加入下载队列 -> 保存至: {dest_dir}")
        messagebox.showinfo("已加入队列", f"已将目录 '{dir_name}' 下的 {added_count} 个文件成功加入下载队列！")

    def _refresh_queue_tree(self):
        self.tree_queue.delete(*self.tree_queue.get_children())
        for task in self.tasks:
            if task.status == "已完成":
                s_tag = "status_done"
            elif task.status == "下载中":
                s_tag = "status_downloading"
            elif task.status == "已中断":
                s_tag = "status_interrupted"
            elif task.status == "失败":
                s_tag = "status_failed"
            else:
                s_tag = "status_pending"

            is_checked = task.task_id in self.checked_tasks
            check_symbol = "☑" if is_checked else "☐"

            self.tree_queue.insert("", tk.END, iid=str(task.task_id), values=(
                check_symbol,
                task.task_id,
                task.repo_id,
                os.path.basename(task.file_path),
                task.size_str,
                task.date_str,
                task.dest_dir,
                task.status,
                f"{task.progress:.1f}%"
            ), tags=(s_tag,))

        pending_count = sum(1 for t in self.tasks if t.status in ("等待中", "下载中", "已中断"))
        self.notebook.tab(2, text=f" 📑 统一下载队列 ({pending_count}) ")
        self._update_queue_checked_label()

    def _get_target_task_ids(self) -> List[int]:
        if self.checked_tasks:
            return list(self.checked_tasks)
        selected_iids = self.tree_queue.selection()
        if selected_iids:
            return [int(iid) for iid in selected_iids]
        return []

    # ------------------ Advanced Safe Task Removal with Cache Cleaning ------------------
    def remove_selected_tasks(self):
        target_ids = self._get_target_task_ids()
        if not target_ids:
            messagebox.showinfo("提示", "请先在队列表中勾选复选框 ☑ 或高亮选择要移除的任务。")
            return

        remove_set = set(target_ids)
        target_tasks = [t for t in self.tasks if t.task_id in remove_set]

        for t in target_tasks:
            if t.status == "下载中":
                messagebox.showwarning("提示", f"任务 #{t.task_id} 正在下载中，请先暂停/停止后再移除！")
                return

        file_names = [f"#{t.task_id} - {os.path.basename(t.file_path)} ({t.status})" for t in target_tasks]

        dialog = DeleteConfirmDialog(self, len(target_tasks), file_names)
        self.wait_window(dialog)

        choice = dialog.result
        if not choice:
            return

        if choice == "delete_all":
            sec_confirm_msg = (
                f"【⚠️ 高风险物理删除确认】\n\n"
                f"您即将从硬盘彻底物理删除以下 {len(target_tasks)} 个任务的本地实体文件及未完成缓存：\n"
            )
            for t in target_tasks[:5]:
                sec_confirm_msg += f"• {os.path.basename(t.file_path)}\n"
            if len(target_tasks) > 5:
                sec_confirm_msg += f"...以及另外 {len(target_tasks) - 5} 个文件\n"
            
            sec_confirm_msg += "\n⚠️ 注意：此操作不可撤销，本地文件将被直接物理删除！\n\n确定要继续删除硬盘上的实体文档吗？"

            confirm_ok = messagebox.askyesno(
                "二次确认：物理删除本地实体文件",
                sec_confirm_msg,
                icon="warning",
                default="no"
            )
            if not confirm_ok:
                self.log("[!] 用户已取消物理文件删除操作。")
                return

            deleted_file_count = 0
            deleted_cache_count = 0

            for t in target_tasks:
                deleted_paths = t.clean_local_files_and_caches()
                for p in deleted_paths:
                    if p.endswith(".downloading") or p.endswith(".part") or p.endswith(".tmp"):
                        deleted_cache_count += 1
                        self.log(f"     [已清理未完成缓存]: {p}")
                    else:
                        deleted_file_count += 1
                        self.log(f"     [已物理删除本地实体文件]: {p}")

            self.tasks = [t for t in self.tasks if t.task_id not in remove_set]
            self.checked_tasks.difference_update(remove_set)
            self.rescan_all_tasks(silent=True)
            self.log(f"[-] 彻底删除完成: 已移除 {len(target_tasks)} 个任务，清理了 {deleted_file_count} 个实体文件及 {deleted_cache_count} 个临时缓存文件。")
            messagebox.showinfo("彻底删除完成", f"已成功从队列移除 {len(target_tasks)} 个任务，\n并彻底清理了 {deleted_file_count} 个本地文件与 {deleted_cache_count} 个未完成缓存文件！")

        elif choice == "queue_only":
            self.tasks = [t for t in self.tasks if t.task_id not in remove_set]
            self.checked_tasks.difference_update(remove_set)
            self.rescan_all_tasks(silent=True)
            self.log(f"[-] 已从队列中移除 {len(target_tasks)} 个任务 (已保留本地所有文件与缓存)。")

    def clear_completed_tasks(self):
        done_tasks = [t for t in self.tasks if t.status == "已完成"]
        if not done_tasks:
            messagebox.showinfo("提示", "当前队列中没有已完成的任务。")
            return

        done_ids = {t.task_id for t in done_tasks}
        self.tasks = [t for t in self.tasks if t.status != "已完成"]
        self.checked_tasks.difference_update(done_ids)
        self.rescan_all_tasks(silent=True)
        self.log(f"[✓] 已清理 {len(done_tasks)} 个已完成的任务记录 (本地文件已完整保留)。")

    def clear_all_tasks(self):
        if self.is_queue_running:
            messagebox.showwarning("提示", "下载队列正在运行中，请先停止队列！")
            return
        if not self.tasks:
            return

        choice = messagebox.askyesno("清空队列", "确定要清空队列中的所有任务记录吗？\n（仅清空队列记录，不删除本地已下载的文件）")
        if choice:
            self.tasks.clear()
            self.checked_tasks.clear()
            self.rescan_all_tasks(silent=True)
            self.log("[✓] 下载队列已清空。")

    def open_selected_task_folder(self):
        target_ids = self._get_target_task_ids()
        if not target_ids:
            messagebox.showinfo("提示", "请在队列中选择或勾选一个任务。")
            return
        target_id = target_ids[0]
        for t in self.tasks:
            if t.task_id == target_id:
                if os.path.exists(t.dest_dir):
                    os.startfile(t.dest_dir)
                else:
                    messagebox.showinfo("提示", f"目录尚未创建:\n{t.dest_dir}")
                return

    # ------------------ Context Menu Actions ------------------
    def action_resume_selected(self):
        target_ids = self._get_target_task_ids()
        if not target_ids:
            return
        target_set = set(target_ids)
        for t in self.tasks:
            if t.task_id in target_set and t.status in ("已中断", "已暂停", "失败", "等待中"):
                t.status = "等待中"
        self._refresh_queue_tree()
        self._save_tasks()
        if not self.is_queue_running:
            self.start_queue_download()

    def action_pause_selected(self):
        target_ids = self._get_target_task_ids()
        if not target_ids:
            return
        target_set = set(target_ids)
        for t in self.tasks:
            if t.task_id in target_set:
                if t.status == "下载中":
                    self.cancel_current_task = True
                t.status = "已暂停"
        self._refresh_queue_tree()
        self._save_tasks()

    def action_restart_selected(self):
        target_ids = self._get_target_task_ids()
        if not target_ids:
            return
        target_set = set(target_ids)
        for t in self.tasks:
            if t.task_id in target_set:
                t.clean_local_files_and_caches()
                t.status = "等待中"
                t.progress = 0.0
        self._refresh_queue_tree()
        self._save_tasks()
        if not self.is_queue_running:
            self.start_queue_download()

    # ------------------ Queue Execution Loop ------------------
    def start_queue_download(self):
        if self.is_queue_running:
            return

        has_selection = bool(self.checked_tasks)
        if has_selection:
            # Check if selected tasks have non-completed tasks
            pending_tasks = [t for t in self.tasks if t.task_id in self.checked_tasks and t.status in ("等待中", "已中断", "已暂停", "失败")]
            if not pending_tasks:
                # If all selected are completed or something else, prompt or activate them
                sel_tasks = [t for t in self.tasks if t.task_id in self.checked_tasks]
                if sel_tasks and all(t.status == "已完成" for t in sel_tasks):
                    choice = messagebox.askyesno("重新下载", "所勾选的任务均已完成，是否重新下载勾选的任务？")
                    if choice:
                        for t in sel_tasks:
                            t.clean_local_files_and_caches()
                            t.status = "等待中"
                            t.progress = 0.0
                        self._refresh_queue_tree()
                        self._save_tasks()
                        pending_tasks = sel_tasks
                    else:
                        return
                else:
                    messagebox.showinfo("提示", "所勾选的任务中没有需要下载的任务。")
                    return
        else:
            pending_tasks = [t for t in self.tasks if t.status in ("等待中", "已中断", "已暂停", "失败")]
            if not pending_tasks:
                messagebox.showinfo("提示", "当前队列中没有需要下载的任务（全部已完成或队列为空）。")
                return

        self.is_queue_running = True
        self.stop_queue_requested = False
        self.btn_start_queue.config(state=tk.DISABLED)
        self.btn_stop_queue.config(state=tk.NORMAL)
        
        mode_desc = f"勾选的 {len(pending_tasks)} 个任务" if has_selection else f"全队列 ({len(pending_tasks)} 个任务)"
        self.lbl_status.config(text=f"状态: 正在下载 [{mode_desc}]...", foreground="blue")
        self.log(f"\n[*] 启动下载队列: 目标为 {mode_desc}...")

        threading.Thread(target=self._queue_worker, daemon=True).start()

    def stop_queue_download(self):
        if not self.is_queue_running:
            # If not running but has selected tasks, mark selected waiting tasks as paused
            if self.checked_tasks:
                for t in self.tasks:
                    if t.task_id in self.checked_tasks and t.status in ("等待中", "下载中"):
                        t.status = "已暂停"
                self._refresh_queue_tree()
                self._save_tasks()
                self.log(f"[!] 已将勾选的 {len(self.checked_tasks)} 个任务标记为已暂停。")
            return

        has_selection = bool(self.checked_tasks)
        if has_selection:
            for t in self.tasks:
                if t.task_id in self.checked_tasks:
                    if t.status == "下载中":
                        self.cancel_current_task = True
                    t.status = "已暂停"
            self._refresh_queue_tree()
            self._save_tasks()
            # If the current active task was in selection or user requested stop, pause
            if not self.active_task_id or self.active_task_id in self.checked_tasks:
                self.stop_queue_requested = True
                self._reset_progress_ui("已暂停勾选的任务")
                self.log(f"[!] 收到指令，已暂停勾选的任务。")
        else:
            self.stop_queue_requested = True
            self.cancel_current_task = True
            self._reset_progress_ui("正在终止/暂停队列...")
            self.log("[!] 收到终止指令，已中断当前任务并保存进度，随时可恢复。")

    def _queue_worker(self):
        self.log(f"\n================ 启动断点续传队列 ================")
        self._update_lock_file(True)

        while self.is_queue_running and not self.stop_queue_requested:
            current_task = None
            has_selection = bool(self.checked_tasks)

            for t in self.tasks:
                if has_selection:
                    # Only process tasks in checked_tasks
                    if t.task_id in self.checked_tasks and t.status in ("等待中", "已中断", "已暂停", "失败"):
                        current_task = t
                        break
                else:
                    # Process any pending task in queue
                    if t.status in ("等待中", "已中断", "已暂停", "失败"):
                        current_task = t
                        break

            if not current_task:
                break

            self.active_task_id = current_task.task_id
            current_task.status = "下载中"
            self.cancel_current_task = False
            self.after(0, self._refresh_queue_tree)
            self._save_tasks()
            self._update_lock_file(True)

            target_file_path = current_task.get_dest_file_path()
            os.makedirs(os.path.dirname(target_file_path), exist_ok=True)

            if current_task.direct_url:
                download_url = current_task.direct_url
            elif current_task.repo_type == "model":
                download_url = f"{current_task.endpoint}/{current_task.repo_id}/resolve/{current_task.branch}/{current_task.file_path}"
            elif current_task.repo_type == "dataset":
                download_url = f"{current_task.endpoint}/datasets/{current_task.repo_id}/resolve/{current_task.branch}/{current_task.file_path}"
            else:
                download_url = f"{current_task.endpoint}/spaces/{current_task.repo_id}/resolve/{current_task.branch}/{current_task.file_path}"

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HF-Downloader/1.0"}
            if current_task.token:
                headers["Authorization"] = f"Bearer {current_task.token}" if current_task.platform != "github" else f"token {current_task.token}"

            proxy_str = current_task.proxy or self._get_effective_proxy()
            proxies = {"http": proxy_str, "https": proxy_str} if proxy_str else None

            self.log(f"\n[任务 #{current_task.task_id}] 开始/恢复下载: {current_task.file_path}")
            self.log(f"     更新日期: {current_task.date_str} | 大小: {current_task.size_str}")
            self.log(f"     网络代理: {proxy_str or '直连'}")
            self.log(f"     目标路径: {target_file_path}")
            self.after(0, lambda t=current_task: self.lbl_status.config(
                text=f"正在下载 [#{t.task_id}]: {os.path.basename(t.file_path)}", foreground="blue"
            ))

            success = self._stream_download(download_url, target_file_path, headers, proxies, current_task)

            if self.stop_queue_requested or self.cancel_current_task:
                current_task.status = "已中断"
                self.log(f"[!] 任务 #{current_task.task_id} 已平稳终止（断点进度已保留）。")
            elif success:
                current_task.status = "已完成"
                current_task.progress = 100.0
                self.log(f"[✓] 任务 #{current_task.task_id} 下载完成！")
            else:
                current_task.status = "已中断" if "取消" in current_task.error_msg else "失败"
                self.log(f"[✗] 任务 #{current_task.task_id} 中断/失败: {current_task.error_msg}")

            self.active_task_id = None
            self.after(0, self._refresh_queue_tree)
            self._save_tasks()

        self._update_lock_file(False)
        self.after(0, self._on_queue_finished)

    def _stream_download(self, url: str, local_path: str, headers: dict, proxies: Optional[dict], task: QueueTask) -> bool:
        temp_path = local_path + ".downloading"
        chunk_size = 1024 * 1024  # 1MB chunk

        req_headers = headers.copy()
        downloaded_bytes = 0

        if os.path.exists(temp_path):
            downloaded_bytes = os.path.getsize(temp_path)
            if downloaded_bytes > 0:
                req_headers["Range"] = f"bytes={downloaded_bytes}-"
                self.log(f"     [断点续传] 检测到已有缓存 {self._format_size(downloaded_bytes)}，从断点处继续...")

        try:
            with requests.get(url, headers=req_headers, proxies=proxies, stream=True, timeout=30, allow_redirects=True) as resp:
                if resp.status_code == 416:
                    total_size = downloaded_bytes
                elif resp.status_code not in (200, 206):
                    task.error_msg = f"HTTP {resp.status_code}"
                    return False
                else:
                    content_length = resp.headers.get("content-length")
                    if content_length:
                        total_size = int(content_length) + (downloaded_bytes if resp.status_code == 206 else 0)
                        task.total_bytes = total_size
                    else:
                        total_size = task.total_bytes

                mode = "ab" if (resp.status_code == 206 and downloaded_bytes > 0) else "wb"
                if mode == "wb":
                    downloaded_bytes = 0

                start_time = time.time()
                last_update_time = start_time
                bytes_since_last = 0

                with open(temp_path, mode) as f:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if self.cancel_current_task or self.stop_queue_requested:
                            task.error_msg = "用户取消"
                            return False
                        if chunk:
                            f.write(chunk)
                            downloaded_bytes += len(chunk)
                            bytes_since_last += len(chunk)

                            now = time.time()
                            if now - last_update_time >= 0.3:
                                dt = now - last_update_time
                                speed_bps = bytes_since_last / dt
                                speed_str = self._format_size(int(speed_bps)) + "/s"
                                
                                if total_size and total_size > 0:
                                    pct = min(100.0, (downloaded_bytes / total_size) * 100.0)
                                    rem_bytes = max(0, total_size - downloaded_bytes)
                                    eta_sec = int(rem_bytes / speed_bps) if speed_bps > 0 else 0
                                    eta_str = f"{eta_sec // 60}分{eta_sec % 60}秒" if eta_sec > 60 else f"{eta_sec}秒"
                                    
                                    task.progress = pct
                                    self.after(0, lambda p=pct, d=downloaded_bytes, t=total_size, s=speed_str, e=eta_str: 
                                        self._update_progress_ui(p, d, t, s, e)
                                    )
                                else:
                                    self.after(0, lambda d=downloaded_bytes, s=speed_str: 
                                        self._update_progress_indeterminate(d, s)
                                    )

                                last_update_time = now
                                bytes_since_last = 0

            if os.path.exists(local_path):
                os.remove(local_path)
            os.rename(temp_path, local_path)
            return True

        except Exception as e:
            task.error_msg = str(e)
            return False

    def _update_progress_ui(self, pct: float, cur_bytes: int, total_bytes: int, speed: str, eta: str):
        self.progress_var.set(pct)
        cur_str = self._format_size(cur_bytes)
        tot_str = self._format_size(total_bytes)
        self.lbl_progress_text.config(text=f"进度: {pct:.1f}% ({cur_str} / {tot_str})")
        self.lbl_speed_text.config(text=f"速度: {speed} | 预估剩余: {eta}")

    def _update_progress_indeterminate(self, cur_bytes: int, speed: str):
        cur_str = self._format_size(cur_bytes)
        self.lbl_progress_text.config(text=f"已下载: {cur_str}")
        self.lbl_speed_text.config(text=f"速度: {speed}")

    def _reset_progress_ui(self, status_text: str = None):
        self.progress_var.set(0.0)
        self.lbl_progress_text.config(text="进度: 0.0% (0 B / 0 B)")
        self.lbl_speed_text.config(text="速度: 0 KB/s | 预估剩余: --:--:--")
        if status_text:
            self.lbl_status.config(text=f"状态: {status_text}", foreground="#555555")

    def _on_queue_finished(self):
        self.is_queue_running = False
        self.stop_queue_requested = False
        self.cancel_current_task = False
        self.btn_start_queue.config(state=tk.NORMAL)
        self.btn_stop_queue.config(state=tk.DISABLED)

        self._reset_progress_ui()
        self.rescan_all_tasks(silent=True)
        done_count = sum(1 for t in self.tasks if t.status == "已完成")
        total_count = len(self.tasks)

        self.lbl_status.config(text=f"状态: 队列结束 (完成 {done_count}/{total_count})", foreground="green" if done_count == total_count else "orange")
        self.log(f"================ 队列任务结束 ({done_count}/{total_count} 完成) ================\n")

        if total_count > 0 and done_count == total_count:
            messagebox.showinfo("队列完成", f"队列中的所有 {total_count} 个任务已全部下载完成！")

if __name__ == "__main__":
    app = HFDownloaderApp()
    app.mainloop()
