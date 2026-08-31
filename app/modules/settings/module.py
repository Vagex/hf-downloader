import os
import sys
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Tuple

from app.modules.base import BaseAppModule, ModuleManager
from app.core.config import ConfigService
from app.ui.theme import Theme

# Core Python Packages for Super App
SUPER_APP_CORE_PACKAGES: List[Tuple[str, str, str]] = [
    ("requests", "网络请求核心组件", "用于 HuggingFace、GitHub、各平台直链下载与 API 通信"),
    ("urllib3", "HTTP 传输层底层协议", "提供高并发连接池与连接重试保障"),
    ("huggingface_hub", "HF 官方 SDK", "提供大模型仓库文件树高速解析与 Gated 授权"),
    ("certifi", "SSL/TLS 安全证书库", "保障 HTTPS 加密下载与域名证书校验"),
    ("tqdm", "进度条与计量工具", "控制台与后台任务流速计算"),
]

# Binary Standalone Engines
STANDALONE_ENGINES: List[Tuple[str, str, str]] = [
    ("aria2c.exe", "Aria2 极速 P2P/DHT 下载引擎", "提供磁力链接极速传输与 16 线程多通道下载"),
    ("yt-dlp.exe", "yt-dlp 音视频解析与混流引擎", "提供 YouTube、B站高清视频与音视频 DASH 封装"),
    ("ffmpeg.exe", "FFmpeg 多媒体硬件编解码器", "提供媒体工坊音频无损提取、视频转码与切片"),
]

PYPI_MIRRORS = {
    "清华大学镜像源 (推荐)": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "阿里云镜像源": "https://mirrors.aliyun.com/pypi/simple/",
    "腾讯云镜像源": "https://mirrors.cloud.tencent.com/pypi/simple",
    "华为云镜像源": "https://repo.huaweicloud.com/repository/pypi/simple",
    "中国科技大学镜像源": "https://pypi.mirrors.ustc.edu.cn/simple",
    "官方默认源 (PyPI)": "https://pypi.org/simple"
}

PRESET_DIRS_MAP = {
    "VAE 编解码器模型 (vae)": "vae",
    "Diffusion Transformer 扩散主体模型 (diffusion_models)": "diffusion_models",
    "LoRA / LyCORIS 微调模型 (loras)": "loras",
    "ControlNet 条件控制模型 (controlnet)": "controlnet",
    "文本编码器与 CLIP 模型 (text_encoders)": "text_encoders",
    "基础大模型检查点 (checkpoints)": "checkpoints",
    "CLIP 视觉编码器 (clip_vision)": "clip_vision",
    "UPscaler 超分辨率放大模型 (upscale_models)": "upscale_models",
    "UNET 架构扩散模型 (unet)": "unet",
    "Embeddings / 文本反转 (embeddings)": "embeddings",
    "GLIGEN 条件布局模型 (gligen)": "gligen",
    "Style Models 风格迁移 (style_models)": "style_models"
}

class SettingsModule(BaseAppModule):
    module_id = "settings"
    name = "⚙️ 全局设置与环境部署"
    icon_name = "gear"
    category = "系统"
    description = "统一网络代理、全局依赖一键自愈、多媒体引擎与 ComfyUI 生态部署"
    order = 90

    def create_view(self, parent: tk.Widget) -> tk.Widget:
        container = ttk.Frame(parent, padding="6")

        # Top Notebook for Tabbed Settings & Env Deploy
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Global Settings & Proxies
        self.tab_settings = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_settings, text=" 🌐 全局网络与偏好设置 ")
        self._build_settings_tab(self.tab_settings)

        # Tab 2: Full-Stack Env Auto-Deploy
        self.tab_env = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_env, text=" 🛠️ 全局环境与依赖一键部署 ")
        self._build_env_deploy_tab(self.tab_env)

        # Tab 3: ComfyUI & AI Directories Topology
        self.tab_comfy = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_comfy, text=" 📁 ComfyUI 与 AI 模型目录部署 ")
        self._build_comfy_tab(self.tab_comfy)

        self.view_container = container
        return container

    # ------------------ Tab 1: Settings & Proxies ------------------
    def _build_settings_tab(self, parent):
        # Proxy Card
        proxy_card = ttk.LabelFrame(parent, text=" 🌐 全局网络加速与代理池 (Proxy Pool) ", padding="10")
        proxy_card.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(proxy_card, text="当前默认代理:").grid(row=0, column=0, sticky="w", padx=4, pady=6)
        
        self.var_proxy = tk.StringVar(value=ConfigService.get("proxy", "不使用代理 (直连)"))
        proxies_list = ConfigService.get("proxies_list", [])
        self.cb_proxy = ttk.Combobox(proxy_card, textvariable=self.var_proxy, values=proxies_list, width=40, font=Theme.FONT_BODY)
        self.cb_proxy.grid(row=0, column=1, sticky="w", padx=4, pady=6)

        btn_save_proxy = ttk.Button(proxy_card, text="💾 保存全局生效", command=self._save_settings)
        btn_save_proxy.grid(row=0, column=2, padx=8, pady=6)

        # Destination Card
        dest_card = ttk.LabelFrame(parent, text=" 💾 默认文件保存路径 ", padding="10")
        dest_card.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(dest_card, text="全局下载存储根目录:").grid(row=0, column=0, sticky="w", padx=4, pady=6)
        self.var_dest = tk.StringVar(value=ConfigService.get("default_dest_dir", os.path.join(os.path.expanduser("~"), "Downloads")))
        self.entry_dest = ttk.Entry(dest_card, textvariable=self.var_dest, width=45, font=Theme.FONT_BODY)
        self.entry_dest.grid(row=0, column=1, sticky="ew", padx=4, pady=6)

        btn_browse_dest = ttk.Button(dest_card, text=" 浏览更改...", command=self._browse_dest)
        btn_browse_dest.grid(row=0, column=2, padx=8, pady=6)
        dest_card.columnconfigure(1, weight=1)

        # Info Card
        info_card = ttk.LabelFrame(parent, text=" ℹ️ 关于平台与模块化架构 ", padding="10")
        info_card.pack(fill=tk.BOTH, expand=True)

        txt_info = (
            "🌟 SuperTools 万能超级工具箱平台 v2.0\n\n"
            "• 标准化 BaseAppModule 插件接口，支持即插即用无限横向扩展\n"
            "• 现已集成: 🚀 全能下载中心 · 🎬 媒体处理工坊 · ⚙️ 全局设置与环境中心\n"
            "• 系统环境中心提供 Python 库、Aria2、yt-dlp、FFmpeg 等全栈自愈支持！"
        )
        ttk.Label(info_card, text=txt_info, font=Theme.FONT_BODY, justify=tk.LEFT).pack(anchor="w", padx=4, pady=4)

    # ------------------ Tab 2: Full-Stack Env Auto-Deploy ------------------
    def _build_env_deploy_tab(self, parent):
        paned = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Upper Frame: Component Health Status Tables
        upper_frame = ttk.Frame(paned)
        paned.add(upper_frame, weight=3)

        # 1. Python Packages Table
        col_pkgs = ("name", "status", "version", "desc")
        self.tree_pkgs = ttk.Treeview(upper_frame, columns=col_pkgs, show="headings", height=5)
        self.tree_pkgs.heading("name", text="Python 核心依赖库")
        self.tree_pkgs.heading("status", text="安装状态")
        self.tree_pkgs.heading("version", text="当前版本")
        self.tree_pkgs.heading("desc", text="平台功能用途")

        self.tree_pkgs.column("name", width=140, anchor="w")
        self.tree_pkgs.column("status", width=90, anchor="center")
        self.tree_pkgs.column("version", width=90, anchor="center")
        self.tree_pkgs.column("desc", width=400, anchor="w")

        self.tree_pkgs.tag_configure("ok_tag", foreground="#198754")
        self.tree_pkgs.tag_configure("missing_tag", foreground="#dc3545", font=("Segoe UI", 9, "bold"))
        self.tree_pkgs.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        # 2. Standalone Binary Engines Table
        self.tree_bins = ttk.Treeview(upper_frame, columns=("bin_name", "bin_status", "bin_path", "bin_desc"), show="headings", height=4)
        self.tree_bins.heading("bin_name", text="独立加速引擎 (Binary)")
        self.tree_bins.heading("bin_status", text="就绪状态")
        self.tree_bins.heading("bin_path", text="已就绪路径")
        self.tree_bins.heading("bin_desc", text="引擎核心能力")

        self.tree_bins.column("bin_name", width=140, anchor="w")
        self.tree_bins.column("bin_status", width=90, anchor="center")
        self.tree_bins.column("bin_path", width=320, anchor="w")
        self.tree_bins.column("bin_desc", width=260, anchor="w")

        self.tree_bins.tag_configure("ok_tag", foreground="#198754")
        self.tree_bins.tag_configure("missing_tag", foreground="#dc3545", font=("Segoe UI", 9, "bold"))
        self.tree_bins.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        # Operation Bar
        op_bar = ttk.Frame(upper_frame)
        op_bar.pack(fill=tk.X, pady=4)

        ttk.Label(op_bar, text="国内高速安装镜像源:").pack(side=tk.LEFT, padx=(0, 4))
        self.var_pypi_mirror = tk.StringVar(value="清华大学镜像源 (推荐)")
        cb_mirror = ttk.Combobox(op_bar, textvariable=self.var_pypi_mirror, values=list(PYPI_MIRRORS.keys()), width=24, state="readonly")
        cb_mirror.pack(side=tk.LEFT, padx=4)

        self.btn_auto_deploy = tk.Button(
            op_bar,
            text=" 🚀 一键全自动部署与补齐所有依赖 ",
            font=("Segoe UI", 10, "bold"),
            bg=Theme.PRIMARY,
            fg="#ffffff",
            activebackground=Theme.PRIMARY_HOVER,
            activeforeground="#ffffff",
            padx=12, pady=4,
            relief=tk.RAISED,
            command=self._install_all_dependencies
        )
        self.btn_auto_deploy.pack(side=tk.LEFT, padx=12)

        btn_recheck = ttk.Button(op_bar, text=" 🔄 重新检测环境健康度 ", command=self._check_all_env_health)
        btn_recheck.pack(side=tk.RIGHT)

        # Lower Frame: Realtime Output Log
        lower_frame = ttk.LabelFrame(paned, text=" 📜 依赖安装与终端部署输出 ", padding="6")
        paned.add(lower_frame, weight=2)

        self.txt_env_log = tk.Text(lower_frame, font=Theme.FONT_MONO, bg="#1e1e1e", fg="#d4d4d4", wrap=tk.WORD, height=6)
        scroll_log = ttk.Scrollbar(lower_frame, orient=tk.VERTICAL, command=self.txt_env_log.yview)
        self.txt_env_log.configure(yscrollcommand=scroll_log.set)
        self.txt_env_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)

        self._check_all_env_health()

    def _check_all_env_health(self):
        # 1. Check Python packages
        self.tree_pkgs.delete(*self.tree_pkgs.get_children())
        import importlib.metadata
        for pkg_name, short_name, desc in SUPER_APP_CORE_PACKAGES:
            norm_name = pkg_name.replace("_", "-")
            installed = False
            ver_str = "--"
            for test_name in (pkg_name, norm_name):
                try:
                    ver_str = importlib.metadata.version(test_name)
                    installed = True
                    break
                except Exception:
                    pass
            if installed:
                self.tree_pkgs.insert("", tk.END, values=(pkg_name, "✓ 已就绪", ver_str, f"{short_name} · {desc}"), tags=("ok_tag",))
            else:
                self.tree_pkgs.insert("", tk.END, values=(pkg_name, "✗ 缺失", "--", f"{short_name} · {desc}"), tags=("missing_tag",))

        # 2. Check Binary Standalone Engines
        self.tree_bins.delete(*self.tree_bins.get_children())
        for bin_name, label, desc in STANDALONE_ENGINES:
            # Check PATH or local bin
            found_path = shutil.which(bin_name.replace(".exe", "")) or shutil.which(bin_name)
            if not found_path:
                local_cand = os.path.join(os.path.expanduser("~"), ".hf_downloader", "bin", bin_name)
                if os.path.exists(local_cand) and os.path.getsize(local_cand) > 1024:
                    found_path = local_cand

            if found_path:
                self.tree_bins.insert("", tk.END, values=(bin_name, "✓ 已就绪", found_path, f"{label} · {desc}"), tags=("ok_tag",))
            else:
                self.tree_bins.insert("", tk.END, values=(bin_name, "✗ 缺失 (自动拉取)", "未检测到本地路径", f"{label} · {desc}"), tags=("missing_tag",))

    def _install_all_dependencies(self):
        self.btn_auto_deploy.config(state=tk.DISABLED, text=" 正在高速下载与部署中... ")
        mirror_name = self.var_pypi_mirror.get()
        mirror_url = PYPI_MIRRORS.get(mirror_name, "https://pypi.tuna.tsinghua.edu.cn/simple")

        self.txt_env_log.insert(tk.END, f"\n================ 启动 Super App 全栈依赖自动化一键部署 ================\n")
        self.txt_env_log.insert(tk.END, f"[*] 选用 PyPI 国内极速源: {mirror_name} ({mirror_url})\n")
        self.txt_env_log.see(tk.END)

        def _worker():
            # Step 1: Install Python packages
            pkgs = [p[0] for p in SUPER_APP_CORE_PACKAGES]
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + pkgs + ["-i", mirror_url]
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            try:
                proc = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True, 
                    bufsize=1, 
                    encoding="utf-8", 
                    errors="replace",
                    creationflags=creationflags
                )
                for line in proc.stdout:
                    self.container_after(lambda l=line: (self.txt_env_log.insert(tk.END, l), self.txt_env_log.see(tk.END)))
                proc.wait()
                
                # Step 2: Ensure Aria2
                self.container_after(lambda: (self.txt_env_log.insert(tk.END, "\n[*] 正在检测并自动准备绿色版 Aria2 极速 P2P 下载引擎...\n"), self.txt_env_log.see(tk.END)))
                try:
                    from hf_downloader_gui import Aria2Manager
                    Aria2Manager.ensure_executable(log_callback=lambda m: self.container_after(lambda msg=m: (self.txt_env_log.insert(tk.END, f"{msg}\n"), self.txt_env_log.see(tk.END))))
                except Exception as ex:
                    self.container_after(lambda e=ex: self.txt_env_log.insert(tk.END, f"Aria2 部署提示: {e}\n"))

                self.container_after(lambda: messagebox.showinfo("部署完成", "所有核心依赖与运行加速引擎已全自动部署就绪！"))
                self.container_after(self._check_all_env_health)
            except Exception as e:
                self.container_after(lambda err=e: messagebox.showerror("错误", f"执行异常: {err}"))
            finally:
                self.container_after(lambda: self.btn_auto_deploy.config(state=tk.NORMAL, text=" 🚀 一键全自动部署与补齐所有依赖 "))

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------ Tab 3: ComfyUI Ecosystem Deployer ------------------
    def _build_comfy_tab(self, parent):
        lbl_info = ttk.Label(
            parent, 
            text="为 AI 与 ComfyUI 生态提供标准模型拓扑目录的一键创建、智能探测与目录规范化收纳！", 
            font=Theme.FONT_BODY, 
            foreground=Theme.TEXT_MUTED
        )
        lbl_info.pack(anchor="w", pady=(0, 8))

        top_sel = ttk.Frame(parent)
        top_sel.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(top_sel, text="ComfyUI 模型根目录 (models):").pack(side=tk.LEFT, padx=(0, 4))
        self.var_comfy_root = tk.StringVar(value=r"F:\ComfyUI-aki-v3\ComfyUI\models")
        entry_c = ttk.Entry(top_sel, textvariable=self.var_comfy_root, width=45)
        entry_c.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        btn_b_comfy = ttk.Button(top_sel, text=" 浏览目录...", command=self._browse_comfy_root)
        btn_b_comfy.pack(side=tk.LEFT, padx=4)

        btn_auto_find = ttk.Button(top_sel, text=" 🔍 自动探测 ComfyUI", command=self._auto_detect_comfy)
        btn_auto_find.pack(side=tk.LEFT, padx=4)

        # Tree for directories
        self.tree_comfy_dirs = ttk.Treeview(parent, columns=("dir_name", "dir_status", "dir_path", "dir_action"), show="headings", height=9)
        self.tree_comfy_dirs.heading("dir_name", text="ComfyUI 标准模型分类目录")
        self.tree_comfy_dirs.heading("dir_status", text="状态")
        self.tree_comfy_dirs.heading("dir_path", text="目标磁盘物理路径")
        self.tree_comfy_dirs.heading("dir_action", text="快捷操作 (双击)")

        self.tree_comfy_dirs.column("dir_name", width=220, anchor="w")
        self.tree_comfy_dirs.column("dir_status", width=90, anchor="center")
        self.tree_comfy_dirs.column("dir_path", width=360, anchor="w")
        self.tree_comfy_dirs.column("dir_action", width=120, anchor="center")

        self.tree_comfy_dirs.tag_configure("ok_tag", foreground="#198754")
        self.tree_comfy_dirs.tag_configure("missing_tag", foreground="#dc3545")
        self.tree_comfy_dirs.pack(fill=tk.BOTH, expand=True, pady=6)
        self.tree_comfy_dirs.bind("<Double-1>", self._on_comfy_tree_double_click)

        btn_create_all = tk.Button(
            parent,
            text=" 📁 一键全自动补齐与创建所有缺失目录 ",
            font=("Segoe UI", 10, "bold"),
            bg="#198754",
            fg="#ffffff",
            activebackground="#146c43",
            activeforeground="#ffffff",
            padx=12, pady=4,
            relief=tk.RAISED,
            command=self._create_all_comfy_dirs
        )
        btn_create_all.pack(anchor="w", pady=4)

        self._refresh_comfy_dirs()

    def _browse_comfy_root(self):
        d = filedialog.askdirectory(title="选择 ComfyUI 模型根目录 (models)")
        if d:
            self.var_comfy_root.set(os.path.normpath(d))
            self._refresh_comfy_dirs()

    def _auto_detect_comfy(self):
        candidates = [
            r"F:\ComfyUI-aki-v3\ComfyUI\models",
            r"D:\ComfyUI-aki-v3\ComfyUI\models",
            r"E:\ComfyUI-aki-v3\ComfyUI\models",
            r"C:\ComfyUI-aki-v3\ComfyUI\models",
            r"D:\ComfyUI\models",
            r"E:\ComfyUI\models",
            r"F:\ComfyUI\models",
        ]
        for c in candidates:
            if os.path.exists(c):
                self.var_comfy_root.set(c)
                self._refresh_comfy_dirs()
                messagebox.showinfo("检测成功", f"成功探测到 ComfyUI 路径:\n{c}")
                return
        messagebox.showwarning("提示", "未能自动探测到 ComfyUI 路径，请点击【浏览目录...】手动选择。")

    def _refresh_comfy_dirs(self):
        self.tree_comfy_dirs.delete(*self.tree_comfy_dirs.get_children())
        base = self.var_comfy_root.get().strip()
        for label, rel_or_abs in PRESET_DIRS_MAP.items():
            folder_name = label.split("(")[-1].rstrip(")")
            target_path = os.path.join(base, folder_name) if not os.path.isabs(rel_or_abs) else rel_or_abs
            exists = os.path.exists(target_path)
            status_text = "✓ 已就绪" if exists else "✗ 未创建"
            tag = "ok_tag" if exists else "missing_tag"
            action_text = "📂 点击打开" if exists else "➕ 待创建"
            self.tree_comfy_dirs.insert("", tk.END, values=(label, status_text, target_path, action_text), tags=(tag,))

    def _on_comfy_tree_double_click(self, event):
        item_id = self.tree_comfy_dirs.focus()
        if not item_id:
            return
        vals = self.tree_comfy_dirs.item(item_id, "values")
        if vals and len(vals) >= 3:
            path = vals[2]
            if os.path.exists(path):
                os.startfile(path)
            else:
                if messagebox.askyesno("创建目录", f"目录不存在，是否立即创建？\n{path}"):
                    try:
                        os.makedirs(path, exist_ok=True)
                        self._refresh_comfy_dirs()
                        messagebox.showinfo("成功", f"目录已成功创建:\n{path}")
                    except Exception as err:
                        messagebox.showerror("错误", f"创建失败: {err}")

    def _create_all_comfy_dirs(self):
        base = self.var_comfy_root.get().strip()
        created = 0
        for label, rel_or_abs in PRESET_DIRS_MAP.items():
            folder_name = label.split("(")[-1].rstrip(")")
            target_path = os.path.join(base, folder_name) if not os.path.isabs(rel_or_abs) else rel_or_abs
            if not os.path.exists(target_path):
                try:
                    os.makedirs(target_path, exist_ok=True)
                    created += 1
                except Exception:
                    pass
        self._refresh_comfy_dirs()
        messagebox.showinfo("完成", f"一键环境部署完成！共补齐/创建 {created} 个模型分类目录。")

    def _browse_dest(self):
        d = filedialog.askdirectory(title="选择全局默认保存目录", initialdir=self.var_dest.get())
        if d:
            self.var_dest.set(os.path.normpath(d))
            self._save_settings()

    def _save_settings(self):
        ConfigService.set("proxy", self.var_proxy.get().strip())
        ConfigService.set("default_dest_dir", self.var_dest.get().strip())
        messagebox.showinfo("设置已保存", "全局配置已成功保存并立即生效！")

    def container_after(self, func):
        if self.view_container:
            self.view_container.after(0, func)
        else:
            func()

ModuleManager.register(SettingsModule)
