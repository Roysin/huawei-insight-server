#!/usr/bin/env python3
"""
华为开发者论坛每日采集
轻量级版 - 只监控论坛热帖
"""

import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict

CONFIG = {
    "output_dir": "/root/.openclaw/workspace/data/huawei_forum",
    "history_file": "forum_history.json",
    "max_history": 200,
}

FORUM_URL = "https://developer.huawei.com/consumer/cn/forum/block/1018317060917936456"
KEYWORDS = ["游戏", "GPU", "性能", "图形", "渲染", "卡顿", "掉帧"]

def get_today_str():
    return datetime.now().strftime("%Y-%m-%d")

def get_now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_output_path(filename):
    output_dir = Path(CONFIG["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / filename

def load_history():
    history_path = get_output_path(CONFIG["history_file"])
    if history_path.exists():
        with open(history_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"items": [], "last_run": None, "content_hashes": {}}

def save_history(history):
    history_path = get_output_path(CONFIG["history_file"])
    history["last_run"] = get_now_str()
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def content_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]

def kimi_fetch(url: str) -> str:
    try:
        result = subprocess.run(
            ['python3', '-c', 
             f'import sys; sys.path.insert(0, "/usr/lib/node_modules/openclaw/extensions/kimi"); '
             f'from kimi_fetch import kimi_fetch; print(kimi_fetch("{url}"))'],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return result.stdout
    except:
        pass
    return ""

def extract_posts(content: str) -> List[str]:
    """提取论坛热帖标题"""
    posts = []
    if not content:
        return posts
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        # 找包含关键词的帖子标题
        if any(kw in line for kw in KEYWORDS) and 10 < len(line) < 80:
            if line not in posts:
                posts.append(line[:80])
        if len(posts) >= 5:
            break
    
    return posts

def main():
    print("=" * 60)
    print("  华为开发者论坛每日采集")
    print("=" * 60)
    print(f"运行时间: {get_now_str()}")
    print(f"监控关键词: {', '.join(KEYWORDS)}")
    
    history = load_history()
    print(f"\n历史记录: {len(history['items'])} 条")
    
    print(f"\n💬 采集论坛: {FORUM_URL}...")
    
    content = kimi_fetch(FORUM_URL)
    current_hash = content_hash(content) if content else ""
    
    # 提取热帖
    posts = extract_posts(content)
    
    item_id = "forum_latest"
    content_hashes = history.get("content_hashes", {})
    is_new = item_id not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get(item_id) != current_hash
    
    if not posts:
        posts = ["暂无相关热帖"]
    
    item = {
        "id": item_id,
        "source": "huawei_forum",
        "source_name": "华为开发者论坛",
        "name": "游戏/图形技术热帖",
        "icon": "💬",
        "category": "社区讨论",
        "url": FORUM_URL,
        "brief": "开发者论坛游戏性能相关讨论",
        "highlights": posts,
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    }
    
    # 更新历史
    history["items"] = [i for i in history["items"] if i["id"] != item_id]
    history["items"].append(item)
    history["items"] = history["items"][-CONFIG["max_history"]:]
    content_hashes[item_id] = current_hash
    history["content_hashes"] = content_hashes
    save_history(history)
    
    # 生成飞书消息
    status = "新增" if is_new else ("更新" if is_updated else "无变化")
    print(f"    ✓ {status} - 发现 {len(posts)} 个相关帖子")
    
    lines = [
        f"💬 **华为开发者论坛日报 - {get_today_str()}**",
        "",
        "━━━━━━━━━━━━━━━━━━",
        f"📊 状态: {status}",
        "━━━━━━━━━━━━━━━━━━",
        "",
        f"💬 **游戏/图形技术热帖**",
        f"关键词: {', '.join(KEYWORDS[:4])}",
        "",
    ]
    
    for post in posts:
        lines.append(f"• {post}")
    
    lines.extend([
        "",
        f"🔗 {FORUM_URL}",
        "",
        f"⏰ {get_now_str()}"
    ])
    
    feishu_msg = "\n".join(lines)
    
    # 保存输出
    feishu_path = get_output_path(f"feishu_msg_{get_today_str()}.txt")
    with open(feishu_path, 'w', encoding='utf-8') as f:
        f.write(feishu_msg)
    print(f"\n  ✓ 飞书消息: {feishu_path}")
    
    json_data = {
        "date": get_today_str(),
        "collected_at": get_now_str(),
        "status": status,
        "posts_found": len(posts),
        "posts": posts
    }
    json_path = get_output_path(f"data_{get_today_str()}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ JSON数据: {json_path}")
    
    # 输出预览
    print("\n" + "=" * 60)
    print("飞书消息预览:")
    print("=" * 60)
    print(feishu_msg[:600] + "..." if len(feishu_msg) > 600 else feishu_msg)
    
    print("\n" + "=" * 60)
    print("✓ 采集完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
