import sys
import tkinter as tk
from tkinter import font as tkfont

class Theme:
    # Modern Fluent Color Palette
    PRIMARY = "#0d6efd"
    PRIMARY_HOVER = "#0b5ed7"
    PRIMARY_LIGHT = "#e7f1ff"
    
    SUCCESS = "#198754"
    WARNING = "#ffc107"
    DANGER = "#dc3545"
    INFO = "#0dcaf0"
    
    BG_LIGHT = "#f8f9fa"
    BG_CARD = "#ffffff"
    BG_SIDEBAR = "#f0f2f5"
    BG_SIDEBAR_ACTIVE = "#e2e8f0"
    
    TEXT_MAIN = "#212529"
    TEXT_MUTED = "#6c757d"
    TEXT_LIGHT = "#ffffff"
    
    BORDER = "#dee2e6"

    @classmethod
    def setup_fonts(cls, root: tk.Tk):
        base_font = "Segoe UI" if sys.platform == "win32" else "Helvetica"
        cls.FONT_TITLE = tkfont.Font(root, family=base_font, size=13, weight="bold")
        cls.FONT_SUBTITLE = tkfont.Font(root, family=base_font, size=11, weight="bold")
        cls.FONT_BODY = tkfont.Font(root, family=base_font, size=9)
        cls.FONT_BODY_BOLD = tkfont.Font(root, family=base_font, size=9, weight="bold")
        cls.FONT_SMALL = tkfont.Font(root, family=base_font, size=8)
        cls.FONT_MONO = tkfont.Font(root, family="Consolas" if sys.platform == "win32" else "Courier", size=9)
