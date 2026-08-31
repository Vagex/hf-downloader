import os
import tkinter as tk
from tkinter import ttk
from app.modules.base import BaseAppModule, ModuleManager

class DownloaderModule(BaseAppModule):
    module_id = "downloader"
    name = "🚀 全能下载中心"
    icon_name = "download"
    category = "核心功能"
    description = "HF大模型 / GitHub仓库 / 主流视频流 / 磁力链接BT 统一极速下载"
    order = 10

    def create_view(self, parent: tk.Widget) -> tk.Widget:
        from hf_downloader_gui import HFDownloaderView
        self.downloader_view = HFDownloaderView(master=parent)
        self.view_container = self.downloader_view
        return self.downloader_view

    def on_activate(self):
        if hasattr(self, "downloader_view") and hasattr(self.downloader_view, "_refresh_queue_tree"):
            self.downloader_view._refresh_queue_tree()

    def on_shutdown(self):
        if hasattr(self, "downloader_view") and self.downloader_view:
            try:
                self.downloader_view._save_tasks()
                self.downloader_view._save_settings()
                self.downloader_view._update_lock_file(False)
            except Exception:
                pass

ModuleManager.register(DownloaderModule)
