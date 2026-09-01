import tkinter as tk
from tkinter import ttk

class UniversalContextMenu:
    """Provides a native, modern right-click context menu (Cut, Copy, Paste, Select All, Clear)
    for all Entry, Text, and Combobox widgets globally across the entire platform.
    """

    @classmethod
    def setup(cls, root: tk.Tk):
        """Globally registers right-click context menu bindings on all widget classes."""
        root.bind_class("Text", "<Button-3>", cls.on_right_click, add="+")
        root.bind_class("Entry", "<Button-3>", cls.on_right_click, add="+")
        root.bind_class("TEntry", "<Button-3>", cls.on_right_click, add="+")
        root.bind_class("TCombobox", "<Button-3>", cls.on_right_click, add="+")

    @classmethod
    def attach_to_widget(cls, widget: tk.Widget):
        """Explicitly attaches right-click context menu to a specific widget instance."""
        widget.bind("<Button-3>", cls.on_right_click, add="+")

    @classmethod
    def on_right_click(cls, event):
        widget = event.widget
        if not widget:
            return

        # Ensure widget receives focus on right click
        try:
            widget.focus_set()
        except Exception:
            pass

        # Create modern styled menu
        menu = tk.Menu(
            widget, 
            tearoff=0, 
            bg="#ffffff", 
            fg="#212529", 
            activebackground="#0d6efd", 
            activeforeground="#ffffff", 
            font=("Segoe UI", 9)
        )

        # Check widget state
        is_readonly = False
        try:
            state = str(widget.cget("state"))
            if state in ("readonly", "disabled"):
                is_readonly = True
        except Exception:
            pass

        # Check selection state
        has_selection = False
        try:
            if isinstance(widget, tk.Text):
                try:
                    sel = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                    has_selection = bool(sel)
                except Exception:
                    has_selection = False
            elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
                if widget.select_present():
                    has_selection = True
        except Exception:
            has_selection = False

        # Check clipboard content
        has_clipboard = False
        try:
            cb = widget.clipboard_get()
            has_clipboard = bool(cb)
        except Exception:
            has_clipboard = False

        # 1. 剪切 (Cut)
        def do_cut():
            try:
                if has_selection and not is_readonly:
                    widget.event_generate("<<Cut>>")
            except Exception:
                pass

        # 2. 复制 (Copy)
        def do_copy():
            try:
                if has_selection:
                    widget.event_generate("<<Copy>>")
                else:
                    # If nothing selected, copy all content
                    if isinstance(widget, tk.Text):
                        full_txt = widget.get("1.0", tk.END).rstrip("\n")
                    else:
                        full_txt = widget.get()
                    if full_txt:
                        widget.clipboard_clear()
                        widget.clipboard_append(full_txt)
            except Exception:
                pass

        # 3. 粘贴 (Paste)
        def do_paste():
            try:
                if not is_readonly:
                    widget.event_generate("<<Paste>>")
            except Exception:
                pass

        # 4. 全选 (Select All)
        def do_select_all():
            try:
                if isinstance(widget, tk.Text):
                    widget.tag_add(tk.SEL, "1.0", "end-1c")
                    widget.mark_set(tk.INSERT, "1.0")
                elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
                    widget.select_range(0, tk.END)
                    widget.icursor(tk.END)
            except Exception:
                pass

        # 5. 清空 (Clear)
        def do_clear():
            try:
                if not is_readonly:
                    if isinstance(widget, tk.Text):
                        widget.delete("1.0", tk.END)
                    elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
                        widget.delete(0, tk.END)
            except Exception:
                pass

        # Build menu items
        menu.add_command(
            label="✂️ 剪切 (Cut)", 
            command=do_cut, 
            state=tk.NORMAL if (has_selection and not is_readonly) else tk.DISABLED, 
            accelerator="Ctrl+X"
        )
        menu.add_command(
            label="📋 复制 (Copy)", 
            command=do_copy, 
            state=tk.NORMAL, 
            accelerator="Ctrl+C"
        )
        menu.add_command(
            label="📥 粘贴 (Paste)", 
            command=do_paste, 
            state=tk.NORMAL if (has_clipboard and not is_readonly) else tk.DISABLED, 
            accelerator="Ctrl+V"
        )
        menu.add_separator()
        menu.add_command(
            label="🔘 全选 (Select All)", 
            command=do_select_all, 
            accelerator="Ctrl+A"
        )
        menu.add_command(
            label="🗑️ 清空 (Clear)", 
            command=do_clear, 
            state=tk.NORMAL if not is_readonly else tk.DISABLED
        )

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

        return "break"
