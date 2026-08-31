import os
import json
from typing import Any, Dict

class ConfigService:
    """Unified application settings and persistent configuration service."""
    CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".hf_downloader")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "app_config.json")
    
    DEFAULT_CONFIG = {
        "theme": "light",
        "proxy": "不使用代理 (直连)",
        "proxies_list": [
            "不使用代理 (直连)",
            "http://127.0.0.1:7890",
            "http://127.0.0.1:10809",
            "http://127.0.0.1:1080",
            "socks5://127.0.0.1:7890",
            "socks5://127.0.0.1:10808"
        ],
        "default_dest_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
        "enable_notifications": True,
        "max_concurrent_tasks": 1,
        "auto_clear_completed": False
    }

    _config_cache: Dict[str, Any] = {}

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        os.makedirs(cls.CONFIG_DIR, exist_ok=True)
        if not cls._config_cache:
            cls._config_cache = cls.DEFAULT_CONFIG.copy()
            if os.path.exists(cls.CONFIG_FILE):
                try:
                    with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                        saved = json.load(f)
                        cls._config_cache.update(saved)
                except Exception as e:
                    print(f"[ConfigService] Error reading config: {e}")
        return cls._config_cache

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        cfg = cls.load_config()
        return cfg.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any):
        cfg = cls.load_config()
        cfg[key] = value
        cls.save_config()

    @classmethod
    def save_config(cls):
        os.makedirs(cls.CONFIG_DIR, exist_ok=True)
        try:
            with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cls._config_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ConfigService] Error saving config: {e}")
