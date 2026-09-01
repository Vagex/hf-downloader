import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

from app.ui.theme import Theme
from app.core.context import AppContext
from app.modules.base import BaseAppModule, ModuleManager
from app.modules.translator.engine import TranslationEngine

class TranslatorModule(BaseAppModule):
    module_id = "translator"
    name = "🌐 智能双语对照翻译"
    icon_name = "globe"
    category = "效率工具"
    description = "文本/文档实时多引擎双语对比翻译、段落智能对齐与多格式导出"
    order = 30

    def create_view(self, parent: tk.Widget) -> tk.Widget:
        self.container = ttk.Frame(parent, padding="8")
        self._build_ui()
        return self.container

    def _build_ui(self):
        # 1. Top Control Bar (Language Selector, Engine Selector, Auto-Translate Toggle)
        top_ctrl = ttk.LabelFrame(self.container, text=" 🌐 翻译引擎与语言配置 ", padding="6")
        top_ctrl.pack(fill=tk.X, pady=(0, 6))

        # Source Language
        ttk.Label(top_ctrl, text="源语言:", font=Theme.FONT_BODY).pack(side=tk.LEFT, padx=(4, 2))
        self.lang_keys = list(TranslationEngine.LANGUAGES.keys())
        self.lang_labels = list(TranslationEngine.LANGUAGES.values())

        self.var_src_lang = tk.StringVar(value=self.lang_labels[0]) # Auto
        self.cb_src = ttk.Combobox(top_ctrl, textvariable=self.var_src_lang, values=self.lang_labels, width=16, state="readonly", font=Theme.FONT_BODY)
        self.cb_src.pack(side=tk.LEFT, padx=4)

        # Swap button
        btn_swap = ttk.Button(top_ctrl, text=" ⇄ 互换 ", command=self._swap_languages)
        btn_swap.pack(side=tk.LEFT, padx=4)

        # Dest Language
        ttk.Label(top_ctrl, text="目标语言:", font=Theme.FONT_BODY).pack(side=tk.LEFT, padx=(4, 2))
        self.var_dest_lang = tk.StringVar(value=self.lang_labels[1]) # Chinese
        self.cb_dest = ttk.Combobox(top_ctrl, textvariable=self.var_dest_lang, values=self.lang_labels[1:], width=16, state="readonly", font=Theme.FONT_BODY)
        self.cb_dest.pack(side=tk.LEFT, padx=4)

        # Engine selector
        ttk.Label(top_ctrl, text="翻译服务商:", font=Theme.FONT_BODY).pack(side=tk.LEFT, padx=(12, 2))
        self.var_engine = tk.StringVar(value="Google 极速翻译 (免Key)")
        self.cb_engine = ttk.Combobox(
            top_ctrl, 
            textvariable=self.var_engine, 
            values=["Google 极速翻译 (免Key)", "MyMemory 智能翻译 (免Key)"], 
            width=22, 
            state="readonly", 
            font=Theme.FONT_BODY
        )
        self.cb_engine.pack(side=tk.LEFT, padx=4)

        # Translate Button
        self.btn_translate = ttk.Button(top_ctrl, text=" 🚀 立即翻译 ", command=self.trigger_translation)
        self.btn_translate.pack(side=tk.RIGHT, padx=6)

        # Real-time translation check
        self.var_realtime = tk.BooleanVar(value=True)
        chk_rt = ttk.Checkbutton(top_ctrl, text="输入时实时自动翻译", variable=self.var_realtime)
        chk_rt.pack(side=tk.RIGHT, padx=6)

        # 2. Main Translation Dual-Pane Workspace (Left: Source | Right: Target)
        paned = ttk.PanedWindow(self.container, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        # Left Pane: Source Text
        left_frame = ttk.LabelFrame(paned, text=" 📝 原文内容 (支持直接粘贴、拖入文本或导入文件) ", padding="6")
        paned.add(left_frame, weight=1)

        left_toolbar = ttk.Frame(left_frame)
        left_toolbar.pack(fill=tk.X, pady=(0, 4))

        self.lbl_src_count = ttk.Label(left_toolbar, text="字数: 0 | 行数: 0", font=Theme.FONT_SMALL, foreground=Theme.TEXT_MUTED)
        self.lbl_src_count.pack(side=tk.LEFT)

        btn_import = ttk.Button(left_toolbar, text=" 📂 导入文件...", command=self._import_file)
        btn_import.pack(side=tk.RIGHT, padx=2)

        btn_paste = ttk.Button(left_toolbar, text=" 📋 粘贴剪贴板", command=self._paste_clipboard)
        btn_paste.pack(side=tk.RIGHT, padx=2)

        btn_clear_src = ttk.Button(left_toolbar, text=" 🗑️ 清空", command=self._clear_src)
        btn_clear_src.pack(side=tk.RIGHT, padx=2)

        # Text input area
        src_text_box = ttk.Frame(left_frame)
        src_text_box.pack(fill=tk.BOTH, expand=True)

        self.txt_source = tk.Text(
            src_text_box, 
            font=("Segoe UI", 10), 
            wrap=tk.WORD, 
            undo=True,
            bg="#ffffff", 
            fg="#212529",
            bd=1,
            relief=tk.SOLID
        )
        scroll_src = ttk.Scrollbar(src_text_box, orient=tk.VERTICAL, command=self.txt_source.yview)
        self.txt_source.configure(yscrollcommand=scroll_src.set)

        self.txt_source.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_src.pack(side=tk.RIGHT, fill=tk.Y)

        self.txt_source.bind("<KeyRelease>", self._on_source_text_changed)

        # Right Pane: Target Text
        right_frame = ttk.LabelFrame(paned, text=" 📖 双语对照与译文结果 ", padding="6")
        paned.add(right_frame, weight=1)

        right_toolbar = ttk.Frame(right_frame)
        right_toolbar.pack(fill=tk.X, pady=(0, 4))

        self.lbl_trans_status = ttk.Label(right_toolbar, text="状态: 就绪", font=Theme.FONT_SMALL, foreground=Theme.PRIMARY)
        self.lbl_trans_status.pack(side=tk.LEFT)

        btn_export_bilingual = ttk.Button(right_toolbar, text=" 📑 导出双语对照文档...", command=self._export_bilingual)
        btn_export_bilingual.pack(side=tk.RIGHT, padx=2)

        btn_copy_target = ttk.Button(right_toolbar, text=" 📋 复制全部译文", command=self._copy_target)
        btn_copy_target.pack(side=tk.RIGHT, padx=2)

        # Target output area
        target_text_box = ttk.Frame(right_frame)
        target_text_box.pack(fill=tk.BOTH, expand=True)

        self.txt_target = tk.Text(
            target_text_box, 
            font=("Segoe UI", 10), 
            wrap=tk.WORD, 
            bg="#fbfbfb", 
            fg="#0f5132",
            bd=1,
            relief=tk.SOLID
        )
        scroll_tgt = ttk.Scrollbar(target_text_box, orient=tk.VERTICAL, command=self.txt_target.yview)
        self.txt_target.configure(yscrollcommand=scroll_tgt.set)

        self.txt_target.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_tgt.pack(side=tk.RIGHT, fill=tk.Y)

        # Default placeholder text
        sample_text = (
            "ComfyUI is a powerful and modular stable diffusion GUI with a graph/nodes interface.\n"
            "This universal SuperTools platform allows you to manage models, download resources, and process multimedia effortlessly.\n"
            "Enjoy real-time bilingual comparison and document alignment right here!"
        )
        self.txt_source.insert("1.0", sample_text)
        self._update_stats()

        # Real-time debounce timer
        self._debounce_timer = None

    def _get_selected_src_code(self) -> str:
        label = self.var_src_lang.get()
        for k, v in TranslationEngine.LANGUAGES.items():
            if v == label:
                return k
        return "auto"

    def _get_selected_dest_code(self) -> str:
        label = self.var_dest_lang.get()
        for k, v in TranslationEngine.LANGUAGES.items():
            if v == label:
                return k
        return "zh-CN"

    def _swap_languages(self):
        cur_src = self.var_src_lang.get()
        cur_dest = self.var_dest_lang.get()
        if "自动" not in cur_src:
            self.var_src_lang.set(cur_dest)
            self.var_dest_lang.set(cur_src)
        else:
            self.var_src_lang.set(cur_dest)
            self.var_dest_lang.set(self.lang_labels[3]) # English
        
        # Swap texts
        s = self.txt_source.get("1.0", tk.END).strip()
        t = self.txt_target.get("1.0", tk.END).strip()
        if t:
            self.txt_source.delete("1.0", tk.END)
            self.txt_source.insert("1.0", t)
            self.trigger_translation()

    def _on_source_text_changed(self, event=None):
        self._update_stats()
        if self.var_realtime.get():
            if self._debounce_timer:
                self.container.after_cancel(self._debounce_timer)
            self._debounce_timer = self.container.after(600, self.trigger_translation)

    def _update_stats(self):
        text = self.txt_source.get("1.0", tk.END).rstrip("\n")
        chars = len(text)
        lines = len(text.split("\n")) if text else 0
        self.lbl_src_count.config(text=f"字数: {chars} | 段落行数: {lines}")

    def trigger_translation(self):
        text = self.txt_source.get("1.0", tk.END).strip()
        if not text:
            self.txt_target.delete("1.0", tk.END)
            self.lbl_trans_status.config(text="状态: 就绪", foreground=Theme.PRIMARY)
            return

        self.btn_translate.config(state=tk.DISABLED)
        self.lbl_trans_status.config(text="状态: 正在高速翻译中...", foreground="#0d6efd")

        src = self._get_selected_src_code()
        dest = self._get_selected_dest_code()
        engine_choice = "google" if "Google" in self.var_engine.get() else "mymemory"
        proxy = self.context.get_proxy()

        def _worker():
            try:
                res = TranslationEngine.translate_smart(
                    text=text, 
                    src=src, 
                    dest=dest, 
                    provider=engine_choice, 
                    proxy=proxy
                )
                self.container.after(0, lambda: self._apply_translation_result(res))
            except Exception as e:
                self.container.after(0, lambda: self._handle_error(str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_translation_result(self, result: str):
        self.txt_target.delete("1.0", tk.END)
        self.txt_target.insert("1.0", result)
        self.lbl_trans_status.config(text="状态: 翻译完成 ✓", foreground="#198754")
        self.btn_translate.config(state=tk.NORMAL)

    def _handle_error(self, err_msg: str):
        self.lbl_trans_status.config(text=f"状态: 翻译失败 ({err_msg[:20]})", foreground="#dc3545")
        self.btn_translate.config(state=tk.NORMAL)

    def _clear_src(self):
        self.txt_source.delete("1.0", tk.END)
        self.txt_target.delete("1.0", tk.END)
        self._update_stats()
        self.lbl_trans_status.config(text="状态: 就绪", foreground=Theme.PRIMARY)

    def _paste_clipboard(self):
        try:
            content = self.container.clipboard_get()
            if content:
                self.txt_source.insert(tk.INSERT, content)
                self._update_stats()
                self.trigger_translation()
        except Exception:
            pass

    def _copy_target(self):
        content = self.txt_target.get("1.0", tk.END).strip()
        if content:
            self.container.clipboard_clear()
            self.container.clipboard_append(content)
            messagebox.showinfo("成功", "译文已成功复制到剪贴板！", parent=self.container)

    def _import_file(self):
        path = filedialog.askopenfilename(
            title="选择要翻译的文本文件", 
            filetypes=[("Text/Markdown Files", "*.txt;*.md;*.json;*.srt;*.csv;*.py"), ("All Files", "*.*")]
        )
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.txt_source.delete("1.0", tk.END)
                self.txt_source.insert("1.0", content)
                self._update_stats()
                self.trigger_translation()
            except Exception as e:
                messagebox.showerror("读取失败", f"无法读取文件内容: {e}", parent=self.container)

    def _export_bilingual(self):
        orig = self.txt_source.get("1.0", tk.END).strip()
        trans = self.txt_target.get("1.0", tk.END).strip()
        if not orig:
            messagebox.showwarning("提示", "当前没有可导出的内容！", parent=self.container)
            return

        path = filedialog.asksaveasfilename(
            title="保存双语对照文档", 
            defaultextension=".md",
            filetypes=[("Markdown 对照文档 (*.md)", "*.md"), ("双语对照纯文本 (*.txt)", "*.txt")]
        )
        if not path:
            return

        pairs = TranslationEngine.align_bilingual_paragraphs(orig, trans)
        lines = []
        is_md = path.lower().endswith(".md")

        if is_md:
            lines.append("# 🌐 双语对照翻译报告 (Bilingual Alignment Document)\n\n")
            lines.append("> 导出时间: 自动生成 | 工具: SuperTools 万能超级工具箱 v2.0\n\n---\n\n")
            for idx, (o, t) in enumerate(pairs, 1):
                if o.strip():
                    lines.append(f"**[{idx}] 原文:**\n{o}\n\n")
                if t.strip():
                    lines.append(f"**译文:**\n> {t}\n\n---\n\n")
        else:
            lines.append("================ 双语对照翻译文档 ================\n\n")
            for idx, (o, t) in enumerate(pairs, 1):
                lines.append(f"[{idx}] 原文: {o}\n")
                lines.append(f"    译文: {t}\n\n")

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            messagebox.showinfo("导出成功", f"双语对照文档已成功导出至:\n{path}", parent=self.container)
        except Exception as e:
            messagebox.showerror("导出失败", f"导出文件时出错: {e}", parent=self.container)

ModuleManager.register(TranslatorModule)
