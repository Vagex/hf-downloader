import os
import sys
import time
import json
import datetime
import threading
import subprocess
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
import flet as ft

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

# Preset Directory Mappings: Display Label -> Absolute Path
DEFAULT_COMFYUI_ROOT = r"F:\ComfyUI-aki-v3\ComfyUI\models"
PRESET_DIRS_MAP = {
    "扩散模型 (diffusion_models)": os.path.join(DEFAULT_COMFYUI_ROOT, "diffusion_models"),
    "控制网络 (controlnet)": os.path.join(DEFAULT_COMFYUI_ROOT, "controlnet"),
    "大模型底模 (checkpoints)": os.path.join(DEFAULT_COMFYUI_ROOT, "checkpoints"),
    "微调模型 (loras)": os.path.join(DEFAULT_COMFYUI_ROOT, "loras"),
    "变分自编码 (vae)": os.path.join(DEFAULT_COMFYUI_ROOT, "vae"),
    "UNet 主干 (unet)": os.path.join(DEFAULT_COMFYUI_ROOT, "unet"),
    "文本编码器 (clip)": os.path.join(DEFAULT_COMFYUI_ROOT, "clip"),
}

# Modern Professional Color Palette
COLOR_BG_DARK = "#090d16"         # App Background
COLOR_SURFACE_DARK = "#111827"    # Card/Panel Background
COLOR_CARD_DARK = "#182234"       # Inner Container Background
COLOR_BORDER = "#283548"          # Subtle Border
COLOR_HOVER = "#243248"           # Hover Highlight
COLOR_ACTIVE = "#1e3a8a"          # Active Selected
COLOR_ACCENT = "#3b82f6"          # Primary Blue Accent
COLOR_TEXT_PRIMARY = "#f8fafc"    # Main Bright Text
COLOR_TEXT_SECONDARY = "#94a3b8"  # Slate Muted Text
COLOR_SUCCESS = "#10b981"         # Green
COLOR_WARNING = "#f59e0b"         # Amber/Gold
COLOR_DANGER = "#ef4444"          # Red


def format_size(size_bytes: Optional[int]) -> str:
    if size_bytes is None:
        return "--"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_date(dt: Any) -> str:
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


class QueueTask:
    def __init__(self, task_id: int, repo_id: str, repo_type: str, branch: str, 
                 file_path: str, size_str: str, date_str: str, dest_dir: str, flatten: bool, 
                 endpoint: str, token: Optional[str], proxy: Optional[str] = None, 
                 status: str = "等待中", progress: float = 0.0, total_bytes: Optional[int] = None):
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
        
        self.status = status
        self.progress = progress
        self.speed_str = "--"
        self.eta_str = "--"
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
            status=data.get("status", "等待中"),
            progress=data.get("progress", 0.0),
            total_bytes=data.get("total_bytes")
        )
        task.check_local_status()
        return task


def get_windows_system_theme() -> ft.ThemeMode:
    """Accurately detects Windows system Dark/Light mode preference from registry."""
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return ft.ThemeMode.LIGHT if value == 1 else ft.ThemeMode.DARK
        except Exception:
            pass
    return ft.ThemeMode.DARK


def main(page: ft.Page):
    page.title = "🚀 Hugging Face 极速多线程与断点续传下载器 (Pro Edition)"
    
    # ---------------- State Variables ----------------
    mirrors_list: List[str] = list(DEFAULT_MIRRORS)
    proxies_list: List[str] = list(DEFAULT_PROXIES)
    saved_proxy: str = ""
    saved_token: str = ""
    saved_theme_pref: str = "system"  # 'system', 'dark', 'light'

    # Load Settings
    if os.path.exists(APP_CONFIG_FILE):
        try:
            with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                saved_proxy = data.get("proxy", "")
                saved_token = data.get("token", "")
                saved_theme_pref = data.get("theme_mode", "system")
        except Exception:
            pass

    # Apply initial theme mode
    current_theme_pref = saved_theme_pref
    if current_theme_pref == "dark":
        page.theme_mode = ft.ThemeMode.DARK
    elif current_theme_pref == "light":
        page.theme_mode = ft.ThemeMode.LIGHT
    else:
        page.theme_mode = get_windows_system_theme()

    page.padding = 8
    page.window.width = 1280
    page.window.height = 900
    page.window.min_width = 1000
    page.window.min_height = 720
    
    raw_files_dict: Dict[str, Dict[str, Any]] = {}
    current_selected_dir: str = ""
    collapsed_dirs: Set[str] = set()
    checked_files: Set[str] = set()
    checked_tasks: Set[int] = set()

    tasks: List[QueueTask] = []
    task_counter: int = 1
    is_queue_running: bool = False
    cancel_current_task: bool = False
    stop_queue_requested: bool = False
    active_task_id: Optional[int] = None

    # Load Settings
    if os.path.exists(APP_CONFIG_FILE):
        try:
            with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                saved_proxy = data.get("proxy", "")
                saved_token = data.get("token", "")
        except Exception:
            pass

    if os.path.exists(MIRRORS_CONFIG_FILE):
        try:
            with open(MIRRORS_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                saved = data.get("mirrors", [])
                if saved and isinstance(saved, list):
                    mirrors_list = [m for m in saved if m and isinstance(m, str)]
        except Exception:
            pass

    if os.path.exists(PROXIES_CONFIG_FILE):
        try:
            with open(PROXIES_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                saved = data.get("proxies", [])
                if saved and isinstance(saved, list):
                    proxies_list = [p for p in saved if p and isinstance(p, str)]
        except Exception:
            pass

    def save_settings():
        try:
            p_val = get_effective_proxy()
            t_val = tf_token.value.strip() if tf_token.value else ""
            with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "proxy": p_val,
                    "token": t_val,
                    "theme_mode": current_theme_pref
                }, f, ensure_ascii=False, indent=2)
            if t_val:
                os.environ["HF_TOKEN"] = t_val
        except Exception:
            pass

    def save_tasks():
        try:
            data = {"tasks": [t.to_dict() for t in tasks]}
            with open(TASKS_DB_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_effective_proxy() -> Optional[str]:
        val = dd_proxy.value or ""
        if not val or "不使用代理" in val or "直连" in val:
            return None
        if not (val.startswith("http://") or val.startswith("https://") or val.startswith("socks5://") or val.startswith("socks5h://")):
            val = "http://" + val
        return val

    def get_request_proxies() -> Optional[Dict[str, str]]:
        p = get_effective_proxy()
        return {"http": p, "https": p} if p else None

    def log(msg: str):
        t_str = time.strftime("%H:%M:%S")
        log_text.value += f"[{t_str}] {msg}\n"
        page.update()

    def show_snack(text: str, is_error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(text, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=COLOR_DANGER if is_error else COLOR_SUCCESS,
            open=True
        )
        page.overlay.append(snack)
        page.update()

    # ------------------ UI Controls: Strict 38px Desktop Standard ------------------
    STANDARD_CONTROL_HEIGHT = 38
    STD_PADDING = ft.Padding.symmetric(horizontal=8, vertical=4)
    STD_RADIUS = 4

    tf_repo = ft.TextField(
        hint_text="例如: Kijai/MiniMax-H3-experimental", value="Kijai/MiniMax-H3-experimental",
        expand=3, dense=True, height=STANDARD_CONTROL_HEIGHT, text_size=12,
        content_padding=STD_PADDING, border_radius=STD_RADIUS
    )
    dd_type = ft.Dropdown(
        value="model",
        options=[ft.DropdownOption("model"), ft.DropdownOption("dataset"), ft.DropdownOption("space")],
        width=120, dense=True, height=STANDARD_CONTROL_HEIGHT, text_size=12,
        content_padding=STD_PADDING, border_radius=STD_RADIUS
    )
    tf_branch = ft.TextField(
        value="main", width=80,
        dense=True, height=STANDARD_CONTROL_HEIGHT, text_size=12,
        content_padding=STD_PADDING, border_radius=STD_RADIUS
    )

    dd_mirror = ft.Dropdown(
        value=mirrors_list[0] if mirrors_list else DEFAULT_MIRRORS[0],
        options=[ft.DropdownOption(m) for m in mirrors_list],
        expand=3, dense=True, height=STANDARD_CONTROL_HEIGHT, text_size=12,
        content_padding=STD_PADDING, border_radius=STD_RADIUS,
        on_select=lambda e: save_settings()
    )
    tf_token = ft.TextField(
        hint_text="HF Token (私有/受限模型填写，无则留空)", value=saved_token, password=True, can_reveal_password=True,
        expand=2, dense=True, height=STANDARD_CONTROL_HEIGHT, text_size=12,
        content_padding=STD_PADDING, border_radius=STD_RADIUS,
        on_change=lambda e: save_settings()
    )

    dd_proxy = ft.Dropdown(
        value=saved_proxy if saved_proxy in proxies_list else proxies_list[0],
        options=[ft.DropdownOption(p) for p in proxies_list],
        expand=3, dense=True, height=STANDARD_CONTROL_HEIGHT, text_size=12,
        content_padding=STD_PADDING, border_radius=STD_RADIUS,
        on_select=lambda e: save_settings()
    )

    # Preset Directory
    preset_keys = list(PRESET_DIRS_MAP.keys())
    tf_dest_path = ft.TextField(
        value=PRESET_DIRS_MAP[preset_keys[0]],
        expand=True, dense=True, height=STANDARD_CONTROL_HEIGHT, text_size=12,
        content_padding=STD_PADDING, border_radius=STD_RADIUS
    )
    
    def on_preset_change(e):
        if dd_preset.value in PRESET_DIRS_MAP:
            tf_dest_path.value = PRESET_DIRS_MAP[dd_preset.value]
            page.update()

    dd_preset = ft.Dropdown(
        value=preset_keys[0],
        options=[ft.DropdownOption(k) for k in preset_keys],
        width=250, dense=True, height=STANDARD_CONTROL_HEIGHT, text_size=12,
        content_padding=STD_PADDING, border_radius=STD_RADIUS,
        on_select=on_preset_change
    )
    cb_flatten = ft.Checkbox(label="扁平化保存", value=True, scale=0.88)

    # Standard Toolbar Controls
    lbl_checked_files = ft.Text("[已勾选: 0 项]", weight=ft.FontWeight.BOLD, color=COLOR_SUCCESS, size=13)
    lbl_current_dir = ft.Text("当前位置: / (根目录)", weight=ft.FontWeight.BOLD, color=COLOR_ACCENT, size=13)

    # Progress & Status
    pb_global = ft.ProgressBar(value=0.0, height=6, expand=True)
    lbl_global_pct = ft.Text("进度: 0.0%", weight=ft.FontWeight.BOLD, size=13)
    lbl_global_speed = ft.Text("速度: 0 KB/s", size=13)
    lbl_global_status = ft.Text("状态: 就绪", size=13)

    log_text = ft.TextField(multiline=True, read_only=True, expand=True, text_size=12, text_style=ft.TextStyle(font_family="Consolas"))

    # Containers for Dynamic Views
    col_dir_list = ft.ListView(expand=True, spacing=2, padding=ft.Padding.all(4))
    col_file_list = ft.ListView(expand=True, spacing=2, padding=ft.Padding.all(4))
    col_queue_list = ft.ListView(expand=True, spacing=3, padding=ft.Padding.all(4))

    def apply_theme_colors():
        eff_mode = page.theme_mode
        if eff_mode == ft.ThemeMode.SYSTEM:
            eff_mode = get_windows_system_theme()
        if eff_mode == ft.ThemeMode.LIGHT:
            page.bgcolor = "#f1f5f9"  # Windows Fluent Soft Slate Gray
        else:
            page.bgcolor = "#090d16"  # Deep Space Slate Dark

    # ------------------ Actions ------------------
    def toggle_theme(e):
        nonlocal current_theme_pref
        if current_theme_pref == "system":
            current_theme_pref = "dark"
            page.theme_mode = ft.ThemeMode.DARK
            btn_theme.icon = ft.Icons.DARK_MODE
            btn_theme.tooltip = "当前: 暗黑模式 (点击切换为明亮模式)"
            show_snack("已切换为: 🌙 暗黑模式")
        elif current_theme_pref == "dark":
            current_theme_pref = "light"
            page.theme_mode = ft.ThemeMode.LIGHT
            btn_theme.icon = ft.Icons.LIGHT_MODE
            btn_theme.tooltip = "当前: 明亮模式 (点击切换为跟随系统)"
            show_snack("已切换为: 🌞 明亮模式 (Windows 烟灰质感)")
        else:
            current_theme_pref = "system"
            sys_mode = get_windows_system_theme()
            page.theme_mode = sys_mode
            btn_theme.icon = ft.Icons.BRIGHTNESS_AUTO
            sys_desc = "暗黑" if sys_mode == ft.ThemeMode.DARK else "明亮浅灰"
            btn_theme.tooltip = f"当前: 跟随系统模式 (系统当前为: {sys_desc})"
            show_snack(f"已切换为: 💻 跟随系统模式 (当前为 {sys_desc})")
        apply_theme_colors()
        save_settings()
        page.update()

    # Initial tooltip & icon for theme button
    initial_icon = ft.Icons.BRIGHTNESS_AUTO if current_theme_pref == "system" else (ft.Icons.DARK_MODE if current_theme_pref == "dark" else ft.Icons.LIGHT_MODE)
    btn_theme = ft.IconButton(icon=initial_icon, tooltip=f"当前主题: {current_theme_pref} (点击切换)", on_click=toggle_theme)
    apply_theme_colors()

    def test_proxy(e):
        proxy = get_effective_proxy()
        endpoint = (dd_mirror.value or "https://hf-mirror.com").rstrip("/")
        test_url = f"{endpoint}/api/models"
        log(f"[*] 正在测试网络与代理 -> 目标: {endpoint} | 代理: {proxy or '直连'}...")

        def _worker():
            proxies = {"http": proxy, "https": proxy} if proxy else None
            start_t = time.time()
            try:
                resp = requests.get(test_url, proxies=proxies, timeout=8, headers={"User-Agent": "HF-Flet-Downloader"})
                cost = (time.time() - start_t) * 1000
                if resp.status_code in (200, 401, 403):
                    show_snack(f"网络连接畅通！响应延迟: {cost:.0f} ms (HTTP {resp.status_code})")
                    log(f"[✓] 连通性通过! 延迟: {cost:.0f} ms")
                else:
                    show_snack(f"连接警告: HTTP {resp.status_code}", is_error=True)
            except Exception as err:
                show_snack(f"连接失败: {str(err)}", is_error=True)
                log(f"[✗] 连接失败: {str(err)}")

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------ Fetch Files & Auto-Linkage ------------------
    def start_fetch(e=None):
        repo_id = tf_repo.value.strip()
        if not repo_id:
            show_snack("请输入 Repo ID！", is_error=True)
            return

        btn_fetch.disabled = True
        lbl_global_status.value = "状态: 正在获取仓库文件列表与目录树..."
        page.update()
        log(f"[*] 开始获取仓库 '{repo_id}' 的文件列表...")

        def _worker():
            nonlocal raw_files_dict, current_selected_dir
            repo_type = dd_type.value or "model"
            branch = tf_branch.value.strip() or "main"
            endpoint = (dd_mirror.value or "https://hf-mirror.com").rstrip("/")
            token = tf_token.value.strip() or None
            proxies = get_request_proxies()

            files_map = {}
            err_msg = None

            try:
                api = HfApi(endpoint=endpoint, token=token, proxies=proxies)
                tree = list(api.list_repo_tree(repo_id, repo_type=repo_type, revision=branch, recursive=True, expand=True))
                for item in tree:
                    if getattr(item, "type", None) == "directory":
                        continue
                    if getattr(item, "size", None) is not None or getattr(item, "lfs", None) is not None:
                        rfilename = item.path
                        raw_size = getattr(item, "size", None)
                        lfs_info = getattr(item, "lfs", None)
                        if lfs_info:
                            lfs_size = getattr(lfs_info, "size", None) if not isinstance(lfs_info, dict) else lfs_info.get("size")
                            if lfs_size is not None and lfs_size > 0:
                                raw_size = lfs_size
                        
                        size_str = format_size(raw_size)
                        last_commit = getattr(item, "last_commit", None)
                        raw_date = getattr(last_commit, "date", None) if last_commit else None
                        date_str = format_date(raw_date)

                        files_map[rfilename] = {
                            "path": rfilename,
                            "size_str": size_str,
                            "date_str": date_str,
                            "raw_size": raw_size or 0,
                            "raw_date": raw_date
                        }
            except Exception as e1:
                err_msg = str(e1)

            if not files_map:
                try:
                    base_type = "models" if repo_type == "model" else (repo_type + "s" if not repo_type.endswith("s") else repo_type)
                    api_url = f"{endpoint}/api/{base_type}/{repo_id}/tree/{branch}?recursive=True"
                    headers = {"User-Agent": "HF-Downloader-Flet/1.0"}
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
                                    
                                    size_str = format_size(raw_size)
                                    last_mod = item.get("lastModified")
                                    date_str = format_date(last_mod)
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

            if files_map:
                raw_files_dict = files_map
                checked_files.clear()
                collapsed_dirs.clear()
                
                # Auto-link to controlnet or root
                if any(f.startswith("controlnet/") for f in files_map):
                    current_selected_dir = "controlnet"
                else:
                    current_selected_dir = ""

                log(f"[✓] 成功获取到 {len(files_map)} 个文件！已自动联动展示目录树与文件列表。")
                show_snack(f"成功获取到 {len(files_map)} 个文件！已自动联动展示。")
                lbl_global_status.value = f"状态: 共获取到 {len(files_map)} 个文件"
                
                # Switch to browser view automatically
                switch_to_tab("browse")
                refresh_dir_tree()
                refresh_files_view()
            else:
                log(f"[✗] 获取失败: {err_msg}")
                show_snack(f"获取失败: {err_msg}", is_error=True)
                lbl_global_status.value = "状态: 获取文件列表失败"

            btn_fetch.disabled = False
            page.update()

        threading.Thread(target=_worker, daemon=True).start()

    btn_fetch = ft.ElevatedButton(
        "获取文件列表", icon=ft.Icons.SEARCH,
        on_click=start_fetch, height=38
    )

    # ------------------ Hierarchical Directory Tree with ▶/▼ Toggle ------------------
    def toggle_dir_collapse(d: str):
        if d in collapsed_dirs:
            collapsed_dirs.remove(d)
        else:
            collapsed_dirs.add(d)
        refresh_dir_tree()

    def refresh_dir_tree():
        col_dir_list.controls.clear()
        
        # Collect all directories
        all_dirs = set()
        for fpath in raw_files_dict.keys():
            parts = fpath.split("/")
            for i in range(1, len(parts)):
                all_dirs.add("/".join(parts[:i]))

        sorted_dirs = [""] + sorted(list(all_dirs))

        # Build parent -> children map
        has_children_map = {}
        for d in sorted_dirs:
            if d == "":
                has_children_map[d] = len(sorted_dirs) > 1
            else:
                has_children_map[d] = any(other.startswith(d + "/") for other in sorted_dirs)

        def make_dir_click(d):
            def _handler(e):
                nonlocal current_selected_dir
                current_selected_dir = d
                refresh_dir_tree()
                refresh_files_view()
            return _handler

        def make_toggle_click(d):
            def _handler(e):
                e.control.parent.on_click = None  # prevent propagation
                toggle_dir_collapse(d)
            return _handler

        for d in sorted_dirs:
            # Check if any parent of d is collapsed
            if d != "":
                parts = d.split("/")
                is_hidden = False
                for i in range(1, len(parts)):
                    parent_p = "/".join(parts[:i])
                    if parent_p in collapsed_dirs:
                        is_hidden = True
                        break
                if is_hidden:
                    continue

            if d == "":
                label = "/ 全部文件 (根目录)"
                depth = 0
                icon = ft.Icons.FOLDER_SPECIAL
            else:
                parts = d.split("/")
                label = parts[-1]
                depth = len(parts)
                icon = ft.Icons.FOLDER_OPEN if d == current_selected_dir else ft.Icons.FOLDER

            is_active = (d == current_selected_dir)
            indent_px = depth * 14
            has_children = has_children_map.get(d, False)
            is_collapsed = d in collapsed_dirs

            # Toggle arrow or spacer
            if has_children:
                arrow_icon = ft.Icons.ARROW_RIGHT if is_collapsed else ft.Icons.ARROW_DROP_DOWN
                btn_arrow = ft.IconButton(
                    icon=arrow_icon,
                    icon_size=16,
                    width=22, height=22,
                    padding=0,
                    tooltip="折叠/展开子目录",
                    on_click=make_toggle_click(d)
                )
            else:
                btn_arrow = ft.Container(width=22)

            col_dir_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        btn_arrow,
                        ft.Icon(icon, size=18, color=COLOR_WARNING if not is_active else COLOR_ACCENT),
                        ft.Text(label, size=13, weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL, expand=True)
                    ], spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    border=ft.Border.all(1, COLOR_ACCENT if is_active else ft.Colors.TRANSPARENT),
                    border_radius=4,
                    padding=ft.Padding.only(left=4 + indent_px, top=3, bottom=3, right=6),
                    on_click=make_dir_click(d),
                    ink=True
                )
            )
        page.update()

    # ------------------ Ultra-Compact File Table ------------------
    def quick_single_download(fpath: str):
        checked_files.clear()
        checked_files.add(fpath)
        add_to_queue(jump=True)

    def refresh_files_view():
        col_file_list.controls.clear()
        lbl_current_dir.value = f"当前位置: {'/ (根目录)' if not current_selected_dir else '/' + current_selected_dir}"

        matched = []
        for fpath, meta in raw_files_dict.items():
            if not current_selected_dir:
                if "/" in fpath:
                    continue
            else:
                prefix = current_selected_dir + "/"
                if not fpath.startswith(prefix):
                    continue

            matched.append((fpath, meta))

        matched.sort(key=lambda x: x[0])

        def make_row_click(fp):
            def _handler(e):
                if fp in checked_files:
                    checked_files.remove(fp)
                else:
                    checked_files.add(fp)
                lbl_checked_files.value = f"[已勾选: {len(checked_files)} 项]"
                refresh_files_view()
            return _handler

        def make_chk_change(fp):
            def _handler(e):
                if e.control.value:
                    checked_files.add(fp)
                else:
                    checked_files.discard(fp)
                lbl_checked_files.value = f"[已勾选: {len(checked_files)} 项]"
                refresh_files_view()
            return _handler

        # Header Row
        col_file_list.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text("选择", width=38, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("文件名 / 相对路径 (点击整行切换勾选)", expand=True, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("文件大小", width=95, text_align=ft.TextAlign.RIGHT, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("更新日期", width=130, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("操作", width=65, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD, size=12),
                ]),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=8, vertical=6)
            )
        )

        for idx, (fpath, meta) in enumerate(matched):
            fname = os.path.basename(fpath)
            is_chk = fpath in checked_files
            ext = os.path.splitext(fname)[1].lower()
            
            icon = ft.Icons.INVENTORY_2 if ext in (".safetensors", ".bin", ".pt", ".pth", ".onnx", ".ckpt", ".gguf") else ft.Icons.DESCRIPTION
            icon_color = COLOR_WARNING if icon == ft.Icons.INVENTORY_2 else COLOR_ACCENT

            col_file_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Checkbox(value=is_chk, on_change=make_chk_change(fpath), scale=0.85),
                        ft.Icon(icon, size=18, color=icon_color),
                        ft.Text(fname, expand=True, size=13, weight=ft.FontWeight.BOLD if is_chk else ft.FontWeight.NORMAL),
                        ft.Text(meta["size_str"], width=95, text_align=ft.TextAlign.RIGHT, size=12, color=COLOR_SUCCESS, weight=ft.FontWeight.BOLD),
                        ft.Text(meta["date_str"], width=130, text_align=ft.TextAlign.CENTER, size=12),
                        ft.IconButton(
                            icon=ft.Icons.DOWNLOAD,
                            icon_size=16,
                            tooltip="加入队列并立即下载",
                            on_click=lambda e, fp=fpath: quick_single_download(fp)
                        )
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    border=ft.Border.all(1, COLOR_ACCENT if is_chk else ft.Colors.TRANSPARENT),
                    border_radius=4,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    on_click=make_row_click(fpath),
                    ink=True
                )
            )

        lbl_checked_files.value = f"[已勾选: {len(checked_files)} 项]"
        page.update()

    def check_all_visible(e):
        for fpath in raw_files_dict.keys():
            if not current_selected_dir:
                if "/" in fpath:
                    continue
            else:
                prefix = current_selected_dir + "/"
                if not fpath.startswith(prefix):
                    continue
            checked_files.add(fpath)
        refresh_files_view()

    def uncheck_all_visible(e):
        checked_files.clear()
        refresh_files_view()

    # ------------------ Queue Management ------------------
    def add_to_queue(jump: bool = False):
        target_fpaths = list(checked_files)
        if not target_fpaths:
            show_snack("请先勾选需要下载的文件！", is_error=True)
            return

        dest_dir = tf_dest_path.value.strip()
        if not dest_dir:
            show_snack("请设置目标保存路径！", is_error=True)
            return

        repo_id = tf_repo.value.strip()
        repo_type = dd_type.value or "model"
        branch = tf_branch.value.strip() or "main"
        endpoint = (dd_mirror.value or "https://hf-mirror.com").rstrip("/")
        token = tf_token.value.strip() or None
        proxy = get_effective_proxy()
        flatten = cb_flatten.value

        nonlocal task_counter
        added = 0
        for fpath in sorted(target_fpaths):
            if any(t.repo_id == repo_id and t.file_path == fpath and t.dest_dir == dest_dir for t in tasks):
                continue

            meta = raw_files_dict.get(fpath, {})
            task = QueueTask(
                task_id=task_counter,
                repo_id=repo_id,
                repo_type=repo_type,
                branch=branch,
                file_path=fpath,
                size_str=meta.get("size_str", "--"),
                date_str=meta.get("date_str", "--"),
                dest_dir=dest_dir,
                flatten=flatten,
                endpoint=endpoint,
                token=token,
                proxy=proxy,
                total_bytes=meta.get("raw_size")
            )
            task.check_local_status()
            tasks.append(task)
            task_counter += 1
            added += 1

        save_tasks()
        refresh_queue_view()
        show_snack(f"已成功将 {added} 个文件加入下载队列！")
        log(f"[+] 已加入 {added} 个任务 -> 目标: {dest_dir}")

        if jump:
            switch_to_tab("queue")

    def add_dir_to_queue(e):
        matched = []
        for fpath in raw_files_dict.keys():
            if current_selected_dir:
                if fpath == current_selected_dir or fpath.startswith(current_selected_dir + "/"):
                    matched.append(fpath)
            else:
                matched.append(fpath)

        for fp in matched:
            checked_files.add(fp)
        add_to_queue(jump=False)

    def refresh_queue_view():
        col_queue_list.controls.clear()
        
        for task in tasks:
            status_color = COLOR_SUCCESS if task.status == "已完成" else (
                COLOR_ACCENT if task.status == "下载中" else (
                    COLOR_WARNING if task.status == "已中断" else ft.Colors.GREY_600
                )
            )

            is_chk = task.task_id in checked_tasks

            def make_task_chk(tid):
                def _handler(e):
                    if e.control.value:
                        checked_tasks.add(tid)
                    else:
                        checked_tasks.discard(tid)
                    page.update()
                return _handler

            col_queue_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Checkbox(value=is_chk, on_change=make_task_chk(task.task_id), scale=0.85),
                            ft.Text(f"#{task.task_id}", weight=ft.FontWeight.BOLD, size=12),
                            ft.Text(os.path.basename(task.file_path), expand=True, weight=ft.FontWeight.BOLD, size=13),
                            ft.Container(
                                content=ft.Text(task.status, size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                                bgcolor=status_color,
                                border_radius=4,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=2)
                            ),
                            ft.Text(f"{task.progress:.1f}%", width=55, text_align=ft.TextAlign.RIGHT, weight=ft.FontWeight.BOLD, size=13),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.ProgressBar(value=task.progress / 100.0, height=4, color=status_color),
                        ft.Row([
                            ft.Text(f"大小: {task.size_str} | 目标: {task.dest_dir}", size=11, expand=True),
                            ft.Text(f"速率: {task.speed_str}", size=11, color=COLOR_SUCCESS, weight=ft.FontWeight.BOLD),
                        ])
                    ], spacing=3),
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=6)
                )
            )
        update_queue_tab_badge()
        page.update()

    # ------------------ Download Engine Loop ------------------
    def start_queue(e):
        nonlocal is_queue_running, stop_queue_requested
        if is_queue_running:
            return

        has_selection = bool(checked_tasks)
        if has_selection:
            pending = [t for t in tasks if t.task_id in checked_tasks and t.status in ("等待中", "已中断", "已暂停", "失败")]
            if not pending:
                sel_tasks = [t for t in tasks if t.task_id in checked_tasks]
                if sel_tasks and all(t.status == "已完成" for t in sel_tasks):
                    for t in sel_tasks:
                        t.clean_local_files_and_caches()
                        t.status = "等待中"
                        t.progress = 0.0
                    refresh_queue_view()
                    save_tasks()
                    pending = sel_tasks
                    show_snack("已重置勾选的已完成任务并开始重新下载。")
                else:
                    show_snack("所勾选的任务中没有需要下载的任务。")
                    return
        else:
            pending = [t for t in tasks if t.status in ("等待中", "已中断", "已暂停", "失败")]
            if not pending:
                show_snack("当前队列中没有需要下载的任务。")
                return

        is_queue_running = True
        stop_queue_requested = False
        btn_start_q.disabled = True
        btn_stop_q.disabled = False
        
        mode_str = f"勾选的 {len(pending)} 个任务" if has_selection else f"全队列 ({len(pending)} 个任务)"
        lbl_global_status.value = f"状态: 正在下载 [{mode_str}]..."
        page.update()
        log(f"\n[*] 启动下载队列: 目标为 {mode_str}...")

        threading.Thread(target=_queue_worker, daemon=True).start()

    def stop_queue(e):
        nonlocal stop_queue_requested, cancel_current_task
        if not is_queue_running:
            if checked_tasks:
                for t in tasks:
                    if t.task_id in checked_tasks and t.status in ("等待中", "下载中"):
                        t.status = "已暂停"
                refresh_queue_view()
                save_tasks()
                show_snack(f"已将勾选的 {len(checked_tasks)} 个任务标记为已暂停。")
            return

        has_selection = bool(checked_tasks)
        if has_selection:
            for t in tasks:
                if t.task_id in checked_tasks:
                    if t.status == "下载中":
                        cancel_current_task = True
                    t.status = "已暂停"
            refresh_queue_view()
            save_tasks()
            if not active_task_id or active_task_id in checked_tasks:
                stop_queue_requested = True
                reset_global_progress("已暂停勾选的任务")
                log("[!] 收到指令，已暂停勾选的任务。")
        else:
            stop_queue_requested = True
            cancel_current_task = True
            reset_global_progress("正在终止队列...")
            log("[!] 收到终止指令，已中断当前任务并保存进度。")

    def _queue_worker():
        nonlocal is_queue_running, active_task_id
        log("\n================ 启动断点续传队列 ================")

        while is_queue_running and not stop_queue_requested:
            current_task = None
            has_selection = bool(checked_tasks)

            for t in tasks:
                if has_selection:
                    if t.task_id in checked_tasks and t.status in ("等待中", "已中断", "已暂停", "失败"):
                        current_task = t
                        break
                else:
                    if t.status in ("等待中", "已中断", "已暂停", "失败"):
                        current_task = t
                        break

            if not current_task:
                break

            active_task_id = current_task.task_id
            current_task.status = "下载中"
            refresh_queue_view()
            save_tasks()

            target_file_path = current_task.get_dest_file_path()
            os.makedirs(os.path.dirname(target_file_path), exist_ok=True)

            if current_task.repo_type == "model":
                download_url = f"{current_task.endpoint}/{current_task.repo_id}/resolve/{current_task.branch}/{current_task.file_path}"
            elif current_task.repo_type == "dataset":
                download_url = f"{current_task.endpoint}/datasets/{current_task.repo_id}/resolve/{current_task.branch}/{current_task.file_path}"
            else:
                download_url = f"{current_task.endpoint}/spaces/{current_task.repo_id}/resolve/{current_task.branch}/{current_task.file_path}"

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HF-Downloader/1.0"}
            if current_task.token:
                headers["Authorization"] = f"Bearer {current_task.token}"

            proxy_str = current_task.proxy or get_effective_proxy()
            proxies = {"http": proxy_str, "https": proxy_str} if proxy_str else None

            log(f"[任务 #{current_task.task_id}] 开始下载: {os.path.basename(current_task.file_path)} (代理: {proxy_str or '直连'})")

            success = _stream_download(download_url, target_file_path, headers, proxies, current_task)

            if stop_queue_requested or cancel_current_task:
                current_task.status = "已中断"
                log(f"[!] 任务 #{current_task.task_id} 已中断，进度已保留。")
            elif success:
                current_task.status = "已完成"
                current_task.progress = 100.0
                log(f"[✓] 任务 #{current_task.task_id} 下载完成！")
            else:
                current_task.status = "失败"
                log(f"[✗] 任务 #{current_task.task_id} 失败: {current_task.error_msg}")

            active_task_id = None
            refresh_queue_view()
            save_tasks()

        is_queue_running = False
        btn_start_q.disabled = False
        btn_stop_q.disabled = True
        reset_global_progress("队列运行结束")

    def _stream_download(url: str, local_path: str, headers: dict, proxies: Optional[dict], task: QueueTask) -> bool:
        nonlocal cancel_current_task
        temp_path = local_path + ".downloading"
        chunk_size = 1024 * 1024

        req_headers = headers.copy()
        downloaded_bytes = 0

        if os.path.exists(temp_path):
            downloaded_bytes = os.path.getsize(temp_path)
            if downloaded_bytes > 0:
                req_headers["Range"] = f"bytes={downloaded_bytes}-"

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
                last_update = start_time
                bytes_since = 0

                with open(temp_path, mode) as f:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if cancel_current_task or stop_queue_requested:
                            task.error_msg = "用户取消"
                            return False
                        if chunk:
                            f.write(chunk)
                            downloaded_bytes += len(chunk)
                            bytes_since += len(chunk)

                            now = time.time()
                            if now - last_update >= 0.3:
                                dt = now - last_update
                                speed_bps = bytes_since / dt
                                speed_str = format_size(int(speed_bps)) + "/s"
                                
                                if total_size and total_size > 0:
                                    pct = min(100.0, (downloaded_bytes / total_size) * 100.0)
                                    rem_bytes = max(0, total_size - downloaded_bytes)
                                    eta_sec = int(rem_bytes / speed_bps) if speed_bps > 0 else 0
                                    eta_str = f"{eta_sec // 60}分{eta_sec % 60}秒" if eta_sec > 60 else f"{eta_sec}秒"
                                    
                                    task.progress = pct
                                    task.speed_str = speed_str
                                    task.eta_str = eta_str

                                    pb_global.value = pct / 100.0
                                    lbl_global_pct.value = f"进度: {pct:.1f}% ({format_size(downloaded_bytes)} / {format_size(total_size)})"
                                    lbl_global_speed.value = f"速度: {speed_str} | 预估剩余: {eta_str}"
                                    page.update()

                                last_update = now
                                bytes_since = 0

            if os.path.exists(local_path):
                os.remove(local_path)
            os.rename(temp_path, local_path)
            return True

        except Exception as e:
            task.error_msg = str(e)
            return False

    # ------------------ Safe Deletion Dialog ------------------
    def delete_checked_tasks(e):
        target_ids = list(checked_tasks)
        if not target_ids:
            show_snack("请先勾选需要移除的任务！", is_error=True)
            return

        target_tasks = [t for t in tasks if t.task_id in target_ids]

        def do_delete_all(e_dlg):
            dlg_confirm.open = False
            page.update()
            
            def execute_real_delete(e_sec):
                dlg_sec.open = False
                page.update()
                
                del_files = 0
                for t in target_tasks:
                    paths = t.clean_local_files_and_caches()
                    del_files += len(paths)
                
                nonlocal tasks
                tasks = [t for t in tasks if t.task_id not in target_ids]
                checked_tasks.clear()
                save_tasks()
                refresh_queue_view()
                show_snack(f"已彻底删除 {len(target_tasks)} 个任务及 {del_files} 个本地文件与缓存！")

            dlg_sec = ft.AlertDialog(
                title=ft.Text("⚠️ 高风险物理删除二次确认", color=COLOR_DANGER),
                content=ft.Text(f"即将从硬盘彻底物理删除 {len(target_tasks)} 个任务的本地实体文件及未完成缓存！\n此操作不可恢复，确定继续吗？"),
                actions=[
                    ft.TextButton("取消", on_click=lambda e: setattr(dlg_sec, "open", False) or page.update()),
                    ft.ElevatedButton("确定物理删除", bgcolor=COLOR_DANGER, color=ft.Colors.WHITE, on_click=execute_real_delete)
                ]
            )
            page.overlay.append(dlg_sec)
            dlg_sec.open = True
            page.update()

        def do_queue_only(e_dlg):
            dlg_confirm.open = False
            nonlocal tasks
            tasks = [t for t in tasks if t.task_id not in target_ids]
            checked_tasks.clear()
            save_tasks()
            refresh_queue_view()
            show_snack(f"已从队列移除 {len(target_tasks)} 个任务 (本地文件已保留)。")

        dlg_confirm = ft.AlertDialog(
            title=ft.Text("⚠️ 确认移除下载任务"),
            content=ft.Text(f"准备从队列中移除 {len(target_tasks)} 个任务。\n请选择移除方式："),
            actions=[
                ft.ElevatedButton("🗑️ 彻底删除 (任务 + 实体文件与缓存)", bgcolor=COLOR_DANGER, color=ft.Colors.WHITE, on_click=do_delete_all),
                ft.ElevatedButton("📋 仅移除任务记录 (保留本地文件)", on_click=do_queue_only),
                ft.TextButton("取消", on_click=lambda e: setattr(dlg_confirm, "open", False) or page.update()),
            ]
        )
        page.overlay.append(dlg_confirm)
        dlg_confirm.open = True
        page.update()

    def clear_completed(e):
        nonlocal tasks
        done = [t for t in tasks if t.status == "已完成"]
        if not done:
            show_snack("没有已完成的任务。")
            return
        tasks = [t for t in tasks if t.status != "已完成"]
        save_tasks()
        refresh_queue_view()
        show_snack(f"已清理 {len(done)} 个已完成任务。")

    def open_dest_folder(e):
        if tasks:
            t = tasks[0]
            if os.path.exists(t.dest_dir):
                os.startfile(t.dest_dir)
            else:
                show_snack(f"目录尚未创建: {t.dest_dir}")

    # Buttons in Queue Tab (Standard Action Height: 38px)
    btn_start_q = ft.ElevatedButton("开始/恢复队列", icon=ft.Icons.PLAY_ARROW, bgcolor=COLOR_SUCCESS, color=ft.Colors.WHITE, on_click=start_queue, height=38)
    btn_stop_q = ft.ElevatedButton("暂停/终止队列", icon=ft.Icons.PAUSE, bgcolor=COLOR_WARNING, color=ft.Colors.WHITE, disabled=True, on_click=stop_queue, height=38)

    # Assemble Top Configuration Card (Strict 36px Height Grid)
    top_config_container = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("仓库:", size=13, weight=ft.FontWeight.BOLD), tf_repo,
                ft.Text("类型:", size=13, weight=ft.FontWeight.BOLD), dd_type,
                ft.Text("分支:", size=13, weight=ft.FontWeight.BOLD), tf_branch,
                btn_fetch
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("镜像:", size=13, weight=ft.FontWeight.BOLD), dd_mirror,
                ft.Text("Token:", size=13, weight=ft.FontWeight.BOLD), tf_token
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("代理:", size=13, weight=ft.FontWeight.BOLD), dd_proxy,
                ft.ElevatedButton("检测代理连通性", icon=ft.Icons.BOLT, on_click=test_proxy, height=38)
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("预设:", size=13, weight=ft.FontWeight.BOLD), dd_preset,
                ft.Text("路径:", size=13, weight=ft.FontWeight.BOLD), tf_dest_path,
                cb_flatten
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=6),
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        padding=10
    )

    # Browser tab view includes the top configuration card + breadcrumb + dual-pane explorer + action buttons
    tab_browser_view = ft.Column([
        top_config_container,
        ft.Container(
            content=ft.Row([
                lbl_current_dir,
                lbl_checked_files,
                ft.Container(expand=True),
                ft.ElevatedButton("全选可见", icon=ft.Icons.SELECT_ALL, on_click=check_all_visible, height=36),
                ft.ElevatedButton("取消勾选", icon=ft.Icons.DESELECT, on_click=uncheck_all_visible, height=36),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(horizontal=4, vertical=2)
        ),
        ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Text("📁 仓库目录层级树 (点击 ▶/▼ 折叠展开)", weight=ft.FontWeight.BOLD, size=12),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=7)
                    ),
                    col_dir_list
                ], expand=True),
                width=300, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=6
            ),
            ft.Container(
                content=col_file_list,
                expand=True, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=6
            )
        ], expand=True, spacing=6),
        ft.Row([
            ft.ElevatedButton("加入下载队列", icon=ft.Icons.DOWNLOAD, bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE, on_click=lambda e: add_to_queue(False), height=38),
            ft.ElevatedButton("目录整包入队", icon=ft.Icons.FOLDER_ZIP, on_click=add_dir_to_queue, height=38),
            ft.ElevatedButton("入队并跳转到队列", icon=ft.Icons.ROCKET_LAUNCH, on_click=lambda e: add_to_queue(True), height=38),
        ], spacing=8)
    ], expand=True, spacing=6)

    tab_queue_view = ft.Column([
        ft.Container(
            content=ft.Row([
                btn_start_q,
                btn_stop_q,
                ft.ElevatedButton("移除勾选任务", icon=ft.Icons.DELETE, on_click=delete_checked_tasks, height=38),
                ft.ElevatedButton("清理已完成", icon=ft.Icons.CLEANING_SERVICES, on_click=clear_completed, height=38),
                ft.ElevatedButton("打开保存目录", icon=ft.Icons.FOLDER_OPEN, on_click=open_dest_folder, height=38),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(vertical=4)
        ),
        ft.Container(content=col_queue_list, expand=True, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=6),
        ft.Container(content=log_text, height=120, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=6, padding=4)
    ], expand=True, spacing=6)

    # ------------------ Environment Deployment & Folder Manager Tab ------------------
    tf_comfy_root_input = ft.TextField(
        value=DEFAULT_COMFYUI_ROOT, expand=True, dense=True, height=38, text_size=12,
        content_padding=STD_PADDING, border_radius=STD_RADIUS
    )

    col_env_dirs = ft.ListView(expand=True, spacing=4, padding=ft.Padding.all(4))
    lbl_env_status = ft.Text("状态: 就绪", size=13, weight=ft.FontWeight.BOLD, color=COLOR_SUCCESS)

    def refresh_env_dirs_view():
        col_env_dirs.controls.clear()
        base_path = tf_comfy_root_input.value.strip()
        for label, rel_or_abs in PRESET_DIRS_MAP.items():
            folder_name = label.split("(")[-1].rstrip(")")
            target_path = os.path.join(base_path, folder_name) if not os.path.isabs(rel_or_abs) else rel_or_abs
            exists = os.path.exists(target_path)

            def make_open_dir(p):
                return lambda e: os.startfile(p) if os.path.exists(p) else show_snack(f"目录不存在: {p}", is_error=True)

            def make_create_dir(p):
                def _create(e):
                    try:
                        os.makedirs(p, exist_ok=True)
                        show_snack(f"成功创建目录: {p}")
                        refresh_env_dirs_view()
                    except Exception as err:
                        show_snack(f"创建失败: {str(err)}", is_error=True)
                return _create

            status_chip = ft.Container(
                content=ft.Text("已就绪" if exists else "未创建", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                bgcolor=COLOR_SUCCESS if exists else COLOR_WARNING,
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=8, vertical=2)
            )

            btn_action = ft.ElevatedButton(
                "打开目录", icon=ft.Icons.FOLDER_OPEN,
                on_click=make_open_dir(target_path), height=32,
                disabled=not exists
            )
            btn_create = ft.ElevatedButton(
                "创建", icon=ft.Icons.ADD,
                on_click=make_create_dir(target_path), height=32,
                visible=not exists
            )

            col_env_dirs.controls.append(
                ft.Container(
                    content=ft.Row([
                        status_chip,
                        ft.Text(label, width=220, weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(target_path, expand=True, size=12, color=COLOR_TEXT_SECONDARY),
                        btn_create,
                        btn_action
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4)
                )
            )
        page.update()

    def create_all_dirs(e):
        base_path = tf_comfy_root_input.value.strip()
        created_count = 0
        for label, rel_or_abs in PRESET_DIRS_MAP.items():
            folder_name = label.split("(")[-1].rstrip(")")
            target_path = os.path.join(base_path, folder_name) if not os.path.isabs(rel_or_abs) else rel_or_abs
            try:
                if not os.path.exists(target_path):
                    os.makedirs(target_path, exist_ok=True)
                    created_count += 1
            except Exception:
                pass
        refresh_env_dirs_view()
        show_snack(f"一键环境部署完成！共补齐/创建 {created_count} 个模型目录。")

    def auto_detect_comfy(e):
        candidates = [
            r"F:\ComfyUI-aki-v3\ComfyUI\models",
            r"D:\ComfyUI-aki-v3\ComfyUI\models",
            r"E:\ComfyUI-aki-v3\ComfyUI\models",
            r"C:\ComfyUI-aki-v3\ComfyUI\models",
            r"D:\ComfyUI\models",
            r"E:\ComfyUI\models",
            r"F:\ComfyUI\models",
        ]
        found = None
        for c in candidates:
            if os.path.exists(c):
                found = c
                break
        if found:
            tf_comfy_root_input.value = found
            # Update preset map root
            for k in PRESET_DIRS_MAP.keys():
                folder_name = k.split("(")[-1].rstrip(")")
                PRESET_DIRS_MAP[k] = os.path.join(found, folder_name)
            refresh_env_dirs_view()
            show_snack(f"已智能探测到 ComfyUI 路径: {found}")
        else:
            show_snack("未在常见盘符探测到 ComfyUI，请手动输入路径。", is_error=True)

    def install_pip_deps(e):
        lbl_env_status.value = "状态: 正在使用清华大学镜像源升级依赖..."
        page.update()

        def _worker():
            try:
                cmd = [sys.executable, "-m", "pip", "install", "-U", "flet", "requests", "huggingface_hub", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if res.returncode == 0:
                    show_snack("依赖环境检测与升级成功！")
                    lbl_env_status.value = "状态: 所有核心依赖均已是最新版"
                else:
                    show_snack(f"安装提示: {res.stderr[:80]}", is_error=True)
                    lbl_env_status.value = "状态: 安装完成 (带提示)"
            except Exception as err:
                show_snack(f"执行失败: {str(err)}", is_error=True)
                lbl_env_status.value = f"状态: 错误 ({str(err)})"
            page.update()

        threading.Thread(target=_worker, daemon=True).start()

    tab_env_view = ft.Column([
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("ComfyUI 模型根目录:", size=13, weight=ft.FontWeight.BOLD),
                    tf_comfy_root_input,
                    ft.ElevatedButton("智能探测", icon=ft.Icons.SEARCH, on_click=auto_detect_comfy, height=38),
                    ft.ElevatedButton("一键部署全部目录", icon=ft.Icons.PLAY_FOR_WORK, bgcolor=COLOR_SUCCESS, color=ft.Colors.WHITE, on_click=create_all_dirs, height=38),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.ElevatedButton("⚡ 一键检测与升级 Python 核心依赖 (清华源)", icon=ft.Icons.BOLT, on_click=install_pip_deps, height=36),
                    lbl_env_status
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=8),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=10
        ),
        ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("📁 ComfyUI 常用模型目录状态与快捷直达", weight=ft.FontWeight.BOLD, size=13),
                        ft.ElevatedButton("刷新状态", icon=ft.Icons.REFRESH, on_click=lambda e: refresh_env_dirs_view(), height=32)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4)
                ),
                col_env_dirs
            ], expand=True),
            expand=True,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=6
        )
    ], expand=True, spacing=6)

    content_area = ft.Container(content=tab_browser_view, expand=True)

    def update_queue_tab_badge():
        pending_cnt = sum(1 for t in tasks if t.status in ("等待中", "下载中", "已中断"))
        btn_nav_queue.text = f"下载任务队列 ({pending_cnt})"
        page.update()

    def switch_to_tab(tab_name: str):
        if tab_name == "browse":
            btn_nav_browse.style = ft.ButtonStyle(bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE)
            btn_nav_queue.style = None
            btn_nav_env.style = None
            content_area.content = tab_browser_view
        elif tab_name == "queue":
            btn_nav_browse.style = None
            btn_nav_queue.style = ft.ButtonStyle(bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE)
            btn_nav_env.style = None
            content_area.content = tab_queue_view
        else:
            btn_nav_browse.style = None
            btn_nav_queue.style = None
            btn_nav_env.style = ft.ButtonStyle(bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE)
            content_area.content = tab_env_view
            refresh_env_dirs_view()
        page.update()

    btn_nav_browse = ft.ElevatedButton(
        "仓库文件浏览器", icon=ft.Icons.FOLDER_COPY,
        style=ft.ButtonStyle(bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE),
        on_click=lambda e: switch_to_tab("browse"), height=38
    )
    btn_nav_queue = ft.ElevatedButton(
        "下载任务队列 (0)", icon=ft.Icons.FORMAT_LIST_BULLETED,
        on_click=lambda e: switch_to_tab("queue"), height=38
    )
    btn_nav_env = ft.ElevatedButton(
        "一键部署环境", icon=ft.Icons.CONSTRUCTION,
        on_click=lambda e: switch_to_tab("env"), height=38
    )

    btn_about = ft.IconButton(
        icon=ft.Icons.INFO_OUTLINE,
        tooltip="关于与使用说明",
        on_click=lambda e: show_snack("🚀 Hugging Face 极速多线程与断点续传下载器 (Pro Edition)")
    )

    nav_bar = ft.Container(
        content=ft.Row([
            btn_nav_browse,
            btn_nav_queue,
            btn_nav_env,
            ft.Container(expand=True),  # Push controls to the right
            btn_theme,
            btn_about
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(horizontal=4, vertical=2)
    )

    # Bottom Progress Card (Global Footer)
    bottom_prog_container = ft.Container(
        content=ft.Column([
            pb_global,
            ft.Row([lbl_global_pct, lbl_global_speed, lbl_global_status], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=4),
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=10, vertical=6)
    )

    page.add(
        nav_bar,
        content_area,
        bottom_prog_container
    )

    # Initial Loading of Tasks
    if os.path.exists(TASKS_DB_FILE):
        try:
            with open(TASKS_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                max_id = 0
                for td in data.get("tasks", []):
                    t = QueueTask.from_dict(td)
                    tasks.append(t)
                    if t.task_id > max_id:
                        max_id = t.task_id
                task_counter = max_id + 1
        except Exception:
            pass

    refresh_queue_view()
    log("✨ Flet 专业高颜值下载器引擎已就绪！")

if __name__ == "__main__":
    ft.run(main)
