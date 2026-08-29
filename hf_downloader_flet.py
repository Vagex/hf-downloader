import os
import sys
import time
import json
import datetime
from datetime import datetime
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
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
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
HISTORY_DB_FILE = os.path.join(CONFIG_DIR, "hf_downloader_history.json")

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

PRESET_DIRS_MAP = PresetDirectoryManager.load_presets()

# Default GitHub Accelerators
DEFAULT_GITHUB_ACCELERATORS = [
    "https://ghfast.top/",
    "https://ghproxy.net/",
    "https://mirror.ghproxy.com/",
    "https://github.moeyy.xyz/",
    "不使用加速 (官方直连)"
]

class TwitterMediaResolver:
    """High-reliability multi-engine parser for Twitter / X media."""

    @staticmethod
    def extract_tweet_id(raw_input: str) -> Optional[str]:
        if not raw_input:
            return None
        raw_input = raw_input.strip()
        # Clean URL query params if status id is followed by ?
        m = re.search(r'status/(\d+)', raw_input)
        if m:
            return m.group(1)
        m = re.search(r'^\d+$', raw_input)
        if m:
            return m.group(0)
        return None

    @classmethod
    def resolve(cls, raw_input: str, proxy: Optional[str] = None) -> Dict[str, Any]:
        """Resolves tweet media information with multiple fallback strategies."""
        tweet_id = cls.extract_tweet_id(raw_input)
        if not tweet_id and "http" not in raw_input:
            raise ValueError("请输入有效的 Twitter / X 推文链接或 Tweet ID！")

        target_url = f"https://twitter.com/i/status/{tweet_id}" if tweet_id else raw_input.strip()
        last_error_details = []

        # Strategy 1: yt-dlp deep resolution (Primary engine)
        try:
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
                if info:
                    title = info.get('description') or info.get('title') or f"Tweet {tweet_id or ''}"
                    uploader = info.get('uploader') or info.get('channel') or "Twitter 用户"
                    uploader_id = info.get('uploader_id') or info.get('channel_id') or ""
                    thumbnail = info.get('thumbnail')
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

                        if height:
                            if height >= 1080:
                                q_label = f"🎬 1080P 超清 ({width}x{height})"
                            elif height >= 720:
                                q_label = f"🎬 720P 高清 ({width}x{height})"
                            elif height >= 480:
                                q_label = f"🎬 480P 标清 ({width}x{height})"
                            elif height >= 360:
                                q_label = f"🎬 360P 流畅 ({width}x{height})"
                            else:
                                q_label = f"🎬 {height}P ({width}x{height})"
                        elif vcodec != 'none' and ('.mp4' in furl or furl.endswith('.mp4')):
                            q_label = "🎬 标准 MP4 视频"
                        elif acodec != 'none' and vcodec == 'none':
                            q_label = "🎵 仅提取音频 (Audio Stream)"
                        else:
                            continue

                        size_str = "--"
                        if filesize:
                            size_str = f"{filesize / (1024*1024):.2f} MB" if filesize >= 1024*1024 else f"{filesize/1024:.1f} KB"
                        elif tbr and info.get('duration'):
                            est = (tbr * 1000 / 8) * info.get('duration')
                            size_str = f"~{est / (1024*1024):.1f} MB"

                        bitrate_str = f"{int(tbr)} kbps" if tbr else "--"
                        clean_fn = re.sub(r'[\\/*?:"<>|]', '_', f"{uploader_id or 'twitter'}_{tweet_id or info.get('id')}_{height or 'video'}.mp4")

                        video_variants.append({
                            "quality": q_label,
                            "height": height or 0,
                            "bitrate": tbr or 0,
                            "bitrate_str": bitrate_str,
                            "size_str": size_str,
                            "raw_size": filesize or 0,
                            "url": furl,
                            "filename": clean_fn
                        })

                    video_variants.sort(key=lambda x: (x["height"], x["bitrate"]), reverse=True)

                    if video_variants:
                        return {
                            "tweet_id": tweet_id or str(info.get('id')),
                            "author": uploader,
                            "author_id": f"@{uploader_id}" if uploader_id else "",
                            "text": title.strip(),
                            "date": upload_date,
                            "duration": info.get('duration_string') or "--",
                            "thumbnail": thumbnail,
                            "variants": video_variants
                        }
        except Exception as e_ytdlp:
            last_error_details.append(f"yt-dlp: {str(e_ytdlp)}")

        # Strategy 2: Syndication API fallback (Pure requests)
        if tweet_id:
            try:
                api_url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&lang=en"
                proxies = {"http": proxy, "https": proxy} if proxy else None
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json"
                }
                resp = requests.get(api_url, headers=headers, proxies=proxies, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    user = data.get("user", {})
                    author = user.get("name", "Twitter 用户")
                    author_id = f"@{user.get('screen_name', '')}"
                    text = data.get("text", "")
                    raw_created = data.get("created_at")
                    pub_date = raw_created[:16].replace("T", " ") if raw_created else datetime.now().strftime("%Y-%m-%d %H:%M")

                    media_list = data.get("mediaDetails", [])
                    variants_list = []
                    for m in media_list:
                        v_info = m.get("video_info", {})
                        for var in v_info.get("variants", []):
                            if var.get("content_type") == "video/mp4":
                                br = var.get("bitrate", 0)
                                furl = var.get("url")
                                m_res = re.search(r'/(\d+)x(\d+)/', furl)
                                if m_res:
                                    w, h = int(m_res.group(1)), int(m_res.group(2))
                                    h_min = min(w, h)
                                    q_label = f"🎬 {h_min}P 高清 ({w}x{h})"
                                else:
                                    q_label = f"🎬 MP4 视频 ({br // 1000} kbps)"
                                
                                clean_fn = f"twitter_{user.get('screen_name', 'video')}_{tweet_id}_{br}.mp4"
                                variants_list.append({
                                    "quality": q_label,
                                    "height": br,
                                    "bitrate": br // 1000,
                                    "bitrate_str": f"{br // 1000} kbps",
                                    "size_str": "--",
                                    "raw_size": 0,
                                    "url": furl,
                                    "filename": clean_fn
                                })

                    variants_list.sort(key=lambda x: x["bitrate"], reverse=True)
                    if variants_list:
                        return {
                            "tweet_id": tweet_id,
                            "author": author,
                            "author_id": author_id,
                            "text": text,
                            "date": pub_date,
                            "duration": "--",
                            "thumbnail": None,
                            "variants": variants_list
                        }
            except Exception as e_syn:
                last_error_details.append(f"Syndication: {str(e_syn)}")

        err_summary = "; ".join(last_error_details) if last_error_details else "未检测到推文中的视频直链"
        raise ValueError(f"{err_summary} (请检查推文中是否包含视频，或确认是否已开启网络代理！)")


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
    saved_gh_token: str = ""
    saved_theme_pref: str = "system"  # 'system', 'dark', 'light'

    # Load Settings
    if os.path.exists(APP_CONFIG_FILE):
        try:
            with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                saved_proxy = data.get("proxy", "")
                saved_token = data.get("token", "")
                saved_gh_token = data.get("gh_token", "")
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
            gh_t_val = tf_gh_token.value.strip() if 'tf_gh_token' in locals() and tf_gh_token.value else saved_gh_token
            with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "proxy": p_val,
                    "token": t_val,
                    "gh_token": gh_t_val,
                    "theme_mode": current_theme_pref
                }, f, ensure_ascii=False, indent=2)
            if t_val:
                os.environ["HF_TOKEN"] = t_val
            if gh_t_val:
                os.environ["GITHUB_TOKEN"] = gh_t_val
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
        width=280, dense=True, height=STANDARD_CONTROL_HEIGHT, text_size=12,
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
            effective_proxy = get_effective_proxy()

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
                headers = {"User-Agent": "HF-Downloader-Flet/1.0"}
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                resp_info = requests.get(info_url, headers=headers, proxies=proxies, timeout=8)
                if resp_info.status_code == 200:
                    inf = resp_info.json()
                    raw_mod = inf.get("lastModified") or inf.get("createdAt")
                    if raw_mod:
                        repo_real_date_str = format_date(raw_mod)
            except Exception:
                pass

            try:
                api = HfApi(endpoint=endpoint, token=token)
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
                        if date_str in ("--", "未知", "None", ""):
                            date_str = repo_real_date_str if repo_real_date_str != "--" else datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

                        files_map[rfilename] = {
                            "path": rfilename,
                            "size_str": size_str,
                            "date_str": date_str,
                            "raw_size": raw_size or 0,
                            "raw_date": raw_date or repo_real_date_str
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
                                    if date_str in ("--", "未知", "None", ""):
                                        date_str = repo_real_date_str if repo_real_date_str != "--" else datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

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

            if files_map:
                raw_files_dict = files_map
                checked_files.clear()
                collapsed_dirs.clear()
                HistoryManager.record_access(repo_id, "huggingface", repo_type, branch, len(files_map))
                
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

                if current_task.repo_type == "github_zip" and target_file_path.endswith(".zip"):
                    try:
                        import zipfile
                        extract_dest = current_task.dest_dir
                        log(f"     [自动解压] 正在解压 {os.path.basename(target_file_path)} 至: {extract_dest}")
                        with zipfile.ZipFile(target_file_path, 'r') as zip_ref:
                            file_list = zip_ref.namelist()
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

                        log(f"     [✓] 解压完成！所有文件已收纳在独立目录: {extract_dest}")
                    except Exception as ze:
                        log(f"     [!] 自动解压提示: {str(ze)}")
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
            if cancel_current_task or stop_queue_requested:
                task.error_msg = "用户取消"
                return False

            if try_idx > 0:
                log(f"     [自动故障转移] 尝试备用加速节点 ({try_idx+1}/{len(candidate_urls)}): {try_url[:60]}...")

            try:
                with requests.get(try_url, headers=req_headers, proxies=proxies, stream=True, timeout=25, verify=False, allow_redirects=True) as resp:
                    if resp.status_code == 416:
                        total_size = downloaded_bytes
                    elif resp.status_code not in (200, 206):
                        last_error = f"HTTP {resp.status_code}"
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
                last_error = str(e)
                continue

        task.error_msg = str(last_error)
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

    def open_history_dialog(default_platform: Optional[str] = None):
        search_tf = ft.TextField(hint_text="搜索仓库名/推文/备注...", prefix_icon=ft.Icons.SEARCH, dense=True, expand=True, height=38)
        col_hist_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=360)

        # Dynamic dialog title
        if default_platform == "huggingface":
            dialog_title_text = "🤗 Hugging Face 专属历史记录与智能收藏库"
            default_filter_val = "🤗 Hugging Face 专属"
            filter_options = [
                ft.dropdown.Option("🤗 Hugging Face 专属"),
                ft.dropdown.Option("⭐ 仅看当前收藏"),
                ft.dropdown.Option("🐙 GitHub"),
                ft.dropdown.Option("🐦 Twitter / X"),
                ft.dropdown.Option("🌐 全部历史记录")
            ]
        elif default_platform == "github":
            dialog_title_text = "🐙 GitHub 仓库专属历史记录与智能收藏库"
            default_filter_val = "🐙 GitHub 专属"
            filter_options = [
                ft.dropdown.Option("🐙 GitHub 专属"),
                ft.dropdown.Option("⭐ 仅看当前收藏"),
                ft.dropdown.Option("🤗 Hugging Face"),
                ft.dropdown.Option("🐦 Twitter / X"),
                ft.dropdown.Option("🌐 全部历史记录")
            ]
        elif default_platform == "twitter":
            dialog_title_text = "🐦 Twitter / X 专属推文解析历史与智能收藏库"
            default_filter_val = "🐦 Twitter / X 专属"
            filter_options = [
                ft.dropdown.Option("🐦 Twitter / X 专属"),
                ft.dropdown.Option("⭐ 仅看当前收藏"),
                ft.dropdown.Option("🤗 Hugging Face"),
                ft.dropdown.Option("🐙 GitHub"),
                ft.dropdown.Option("🌐 全部历史记录")
            ]
        else:
            dialog_title_text = "🕒 全局历史记录与智能收藏库 (History & Starred Hub)"
            default_filter_val = "🌐 全部历史记录"
            filter_options = [
                ft.dropdown.Option("🌐 全部历史记录"),
                ft.dropdown.Option("🤗 Hugging Face"),
                ft.dropdown.Option("🐙 GitHub"),
                ft.dropdown.Option("🐦 Twitter / X"),
                ft.dropdown.Option("⭐ 全部收藏")
            ]

        dd_filter_scope = ft.Dropdown(
            options=filter_options,
            value=default_filter_val,
            dense=True,
            width=210,
            height=38
        )

        def refresh_hist_modal(filter_txt=""):
            records = HistoryManager.load_history()
            col_hist_list.controls.clear()
            scope = dd_filter_scope.value or "🌐 全部历史记录"
            
            for r in records:
                rid = r.get("repo_id", "")
                plat = r.get("platform", "")
                note = r.get("note", "")
                is_star = r.get("is_starred", False)
                branch = r.get("branch", "main")
                fcount = r.get("file_count", 0)
                t_str = r.get("last_accessed", "--")

                # Platform filtering
                if "Hugging Face" in scope and plat != "huggingface":
                    continue
                elif "GitHub" in scope and plat != "github":
                    continue
                elif "Twitter" in scope and plat != "twitter":
                    continue
                elif scope == "⭐ 仅看当前收藏":
                    target_p = default_platform or "huggingface"
                    if plat != target_p or not is_star:
                        continue
                elif scope == "⭐ 全部收藏" and not is_star:
                    continue

                if filter_txt:
                    if filter_txt.lower() not in rid.lower() and filter_txt.lower() not in note.lower():
                        continue

                def make_load_action(p=plat, repo=rid, b=branch, rtype=r.get("repo_type", "model")):
                    def _load(e):
                        dlg_hist.open = False
                        page.update()
                        if p == "github":
                            switch_to_tab("github")
                            tf_gh_repo.value = repo
                            tf_gh_branch.value = b
                            start_fetch_gh()
                        elif p == "twitter":
                            switch_to_tab("twitter")
                            tf_tw_url.value = repo if repo.startswith("http") else (f"https://x.com/i/status/{repo}" if repo.isdigit() else repo)
                            start_fetch_tw()
                        else:
                            switch_to_tab("browse")
                            tf_repo.value = repo
                            tf_branch.value = b
                            dd_type.value = rtype
                            start_fetch()
                    return _load

                def make_toggle_star(repo=rid, p=plat):
                    def _toggle(e):
                        HistoryManager.toggle_star(repo, p)
                        refresh_hist_modal(search_tf.value)
                    return _toggle

                def make_del(repo=rid, p=plat):
                    def _del(e):
                        HistoryManager.delete_record(repo, p)
                        refresh_hist_modal(search_tf.value)
                    return _del

                if plat == "huggingface":
                    plat_label = "🤗 HF"
                    plat_color = COLOR_ACCENT
                    desc_str = f"分支: {branch} | {fcount} 文件 | 访问: {t_str}"
                elif plat == "github":
                    plat_label = "🐙 GitHub"
                    plat_color = COLOR_SUCCESS
                    desc_str = f"分支: {branch} | {fcount} 文件/Release | 访问: {t_str}"
                elif plat == "twitter":
                    plat_label = "🐦 Twitter"
                    plat_color = "#0284c7"
                    desc_str = f"推文ID: {branch} | {fcount} 个画质规格 | 解析: {t_str}"
                else:
                    plat_label = plat
                    plat_color = COLOR_ACCENT
                    desc_str = f"访问: {t_str}"

                row_card = ft.Container(
                    content=ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.STAR if is_star else ft.Icons.STAR_BORDER,
                            icon_color=COLOR_WARNING if is_star else ft.Colors.OUTLINE,
                            on_click=make_toggle_star(),
                            tooltip="收藏置顶"
                        ),
                        ft.Container(
                            content=ft.Text(plat_label, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            bgcolor=plat_color,
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2)
                        ),
                        ft.Column([
                            ft.Text(rid, weight=ft.FontWeight.BOLD, size=13),
                            ft.Text(desc_str + (f" | 备注: {note}" if note else ""), size=11, color=COLOR_TEXT_SECONDARY)
                        ], expand=True, spacing=2),
                        ft.ElevatedButton("载入", icon=ft.Icons.ARROW_FORWARD, on_click=make_load_action(), height=32),
                        ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=COLOR_DANGER, on_click=make_del(), tooltip="删除记录")
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=COLOR_CARD_DARK
                )
                col_hist_list.controls.append(row_card)
            
            if not col_hist_list.controls:
                col_hist_list.controls.append(
                    ft.Container(content=ft.Text("暂无符合条件的历史记录", color=COLOR_TEXT_SECONDARY, text_align=ft.TextAlign.CENTER), padding=20)
                )
            page.update()

        search_tf.on_change = lambda e: refresh_hist_modal(search_tf.value)
        dd_filter_scope.on_change = lambda e: refresh_hist_modal(search_tf.value)

        dlg_hist = ft.AlertDialog(
            title=ft.Text(dialog_title_text, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([search_tf, dd_filter_scope], spacing=8),
                    col_hist_list
                ], spacing=8),
                width=760, height=440
            ),
            actions=[
                ft.TextButton("清空全部历史", on_click=lambda e: (HistoryManager.clear_all(), refresh_hist_modal())),
                ft.ElevatedButton("关闭", on_click=lambda e: (setattr(dlg_hist, 'open', False), page.update()))
            ]
        )
        page.overlay.append(dlg_hist)
        dlg_hist.open = True
        refresh_hist_modal()
        page.update()

    btn_hf_hist = ft.ElevatedButton("历史/收藏", icon=ft.Icons.HISTORY, on_click=lambda e: open_history_dialog("huggingface"), height=38)
    btn_gh_hist = ft.ElevatedButton("历史/收藏", icon=ft.Icons.HISTORY, on_click=lambda e: open_history_dialog("github"), height=38)

    # Assemble Top Configuration Card (Strict 36px Height Grid)
    top_config_container = ft.Container(
        content=ft.Column([
            ft.Text("🤗 Hugging Face 仓库、模型与网络加速配置", weight=ft.FontWeight.BOLD, size=13, color=COLOR_ACCENT),
            ft.Row([
                ft.Text("HF 仓库:", size=13, weight=ft.FontWeight.BOLD), tf_repo,
                ft.Text("类型:", size=13, weight=ft.FontWeight.BOLD), dd_type,
                ft.Text("分支:", size=13, weight=ft.FontWeight.BOLD), tf_branch,
                btn_fetch,
                btn_hf_hist
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("镜像加速:", size=13, weight=ft.FontWeight.BOLD), dd_mirror,
                ft.Text("HF Token:", size=13, weight=ft.FontWeight.BOLD), tf_token
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("网络代理:", size=13, weight=ft.FontWeight.BOLD), dd_proxy,
                ft.ElevatedButton("检测代理连通性", icon=ft.Icons.BOLT, on_click=test_proxy, height=38)
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("分类预设:", size=13, weight=ft.FontWeight.BOLD), dd_preset,
                ft.Text("保存路径:", size=13, weight=ft.FontWeight.BOLD), tf_dest_path,
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

    # ------------------ GitHub Explorer UI & Logic ------------------
    tf_gh_repo = ft.TextField(value="comfyanonymous/ComfyUI", label=None, dense=True, text_size=12, expand=3, height=38, content_padding=ft.Padding.symmetric(horizontal=8, vertical=4))
    dd_gh_mode = ft.Dropdown(
        options=[ft.dropdown.Option("Release 发布包"), ft.dropdown.Option("源码目录树")],
        value="Release 发布包", dense=True, text_size=12, width=130, height=38, content_padding=ft.Padding.symmetric(horizontal=8, vertical=4)
    )
    tf_gh_branch = ft.TextField(value="master", label=None, dense=True, text_size=12, width=100, height=38, content_padding=ft.Padding.symmetric(horizontal=8, vertical=4))
    
    dd_gh_mirror = ft.Dropdown(
        options=[ft.dropdown.Option(m) for m in DEFAULT_GITHUB_ACCELERATORS],
        value=DEFAULT_GITHUB_ACCELERATORS[0], dense=True, text_size=12, expand=3, height=38, content_padding=ft.Padding.symmetric(horizontal=8, vertical=4)
    )
    tf_gh_token = ft.TextField(
        value=saved_gh_token, 
        label=None, 
        password=True, 
        can_reveal_password=True, 
        dense=True, 
        text_size=12, 
        expand=2, 
        height=38, 
        content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        on_blur=lambda e: save_settings(),
        on_change=lambda e: save_settings()
    )
    
    def on_gh_preset_change(e):
        pname = dd_gh_preset.value
        if pname in PRESET_DIRS_MAP:
            rname = (tf_gh_repo.value or "").strip().split("/")[-1] or "download"
            base_dir = PRESET_DIRS_MAP[pname]
            if "custom_nodes" in pname:
                tf_gh_dest.value = os.path.normpath(os.path.join(base_dir, rname))
            else:
                tf_gh_dest.value = base_dir
            page.update()

    dd_gh_preset = ft.Dropdown(
        options=[ft.dropdown.Option(k) for k in PRESET_DIRS_MAP.keys()],
        value=list(PRESET_DIRS_MAP.keys())[0], dense=True, text_size=12, width=280, height=38,
        content_padding=ft.Padding.symmetric(horizontal=8, vertical=4)
    )
    dd_gh_preset.on_change = on_gh_preset_change
    tf_gh_dest = ft.TextField(value=DEFAULT_CUSTOM_NODES_DIR, label=None, dense=True, text_size=12, expand=True, height=38, content_padding=ft.Padding.symmetric(horizontal=8, vertical=4))
    cb_gh_flatten = ft.Checkbox(label="扁平化保存", value=True)

    lbl_gh_current_scope = ft.Text("当前位置: 未获取资源", size=12, weight=ft.FontWeight.BOLD, color=COLOR_ACCENT)
    lbl_gh_checked_count = ft.Text("[已勾选: 0 项]", size=12, weight=ft.FontWeight.BOLD, color=COLOR_SUCCESS)

    col_gh_nav = ft.ListView(expand=True, spacing=2)
    col_gh_files = ft.ListView(expand=True, spacing=2)

    raw_gh_items = {}
    gh_nav_structure = {}
    checked_gh_items = set()

    def get_gh_accelerated_url(raw_url: str) -> str:
        accel = (dd_gh_mirror.value or "").strip()
        if not accel or "不使用" in accel or "直连" in accel:
            return raw_url
        accel = accel.rstrip("/") + "/"
        return accel + raw_url

    def test_gh_node(e):
        node = (dd_gh_mirror.value or "").strip()
        log(f"[*] 正在测试 GitHub 加速节点: {node}...")
        show_snack(f"正在测试加速节点: {node}...")

        def _worker():
            test_url = get_gh_accelerated_url("https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/README.md")
            proxies = get_request_proxies()
            try:
                t0 = time.time()
                resp = requests.head(test_url, proxies=proxies, timeout=8, allow_redirects=True)
                cost = (time.time() - t0) * 1000
                if resp.status_code in (200, 301, 302):
                    show_snack(f"GitHub 节点正常！响应延迟: {cost:.0f} ms")
                    log(f"[✓] GitHub 加速节点测试成功: 延迟 {cost:.0f} ms")
                else:
                    show_snack(f"节点返回 HTTP {resp.status_code}，建议更换节点", is_error=True)
            except Exception as err:
                show_snack(f"节点连接失败: {str(err)}", is_error=True)
                log(f"[✗] GitHub 节点连接失败: {str(err)}")
            page.update()

        threading.Thread(target=_worker, daemon=True).start()

    def start_fetch_gh(e=None):
        raw_input = (tf_gh_repo.value or "").strip()
        clean_repo = raw_input
        if "github.com/" in clean_repo:
            clean_repo = clean_repo.split("github.com/")[-1].split(".git")[0].strip("/")
        elif clean_repo.endswith(".git"):
            clean_repo = clean_repo[:-4]

        if not clean_repo or "/" not in clean_repo:
            show_snack("请输入有效的 GitHub 仓库名或链接 (例如: sepiablue-ai/minimax_h3_workflows)！", is_error=True)
            return

        tf_gh_repo.value = clean_repo
        on_gh_preset_change(None)
        btn_gh_fetch.disabled = True
        lbl_global_status.value = f"状态: 正在智能分析 GitHub [{clean_repo}] 仓库与分支..."
        log(f"\n[*] 正在连接 GitHub API 查询仓库 '{clean_repo}'...")
        page.update()

        def _worker():
            nonlocal raw_gh_items, gh_nav_structure
            mode = dd_gh_mode.value or "Release 发布包"
            branch_input = (tf_gh_branch.value or "").strip()
            token = (tf_gh_token.value or "").strip() or None
            proxies = get_request_proxies()

            headers = {"User-Agent": "HF-Flet-Downloader", "Accept": "application/vnd.github.v3+json"}
            if token:
                headers["Authorization"] = f"token {token}"

            items_map = {}
            nav_struct = {}
            err_msg = None
            actual_branch = branch_input or "main"

            # 1. Fetch Repository Metadata
            try:
                repo_api_url = f"https://api.github.com/repos/{clean_repo}"
                r_info = requests.get(repo_api_url, headers=headers, proxies=proxies, timeout=10)
                repo_pushed_date = "--"
                if r_info.status_code == 200:
                    repo_info = r_info.json()
                    default_b = repo_info.get("default_branch") or "main"
                    if not branch_input or branch_input in ("main", "master"):
                        actual_branch = default_b
                        tf_gh_branch.value = actual_branch
                    raw_pushed = repo_info.get("pushed_at") or repo_info.get("updated_at")
                    if raw_pushed:
                        repo_pushed_date = raw_pushed[:16].replace("T", " ")
                elif r_info.status_code == 404:
                    err_msg = "未找到该 GitHub 仓库，请核对 owner/repo 拼写或确认是否为私有仓库。"
                elif r_info.status_code == 403:
                    err_msg = "GitHub API 调用频率已达上限，请在上方输入 GitHub Token！"
            except Exception as e:
                pass

            def _get_branch_commit_date(target_b: str) -> str:
                try:
                    commit_api_url = f"https://api.github.com/repos/{clean_repo}/commits/{target_b}"
                    c_resp = requests.get(commit_api_url, headers=headers, proxies=proxies, timeout=8)
                    if c_resp.status_code == 200:
                        c_data = c_resp.json()
                        commit_obj = c_data.get("commit", {})
                        dt_str = commit_obj.get("committer", {}).get("date") or commit_obj.get("author", {}).get("date")
                        if dt_str:
                            return dt_str[:16].replace("T", " ")
                except Exception:
                    pass
                return repo_pushed_date if repo_pushed_date != "--" else datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

            if not err_msg:
                # 2. Release Mode or Fallback
                if "Release" in mode:
                    api_url = f"https://api.github.com/repos/{clean_repo}/releases"
                    try:
                        resp = requests.get(api_url, headers=headers, proxies=proxies, timeout=12)
                        if resp.status_code == 200:
                            releases = resp.json()
                            if releases:
                                for rel in releases:
                                    tag_name = rel.get("tag_name", "未知Tag")
                                    pub_date = (rel.get("published_at") or "--")[:16].replace("T", " ")
                                    nav_struct[tag_name] = f"📦 {tag_name} ({pub_date})"

                                    zipball = rel.get("zipball_url") or f"https://github.com/{clean_repo}/archive/refs/tags/{tag_name}.zip"
                                    key_zip = f"{tag_name}/[Source code] {clean_repo.split('/')[-1]}-{tag_name}.zip"
                                    items_map[key_zip] = {
                                        "name": f"[源码包] {clean_repo.split('/')[-1]}-{tag_name}.zip",
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
                                            "size_str": format_size(asize),
                                            "raw_size": asize,
                                            "date_str": adate,
                                            "downloads": adls,
                                            "url": aurl
                                        }
                            else:
                                log(f"[i] 该仓库未发布 Release，自动为您切换为【源码目录树】模式拉取分支 '{actual_branch}'...")
                                dd_gh_mode.value = "源码目录树"
                                mode = "源码目录树"
                        elif resp.status_code == 404:
                            err_msg = "未找到该仓库，请检查 owner/repo 拼写。"
                        elif resp.status_code == 403:
                            err_msg = "GitHub API 调用频率受限，建议填入 GitHub Token！"
                        else:
                            err_msg = f"HTTP {resp.status_code}: {resp.text[:80]}"
                    except Exception as err:
                        err_msg = str(err)

                # 3. Source Tree Mode
                if "源码" in mode and not items_map and not err_msg:
                    api_url = f"https://api.github.com/repos/{clean_repo}/git/trees/{actual_branch}?recursive=1"
                    try:
                        resp = requests.get(api_url, headers=headers, proxies=proxies, timeout=15)
                        if resp.status_code == 200:
                            tree = resp.json().get("tree", [])
                            nav_struct["ROOT"] = "📁 全部源码 (根目录 /)"
                            branch_real_date = _get_branch_commit_date(actual_branch)
                            for item in tree:
                                ipath = item.get("path")
                                if item.get("type") == "tree":
                                    nav_struct[ipath] = f"📁 {ipath}"
                                elif item.get("type") == "blob":
                                    isize = item.get("size") or 0
                                    raw_url = f"https://raw.githubusercontent.com/{clean_repo}/{actual_branch}/{ipath}"
                                    scope = os.path.dirname(ipath) if "/" in ipath else "ROOT"
                                    items_map[ipath] = {
                                        "name": ipath,
                                        "scope": scope,
                                        "size_str": format_size(isize),
                                        "raw_size": isize,
                                        "date_str": branch_real_date,
                                        "downloads": "--",
                                        "url": raw_url
                                    }
                        elif resp.status_code == 404:
                            alt_branch = "master" if actual_branch == "main" else "main"
                            alt_url = f"https://api.github.com/repos/{clean_repo}/git/trees/{alt_branch}?recursive=1"
                            alt_resp = requests.get(alt_url, headers=headers, proxies=proxies, timeout=15)
                            if alt_resp.status_code == 200:
                                tree = alt_resp.json().get("tree", [])
                                nav_struct["ROOT"] = "📁 全部源码 (根目录 /)"
                                tf_gh_branch.value = alt_branch
                                alt_branch_date = _get_branch_commit_date(alt_branch)
                                for item in tree:
                                    ipath = item.get("path")
                                    if item.get("type") == "tree":
                                        nav_struct[ipath] = f"📁 {ipath}"
                                    elif item.get("type") == "blob":
                                        isize = item.get("size") or 0
                                        raw_url = f"https://raw.githubusercontent.com/{clean_repo}/{alt_branch}/{ipath}"
                                        scope = os.path.dirname(ipath) if "/" in ipath else "ROOT"
                                        items_map[ipath] = {
                                            "name": ipath,
                                            "scope": scope,
                                            "size_str": format_size(isize),
                                            "raw_size": isize,
                                            "date_str": alt_branch_date,
                                            "downloads": "--",
                                            "url": raw_url
                                        }
                            else:
                                err_msg = f"未找到仓库或分支 '{actual_branch}'，请核对分支名称。"
                        else:
                            err_msg = f"HTTP {resp.status_code}: {resp.text[:80]}"
                    except Exception as err:
                        err_msg = str(err)

            if items_map:
                raw_gh_items = items_map
                gh_nav_structure = nav_struct
                checked_gh_items.clear()
                HistoryManager.record_access(clean_repo, "github", "github", actual_branch, len(items_map))
                populate_gh_views()
                log(f"[✓] 成功获取 GitHub {len(items_map)} 项资源。")
                lbl_global_status.value = f"状态: 共检索到 {len(items_map)} 项 GitHub 资源"
            else:
                show_snack(f"获取失败: {err_msg}", is_error=True)
                log(f"[✗] 获取 GitHub 资源失败: {err_msg}")
                lbl_global_status.value = "状态: 获取 GitHub 资源失败"

            btn_gh_fetch.disabled = False
            page.update()

        threading.Thread(target=_worker, daemon=True).start()

    def populate_gh_views():
        col_gh_nav.controls.clear()
        first_scope = None
        for key, label in gh_nav_structure.items():
            if first_scope is None:
                first_scope = key
            btn_n = ft.TextButton(
                label, style=ft.ButtonStyle(alignment=ft.alignment.center_left),
                on_click=lambda e, k=key: render_gh_scope(k)
            )
            col_gh_nav.controls.append(btn_n)

        if first_scope:
            render_gh_scope(first_scope)
        page.update()

    def render_gh_scope(scope: str):
        lbl_gh_current_scope.value = f"当前位置: {scope}"
        col_gh_files.controls.clear()

        for key, item in raw_gh_items.items():
            if item["scope"] == scope or scope == "ROOT":
                is_chk = key in checked_gh_items
                
                cb = ft.Checkbox(value=is_chk, on_change=lambda e, k=key: toggle_gh_check(k))
                row = ft.Container(
                    content=ft.Row([
                        cb,
                        ft.Text(item["name"], weight=ft.FontWeight.BOLD, size=12, expand=4),
                        ft.Text(item["size_str"], size=12, color=COLOR_ACCENT, width=90),
                        ft.Text(item["date_str"], size=12, color=COLOR_TEXT_SECONDARY, width=130),
                        ft.Text(f"下载:{item['downloads']}", size=11, color=COLOR_SUCCESS, width=80),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=COLOR_ACTIVE if is_chk else None,
                    border_radius=4,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=3),
                    on_click=lambda e, k=key: toggle_gh_check(k)
                )
                col_gh_files.controls.append(row)

        update_gh_checked_label()
        page.update()

    def toggle_gh_check(key: str):
        if key in checked_gh_items:
            checked_gh_items.remove(key)
        else:
            checked_gh_items.add(key)
        update_gh_checked_label()
        # Rerender current scope
        scope = lbl_gh_current_scope.value.replace("当前位置: ", "")
        render_gh_scope(scope)

    def update_gh_checked_label():
        lbl_gh_checked_count.value = f"[已勾选: {len(checked_gh_items)} 项]"

    def check_all_gh(e):
        scope = lbl_gh_current_scope.value.replace("当前位置: ", "")
        for key, item in raw_gh_items.items():
            if item["scope"] == scope or scope == "ROOT":
                checked_gh_items.add(key)
        render_gh_scope(scope)

    def uncheck_all_gh(e):
        scope = lbl_gh_current_scope.value.replace("当前位置: ", "")
        for key, item in raw_gh_items.items():
            if item["scope"] == scope or scope == "ROOT":
                checked_gh_items.discard(key)
        render_gh_scope(scope)

    def _resolve_github_dest_dir(base_dest: str, repo_id: str) -> str:
        clean_repo = repo_id.replace("🐙", "").strip()
        repo_name = clean_repo.split("/")[-1]
        norm_dest = os.path.normpath(base_dest)
        last_dir = os.path.basename(norm_dest)
        if last_dir.lower() != repo_name.lower():
            return os.path.join(norm_dest, repo_name)
        return norm_dest

    def add_gh_to_queue(jump: bool = False):
        if not checked_gh_items:
            show_snack("请先在右侧勾选需要下载的 GitHub 文件或资源！", is_error=True)
            return

        raw_dest_dir = (tf_gh_dest.value or "").strip()
        if not raw_dest_dir:
            show_snack("请指定保存目标路径！", is_error=True)
            return

        repo_id = (tf_gh_repo.value or "").strip()
        dest_dir = _resolve_github_dest_dir(raw_dest_dir, repo_id)
        os.makedirs(dest_dir, exist_ok=True)
        
        token = (tf_gh_token.value or "").strip() or None
        proxy = get_effective_proxy()
        flatten = cb_gh_flatten.value

        added_cnt = 0
        for key in list(checked_gh_items):
            item = raw_gh_items.get(key)
            if not item:
                continue

            raw_url = item["url"]
            accel_url = get_gh_accelerated_url(raw_url)
            fname = os.path.basename(item["name"])

            exists = any(t.platform == "github" and t.direct_url == accel_url and t.dest_dir == dest_dir for t in tasks)
            if exists:
                continue

            tid = (max([t.task_id for t in tasks]) + 1) if tasks else 1
            task = QueueTask(
                task_id=tid,
                repo_id=f"🐙 {repo_id}",
                repo_type="github",
                branch=(tf_gh_branch.value or "master").strip(),
                file_path=fname,
                size_str=item["size_str"],
                date_str=item["date_str"],
                dest_dir=dest_dir,
                flatten=flatten,
                endpoint=(dd_gh_mirror.value or "").strip(),
                token=token,
                proxy=proxy,
                status="等待中",
                progress=0.0,
                total_bytes=item["raw_size"] if item["raw_size"] > 0 else None,
                platform="github",
                direct_url=accel_url
            )
            tasks.append(task)
            added_cnt += 1

        save_tasks()
        refresh_queue_view()
        update_queue_tab_badge()
        show_snack(f"成功将 {added_cnt} 个 GitHub 资源加入下载队列！(保存至: {dest_dir})")
        log(f"[✓] 成功将 {added_cnt} 个 GitHub 资源加入下载队列！(目录: {dest_dir})")

        if jump:
            switch_to_tab("queue")

    def download_gh_zip(e):
        repo_id = (tf_gh_repo.value or "").strip()
        if not repo_id or "/" not in repo_id:
            show_snack("请输入有效的 GitHub 仓库名！", is_error=True)
            return

        branch = (tf_gh_branch.value or "master").strip()
        raw_dest_dir = (tf_gh_dest.value or "").strip()
        if not raw_dest_dir:
            show_snack("请指定保存目标路径！", is_error=True)
            return

        dest_dir = _resolve_github_dest_dir(raw_dest_dir, repo_id)
        os.makedirs(dest_dir, exist_ok=True)

        repo_name = repo_id.split("/")[-1]
        zip_name = f"{repo_name}-{branch}.zip"
        raw_url = f"https://github.com/{repo_id}/archive/refs/heads/{branch}.zip"
        accel_url = get_gh_accelerated_url(raw_url)

        tid = (max([t.task_id for t in tasks]) + 1) if tasks else 1
        real_zip_date = ""
        if raw_gh_items:
            for it in raw_gh_items.values():
                d = it.get("date_str")
                if d and d not in ("最新", "--"):
                    real_zip_date = d
                    break
        if not real_zip_date:
            real_zip_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        task = QueueTask(
            task_id=tid,
            repo_id=f"🐙 {repo_id}",
            repo_type="github_zip",
            branch=branch,
            file_path=zip_name,
            size_str="整包源码Zip",
            date_str=real_zip_date,
            dest_dir=dest_dir,
            flatten=True,
            endpoint=(dd_gh_mirror.value or "").strip(),
            token=(tf_gh_token.value or "").strip() or None,
            proxy=get_effective_proxy(),
            status="等待中",
            progress=0.0,
            platform="github",
            direct_url=accel_url
        )
        tasks.append(task)
        save_tasks()
        refresh_queue_view()
        update_queue_tab_badge()
        show_snack(f"已添加整包源码 Zip 任务: {zip_name} (下载后将自动解压至: {dest_dir})")
        log(f"[✓] 已添加 GitHub 仓库整包源码 Zip 任务: {zip_name} (目录: {dest_dir})")
        switch_to_tab("queue")

    btn_gh_fetch = ft.ElevatedButton("获取 GitHub 资源", icon=ft.Icons.SEARCH, bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE, on_click=start_fetch_gh, height=38)

    # Top Configuration Card for GitHub (Strict 38px Grid)
    top_gh_config_container = ft.Container(
        content=ft.Column([
            ft.Text("🐙 GitHub 仓库、Release与网络加速配置", weight=ft.FontWeight.BOLD, size=13, color=COLOR_ACCENT),
            ft.Row([
                ft.Text("GitHub 仓库:", size=13, weight=ft.FontWeight.BOLD), tf_gh_repo,
                ft.Text("模式:", size=13, weight=ft.FontWeight.BOLD), dd_gh_mode,
                ft.Text("分支/Tag:", size=13, weight=ft.FontWeight.BOLD), tf_gh_branch,
                btn_gh_fetch,
                btn_gh_hist
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("加速节点:", size=13, weight=ft.FontWeight.BOLD), dd_gh_mirror,
                ft.ElevatedButton("检测加速节点", icon=ft.Icons.BOLT, on_click=test_gh_node, height=38),
                ft.Text("GitHub Token:", size=13, weight=ft.FontWeight.BOLD), tf_gh_token
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("网络代理:", size=13, weight=ft.FontWeight.BOLD), dd_proxy,
                ft.ElevatedButton("检测代理连通性", icon=ft.Icons.BOLT, on_click=test_proxy, height=38)
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=6),
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        padding=10
    )

    gh_dest_container = ft.Container(
        content=ft.Column([
            ft.Text("💾 当前文件的保存目标目录 (默认开启扁平化保存：直接存入目标目录，不生成多层嵌套子文件夹)", weight=ft.FontWeight.BOLD, size=13, color=COLOR_ACCENT),
            ft.Row([
                ft.Text("分类预设:", size=13, weight=ft.FontWeight.BOLD), dd_gh_preset,
                ft.Text("保存路径:", size=13, weight=ft.FontWeight.BOLD), tf_gh_dest,
                cb_gh_flatten
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=6),
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        padding=10
    )

    tab_github_view = ft.Column([
        top_gh_config_container,
        gh_dest_container,
        ft.Container(
            content=ft.Row([
                lbl_gh_current_scope,
                lbl_gh_checked_count,
                ft.Container(expand=True),
                ft.ElevatedButton("全选可见", icon=ft.Icons.SELECT_ALL, on_click=check_all_gh, height=36),
                ft.ElevatedButton("取消勾选", icon=ft.Icons.DESELECT, on_click=uncheck_all_gh, height=36),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(horizontal=4, vertical=2)
        ),
        ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Text("📁 Release版本 / 源码目录树", weight=ft.FontWeight.BOLD, size=12),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=7)
                    ),
                    col_gh_nav
                ], expand=True),
                width=300, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=6
            ),
            ft.Container(
                content=col_gh_files,
                expand=True, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=6
            )
        ], expand=True, spacing=6),
        ft.Row([
            ft.ElevatedButton("加入统一下载队列", icon=ft.Icons.DOWNLOAD, bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE, on_click=lambda e: add_gh_to_queue(False), height=38),
            ft.ElevatedButton("📦 下载整包源码 Zip (含加速)", icon=ft.Icons.ROCKET_LAUNCH, on_click=download_gh_zip, height=38),
            ft.ElevatedButton("入队并跳转到队列", icon=ft.Icons.PLAY_ARROW, on_click=lambda e: add_gh_to_queue(True), height=38),
        ], spacing=8)
    ], expand=True, spacing=6)

    # ------------------ Tab 3: Twitter / X Video Downloader View & Handlers (Flet) ------------------
    tf_tw_url = ft.TextField(
        hint_text="输入 Twitter / X 推文链接 (例如 https://x.com/user/status/123456789) 或 Tweet ID",
        expand=True, dense=True, height=STANDARD_CONTROL_HEIGHT, text_size=12,
        content_padding=STD_PADDING, border_radius=STD_RADIUS
    )

    dd_tw_preset = ft.Dropdown(
        options=[ft.dropdown.Option(k) for k in PRESET_DIRS_MAP.keys()],
        value=list(PRESET_DIRS_MAP.keys())[0], dense=True, text_size=12, width=280, height=38,
        content_padding=ft.Padding.symmetric(horizontal=8, vertical=4)
    )

    tf_tw_dest = ft.TextField(
        value=PRESET_DIRS_MAP[list(PRESET_DIRS_MAP.keys())[0]],
        expand=True, dense=True, height=STANDARD_CONTROL_HEIGHT, text_size=12,
        content_padding=STD_PADDING, border_radius=STD_RADIUS
    )

    def on_tw_preset_change(e):
        k = dd_tw_preset.value
        if k in PRESET_DIRS_MAP:
            tf_tw_dest.value = PRESET_DIRS_MAP[k]
            page.update()

    dd_tw_preset.on_change = on_tw_preset_change

    lbl_tw_author = ft.Text("推文作者: --", weight=ft.FontWeight.BOLD, size=13, color=COLOR_ACCENT)
    lbl_tw_date = ft.Text("发布日期: -- | 视频时长: --", size=12, color=ft.Colors.GREY_600)
    lbl_tw_text = ft.Text("推文内容: (请在上方面板输入推文链接并点击【开始解析视频】)", size=12)
    lbl_tw_checked = ft.Text("[已勾选: 0 项规格]", weight=ft.FontWeight.BOLD, color=COLOR_SUCCESS, size=13)
    img_tw_thumb = ft.Image(src="", width=150, height=90, fit=ft.ImageFit.COVER, border_radius=ft.BorderRadius(6, 6, 6, 6), visible=False)

    col_tw_variants = ft.ListView(expand=True, spacing=4)
    raw_tw_data = None
    checked_tw_indices = set()

    def refresh_tw_variants_view():
        col_tw_variants.controls.clear()
        if not raw_tw_data:
            page.update()
            return

        variants = raw_tw_data.get("variants", [])
        
        # Header Row
        col_tw_variants.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text("勾选", width=42, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("画质 / 清晰度规格", width=220, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("视频码率", width=110, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("预估大小", width=110, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("目标文件名", expand=True, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("在线预览与操作", width=110, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD, size=12),
                ]),
                border_radius=4,
                padding=ft.Padding.symmetric(horizontal=8, vertical=6)
            )
        )

        def make_chk_handler(idx):
            def _handler(e):
                if e.control.value:
                    checked_tw_indices.add(idx)
                else:
                    checked_tw_indices.discard(idx)
                lbl_tw_checked.value = f"[已勾选: {len(checked_tw_indices)} 项规格]"
                refresh_tw_variants_view()
            return _handler

        def make_quick_dl_single(idx):
            checked_tw_indices.clear()
            checked_tw_indices.add(idx)
            add_tw_to_queue(jump=True)

        for idx, v in enumerate(variants):
            is_chk = idx in checked_tw_indices
            col_tw_variants.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Checkbox(value=is_chk, on_change=make_chk_handler(idx), scale=0.85),
                        ft.Row([
                            ft.Icon(ft.Icons.SMART_DISPLAY, size=18, color=COLOR_ACCENT if is_chk else COLOR_WARNING),
                            ft.Text(v["quality"], size=13, weight=ft.FontWeight.BOLD if is_chk else ft.FontWeight.NORMAL)
                        ], width=220),
                        ft.Text(v["bitrate_str"], width=110, text_align=ft.TextAlign.CENTER, size=12),
                        ft.Text(v["size_str"], width=110, text_align=ft.TextAlign.CENTER, size=12, color=COLOR_SUCCESS, weight=ft.FontWeight.BOLD),
                        ft.Text(v["filename"], expand=True, size=12),
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.PLAY_CIRCLE_FILL,
                                icon_color=COLOR_ACCENT,
                                icon_size=18,
                                tooltip="在线预览播放视频",
                                on_click=lambda e, u=v["url"]: page.launch_url(u)
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DOWNLOAD,
                                icon_size=18,
                                tooltip="加入队列并立即下载",
                                on_click=lambda e, i=idx: make_quick_dl_single(i)
                            ),
                        ], width=110, alignment=ft.MainAxisAlignment.CENTER, spacing=0)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    border=ft.Border.all(1, COLOR_ACCENT if is_chk else ft.Colors.TRANSPARENT),
                    border_radius=4,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    bgcolor=ft.Colors.with_opacity(0.06, COLOR_ACCENT) if is_chk else None
                )
            )
        page.update()

    def start_fetch_tw(e=None):
        raw_url = (tf_tw_url.value or "").strip()
        if not raw_url:
            show_snack("请输入有效的 Twitter / X 推文链接或 Tweet ID！", is_error=True)
            return

        btn_tw_fetch.disabled = True
        lbl_global_status.value = "状态: 正在智能解析 Twitter / X 视频元数据与高清直链..."
        lbl_tw_author.value = "推文作者: 正在连接网络并解析推文信息..."
        lbl_tw_date.value = "发布日期: 解析中... | 视频时长: 解析中..."
        lbl_tw_text.value = f"推文内容: 正在解析目标推文视频流直链与清晰度规格 ({raw_url})..."
        img_tw_thumb.visible = False
        log(f"\n[*] 正在解析推文: {raw_url}...")
        page.update()

        def _worker():
            nonlocal raw_tw_data
            proxy = get_effective_proxy()
            try:
                res = TwitterMediaResolver.resolve(raw_url, proxy)
                raw_tw_data = res
                checked_tw_indices.clear()
                if res.get("variants"):
                    checked_tw_indices.add(0) # Default check highest quality
                
                lbl_tw_author.value = f"推文作者: {res.get('author')} ({res.get('author_id')})"
                lbl_tw_date.value = f"发布日期: {res.get('date')} | 视频时长: {res.get('duration')}"
                lbl_tw_text.value = f"推文内容: {res.get('text')}"
                lbl_tw_checked.value = f"[已勾选: {len(checked_tw_indices)} 项规格]"
                
                if res.get("thumbnail"):
                    img_tw_thumb.src = res.get("thumbnail")
                    img_tw_thumb.visible = True
                else:
                    img_tw_thumb.visible = False

                HistoryManager.record_access(f"@{res.get('author_id', '')} / {res.get('tweet_id')}", "twitter", "video", "main", len(res.get("variants", [])))
                log(f"[✓] 成功解析到 {len(res.get('variants', []))} 个画质规格！作者: {res.get('author')} ({res.get('author_id')})")
                show_snack(f"成功解析到 {len(res.get('variants', []))} 个画质规格！")
                lbl_global_status.value = f"状态: 成功解析推文视频 (共 {len(res.get('variants', []))} 项清晰度)"
                refresh_tw_variants_view()
            except Exception as err:
                raw_tw_data = None
                checked_tw_indices.clear()
                lbl_tw_author.value = "推文作者: 解析未成功"
                lbl_tw_date.value = "发布日期: -- | 视频时长: --"
                lbl_tw_text.value = f"推文内容: ❌ 无法解析视频: {str(err)}\n\n💡 提示: 请确认推文链接是否有效，或确认是否已开启网络代理 (如 Clash/v2rayN)。"
                lbl_tw_checked.value = "[已勾选: 0 项规格]"
                img_tw_thumb.visible = False
                refresh_tw_variants_view()
                log(f"[✗] 解析 Twitter 视频失败: {str(err)}")
                show_snack(f"解析失败: {str(err)}", is_error=True)
                lbl_global_status.value = "状态: Twitter 视频解析失败"
            finally:
                btn_tw_fetch.disabled = False
                page.update()

        threading.Thread(target=_worker, daemon=True).start()

    def add_tw_to_queue(jump: bool = False):
        if not raw_tw_data or not raw_tw_data.get("variants"):
            show_snack("请先解析推文视频！", is_error=True)
            return

        if not checked_tw_indices:
            show_snack("请先勾选需要下载的画质规格！", is_error=True)
            return

        dest_dir = tf_tw_dest.value.strip()
        if not dest_dir:
            show_snack("请指定保存目标路径！", is_error=True)
            return
        os.makedirs(dest_dir, exist_ok=True)

        variants = raw_tw_data.get("variants", [])
        proxy = get_effective_proxy()
        added = 0

        for idx in sorted(list(checked_tw_indices)):
            if idx < 0 or idx >= len(variants):
                continue
            v = variants[idx]
            v_url = v["url"]
            v_name = v["filename"]

            if any(t.platform == "twitter" and t.direct_url == v_url and t.dest_dir == dest_dir for t in tasks):
                continue

            nonlocal task_counter
            task = QueueTask(
                task_id=task_counter,
                repo_id=f"🐦 {raw_tw_data.get('author_id') or 'Twitter'}",
                repo_type="twitter",
                branch=raw_tw_data.get("tweet_id", ""),
                file_path=v_name,
                size_str=v["size_str"],
                date_str=raw_tw_data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M")),
                dest_dir=dest_dir,
                flatten=True,
                endpoint="https://twitter.com",
                token=None,
                proxy=proxy,
                status="等待中",
                progress=0.0,
                total_bytes=v["raw_size"] if v["raw_size"] > 0 else None,
                platform="twitter",
                direct_url=v_url
            )
            task.check_local_status()
            tasks.append(task)
            task_counter += 1
            added += 1

        if added > 0:
            save_tasks()
            refresh_queue_view()
            update_queue_tab_badge()
            show_snack(f"已成功将 {added} 项 Twitter 视频任务加入下载队列！")
            log(f"[✓] 已将 {added} 项 Twitter 视频任务成功加入统一下载队列！(目标目录: {dest_dir})")
            if jump:
                switch_to_tab("queue")
        else:
            show_snack("所选的任务均已在队列中！")

    btn_tw_fetch = ft.ElevatedButton("⚡ 开始解析视频", icon=ft.Icons.SEARCH, bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE, on_click=start_fetch_tw, height=38)

    top_tw_config_container = ft.Container(
        content=ft.Column([
            ft.Text("🐦 Twitter / X 视频解析与网络加速配置", weight=ft.FontWeight.BOLD, size=13, color=COLOR_ACCENT),
            ft.Row([
                ft.Text("推文链接:", size=13, weight=ft.FontWeight.BOLD), tf_tw_url,
                btn_tw_fetch,
                ft.ElevatedButton("历史/收藏", icon=ft.Icons.HISTORY, on_click=lambda e: open_history_dialog("twitter"), height=38)
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("网络代理:", size=13, weight=ft.FontWeight.BOLD), dd_proxy,
                ft.ElevatedButton("检测代理连通性", icon=ft.Icons.BOLT, on_click=test_proxy, height=38)
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=6),
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        padding=10
    )

    tw_dest_container = ft.Container(
        content=ft.Column([
            ft.Text("💾 视频保存目标目录", weight=ft.FontWeight.BOLD, size=13, color=COLOR_ACCENT),
            ft.Row([
                ft.Text("分类预设:", size=13, weight=ft.FontWeight.BOLD), dd_tw_preset,
                ft.Text("保存路径:", size=13, weight=ft.FontWeight.BOLD), tf_tw_dest
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=6),
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        padding=10
    )

    tw_meta_container = ft.Container(
        content=ft.Row([
            ft.Column([
                lbl_tw_author,
                lbl_tw_date,
                lbl_tw_text
            ], spacing=3, expand=True),
            img_tw_thumb
        ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=8),
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        padding=10
    )

    tab_twitter_view = ft.Column([
        top_tw_config_container,
        tw_dest_container,
        tw_meta_container,
        ft.Container(
            content=ft.Row([
                lbl_tw_checked,
                ft.Container(expand=True),
                ft.ElevatedButton("全选画质", icon=ft.Icons.SELECT_ALL, on_click=lambda e: (checked_tw_indices.update(range(len(raw_tw_data.get("variants", [])))) if raw_tw_data else None) or (setattr(lbl_tw_checked, "value", f"[已勾选: {len(checked_tw_indices)} 项规格]") or refresh_tw_variants_view()), height=36),
                ft.ElevatedButton("清空勾选", icon=ft.Icons.DESELECT, on_click=lambda e: checked_tw_indices.clear() or (setattr(lbl_tw_checked, "value", "[已勾选: 0 项规格]") or refresh_tw_variants_view()), height=36),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(horizontal=4, vertical=2)
        ),
        ft.Container(
            content=col_tw_variants,
            expand=True, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=6
        ),
        ft.Row([
            ft.ElevatedButton("加入统一下载队列", icon=ft.Icons.DOWNLOAD, bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE, on_click=lambda e: add_tw_to_queue(False), height=38),
            ft.ElevatedButton("入队并跳转到队列", icon=ft.Icons.PLAY_ARROW, on_click=lambda e: add_tw_to_queue(True), height=38),
        ], spacing=8)
    ], expand=True, spacing=6)

    content_area = ft.Container(content=tab_browser_view, expand=True)

    def update_queue_tab_badge():
        pending_cnt = sum(1 for t in tasks if t.status in ("等待中", "下载中", "已中断"))
        btn_nav_queue.text = f"统一下载队列 ({pending_cnt})"
        page.update()

    def switch_to_tab(tab_name: str):
        btn_nav_browse.style = None
        btn_nav_github.style = None
        btn_nav_twitter.style = None
        btn_nav_queue.style = None
        btn_nav_env.style = None

        if tab_name == "browse":
            btn_nav_browse.style = ft.ButtonStyle(bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE)
            content_area.content = tab_browser_view
        elif tab_name == "github":
            btn_nav_github.style = ft.ButtonStyle(bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE)
            content_area.content = tab_github_view
        elif tab_name == "twitter":
            btn_nav_twitter.style = ft.ButtonStyle(bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE)
            content_area.content = tab_twitter_view
        elif tab_name == "queue":
            btn_nav_queue.style = ft.ButtonStyle(bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE)
            content_area.content = tab_queue_view
        else:
            btn_nav_env.style = ft.ButtonStyle(bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE)
            content_area.content = tab_env_view
            refresh_env_dirs_view()
        page.update()

    btn_nav_browse = ft.ElevatedButton(
        "HuggingFace 浏览器", icon=ft.Icons.FOLDER_COPY,
        style=ft.ButtonStyle(bgcolor=COLOR_ACCENT, color=ft.Colors.WHITE),
        on_click=lambda e: switch_to_tab("browse"), height=38
    )
    btn_nav_github = ft.ElevatedButton(
        "GitHub 资源浏览器", icon=ft.Icons.AUTO_AWESOME_MOTION,
        on_click=lambda e: switch_to_tab("github"), height=38
    )
    btn_nav_twitter = ft.ElevatedButton(
        "Twitter / X 视频", icon=ft.Icons.SMART_DISPLAY,
        on_click=lambda e: switch_to_tab("twitter"), height=38
    )
    btn_nav_queue = ft.ElevatedButton(
        "统一下载队列 (0)", icon=ft.Icons.FORMAT_LIST_BULLETED,
        on_click=lambda e: switch_to_tab("queue"), height=38
    )
    btn_nav_env = ft.ElevatedButton(
        "一键部署环境", icon=ft.Icons.CONSTRUCTION,
        on_click=lambda e: switch_to_tab("env"), height=38
    )

    btn_about = ft.IconButton(
        icon=ft.Icons.INFO_OUTLINE,
        tooltip="关于与使用说明",
        on_click=lambda e: show_snack("🚀 Hugging Face & GitHub & Twitter 极速下载器 (Pro Edition)")
    )

    nav_bar = ft.Container(
        content=ft.Row([
            btn_nav_browse,
            btn_nav_github,
            btn_nav_twitter,
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
