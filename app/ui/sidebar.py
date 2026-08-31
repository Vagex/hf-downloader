import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict
from app.ui.theme import Theme
from app.modules.base import BaseAppModule

class Sidebar(ttk.Frame):
    """Modern macOS/Fluent style navigation sidebar for the Super App."""
    def __init__(self, parent, on_module_selected: Callable[[str], None], **kwargs):
        super().__init__(parent, **kwargs)
        self.on_module_selected = on_module_selected
        self.buttons: Dict[str, tk.Button] = {}
        self.active_module_id: str = ""

        self._build_ui()

    def _build_ui(self):
        # App Branding Header
        brand_frame = tk.Frame(self, bg=Theme.BG_SIDEBAR, pady=12, padx=10)
        brand_frame.pack(fill=tk.X)

        lbl_logo = tk.Label(
            brand_frame, 
            text="🌟 万能超级工具箱", 
            font=("Segoe UI", 12, "bold"), 
            bg=Theme.BG_SIDEBAR, 
            fg=Theme.PRIMARY,
            anchor="w"
        )
        lbl_logo.pack(fill=tk.X)

        lbl_sub = tk.Label(
            brand_frame, 
            text="Universal Super App v2.0", 
            font=("Segoe UI", 8), 
            bg=Theme.BG_SIDEBAR, 
            fg=Theme.TEXT_MUTED,
            anchor="w"
        )
        lbl_sub.pack(fill=tk.X)

        # Separator line
        sep = tk.Frame(self, height=1, bg=Theme.BORDER)
        sep.pack(fill=tk.X, padx=8, pady=(4, 8))

        # Scrollable / list container for module navigation buttons
        self.nav_container = tk.Frame(self, bg=Theme.BG_SIDEBAR)
        self.nav_container.pack(fill=tk.BOTH, expand=True, padx=6)

        # Bottom section for settings
        self.bottom_container = tk.Frame(self, bg=Theme.BG_SIDEBAR, pady=6)
        self.bottom_container.pack(side=tk.BOTTOM, fill=tk.X, padx=6)

    def set_modules(self, modules: List[BaseAppModule]):
        for widget in self.nav_container.winfo_children():
            widget.destroy()
        self.buttons.clear()

        # Group modules by category or list directly
        for mod in modules:
            btn = tk.Button(
                self.nav_container,
                text=f"  {mod.name}",
                font=("Segoe UI", 10, "bold" if mod.order < 50 else "normal"),
                anchor="w",
                padx=12,
                pady=8,
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                bg=Theme.BG_SIDEBAR,
                fg=Theme.TEXT_MAIN,
                activebackground=Theme.BG_SIDEBAR_ACTIVE,
                activeforeground=Theme.PRIMARY,
                command=lambda mid=mod.module_id: self._on_btn_click(mid)
            )
            btn.pack(fill=tk.X, pady=2)
            self.buttons[mod.module_id] = btn

    def select_module(self, module_id: str):
        self.active_module_id = module_id
        for mid, btn in self.buttons.items():
            if mid == module_id:
                btn.config(bg=Theme.PRIMARY_LIGHT, fg=Theme.PRIMARY, relief=tk.SOLID, bd=1)
            else:
                btn.config(bg=Theme.BG_SIDEBAR, fg=Theme.TEXT_MAIN, relief=tk.FLAT, bd=0)

    def _on_btn_click(self, module_id: str):
        if module_id != self.active_module_id:
            self.select_module(module_id)
            if self.on_module_selected:
                self.on_module_selected(module_id)
