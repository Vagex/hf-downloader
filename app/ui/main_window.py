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

class StdoutRedirector:
    """Redirects sys.stdout and sys.stderr to the GUI live log drawer."""
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def write(self, text):
        if text:
            try:
                self.log_callback(text)
            except Exception:
                pass

    def flush(self):
        pass


class MainWindow(tk.Tk):
    """Main Workbench window for the Universal Super App Platform."""
    def __init__(self):
        super().__init__()
        self.title("🌟 SuperTools 万能超级工具箱 v2.0")
        self.geometry("1280x860")
        self.minsize(1050, 720)

        Theme.setup_fonts(self)
        self.context = AppContext(self)
        self.module_views: Dict[str, tk.Widget] = {}
        self.active_module: Optional[BaseAppModule] = None
        self.is_terminal_visible: bool = False
        self.auto_scroll_terminal: bool = True

        self._build_workbench()
        self._init_modules()
        self._bind_events()
        self._setup_stdout_redirect()
        self.protocol("WM_DELETE_WINDOW", self._on_window_closing)

    def _build_workbench(self):
        # Configure root grid
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Top Header Control Bar
        top_bar = tk.Frame(self, height=44, bg=Theme.BG_CARD, bd=0, relief=tk.FLAT)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        # Current active module indicator
        self.lbl_active_tab = tk.Label(
            top_bar, 
            text="  📁 当前功能: 🚀 全能下载中心", 
            font=Theme.FONT_SUBTITLE, 
            bg=Theme.BG_CARD, 
            fg=Theme.PRIMARY
        )
        self.lbl_active_tab.pack(side=tk.LEFT, padx=(10, 6), pady=8)

        sep_top = tk.Frame(top_bar, width=1, bg=Theme.BORDER)
        sep_top.pack(side=tk.LEFT, fill=tk.Y, pady=8, padx=6)

        self.lbl_global_status = tk.Label(
            top_bar, 
            text="就绪 · 支持断点续传与多引擎加速", 
            font=Theme.FONT_BODY, 
            bg=Theme.BG_CARD, 
            fg=Theme.TEXT_MUTED
        )
        self.lbl_global_status.pack(side=tk.LEFT, padx=6)

        # Right header tools
        btn_feedback = ttk.Button(top_bar, text=" 💡 更多扩展...", command=self._show_future_roadmap)
        btn_feedback.pack(side=tk.RIGHT, padx=(4, 12), pady=6)

        # Toggle Terminal Drawer Button
        self.btn_toggle_terminal = ttk.Button(top_bar, text=" 📜 显示实时终端 ", command=self.toggle_terminal_drawer)
        self.btn_toggle_terminal.pack(side=tk.RIGHT, padx=4, pady=6)

        # Quick Proxy indicator on the top right
        self.var_top_proxy = tk.StringVar(value=self.context.config.get("proxy", "直连"))
        lbl_p = tk.Label(top_bar, text="全局代理:", font=Theme.FONT_BODY, bg=Theme.BG_CARD, fg=Theme.TEXT_MUTED)
        lbl_p.pack(side=tk.RIGHT, padx=(6, 2), pady=8)

        cb_top_p = ttk.Combobox(
            top_bar, 
            textvariable=self.var_top_proxy, 
            values=self.context.config.get("proxies_list", ["不使用代理 (直连)"]), 
            width=18, 
            state="readonly",
            font=Theme.FONT_SMALL
        )
        cb_top_p.pack(side=tk.RIGHT, padx=(2, 6), pady=8)
        cb_top_p.bind("<<ComboboxSelected>>", self._on_top_proxy_changed)

        # 2. Left Sidebar Navigation
        self.sidebar = Sidebar(self, on_module_selected=self.switch_to_module, width=220)
        self.sidebar.grid(row=1, column=0, sticky="nsew")

        # 3. Right Main Area (Split into Workspace + Collapsible Terminal Drawer)
        right_main_container = tk.Frame(self, bg=Theme.BG_LIGHT)
        right_main_container.grid(row=1, column=1, sticky="nsew")
        right_main_container.columnconfigure(0, weight=1)
        right_main_container.rowconfigure(0, weight=1)

        # Dynamic Workspace Frame
        self.workspace_frame = tk.Frame(right_main_container, bg=Theme.BG_LIGHT)
        self.workspace_frame.grid(row=0, column=0, sticky="nsew")
        self.workspace_frame.columnconfigure(0, weight=1)
        self.workspace_frame.rowconfigure(0, weight=1)

        # Collapsible Live Terminal Drawer Frame (Initially not packed/hidden)
        self.terminal_drawer = tk.Frame(right_main_container, height=220, bg="#181818", relief=tk.SUNKEN, bd=1)
        self._build_terminal_drawer(self.terminal_drawer)

        # 4. Global Bottom Progress & Status Bar (Docked across all modules)
        self.status_bar = tk.Frame(self, bg=Theme.BG_CARD, height=36, bd=1, relief=tk.SOLID)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.status_bar.columnconfigure(1, weight=1) # Progress bar auto expands

        # Col 0: Status message icon & text
        left_status_frame = tk.Frame(self.status_bar, bg=Theme.BG_CARD)
        left_status_frame.grid(row=0, column=0, sticky="w", padx=(10, 8), pady=4)

        self.lbl_global_status_icon = tk.Label(
            left_status_frame, 
            text="🟢", 
            font=("Segoe UI Emoji", 9), 
            bg=Theme.BG_CARD
        )
        self.lbl_global_status_icon.pack(side=tk.LEFT, padx=(0, 4))

        self.lbl_global_status_text = tk.Label(
            left_status_frame, 
            text="状态: 就绪", 
            font=Theme.FONT_SMALL, 
            bg=Theme.BG_CARD, 
            fg=Theme.TEXT_MAIN
        )
        self.lbl_global_status_text.pack(side=tk.LEFT)

        # Col 1: Universal Global Dynamic Progress Bar
        self.global_progress_bar = ttk.Progressbar(
            self.status_bar, 
            mode="determinate", 
            value=0.0
        )
        self.global_progress_bar.grid(row=0, column=1, sticky="ew", padx=(4, 8), pady=6)

        # Col 2: Progress Percentage & Speed Metrics
        metrics_frame = tk.Frame(self.status_bar, bg=Theme.BG_CARD)
        metrics_frame.grid(row=0, column=2, sticky="e", padx=(4, 8), pady=4)

        self.lbl_global_progress_text = tk.Label(
            metrics_frame, 
            text="0.0%", 
            font=Theme.FONT_SMALL, 
            bg=Theme.BG_CARD, 
            fg=Theme.PRIMARY
        )
        self.lbl_global_progress_text.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_global_speed_text = tk.Label(
            metrics_frame, 
            text="0.0 KB/s", 
            font=Theme.FONT_SMALL, 
            bg=Theme.BG_CARD, 
            fg=Theme.TEXT_MUTED
        )
        self.lbl_global_speed_text.pack(side=tk.LEFT, padx=(0, 8))

        # Col 3: Right terminal button
        self.btn_bottom_term = tk.Button(
            self.status_bar,
            text="📜 终端日志",
            font=Theme.FONT_SMALL,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            bg=Theme.BG_CARD,
            fg=Theme.PRIMARY,
            command=self.toggle_terminal_drawer
        )
        self.btn_bottom_term.grid(row=0, column=3, sticky="e", padx=(0, 10), pady=4)

    def set_progress_indeterminate(self, status_text: str = ""):
        def _ui():
            self.lbl_global_status_icon.config(text="🔄")
            if status_text:
                self.lbl_global_status_text.config(text=f"状态: {status_text}", fg=Theme.PRIMARY)
                self.lbl_global_status.config(text=status_text)
            self.lbl_global_progress_text.config(text="处理中...")
            self.lbl_global_speed_text.config(text="")
            self.global_progress_bar.config(mode="indeterminate")
            self.global_progress_bar.start(10)
        self.after(0, _ui)

    def set_progress_determinate(self, value: float, status_text: str = "", speed_text: str = "", progress_text: str = ""):
        def _ui():
            self.global_progress_bar.stop()
            self.global_progress_bar.config(mode="determinate", value=value)
            if status_text:
                self.lbl_global_status_icon.config(text="🚀")
                self.lbl_global_status_text.config(text=f"状态: {status_text}", fg=Theme.TEXT_MAIN)
                self.lbl_global_status.config(text=status_text)
            if progress_text:
                self.lbl_global_progress_text.config(text=progress_text)
            else:
                self.lbl_global_progress_text.config(text=f"{value:.1f}%")
            if speed_text:
                self.lbl_global_speed_text.config(text=speed_text)
        self.after(0, _ui)

    def stop_progress(self, status_text: str = "就绪", value: float = 100.0):
        def _ui():
            self.global_progress_bar.stop()
            self.global_progress_bar.config(mode="determinate", value=value)
            self.lbl_global_status_icon.config(text="🟢" if value >= 100.0 else "🛑")
            self.lbl_global_status_text.config(text=f"状态: {status_text}", fg="#198754" if value >= 100.0 else Theme.TEXT_MAIN)
            self.lbl_global_status.config(text=status_text)
            if value >= 100.0:
                self.lbl_global_progress_text.config(text="100.0%")
        self.after(0, _ui)

    def reset_progress(self, status_text: str = "就绪"):
        def _ui():
            self.global_progress_bar.stop()
            self.global_progress_bar.config(mode="determinate", value=0.0)
            self.lbl_global_status_icon.config(text="🟢")
            self.lbl_global_status_text.config(text=f"状态: {status_text}", fg=Theme.TEXT_MUTED)
            self.lbl_global_progress_text.config(text="0.0%")
            self.lbl_global_speed_text.config(text="0.0 KB/s")
        self.after(0, _ui)

    def _build_terminal_drawer(self, parent):
        # Header bar of terminal drawer
        header = tk.Frame(parent, bg="#252526", height=28)
        header.pack(fill=tk.X)

        lbl_title = tk.Label(
            header, 
            text=" 🖥️ 实时运行终端输出 (Live Console)", 
            font=("Segoe UI", 9, "bold"), 
            bg="#252526", 
            fg="#cccccc"
        )
        lbl_title.pack(side=tk.LEFT, padx=6, pady=3)

        btn_close = tk.Button(
            header,
            text="✕ 收起",
            font=("Segoe UI", 8),
            bg="#252526",
            fg="#999999",
            activebackground="#333333",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self.toggle_terminal_drawer
        )
        btn_close.pack(side=tk.RIGHT, padx=6, pady=2)

        self.btn_scroll = tk.Button(
            header,
            text="📌 自动滚屏: 开",
            font=("Segoe UI", 8),
            bg="#252526",
            fg="#38d430",
            activebackground="#333333",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self._toggle_auto_scroll
        )
        self.btn_scroll.pack(side=tk.RIGHT, padx=4, pady=2)

        btn_copy = tk.Button(
            header,
            text="📋 复制全部",
            font=("Segoe UI", 8),
            bg="#252526",
            fg="#999999",
            activebackground="#333333",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self._copy_terminal_log
        )
        btn_copy.pack(side=tk.RIGHT, padx=4, pady=2)

        btn_clear = tk.Button(
            header,
            text="🗑️ 清空",
            font=("Segoe UI", 8),
            bg="#252526",
            fg="#999999",
            activebackground="#333333",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self._clear_terminal_log
        )
        btn_clear.pack(side=tk.RIGHT, padx=4, pady=2)

        # Terminal Text Area
        body = tk.Frame(parent, bg="#181818")
        body.pack(fill=tk.BOTH, expand=True)

        self.txt_terminal = tk.Text(
            body, 
            font=("Consolas", 9), 
            bg="#181818", 
            fg="#38d430", 
            insertbackground="#ffffff", 
            wrap=tk.WORD,
            bd=0,
            highlightthickness=0
        )
        scroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.txt_terminal.yview)
        self.txt_terminal.configure(yscrollcommand=scroll.set)

        self.txt_terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.txt_terminal.insert(tk.END, "[SuperTools v2.0] 实时运行终端已就绪。所有后台输出与引擎日志将实时汇聚于此。\n")

    def toggle_terminal_drawer(self):
        if self.is_terminal_visible:
            # Hide drawer
            self.terminal_drawer.grid_remove()
            self.is_terminal_visible = False
            self.btn_toggle_terminal.config(text=" 📜 显示实时终端 ")
            self.btn_bottom_term.config(text="📜 终端日志: [收起]")
        else:
            # Show drawer
            self.terminal_drawer.grid(row=1, column=0, sticky="sew")
            self.is_terminal_visible = True
            self.btn_toggle_terminal.config(text=" ✕ 收起终端 ")
            self.btn_bottom_term.config(text="📜 终端日志: [已展开]")

    def _toggle_auto_scroll(self):
        self.auto_scroll_terminal = not self.auto_scroll_terminal
        if self.auto_scroll_terminal:
            self.btn_scroll.config(text="📌 自动滚屏: 开", fg="#38d430")
        else:
            self.btn_scroll.config(text="📌 自动滚屏: 关", fg="#999999")

    def _clear_terminal_log(self):
        self.txt_terminal.delete("1.0", tk.END)

    def _copy_terminal_log(self):
        content = self.txt_terminal.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("已复制", "实时终端日志已复制到剪贴板！", parent=self)

    def _append_terminal_output(self, text: str):
        def _insert():
            try:
                self.txt_terminal.insert(tk.END, text)
                if self.auto_scroll_terminal:
                    self.txt_terminal.see(tk.END)
            except Exception:
                pass
        self.after(0, _insert)

    def _setup_stdout_redirect(self):
        sys.stdout = StdoutRedirector(self._append_terminal_output)
        sys.stderr = StdoutRedirector(self._append_terminal_output)

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
        self.lbl_active_tab.config(text=f"  📁 当前功能: {mod.name}")
        self.lbl_global_status.config(text=f"{mod.description}")

    def _on_top_proxy_changed(self, event=None):
        val = self.var_top_proxy.get().strip()
        self.context.config.set("proxy", val)
        self.context.log(f"[*] 全局代理已切换为: {val}")

    def _bind_events(self):
        EventBus.subscribe("app_log", lambda msg: self._append_terminal_output(f"{msg}\n"))
        EventBus.subscribe("app_status", lambda st: self.lbl_global_status.config(text=str(st)))

    def _on_window_closing(self):
        # Restore standard streams
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        # Notify all modules to save their states and release locks
        for mod in ModuleManager.get_all_modules():
            try:
                mod.on_shutdown()
            except Exception:
                pass

        try:
            self.destroy()
        except Exception:
            pass

        # Force clean process termination
        import os
        os._exit(0)

    def _show_future_roadmap(self):
        messagebox.showinfo(
            "🌟 超级应用平台扩展规划", 
            "本系统已升级为现代化插件式超级工具箱架构！\n\n"
            "已集成核心模块:\n"
            "• 🚀 全能下载中心 (HF模型 / GitHub / 视频流 / 磁力链接)\n"
            "• 🎬 媒体转换与音视频处理工坊\n"
            "• ⚙️ 全局设置与环境部署中心\n\n"
            "后续可随时一键加入更多工具模块（如 AI ComfyUI 助手、批量文件处理、图片无损压缩等），即插即用！",
            parent=self
        )
