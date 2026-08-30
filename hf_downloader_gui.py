import os
import sys
import time
import json
import datetime
from datetime import datetime
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
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
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
HISTORY_DB_FILE = os.path.join(CONFIG_DIR, "hf_downloader_history.json")

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
    ("certifi", "Mozilla CA 根证书集 (保障 SSL/TLS 下载安全)"),
    ("yt_dlp", "Twitter / X / 社交媒体流媒体高清音视频解析引擎")
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
    "https://ghfast.top/",
    "https://ghproxy.net/",
    "https://mirror.ghproxy.com/",
    "https://github.moeyy.xyz/",
    "不使用加速 (官方直连)"
]

# Preset Directory Mappings: Display Label -> Absolute Path
DEFAULT_COMFYUI_ROOT = r"F:\ComfyUI-aki-v3\ComfyUI\models"
DEFAULT_CUSTOM_NODES_DIR = os.path.normpath(os.path.join(DEFAULT_COMFYUI_ROOT, "..", "custom_nodes"))
PRESETS_CONFIG_FILE = os.path.join(CONFIG_DIR, "hf_downloader_presets.json")

class PresetDirectoryManager:
    """Centralized manager for preset target directories with persistent JSON storage."""

    @staticmethod
    def get_default_presets(comfy_root: Optional[str] = None) -> Dict[str, str]:
        root = comfy_root or DEFAULT_COMFYUI_ROOT
        custom_nodes = os.path.normpath(os.path.join(root, "..", "custom_nodes"))
        return {
            "🧩 ComfyUI 插件目录 (custom_nodes)": custom_nodes,
            "🎨 扩散模型 (diffusion_models)": os.path.join(root, "diffusion_models"),
            "🎮 控制网络 (controlnet)": os.path.join(root, "controlnet"),
            "💾 大模型底模 (checkpoints)": os.path.join(root, "checkpoints"),
            "⚡ 微调模型 (loras)": os.path.join(root, "loras"),
            "🔍 变分自编码 (vae)": os.path.join(root, "vae"),
            "🧠 UNet 主干 (unet)": os.path.join(root, "unet"),
            "🔤 文本编码器 (clip)": os.path.join(root, "clip"),
            "📥 默认下载输出目录 (downloads)": os.path.join(os.path.expanduser("~"), "Downloads", "HF_Downloads"),
        }

    @classmethod
    def load_presets(cls) -> Dict[str, str]:
        global PRESET_DIRS_MAP
        if os.path.exists(PRESETS_CONFIG_FILE):
            try:
                with open(PRESETS_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data:
                        PRESET_DIRS_MAP = data
                        return data
            except Exception:
                pass
        defaults = cls.get_default_presets()
        PRESET_DIRS_MAP = defaults
        cls.save_presets(defaults)
        return defaults

    @classmethod
    def save_presets(cls, presets: Dict[str, str]):
        global PRESET_DIRS_MAP
        PRESET_DIRS_MAP = presets
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(PRESETS_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(presets, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def update_root_base(cls, new_comfy_root: str) -> Dict[str, str]:
        current = cls.load_presets()
        custom_nodes = os.path.normpath(os.path.join(new_comfy_root, "..", "custom_nodes"))
        updated = {}
        for label, path in current.items():
            if "custom_nodes" in label:
                updated[label] = custom_nodes
            elif any(k in label for k in ["diffusion_models", "controlnet", "checkpoints", "loras", "vae", "unet", "clip"]):
                folder = label.split("(")[-1].rstrip(")")
                updated[label] = os.path.join(new_comfy_root, folder)
            else:
                updated[label] = path
        cls.save_presets(updated)
        return updated

PRESET_DIRS_MAP = PresetDirectoryManager.load_presets()

def center_window_on_parent(win: tk.Toplevel, parent: Optional[tk.Widget] = None, width: Optional[int] = None, height: Optional[int] = None):
    """Accurately center a child or dialog window relative to its parent window, keeping it strictly on-screen."""
    try:
        win.update_idletasks()
        if parent:
            parent.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
        else:
            pw = win.winfo_screenwidth()
            ph = win.winfo_screenheight()
            px = 0
            py = 0

        w = width or win.winfo_reqwidth() or win.winfo_width()
        h = height or win.winfo_reqheight() or win.winfo_height()

        if w <= 1: w = 560
        if h <= 1: h = 380

        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)

        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = max(10, min(x, sw - w - 20))
        y = max(10, min(y, sh - h - 40))

        win.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass


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

        # 14. Clock / History (Indigo Watch Face with Hands)
        img_clock = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_clock)
        d.ellipse([1, 1, 16, 16], fill="#e0e7ff", outline="#6366f1", width=2)
        d.line([9, 4, 9, 9], fill="#4338ca", width=2)
        d.line([9, 9, 13, 9], fill="#4338ca", width=2)
        icons_pil["clock"] = img_clock

        # 15. Star / Bookmark (Golden Five-Pointed Star)
        img_star = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_star)
        d.polygon([(9, 1), (11, 6), (17, 7), (12, 11), (14, 17), (9, 13), (4, 17), (6, 11), (1, 7), (7, 6)], fill="#f59e0b", outline="#d97706")
        icons_pil["star"] = img_star

        # 14. Twitter / X Bird Icon (Sky Blue Emblem with X/Bird styling)
        img_tw = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(img_tw)
        d.ellipse([1, 1, 16, 16], fill="#1d9bf0")
        d.line([5, 5, 13, 13], fill="#ffffff", width=2)
        d.line([13, 5, 5, 13], fill="#ffffff", width=2)
        icons_pil["twitter"] = img_tw

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

        center_window_on_parent(self, parent, 720, 560)

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
                    self.after(0, lambda: messagebox.showinfo("部署成功", "所有核心依赖组件（含 huggingface_hub, hf_transfer, requests 等）已全部成功安装部署！", parent=self))
                    if self.on_complete_callback:
                        self.after(0, self.on_complete_callback)
                else:
                    self.after(0, lambda: self._log(f"\n[✗] 安装过程返回异常代码: {proc.returncode}，请检查网络或切换镜像源后重试。"))
                    self.after(0, lambda: messagebox.showerror("安装遇到问题", f"依赖安装未完全成功 (Code {proc.returncode}, parent=self)，请尝试切换上方不同的 PyPI 镜像源后重试。"))
            except Exception as e:
                self.after(0, lambda: self._log(f"\n[✗] 执行安装失败: {str(e)}"))
                self.after(0, lambda: messagebox.showerror("错误", f"启动安装进程失败: {str(e, parent=self)}"))

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

        center_window_on_parent(self, parent, 560, 420)

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
            messagebox.showwarning("提示", "请输入镜像源 URL 地址！", parent=self)
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url

        if url in self.mirrors:
            messagebox.showinfo("提示", "该镜像源已在列表中。", parent=self)
            return

        self.mirrors.append(url)
        self._refresh_listbox()
        self.new_mirror_var.set("")
        self.on_update_callback(self.mirrors, selected=url)

    def delete_selected_mirror(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("提示", "请在上方列表中先选择要删除的镜像源。", parent=self)
            return
        idx = sel[0]
        url = self.mirrors[idx]

        if messagebox.askyesno("确认删除", f"确定要永久删除以下镜像源吗？\n{url}", parent=self):
            self.mirrors.pop(idx)
            self._refresh_listbox()
            self.on_update_callback(self.mirrors)

    def reset_default_mirrors(self):
        if messagebox.askyesno("恢复默认", "确定要恢复为官方默认镜像源列表吗？", parent=self):
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

        center_window_on_parent(self, parent, 560, 430)

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
            messagebox.showwarning("提示", "请输入代理地址！", parent=self)
            return

        if "直连" not in raw and not (raw.startswith("http://") or raw.startswith("https://") or raw.startswith("socks5://") or raw.startswith("socks5h://")):
            raw = "http://" + raw

        if raw in self.proxies:
            messagebox.showinfo("提示", "该代理地址已在列表中。", parent=self)
            return

        self.proxies.append(raw)
        self._refresh_listbox()
        self.new_proxy_var.set("")
        self.on_update_callback(self.proxies, selected=raw)

    def delete_selected_proxy(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("提示", "请在上方列表中先选择要删除的代理。", parent=self)
            return
        idx = sel[0]
        val = self.proxies[idx]

        if "不使用代理" in val or "直连" in val:
            messagebox.showwarning("提示", "【不使用代理 (直连)】为核心基础项，不可删除。", parent=self)
            return

        if messagebox.askyesno("确认删除", f"确定要永久删除以下代理地址吗？\n{val}", parent=self):
            self.proxies.pop(idx)
            self._refresh_listbox()
            self.on_update_callback(self.proxies)

    def reset_default_proxies(self):
        if messagebox.askyesno("恢复默认", "确定要恢复为默认常用代理列表吗？", parent=self):
            self.proxies = list(DEFAULT_PROXIES)
            self._refresh_listbox()
            self.on_update_callback(self.proxies)


# ------------------ Preset Directories Visual Manager Dialog ------------------
class PresetDirectoryManagerDialog(tk.Toplevel):
    """Visual Dialog for managing, adding, editing, deleting and creating preset target directories."""

    def __init__(self, parent, on_update_callback):
        super().__init__(parent)
        self.title("⚙️ 预设分类目录实时管理器 (Preset Directory Manager)")
        self.geometry("920x580")
        self.minsize(780, 460)
        self.transient(parent)
        self.grab_set()

        self.on_update_callback = on_update_callback
        self.presets: Dict[str, str] = dict(PresetDirectoryManager.load_presets())

        center_window_on_parent(self, parent, 920, 580)
        self._build_ui()
        self._refresh_table()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Top description & Quick Action bar
        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(
            top_bar, 
            text="💡 在此可自由新增、修改、重命名、删除预设分类目录，修改后全软件所有 Tab 实时生效并持久保存。", 
            font=FONT_SMALL, 
            foreground="#555555"
        ).pack(side=tk.LEFT)

        self.lbl_stats = ttk.Label(top_bar, text="共 0 个预设", font=FONT_BOLD, foreground="#0d6efd")
        self.lbl_stats.pack(side=tk.RIGHT)

        # 2. Main Preset Table
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        cols = ("status", "label", "path")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("status", text="状态", anchor=tk.CENTER)
        self.tree.heading("label", text="预设分类名称 / 标识 (支持Emoji与说明)", anchor=tk.W)
        self.tree.heading("path", text="保存目标绝对路径 (本地文件夹)", anchor=tk.W)

        self.tree.column("status", width=95, minwidth=80, stretch=False, anchor=tk.CENTER)
        self.tree.column("label", width=310, minwidth=180, stretch=False, anchor=tk.W)
        self.tree.column("path", width=460, minwidth=220, stretch=True, anchor=tk.W)

        self.tree.tag_configure("ok_tag", foreground="#198754", font=FONT_TABLE_BOLD)
        self.tree.tag_configure("missing_tag", foreground="#dc3545", font=FONT_TABLE)

        scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        scroll_y.grid(row=0, column=1, sticky=tk.NS)
        scroll_x.grid(row=1, column=0, sticky=tk.EW)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        # 3. Edit / Add Form Panel
        form_frame = ttk.LabelFrame(main_frame, text=" 📝 预设分类编辑与新增表单 ", padding="8")
        form_frame.pack(fill=tk.X, pady=(0, 8))

        # Row 0: Label
        ttk.Label(form_frame, text="分类名称:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        self.edit_label_var = tk.StringVar()
        self.entry_label = ttk.Entry(form_frame, textvariable=self.edit_label_var, font=FONT_NORMAL)
        self.entry_label.grid(row=0, column=1, sticky=tk.EW, padx=4, pady=3)

        # Row 1: Path & Browse
        ttk.Label(form_frame, text="目标路径:", font=FONT_BOLD).grid(row=1, column=0, sticky=tk.W, padx=4, pady=3)
        path_box = ttk.Frame(form_frame)
        path_box.grid(row=1, column=1, sticky=tk.EW, padx=4, pady=3)

        self.edit_path_var = tk.StringVar()
        self.entry_path = ttk.Entry(path_box, textvariable=self.edit_path_var, font=FONT_NORMAL)
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_browse = ttk.Button(path_box, text=" 浏览文件夹...", command=self._browse_path)
        btn_browse.pack(side=tk.RIGHT, padx=(4, 0))

        form_frame.columnconfigure(1, weight=1)

        # Buttons inside Form
        form_btn_bar = ttk.Frame(form_frame)
        form_btn_bar.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(4, 0))

        btn_save_item = tk.Button(
            form_btn_bar,
            text="💾 保存/更新当前预设",
            font=FONT_BOLD,
            bg="#0d6efd",
            fg="#ffffff",
            activebackground="#0b5ed7",
            activeforeground="#ffffff",
            padx=10, pady=3,
            command=self.save_current_preset
        )
        btn_save_item.pack(side=tk.LEFT, padx=4)

        btn_add_new = ttk.Button(form_btn_bar, text="➕ 另存为新分类", command=self.add_as_new_preset)
        btn_add_new.pack(side=tk.LEFT, padx=4)

        btn_create_dir = ttk.Button(form_btn_bar, text="📁 创建当前物理文件夹", command=self.create_current_dir)
        btn_create_dir.pack(side=tk.LEFT, padx=4)

        btn_open_dir = ttk.Button(form_btn_bar, text="📂 在资源管理器中打开", command=self.open_current_dir)
        btn_open_dir.pack(side=tk.LEFT, padx=4)

        btn_clear_form = ttk.Button(form_btn_bar, text="🧹 清空输入框", command=self._clear_form)
        btn_clear_form.pack(side=tk.RIGHT, padx=4)

        # 4. Bottom Actions Toolbar
        bottom_bar = ttk.Frame(main_frame)
        bottom_bar.pack(fill=tk.X)

        btn_del = ttk.Button(bottom_bar, text="🗑️ 删除选中项", command=self.delete_selected_preset)
        btn_del.pack(side=tk.LEFT, padx=2)

        btn_move_up = ttk.Button(bottom_bar, text="⬆️ 上移", width=6, command=lambda: self._move_item(-1))
        btn_move_up.pack(side=tk.LEFT, padx=2)

        btn_move_down = ttk.Button(bottom_bar, text="⬇️ 下移", width=6, command=lambda: self._move_item(1))
        btn_move_down.pack(side=tk.LEFT, padx=2)

        btn_create_all = ttk.Button(bottom_bar, text="📁 一键创建全部缺失目录", command=self.create_all_missing_dirs)
        btn_create_all.pack(side=tk.LEFT, padx=6)

        btn_reset_defaults = ttk.Button(bottom_bar, text="↺ 恢复官方默认预设", command=self.reset_to_defaults)
        btn_reset_defaults.pack(side=tk.LEFT, padx=4)

        btn_close = ttk.Button(bottom_bar, text="完成并关闭", command=self.destroy)
        btn_close.pack(side=tk.RIGHT, padx=2)

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for i, (label, path) in enumerate(self.presets.items()):
            exists = os.path.exists(path)
            status_str = "✅ 已就绪" if exists else "❌ 未创建"
            tag = "ok_tag" if exists else "missing_tag"
            self.tree.insert("", tk.END, iid=str(i), values=(status_str, label, path), tags=(tag,))
        self.lbl_stats.config(text=f"共 {len(self.presets)} 个预设目录")

    def _on_tree_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        labels = list(self.presets.keys())
        if 0 <= idx < len(labels):
            lbl = labels[idx]
            self.edit_label_var.set(lbl)
            self.edit_path_var.set(self.presets[lbl])

    def _on_tree_double_click(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        labels = list(self.presets.keys())
        if 0 <= idx < len(labels):
            lbl = labels[idx]
            p = self.presets[lbl]
            if os.path.exists(p):
                os.startfile(p)
            else:
                if messagebox.askyesno("创建目录", f"目录不存在，是否立即创建？\n{p}", parent=self):
                    try:
                        os.makedirs(p, exist_ok=True)
                        self._refresh_table()
                        messagebox.showinfo("成功", f"目录已成功创建:\n{p}", parent=self)
                    except Exception as e:
                        messagebox.showerror("错误", f"创建失败: {str(e)}", parent=self)

    def _browse_path(self):
        init_dir = self.edit_path_var.get().strip()
        if not os.path.exists(init_dir):
            init_dir = os.path.expanduser("~")
        d = filedialog.askdirectory(title="选择预设分类保存目录", initialdir=init_dir)
        if d:
            self.edit_path_var.set(os.path.normpath(d))

    def _clear_form(self):
        self.edit_label_var.set("")
        self.edit_path_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def save_current_preset(self):
        label = self.edit_label_var.get().strip()
        path = self.edit_path_var.get().strip()
        if not label or not path:
            messagebox.showwarning("提示", "分类名称和目标路径均不能为空！", parent=self)
            return

        path = os.path.normpath(path)
        sel = self.tree.selection()
        
        if sel:
            idx = int(sel[0])
            labels = list(self.presets.keys())
            old_label = labels[idx]
            # Replace at same position
            new_dict = {}
            for k, v in self.presets.items():
                if k == old_label:
                    new_dict[label] = path
                else:
                    new_dict[k] = v
            self.presets = new_dict
        else:
            self.presets[label] = path

        PresetDirectoryManager.save_presets(self.presets)
        self._refresh_table()
        self.on_update_callback(self.presets, selected_label=label)
        messagebox.showinfo("成功", f"预设分类【{label}】已成功保存！", parent=self)

    def add_as_new_preset(self):
        label = self.edit_label_var.get().strip()
        path = self.edit_path_var.get().strip()
        if not label or not path:
            messagebox.showwarning("提示", "分类名称和目标路径均不能为空！", parent=self)
            return

        path = os.path.normpath(path)
        if label in self.presets:
            if not messagebox.askyesno("重名覆盖", f"已存在名为【{label}】的预设，是否覆盖其路径？", parent=self):
                return

        self.presets[label] = path
        PresetDirectoryManager.save_presets(self.presets)
        self._refresh_table()
        self.on_update_callback(self.presets, selected_label=label)
        messagebox.showinfo("成功", f"新预设分类【{label}】已添加成功！", parent=self)

    def delete_selected_preset(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先在上方列表中选择要删除的预设分类！", parent=self)
            return
        idx = int(sel[0])
        labels = list(self.presets.keys())
        lbl = labels[idx]

        if len(self.presets) <= 1:
            messagebox.showwarning("提示", "至少需保留一个预设分类，不可全部删除！", parent=self)
            return

        if messagebox.askyesno("确认删除", f"确定要删除预设分类【{lbl}】吗？\n（注：仅删除预设配置，不会删除硬盘上的实际文件夹）", parent=self):
            del self.presets[lbl]
            PresetDirectoryManager.save_presets(self.presets)
            self._refresh_table()
            self._clear_form()
            self.on_update_callback(self.presets)

    def create_current_dir(self):
        path = self.edit_path_var.get().strip()
        if not path:
            messagebox.showwarning("提示", "请先选择或输入目标路径！", parent=self)
            return
        try:
            os.makedirs(path, exist_ok=True)
            self._refresh_table()
            messagebox.showinfo("成功", f"物理文件夹已成功创建:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("错误", f"创建目录失败: {str(e)}", parent=self)

    def open_current_dir(self):
        path = self.edit_path_var.get().strip()
        if not path:
            messagebox.showwarning("提示", "请先选择或输入目标路径！", parent=self)
            return
        if os.path.exists(path):
            os.startfile(path)
        else:
            if messagebox.askyesno("目录不存在", f"目录尚不存在，是否立即创建并打开？\n{path}", parent=self):
                try:
                    os.makedirs(path, exist_ok=True)
                    self._refresh_table()
                    os.startfile(path)
                except Exception as e:
                    messagebox.showerror("错误", f"创建失败: {str(e)}", parent=self)

    def create_all_missing_dirs(self):
        created = 0
        for lbl, p in self.presets.items():
            if not os.path.exists(p):
                try:
                    os.makedirs(p, exist_ok=True)
                    created += 1
                except Exception:
                    pass
        self._refresh_table()
        messagebox.showinfo("完成", f"批量创建完成！共创建/补齐 {created} 个物理文件夹。", parent=self)

    def reset_to_defaults(self):
        if messagebox.askyesno("恢复默认", "确定要恢复为 ComfyUI 官方标准默认预设目录列表吗？\n（自定义的预设将被重置）", parent=self):
            self.presets = PresetDirectoryManager.get_default_presets()
            PresetDirectoryManager.save_presets(self.presets)
            self._refresh_table()
            self._clear_form()
            self.on_update_callback(self.presets)
            messagebox.showinfo("完成", "已恢复为官方标准预设目录列表！", parent=self)

    def _move_item(self, direction: int):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        labels = list(self.presets.keys())
        new_idx = idx + direction
        if 0 <= new_idx < len(labels):
            labels[idx], labels[new_idx] = labels[new_idx], labels[idx]
            reordered = {k: self.presets[k] for k in labels}
            self.presets = reordered
            PresetDirectoryManager.save_presets(self.presets)
            self._refresh_table()
            self.tree.selection_set(str(new_idx))
            self.on_update_callback(self.presets)

    def destroy(self):
        try:
            self.on_update_callback(self.presets)
        except Exception:
            pass
        super().destroy()


# ------------------ Twitter Video & Thumbnail Visual Preview Dialog ------------------
# ------------------ Universal Built-in Video Player Engine ------------------
import shutil
import subprocess
import tempfile
import hashlib

class BuiltinTkinterPlayerDialog(tk.Toplevel):
    """Pure Python embedded video player window using OpenCV & Tkinter Canvas with smart live buffering."""

    def __init__(self, parent, video_source: str, title_text: str = "内置视频播放器", http_headers: Optional[Dict[str, str]] = None, proxy: Optional[str] = None):
        super().__init__(parent)
        self.video_source = video_source
        self.title_text = title_text
        self.http_headers = http_headers or {}
        self.proxy = proxy
        
        self.title(f"🎬 内置视频播放器 - {title_text}")
        self.geometry("840x620")
        self.minsize(640, 480)
        self.configure(bg="#0f172a")
        self.transient(parent)

        self.cap = None
        self.is_playing = False
        self.total_frames = 0
        self.fps = 30.0
        self.current_frame_idx = 0
        self.is_slider_dragging = False
        self.temp_buffer_file = None
        self.is_buffering_active = False

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<space>", lambda e: self.toggle_play())
        self.bind("<Left>", lambda e: self.seek_relative(-5))
        self.bind("<Right>", lambda e: self.seek_relative(5))
        self.bind("<Escape>", lambda e: self._on_close())

        self.after(50, self._init_and_play)

    def _build_ui(self):
        # 1. Canvas for Video Frame Rendering
        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", lambda e: self.toggle_play())
        self.canvas.bind("<Double-1>", lambda e: self._toggle_fullscreen())

        # Loading text overlay
        self.canvas.create_text(
            420, 260,
            text="⏳ 正在初始化视频流，准备播放...",
            fill="#38bdf8",
            font=FONT_BOLD,
            tags=("loading_text",)
        )

        # 2. Bottom Controls Bar
        ctrl_frame = tk.Frame(self, bg="#1e293b", padx=10, pady=6)
        ctrl_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Progress Slider
        slider_frame = tk.Frame(ctrl_frame, bg="#1e293b")
        slider_frame.pack(fill=tk.X, pady=(0, 4))

        self.progress_var = tk.DoubleVar(value=0.0)
        self.slider = tk.Scale(
            slider_frame,
            variable=self.progress_var,
            from_=0.0,
            to=100.0,
            orient=tk.HORIZONTAL,
            showvalue=0,
            bg="#334155",
            fg="#38bdf8",
            activebackground="#0284c7",
            troughcolor="#0f172a",
            highlightthickness=0,
            bd=0,
            command=self._on_slider_move
        )
        self.slider.pack(fill=tk.X, expand=True)
        self.slider.bind("<ButtonPress-1>", self._on_slider_press)
        self.slider.bind("<ButtonRelease-1>", self._on_slider_release)

        # Buttons & Time info row
        btn_row = tk.Frame(ctrl_frame, bg="#1e293b")
        btn_row.pack(fill=tk.X)

        self.btn_play_pause = tk.Button(
            btn_row,
            text="⏸️ 暂停",
            font=FONT_BOLD,
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            bd=0,
            padx=10,
            pady=3,
            command=self.toggle_play
        )
        self.btn_play_pause.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_restart = tk.Button(
            btn_row,
            text="🔄 重播",
            font=FONT_NORMAL,
            bg="#475569",
            fg="#ffffff",
            activebackground="#334155",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=3,
            command=self.restart_video
        )
        self.btn_restart.pack(side=tk.LEFT, padx=4)

        self.lbl_time = tk.Label(
            btn_row,
            text="00:00 / 00:00",
            font=FONT_SMALL,
            bg="#1e293b",
            fg="#94a3b8"
        )
        self.lbl_time.pack(side=tk.LEFT, padx=10)

        # Shortcut hint
        lbl_hint = tk.Label(
            btn_row,
            text="快捷键: [空格] 暂停/播放 | [←/→] 快退/快进5秒 | [Esc] 退出",
            font=FONT_SMALL,
            bg="#1e293b",
            fg="#64748b"
        )
        lbl_hint.pack(side=tk.RIGHT)

    def _init_and_play(self):
        # Case 1: Direct Local File Playback
        if os.path.exists(self.video_source):
            self._open_opencv_capture(self.video_source)
            return

        # Case 2: Network Stream with Live Pre-Buffering (Bypasses 403 Anti-Leech & Proxy Issues)
        self._update_loading_status("⏳ 正在通过防盗链/代理高速缓冲视频流数据...")
        raw_hash = hashlib.md5(self.video_source.encode("utf-8", errors="ignore")).hexdigest()[:10]
        self.temp_buffer_file = os.path.join(tempfile.gettempdir(), f"hf_preview_{raw_hash}.mp4")
        self.is_buffering_active = True

        def _buffer_worker():
            try:
                proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
                headers = dict(self.http_headers) if self.http_headers else {}
                if "User-Agent" not in headers:
                    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                
                resp = requests.get(self.video_source, headers=headers, proxies=proxies, stream=True, timeout=15)
                if resp.status_code not in (200, 206):
                    self.after(0, lambda code=resp.status_code: self._handle_stream_error(f"服务器返回 HTTP {code}，无法读取视频流。"))
                    return

                bytes_written = 0
                has_started_cap = False
                with open(self.temp_buffer_file, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if not self.is_buffering_active:
                            break
                        if chunk:
                            f.write(chunk)
                            bytes_written += len(chunk)
                            
                            # As soon as 1.2MB is buffered, launch OpenCV playback immediately!
                            if not has_started_cap and bytes_written >= 1024 * 1024 * 1.2:
                                has_started_cap = True
                                self.after(0, lambda: self._open_opencv_capture(self.temp_buffer_file))
                
                if not has_started_cap and bytes_written > 0:
                    self.after(0, lambda: self._open_opencv_capture(self.temp_buffer_file))
            except Exception as e:
                if not self.is_playing:
                    self.after(0, lambda err=str(e): self._handle_stream_error(f"网络流缓冲失败: {err}"))

        threading.Thread(target=_buffer_worker, daemon=True).start()

    def _update_loading_status(self, text: str):
        try:
            self.canvas.delete("loading_text")
            w = max(400, self.canvas.winfo_width()) // 2
            h = max(300, self.canvas.winfo_height()) // 2
            self.canvas.create_text(w, h, text=text, fill="#38bdf8", font=FONT_BOLD, tags=("loading_text",))
        except Exception:
            pass

    def _handle_stream_error(self, msg: str):
        messagebox.showerror("播放提示", f"{msg}\n\n建议:\n1. 确认该视频链接是否正常；\n2. 您也可以点击【浏览器中播放】或使用外部播放器。", parent=self)
        self.destroy()

    def _open_opencv_capture(self, filepath: str):
        try:
            import cv2
            self.cap = cv2.VideoCapture(filepath)
            if not self.cap.isOpened():
                self._handle_stream_error("未能解析视频帧编码。")
                return

            self.canvas.delete("loading_text")
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
            if self.fps <= 0 or self.fps > 120:
                self.fps = 30.0

            self.is_playing = True
            self._update_frame()
        except Exception as e:
            self._handle_stream_error(f"OpenCV 读取失败: {e}")

    def _update_frame(self):
        if not self.is_playing or not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            # Reached current buffered end or video end
            if not self.is_buffering_active:
                self.is_playing = False
                self.btn_play_pause.config(text="▶️ 播放")
            else:
                # Still downloading in background, wait slightly and retry
                self.after(300, self._update_frame)
            return

        self.current_frame_idx += 1
        
        # Resize frame to fit canvas while preserving aspect ratio
        try:
            import cv2
            canvas_w = max(100, self.canvas.winfo_width())
            canvas_h = max(100, self.canvas.winfo_height())
            
            fh, fw, _ = frame.shape
            scale = min(canvas_w / fw, canvas_h / fh)
            new_w = max(1, int(fw * scale))
            new_h = max(1, int(fh * scale))
            
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            tk_img = ImageTk.PhotoImage(pil_img)

            self.canvas.delete("all")
            self.canvas.create_image(canvas_w // 2, canvas_h // 2, anchor=tk.CENTER, image=tk_img)
            self.canvas_img = tk_img  # Keep reference

            # Update time and slider if not user dragging
            cur_sec = self.current_frame_idx / self.fps
            tot_sec = (self.total_frames / self.fps) if self.total_frames > 0 else 0
            cur_str = f"{int(cur_sec//60):02d}:{int(cur_sec%60):02d}"
            tot_str = f"{int(tot_sec//60):02d}:{int(tot_sec%60):02d}" if tot_sec > 0 else "--:--"
            self.lbl_time.config(text=f"{cur_str} / {tot_str}")

            if not self.is_slider_dragging and self.total_frames > 0:
                pct = (self.current_frame_idx / self.total_frames) * 100.0
                self.progress_var.set(pct)

        except Exception:
            pass

        delay_ms = max(10, int(1000.0 / self.fps))
        self.after(delay_ms, self._update_frame)

    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play_pause.config(text="⏸️ 暂停")
            self._update_frame()
        else:
            self.btn_play_pause.config(text="▶️ 播放")

    def restart_video(self):
        if self.cap and self.cap.isOpened():
            import cv2
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame_idx = 0
            self.is_playing = True
            self.btn_play_pause.config(text="⏸️ 暂停")
            self._update_frame()

    def seek_relative(self, delta_seconds: float):
        if not self.cap or not self.cap.isOpened() or self.total_frames <= 0:
            return
        import cv2
        delta_frames = int(delta_seconds * self.fps)
        target = max(0, min(self.total_frames - 1, self.current_frame_idx + delta_frames))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target)
        self.current_frame_idx = target
        if not self.is_playing:
            self.is_playing = True
            self._update_frame()

    def _on_slider_press(self, event):
        self.is_slider_dragging = True

    def _on_slider_release(self, event):
        self.is_slider_dragging = False
        if not self.cap or self.total_frames <= 0:
            return
        import cv2
        pct = self.progress_var.get()
        target = int((pct / 100.0) * self.total_frames)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target)
        self.current_frame_idx = target
        if not self.is_playing:
            self.is_playing = True
            self._update_frame()

    def _on_slider_move(self, val):
        pass

    def _toggle_fullscreen(self):
        is_fs = getattr(self, "_is_fullscreen", False)
        self._is_fullscreen = not is_fs
        self.attributes("-fullscreen", self._is_fullscreen)

    def _on_close(self):
        self.is_buffering_active = False
        self.is_playing = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        if self.temp_buffer_file and os.path.exists(self.temp_buffer_file):
            try:
                os.remove(self.temp_buffer_file)
            except Exception:
                pass
        self.destroy()


class UniversalMediaPlayer:
    """Master playback dispatcher supporting FFplay hardware accelerator, OpenCV embed player, and fallback."""

    @classmethod
    def play_video(cls, video_target: str, title: str = "视频播放", http_headers: Optional[Dict[str, str]] = None, proxy: Optional[str] = None, parent: Optional[tk.Widget] = None):
        if not video_target:
            return

        ffplay_exe = shutil.which("ffplay")
        is_local = os.path.exists(video_target)

        # Strategy 1: Ultra-Fast Dedicated FFplay Player (Supports full HEVC/AV1/VP9 codec + Audio Sync)
        if ffplay_exe:
            try:
                clean_title = f"{title} [全格式硬件加速播放器 - 空格暂停/方向键快退快进/Esc退出]"
                cmd = [ffplay_exe, "-window_title", clean_title]
                
                # Pass proxy to subprocess environment
                env = os.environ.copy()
                if proxy:
                    env["http_proxy"] = proxy
                    env["https_proxy"] = proxy
                    env["all_proxy"] = proxy

                # If network stream with anti-leech headers (e.g. Bilibili / WeChat)
                if not is_local and http_headers:
                    hdrs_list = []
                    for k, v in http_headers.items():
                        hdrs_list.append(f"{k}: {v}\r\n")
                    if hdrs_list:
                        cmd.extend(["-headers", "".join(hdrs_list)])

                cmd.append(video_target)
                
                creation_flags = 0
                if sys.platform == "win32":
                    creation_flags = subprocess.CREATE_NO_WINDOW

                subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creation_flags
                )
                return
            except Exception:
                pass

        # Strategy 2: Pure Python Built-in Embedded Canvas Player (Guaranteed Zero-Dependency Playback)
        if parent:
            try:
                BuiltinTkinterPlayerDialog(parent, video_target, title_text=title, http_headers=http_headers, proxy=proxy)
                return
            except Exception:
                pass

        # Strategy 3: System / Browser Fallback
        import webbrowser
        try:
            if sys.platform == "win32" and is_local:
                os.startfile(video_target)
            else:
                webbrowser.open(video_target)
        except Exception:
            webbrowser.open(video_target)


# ------------------ Universal Video & Thumbnail Visual Preview Dialog ------------------
class MediaPreviewDialog(tk.Toplevel):
    """Visual Dialog for previewing video thumbnail and streaming the MP4 video directly (prioritizing local downloaded files to save bandwidth)."""

    def __init__(self, parent, media_data: Dict[str, Any], variant_index: int = 0, proxy: Optional[str] = None, dest_dir: Optional[str] = None):
        super().__init__(parent)
        self.media_data = media_data
        self.proxy = proxy
        self.dest_dir = dest_dir
        variants = media_data.get("variants", [])
        self.current_variant = variants[variant_index] if 0 <= variant_index < len(variants) else (variants[0] if variants else {})
        
        # Check if file has already been downloaded to local disk
        filename = self.current_variant.get("filename", "")
        self.local_file_path = None
        if self.dest_dir and filename:
            candidate = os.path.normpath(os.path.join(self.dest_dir, filename))
            if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
                self.local_file_path = candidate

        plat_label = media_data.get("platform_label", "流媒体视频")
        loc_badge = " [🟢 本地已下载·0流量]" if self.local_file_path else " [🌐 远程网络流]"
        self.title(f"🎬 {plat_label} 视频与封面在线预览{loc_badge}")
        self.geometry("780x580")
        self.minsize(680, 480)
        self.transient(parent)
        self.grab_set()

        self.thumbnail_img = None
        center_window_on_parent(self, parent, 780, 580)
        self._build_ui()
        self._load_thumbnail_async()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Top Meta Header
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 6))

        plat_label = self.media_data.get("platform_label", "视频")
        author = self.media_data.get("author", "视频作者")
        author_id = self.media_data.get("author_id", "")
        pub_date = self.media_data.get("date", "--")
        q_label = self.current_variant.get("quality", "标准 MP4")
        sz = self.current_variant.get("size_str", "--")

        title_color = "#198754" if self.local_file_path else "#0d6efd"
        status_tag = " [🟢 本地已下载·0流量秒开]" if self.local_file_path else ""
        lbl_title = ttk.Label(top_frame, text=f"[{plat_label}] 👤 {author} ({author_id})  |  {q_label}{status_tag}  |  大小: {sz}", font=FONT_BOLD, foreground=title_color)
        lbl_title.pack(anchor=tk.W, pady=(0, 2))

        lbl_sub = ttk.Label(top_frame, text=f"🕒 发布时间: {pub_date}  |  时长: {self.media_data.get('duration', '--')}", font=FONT_SMALL, foreground="#555555")
        lbl_sub.pack(anchor=tk.W, pady=(0, 4))

        # Text display
        text_box = tk.Text(top_frame, height=2, font=FONT_NORMAL, bg="#f8fafc", fg="#1e293b", wrap=tk.WORD, relief=tk.SOLID, bd=1)
        text_box.insert("1.0", self.media_data.get("text", "(无描述内容)"))
        text_box.config(state=tk.DISABLED)
        text_box.pack(fill=tk.X)

        # 2. Middle Thumbnail Canvas / Image Box
        img_frame = ttk.LabelFrame(main_frame, text=" 🖼️ 视频封面 (双击直接唤起内置全能播放器) ", padding="6")
        img_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 8))

        self.lbl_image = ttk.Label(img_frame, text="正在通过网络加载视频高清封面...", anchor=tk.CENTER, justify=tk.CENTER, font=FONT_NORMAL, cursor="hand2")
        self.lbl_image.pack(fill=tk.BOTH, expand=True)
        self.lbl_image.bind("<Double-1>", lambda e: self.play_with_builtin_player())
        self.lbl_image.bind("<Button-1>", lambda e: self.play_with_builtin_player())

        # 3. Direct URL / Local Path Box
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 6))

        lbl_url_title = "本地路径:" if self.local_file_path else "直链地址:"
        ttk.Label(url_frame, text=lbl_url_title).pack(side=tk.LEFT, padx=(0, 4))
        
        self.direct_url = self.current_variant.get("url", "")
        display_path = self.local_file_path or self.direct_url
        entry_url = ttk.Entry(url_frame, font=FONT_NORMAL)
        entry_url.insert(0, display_path)
        entry_url.config(state="readonly")
        entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        copy_btn_text = "📋 复制本地路径" if self.local_file_path else "📋 复制直链"
        btn_copy_url = ttk.Button(url_frame, text=copy_btn_text, command=self._copy_url)
        btn_copy_url.pack(side=tk.RIGHT)

        # 4. Action Buttons Toolbar
        action_bar = ttk.Frame(main_frame)
        action_bar.pack(fill=tk.X)

        btn_play_builtin = tk.Button(
            action_bar,
            text="▶️ 内置全能播放器 (支持HEVC/AV1/全格式)",
            font=FONT_BOLD,
            bg="#198754" if self.local_file_path else "#0d6efd",
            fg="#ffffff",
            activebackground="#157347",
            activeforeground="#ffffff",
            padx=12, pady=4,
            command=self.play_with_builtin_player
        )
        btn_play_builtin.pack(side=tk.LEFT, padx=(0, 6))

        btn_embed = ttk.Button(
            action_bar,
            text="📺 内置弹窗播放",
            command=self.open_embedded_player
        )
        btn_embed.pack(side=tk.LEFT, padx=4)

        if not self.local_file_path:
            btn_play_browser = ttk.Button(
                action_bar,
                text="🌐 浏览器中播放",
                command=self.open_in_browser
            )
            btn_play_browser.pack(side=tk.LEFT, padx=4)
        else:
            btn_open_loc = ttk.Button(
                action_bar,
                text="📂 打开所在文件夹",
                command=lambda: os.startfile(os.path.dirname(self.local_file_path)) if sys.platform == "win32" else None
            )
            btn_open_loc.pack(side=tk.LEFT, padx=4)

        btn_close = ttk.Button(action_bar, text="关闭预览", command=self.destroy)
        btn_close.pack(side=tk.RIGHT)

    def _copy_url(self):
        target = self.local_file_path or self.direct_url
        if target:
            self.clipboard_clear()
            self.clipboard_append(target)
            msg = "已将本地文件路径复制到剪贴板！" if self.local_file_path else "已将视频播放直链复制到剪贴板！"
            messagebox.showinfo("复制成功", msg, parent=self)

    def play_with_builtin_player(self):
        target = self.local_file_path or self.direct_url
        if not target:
            return
        title = self.media_data.get("text") or "视频预览"
        headers = self.current_variant.get("http_headers")
        UniversalMediaPlayer.play_video(target, title=title, http_headers=headers, proxy=self.proxy, parent=self)

    def open_embedded_player(self):
        target = self.local_file_path or self.direct_url
        if not target:
            return
        title = self.media_data.get("text") or "视频播放"
        headers = self.current_variant.get("http_headers")
        BuiltinTkinterPlayerDialog(self, target, title_text=title, http_headers=headers, proxy=self.proxy)

    def open_in_browser(self):
        target = self.local_file_path or self.direct_url
        if not target:
            return
        import webbrowser
        webbrowser.open(target)

    def _load_thumbnail_async(self):
        thumb_url = self.media_data.get("thumbnail")
        if not thumb_url:
            self.lbl_image.config(text="▶️ 该视频未提供封面 (点击直接内置播放)")
            return

        def _fetch():
            try:
                proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                if "bilibili" in thumb_url or "hdslb.com" in thumb_url:
                    headers["Referer"] = "https://www.bilibili.com/"
                elif "weixin.qq.com" in thumb_url or "qpic.cn" in thumb_url:
                    headers["Referer"] = "https://mp.weixin.qq.com/"
                resp = requests.get(thumb_url, headers=headers, proxies=proxies, timeout=12)
                if resp.status_code == 200:
                    import io
                    img_data = io.BytesIO(resp.content)
                    pil_img = Image.open(img_data)
                    pil_img.thumbnail((620, 320), Image.Resampling.LANCZOS)
                    tk_img = ImageTk.PhotoImage(pil_img)
                    self.after(0, lambda img=tk_img: self._set_image(img))
                else:
                    self.after(0, lambda: self.lbl_image.config(text="▶️ 封面加载失败 (点击直接调用内置播放器播放)"))
            except Exception:
                self.after(0, lambda: self.lbl_image.config(text="▶️ 点击直接调用内置播放器播放"))

        threading.Thread(target=_fetch, daemon=True).start()

    def _set_image(self, tk_img):
        self.thumbnail_img = tk_img
        self.lbl_image.config(image=tk_img, text="")


# Backward compatibility alias
TwitterPreviewDialog = MediaPreviewDialog


# ------------------ History & Starred Repository Database ------------------
class HistoryManager:
    """Lightweight persistent JSON database manager for Hugging Face and GitHub repository access history."""
    
    @staticmethod
    def load_history() -> List[Dict[str, Any]]:
        if os.path.exists(HISTORY_DB_FILE):
            try:
                with open(HISTORY_DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("history", [])
            except Exception:
                return []
        return []

    @staticmethod
    def save_history(records: List[Dict[str, Any]]):
        try:
            with open(HISTORY_DB_FILE, "w", encoding="utf-8") as f:
                json.dump({"history": records}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @staticmethod
    def record_access(repo_id: str, platform: str, repo_type: str = "model", branch: str = "main", file_count: int = 0, note: str = "") -> List[Dict[str, Any]]:
        records = HistoryManager.load_history()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        target = None
        for r in records:
            if r.get("repo_id") == repo_id and r.get("platform") == platform:
                target = r
                break
        
        if target:
            target["last_accessed"] = now_str
            target["branch"] = branch
            target["repo_type"] = repo_type
            if file_count > 0:
                target["file_count"] = file_count
            if note:
                target["note"] = note
            records.remove(target)
            records.insert(0, target)
        else:
            records.insert(0, {
                "repo_id": repo_id,
                "platform": platform,
                "repo_type": repo_type,
                "branch": branch,
                "file_count": file_count,
                "last_accessed": now_str,
                "is_starred": False,
                "note": note
            })
        
        # Sort: starred first, then last_accessed desc
        records.sort(key=lambda x: (not x.get("is_starred", False), x.get("last_accessed", "")), reverse=False)
        records = records[:300]
        HistoryManager.save_history(records)
        return records

    @staticmethod
    def toggle_star(repo_id: str, platform: str) -> bool:
        records = HistoryManager.load_history()
        new_state = False
        for r in records:
            if r.get("repo_id") == repo_id and r.get("platform") == platform:
                r["is_starred"] = not r.get("is_starred", False)
                new_state = r["is_starred"]
                break
        records.sort(key=lambda x: (not x.get("is_starred", False), x.get("last_accessed", "")), reverse=False)
        HistoryManager.save_history(records)
        return new_state

    @staticmethod
    def update_note(repo_id: str, platform: str, note: str):
        records = HistoryManager.load_history()
        for r in records:
            if r.get("repo_id") == repo_id and r.get("platform") == platform:
                r["note"] = note
                break
        HistoryManager.save_history(records)

    @staticmethod
    def delete_record(repo_id: str, platform: str):
        records = HistoryManager.load_history()
        records = [r for r in records if not (r.get("repo_id") == repo_id and r.get("platform") == platform)]
        HistoryManager.save_history(records)

    @staticmethod
    def clear_all():
        HistoryManager.save_history([])

    @staticmethod
    def get_recent_repos(platform: Optional[str] = None) -> List[str]:
        records = HistoryManager.load_history()
        res = []
        for r in records:
            if platform is None or r.get("platform") == platform:
                rid = r.get("repo_id")
                if rid and rid not in res:
                    res.append(rid)
        return res


class HistoryManagerDialog(tk.Toplevel):
    """Visual Manager Dialog for Repository Access History and Starred Bookmarks."""
    
    def __init__(self, parent, on_load_callback, default_platform: Optional[str] = None):
        super().__init__(parent)
        self.on_load_callback = on_load_callback
        self.default_platform = default_platform
        self.records: List[Dict[str, Any]] = HistoryManager.load_history()

        # Dynamic title based on active tab
        if default_platform == "huggingface":
            self.title("🤗 Hugging Face 专属历史记录与智能收藏库")
        elif default_platform == "github":
            self.title("🐙 GitHub 仓库专属历史记录与智能收藏库")
        elif default_platform == "twitter":
            self.title("🐦 Twitter / X 专属推文解析历史与智能收藏库")
        else:
            self.title("🕒 全局历史记录与智能收藏库 (History & Starred Hub)")

        self.geometry("880x540")
        self.minsize(740, 420)
        self.transient(parent)
        self.grab_set()

        center_window_on_parent(self, parent, 880, 540)

        self._build_ui()
        self._filter_and_render()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Top Filter and Search Bar
        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(top_bar, text="🔍 搜索历史:", font=FONT_BOLD).pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_and_render())
        search_entry = ttk.Entry(top_bar, textvariable=self.search_var, width=24, font=FONT_NORMAL)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(top_bar, text="视图范围:", font=FONT_BOLD).pack(side=tk.LEFT, padx=(0, 4))
        
        # Dedicated platform filter options
        if self.default_platform == "huggingface":
            platform_options = ["🤗 Hugging Face 专属", "⭐ 仅看当前收藏", "🐙 GitHub", "🐦 Twitter / X", "🌐 全部历史记录"]
            self.filter_platform_var = tk.StringVar(value="🤗 Hugging Face 专属")
        elif self.default_platform == "github":
            platform_options = ["🐙 GitHub 专属", "⭐ 仅看当前收藏", "🤗 Hugging Face", "🐦 Twitter / X", "🌐 全部历史记录"]
            self.filter_platform_var = tk.StringVar(value="🐙 GitHub 专属")
        elif self.default_platform == "twitter":
            platform_options = ["🐦 Twitter / X 专属", "⭐ 仅看当前收藏", "🤗 Hugging Face", "🐙 GitHub", "🌐 全部历史记录"]
            self.filter_platform_var = tk.StringVar(value="🐦 Twitter / X 专属")
        else:
            platform_options = ["🌐 全部历史记录", "🤗 Hugging Face", "🐙 GitHub", "🐦 Twitter / X", "⭐ 仅看收藏"]
            self.filter_platform_var = tk.StringVar(value="🌐 全部历史记录")

        filter_combo = ttk.Combobox(
            top_bar, 
            textvariable=self.filter_platform_var, 
            values=platform_options, 
            width=20, 
            state="readonly", 
            font=FONT_NORMAL
        )
        filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self._filter_and_render())

        self.lbl_stats = ttk.Label(top_bar, text="共 0 条记录", font=FONT_SMALL, foreground="#555555")
        self.lbl_stats.pack(side=tk.RIGHT, padx=4)

        # 2. Main History Treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        cols = ("star", "platform", "repo_id", "branch", "file_count", "time", "note")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        
        self.tree.heading("star", text="⭐ 收藏", anchor=tk.CENTER)
        self.tree.heading("platform", text="平台", anchor=tk.CENTER)
        self.tree.heading("repo_id", text="仓库 ID / 推文项目", anchor=tk.W)
        self.tree.heading("branch", text="分支/ID", anchor=tk.CENTER)
        self.tree.heading("file_count", text="资源数", anchor=tk.CENTER)
        self.tree.heading("time", text="最后访问时间", anchor=tk.CENTER)
        self.tree.heading("note", text="自定义备注 (双击编辑)", anchor=tk.W)

        self.tree.column("star", width=65, minwidth=55, stretch=False, anchor=tk.CENTER)
        self.tree.column("platform", width=120, minwidth=100, stretch=False, anchor=tk.CENTER)
        self.tree.column("repo_id", width=260, minwidth=180, stretch=True, anchor=tk.W)
        self.tree.column("branch", width=85, minwidth=70, stretch=False, anchor=tk.CENTER)
        self.tree.column("file_count", width=80, minwidth=65, stretch=False, anchor=tk.CENTER)
        self.tree.column("time", width=130, minwidth=120, stretch=False, anchor=tk.CENTER)
        self.tree.column("note", width=180, minwidth=120, stretch=True, anchor=tk.W)

        self.tree.tag_configure("starred_tag", background="#fff8e1")
        self.tree.tag_configure("hf_tag", foreground="#0d6efd")
        self.tree.tag_configure("gh_tag", foreground="#198754")
        self.tree.tag_configure("tw_tag", foreground="#0284c7")

        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        scroll_y.grid(row=0, column=1, sticky=tk.NS)
        scroll_x.grid(row=1, column=0, sticky=tk.EW)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self._on_double_click)

        # 3. Bottom Action Buttons Bar
        action_bar = ttk.Frame(main_frame)
        action_bar.pack(fill=tk.X)

        btn_load = tk.Button(
            action_bar,
            text="🚀 载入并检索选中项目",
            font=FONT_BOLD,
            bg="#0d6efd",
            fg="#ffffff",
            activebackground="#0b5ed7",
            activeforeground="#ffffff",
            padx=12, pady=4,
            command=self.load_selected
        )
        btn_load.pack(side=tk.LEFT, padx=(0, 6))

        btn_star = ttk.Button(action_bar, text="⭐ 切换收藏", command=self.toggle_selected_star)
        btn_star.pack(side=tk.LEFT, padx=4)

        btn_edit_note = ttk.Button(action_bar, text="✏️ 编辑备注...", command=self.edit_selected_note)
        btn_edit_note.pack(side=tk.LEFT, padx=4)

        btn_del = ttk.Button(action_bar, text="🗑️ 删除记录", command=self.delete_selected)
        btn_del.pack(side=tk.LEFT, padx=4)

        btn_clear = ttk.Button(action_bar, text="🧹 清空当前历史", command=self.clear_all_history)
        btn_clear.pack(side=tk.LEFT, padx=6)

        btn_close = ttk.Button(action_bar, text="关闭窗口", command=self.destroy)
        btn_close.pack(side=tk.RIGHT)

    def _filter_and_render(self):
        self.records = HistoryManager.load_history()
        search_kw = self.search_var.get().strip().lower()
        platform_filter = self.filter_platform_var.get()

        filtered = []
        for r in self.records:
            plat = r.get("platform", "")
            
            # Platform filtering
            if "Hugging Face" in platform_filter and plat != "huggingface":
                continue
            elif "GitHub" in platform_filter and plat != "github":
                continue
            elif "Twitter" in platform_filter and plat != "twitter":
                continue
            elif platform_filter == "⭐ 仅看当前收藏":
                target_plat = self.default_platform or "huggingface"
                if plat != target_plat or not r.get("is_starred", False):
                    continue
            elif platform_filter == "⭐ 全部收藏" and not r.get("is_starred", False):
                continue

            # Search keyword matching
            if search_kw:
                rid = r.get("repo_id", "").lower()
                note = r.get("note", "").lower()
                branch = r.get("branch", "").lower()
                if search_kw not in rid and search_kw not in note and search_kw not in branch:
                    continue

            filtered.append(r)

        # Dynamic Headings based on active filter
        if "Twitter" in platform_filter:
            self.tree.heading("repo_id", text="推文作者 / Tweet ID")
            self.tree.heading("branch", text="推文 ID")
            self.tree.heading("file_count", text="视频画质数")
        else:
            self.tree.heading("repo_id", text="仓库 ID / 项目名称")
            self.tree.heading("branch", text="分支/Tag")
            self.tree.heading("file_count", text="文件数")

        self.tree.delete(*self.tree.get_children())
        for i, item in enumerate(filtered):
            is_starred = item.get("is_starred", False)
            star_sym = "⭐ 收藏" if is_starred else "☆"
            plat_raw = item.get("platform", "")
            
            if plat_raw == "huggingface":
                plat_disp = "🤗 HuggingFace"
                tag_plat = "hf_tag"
            elif plat_raw == "github":
                plat_disp = "🐙 GitHub"
                tag_plat = "gh_tag"
            elif plat_raw == "twitter":
                plat_disp = "🐦 Twitter/X"
                tag_plat = "tw_tag"
            else:
                plat_disp = plat_raw
                tag_plat = "hf_tag"

            f_count = f"{item.get('file_count', 0)} 项" if item.get("file_count") else "--"
            
            tags = [tag_plat]
            if is_starred:
                tags.append("starred_tag")

            self.tree.insert(
                "", tk.END, iid=str(i),
                values=(
                    star_sym,
                    plat_disp,
                    item.get("repo_id", ""),
                    item.get("branch", "main"),
                    f_count,
                    item.get("last_accessed", "--"),
                    item.get("note", "")
                ),
                tags=tuple(tags)
            )

        self.filtered_records = filtered
        self.lbl_stats.config(text=f"显示 {len(filtered)} / 共 {len(self.records)} 条")

    def _get_selected_record(self) -> Optional[Dict[str, Any]]:
        sel = self.tree.selection()
        if not sel:
            return None
        idx = int(sel[0])
        if 0 <= idx < len(self.filtered_records):
            return self.filtered_records[idx]
        return None

    def load_selected(self):
        rec = self._get_selected_record()
        if not rec:
            messagebox.showinfo("提示", "请先在表格中选择要载入的历史仓库！", parent=self)
            return
        
        self.destroy()
        self.on_load_callback(
            platform=rec.get("platform", "huggingface"),
            repo_id=rec.get("repo_id", ""),
            repo_type=rec.get("repo_type", "model"),
            branch=rec.get("branch", "main")
        )

    def _on_double_click(self, event):
        self.load_selected()

    def toggle_selected_star(self):
        rec = self._get_selected_record()
        if not rec:
            messagebox.showinfo("提示", "请先选择要收藏/取消收藏的仓库记录！", parent=self)
            return
        HistoryManager.toggle_star(rec["repo_id"], rec["platform"])
        self._filter_and_render()

    def edit_selected_note(self):
        rec = self._get_selected_record()
        if not rec:
            messagebox.showinfo("提示", "请先选择要编辑备注的仓库！", parent=self)
            return
        
        from tkinter import simpledialog
        new_note = simpledialog.askstring(
            "修改自定义备注",
            f"为仓库 [{rec['repo_id']}] 设置便于记忆的中文备注：",
            initialvalue=rec.get("note", ""),
            parent=self
        )
        if new_note is not None:
            HistoryManager.update_note(rec["repo_id"], rec["platform"], new_note.strip())
            self._filter_and_render()

    def delete_selected(self):
        rec = self._get_selected_record()
        if not rec:
            messagebox.showinfo("提示", "请先选择要删除的历史记录！", parent=self)
            return
        
        if messagebox.askyesno("确认删除", f"确定要从历史记录中移除该仓库吗？\n{rec['repo_id']}", parent=self):
            HistoryManager.delete_record(rec["repo_id"], rec["platform"])
            self._filter_and_render()

    def clear_all_history(self):
        if messagebox.askyesno("确认清空", "确定要清空全部仓库访问历史与收藏吗？\n此操作不可撤销！", parent=self):
            HistoryManager.clear_all()
            self._filter_and_render()


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

        center_window_on_parent(self, parent, 520, 330)

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


import re

# ------------------ High-Performance Magnet & BitTorrent Engine ------------------
DEFAULT_PUBLIC_TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.tracker.cl:1337/announce",
    "udp://9.rarbg.to:2920/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.moeking.me:6969/announce",
    "udp://explodie.org:6969/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://tracker.dler.org:6969/announce",
    "udp://ipv4.tracker.harry.lu:80/announce",
    "http://tracker.openbittorrent.com:80/announce",
    "udp://tracker.bittor.pw:1337/announce"
]

class MagnetResolver:
    """Intelligent Magnet link parser and active public trackers enhancer."""

    @staticmethod
    def is_magnet_link(url: str) -> bool:
        if not url:
            return False
        s = url.strip().lower()
        return s.startswith("magnet:?") or "xt=urn:btih:" in s

    @classmethod
    def parse_magnet(cls, raw_magnet: str) -> Dict[str, Any]:
        import urllib.parse
        raw_magnet = raw_magnet.strip()
        parsed = urllib.parse.urlparse(raw_magnet)
        query_params = urllib.parse.parse_qs(parsed.query)

        xt_list = query_params.get("xt", [])
        info_hash = ""
        for xt in xt_list:
            if xt.lower().startswith("urn:btih:"):
                info_hash = xt[9:].strip().upper()
                break

        if not info_hash:
            m = re.search(r'urn:btih:([a-zA-Z0-9]{32,40})', raw_magnet, re.IGNORECASE)
            if m:
                info_hash = m.group(1).upper()

        if not info_hash:
            raise ValueError("无法从磁力链接中提取到有效的特征码 (InfoHash)！")

        dn_list = query_params.get("dn", [])
        display_name = dn_list[0] if dn_list else f"Magnet_{info_hash[:12]}"
        display_name = urllib.parse.unquote_plus(display_name)

        existing_tr = query_params.get("tr", [])
        all_trackers = list(dict.fromkeys(existing_tr + DEFAULT_PUBLIC_TRACKERS))

        enhanced_params = [
            ("xt", f"urn:btih:{info_hash}"),
            ("dn", display_name)
        ]
        for tr in all_trackers:
            enhanced_params.append(("tr", tr))
        
        enhanced_magnet = "magnet:?" + urllib.parse.urlencode(enhanced_params, doseq=True)

        return {
            "info_hash": info_hash,
            "name": display_name,
            "trackers": all_trackers,
            "tracker_count": len(all_trackers),
            "enhanced_magnet": enhanced_magnet,
            "raw_magnet": raw_magnet
        }


class Aria2Manager:
    """Portable Aria2 engine manager for multi-thread high-speed BT/Magnet downloading."""

    _cached_exe = None

    @classmethod
    def find_executable(cls) -> Optional[str]:
        if cls._cached_exe and os.path.exists(cls._cached_exe):
            return cls._cached_exe

        candidates = [
            os.path.join(os.path.dirname(__file__), "aria2c.exe"),
            os.path.join(os.path.dirname(__file__), "bin", "aria2c.exe"),
            os.path.join(os.path.dirname(__file__), "tools", "aria2c.exe"),
            os.path.join(os.path.expanduser("~"), ".hf_downloader", "bin", "aria2c.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "aria2", "aria2c.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "aria2", "aria2c.exe"),
        ]
        which_path = shutil.which("aria2c")
        if which_path:
            candidates.insert(0, which_path)

        for p in candidates:
            if p and os.path.exists(p) and os.path.isfile(p):
                cls._cached_exe = p
                return p
        return None

    @classmethod
    def ensure_executable(cls, log_callback=None) -> str:
        exe = cls.find_executable()
        if exe:
            return exe

        # Auto-download portable static aria2c.exe for Windows
        dest_dir = os.path.join(os.path.expanduser("~"), ".hf_downloader", "bin")
        os.makedirs(dest_dir, exist_ok=True)
        dest_exe = os.path.join(dest_dir, "aria2c.exe")

        if os.path.exists(dest_exe) and os.path.getsize(dest_exe) > 1024 * 1024:
            cls._cached_exe = dest_exe
            return dest_exe

        if log_callback:
            log_callback("⏳ 首次使用磁力下载，正在自动准备高速绿色版 Aria2 引擎...")

        # Official static win64 release with multiple accelerator mirrors
        download_urls = [
            "https://ghfast.top/https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip",
            "https://mirror.ghproxy.com/https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip",
            "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip"
        ]
        
        import zipfile
        temp_zip = os.path.join(dest_dir, "aria2_temp.zip")
        for u in download_urls:
            try:
                r = requests.get(u, stream=True, timeout=20)
                if r.status_code == 200:
                    with open(temp_zip, "wb") as f:
                        for chunk in r.iter_content(chunk_size=64*1024):
                            if chunk:
                                f.write(chunk)
                    
                    with zipfile.ZipFile(temp_zip, 'r') as z:
                        for item in z.namelist():
                            if item.endswith("aria2c.exe"):
                                with z.open(item) as src, open(dest_exe, "wb") as dst:
                                    dst.write(src.read())
                                break
                    
                    if os.path.exists(temp_zip):
                        os.remove(temp_zip)
                    if os.path.exists(dest_exe):
                        if log_callback:
                            log_callback("✓ 高速绿色版 Aria2 引擎已就绪！")
                        cls._cached_exe = dest_exe
                        return dest_exe
            except Exception as e:
                continue

        if os.path.exists(temp_zip):
            try: os.remove(temp_zip)
            except Exception: pass

        raise RuntimeError("未能自动下载 Aria2 引擎，请确认网络连接或手动安装 aria2c！")

    @classmethod
    def download_magnet(cls, enhanced_magnet: str, dest_dir: str, filename_hint: str,
                        proxy: Optional[str] = None, task: Optional[Any] = None,
                        update_ui_callback=None, cancel_checker=None, log_callback=None) -> bool:
        exe = cls.ensure_executable(log_callback=log_callback)
        os.makedirs(dest_dir, exist_ok=True)

        cmd = [
            exe,
            enhanced_magnet,
            f"--dir={dest_dir}",
            "--enable-dht=true",
            "--dht-listen-port=6881-6999",
            "--enable-peer-exchange=true",
            "--bt-enable-lpd=true",
            "--bt-max-peers=120",
            "--bt-request-peer-speed-limit=100M",
            "--max-connection-per-server=16",
            "--seed-time=0",
            "--summary-interval=1",
            "--file-allocation=none",
            "--console-log-level=notice"
        ]
        if proxy:
            cmd.append(f"--all-proxy={proxy}")

        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=creationflags
        )

        prog_pattern = re.compile(
            r'\[#\w+\s+([\d\.]+\w+)/([\d\.]+\w+)\s*(?:\((\d+(?:\.\d+)?)%\))?\s+CN:(\d+)(?:\s+SD:(\d+))?\s+DL:([\d\.]+\w+(?:/s)?)(?:\s+ETA:(\w+))?\]'
        )

        last_update = 0.0
        success = False

        try:
            for line in proc.stdout:
                if cancel_checker and cancel_checker():
                    proc.terminate()
                    break

                line_s = line.strip()
                if not line_s:
                    continue

                if "Download complete" in line_s or "download completed" in line_s.lower():
                    success = True

                m = prog_pattern.search(line_s)
                if m:
                    cur_sz, tot_sz, pct, cn, sd, dl, eta = m.groups()
                    now = time.time()
                    if now - last_update >= 0.3:
                        last_update = now
                        pct_val = float(pct) if pct else 0.0
                        speed_str = dl if "/s" in dl else f"{dl}/s"
                        peer_info = f"连接: {cn} | 种子: {sd or 0}"
                        eta_str = eta or "--"
                        if task:
                            task.progress = pct_val
                            task.speed_str = speed_str
                            task.eta_str = eta_str
                        if update_ui_callback:
                            update_ui_callback(pct_val, cur_sz, tot_sz, speed_str, eta_str, peer_info)

            proc.wait(timeout=5)
            if proc.returncode == 0:
                success = True
        except Exception as e:
            try: proc.kill()
            except Exception: pass
            if task:
                task.error_msg = str(e)
            return False

        if success and task:
            task.progress = 100.0
        return success


# ------------------ Intelligent Quark Cloud Drive (pan.quark.cn) Resolver ------------------
# ------------------ Intelligent Quark Cloud Drive (pan.quark.cn) Resolver ------------------
class QuarkPanResolver:
    """Intelligent Quark Cloud Drive (pan.quark.cn) share parser and direct download link generator."""

    BASE_URLS = [
        "https://drive.quark.cn/1/clouddrive",
        "https://pan.quark.cn/1/clouddrive",
        "https://drive-pc.quark.cn/1/clouddrive"
    ]

    @staticmethod
    def is_quark_link(url: str) -> bool:
        if not url:
            return False
        return "pan.quark.cn/s/" in url or "quark.cn/s/" in url

    @staticmethod
    def extract_pwd_and_passcode(raw_input: str) -> tuple:
        m_pwd = re.search(r'pan\.quark\.cn/s/([a-zA-Z0-9]+)', raw_input)
        if not m_pwd:
            m_pwd = re.search(r'quark\.cn/s/([a-zA-Z0-9]+)', raw_input)
        pwd_id = m_pwd.group(1) if m_pwd else ""

        m_code = re.search(r'(?:提取码|密码|code|pwd)[:：\s=]*([a-zA-Z0-9]{4,6})', raw_input, re.IGNORECASE)
        passcode = m_code.group(1) if m_code else ""

        return pwd_id, passcode

    @classmethod
    def resolve_share(cls, raw_input: str, proxy: Optional[str] = None, cookie: Optional[str] = None) -> Dict[str, Any]:
        pwd_id, passcode = cls.extract_pwd_and_passcode(raw_input)
        if not pwd_id:
            raise ValueError("未能识别到有效的夸克网盘分享链接 (https://pan.quark.cn/s/...)！")

        proxies = {"http": proxy, "https": proxy} if proxy else None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 QuarkPC/2.5.0",
            "Referer": f"https://pan.quark.cn/s/{pwd_id}",
            "Origin": "https://pan.quark.cn",
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*"
        }
        if cookie:
            headers["Cookie"] = cookie

        # Step 1: Request share_token with multi-endpoint failover and detailed error diagnostics
        share_token = ""
        last_err = ""
        for base in cls.BASE_URLS:
            try:
                token_url = f"{base}/share/sharepage/token"
                r_tok = requests.post(token_url, json={"pwd_id": pwd_id, "passcode": passcode}, headers=headers, proxies=proxies, timeout=10)
                tok_data = r_tok.json()
                code = tok_data.get("code")
                msg = tok_data.get("message") or tok_data.get("msg") or ""

                if code == 0 or tok_data.get("status") == 200:
                    share_token = tok_data.get("data", {}).get("share_token") or ""
                    if share_token:
                        break
                elif code == 41006 or r_tok.status_code == 404:
                    raise ValueError("夸克网盘提示: 该分享链接不存在或已被作者取消！")
                elif code == 41007:
                    raise ValueError("夸克网盘提示: 提取码错误，请在链接后附带 提取码:xxxx")
                elif code == 41008:
                    raise ValueError("夸克网盘提示: 该分享链接已过期！")
                elif msg:
                    last_err = msg
            except ValueError:
                raise
            except Exception as e:
                last_err = str(e)
                continue

        if not share_token:
            err = last_err or "获取分享 Token 失败，可能是链接失效或需要提取码"
            raise ValueError(f"夸克网盘提示: {err} (若需提取码请在链接后输入 提取码:xxxx)")

        # Step 2: Request share file list detail
        detail_json = None
        for base in cls.BASE_URLS:
            try:
                detail_url = f"{base}/share/sharepage/detail"
                params = {
                    "pwd_id": pwd_id,
                    "stoken": share_token,
                    "pdir_fid": "0",
                    "force": "0",
                    "_page": "1",
                    "_size": "50",
                    "_fetch_total": "1",
                    "_sort": "file_type:asc,updated_at:desc"
                }
                r_detail = requests.get(detail_url, params=params, headers=headers, proxies=proxies, timeout=10)
                if r_detail.status_code == 200:
                    dj = r_detail.json()
                    if dj.get("code") == 0:
                        detail_json = dj
                        break
            except Exception:
                continue

        if not detail_json:
            raise ValueError("获取夸克分享文件列表失败，可能是由于网络连接波动或该分享受限，请稍后重试！")

        d_data = detail_json.get("data", {})
        share_title = d_data.get("title") or "夸克网盘分享资源"
        file_list = d_data.get("list", [])

        if not file_list:
            raise ValueError("该夸克网盘分享中暂无文件或已被分享者清空！")

        variants = []
        for f in file_list:
            fname = f.get("file_name") or "未命名文件"
            fid = f.get("fid") or ""
            fsize = f.get("size") or 0
            is_dir = f.get("file_type") == 0

            sz_str = f"{fsize / (1024*1024):.2f} MB" if fsize >= 1024*1024 else (f"{fsize/1024:.1f} KB" if fsize else ("目录" if is_dir else "--"))
            clean_fn = re.sub(r'[\\/*?:"<>|\r\n\t]', '_', f"[夸克]_{fname}")

            down_url = ""
            for base in cls.BASE_URLS:
                try:
                    down_api_url = f"{base}/share/sharepage/download"
                    r_dl = requests.post(down_api_url, json={
                        "pwd_id": pwd_id,
                        "stoken": share_token,
                        "fids": [fid]
                    }, headers=headers, proxies=proxies, timeout=8)
                    if r_dl.status_code == 200:
                        dl_json = r_dl.json()
                        dl_data = dl_json.get("data", [])
                        if dl_data and isinstance(dl_data, list):
                            down_url = dl_data[0].get("download_url") or ""
                            if down_url:
                                break
                except Exception:
                    continue

            target_download_url = down_url or f"https://pan.quark.cn/s/{pwd_id}#fid={fid}"
            ext_icon = "📁 " if is_dir else "📄 "
            variants.append({
                "quality": f"{ext_icon}{fname}",
                "height": 1080 if not is_dir else 0,
                "bitrate": 0,
                "bitrate_str": "夸克高速直链" if down_url else "夸克网盘资源",
                "size_str": sz_str,
                "raw_size": fsize,
                "url": target_download_url,
                "filename": clean_fn,
                "http_headers": {
                    "User-Agent": headers["User-Agent"],
                    "Referer": "https://pan.quark.cn/"
                },
                "source_url": f"https://pan.quark.cn/s/{pwd_id}",
                "format_id": fid
            })

        return {
            "platform": "quark",
            "platform_label": "📁 夸克网盘 (Quark Pan)",
            "media_id": pwd_id,
            "author": "夸克网盘分享",
            "author_id": f"分享ID: {pwd_id}",
            "text": share_title,
            "date": d_data.get("created_at") or "",
            "duration": f"共 {len(variants)} 个文件/目录",
            "thumbnail": None,
            "variants": variants
        }

class UniversalMediaResolver:
    """High-reliability multi-platform universal media parser for Bilibili, WeChat, Twitter/X, and 1000+ sites."""

    @staticmethod
    def detect_platform(raw_input: str) -> str:
        s = raw_input.strip().lower()
        if QuarkPanResolver.is_quark_link(raw_input):
            return "quark"
        if MagnetResolver.is_magnet_link(raw_input):
            return "magnet"
        if "bilibili.com" in s or "b23.tv" in s or re.search(r'\b(bv[a-za-z0-9]{10}|av\d+)\b', s):
            return "bilibili"
        if "mp.weixin.qq.com" in s:
            return "wechat_article"
        if "channels.weixin.qq.com" in s or "weixin.qq.com/sph" in s:
            return "wechat_channels"
        if "twitter.com" in s or "x.com" in s or "t.co" in s or re.match(r'^\d+$', s.strip()):
            return "twitter"
        return "universal"

    @classmethod
    def sanitize_filename(cls, name: str, max_len: int = 50) -> str:
        """Sanitize string for valid and readable OS filenames across Windows, macOS and Linux."""
        if not name:
            return "video"
        name = re.sub(r'<[^>]+>', '', str(name))
        cleaned = re.sub(r'[\\/*?:"<>|\r\n\t]', '_', name)
        cleaned = re.sub(r'[\s_]+', '_', cleaned).strip(' ._')
        if len(cleaned) > max_len:
            cleaned = cleaned[:max_len].rstrip(' ._')
        return cleaned or "video"

    @classmethod
    def build_media_filename(cls, platform: str, title: str, author: str = "", quality_tag: str = "", media_id: str = "", ext: str = "mp4") -> str:
        """Build an informative, clean, and intuitive filename across video platforms."""
        plat_tags = {
            "bilibili": "[B站]",
            "wechat_article": "[微信]",
            "wechat_channels": "[微信视频号]",
            "twitter": "[Twitter]",
            "youtube": "[YouTube]",
            "douyin": "[抖音]",
            "kuaishou": "[快手]",
            "universal": "[网络视频]"
        }
        tag = plat_tags.get(platform.lower(), f"[{platform.capitalize()}]")
        safe_title = cls.sanitize_filename(title or "视频", max_len=45)
        safe_author = cls.sanitize_filename(author or "", max_len=20)
        safe_q = cls.sanitize_filename(quality_tag or "", max_len=15)
        safe_id = cls.sanitize_filename(media_id or "", max_len=20)

        parts = [tag + safe_title]
        if safe_author:
            parts.append(safe_author)
        if safe_q:
            parts.append(safe_q)
        if safe_id and safe_id not in (safe_title, safe_author):
            parts.append(safe_id)

        base_name = "_".join(parts)
        ext_clean = ext.lstrip(".")
        return f"{base_name}.{ext_clean}"

    @classmethod
    def resolve(cls, raw_input: str, proxy: Optional[str] = None) -> Dict[str, Any]:
        if not raw_input or not raw_input.strip():
            raise ValueError("请输入有效的视频链接或推文/视频 ID！")
        raw_input = raw_input.strip()
        platform = cls.detect_platform(raw_input)

        if platform == "quark":
            return QuarkPanResolver.resolve_share(raw_input, proxy)
        elif platform == "magnet":
            return cls._resolve_magnet(raw_input, proxy)
        elif platform == "bilibili":
            return cls._resolve_bilibili(raw_input, proxy)
        elif platform == "wechat_article":
            return cls._resolve_wechat_article(raw_input, proxy)
        elif platform == "wechat_channels":
            return cls._resolve_wechat_channels(raw_input, proxy)
        elif platform == "twitter":
            return cls._resolve_twitter(raw_input, proxy)
        else:
            return cls._resolve_universal(raw_input, proxy)

    # ---------------- Magnet / BitTorrent Resolver ----------------
    @classmethod
    def _resolve_magnet(cls, raw_input: str, proxy: Optional[str]) -> Dict[str, Any]:
        info = MagnetResolver.parse_magnet(raw_input)
        info_hash = info["info_hash"]
        display_name = info["name"]
        enhanced_magnet = info["enhanced_magnet"]
        tr_cnt = info["tracker_count"]

        clean_fn = cls.sanitize_filename(f"[磁力]_{display_name}", max_len=60)
        # Preserve common extension if already present
        if not re.search(r'\.[a-zA-Z0-9]{2,5}$', clean_fn):
            clean_fn += ".mp4"

        variants_list = [{
            "quality": "🧲 P2P 完整资源包 (BT/磁力链接)",
            "height": 1080,
            "bitrate": 0,
            "bitrate_str": f"{tr_cnt} 个加速节点",
            "size_str": "P2P 动态流",
            "raw_size": 0,
            "url": enhanced_magnet,
            "filename": clean_fn,
            "http_headers": {},
            "source_url": enhanced_magnet,
            "format_id": "magnet"
        }]

        return {
            "platform": "magnet",
            "platform_label": "🧲 磁力链接 (BitTorrent)",
            "media_id": info_hash,
            "author": f"InfoHash: {info_hash[:16]}...",
            "author_id": f"Trackers: {tr_cnt}个",
            "text": display_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": "P2P 资源",
            "thumbnail": None,
            "variants": variants_list
        }

    # ---------------- Bilibili Resolver (Official View/PlayURL API + yt-dlp) ----------------
    @classmethod
    def _resolve_bilibili(cls, raw_input: str, proxy: Optional[str]) -> Dict[str, Any]:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com/"
        }

        # Follow 302 redirects for b23.tv short links
        clean_url = raw_input
        if "b23.tv" in clean_url:
            try:
                r_redir = requests.head(clean_url, headers=headers, proxies=proxies, allow_redirects=True, timeout=8)
                clean_url = r_redir.url
            except Exception:
                pass

        m_bv = re.search(r'(BV[a-zA-Z0-9]{10})', clean_url, re.IGNORECASE)
        m_av = re.search(r'av(\d+)', clean_url, re.IGNORECASE)
        bvid = m_bv.group(1) if m_bv else (f"av{m_av.group(1)}" if m_av else None)

        if bvid:
            try:
                # 1. Fetch metadata from Bilibili View API
                view_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}" if bvid.upper().startswith("BV") else f"https://api.bilibili.com/x/web-interface/view?aid={bvid[2:]}"
                r_view = requests.get(view_url, headers=headers, proxies=proxies, timeout=10)
                if r_view.status_code == 200:
                    v_json = r_view.json()
                    if v_json.get("code") == 0:
                        v_data = v_json.get("data", {})
                        title = v_data.get("title", "Bilibili 视频")
                        author = v_data.get("owner", {}).get("name", "Bilibili UP主")
                        author_id = f"UID: {v_data.get('owner', {}).get('mid', '')}"
                        thumbnail = v_data.get("pic")
                        cid = v_data.get("cid")
                        dur_sec = v_data.get("duration", 0)
                        dur_str = f"{int(dur_sec//60)}:{int(dur_sec%60):02d}" if dur_sec else "--"
                        pub_time = v_data.get("pubdate")
                        pub_date = datetime.fromtimestamp(pub_time).strftime("%Y-%m-%d %H:%M") if pub_time else datetime.now().strftime("%Y-%m-%d %H:%M")

                        # 2. Fetch PlayURL for high-res stream
                        play_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=80&fnval=1" if bvid.upper().startswith("BV") else f"https://api.bilibili.com/x/player/playurl?aid={bvid[2:]}&cid={cid}&qn=80&fnval=1"
                        r_play = requests.get(play_url, headers=headers, proxies=proxies, timeout=10)
                        variants_list = []
                        if r_play.status_code == 200:
                            p_json = r_play.json()
                            if p_json.get("code") == 0:
                                p_data = p_json.get("data", {})
                                durl_list = p_data.get("durl", [])
                                for d in durl_list:
                                    v_stream_url = d.get("url")
                                    v_size = d.get("size", 0)
                                    v_sz_str = f"{v_size / (1024*1024):.2f} MB" if v_size else "--"
                                    clean_fn = cls.build_media_filename("bilibili", title=title, author=author, quality_tag="1080P", media_id=bvid)
                                    variants_list.append({
                                        "quality": "🎬 1080P/720P 高清 (B站官方原生流)",
                                        "height": 1080,
                                        "bitrate": 0,
                                        "bitrate_str": "--",
                                        "size_str": v_sz_str,
                                        "raw_size": v_size,
                                        "url": v_stream_url,
                                        "filename": clean_fn,
                                        "http_headers": headers
                                    })
                        if variants_list:
                            return {
                                "platform": "bilibili",
                                "platform_label": "📺 哔哩哔哩 (Bilibili)",
                                "media_id": bvid,
                                "author": author,
                                "author_id": author_id,
                                "text": title.strip(),
                                "date": pub_date,
                                "duration": dur_str,
                                "thumbnail": thumbnail,
                                "variants": variants_list
                            }
            except Exception:
                pass

        # Strategy 2: Fallback to Universal yt-dlp
        return cls._resolve_universal(clean_url, proxy, override_label="📺 哔哩哔哩 (Bilibili)")

    # ---------------- WeChat Article Video Resolver ----------------
    @classmethod
    def _resolve_wechat_article(cls, article_url: str, proxy: Optional[str]) -> Dict[str, Any]:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Referer": "https://mp.weixin.qq.com/"
        }
        resp = requests.get(article_url, headers=headers, proxies=proxies, timeout=12)
        if resp.status_code != 200:
            raise ValueError(f"无法访问微信公众号文章 (HTTP {resp.status_code})！")

        html = resp.text
        m_title = re.search(r'<meta\s+property=[\'"]og:title[\'"]\s+content=[\'"](.*?)[\'"]', html) or re.search(r'var\s+msg_title\s*=\s*[\'"](.*?)[\'"]', html)
        title = m_title.group(1) if m_title else "微信公众号文章视频"
        m_author = re.search(r'<meta\s+property=[\'"]og:article:author[\'"]\s+content=[\'"](.*?)[\'"]', html) or re.search(r'var\s+nickname\s*=\s*[\'"](.*?)[\'"]', html)
        author = m_author.group(1) if m_author else "微信公众号"
        m_thumb = re.search(r'<meta\s+property=[\'"]og:image[\'"]\s+content=[\'"](.*?)[\'"]', html) or re.search(r'var\s+msg_cdn_url\s*=\s*[\'"](.*?)[\'"]', html)
        thumbnail = m_thumb.group(1) if m_thumb else None
        m_date = re.search(r'var\s+createTime\s*=\s*[\'"]?(\d+)[\'"]?', html)
        if m_date:
            try:
                pub_date = datetime.fromtimestamp(int(m_date.group(1))).strftime("%Y-%m-%d %H:%M")
            except:
                pub_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        else:
            pub_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Extract wxv_ vid list
        vids = list(dict.fromkeys(re.findall(r'vid=(wxv_\d+)', html) + re.findall(r'data-mpvid=[\'"](wxv_\d+)[\'"]', html) + re.findall(r'[\'"](wxv_\d+)[\'"]', html)))
        
        variants_list = []
        dur_str = "--"

        for vid in vids:
            api_url = f"https://mp.weixin.qq.com/mp/videoplayer?action=get_mp_video_play_url&preview=0&vid={vid}&f=json"
            r_api = requests.get(api_url, headers=headers, proxies=proxies, timeout=10)
            if r_api.status_code == 200:
                try:
                    data = r_api.json()
                    url_info = data.get("url_info", [])
                    for item in url_info:
                        furl = item.get("url")
                        if not furl:
                            continue
                        f_fmt = item.get("video_quality_wording") or "高清 MP4"
                        filesize = item.get("filesize", 0)
                        dur_ms = item.get("duration_ms", 0)
                        if dur_ms:
                            dur_sec = dur_ms / 1000
                            dur_str = f"{int(dur_sec//60)}:{int(dur_sec%60):02d}"
                        
                        sz_str = f"{filesize/(1024*1024):.2f} MB" if filesize else "--"
                        clean_fn = cls.build_media_filename("wechat_article", title=title, author=author, quality_tag=f_fmt, media_id=vid)

                        variants_list.append({
                            "quality": f"🎬 {f_fmt} (微信原生直链)",
                            "height": filesize or 720,
                            "bitrate": 0,
                            "bitrate_str": "--",
                            "size_str": sz_str,
                            "raw_size": filesize or 0,
                            "url": furl,
                            "filename": clean_fn,
                            "http_headers": headers
                        })
                except Exception:
                    pass

        if not variants_list:
            # Fallback to universal yt-dlp deep extract
            try:
                res_uni = cls._resolve_universal(article_url, proxy, override_label="📰 微信公众号视频")
                return res_uni
            except Exception:
                pass

        if not variants_list:
            raise ValueError("未能从该微信公众号文章中提取到视频，请确认文章内是否包含视频！")

        return {
            "platform": "wechat_article",
            "platform_label": "📰 微信公众号视频",
            "media_id": vids[0] if vids else "wechat",
            "author": author,
            "author_id": "@微信公众号",
            "text": title.strip(),
            "date": pub_date,
            "duration": dur_str,
            "thumbnail": thumbnail,
            "variants": variants_list
        }

    # ---------------- WeChat Channels Resolver ----------------
    @classmethod
    def _resolve_wechat_channels(cls, raw_input: str, proxy: Optional[str]) -> Dict[str, Any]:
        return cls._resolve_universal(raw_input, proxy, override_label="📱 微信视频号 (Channels)")

    # ---------------- Twitter / X 4-Layer Resolver ----------------
    @classmethod
    def _resolve_twitter(cls, raw_input: str, proxy: Optional[str]) -> Dict[str, Any]:
        tweet_id = None
        m = re.search(r'status/(\d+)', raw_input)
        if m:
            tweet_id = m.group(1)
        elif re.match(r'^\d+$', raw_input.strip()):
            tweet_id = raw_input.strip()

        target_url = f"https://twitter.com/i/status/{tweet_id}" if tweet_id else raw_input.strip()
        last_error_details = []

        # Strategy 1: FxTwitter High-Speed Global CDN API
        if tweet_id:
            try:
                url = f"https://api.fxtwitter.com/status/{tweet_id}"
                proxies = {"http": proxy, "https": proxy} if proxy else None
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                resp = requests.get(url, headers=headers, proxies=proxies, timeout=8)
                if resp.status_code == 200:
                    tweet = resp.json().get("tweet", {})
                    if tweet:
                        author_info = tweet.get("author", {})
                        author = author_info.get("name", "Twitter 用户")
                        screen_name = author_info.get("screen_name", "")
                        text = tweet.get("text", "")
                        pub_date = tweet.get("created_at", "")[:16].replace("T", " ") if tweet.get("created_at") else datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        all_media = tweet.get("media", {}).get("all", []) or tweet.get("media", {}).get("videos", [])
                        if all_media:
                            first_v = all_media[0]
                            thumbnail = first_v.get("thumbnail_url")
                            dur_sec = first_v.get("duration")
                            dur_str = f"{int(dur_sec//60)}:{int(dur_sec%60):02d}" if dur_sec else "--"
                            raw_variants = first_v.get("variants", [])
                            variants_list = []
                            seen_urls = set()

                            for var in raw_variants:
                                furl = var.get("url")
                                if not furl or furl in seen_urls:
                                    continue
                                seen_urls.add(furl)
                                br = var.get("bitrate", 0)
                                m_res = re.search(r'/(\d+)x(\d+)/', furl)
                                if m_res:
                                    w, h = int(m_res.group(1)), int(m_res.group(2))
                                    h_min = min(w, h)
                                    q_label = f"🎬 {h_min}P 超清 ({w}x{h})" if h_min >= 1080 else f"🎬 {h_min}P 高清 ({w}x{h})"
                                    clean_fn = cls.build_media_filename("twitter", title=text or f"推文视频_{tweet_id}", author=screen_name or author, quality_tag=f"{h_min}P", media_id=tweet_id)
                                else:
                                    q_label = f"🎬 MP4 视频 ({br // 1000} kbps)" if br else "🎬 标准 MP4 视频"
                                    clean_fn = cls.build_media_filename("twitter", title=text or f"推文视频_{tweet_id}", author=screen_name or author, quality_tag=f"{br//1000}k" if br else "标准", media_id=tweet_id)

                                est_size = f"{(br / 8 * dur_sec) / (1024*1024):.2f} MB" if (br and dur_sec) else "--"
                                variants_list.append({
                                    "quality": q_label,
                                    "height": br,
                                    "bitrate": br // 1000 if br else 0,
                                    "bitrate_str": f"{br // 1000} kbps" if br else "--",
                                    "size_str": est_size,
                                    "raw_size": int((br / 8) * dur_sec) if (br and dur_sec) else 0,
                                    "url": furl,
                                    "filename": clean_fn,
                                    "http_headers": {}
                                })

                            if variants_list:
                                variants_list.sort(key=lambda x: x["height"], reverse=True)
                                return {
                                    "platform": "twitter",
                                    "platform_label": "🐦 Twitter / X",
                                    "media_id": tweet_id,
                                    "author": author,
                                    "author_id": f"@{screen_name}" if screen_name else "",
                                    "text": text,
                                    "date": pub_date,
                                    "duration": dur_str,
                                    "thumbnail": thumbnail,
                                    "variants": variants_list
                                }
            except Exception as e_fx:
                last_error_details.append(f"FxTwitter: {e_fx}")

        # Strategy 2: Universal / yt-dlp Fallback
        try:
            res = cls._resolve_universal(target_url, proxy, override_label="🐦 Twitter / X")
            res["platform"] = "twitter"
            return res
        except Exception as e_uni:
            last_error_details.append(f"yt-dlp: {e_uni}")

        err_summary = "; ".join(last_error_details) if last_error_details else "未检测到推文中的视频直链"
        raise ValueError(f"{err_summary} (请检查推文是否包含视频或确认网络代理！)")

    # ---------------- Universal 1000+ Platforms Resolver ----------------
    @classmethod
    def _resolve_universal(cls, target_url: str, proxy: Optional[str], override_label: Optional[str] = None) -> Dict[str, Any]:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'socket_timeout': 15,
            'nocheckcertificate': True
        }
        if proxy:
            ydl_opts['proxy'] = proxy

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            if not info:
                raise ValueError("无法提取视频信息，请检查链接或网络代理！")

            title = info.get('description') or info.get('title') or "网络视频"
            uploader = info.get('uploader') or info.get('channel') or info.get('extractor_key') or "视频作者"
            uploader_id = info.get('uploader_id') or info.get('channel_id') or ""
            thumbnail = info.get('thumbnail')
            duration_sec = info.get('duration') or 0
            dur_str = f"{int(duration_sec//60)}:{int(duration_sec%60):02d}" if duration_sec else (info.get('duration_string') or "--")
            upload_date = info.get('upload_date')
            if upload_date and len(upload_date) == 8:
                upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
            else:
                upload_date = datetime.now().strftime("%Y-%m-%d %H:%M")

            formats = info.get('formats', [])
            video_variants = []
            seen_urls = set()

            for f in formats:
                furl = f.get('url')
                if not furl or furl in seen_urls:
                    continue
                seen_urls.add(furl)

                vcodec = f.get('vcodec')
                acodec = f.get('acodec')
                width = f.get('width')
                height = f.get('height')
                filesize = f.get('filesize') or f.get('filesize_approx')
                tbr = f.get('tbr') or f.get('vbr') or 0
                format_note = f.get('format_note') or ""

                if height:
                    if height >= 1080:
                        q_label = f"🎬 1080P 超清 ({width}x{height})"
                    elif height >= 720:
                        q_label = f"🎬 720P 高清 ({width}x{height})"
                    elif height >= 480:
                        q_label = f"🎬 480P 标清 ({width}x{height})"
                    else:
                        q_label = f"🎬 {height}P 流畅 ({width}x{height})"
                elif vcodec != 'none':
                    q_label = f"🎬 标准 MP4 视频 [{format_note}]" if format_note else "🎬 标准 MP4 视频"
                elif acodec != 'none' and vcodec == 'none':
                    q_label = "🎵 仅提取音频 (Audio Stream)"
                else:
                    continue

                size_str = "--"
                if filesize:
                    size_str = f"{filesize / (1024*1024):.2f} MB" if filesize >= 1024*1024 else f"{filesize/1024:.1f} KB"
                elif tbr and duration_sec:
                    est = (tbr * 1000 / 8) * duration_sec
                    size_str = f"~{est / (1024*1024):.1f} MB"

                ext = "m4a" if (acodec != 'none' and vcodec == 'none') else "mp4"
                q_tag = "音频" if ext == "m4a" else (f"{height}P" if height else "MP4")
                plat_key = str(info.get('extractor_key') or 'universal').lower()
                clean_fn = cls.build_media_filename(plat_key, title=title, author=uploader, quality_tag=q_tag, media_id=str(info.get('id') or '')[:16], ext=ext)

                video_variants.append({
                    "quality": q_label,
                    "height": height or (9999 if acodec != 'none' and vcodec == 'none' else 0),
                    "bitrate": int(tbr) if tbr else 0,
                    "bitrate_str": f"{int(tbr)} kbps" if tbr else "--",
                    "size_str": size_str,
                    "raw_size": filesize or 0,
                    "url": furl,
                    "filename": clean_fn,
                    "http_headers": info.get('http_headers') or {},
                    "format_id": str(f.get('format_id') or ""),
                    "source_url": target_url
                })

            video_variants.sort(key=lambda x: (x["height"], x["bitrate"]), reverse=True)
            if not video_variants:
                raise ValueError("未能提取到有效清晰度视频流！")

            plat_label = override_label or f"🎬 {info.get('extractor_key') or '网络视频'}"
            return {
                "platform": "universal",
                "platform_label": plat_label,
                "media_id": str(info.get('id')),
                "author": uploader,
                "author_id": f"@{uploader_id}" if uploader_id else "",
                "text": title.strip(),
                "date": upload_date,
                "duration": dur_str,
                "thumbnail": thumbnail,
                "variants": video_variants
            }


# Backward compatibility alias
TwitterMediaResolver = UniversalMediaResolver


class QueueTask:
    def __init__(self, task_id: int, repo_id: str, repo_type: str, branch: str, 
                 file_path: str, size_str: str, date_str: str, dest_dir: str, flatten: bool, 
                 endpoint: str, token: Optional[str], proxy: Optional[str] = None, 
                 status: str = "等待中", progress: float = 0.0, total_bytes: Optional[int] = None,
                 platform: str = "hf", direct_url: Optional[str] = None,
                 http_headers: Optional[Dict[str, str]] = None,
                 source_url: Optional[str] = None,
                 format_id: Optional[str] = None):
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
        self.http_headers = http_headers or {}
        self.source_url = source_url
        self.format_id = format_id
        
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
            # If total_bytes is known and local file is truncated (smaller than total_bytes), recover to .downloading for resume
            if self.total_bytes and self.total_bytes > 0 and size < self.total_bytes:
                try:
                    if not os.path.exists(temp_file):
                        os.rename(dest_file, temp_file)
                    else:
                        os.remove(dest_file)
                except Exception:
                    pass
                self.progress = min(99.9, (size / self.total_bytes) * 100.0)
                self.status = "已中断"
                return

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
            "http_headers": self.http_headers,
            "source_url": getattr(self, "source_url", None),
            "format_id": getattr(self, "format_id", None),
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
            http_headers=data.get("http_headers"),
            status=data.get("status", "等待中"),
            progress=data.get("progress", 0.0),
            total_bytes=data.get("total_bytes")
        )
        task.check_local_status()
        return task


class HFDownloaderApp(tk.Tk):
    # ------------------ Centered Modal Dialog Helpers ------------------
    def show_info(self, title: str, msg: str):
        messagebox.showinfo(title, msg, parent=self)

    def show_warning(self, title: str, msg: str):
        messagebox.showwarning(title, msg, parent=self)

    def show_error(self, title: str, msg: str):
        messagebox.showerror(title, msg, parent=self)

    def ask_yes_no(self, title: str, msg: str, **kwargs) -> bool:
        return messagebox.askyesno(title, msg, parent=self, **kwargs)

    def ask_yes_no_cancel(self, title: str, msg: str, **kwargs):
        return messagebox.askyesnocancel(title, msg, parent=self, **kwargs)

    def __init__(self):
        super().__init__()
        self.title("🚀 Hugging Face 批量与断点续传极速下载器 (HF Explorer & Queue Manager)")
        self.minsize(940, 680)

        # Center main window on screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        ww, wh = 1220, 880
        x = max(20, (sw - ww) // 2)
        y = max(20, (sh - wh) // 2)
        self.geometry(f"{ww}x{wh}+{x}+{y}")

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
        self.saved_gh_token = ""
        if os.path.exists(APP_CONFIG_FILE):
            try:
                with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.saved_proxy = data.get("proxy", "")
                    self.saved_token = data.get("token", "")
                    self.saved_gh_token = data.get("gh_token", "")
                    self.saved_tw_url = data.get("tw_url", "")
            except Exception:
                pass

    def _save_settings(self):
        try:
            token_val = self.token_var.get().strip() if hasattr(self, "token_var") else self.saved_token
            gh_token_val = self.gh_token_var.get().strip() if hasattr(self, "gh_token_var") else self.saved_gh_token
            tw_url_val = self.tw_url_var.get().strip() if hasattr(self, "tw_url_var") else getattr(self, "saved_tw_url", "")
            with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "proxy": self._get_effective_proxy() if hasattr(self, "proxy_var") else self.saved_proxy,
                    "token": token_val,
                    "gh_token": gh_token_val,
                    "tw_url": tw_url_val
                }, f, ensure_ascii=False, indent=2)
            if token_val:
                os.environ["HF_TOKEN"] = token_val
            if gh_token_val:
                os.environ["GITHUB_TOKEN"] = gh_token_val
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

    def _toggle_gh_token_visibility(self):
        self.gh_token_show_state = not self.gh_token_show_state
        if self.gh_token_show_state:
            self.gh_token_entry.config(show="")
            self.btn_toggle_gh_token.config(text=" 隐藏", image=self.icons["eye_lock"], compound=tk.LEFT)
        else:
            self.gh_token_entry.config(show="*")
            self.btn_toggle_gh_token.config(text=" 显示", image=self.icons["eye_open"], compound=tk.LEFT)

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
        if hasattr(self, "gh_proxy_combo"):
            self.gh_proxy_combo["values"] = self.proxies_list
        if hasattr(self, "tw_proxy_combo"):
            self.tw_proxy_combo["values"] = self.proxies_list
        if selected:
            self.proxy_var.set(selected)
        elif self.proxy_var.get() not in self.proxies_list and self.proxies_list:
            self.proxy_var.set(self.proxies_list[0])
        self._save_settings()
        self.log(f"[✓] 网络代理列表已更新并永久保存 (当前共有 {len(self.proxies_list)} 个配置项)。")

    # ------------------ Preset Directories Management ------------------
    def open_preset_manager(self):
        PresetDirectoryManagerDialog(self, on_update_callback=self._on_presets_updated)

    def _on_presets_updated(self, new_presets: Dict[str, str], selected_label: Optional[str] = None):
        global PRESET_DIRS_MAP
        PRESET_DIRS_MAP = new_presets
        labels = list(new_presets.keys())
        self.preset_labels = labels
        
        # 1. Update Tab 1 (Hugging Face)
        if hasattr(self, "preset_combo"):
            self.preset_combo.configure(values=labels)
            ComboboxItemToolTip(self.preset_combo, PRESET_DIRS_MAP)
            if selected_label and selected_label in new_presets:
                self.preset_var.set(selected_label)
                self.dest_dir_var.set(new_presets[selected_label])
            elif self.preset_var.get() not in new_presets and labels:
                self.preset_var.set(labels[0])
                self.dest_dir_var.set(new_presets[labels[0]])
            elif self.preset_var.get() in new_presets:
                self.dest_dir_var.set(new_presets[self.preset_var.get()])

        # 2. Update Tab 2 (GitHub)
        if hasattr(self, "gh_preset_combo"):
            self.gh_preset_combo.configure(values=labels)
            ComboboxItemToolTip(self.gh_preset_combo, PRESET_DIRS_MAP)
            if selected_label and selected_label in new_presets:
                self.gh_preset_var.set(selected_label)
                self._on_gh_preset_changed()
            elif self.gh_preset_var.get() not in new_presets and labels:
                self.gh_preset_var.set(labels[0])
                self._on_gh_preset_changed()
            elif self.gh_preset_var.get() in new_presets:
                self._on_gh_preset_changed()

        # 3. Update Tab 3 (Twitter)
        if hasattr(self, "tw_preset_combo"):
            self.tw_preset_combo.configure(values=labels)
            if selected_label and selected_label in new_presets:
                self.tw_preset_var.set(selected_label)
                self.tw_dest_path_var.set(new_presets[selected_label])
            elif self.tw_preset_var.get() not in new_presets and labels:
                self.tw_preset_var.set(labels[0])
                self.tw_dest_path_var.set(new_presets[labels[0]])
            elif self.tw_preset_var.get() in new_presets:
                self.tw_dest_path_var.set(new_presets[self.tw_preset_var.get()])

        # 4. Update Tab 5 (Environment Setup)
        if hasattr(self, "tree_tab_dirs"):
            self._refresh_tab_env_dirs()

        self.update_idletasks()
        self.log(f"[✓] 预设分类目录已实时更新 (当前共有 {len(new_presets)} 个预设路径)。")

    # ------------------ History & Starred Bookmarks Management ------------------
    def open_history_dialog(self, default_platform: Optional[str] = None):
        HistoryManagerDialog(self, on_load_callback=self._load_repo_from_history, default_platform=default_platform)

    def _load_repo_from_history(self, platform: str, repo_id: str, repo_type: str = "model", branch: str = "main"):
        if platform == "github":
            self.notebook.select(1)
            self.gh_repo_var.set(repo_id)
            if branch:
                self.gh_branch_var.set(branch)
            self._on_gh_preset_changed()
            self.start_fetch_github()
        elif platform == "twitter":
            self.notebook.select(2)
            if "status/" in repo_id or repo_id.isdigit():
                self.tw_url_var.set(repo_id if repo_id.startswith("http") else f"https://x.com/i/status/{repo_id}")
            else:
                self.tw_url_var.set(repo_id)
            self.start_resolve_twitter()
        else:
            self.notebook.select(0)
            self.repo_id_var.set(repo_id)
            self.repo_type_var.set(repo_type or "model")
            if branch:
                self.branch_var.set(branch)
            self._on_repo_type_changed()
            self.start_fetch_files()

    def _refresh_history_comboboxes(self):
        if hasattr(self, "repo_combo"):
            self.repo_combo["values"] = HistoryManager.get_recent_repos("huggingface")
        if hasattr(self, "gh_repo_combo"):
            self.gh_repo_combo["values"] = HistoryManager.get_recent_repos("github")
        if hasattr(self, "tw_url_combo"):
            self.tw_url_combo["values"] = HistoryManager.get_recent_repos("twitter")

    def open_env_setup(self):
        self.notebook.select(4)
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
                    self.after(0, lambda: messagebox.showinfo("连接成功", msg, parent=self))
                    self.after(0, lambda: self.log(f"[✓] 连通性测试通过! 延迟: {cost:.0f} ms"))
                    self.after(0, lambda: self.lbl_status.config(text=f"状态: 网络连通正常 ({cost:.0f} ms)", foreground="green"))
                else:
                    msg = f"连接返回异常状态码: {resp.status_code}\n• 目标: {endpoint}\n• 代理: {proxy or '直连'}"
                    self.after(0, lambda: messagebox.showwarning("连接警告", msg, parent=self))
                    self.after(0, lambda: self.log(f"[!] 连通性测试警告: HTTP {resp.status_code}"))
            except Exception as e:
                msg = f"无法通过当前配置连接到目标站点:\n\n• 目标: {endpoint}\n• 代理: {proxy or '直连'}\n• 错误详情: {str(e)}\n\n建议检查代理客户端是否开启 (如 Clash/v2rayN) 或切换镜像源！"
                self.after(0, lambda: messagebox.showerror("连接失败", msg, parent=self))
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

        # Tab 3: Universal Video Downloader
        self.tab_twitter = ttk.Frame(self.notebook, padding="6")
        self.notebook.add(self.tab_twitter, text=" 🎬 视频解析下载 ")

        # Tab 4: Download Queue
        self.tab_queue = ttk.Frame(self.notebook, padding="6")
        self.notebook.add(self.tab_queue, text=" 📑 统一下载队列 (0) ")

        # Tab 5: Environment Setup & Directory Manager
        self.tab_env = ttk.Frame(self.notebook, padding="6")
        self.notebook.add(self.tab_env, text=" 🛠️ 一键部署环境 ")

        self._build_tab_browse()
        self._build_tab_github()
        self._build_tab_twitter()
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

        # Row 0: Repo ID, Type, Branch, Fetch button, History button
        ttk.Label(config_frame, text="HF 仓库 (Repo ID):").grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        self.repo_id_var = tk.StringVar(value="Kijai/MiniMax-H3-experimental")
        self.repo_combo = ttk.Combobox(config_frame, textvariable=self.repo_id_var, values=HistoryManager.get_recent_repos("huggingface"), width=30, font=FONT_NORMAL)
        self.repo_combo.grid(row=0, column=1, sticky=tk.EW, padx=4, pady=3)

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

        btn_hf_hist = ttk.Button(config_frame, text=" 历史/收藏...", image=self.icons["clock"], compound=tk.LEFT, command=lambda: self.open_history_dialog("huggingface"))
        btn_hf_hist.grid(row=0, column=7, padx=4, pady=3)

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
            width=29,
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

        btn_manage_preset = ttk.Button(dest_frame, text=" ⚙️ 管理预设...", image=self.icons["shield"], compound=tk.LEFT, command=self.open_preset_manager)
        btn_manage_preset.grid(row=0, column=5, padx=4, pady=3)

        self.flatten_var = tk.BooleanVar(value=True)
        flatten_chk = ttk.Checkbutton(
            dest_frame, 
            text="扁平化保存", 
            variable=self.flatten_var
        )
        flatten_chk.grid(row=0, column=6, sticky=tk.W, padx=(6, 4), pady=3)
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

        # Row 0: Repo ID, Mode (Release/SourceTree), Branch/Tag, Fetch Button, History Button
        ttk.Label(config_frame, text="GitHub 仓库 (owner/repo):").grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        self.gh_repo_var = tk.StringVar(value="comfyanonymous/ComfyUI")
        self.gh_repo_combo = ttk.Combobox(config_frame, textvariable=self.gh_repo_var, values=HistoryManager.get_recent_repos("github"), width=28, font=FONT_NORMAL)
        self.gh_repo_combo.grid(row=0, column=1, sticky=tk.EW, padx=4, pady=3)

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

        btn_gh_hist = ttk.Button(config_frame, text=" 历史/收藏...", image=self.icons["clock"], compound=tk.LEFT, command=lambda: self.open_history_dialog("github"))
        btn_gh_hist.grid(row=0, column=7, padx=4, pady=3)

        # Row 1: Accelerator Mirror with Test Button & GitHub Token with Focus Save
        ttk.Label(config_frame, text="国内加速节点:").grid(row=1, column=0, sticky=tk.W, padx=4, pady=3)
        
        mirror_gh_subframe = ttk.Frame(config_frame)
        mirror_gh_subframe.grid(row=1, column=1, sticky=tk.EW, padx=4, pady=3)

        self.gh_mirror_var = tk.StringVar(value=DEFAULT_GITHUB_ACCELERATORS[0])
        gh_mirror_combo = ttk.Combobox(mirror_gh_subframe, textvariable=self.gh_mirror_var, values=DEFAULT_GITHUB_ACCELERATORS, font=FONT_NORMAL)
        gh_mirror_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_test_gh_node = ttk.Button(mirror_gh_subframe, text=" 检测加速节点", image=self.icons["bolt"], compound=tk.LEFT, width=13, command=self.test_github_accelerator)
        btn_test_gh_node.pack(side=tk.RIGHT, padx=(4, 0))

        ttk.Label(config_frame, text="GitHub Token:").grid(row=1, column=2, sticky=tk.W, padx=4, pady=3)
        
        gh_token_subframe = ttk.Frame(config_frame)
        gh_token_subframe.grid(row=1, column=3, columnspan=5, sticky=tk.EW, padx=4, pady=3)

        self.gh_token_var = tk.StringVar(value=self.saved_gh_token)
        self.gh_token_show_state = False
        self.gh_token_entry = ttk.Entry(gh_token_subframe, textvariable=self.gh_token_var, show="*", font=FONT_NORMAL)
        self.gh_token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.gh_token_entry.bind("<FocusOut>", lambda e: self._save_settings())
        self.gh_token_entry.bind("<KeyRelease>", lambda e: self._save_settings())

        self.btn_toggle_gh_token = ttk.Button(gh_token_subframe, text=" 显示", image=self.icons["eye_open"], compound=tk.LEFT, width=7, command=self._toggle_gh_token_visibility)
        self.btn_toggle_gh_token.pack(side=tk.RIGHT, padx=(4, 0))

        ToolTip(self.gh_token_entry, "可选。当遇到 GitHub API 速率限制 (Rate Limit) 时，可在此填入个人 GitHub Personal Access Token 提升配额，输入后自动永久保存")

        # Row 2: Proxy settings & management (Identical to Hugging Face)
        ttk.Label(config_frame, text="网络代理 (Proxy):").grid(row=2, column=0, sticky=tk.W, padx=4, pady=3)

        proxy_gh_subframe = ttk.Frame(config_frame)
        proxy_gh_subframe.grid(row=2, column=1, sticky=tk.EW, padx=4, pady=3)

        self.gh_proxy_combo = ttk.Combobox(proxy_gh_subframe, textvariable=self.proxy_var, values=self.proxies_list, font=FONT_NORMAL)
        self.gh_proxy_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.gh_proxy_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())
        self.gh_proxy_combo.bind("<FocusOut>", lambda e: self._save_settings())

        btn_gh_manage_proxy = ttk.Button(proxy_gh_subframe, text=" 增删管理代理...", image=self.icons["shield"], compound=tk.LEFT, width=14, command=self.open_proxy_manager)
        btn_gh_manage_proxy.pack(side=tk.RIGHT, padx=(4, 0))

        btn_gh_test_proxy = ttk.Button(proxy_gh_subframe, text=" 检测连通性", image=self.icons["bolt"], compound=tk.LEFT, width=12, command=self.test_proxy_connectivity)
        btn_gh_test_proxy.pack(side=tk.RIGHT, padx=(4, 0))

        config_frame.columnconfigure(1, weight=1)

        # Target Directory Frame (Separate Panel identical to Hugging Face)
        gh_dest_frame = ttk.LabelFrame(
            pane_upper, 
            text=" 💾 当前文件的保存目标目录 (默认开启扁平化保存：直接存入目标目录，不生成多层嵌套子文件夹) ", 
            padding="6"
        )
        gh_dest_frame.pack(fill=tk.X, pady=(0, 2))

        ttk.Label(gh_dest_frame, text="常用预设分类:").grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        
        preset_names = list(PRESET_DIRS_MAP.keys())
        self.gh_preset_var = tk.StringVar(value=preset_names[0])
        self.gh_preset_combo = ttk.Combobox(
            gh_dest_frame, 
            textvariable=self.gh_preset_var, 
            values=preset_names, 
            state="readonly", 
            width=29, 
            font=FONT_BOLD
        )
        self.gh_preset_combo.grid(row=0, column=1, sticky=tk.W, padx=4, pady=3)
        self.gh_preset_combo.bind("<<ComboboxSelected>>", self._on_gh_preset_changed)
        ComboboxItemToolTip(self.gh_preset_combo, PRESET_DIRS_MAP)

        ttk.Label(gh_dest_frame, text="完整路径:").grid(row=0, column=2, sticky=tk.W, padx=(8, 4), pady=3)
        
        self.gh_dest_path_var = tk.StringVar(value=DEFAULT_CUSTOM_NODES_DIR)
        gh_dest_entry = ttk.Entry(gh_dest_frame, textvariable=self.gh_dest_path_var, font=FONT_NORMAL)
        gh_dest_entry.grid(row=0, column=3, sticky=tk.EW, padx=4, pady=3)
        ToolTip(gh_dest_entry, lambda: f"目标保存目录完整绝对路径:\n{self.gh_dest_path_var.get()}")

        btn_browse_gh_dest = ttk.Button(gh_dest_frame, text=" 浏览更改...", image=self.icons["folder"], compound=tk.LEFT, command=self._browse_gh_dest)
        btn_browse_gh_dest.grid(row=0, column=4, padx=4, pady=3)

        btn_manage_gh_preset = ttk.Button(gh_dest_frame, text=" ⚙️ 管理预设...", image=self.icons["shield"], compound=tk.LEFT, command=self.open_preset_manager)
        btn_manage_gh_preset.grid(row=0, column=5, padx=4, pady=3)

        self.gh_flatten_var = tk.BooleanVar(value=True)
        cb_gh_flatten = ttk.Checkbutton(
            gh_dest_frame, 
            text="扁平化保存", 
            variable=self.gh_flatten_var
        )
        cb_gh_flatten.grid(row=0, column=6, sticky=tk.W, padx=(6, 4), pady=3)
        ToolTip(cb_gh_flatten, "勾选后将文件直接保存到目标目录，不创建多层子文件夹")

        gh_dest_frame.columnconfigure(3, weight=1)

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
            gh_act_frame, text=" 下载整包源码 Zip (含加速)", image=self.icons["rocket"], compound=tk.LEFT,
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
                    self.after(0, lambda: messagebox.showinfo("测试成功", f"GitHub 加速节点连通正常！\n节点: {node}\n响应延迟: {latency} ms", parent=self))
                    self.after(0, lambda: self.log(f"[✓] GitHub 加速节点测试成功: 延迟 {latency} ms"))
                    self.after(0, lambda: self.lbl_status.config(text=f"状态: GitHub 节点正常 ({latency} ms)", foreground="green"))
                else:
                    self.after(0, lambda: messagebox.showwarning("提示", f"节点返回状态码: HTTP {resp.status_code}\n建议更换其他加速源。", parent=self))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("连接失败", f"节点连接超时/失败:\n{str(e, parent=self)}"))
                self.after(0, lambda: self.log(f"[✗] GitHub 节点连接失败: {str(e)}"))
                self.after(0, lambda: self.lbl_status.config(text="状态: GitHub 节点连接失败", foreground="red"))

        threading.Thread(target=_worker, daemon=True).start()

    def start_fetch_github(self):
        raw_input = self.gh_repo_var.get().strip()
        # Clean URL if user pasted full github URL
        clean_repo = raw_input
        if "github.com/" in clean_repo:
            clean_repo = clean_repo.split("github.com/")[-1].split(".git")[0].strip("/")
        elif clean_repo.endswith(".git"):
            clean_repo = clean_repo[:-4]
        
        if not clean_repo or "/" not in clean_repo:
            messagebox.showwarning("提示", "请输入有效的 GitHub 仓库名或链接 (例如: sepiablue-ai/minimax_h3_workflows, parent=self)！")
            return

        self.gh_repo_var.set(clean_repo)
        self._on_gh_preset_changed()
        self.btn_gh_fetch.config(state=tk.DISABLED)
        self.lbl_status.config(text=f"状态: 正在智能分析 GitHub [{clean_repo}] 仓库与分支...", foreground="blue")
        self.log(f"\n[*] 正在连接 GitHub API 查询仓库 '{clean_repo}'...")

        mode = self.gh_mode_var.get().strip()
        branch_input = self.gh_branch_var.get().strip()
        token = self.gh_token_var.get().strip() or None
        proxies = self._get_request_proxies()

        threading.Thread(target=self._fetch_github_worker, args=(clean_repo, mode, branch_input, token, proxies), daemon=True).start()

    def _fetch_github_worker(self, repo_id: str, mode: str, branch_input: str, token: Optional[str], proxies: Optional[dict]):

        headers = {"User-Agent": "HF-Downloader-GUI/1.0", "Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        def _gh_api_get(url: str, timeout: int = 15, retries: int = 2) -> Tuple[Optional[requests.Response], Optional[str]]:
            last_err = None
            for attempt in range(retries + 1):
                try:
                    resp = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
                    return resp, None
                except requests.exceptions.Timeout:
                    last_err = f"连接 GitHub API 超时 (Read timed out, 超时设置 {timeout}s)"
                    if attempt < retries:
                        time.sleep(1)
                except requests.exceptions.ConnectionError as ce:
                    last_err = f"网络连接失败 (无法连接 api.github.com): {str(ce)}"
                    if attempt < retries:
                        time.sleep(1)
                except Exception as e:
                    last_err = str(e)
                    break
            return None, last_err

        items_map = {}
        nav_structure = {}
        err_msg = None
        actual_branch = branch_input or "main"
        repo_pushed_date = "--"

        # 1. Fetch Repository Metadata to get actual default_branch & real push date
        repo_api_url = f"https://api.github.com/repos/{repo_id}"
        r_info, r_err = _gh_api_get(repo_api_url, timeout=12, retries=1)
        if r_info is not None:
            if r_info.status_code == 200:
                repo_info = r_info.json()
                default_b = repo_info.get("default_branch") or "main"
                if not branch_input or branch_input in ("main", "master"):
                    actual_branch = default_b
                    self.after(0, lambda b=actual_branch: self.gh_branch_var.set(b))
                raw_pushed = repo_info.get("pushed_at") or repo_info.get("updated_at")
                if raw_pushed:
                    repo_pushed_date = raw_pushed[:16].replace("T", " ")
            elif r_info.status_code == 404:
                err_msg = "未找到该 GitHub 仓库，请核对 owner/repo 拼写或确认是否为私有仓库。"
            elif r_info.status_code == 403:
                err_msg = "GitHub API 调用频率已达上限 (403 Rate Limit)，请在上方输入 GitHub Token 即可大幅提升请求配额！"
            else:
                err_msg = f"HTTP {r_info.status_code}: {r_info.text[:120]}"
        elif r_err:
            # If rate limited or connection failed, provide clear advice
            err_msg = f"{r_err}\n\n💡 解决建议:\n1. 请在上方【网络代理】处选择本地代理 (如 127.0.0.1:7890 / 10809)；\n2. 如遇官方速率限制，可在上方输入 GitHub Token。"

        def _get_branch_commit_date(target_b: str) -> str:
            commit_api_url = f"https://api.github.com/repos/{repo_id}/commits/{target_b}"
            c_resp, _ = _gh_api_get(commit_api_url, timeout=8, retries=1)
            if c_resp is not None and c_resp.status_code == 200:
                c_data = c_resp.json()
                commit_obj = c_data.get("commit", {})
                dt_str = commit_obj.get("committer", {}).get("date") or commit_obj.get("author", {}).get("date")
                if dt_str:
                    return dt_str[:16].replace("T", " ")
            return repo_pushed_date if repo_pushed_date != "--" else datetime.now().strftime("%Y-%m-%d %H:%M")

        if not err_msg:
            # 2. Release Mode or Fallback
            if "Release" in mode:
                api_url = f"https://api.github.com/repos/{repo_id}/releases"
                resp, rel_err = _gh_api_get(api_url, timeout=15, retries=2)
                if resp is not None:
                    if resp.status_code == 200:
                        releases = resp.json()
                        if releases:
                            for rel in releases:
                                tag_name = rel.get("tag_name", "未知Tag")
                                rel_name = rel.get("name") or tag_name
                                pub_date = (rel.get("published_at") or rel.get("created_at") or repo_pushed_date)[:16].replace("T", " ")
                                
                                nav_structure[tag_name] = f"📦 {tag_name} ({pub_date})"
                                
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
                                    adate = (asset.get("updated_at") or asset.get("created_at") or pub_date)[:16].replace("T", " ")
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
                        else:
                            # Auto fallback to source tree mode
                            self.log(f"[i] 该仓库未发布 Release，自动为您切换为【源码目录树】模式拉取分支 '{actual_branch}'...")
                            self.after(0, lambda: self.gh_mode_var.set("🌲 源码目录树"))
                            mode = "🌲 源码目录树"
                    elif resp.status_code == 404:
                        err_msg = "未找到该仓库，请检查 owner/repo 拼写。"
                    elif resp.status_code == 403:
                        err_msg = "GitHub API 调用频率受限，建议填入 GitHub Token！"
                    else:
                        err_msg = f"HTTP {resp.status_code}: {resp.text[:120]}"
                elif rel_err:
                    err_msg = rel_err

            # 3. Source Tree Mode (or fallen back from Release)
            if "源码" in mode and not items_map and not err_msg:
                api_url = f"https://api.github.com/repos/{repo_id}/git/trees/{actual_branch}?recursive=1"
                resp, tree_err = _gh_api_get(api_url, timeout=18, retries=2)
                if resp is not None:
                    if resp.status_code == 200:
                        data = resp.json()
                        tree = data.get("tree", [])
                        nav_structure["ROOT"] = "📁 全部源码 (根目录 /)"
                        branch_real_date = _get_branch_commit_date(actual_branch)

                        for item in tree:
                            itype = item.get("type")
                            ipath = item.get("path")
                            if itype == "tree":
                                nav_structure[ipath] = f"📁 {ipath}"
                            elif itype == "blob":
                                isize = item.get("size") or 0
                                raw_url = f"https://raw.githubusercontent.com/{repo_id}/{actual_branch}/{ipath}"
                                scope = os.path.dirname(ipath) if "/" in ipath else "ROOT"
                                items_map[ipath] = {
                                    "name": ipath,
                                    "scope": scope,
                                    "size_str": self._format_size(isize),
                                    "raw_size": isize,
                                    "date_str": branch_real_date,
                                    "downloads": "--",
                                    "url": raw_url
                                }
                    elif resp.status_code == 404:
                        # Try alternate branch (master <-> main)
                        alt_branch = "master" if actual_branch == "main" else "main"
                        alt_url = f"https://api.github.com/repos/{repo_id}/git/trees/{alt_branch}?recursive=1"
                        alt_resp, _ = _gh_api_get(alt_url, timeout=15, retries=1)
                        if alt_resp is not None and alt_resp.status_code == 200:
                            data = alt_resp.json()
                            tree = data.get("tree", [])
                            nav_structure["ROOT"] = "📁 全部源码 (根目录 /)"
                            self.after(0, lambda b=alt_branch: self.gh_branch_var.set(b))
                            alt_branch_date = _get_branch_commit_date(alt_branch)

                            for item in tree:
                                itype = item.get("type")
                                ipath = item.get("path")
                                if itype == "tree":
                                    nav_structure[ipath] = f"📁 {ipath}"
                                elif itype == "blob":
                                    isize = item.get("size") or 0
                                    raw_url = f"https://raw.githubusercontent.com/{repo_id}/{alt_branch}/{ipath}"
                                    scope = os.path.dirname(ipath) if "/" in ipath else "ROOT"
                                    items_map[ipath] = {
                                        "name": ipath,
                                        "scope": scope,
                                        "size_str": self._format_size(isize),
                                        "raw_size": isize,
                                        "date_str": alt_branch_date,
                                        "downloads": "--",
                                        "url": raw_url
                                    }
                        else:
                            err_msg = f"未找到仓库或分支 '{actual_branch}'，请核对分支名称。"
                    elif resp.status_code == 403:
                        err_msg = "GitHub API 调用频率已达上限 (403 Rate Limit)，请在上方输入 GitHub Token！"
                    else:
                        err_msg = f"HTTP {resp.status_code}: {resp.text[:120]}"
                elif tree_err:
                    err_msg = tree_err

        if items_map:
            self.raw_gh_items = items_map
            self.gh_nav_structure = nav_structure
            self.checked_gh_items.clear()
            HistoryManager.record_access(repo_id, "github", "github", actual_branch, len(items_map))
            self.after(0, self._refresh_history_comboboxes)
            self.after(0, self._populate_github_browser)
            self.after(0, lambda: self.log(f"[✓] 成功获取 GitHub {len(items_map)} 项资源。"))
            self.after(0, lambda: self.lbl_status.config(text=f"状态: 共检索到 {len(items_map)} 项 GitHub 资源", foreground="green"))
        else:
            self.after(0, lambda: self.log(f"[✗] 获取 GitHub 资源失败: {err_msg}"))
            self.after(0, lambda: self.lbl_status.config(text="状态: 获取 GitHub 资源失败", foreground="red"))
            self.after(0, lambda: messagebox.showerror("获取失败", f"无法获取 GitHub 资源:\n{err_msg}\n\n💡 提示:\n1. 若网络连接超时，请在上方【网络代理】下拉框中选择您正在运行的代理 (如 127.0.0.1:7890)；\n2. 如遇 API 速率限制，可在上方输入 GitHub Token (无需权限的公开 Token 即可提高至 5000 次/小时)。", parent=self))

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

    def _get_next_task_id(self) -> int:
        if self.tasks:
            tid = max(t.task_id for t in self.tasks) + 1
        else:
            tid = self.task_counter
        self.task_counter = tid + 1
        return tid

    def _resolve_github_dest_dir(self, base_dest: str, repo_id: str) -> str:
        """
        Ensures downloaded files or zips are neatly encapsulated in a dedicated subfolder
        (e.g., custom_nodes/minimax_h3_workflows) rather than scattered loose in parent folder.
        """
        clean_repo = repo_id.replace("🐙", "").strip()
        repo_name = clean_repo.split("/")[-1]
        norm_dest = os.path.normpath(base_dest)
        last_dir = os.path.basename(norm_dest)
        
        # If the destination does not already end with repo_name, auto-append repo subfolder
        if last_dir.lower() != repo_name.lower():
            return os.path.join(norm_dest, repo_name)
        return norm_dest

    def add_github_to_queue(self, jump: bool = False):
        target_keys = list(self.checked_gh_items)
        if not target_keys:
            sel_iids = self.tree_gh_files.selection()
            if sel_iids:
                target_keys = list(sel_iids)

        if not target_keys:
            messagebox.showwarning("提示", "请先在右侧列表中勾选或鼠标选择需要下载的 GitHub 文件或资源！", parent=self)
            return

        raw_dest_dir = self.gh_dest_path_var.get().strip()
        if not raw_dest_dir:
            messagebox.showwarning("提示", "请指定保存目标路径！", parent=self)
            return

        repo_id = self.gh_repo_var.get().strip()
        dest_dir = self._resolve_github_dest_dir(raw_dest_dir, repo_id)
        os.makedirs(dest_dir, exist_ok=True)
        
        token = self.gh_token_var.get().strip() or None
        proxy = self._get_effective_proxy()
        flatten = self.gh_flatten_var.get()

        added_cnt = 0
        for key in target_keys:
            item = self.raw_gh_items.get(key)
            if not item:
                continue

            raw_url = item["url"]
            accel_url = self._get_accelerated_url(raw_url)
            fname = os.path.basename(item["name"])

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
            task.check_local_status()
            self.tasks.append(task)
            added_cnt += 1

        self._save_tasks()
        self.rescan_all_tasks(silent=True)
        self._refresh_queue_tree()
        self.log(f"[✓] 成功将 {added_cnt} 个 GitHub 资源加入统一下载队列！(专属目标目录: {dest_dir})")
        messagebox.showinfo("入队成功", f"成功将 {added_cnt} 个 GitHub 资源加入统一下载队列！\n所有文件将集中保存在独立目录:\n{dest_dir}", parent=self)

        if jump or True:
            self.notebook.select(3)

    def download_github_repo_zip(self):
        repo_id = self.gh_repo_var.get().strip()
        if not repo_id or "/" not in repo_id:
            messagebox.showwarning("提示", "请输入有效的 GitHub 仓库名！", parent=self)
            return

        branch = self.gh_branch_var.get().strip() or "main"
        raw_dest_dir = self.gh_dest_path_var.get().strip()
        if not raw_dest_dir:
            messagebox.showwarning("提示", "请指定保存目标路径！", parent=self)
            return

        dest_dir = self._resolve_github_dest_dir(raw_dest_dir, repo_id)
        os.makedirs(dest_dir, exist_ok=True)

        repo_name = repo_id.split("/")[-1]
        zip_name = f"{repo_name}-{branch}.zip"
        raw_url = f"https://github.com/{repo_id}/archive/refs/heads/{branch}.zip"
        accel_url = self._get_accelerated_url(raw_url)

        task_id = self._get_next_task_id()
        real_zip_date = ""
        if hasattr(self, "raw_gh_items") and self.raw_gh_items:
            for it in self.raw_gh_items.values():
                d = it.get("date_str")
                if d and d not in ("最新", "--"):
                    real_zip_date = d
                    break
        if not real_zip_date:
            real_zip_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        task = QueueTask(
            task_id=task_id,
            repo_id=f"🐙 {repo_id}",
            repo_type="github_zip",
            branch=branch,
            file_path=zip_name,
            size_str="整包源码Zip",
            date_str=real_zip_date,
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
        task.check_local_status()
        self.tasks.append(task)
        self._save_tasks()
        self.log(f"[✓] 已添加 GitHub 仓库整包源码 Zip 任务: {zip_name} (下载后将自动解压并收纳在: {dest_dir})")
        messagebox.showinfo("入队成功", f"已将 GitHub 整包源码 Zip 任务加入队列:\n{zip_name}\n保存与解压目标目录: {dest_dir}", parent=self)
        self.notebook.select(3)

    # ------------------ Tab 3: Universal Media Video Downloader UI & Handlers ------------------
    def _build_tab_twitter(self):
        self.tw_paned_v = ttk.PanedWindow(self.tab_twitter, orient=tk.VERTICAL)
        self.tw_paned_v.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Upper Area: Config Panel & Media Summary Card
        tw_upper = ttk.Frame(self.tw_paned_v)
        self.tw_paned_v.add(tw_upper, weight=1)

        # Panel 1: Media Configuration
        tw_config_frame = ttk.LabelFrame(tw_upper, text=" 🎬 多平台视频解析与网络加速配置 (B站 / 微信公众号 / 视频号 / Twitter / 全网) ", padding="6")
        tw_config_frame.pack(fill=tk.X, pady=(0, 4))

        # Row 0: Media URL, Paste button, Parse button, History button
        ttk.Label(tw_config_frame, text="视频/推文/文章链接:").grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        
        url_box = ttk.Frame(tw_config_frame)
        url_box.grid(row=0, column=1, sticky=tk.EW, padx=4, pady=3)

        self.tw_url_var = tk.StringVar(value=getattr(self, "saved_tw_url", ""))
        self.tw_url_combo = ttk.Combobox(url_box, textvariable=self.tw_url_var, values=HistoryManager.get_recent_repos("twitter"), font=FONT_NORMAL)
        self.tw_url_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.tw_url_combo.bind("<FocusOut>", lambda e: self._save_settings())
        self.tw_url_combo.bind("<Return>", lambda e: self.start_resolve_twitter())
        self.tw_url_combo.bind("<<ComboboxSelected>>", lambda e: self.start_resolve_twitter())

        btn_paste = ttk.Button(url_box, text=" 粘贴", image=self.icons["bolt"], compound=tk.LEFT, width=7, command=self._paste_twitter_url)
        btn_paste.pack(side=tk.RIGHT, padx=(4, 0))

        self.btn_tw_fetch = ttk.Button(tw_config_frame, text=" ⚡ 开始解析视频", image=self.icons["search"], compound=tk.LEFT, command=self.start_resolve_twitter)
        self.btn_tw_fetch.grid(row=0, column=2, padx=4, pady=3)

        btn_tw_hist = ttk.Button(tw_config_frame, text=" 历史/收藏...", image=self.icons["clock"], compound=tk.LEFT, command=lambda: self.open_history_dialog("twitter"))
        btn_tw_hist.grid(row=0, column=3, padx=4, pady=3)

        ToolTip(self.tw_url_combo, "输入 Twitter/X 推文、B站视频链接 (BV/AV/b23.tv)、微信公众号文章链接、微信视频号或 YouTube/TikTok 等全网 1000+ 视频链接")

        # Row 1: Proxy Settings
        ttk.Label(tw_config_frame, text="网络代理 (Proxy):").grid(row=1, column=0, sticky=tk.W, padx=4, pady=3)

        tw_proxy_subframe = ttk.Frame(tw_config_frame)
        tw_proxy_subframe.grid(row=1, column=1, sticky=tk.EW, padx=4, pady=3)

        self.tw_proxy_combo = ttk.Combobox(tw_proxy_subframe, textvariable=self.proxy_var, values=self.proxies_list, state="readonly", font=FONT_NORMAL)
        self.tw_proxy_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.tw_proxy_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())

        btn_tw_manage_proxy = ttk.Button(tw_proxy_subframe, text=" 增删管理代理...", image=self.icons["shield"], compound=tk.LEFT, width=14, command=self.open_proxy_manager)
        btn_tw_manage_proxy.pack(side=tk.RIGHT, padx=(4, 0))

        btn_tw_test_proxy = ttk.Button(tw_config_frame, text=" ⚡ 检测连通性", image=self.icons["bolt"], compound=tk.LEFT, command=self.test_proxy_connectivity)
        btn_tw_test_proxy.grid(row=1, column=2, padx=4, pady=3)

        tw_config_frame.columnconfigure(1, weight=1)

        # Panel 2: Save Destination
        tw_dest_frame = ttk.LabelFrame(tw_upper, text=" 💾 视频保存目标目录 ", padding="6")
        tw_dest_frame.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(tw_dest_frame, text="常用预设分类:").grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        tw_preset_names = list(PRESET_DIRS_MAP.keys())
        self.tw_preset_var = tk.StringVar(value=tw_preset_names[0])
        self.tw_preset_combo = ttk.Combobox(
            tw_dest_frame, 
            textvariable=self.tw_preset_var, 
            values=tw_preset_names, 
            state="readonly", 
            width=29, 
            font=FONT_BOLD
        )
        self.tw_preset_combo.grid(row=0, column=1, sticky=tk.W, padx=4, pady=3)
        self.tw_preset_combo.bind("<<ComboboxSelected>>", self._on_tw_preset_changed)

        ttk.Label(tw_dest_frame, text="完整路径:").grid(row=0, column=2, sticky=tk.W, padx=4, pady=3)
        self.tw_dest_path_var = tk.StringVar(value=PRESET_DIRS_MAP[tw_preset_names[0]])
        self.tw_dest_entry = ttk.Entry(tw_dest_frame, textvariable=self.tw_dest_path_var, font=FONT_NORMAL)
        self.tw_dest_entry.grid(row=0, column=3, sticky=tk.EW, padx=4, pady=3)

        btn_tw_browse = ttk.Button(tw_dest_frame, text=" 浏览更改...", image=self.icons["folder"], compound=tk.LEFT, command=self.browse_tw_dest_path)
        btn_tw_browse.grid(row=0, column=4, padx=4, pady=3)

        btn_manage_tw_preset = ttk.Button(tw_dest_frame, text=" ⚙️ 管理预设...", image=self.icons["shield"], compound=tk.LEFT, command=self.open_preset_manager)
        btn_manage_tw_preset.grid(row=0, column=5, padx=4, pady=3)

        tw_dest_frame.columnconfigure(3, weight=1)

        # Panel 3: Video Meta Summary Card with Embedded Thumbnail Card
        self.tw_meta_frame = ttk.LabelFrame(tw_upper, text=" 📝 视频/推文/文章信息摘要 (包含高清封面与在线预览) ", padding="6")
        self.tw_meta_frame.pack(fill=tk.X, pady=(0, 4))

        meta_container = ttk.Frame(self.tw_meta_frame)
        meta_container.pack(fill=tk.X, expand=True)

        meta_left = ttk.Frame(meta_container)
        meta_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.lbl_tw_author = ttk.Label(meta_left, text="平台与作者: --", font=FONT_BOLD, foreground="#0d6efd")
        self.lbl_tw_author.pack(anchor=tk.W, pady=(0, 2))

        self.lbl_tw_date = ttk.Label(meta_left, text="发布日期: -- | 视频时长: --", font=FONT_SMALL, foreground="#555555")
        self.lbl_tw_date.pack(anchor=tk.W, pady=(0, 2))

        self.lbl_tw_text = ttk.Label(meta_left, text="内容标题: (请在上方面板输入视频/推文/文章链接并点击【开始解析视频】)", font=FONT_NORMAL, wraplength=760, justify=tk.LEFT)
        self.lbl_tw_text.pack(anchor=tk.W)

        # Right: Video Thumbnail Card
        meta_right = ttk.LabelFrame(meta_container, text=" 🖼️ 视频封面 ", padding="2")
        meta_right.pack(side=tk.RIGHT, padx=2)

        self.lbl_tw_thumb = ttk.Label(
            meta_right, 
            text=" 📹 视频封面 \n(解析后显示)", 
            justify=tk.CENTER, 
            anchor=tk.CENTER, 
            width=18, 
            font=FONT_SMALL, 
            cursor="hand2"
        )
        self.lbl_tw_thumb.pack(padx=4, pady=4)
        self.lbl_tw_thumb.bind("<Button-1>", lambda e: self.preview_twitter_video())
        ToolTip(self.lbl_tw_thumb, "点击放大查看高清视频封面并可在线预览播放")

        # Lower Area: Video Quality Variants Table & Operations
        tw_lower = ttk.Frame(self.tw_paned_v)
        self.tw_paned_v.add(tw_lower, weight=3)

        tw_toolbar = ttk.Frame(tw_lower)
        tw_toolbar.pack(fill=tk.X, pady=(0, 4))

        self.lbl_tw_checked_count = ttk.Label(tw_toolbar, text="[已勾选: 0 项规格]", foreground="#198754", font=FONT_BOLD)
        self.lbl_tw_checked_count.pack(side=tk.LEFT)

        btn_tw_check_all = ttk.Button(tw_toolbar, text=" 全选", image=self.icons["bolt"], compound=tk.LEFT, command=self.check_all_tw_variants)
        btn_tw_check_all.pack(side=tk.LEFT, padx=(8, 2))

        btn_tw_uncheck_all = ttk.Button(tw_toolbar, text=" 清空勾选", image=self.icons["clean"], compound=tk.LEFT, command=self.uncheck_all_tw_variants)
        btn_tw_uncheck_all.pack(side=tk.LEFT, padx=2)

        btn_tw_preview = ttk.Button(tw_toolbar, text=" 🎬 在线预览播放", image=self.icons["play"], compound=tk.LEFT, command=self.preview_twitter_video)
        btn_tw_preview.pack(side=tk.LEFT, padx=4)

        btn_tw_open_folder = ttk.Button(tw_toolbar, text=" 打开保存目录", image=self.icons["folder"], compound=tk.LEFT, command=lambda: self._open_folder(self.tw_dest_path_var.get()))
        btn_tw_open_folder.pack(side=tk.RIGHT, padx=2)

        # Treeview Container for video variants
        tw_file_container = ttk.Frame(tw_lower)
        tw_file_container.pack(fill=tk.BOTH, expand=True)

        cols = ("chk", "quality", "bitrate", "size", "filename")
        self.tree_tw_variants = ttk.Treeview(tw_file_container, columns=cols, show="headings", selectmode="extended")
        
        self.tree_tw_variants.heading("chk", text="☑ 勾选", anchor=tk.CENTER)
        self.tree_tw_variants.heading("quality", text="清晰度 / 画质规格", anchor=tk.W)
        self.tree_tw_variants.heading("bitrate", text="视频码率", anchor=tk.CENTER)
        self.tree_tw_variants.heading("size", text="预估文件大小", anchor=tk.CENTER)
        self.tree_tw_variants.heading("filename", text="下载文件名 / 目标名称 (双击在线预览播放)", anchor=tk.W)

        self.tree_tw_variants.column("chk", width=55, minwidth=50, stretch=False, anchor=tk.CENTER)
        self.tree_tw_variants.column("quality", width=240, minwidth=180, stretch=False, anchor=tk.W)
        self.tree_tw_variants.column("bitrate", width=110, minwidth=90, stretch=False, anchor=tk.CENTER)
        self.tree_tw_variants.column("size", width=120, minwidth=100, stretch=False, anchor=tk.CENTER)
        self.tree_tw_variants.column("filename", width=420, minwidth=200, stretch=True, anchor=tk.W)

        self.tree_tw_variants.tag_configure("checked_tag", foreground="#198754", font=FONT_TABLE_BOLD)
        self.tree_tw_variants.tag_configure("downloaded_tag", foreground="#198754", font=FONT_TABLE_BOLD)
        self.tree_tw_variants.tag_configure("downloaded_checked_tag", foreground="#0d6efd", font=FONT_TABLE_BOLD)
        self.tree_tw_variants.tag_configure("file_tag", foreground="#212529", font=FONT_TABLE)

        tw_scroll_y = ttk.Scrollbar(tw_file_container, orient=tk.VERTICAL, command=self.tree_tw_variants.yview)
        self.tree_tw_variants.configure(yscrollcommand=tw_scroll_y.set)

        self.tree_tw_variants.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tw_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_tw_variants.bind("<Button-1>", self._on_tw_tree_click)
        self.tree_tw_variants.bind("<space>", self._on_tw_tree_space)
        self.tree_tw_variants.bind("<Double-1>", lambda e: self.preview_twitter_video())
        self.tree_tw_variants.bind("<Button-3>", self._show_tw_context_menu)

        # Bottom Actions Bar of Tab 3
        tw_act_frame = ttk.Frame(self.tab_twitter)
        tw_act_frame.pack(fill=tk.X, pady=(4, 0))

        btn_tw_add_q = ttk.Button(
            tw_act_frame, text=" 加入统一下载队列", image=self.icons["download"], compound=tk.LEFT,
            command=lambda: self.add_twitter_to_queue(jump=False)
        )
        btn_tw_add_q.pack(side=tk.LEFT, padx=4, ipady=3)

        btn_tw_add_jump = ttk.Button(
            tw_act_frame, text=" 入队并跳转到队列", image=self.icons["rocket"], compound=tk.LEFT,
            command=lambda: self.add_twitter_to_queue(jump=True)
        )
        btn_tw_add_jump.pack(side=tk.LEFT, padx=4, ipady=3)

        self.tw_resolved_data = None
        self.checked_tw_variants: Set[int] = set()

    def _paste_twitter_url(self):
        try:
            cb_text = self.clipboard_get().strip()
            if cb_text:
                self.tw_url_var.set(cb_text)
                self.log(f"[i] 已从剪贴板粘贴视频链接: {cb_text}")
        except Exception:
            pass

    def _on_tw_preset_changed(self, event=None):
        label = self.tw_preset_var.get()
        if label in PRESET_DIRS_MAP:
            self.tw_dest_path_var.set(PRESET_DIRS_MAP[label])
            if self.tw_resolved_data:
                self._populate_twitter_results()

    def browse_tw_dest_path(self):
        cur = self.tw_dest_path_var.get().strip()
        init_dir = cur if (cur and os.path.exists(cur)) else os.path.expanduser("~")
        chosen = filedialog.askdirectory(parent=self, initialdir=init_dir, title="选择视频保存目标文件夹")
        if chosen:
            norm_dir = os.path.normpath(chosen)
            self.tw_dest_path_var.set(norm_dir)
            if self.tw_resolved_data:
                self._populate_twitter_results()

    def start_resolve_twitter(self):
        raw_url = self.tw_url_var.get().strip()
        if not raw_url:
            messagebox.showwarning("提示", "请输入视频/推文/文章链接或 ID！", parent=self)
            return

        self.btn_tw_fetch.config(state=tk.DISABLED)
        self.lbl_status.config(text="状态: 正在智能解析视频元数据与高清直链...", foreground="blue")
        self.lbl_tw_author.config(text="平台与作者: 正在连接网络并解析视频信息...", foreground="#0d6efd")
        self.lbl_tw_date.config(text="发布日期: 解析中... | 视频时长: 解析中...", foreground="#555555")
        self.lbl_tw_text.config(text=f"内容标题: 正在解析目标视频直链与清晰度规格 ({raw_url})...", foreground="#333333")
        
        proxy = self._get_effective_proxy()
        self.log(f"\n[*] 正在解析视频链接: {raw_url} | 代理: {proxy or '直连'}...")

        threading.Thread(target=self._resolve_twitter_worker, args=(raw_url, proxy), daemon=True).start()

    def _resolve_twitter_worker(self, raw_url: str, proxy: Optional[str]):
        try:
            res = UniversalMediaResolver.resolve(raw_url, proxy)
            self.tw_resolved_data = res
            plat_name = res.get("platform", "video")
            plat_lbl = res.get("platform_label", "视频")
            record_key = f"[{plat_lbl}] {res.get('author_id') or res.get('author')} / {res.get('media_id') or ''}"
            HistoryManager.record_access(record_key, "twitter", plat_name, "video", len(res.get("variants", [])))
            self.after(0, self._refresh_history_comboboxes)
            self.after(0, self._populate_twitter_results)
            self.after(0, lambda: self.log(f"[✓] 成功解析 [{plat_lbl}] {len(res.get('variants', []))} 个清晰度规格！作者: {res.get('author')} ({res.get('author_id')})"))
            self.after(0, lambda: self.lbl_status.config(text=f"状态: 成功解析 [{plat_lbl}] 视频 (共 {len(res.get('variants', []))} 项清晰度)", foreground="green"))
        except Exception as e:
            self.tw_resolved_data = None
            err_str = str(e)
            self.after(0, lambda: self.lbl_tw_author.config(text="平台与作者: 解析未成功", foreground="#dc3545"))
            self.after(0, lambda: self.lbl_tw_date.config(text="发布日期: -- | 视频时长: --", foreground="#555555"))
            self.after(0, lambda: self.lbl_tw_text.config(text=f"内容标题: ❌ 无法解析视频: {err_str}\n\n💡 提示: 请确认视频链接是否有效，或确认网络设置。", foreground="#dc3545"))
            self.after(0, lambda: self.lbl_tw_thumb.config(image="", text=" 📹 视频封面 \n(解析失败)", width=18))
            self.after(0, lambda: self.tree_tw_variants.delete(*self.tree_tw_variants.get_children()))
            self.after(0, lambda: self.checked_tw_variants.clear())
            self.after(0, lambda: self._update_tw_checked_count_label())
            self.after(0, lambda: self.log(f"[✗] 解析视频失败: {err_str}"))
            self.after(0, lambda: self.lbl_status.config(text="状态: 视频解析失败", foreground="red"))
            self.after(0, lambda: messagebox.showerror("解析失败", f"无法解析视频链接:\n{err_str}\n\n建议:\n1. 确认该链接是否包含视频或公开可见；\n2. 若为海外平台 (如 Twitter/YouTube)，请检查网络代理客户端 (如 Clash/v2rayN) 是否正常运行。", parent=self))
        finally:
            self.after(0, lambda: self.btn_tw_fetch.config(state=tk.NORMAL))

    def _populate_twitter_results(self):
        if not self.tw_resolved_data:
            return

        data = self.tw_resolved_data
        plat_lbl = data.get("platform_label", "视频")
        self.lbl_tw_author.config(text=f"[{plat_lbl}] 作者: {data.get('author')} ({data.get('author_id')})", foreground="#0d6efd")
        self.lbl_tw_date.config(text=f"发布日期: {data.get('date')} | 视频时长: {data.get('duration')}", foreground="#555555")
        self.lbl_tw_text.config(text=f"内容标题: {data.get('text')}", foreground="#212529")

        # Load Thumbnail asynchronously for the meta card
        self._load_twitter_thumbnail_async(data.get("thumbnail"))

        self.tree_tw_variants.delete(*self.tree_tw_variants.get_children())
        self.checked_tw_variants.clear()

        dest_dir = self.tw_dest_path_var.get().strip()
        variants = data.get("variants", [])
        for idx, v in enumerate(variants):
            v_name = v.get("filename", "")
            local_p = os.path.normpath(os.path.join(dest_dir, v_name)) if (dest_dir and v_name) else ""
            is_downloaded = bool(local_p and os.path.exists(local_p) and os.path.getsize(local_p) > 0)
            if not is_downloaded:
                is_downloaded = any(
                    t.file_path == v_name and t.dest_dir == dest_dir and t.status == "已完成" 
                    for t in self.tasks
                )

            # If not downloaded, default check highest quality; if already downloaded, do not default check to avoid redundant downloads
            is_default = (idx == 0) and not is_downloaded
            if is_default:
                self.checked_tw_variants.add(idx)
            
            is_chk = idx in self.checked_tw_variants
            chk_sym = "☑" if is_chk else "☐"
            
            q_label = v["quality"]
            if is_downloaded:
                q_label = f"{q_label} [🟢 已下载]"
                fn_label = f"{v_name} (双击直接0流量播放本地文件)"
                tag = "downloaded_checked_tag" if is_chk else "downloaded_tag"
            else:
                fn_label = v_name
                tag = "checked_tag" if is_chk else "file_tag"

            self.tree_tw_variants.insert(
                "", tk.END, iid=str(idx),
                values=(chk_sym, q_label, v["bitrate_str"], v["size_str"], fn_label),
                tags=(tag,)
            )

        self._update_tw_checked_count_label()

    def _load_twitter_thumbnail_async(self, thumb_url: Optional[str]):
        if not thumb_url:
            self.lbl_tw_thumb.config(image="", text=" 📹 暂无封面缩略图 ", width=18)
            return

        self.lbl_tw_thumb.config(image="", text=" ⏳ 封面加载中... ", width=18)
        proxy = self._get_effective_proxy()

        def _fetch():
            try:
                proxies = {"http": proxy, "https": proxy} if proxy else None
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(thumb_url, headers=headers, proxies=proxies, timeout=10)
                if resp.status_code == 200:
                    import io
                    img_data = io.BytesIO(resp.content)
                    pil_img = Image.open(img_data)
                    pil_img.thumbnail((160, 95), Image.Resampling.LANCZOS)
                    tk_img = ImageTk.PhotoImage(pil_img)
                    self.after(0, lambda img=tk_img: self._set_tw_thumb(img))
                else:
                    self.after(0, lambda: self.lbl_tw_thumb.config(image="", text=" ❌ 封面加载失败 ", width=18))
            except Exception:
                self.after(0, lambda: self.lbl_tw_thumb.config(image="", text=" 📹 点击在线预览 ", width=18))

        threading.Thread(target=_fetch, daemon=True).start()

    def _set_tw_thumb(self, tk_img):
        self.tw_card_thumb_img = tk_img
        self.lbl_tw_thumb.config(image=tk_img, text="", width=0)

    def preview_twitter_video(self):
        if not self.tw_resolved_data or not self.tw_resolved_data.get("variants"):
            messagebox.showwarning("提示", "请先解析有效的视频后再查看效果！", parent=self)
            return

        sel = self.tree_tw_variants.selection()
        idx = 0
        if sel and sel[0].isdigit():
            idx = int(sel[0])

        MediaPreviewDialog(
            self, 
            self.tw_resolved_data, 
            variant_index=idx, 
            proxy=self._get_effective_proxy(),
            dest_dir=self.tw_dest_path_var.get().strip()
        )

    def _show_tw_context_menu(self, event):
        if not self.tw_resolved_data:
            return
        item_id = self.tree_tw_variants.identify_row(event.y)
        if item_id and item_id.isdigit():
            self.tree_tw_variants.selection_set(item_id)
            idx = int(item_id)
            variants = self.tw_resolved_data.get("variants", [])
            if 0 <= idx < len(variants):
                v = variants[idx]
                v_url = v.get("url", "")
                v_name = v.get("filename", "")
                dest_dir = self.tw_dest_path_var.get().strip()
                local_path = os.path.normpath(os.path.join(dest_dir, v_name)) if (dest_dir and v_name) else ""
                has_local = bool(local_path and os.path.exists(local_path) and os.path.getsize(local_path) > 0)

                menu = tk.Menu(self, tearoff=0)
                target_src = local_path if has_local else v_url
                eff_proxy = self._get_effective_proxy()
                if has_local:
                    menu.add_command(label="▶️ 内置全能播放本地视频 (0 流量秒开·支持HEVC/AV1)", command=lambda: UniversalMediaPlayer.play_video(target_src, title=t_title, http_headers=hdrs, proxy=eff_proxy, parent=self))
                    menu.add_command(label="🎬 详细预览与封面信息 (包含本地信息)", command=self.preview_twitter_video)
                    menu.add_command(label="📂 打开本地文件所在文件夹", command=lambda: os.startfile(os.path.dirname(local_path)) if sys.platform == "win32" else None)
                else:
                    menu.add_command(label="▶️ 内置全能播放器在线预览 (支持HEVC/AV1/全格式)", command=lambda: UniversalMediaPlayer.play_video(target_src, title=t_title, http_headers=hdrs, proxy=eff_proxy, parent=self))
                    menu.add_command(label="🎬 详细封面与预览弹窗", command=self.preview_twitter_video)
                    menu.add_command(label="🌐 在浏览器中打开播放直链", command=lambda: os.startfile(v_url) if sys.platform == "win32" else None)
                
                menu.add_command(label="📋 复制下载直链", command=lambda: (self.clipboard_clear(), self.clipboard_append(v_url), messagebox.showinfo("提示", "已复制直链到剪贴板！", parent=self)))
                menu.add_separator()
                menu.add_command(label="📥 将当前规格加入统一下载队列", command=lambda: self.add_twitter_to_queue(jump=False))
                menu.post(event.x_root, event.y_root)

    def _on_tw_tree_click(self, event):
        region = self.tree_tw_variants.identify("region", event.x, event.y)
        if region == "heading":
            col = self.tree_tw_variants.identify_column(event.x)
            if col == "#1":
                self.check_all_tw_variants()
                return "break"
        elif region in ("cell", "tree", "item"):
            item_id = self.tree_tw_variants.identify_row(event.y)
            if item_id and item_id.isdigit():
                self._toggle_single_tw_check(int(item_id))
                self.tree_tw_variants.selection_set(item_id)
                return "break"

    def _on_tw_tree_space(self, event):
        sel = self.tree_tw_variants.selection()
        if sel:
            for iid in sel:
                if iid.isdigit():
                    self._toggle_single_tw_check(int(iid))
            return "break"

    def _toggle_single_tw_check(self, idx: int):
        if idx in self.checked_tw_variants:
            self.checked_tw_variants.remove(idx)
        else:
            self.checked_tw_variants.add(idx)
        self._update_tw_checkbox_display(idx)
        self._update_tw_checked_count_label()

    def _update_tw_checkbox_display(self, idx: int):
        iid = str(idx)
        if self.tree_tw_variants.exists(iid):
            is_chk = idx in self.checked_tw_variants
            chk_sym = "☑" if is_chk else "☐"
            vals = list(self.tree_tw_variants.item(iid, "values"))
            vals[0] = chk_sym
            
            # Check if this item is marked as downloaded
            is_downloaded = len(vals) > 1 and "[🟢 已下载]" in str(vals[1])
            if is_downloaded:
                tag = "downloaded_checked_tag" if is_chk else "downloaded_tag"
            else:
                tag = "checked_tag" if is_chk else "file_tag"
                
            self.tree_tw_variants.item(iid, values=vals, tags=(tag,))

    def _update_tw_checked_count_label(self):
        cnt = len(self.checked_tw_variants)
        self.lbl_tw_checked_count.config(text=f"[已勾选: {cnt} 项规格]")

    def check_all_tw_variants(self):
        if not self.tw_resolved_data:
            return
        for idx in range(len(self.tw_resolved_data.get("variants", []))):
            self.checked_tw_variants.add(idx)
            self._update_tw_checkbox_display(idx)
        self._update_tw_checked_count_label()

    def uncheck_all_tw_variants(self):
        self.checked_tw_variants.clear()
        if self.tw_resolved_data:
            for idx in range(len(self.tw_resolved_data.get("variants", []))):
                self._update_tw_checkbox_display(idx)
        self._update_tw_checked_count_label()

    def add_twitter_to_queue(self, jump: bool = False):
        if not self.tw_resolved_data or not self.tw_resolved_data.get("variants"):
            messagebox.showwarning("提示", "请先解析推文视频！", parent=self)
            return

        target_indices = list(self.checked_tw_variants)
        if not target_indices:
            sel = self.tree_tw_variants.selection()
            if sel:
                target_indices = [int(x) for x in sel if x.isdigit()]

        if not target_indices:
            messagebox.showwarning("提示", "请先在列表中勾选需要下载的画质规格！", parent=self)
            return

        dest_dir = self.tw_dest_path_var.get().strip()
        if not dest_dir:
            messagebox.showwarning("提示", "请指定保存目标路径！", parent=self)
            return
        os.makedirs(dest_dir, exist_ok=True)

        data = self.tw_resolved_data
        variants = data.get("variants", [])
        proxy = self._get_effective_proxy()
        added_cnt = 0

        for idx in sorted(target_indices):
            if idx < 0 or idx >= len(variants):
                continue
            v = variants[idx]
            v_url = v["url"]
            v_name = v["filename"]

            # Check if task already exists
            exists = any(t.platform == "twitter" and t.direct_url == v_url and t.dest_dir == dest_dir for t in self.tasks)
            if exists:
                continue

            task_id = self._get_next_task_id()
            task = QueueTask(
                task_id=task_id,
                repo_id=f"🐦 {data.get('author_id') or 'Twitter'}",
                repo_type="twitter",
                branch=data.get("tweet_id", ""),
                file_path=v_name,
                size_str=v["size_str"],
                date_str=data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M")),
                dest_dir=dest_dir,
                flatten=True,
                endpoint="https://twitter.com",
                token=None,
                proxy=proxy,
                status="等待中",
                progress=0.0,
                total_bytes=v["raw_size"] if v["raw_size"] > 0 else None,
                platform="twitter",
                direct_url=v_url,
                source_url=v.get("source_url"),
                format_id=v.get("format_id")
            )
            task.check_local_status()
            self.tasks.append(task)
            added_cnt += 1

        if added_cnt > 0:
            self._save_tasks()
            self.rescan_all_tasks(silent=True)
            self._refresh_queue_tree()
            self.log(f"[✓] 已将 {added_cnt} 项 Twitter 视频任务成功加入统一下载队列！")
            messagebox.showinfo("入队成功", f"成功将 {added_cnt} 项 Twitter 视频任务加入统一下载队列！\n目标目录: {dest_dir}", parent=self)
            if jump:
                self.notebook.select(3)
        else:
            messagebox.showinfo("提示", "所选的任务均已在队列中！", parent=self)

    def quick_download_twitter_highest(self):
        if not self.tw_resolved_data or not self.tw_resolved_data.get("variants"):
            messagebox.showwarning("提示", "请先解析推文视频！", parent=self)
            return

        self.checked_tw_variants.clear()
        self.checked_tw_variants.add(0) # Select index 0 (Highest resolution)
        self._update_tw_checkbox_display(0)
        self._update_tw_checked_count_label()
        self.add_twitter_to_queue(jump=True)
        if not self.is_queue_running:
            self.start_queue_download()

    # ------------------ Tab 4: Download Queue UI with Checkboxes ------------------
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
            messagebox.showinfo("提示", "运行日志已复制到剪贴板。", parent=self)

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

        btn_manage_presets_env = tk.Button(
            row_cf,
            text=" ⚙️ 实时管理维护预设分类目录 ",
            font=FONT_BOLD,
            bg="#0d6efd",
            fg="#ffffff",
            activebackground="#0b5ed7",
            activeforeground="#ffffff",
            padx=8, pady=2,
            command=self.open_preset_manager
        )
        btn_manage_presets_env.pack(side=tk.LEFT, padx=(4, 0))

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
                messagebox.showinfo("检测成功", f"成功探测到 ComfyUI 模型目录:\n{c}", parent=self)
                return
        messagebox.showwarning("提示", "未能自动探测到 ComfyUI 路径，请点击【浏览目录...】手动选择。", parent=self)

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
                if messagebox.askyesno("创建目录", f"目录不存在，是否立即创建？\n{path}", parent=self):
                    try:
                        os.makedirs(path, exist_ok=True)
                        self._refresh_tab_env_dirs()
                        messagebox.showinfo("成功", f"目录已成功创建:\n{path}", parent=self)
                    except Exception as err:
                        messagebox.showerror("错误", f"创建失败: {str(err, parent=self)}")

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
        messagebox.showinfo("完成", f"一键环境部署完成！共补齐/创建 {created} 个模型分类目录。", parent=self)

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
                    self.after(0, lambda: messagebox.showinfo("成功", "所有核心依赖已成功安装并部署完成！", parent=self))
                    self.after(0, self._on_env_setup_completed)
                else:
                    self.after(0, lambda: messagebox.showwarning("提示", "安装过程已结束，部分依赖可能有提示，请检查日志。", parent=self))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("错误", f"执行异常: {str(e, parent=self)}"))
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
            self.after(0, lambda: messagebox.showinfo("检测结果", "未发现任何正在下载或中断的临时文件。", parent=self))
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
                messagebox.showinfo("后台任务检测", msg, parent=self)
            else:
                self.log(f"[✓] 检测到 {len(stopped_list)} 个中断/静止文件，当前无后台进程在写入，可安全点击【开始/恢复】接续下载。")
                messagebox.showinfo("后台任务检测", f"检测到 {len(stopped_list, parent=self)} 个未完成的缓存文件，当前没有活跃的后台下载进程，您可以随时点击【恢复下载】继续。")
            self.lbl_status.config(text="状态: 检测完成", foreground="green")

        self.after(0, update_ui_result)

    # ------------------ Safe Exit & Minimize to Background ------------------
    def hide_to_background(self):
        if not self.is_queue_running:
            if messagebox.askyesno("提示", "当前没有正在进行的下载任务，确定要最小化隐藏到后台吗？", parent=self):
                self.iconify()
        else:
            messagebox.showinfo("后台静默运行", "下载器已在后台全速下载。\n您可以通过任务栏或重新运行启动器随时切回窗口。", parent=self)
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
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d %H:%M")
        if isinstance(dt, str):
            try:
                clean_str = dt.replace("Z", "+00:00")
                parsed = datetime.fromisoformat(clean_str)
                return parsed.strftime("%Y-%m-%d %H:%M")
            except:
                return dt[:16] if len(dt) >= 16 else dt
        return str(dt)

    # ------------------ Tab 1 Actions & Population ------------------
    def start_fetch_files(self):
        repo_id = self.repo_id_var.get().strip()
        if not repo_id:
            messagebox.showwarning("提示", "请输入有效的 Repo ID！", parent=self)
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
        effective_proxy = self._get_effective_proxy()

        # Safely set proxy environment variables for huggingface_hub
        if effective_proxy:
            os.environ["HTTP_PROXY"] = effective_proxy
            os.environ["HTTPS_PROXY"] = effective_proxy
            os.environ["http_proxy"] = effective_proxy
            os.environ["https_proxy"] = effective_proxy
        else:
            for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                os.environ.pop(k, None)

        files_map = {}
        err_msg = None

        # Fetch global repo real date for accurate fallback
        repo_real_date_str = "--"
        try:
            base_type = "models" if repo_type == "model" else (repo_type + "s" if not repo_type.endswith("s") else repo_type)
            info_url = f"{endpoint}/api/{base_type}/{repo_id}"
            headers = {"User-Agent": "HF-Downloader-GUI/1.0"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            resp_info = requests.get(info_url, headers=headers, proxies=proxies, timeout=8)
            if resp_info.status_code == 200:
                inf = resp_info.json()
                raw_mod = inf.get("lastModified") or inf.get("createdAt")
                if raw_mod:
                    repo_real_date_str = self._format_date(raw_mod)
        except Exception:
            pass

        try:
            api = HfApi(endpoint=endpoint, token=token)
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
                    if date_str in ("--", "未知", "None", ""):
                        date_str = repo_real_date_str if repo_real_date_str != "--" else datetime.now().strftime("%Y-%m-%d %H:%M")

                    files_map[rfilename] = {
                        "path": rfilename,
                        "size_str": size_str,
                        "date_str": date_str,
                        "raw_size": raw_size or 0,
                        "raw_date": raw_date or repo_real_date_str
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
                                if date_str in ("--", "未知", "None", ""):
                                    date_str = repo_real_date_str if repo_real_date_str != "--" else datetime.now().strftime("%Y-%m-%d %H:%M")

                                files_map[rfilename] = {
                                    "path": rfilename,
                                    "size_str": size_str,
                                    "date_str": date_str,
                                    "raw_size": raw_size or 0,
                                    "raw_date": last_mod or repo_real_date_str
                                }
                        err_msg = None
            except Exception as e2:
                err_msg = str(e2)

        # Fallback 2: Repo info
        if not files_map:
            try:
                api = HfApi(endpoint=endpoint, token=token)
                info = api.model_info(repo_id, files_metadata=True) if repo_type == "model" else api.repo_info(repo_id, repo_type=repo_type, files_metadata=True)
                global_date_str = self._format_date(getattr(info, "lastModified", None))
                if global_date_str in ("--", "未知", "None", ""):
                    global_date_str = repo_real_date_str if repo_real_date_str != "--" else datetime.now().strftime("%Y-%m-%d %H:%M")
                
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
            HistoryManager.record_access(repo_id, "huggingface", repo_type, branch, len(files_map))
            self.after(0, self._refresh_history_comboboxes)
            self.after(0, self._populate_dual_pane_browser)
            self.after(0, lambda: self.log(f"[✓] 成功获取到 {len(files_map)} 个文件，已按双栏文件浏览器组织。"))
            self.after(0, lambda: self.lbl_status.config(text=f"状态: 共获取到 {len(files_map)} 个文件", foreground="green"))
        else:
            self.after(0, lambda: self.log(f"[错误] 获取文件列表失败: {err_msg}"))
            self.after(0, lambda: self.lbl_status.config(text="状态: 获取失败", foreground="red"))
            self.after(0, lambda: messagebox.showerror("获取失败", f"无法获取仓库文件列表:\n{err_msg}\n\n提示: 如遇网络连接超时，可尝试切换镜像源或在上方设置网络代理 (Proxy, parent=self)。"))

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
            messagebox.showwarning("提示", "请先在右侧文件列表中勾选复选框 ☑ 或高亮选择要下载的文件！\n（或点击【将当前左侧目录全部文件加入下载队列】）", parent=self)
            return

        dest_dir = self.dest_dir_var.get().strip()
        if not dest_dir:
            messagebox.showwarning("提示", "请设置目标保存目录！", parent=self)
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
            self.notebook.select(3)

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
            messagebox.showinfo("提示", "当前目录下没有文件。", parent=self)
            return

        dest_dir = self.dest_dir_var.get().strip()
        if not dest_dir:
            messagebox.showwarning("提示", "请设置目标保存目录！", parent=self)
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
        messagebox.showinfo("已加入队列", f"已将目录 '{dir_name}' 下的 {added_count} 个文件成功加入下载队列！", parent=self)

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
        self.notebook.tab(3, text=f" 📑 统一下载队列 ({pending_count}) ")
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
            messagebox.showinfo("提示", "请先在队列表中勾选复选框 ☑ 或高亮选择要移除的任务。", parent=self)
            return

        remove_set = set(target_ids)
        target_tasks = [t for t in self.tasks if t.task_id in remove_set]

        for t in target_tasks:
            if t.status == "下载中":
                messagebox.showwarning("提示", f"任务 #{t.task_id} 正在下载中，请先暂停/停止后再移除！", parent=self)
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
            messagebox.showinfo("彻底删除完成", f"已成功从队列移除 {len(target_tasks)} 个任务，\n并彻底清理了 {deleted_file_count} 个本地文件与 {deleted_cache_count} 个未完成缓存文件！", parent=self)

        elif choice == "queue_only":
            self.tasks = [t for t in self.tasks if t.task_id not in remove_set]
            self.checked_tasks.difference_update(remove_set)
            self.rescan_all_tasks(silent=True)
            self.log(f"[-] 已从队列中移除 {len(target_tasks)} 个任务 (已保留本地所有文件与缓存)。")

    def clear_completed_tasks(self):
        done_tasks = [t for t in self.tasks if t.status == "已完成"]
        if not done_tasks:
            messagebox.showinfo("提示", "当前队列中没有已完成的任务。", parent=self)
            return

        done_ids = {t.task_id for t in done_tasks}
        self.tasks = [t for t in self.tasks if t.status != "已完成"]
        self.checked_tasks.difference_update(done_ids)
        self.rescan_all_tasks(silent=True)
        self.log(f"[✓] 已清理 {len(done_tasks)} 个已完成的任务记录 (本地文件已完整保留)。")

    def clear_all_tasks(self):
        if self.is_queue_running:
            messagebox.showwarning("提示", "下载队列正在运行中，请先停止队列！", parent=self)
            return
        if not self.tasks:
            return

        choice = messagebox.askyesno("清空队列", "确定要清空队列中的所有任务记录吗？\n（仅清空队列记录，不删除本地已下载的文件）", parent=self)
        if choice:
            self.tasks.clear()
            self.checked_tasks.clear()
            self.rescan_all_tasks(silent=True)
            self.log("[✓] 下载队列已清空。")

    def open_selected_task_folder(self):
        target_ids = self._get_target_task_ids()
        if not target_ids:
            messagebox.showinfo("提示", "请在队列中选择或勾选一个任务。", parent=self)
            return
        target_id = target_ids[0]
        for t in self.tasks:
            if t.task_id == target_id:
                if os.path.exists(t.dest_dir):
                    os.startfile(t.dest_dir)
                else:
                    messagebox.showinfo("提示", f"目录尚未创建:\n{t.dest_dir}", parent=self)
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
                    choice = messagebox.askyesno("重新下载", "所勾选的任务均已完成，是否重新下载勾选的任务？", parent=self)
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
                    messagebox.showinfo("提示", "所勾选的任务中没有需要下载的任务。", parent=self)
                    return
        else:
            pending_tasks = [t for t in self.tasks if t.status in ("等待中", "已中断", "已暂停", "失败")]
            if not pending_tasks:
                messagebox.showinfo("提示", "当前队列中没有需要下载的任务（全部已完成或队列为空）。", parent=self)
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
            if getattr(current_task, "http_headers", None):
                headers.update(current_task.http_headers)
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

            # Check if this task is a Magnet / BitTorrent task
            if current_task.platform == "magnet" or (current_task.direct_url and current_task.direct_url.startswith("magnet:?")):
                self.log(f"     [磁力下载] 启用 Aria2 高性能 P2P/DHT 极速下载引擎...")
                magnet_link = current_task.direct_url or current_task.file_path
                def _update_mag_ui(pct, cur_sz, tot_sz, spd, eta, peer_str):
                    task_text = f"进度: {pct:.1f}% ({cur_sz} / {tot_sz})"
                    spd_text = f"速度: {spd} | {peer_str} | 预估: {eta}"
                    self.after(0, lambda p=pct, t_txt=task_text, s_txt=spd_text: (
                        self.progress_var.set(p),
                        self.lbl_progress_text.config(text=t_txt),
                        self.lbl_speed_text.config(text=s_txt)
                    ))
                
                success = Aria2Manager.download_magnet(
                    enhanced_magnet=magnet_link,
                    dest_dir=current_task.dest_dir,
                    filename_hint=current_task.file_path,
                    proxy=proxy_str,
                    task=current_task,
                    update_ui_callback=_update_mag_ui,
                    cancel_checker=lambda: self.cancel_current_task or self.stop_queue_requested,
                    log_callback=self.log
                )
            # Check if this task requires yt-dlp native extraction & muxing engine (e.g. YouTube googlevideo streams, DASH video+audio muxing)
            is_ytdlp_stream = bool(
                getattr(current_task, "source_url", None) or 
                getattr(current_task, "format_id", None) or 
                "googlevideo.com" in (current_task.direct_url or "") or
                current_task.platform in ("youtube", "universal")
            )
            if is_ytdlp_stream and (getattr(current_task, "source_url", None) or current_task.direct_url):
                src_target = getattr(current_task, "source_url", None) or current_task.direct_url
                self.log(f"     [专业引擎] 启用 yt-dlp 高清无损分片与音视频混流下载引擎...")
                success = self._download_via_ytdlp(src_target, getattr(current_task, "format_id", None), target_file_path, proxy_str, current_task)
            else:
                success = self._stream_download(download_url, target_file_path, headers, proxies, current_task)

            if self.stop_queue_requested or self.cancel_current_task:
                current_task.status = "已中断"
                self.log(f"[!] 任务 #{current_task.task_id} 已平稳终止（断点进度已保留）。")
            elif success:
                current_task.status = "已完成"
                current_task.progress = 100.0
                self.log(f"[✓] 任务 #{current_task.task_id} 下载完成！")

                # Auto-extract and organize GitHub Zip packages into subfolder
                if current_task.repo_type == "github_zip" and target_file_path.endswith(".zip"):
                    try:
                        import zipfile
                        extract_dest = current_task.dest_dir
                        self.log(f"     [自动解压与收纳] 正在将 {os.path.basename(target_file_path)} 解压部署至: {extract_dest}")
                        with zipfile.ZipFile(target_file_path, 'r') as zip_ref:
                            file_list = zip_ref.namelist()
                            # Check if archive wraps all contents inside a single top-level folder (e.g. repo-main/)
                            root_prefix = ""
                            if file_list and "/" in file_list[0]:
                                candidate = file_list[0].split("/")[0] + "/"
                                if all(f.startswith(candidate) for f in file_list if f != candidate):
                                    root_prefix = candidate

                            for member in zip_ref.infolist():
                                target_rel = member.filename
                                if root_prefix and target_rel.startswith(root_prefix):
                                    target_rel = target_rel[len(root_prefix):]
                                if not target_rel:
                                    continue
                                
                                out_path = os.path.join(extract_dest, os.path.normpath(target_rel))
                                if member.is_dir():
                                    os.makedirs(out_path, exist_ok=True)
                                else:
                                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                                    with zip_ref.open(member) as source, open(out_path, "wb") as target:
                                        target.write(source.read())

                        self.log(f"     [✓] 自动解压完成！所有文件已规范收纳在独立目录:\n         {extract_dest}")
                    except Exception as ze:
                        self.log(f"     [!] 自动解压提示: {str(ze)}")

            self.active_task_id = None
            self.after(0, self._refresh_queue_tree)
            self._save_tasks()

        self._update_lock_file(False)
        self.after(0, self._on_queue_finished)

    def _download_via_ytdlp(self, source_url: str, format_id: Optional[str], local_path: str, proxy: Optional[str], task: QueueTask) -> bool:
        import yt_dlp
        
        last_update = [0.0]
        if format_id and format_id not in ("None", ""):
            fmt = f"{format_id}+bestaudio/best" if not local_path.endswith(".m4a") else format_id
        else:
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

        def progress_hook(d):
            if self.cancel_current_task or self.stop_queue_requested:
                raise yt_dlp.utils.DownloadCancelled("用户取消")
            
            status = d.get('status')
            if status == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or task.total_bytes or 0
                downloaded = d.get('downloaded_bytes') or 0
                speed = d.get('speed') or 0
                eta = d.get('eta') or 0
                
                now = time.time()
                if now - last_update[0] >= 0.3:
                    last_update[0] = now
                    speed_str = self._format_size(int(speed)) + "/s" if speed else "--"
                    eta_str = f"{eta // 60}分{eta % 60}秒" if eta > 60 else (f"{eta}秒" if eta else "--")
                    
                    if total > 0:
                        pct = min(99.9, (downloaded / total) * 100.0)
                        task.progress = pct
                        task.total_bytes = total
                        self.after(0, lambda p=pct, dw=downloaded, t=total, s=speed_str, e=eta_str:
                            self._update_progress_ui(p, dw, t, s, e)
                        )
                    else:
                        self.after(0, lambda dw=downloaded, s=speed_str:
                            self._update_progress_indeterminate(dw, s)
                        )
            elif status == 'finished':
                task.progress = 100.0

        ydl_opts = {
            'format': fmt,
            'outtmpl': local_path,
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'socket_timeout': 25,
            'retries': 10,
            'fragment_retries': 10,
            'merge_output_format': 'mp4',
        }
        if proxy:
            ydl_opts['proxy'] = proxy

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([source_url])
            
            if os.path.exists(local_path) and os.path.getsize(local_path) > 1024:
                return True
            
            base, _ = os.path.splitext(local_path)
            for ext in ('.mp4', '.mkv', '.webm', '.m4a'):
                alt = base + ext
                if os.path.exists(alt) and os.path.getsize(alt) > 1024:
                    if alt != local_path:
                        if os.path.exists(local_path):
                            os.remove(local_path)
                        os.rename(alt, local_path)
                    return True
            return False
        except Exception as e:
            task.error_msg = str(e)
            return False

    def _stream_download(self, url: str, local_path: str, headers: dict, proxies: dict, task: QueueTask) -> bool:
        temp_path = local_path + ".downloading"
        chunk_size = 512 * 1024  # 512KB chunk
        max_retries = 5

        # Build candidate URL list for auto-failover
        candidate_urls = [url]
        if task.platform == "github":
            raw_target = url
            for m in DEFAULT_GITHUB_ACCELERATORS:
                if m != "不使用加速 (官方直连)" and raw_target.startswith(m):
                    raw_target = raw_target[len(m):]
                    break
            
            for m in DEFAULT_GITHUB_ACCELERATORS:
                if m != "不使用加速 (官方直连)":
                    cand = m + raw_target
                    if cand not in candidate_urls:
                        candidate_urls.append(cand)
            if raw_target not in candidate_urls:
                candidate_urls.append(raw_target)

        last_error = None
        for try_idx, try_url in enumerate(candidate_urls):
            retry_count = 0
            while retry_count < max_retries:
                if self.cancel_current_task or self.stop_queue_requested:
                    task.error_msg = "用户取消"
                    return False
                
                req_headers = headers.copy()
                downloaded_bytes = 0
                if os.path.exists(temp_path):
                    downloaded_bytes = os.path.getsize(temp_path)
                    if downloaded_bytes > 0:
                        req_headers["Range"] = f"bytes={downloaded_bytes}-"
                        if retry_count == 0:
                            self.log(f"     [断点续传] 检测到已有缓存 {self._format_size(downloaded_bytes)}，从断点处继续...")
                        else:
                            self.log(f"     [自动重连] 正在从断点 {self._format_size(downloaded_bytes)} 继续重试 ({retry_count+1}/{max_retries})...")

                try:
                    with requests.get(try_url, headers=req_headers, proxies=proxies, stream=True, timeout=25, verify=False, allow_redirects=True) as resp:
                        if resp.status_code == 416:
                            total_size = downloaded_bytes
                        elif resp.status_code not in (200, 206):
                            last_error = f"HTTP {resp.status_code}"
                            retry_count += 1
                            time.sleep(1)
                            continue
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
                                        speed_bps = bytes_since_last / dt if dt > 0 else 0
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

                        # STRICT COMPLETENESS VALIDATION:
                        if total_size and total_size > 0 and downloaded_bytes < total_size:
                            self.log(f"     [!] 网络连接中途断开 ({self._format_size(downloaded_bytes)} / {self._format_size(total_size)})，准备自动断点续传...")
                            retry_count += 1
                            time.sleep(1)
                            continue

                    # Verified full file completeness!
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    os.rename(temp_path, local_path)
                    task.progress = 100.0
                    return True

                except Exception as e:
                    last_error = str(e)
                    retry_count += 1
                    time.sleep(1)
                    continue

        task.error_msg = str(last_error)
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
            messagebox.showinfo("队列完成", f"队列中的所有 {total_count} 个任务已全部下载完成！", parent=self)

if __name__ == "__main__":
    app = HFDownloaderApp()
    app.mainloop()
