"""
ComfyUI MiniMax-H3 Local Reverse-Engineering & Director Assistant
Powered by Local Qwen 27B (via Ollama API)

Usage:
    python local_director.py --video "path/to/video.mp4" --duration 15
    python local_director.py --text "15秒雨夜赛博朋克机甲拔刀斩" --duration 15
    python local_director.py --interactive
"""

import os
import sys
import json
import base64
import argparse
import requests

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import cv2
except ImportError:
    cv2 = None

OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://127.0.0.1:11434/api/generate")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.6:27b")

SYSTEM_DIRECTOR_PROMPT = """你是一个世界顶级的电影导演、视效总监以及 ComfyUI MiniMax-H3 Director 提示词工程专家。
你的任务是：根据用户提供的视频信息（或分镜文本、关键帧描述），深度反推爆款视频的生成 Prompt，并重构为 ComfyUI MiniMax-H3 智能导演台专属的【公共提示词】与【5秒分段提示词组】。

【输出规范与结构要求】：
请严格按照以下结构输出，必须包含所有板块，提示词需使用纯正、高信息密度的英文电影专业术语（配合中文解析）：

### 🎬 【模式与节点选择】
- 推荐模式 (task_type): [fl2v / r2v / i2v / t2v / v2v]
- 对应 UNET: [fl2va / ref2va]
- CLIP Loader: minimax (Qwen3-VL)
- 段间引导 (Motion Context): True (22 帧)

---

### 🌐 【公共提示词 (Common Prompt)】
(定义全局 8K 画质、摄影机型号如 ARRI Alexa 35 / 35mm 变形镜头、光影基调、粒子特效如烟雾/雨水/火星、全局音效底噪)

---

### 🎞️ 【分段提示词组 (Prompt Groups)】
(每段固定建议 5.0s / 120 帧，按总时长划分 Group 1 ~ N)
#### 🔹 Group 1 (0.0s - 5.0s) —— [起势爆发]
- 首帧状态与描述
- 动作因果链与运镜推进 (0~5s)
- 拟音与撞击音效

#### 🔹 Group 2 (5.0s - 10.0s) —— [高潮交锋]
- 动量继承：明确承接上一段结尾动势（开启 22 帧段间引导）
- 动作演进与机位转换
- 声音音效

(如果有 Group 3 及以上依此类推，最后一段给出高潮收尾与定格)

---

### 🚫 【专属负向提示词 (Negative Prompt)】
(排除畸变、多肢、掉帧、塑料质感、卡通CG感、突变瞬移等)

---

### ⚙️ 【ComfyUI 节点参数推荐表】
(列出 task_type, UNET, Motion Context 帧数 22, FPS 24/25, Audio, Refine 建议)
"""

def extract_video_summary(video_path, max_frames=5):
    """Extracts frame timestamps and basic info from a video file."""
    if not cv2:
        return f"Video file: {video_path} (cv2 not available, using file reference)"
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return f"Failed to open video at {video_path}"
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    cap.release()
    return f"视频文件信息: 路径={video_path}, 总时长={duration:.2f}秒, 分辨率={width}x{height}, FPS={fps:.1f}"

def call_local_qwen_stream(prompt, model=DEFAULT_MODEL, show_thinking=False):
    """Calls local Qwen model with streaming output."""
    full_prompt = f"{SYSTEM_DIRECTOR_PROMPT}\n\n【用户需要反推与生成的视频需求】：\n{prompt}\n\n请开始进行反推并生成完整的 ComfyUI MiniMax-H3 导演台提示词组："
    
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": True,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 8192
        }
    }
    
    print(f"[*] 正在调用本地模型 [{model}] 进行深度反推与分段导演生成...")
    if show_thinking:
        print("[*] 正在输出推理过程 (Thinking)...")
    
    collected_response = []
    in_thinking = False
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=600)
        if response.status_code != 200:
            err_msg = f"Error: Ollama returned status {response.status_code}: {response.text}"
            print(err_msg)
            return err_msg
        
        for line in response.iter_lines():
            if not line:
                continue
            chunk = json.loads(line.decode("utf-8"))
            
            # Handle thinking tokens
            thinking_token = chunk.get("thinking", "")
            if thinking_token:
                if show_thinking:
                    sys.stdout.write(thinking_token)
                    sys.stdout.flush()
                else:
                    if not in_thinking:
                        sys.stdout.write("[*] 本地模型正在进行深度导演分镜构思中")
                        in_thinking = True
                    sys.stdout.write(".")
                    sys.stdout.flush()
            
            # Handle actual response tokens
            token = chunk.get("response", "")
            if token:
                if in_thinking and not show_thinking:
                    sys.stdout.write("\n\n" + "="*60 + "\n🎬 ComfyUI MiniMax-H3 导演分段生成结果：\n" + "="*60 + "\n\n")
                    in_thinking = False
                sys.stdout.write(token)
                sys.stdout.flush()
                collected_response.append(token)
            
            if chunk.get("done", False):
                break
        
        print("\n")
        return "".join(collected_response)
    
    except Exception as e:
        err_msg = f"\nError connecting to Ollama at {OLLAMA_API_URL}: {str(e)}"
        print(err_msg)
        return err_msg

def main():
    parser = argparse.ArgumentParser(description="ComfyUI MiniMax-H3 Local Reverse-Engineering Director")
    parser.add_argument("--video", type=str, help="Path to video file to reverse-engineer")
    parser.add_argument("--text", type=str, help="Text description of the video to replicate")
    parser.add_argument("--duration", type=int, default=15, help="Target duration in seconds (default: 15)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Ollama model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--output", type=str, help="Path to save output markdown file")
    parser.add_argument("--show-thinking", action="store_true", help="Display reasoning thinking tokens")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive or (not args.video and not args.text):
        print("="*60)
        print("🎬 ComfyUI MiniMax-H3 本地智能导演与反推专家 (Qwen 27B 本地驱动)")
        print("="*60)
        user_input = input("请输入您想反推的视频描述、分镜构想或视频文件路径: ")
        duration_input = input("期望生成视频总时长 (秒，默认 15s): ")
        duration = int(duration_input) if duration_input.strip().isdigit() else 15
        prompt_content = f"{user_input} (目标生成总时长: {duration}秒)"
    elif args.video:
        vid_summary = extract_video_summary(args.video)
        prompt_content = f"{vid_summary}\n用户附加要求: 目标总时长 {args.duration} 秒，完整解构并重构为电影级打斗/动态分镜。"
    else:
        prompt_content = f"{args.text}\n目标总时长: {args.duration} 秒"
    
    output_text = call_local_qwen_stream(prompt_content, model=args.model, show_thinking=args.show_thinking)
    
    if args.output and output_text:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"[+] 结果已成功保存至: {args.output}")

if __name__ == "__main__":
    main()
