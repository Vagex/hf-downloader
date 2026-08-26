import os
import sys
import datetime
import requests
import gradio as gr

# Default Mirror
DEFAULT_MIRROR = "https://hf-mirror.com"

def format_size(size_bytes):
    if not size_bytes:
        return "--"
    try:
        size_bytes = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    except Exception:
        return "--"

def fetch_repo_files(repo_id: str, repo_type: str = "model", branch: str = "main", endpoint: str = DEFAULT_MIRROR, token: str = ""):
    repo_id = repo_id.strip()
    if not repo_id:
        return "⚠️ 请输入有效的 Repo ID (例如: Kijai/MiniMax-H3-experimental)", [], ""

    endpoint = endpoint.strip().rstrip("/")
    token = token.strip() or None
    headers = {"User-Agent": "HF-Downloader-Web/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    base_type = "models" if repo_type == "model" else (repo_type + "s" if not repo_type.endswith("s") else repo_type)
    api_url = f"{endpoint}/api/{base_type}/{repo_id}/tree/{branch}?recursive=True"

    try:
        resp = requests.get(api_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return f"❌ 获取失败: HTTP {resp.status_code} ({resp.text[:120]})", [], ""

        tree_data = resp.json()
        if not isinstance(tree_data, list):
            return "❌ 解析返回数据异常", [], ""

        file_list = []
        direct_links = []
        total_size = 0

        for item in tree_data:
            if item.get("type") == "directory":
                continue
            rfilename = item.get("path")
            if not rfilename:
                continue

            raw_size = item.get("size") or 0
            lfs = item.get("lfs")
            if isinstance(lfs, dict) and lfs.get("size"):
                raw_size = lfs.get("size")

            total_size += raw_size
            size_str = format_size(raw_size)
            last_mod = (item.get("lastModified") or "--")[:16].replace("T", " ")

            # Build direct download link
            if repo_type == "model":
                dl_url = f"{endpoint}/{repo_id}/resolve/{branch}/{rfilename}"
            elif repo_type == "dataset":
                dl_url = f"{endpoint}/datasets/{repo_id}/resolve/{branch}/{rfilename}"
            else:
                dl_url = f"{endpoint}/spaces/{repo_id}/resolve/{branch}/{rfilename}"

            file_list.append([rfilename, size_str, last_mod, dl_url])
            direct_links.append(f"{rfilename} -> {dl_url}")

        summary = f"✅ 成功检索到 **{len(file_list)}** 个文件 | 仓库总体积: **{format_size(total_size)}**"
        links_text = "\n".join(direct_links)
        return summary, file_list, links_text

    except Exception as err:
        return f"❌ 请求异常: {str(err)}", [], ""


# Gradio Web UI
custom_css = """
.gradio-container { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
#title-box { text-align: center; margin-bottom: 12px; }
"""

with gr.Blocks(css=custom_css, title="Hugging Face 极速下载与直链解析器") as demo:
    gr.Markdown(
        """
        # 🚀 Hugging Face 极速下载器 & 直链解析中心
        ### 国内极速镜像直连 · 递归全目录树探测 · LFS 真实体积解析 · 一键批量直链导出
        """,
        elem_id="title-box"
    )

    with gr.Row():
        with gr.Column(scale=3):
            repo_input = gr.Textbox(label="📦 Repo ID (仓库名)", value="Kijai/MiniMax-H3-experimental", placeholder="例如: Kijai/MiniMax-H3-experimental 或 black-forest-labs/FLUX.1-dev")
        with gr.Column(scale=1):
            type_input = gr.Dropdown(label="📌 类型", choices=["model", "dataset", "space"], value="model")
        with gr.Column(scale=1):
            branch_input = gr.Textbox(label="🌿 分支", value="main")

    with gr.Row():
        with gr.Column(scale=3):
            mirror_input = gr.Dropdown(
                label="🌐 镜像源加速节点",
                choices=["https://hf-mirror.com", "https://huggingface.co"],
                value="https://hf-mirror.com"
            )
        with gr.Column(scale=2):
            token_input = gr.Textbox(label="🔒 HF Token (私有/受限模型填写，无则留空)", type="password", placeholder="hf_...")

    btn_search = gr.Button("🔍 立即获取仓库全部文件列表与直链", variant="primary")

    status_output = gr.Markdown("状态: 就绪")

    files_table = gr.Dataframe(
        headers=["文件名 / 相对路径", "文件大小", "更新时间", "极速下载直链"],
        datatype=["str", "str", "str", "str"],
        label="📂 仓库文件清单与下载直链 (支持复制表格/排序)",
        interactive=False,
        wrap=True
    )

    with gr.Accordion("📋 批量下载链接文本导出 (可直接复制到迅雷/Aria2/IDM)", open=False):
        links_output = gr.TextArea(label="全部下载直链", lines=8)

    btn_search.click(
        fn=fetch_repo_files,
        inputs=[repo_input, type_input, branch_input, mirror_input, token_input],
        outputs=[status_output, files_table, links_output]
    )

    gr.Markdown("--- \n💡 **开源桌面客户端支持断点续传与 ComfyUI 自动分类部署** | GitHub 仓库: [Vagex/hf-downloader](https://github.com/Vagex/hf-downloader)")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
