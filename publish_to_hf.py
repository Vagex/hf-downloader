import os
import sys

try:
    from huggingface_hub import HfApi, login
except ImportError:
    print("正在安装 huggingface_hub 依赖...")
    os.system(f'"{sys.executable}" -m pip install -U huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple')
    from huggingface_hub import HfApi, login

REPO_ID = "Vagex/hf-downloader"
REPO_TYPE = "model"  # 或 "space"

def main():
    print("=" * 60)
    print(f"🚀 Hugging Face 仓库一键发布与同步工具")
    print(f"目标仓库: https://huggingface.co/{REPO_ID}")
    print("=" * 60)

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("\n提示: 推送到 Hugging Face 需要 Write (写入) 权限的 Access Token。")
        print("您可以在 https://huggingface.co/settings/tokens 创建并复制 Token。\n")
        token = input("请输入您的 Hugging Face Token (带 Write 权限): ").strip()

    if not token:
        print("❌ 未提供有效的 Token，操作已取消。")
        return

    api = HfApi(token=token)

    try:
        print(f"\n[*] 正在检测/创建远程仓库 '{REPO_ID}'...")
        api.create_repo(repo_id=REPO_ID, repo_type=REPO_TYPE, exist_ok=True)
        print(f"[✓] 远程仓库已确认就绪！")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        ignore_patterns = [
            "__pycache__/*",
            "*.pyc",
            "*.lock",
            "*.downloading",
            ".git/*",
            ".vscode/*",
            "alice-tea-party/*",
            "check_downloads.py",
            "check_minimax_nodes.py",
            "minimax_h3_*.json",
            "workflow_templates/*",
            "hf_download_tasks.json",
            "hf_downloader_settings.json",
            "hf_downloader_mirrors.json",
            "hf_downloader_proxies.json"
        ]

        print(f"[*] 正在打包并极速上传项目文件到 Hugging Face...")
        api.upload_folder(
            folder_path=current_dir,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            ignore_patterns=ignore_patterns,
            commit_message="feat: publish Hugging Face Downloader Pro (Dual Engine + ComfyUI Deployer)"
        )
        print("\n" + "=" * 60)
        print(f"🎉 恭喜！项目已成功发布到 Hugging Face！")
        print(f"🌐 访问地址: https://huggingface.co/{REPO_ID}")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ 上传失败: {str(e)}")

if __name__ == "__main__":
    main()
    input("\n按回车键退出...")
