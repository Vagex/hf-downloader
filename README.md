# 🚀 Hugging Face 极速批量与断点续传下载器 (HF Downloader Pro)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)](https://www.python.org/)
[![UI: Tkinter & Flet](https://img.shields.io/badge/UI-Tkinter%20%7C%20Flet-orange.svg)](https://github.com/Vagex/hf-downloader)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](https://github.com/Vagex/hf-downloader)

专为 **AI 创作者、大模型研究员、ComfyUI / Stable Diffusion / FLUX 玩家** 量身打造的桌面级极速多线程与断点续传下载神器。彻底解决从 Hugging Face 下载大模型时**国内网络龟速、大文件 99% 中断无法恢复、多层级子文件下载繁琐、模型目录手动分类麻烦**等痛点！

---

## 🌟 核心特性与亮点

- ⚡ **国内镜像极速直连**：内置官方认证高可用国内镜像源（`hf-mirror.com`），无需魔法也能跑满千兆下行宽带！支持 HTTP / SOCKS5 代理热切换与一键连通性测速。
- 🐙 **全新 GitHub 资源浏览器**：内置国内极速反代加速节点（`ghproxy.net`、`github.moeyy.xyz` 等），一键极速下载 GitHub Release 发布包（二进制/whl/安装包）、仓库源码目录树文件或整包 Zip！支持 GitHub Token 突破 API 频率限制。
- 🛡️ **真正的“断点续传”**：全协议支持 HTTP Range 切片与 `.downloading` 临时保护，电脑关机、断网重启一秒识别已有进度，99% 中断绝不重下！
- 🌲 **阶梯式目录树与文件挑拣**：多级缩进目录树支持展开/折叠，点击任意行快速勾选，支持单个文件下载、批量挑拣与**【目录整包一键入队】**。
- 🛠️ **ComfyUI 专属一键部署 Tab**：智能全盘探测 ComfyUI 路径，1 秒一键生成 `custom_nodes` 插件目录及 `diffusion_models`、`controlnet`、`checkpoints`、`loras`、`vae`、`unet`、`clip` 等 8 大分类子目录，支持双击直接打开目录。
- 🎛️ **双引擎任选**：
  - **Tkinter 原生旗舰版 (`hf_downloader_gui.py`)**：零额外复杂 UI 依赖，秒开无延迟，内存极低；
  - **Flet 现代美学版 (`hf_downloader_flet.py`)**：自适应 Windows 系统明暗主题，38px 严密对齐桌面网格。
- 🪟 **一键无黑框静默运行**：提供原生 VBS 启动器与调试 BAT，无多余 CMD 黑色控制台弹窗。

---

## 🖥️ 快速启动

### 方式一：Tkinter 原生旗舰版（推荐·秒开免装复杂库）
- **无黑框旗舰模式**：双击运行 `启动下载器(无黑框).vbs`
- **控制台调试模式**：双击运行 `启动下载器.bat`（或在终端运行 `python hf_downloader_gui.py`）

### 方式二：Flet 现代美学版
- **无黑框模式**：双击运行 `启动Flet极速下载器(无黑框).vbs`
- **控制台调试模式**：双击运行 `启动Flet极速下载器.bat`（或在终端运行 `python hf_downloader_flet.py`）

---

## 🎬 交互式动态演播 PPT

项目中包含交互式动态 HTML5 演播演示大屏：
- 双击运行 **`HF极速下载器_全功能动态演示PPT.html`** 即可在浏览器全屏浏览所有功能模块的交互动效与功能解析。

---

## 📖 详细使用指南与推广文案

详见文档：[**`TK版本使用指南与推广文案.md`**](TK版本使用指南与推广文案.md)

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。
