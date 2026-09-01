import os
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Dict, Any

from app.ui.theme import Theme
from app.core.context import AppContext
from app.modules.base import BaseAppModule, ModuleManager
from app.modules.translator.engine import TranslationEngine

class TranslatorModule(BaseAppModule):
    module_id = "translator"
    name = "🌐 智能双语对照翻译"
    icon_name = "globe"
    category = "效率工具"
    description = "多引擎自由切换(Bing/有道/百度/Google/DeepSeek)、文档双语对照与导出"
    order = 30

    def create_view(self, parent: tk.Widget) -> tk.Widget:
        self.container = ttk.Frame(parent, padding="8")
        self._load_preferences()
        self._build_ui()
        return self.container

    def _load_preferences(self):
        self.llm_config = {
            "api_key": self.context.config.get("llm_api_key", ""),
            "base_url": self.context.config.get("llm_base_url", "https://api.deepseek.com/v1"),
            "model": self.context.config.get("llm_model", "deepseek-chat")
        }
        self.saved_engine_key = self.context.config.get("default_translator_engine", "bing")
        self.saved_src_lang = self.context.config.get("default_src_lang", TranslationEngine.LANGUAGES["auto"])
        self.saved_dest_lang = self.context.config.get("default_dest_lang", TranslationEngine.LANGUAGES["zh-CN"])

    def _save_preferences(self):
        self.context.config.set("llm_api_key", self.llm_config.get("api_key", ""))
        self.context.config.set("llm_base_url", self.llm_config.get("base_url", ""))
        self.context.config.set("llm_model", self.llm_config.get("model", ""))
        self.context.config.set("default_translator_engine", self._get_selected_provider_key())
        self.context.config.set("default_src_lang", self.var_src_lang.get())
        self.context.config.set("default_dest_lang", self.var_dest_lang.get())

    def _build_ui(self):
        # 1. Top Control Bar (Responsive Elastic Grid Layout)
        top_ctrl = ttk.LabelFrame(self.container, text=" 🌐 翻译引擎与语言配置 ", padding="6")
        top_ctrl.pack(fill=tk.X, pady=(0, 6))

        # Col 0-1: Source Language
        ttk.Label(top_ctrl, text="源语言:", font=Theme.FONT_BODY).grid(row=0, column=0, sticky=tk.W, padx=(2, 2), pady=2)
        self.lang_labels = list(TranslationEngine.LANGUAGES.values())
        init_src = self.saved_src_lang if self.saved_src_lang in self.lang_labels else self.lang_labels[0]
        self.var_src_lang = tk.StringVar(value=init_src) # Auto
        self.cb_src = ttk.Combobox(top_ctrl, textvariable=self.var_src_lang, values=self.lang_labels, width=15, state="readonly", font=Theme.FONT_BODY)
        self.cb_src.grid(row=0, column=1, sticky=tk.W, padx=2, pady=2)
        self.cb_src.bind("<<ComboboxSelected>>", lambda e: (self._save_preferences(), self.trigger_translation()))

        # Col 2: Swap button
        btn_swap = ttk.Button(top_ctrl, text=" ⇄ ", width=4, command=self._swap_languages)
        btn_swap.grid(row=0, column=2, padx=2, pady=2)

        # Col 3-4: Dest Language
        ttk.Label(top_ctrl, text="目标语言:", font=Theme.FONT_BODY).grid(row=0, column=3, sticky=tk.W, padx=(6, 2), pady=2)
        init_dest = self.saved_dest_lang if self.saved_dest_lang in self.lang_labels else self.lang_labels[1]
        self.var_dest_lang = tk.StringVar(value=init_dest) # Chinese
        self.cb_dest = ttk.Combobox(top_ctrl, textvariable=self.var_dest_lang, values=self.lang_labels[1:], width=15, state="readonly", font=Theme.FONT_BODY)
        self.cb_dest.grid(row=0, column=4, sticky=tk.W, padx=2, pady=2)
        self.cb_dest.bind("<<ComboboxSelected>>", lambda e: (self._save_preferences(), self.trigger_translation()))

        # Col 5-6: Translation Engine Selector with Dynamic AI Model Label
        ttk.Label(top_ctrl, text="翻译引擎:", font=Theme.FONT_BODY).grid(row=0, column=5, sticky=tk.W, padx=(8, 2), pady=2)
        self.provider_keys = list(TranslationEngine.PROVIDERS.keys())

        # Build dynamic provider list
        self.cb_engine = ttk.Combobox(
            top_ctrl, 
            width=30,
            state="readonly", 
            font=Theme.FONT_BODY
        )
        self._refresh_engine_combobox()
        self.cb_engine.grid(row=0, column=6, sticky=tk.W, padx=4, pady=2)
        self.cb_engine.bind("<<ComboboxSelected>>", self._on_engine_changed)

        # Col 7: LLM config button
        btn_llm_cfg = ttk.Button(top_ctrl, text=" 🤖 AI配置...", command=self._open_llm_config_dialog)
        btn_llm_cfg.grid(row=0, column=7, padx=2, pady=2)

        # Col 8: Real-time checkbox
        self.var_realtime = tk.BooleanVar(value=True)
        chk_rt = ttk.Checkbutton(top_ctrl, text="实时翻译", variable=self.var_realtime)
        chk_rt.grid(row=0, column=8, padx=4, pady=2)

        # Col 9: Translate / Abort Button (Dynamic Switching)
        self.btn_translate = ttk.Button(top_ctrl, text=" 🚀 立即翻译 ", command=self.toggle_translation)
        self.btn_translate.grid(row=0, column=9, padx=(4, 2), pady=2)

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
            "Enjoy real-time bilingual comparison and multi-engine translation right here!"
        )
        self.txt_source.insert("1.0", sample_text)
        self._update_stats()

        # Real-time debounce timer
        self._debounce_timer = None

    def _refresh_engine_combobox(self, select_key: Optional[str] = None):
        """Dynamically refreshes the engine combobox values, embedding the actual configured model name."""
        cur_model = self.llm_config.get("model", "")
        self.provider_labels = []
        for k in self.provider_keys:
            self.provider_labels.append(TranslationEngine.get_provider_display_name(k, cur_model))

        self.cb_engine["values"] = self.provider_labels

        target_key = select_key or self.saved_engine_key or "bing"
        selected_label = TranslationEngine.get_provider_display_name(target_key, cur_model)
        if selected_label not in self.provider_labels:
            selected_label = self.provider_labels[0]

        if not hasattr(self, "var_engine"):
            self.var_engine = tk.StringVar(value=selected_label)
            self.cb_engine["textvariable"] = self.var_engine
        else:
            self.var_engine.set(selected_label)

    def _get_selected_provider_key(self) -> str:
        cur_label = self.var_engine.get()
        if "AI 大模型" in cur_label or "自定义" in cur_label:
            return "custom_llm"
        for k, v in TranslationEngine.PROVIDERS.items():
            if v == cur_label:
                return k
        return "bing"

    def _on_engine_changed(self, event=None):
        self._save_preferences()
        if self._get_selected_provider_key() == "custom_llm" and not self.llm_config.get("api_key"):
            self._open_llm_config_dialog()
        else:
            self.trigger_translation()

    def _open_llm_config_dialog(self):
        dlg = tk.Toplevel(self.container)
        dlg.title("🤖 自定义 AI 大模型翻译配置 (自动拉取可用模型)")
        dlg.geometry("580x420")
        dlg.minsize(540, 380)
        dlg.transient(self.container.winfo_toplevel())
        dlg.grab_set()

        # Center dialog
        sw = dlg.winfo_screenwidth()
        sh = dlg.winfo_screenheight()
        x = max(40, (sw - 580) // 2)
        y = max(40, (sh - 420) // 2)
        dlg.geometry(f"+{x}+{y}")

        f = ttk.Frame(dlg, padding="16")
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="🤖 配置自定义 AI 翻译模型 (支持自动拉取在线模型)", font=Theme.FONT_SUBTITLE).pack(anchor=tk.W, pady=(0, 10))

        # Provider Presets
        row0 = ttk.Frame(f)
        row0.pack(fill=tk.X, pady=3)
        ttk.Label(row0, text="服务商预设:", width=13, font=Theme.FONT_BODY).pack(side=tk.LEFT)
        
        presets = {
            "DeepSeek 官方": ("https://api.deepseek.com/v1", "deepseek-chat"),
            "阿里通义千问 (DashScope)": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
            "OpenAI 官方": ("https://api.openai.com/v1", "gpt-4o-mini"),
            "Moonshot 月之暗面 (Kimi)": ("https://api.moonshot.cn/v1", "moonshot-v1-8k"),
            "智谱 AI (GLM)": ("https://open.bigmodel.cn/api/paas/v4", "glm-4-flash"),
            "OpenRouter 聚合平台": ("https://openrouter.ai/api/v1", "openai/gpt-4o-mini"),
            "本地 Ollama (免Key)": ("http://127.0.0.1:11434/v1", "qwen2.5:latest"),
            "自定义 API 端点": ("", "")
        }
        var_preset = tk.StringVar(value=list(presets.keys())[0])
        cb_preset = ttk.Combobox(row0, textvariable=var_preset, values=list(presets.keys()), state="readonly", font=Theme.FONT_BODY)
        cb_preset.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Base URL
        row1 = ttk.Frame(f)
        row1.pack(fill=tk.X, pady=3)
        ttk.Label(row1, text="API Base URL:", width=13, font=Theme.FONT_BODY).pack(side=tk.LEFT)
        var_url = tk.StringVar(value=self.llm_config.get("base_url", "https://api.deepseek.com/v1"))
        entry_url = ttk.Entry(row1, textvariable=var_url, font=Theme.FONT_BODY)
        entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def _on_preset_change(event=None):
            p_name = var_preset.get()
            if p_name in presets and presets[p_name][0]:
                var_url.set(presets[p_name][0])
                if presets[p_name][1]:
                    var_model.set(presets[p_name][1])
                # Automatically populate offline models for this preset
                preset_models = TranslationEngine.get_offline_preset_models(presets[p_name][0])
                cb_model["values"] = preset_models
                lbl_fetch_status.config(text=f"已加载 [{p_name}] 官方精选模型列表 (共 {len(preset_models)} 款)", foreground=Theme.PRIMARY)
        cb_preset.bind("<<ComboboxSelected>>", _on_preset_change)

        # API Key
        row2 = ttk.Frame(f)
        row2.pack(fill=tk.X, pady=3)
        ttk.Label(row2, text="API Key:", width=13, font=Theme.FONT_BODY).pack(side=tk.LEFT)
        var_key = tk.StringVar(value=self.llm_config.get("api_key", ""))
        entry_key = ttk.Entry(row2, textvariable=var_key, show="*", font=Theme.FONT_BODY)
        entry_key.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Model Name + Auto Fetch Button
        row3 = ttk.Frame(f)
        row3.pack(fill=tk.X, pady=3)
        ttk.Label(row3, text="Model Name:", width=13, font=Theme.FONT_BODY).pack(side=tk.LEFT)
        var_model = tk.StringVar(value=self.llm_config.get("model", "deepseek-chat"))
        
        # Initial models list
        init_preset_models = TranslationEngine.get_offline_preset_models(var_url.get())
        cb_model = ttk.Combobox(row3, textvariable=var_model, values=init_preset_models, font=Theme.FONT_BODY)
        cb_model.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_fetch_models = ttk.Button(row3, text=" 🔄 自动拉取模型 ")
        btn_fetch_models.pack(side=tk.RIGHT, padx=(4, 0))

        # Status & Help Box
        lbl_fetch_status = ttk.Label(f, text="就绪 · 支持免Key直接选择官方模型，或点击【自动拉取模型】联网获取账户所有模型", font=Theme.FONT_SMALL, foreground=Theme.PRIMARY)
        lbl_fetch_status.pack(anchor=tk.W, pady=(4, 2))

        dlg._fetch_cancel_event = None
        dlg._is_fetching = False

        def _fetch_models_worker():
            if getattr(dlg, "_is_fetching", False):
                if dlg._fetch_cancel_event:
                    dlg._fetch_cancel_event.set()
                dlg._is_fetching = False
                btn_fetch_models.config(text=" 🔄 自动拉取模型 ")
                lbl_fetch_status.config(text="已手动取消拉取模型 🛑", foreground="#dc3545")
                return

            u = var_url.get().strip()
            k = var_key.get().strip()
            if not u:
                messagebox.showwarning("提示", "请先输入 API Base URL！", parent=dlg)
                return

            dlg._fetch_cancel_event = threading.Event()
            dlg._is_fetching = True
            btn_fetch_models.config(text=" 🛑 取消拉取 ")
            lbl_fetch_status.config(text=f"正在连接 {u}/models 查询账户可用模型 (可点击取消)...", foreground="#0d6efd")
            cancel_ev = dlg._fetch_cancel_event

            def _do_fetch():
                proxy = self.context.get_proxy()
                try:
                    models, is_live = TranslationEngine.fetch_remote_models(base_url=u, api_key=k, proxy=proxy)
                    if not cancel_ev.is_set():
                        def _update_ui():
                            dlg._is_fetching = False
                            btn_fetch_models.config(text=" 🔄 自动拉取模型 ")
                            if models:
                                cb_model["values"] = models
                                if var_model.get() not in models:
                                    var_model.set(models[0])
                                if is_live:
                                    lbl_fetch_status.config(text=f"✓ 成功在线联网拉取到 {len(models)} 个账户可用模型！", foreground="#198754")
                                    messagebox.showinfo("拉取成功", f"成功连接 API 账户并拉取到 {len(models)} 个可用模型！\n已自动填入下拉选择列表中。", parent=dlg)
                                else:
                                    lbl_fetch_status.config(text=f"💡 已为您加载该端点的 {len(models)} 款官方精选模型列表！(填入 Key 可联网拉取账户所有专属模型)", foreground="#0d6efd")
                                    messagebox.showinfo("精选模型已就绪", f"未配置 API Key 或服务端需鉴权。\n\n已为您自动加载该服务商的 {len(models)} 款官方精选模型清单！\n您可直接在下拉框中选择使用。", parent=dlg)
                            else:
                                lbl_fetch_status.config(text="未解析到模型列表，请手动输入模型名称。", foreground="#dc3545")
                        dlg.after(0, _update_ui)
                except Exception as ex:
                    if not cancel_ev.is_set():
                        def _err_ui():
                            dlg._is_fetching = False
                            btn_fetch_models.config(text=" 🔄 自动拉取模型 ")
                            lbl_fetch_status.config(text=f"拉取失败: {str(ex)[:30]}", foreground="#dc3545")
                            messagebox.showerror("拉取失败", f"无法从目标端点获取模型列表:\n{ex}\n\n💡 检查建议:\n1. 确认 Base URL 格式 (通常形如 https://api.xxx.com/v1)；\n2. 确认 API Key 是否正确有效；\n3. 本地 Ollama 确保服务已在后台启动。", parent=dlg)
                        dlg.after(0, _err_ui)

            threading.Thread(target=_do_fetch, daemon=True).start()

        btn_fetch_models.config(command=_fetch_models_worker)

        # Tips
        tips = (
            "💡 自动拉取说明:\n"
            "• 支持任何兼容 OpenAI 规范的平台 (如 DeepSeek、SiliconFlow、OpenRouter、OneAPI、Ollama)\n"
            "• 点击【自动拉取模型】系统将直接请求 /v1/models 接口并将模型列表呈现在下拉框中"
        )
        ttk.Label(f, text=tips, font=Theme.FONT_SMALL, foreground=Theme.TEXT_MUTED, justify=tk.LEFT).pack(anchor=tk.W, pady=6)

        def _save_and_close():
            self.llm_config["base_url"] = var_url.get().strip()
            self.llm_config["api_key"] = var_key.get().strip()
            actual_model = var_model.get().strip()
            self.llm_config["model"] = actual_model
            self._refresh_engine_combobox(select_key="custom_llm")
            self._save_preferences()
            dlg.destroy()
            messagebox.showinfo("已保存", f"AI 大模型配置成功！\n\n• 当前生效模型: {actual_model}\n• 翻译引擎已切换为: 🤖 AI 大模型 ({actual_model})\n• 下次启动将自动默认使用该模型！", parent=self.container)
            self.trigger_translation()

        btn_box = ttk.Frame(f)
        btn_box.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        ttk.Button(btn_box, text=" 💾 保存配置并应用 ", command=_save_and_close).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_box, text=" 取消 ", command=dlg.destroy).pack(side=tk.RIGHT, padx=4)

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

    def toggle_translation(self):
        """Toggles between starting translation and instantly aborting the current running translation."""
        if getattr(self, "_is_translating", False):
            self.cancel_translation()
        else:
            self.trigger_translation()

    def cancel_translation(self):
        """Immediately aborts any ongoing translation task."""
        if getattr(self, "_active_cancel_event", None):
            self._active_cancel_event.set()
        self._is_translating = False
        self.btn_translate.config(text=" 🚀 立即翻译 ", state=tk.NORMAL)
        self.lbl_trans_status.config(text="状态: 操作已由用户手动中断 🛑", foreground="#dc3545")

    def trigger_translation(self):
        text = self.txt_source.get("1.0", tk.END).strip()
        if not text:
            self.txt_target.delete("1.0", tk.END)
            self.lbl_trans_status.config(text="状态: 就绪", foreground=Theme.PRIMARY)
            return

        # Cancel any previous running worker
        if getattr(self, "_active_cancel_event", None):
            self._active_cancel_event.set()

        self._active_cancel_event = threading.Event()
        self._is_translating = True
        self.btn_translate.config(text=" 🛑 中断翻译 ", state=tk.NORMAL)

        provider_key = self._get_selected_provider_key()
        cur_label = self.var_engine.get()
        self.lbl_trans_status.config(text=f"状态: 正在通过 [{cur_label.split()[1] if len(cur_label.split()) > 1 else '引擎'}] 翻译...", foreground="#0d6efd")

        src = self._get_selected_src_code()
        dest = self._get_selected_dest_code()
        proxy = self.context.get_proxy()
        cancel_ev = self._active_cancel_event

        def _worker():
            try:
                res = TranslationEngine.translate_smart(
                    text=text, 
                    src=src, 
                    dest=dest, 
                    provider_key=provider_key, 
                    proxy=proxy,
                    llm_config=self.llm_config,
                    cancel_event=cancel_ev
                )
                if not cancel_ev.is_set():
                    self.container.after(0, lambda: self._apply_translation_result(res))
            except Exception as e:
                if not cancel_ev.is_set():
                    self.container.after(0, lambda: self._handle_error(str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_translation_result(self, result: str):
        self._is_translating = False
        self.txt_target.delete("1.0", tk.END)
        self.txt_target.insert("1.0", result)
        self.lbl_trans_status.config(text="状态: 翻译完成 ✓", foreground="#198754")
        self.btn_translate.config(text=" 🚀 立即翻译 ", state=tk.NORMAL)

    def _handle_error(self, err_msg: str):
        self._is_translating = False
        self.lbl_trans_status.config(text=f"状态: 翻译失败 ({err_msg[:20]})", foreground="#dc3545")
        self.btn_translate.config(text=" 🚀 立即翻译 ", state=tk.NORMAL)

    def on_shutdown(self):
        """Cleans up and signals all workers to stop immediately on app shutdown."""
        self.cancel_translation()

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
