import os
import sys
import time
import json
from typing import List

TASKS_DB_FILE = os.path.join(os.path.dirname(__file__), "hf_download_tasks.json")
LOCK_FILE = os.path.join(os.path.dirname(__file__), "hf_downloader_active.lock")

def format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def check_process_alive(pid: int) -> bool:
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        SYNCHRONIZE = 0x00100000
        process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if process:
            kernel32.CloseHandle(process)
            return True
        return False
    except Exception:
        return False

def main():
    print("=" * 60)
    print("       Hugging Face 后台下载任务与缓存状态检测器       ")
    print("=" * 60)

    # 1. Check lock file
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                data = json.load(f)
                pid = data.get("pid")
                started = data.get("started_at")
                if pid and check_process_alive(pid):
                    print(f"🔴 [活跃中] 检测到下载器主进程正在后台运行 (PID: {pid}, 启动时间: {started})")
                else:
                    print(f"⚪ [空闲] 无运行中的主进程 (发现历史残留锁，已自动释放)")
                    os.remove(LOCK_FILE)
        except Exception as e:
            print(f"⚠️ 读取锁文件异常: {e}")
    else:
        print("⚪ [空闲] 当前没有正在前台/后台运行的下载队列主程序。")

    print("-" * 60)

    # 2. Check task list and disk file transfer status
    if not os.path.exists(TASKS_DB_FILE):
        print("ℹ️ 暂无任何历史任务记录。")
        return

    try:
        with open(TASKS_DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            tasks = data.get("tasks", [])
    except Exception as e:
        print(f"❌ 读取任务列表失败: {e}")
        return

    print(f"📋 共记录 {len(tasks)} 个任务，正在检测文件变动 (采样 1 秒)...")

    # Sample file sizes
    temp_files = []
    for t in tasks:
        dest_dir = t.get("dest_dir", "")
        file_path = t.get("file_path", "")
        flatten = t.get("flatten", True)

        if flatten:
            target_f = os.path.join(dest_dir, os.path.basename(file_path))
        else:
            target_f = os.path.join(dest_dir, os.path.normpath(file_path))
        temp_f = target_f + ".downloading"

        if os.path.exists(temp_f):
            temp_files.append((t, temp_f, target_f, os.path.getsize(temp_f)))

    time.sleep(1.0)

    active_tasks = 0
    interrupted_tasks = 0
    done_tasks = 0

    print("-" * 60)
    for t in tasks:
        dest_dir = t.get("dest_dir", "")
        file_path = t.get("file_path", "")
        flatten = t.get("flatten", True)
        if flatten:
            target_f = os.path.join(dest_dir, os.path.basename(file_path))
        else:
            target_f = os.path.join(dest_dir, os.path.normpath(file_path))
        temp_f = target_f + ".downloading"

        fname = os.path.basename(file_path)

        if os.path.exists(target_f):
            sz = format_size(os.path.getsize(target_f))
            print(f"  [✓ 已完成] {fname} ({sz}) -> {dest_dir}")
            done_tasks += 1
        elif os.path.exists(temp_f):
            initial_sz = [item[3] for item in temp_files if item[1] == temp_f]
            cur_sz = os.path.getsize(temp_f)
            if initial_sz and (cur_sz - initial_sz[0]) > 0:
                speed = format_size(cur_sz - initial_sz[0]) + "/s"
                print(f"  [🔴 正在后台下载] {fname} (已下: {format_size(cur_sz)}, 实时速率: {speed})")
                active_tasks += 1
            else:
                print(f"  [🟡 中断/待续传] {fname} (已缓存: {format_size(cur_sz)}, 随时可接续)")
                interrupted_tasks += 1
        else:
            print(f"  [⚪ 等待中/未开始] {fname}")

    print("=" * 60)
    print(f"汇总统计: 正在后台活跃下载: {active_tasks} | 中断可续传: {interrupted_tasks} | 已完成: {done_tasks}")
    print("=" * 60)

if __name__ == "__main__":
    main()
    print("\n按 Enter 键退出...")
    input()
