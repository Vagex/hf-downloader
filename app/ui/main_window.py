import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional

from app.ui.theme import Theme
from app.ui.sidebar import Sidebar
from app.core.context import AppContext
from app.core.event_bus import EventBus
from app.modules.base import ModuleManager, BaseAppModule

class MainWindow(tk.Tk):
    """Main Workbench window for the Universal Super App Platform."""
    def __init__(self):
        super().__init__()
        self.title("🌟 万能超级工具箱 (Universal Super App Platform) v2.0")
        self.geometry("1280x860")
        self.minsize(1050, 720)

        Theme.setup_fonts(self)
        self.context = AppContext(self)
        self.module_views: Dict[str, tk.Widget] = {}
        self.active_module: Optional[BaseAppModule] = None

        self._build_workbench()
        self._init_modules()
        self._bind_events()

    def _build_workbench(self):
        # Configure root grid
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Top Header Control Bar
        top_bar = tk.Frame(self, height=44, bg=Theme.BG_CARD, bd=0, relief=tk.FLAT)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        lbl_brand = tk.Label(top_bar, text="  🚀 万能超级工作台  ", font=Theme.FONT_SUBTITLE, bg=Theme.BG_CARD, fg=Theme.PRIMARY)
        lbl_brand.pack(side=tk.LEFT, padx=6, pady=8)

        sep_top = tk.Frame(top_bar, width=1, bg=Theme.BORDER)
        sep_top.pack(side=tk.LEFT, fill=tk.Y, pady=8)

        self.lbl_global_status = tk.Label(
            top_bar, 
            text="状态: 平台就绪 · 模块化引擎已激活", 
            font=Theme.FONT_BODY, 
            bg=Theme.BG_CARD, 
            fg=Theme.TEXT_MUTED
        )
        self.lbl_global_status.pack(side=tk.LEFT, padx=12)

        # Right header quick tools
        btn_feedback = ttk.Button(top_bar, text=" 💡 更多功能规划...", command=self._show_future_roadmap)
        btn_feedback.pack(side=tk.RIGHT, padx=(4, 12), pady=6)

        # 2. Left Sidebar Navigation
        self.sidebar = Sidebar(self, on_module_selected=self.switch_to_module, width=220)
        self.sidebar.grid(row=1, column=0, sticky="nsew")

        # 3. Right Main Content Dynamic Workspace
        self.workspace_frame = tk.Frame(self, bg=Theme.BG_LIGHT)
        self.workspace_frame.grid(row=1, column=1, sticky="nsew")
        self.workspace_frame.columnconfigure(0, weight=1)
        self.workspace_frame.rowconfigure(0, weight=1)

        # Bottom StatusBar
        status_bar = tk.Frame(self, height=24, bg=Theme.BG_SIDEBAR)
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.lbl_bottom_info = tk.Label(
            status_bar, 
            text="支持 HuggingFace · GitHub · 主流音视频 · 磁力BT · 媒体工坊 · 即插即用无限扩展", 
            font=Theme.FONT_SMALL, 
            bg=Theme.BG_SIDEBAR, 
            fg=Theme.TEXT_MUTED
        )
        self.lbl_bottom_info.pack(side=tk.LEFT, padx=8, pady=2)

    def _init_modules(self):
        modules = ModuleManager.get_all_modules()
        for mod in modules:
            mod.initialize(self.context)
        
        self.sidebar.set_modules(modules)
        
        # Select first module by default (e.g. downloader)
        if modules:
            first_id = modules[0].module_id
            self.sidebar.select_module(first_id)
            self.switch_to_module(first_id)

    def switch_to_module(self, module_id: str):
        if self.active_module:
            self.active_module.on_deactivate()

        mod = ModuleManager.get_module(module_id)
        if not mod:
            return

        # Lazy view creation & switching
        if module_id not in self.module_views:
            view = mod.create_view(self.workspace_frame)
            self.module_views[module_id] = view

        # Hide all other views
        for mid, v in self.module_views.items():
            if mid == module_id:
                v.grid(row=0, column=0, sticky="nsew")
            else:
                v.grid_remove()

        self.active_module = mod
        mod.on_activate()
        self.lbl_global_status.config(text=f"当前模块: {mod.name} ({mod.description})")

    def _bind_events(self):
        EventBus.subscribe("app_log", lambda msg: self._on_log_event(msg))
        EventBus.subscribe("app_status", lambda st: self.lbl_global_status.config(text=str(st)))

    def _on_log_event(self, msg: str):
        pass

    def _show_future_roadmap(self):
        messagebox.showinfo(
            "🌟 超级应用平台扩展规划", 
            "本系统已升级为现代化插件式超级工具箱架构！\n\n"
            "已集成核心模块:\n"
            "• 🚀 全能下载中心 (HF模型 / GitHub / 视频流 / 磁力链接)\n"
            "• 🎬 媒体转换与音视频处理工坊\n"
            "• ⚙️ 全局设置与网络代理中心\n\n"
            "后续可随时一键加入更多工具模块（如 AI ComfyUI 助手、批量文件处理、图片无损压缩等），即插即用！",
            parent=self
        )
