from typing import Any, Optional
from app.core.config import ConfigService
from app.core.event_bus import EventBus

class AppContext:
    """Global runtime context providing services, main window reference, and logging."""
    def __init__(self, main_window: Any):
        self.main_window = main_window
        self.config = ConfigService
        self.event_bus = EventBus

    def log(self, message: str):
        self.event_bus.emit("app_log", message)

    def show_toast(self, message: str, is_error: bool = False):
        self.event_bus.emit("app_toast", {"message": message, "is_error": is_error})

    def get_proxy(self) -> Optional[str]:
        p = self.config.get("proxy", "")
        if not p or "不使用代理" in p or "直连" in p:
            return None
        return p.strip()

    def set_progress_indeterminate(self, status_text: str = ""):
        if hasattr(self.main_window, "set_progress_indeterminate"):
            self.main_window.set_progress_indeterminate(status_text)

    def set_progress_determinate(self, value: float, status_text: str = "", speed_text: str = "", progress_text: str = ""):
        if hasattr(self.main_window, "set_progress_determinate"):
            self.main_window.set_progress_determinate(value, status_text, speed_text, progress_text)

    def stop_progress(self, status_text: str = "就绪", value: float = 100.0):
        if hasattr(self.main_window, "stop_progress"):
            self.main_window.stop_progress(status_text, value)

    def reset_progress(self, status_text: str = "就绪"):
        if hasattr(self.main_window, "reset_progress"):
            self.main_window.reset_progress(status_text)
