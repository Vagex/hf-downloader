import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from app.modules.base import BaseAppModule, ModuleManager
from app.core.config import ConfigService
from app.ui.theme import Theme

class SettingsModule(BaseAppModule):
    module_id = "settings"
    name = "⚙️ 全局设置与代理"
    icon_name = "gear"
    category = "系统"
    description = "统一网络代理池、默认下载存储目录、外观与快捷偏好配置"
    order = 90

    def create_view(self, parent: tk.Widget) -> tk.Widget:
        container = ttk.Frame(parent, padding="12")

        # Card 1: Network & Proxy
        proxy_card = ttk.LabelFrame(container, text=" 🌐 全局网络加速与代理池 (Proxy Pool) ", padding="10")
        proxy_card.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(proxy_card, text="当前默认代理:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        
        self.var_proxy = tk.StringVar(value=ConfigService.get("proxy", "不使用代理 (直连)"))
        proxies_list = ConfigService.get("proxies_list", [])
        self.cb_proxy = ttk.Combobox(proxy_card, textvariable=self.var_proxy, values=proxies_list, width=40, font=Theme.FONT_BODY)
        self.cb_proxy.grid(row=0, column=1, sticky="w", padx=4, pady=4)

        btn_save_proxy = ttk.Button(proxy_card, text="💾 保存生效", command=self._save_settings)
        btn_save_proxy.grid(row=0, column=2, padx=6, pady=4)

        # Card 2: Storage Destination
        dest_card = ttk.LabelFrame(container, text=" 💾 默认文件保存路径 ", padding="10")
        dest_card.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(dest_card, text="全局下载存储根目录:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.var_dest = tk.StringVar(value=ConfigService.get("default_dest_dir", os.path.join(os.path.expanduser("~"), "Downloads")))
        self.entry_dest = ttk.Entry(dest_card, textvariable=self.var_dest, width=45, font=Theme.FONT_BODY)
        self.entry_dest.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        btn_browse_dest = ttk.Button(dest_card, text=" 浏览更改...", command=self._browse_dest)
        btn_browse_dest.grid(row=0, column=2, padx=6, pady=4)

        dest_card.columnconfigure(1, weight=1)

        # Card 3: Platform Info
        info_card = ttk.LabelFrame(container, text=" ℹ️ 关于平台与扩展架构 ", padding="10")
        info_card.pack(fill=tk.BOTH, expand=True)

        txt_info = (
            "🌟 万能超级工具箱 (Universal Super App Platform)\n"
            "版本: v2.0.0 (模块化超级工作台版)\n\n"
            "架构特性:\n"
            "• 标准化 BaseAppModule 插件接口，支持即插即用无限横向扩展\n"
            "• 内置 全能下载中心、媒体处理工坊、代理配置中心\n"
            "• 支持一键接入 AI/ComfyUI 助手、批量数据工具等全新业务模块"
        )
        lbl_info = ttk.Label(info_card, text=txt_info, font=Theme.FONT_BODY, justify=tk.LEFT)
        lbl_info.pack(anchor="w", padx=4, pady=4)

        self.view_container = container
        return container

    def _browse_dest(self):
        d = filedialog.askdirectory(title="选择全局默认保存目录", initialdir=self.var_dest.get())
        if d:
            self.var_dest.set(os.path.normpath(d))
            self._save_settings()

    def _save_settings(self):
        ConfigService.set("proxy", self.var_proxy.get().strip())
        ConfigService.set("default_dest_dir", self.var_dest.get().strip())
        messagebox.showinfo("设置已保存", "全局配置已成功保存并立即生效！")

ModuleManager.register(SettingsModule)
