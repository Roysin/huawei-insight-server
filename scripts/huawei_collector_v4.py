#!/usr/bin/env python3
"""
华为游戏性能数据采集系统 v4.0
完整版 - 支持自动抓取、变更检测、飞书推送
"""

import json
import hashlib
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# ============ 配置 ============
CONFIG = {
    "output_dir": "/root/.openclaw/workspace/data/huawei_collector",
    "history_file": "collected_history.json",
    "feishu_user_id": "ou_e1ddd4a66b41d453fed0466e55789952",
    "max_history": 1000,
}

# ============ 数据源配置 ============
SOURCES = {
    "huawei_official": {
        "name": "华为开发者联盟",
        "icon": "📚",
        "items": [
            {
                "id": "graphics_kit",
                "name": "Graphics Accelerate Kit",
                "icon": "🎮",
                "category": "图形加速",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/graphics-accelerate-introduction",
                "brief": "解决游戏卡顿/掉帧/发热问题",
                "keywords": ["游戏", "GPU", "性能", "图形", "超帧"]
            },
            {
                "id": "xengine_kit",
                "name": "XEngine Kit",
                "icon": "🚀",
                "category": "GPU加速引擎",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/xengine-kit-introduction",
                "brief": "马良GPU性能提升方案",
                "keywords": ["GPU", "超分", "光线追踪", "马良GPU"]
            },
            {
                "id": "game_service",
                "name": "Game Service Kit",
                "icon": "👤",
                "category": "游戏服务",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/gameservice-introduction",
                "brief": "游戏基础能力建设",
                "keywords": ["游戏", "登录", "防沉迷"]
            },
            {
                "id": "hismartperf",
                "name": "HiSmartPerf",
                "icon": "🔧",
                "category": "性能调优工具",
                "url": "https://developer.huawei.com/consumer/cn/doc/AppGallery-connect-Guides/smartperf-tool-overview",
                "brief": "跨平台游戏性能测试分析",
                "keywords": ["性能测试", "调优", "CPU", "GPU"]
            }
        ]
    },
    "huawei_blogs": {
        "name": "华为开发者博客",
        "icon": "📝",
        "url_pattern": "https://developer.huawei.com/consumer/cn/forum/block/",
        "keywords": ["游戏", "GPU", "性能优化", "图形渲染"]
    }
}

# ============ 工具函数 ============

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
    return {
        "items": [],
        "last_run": None,
        "content_hashes": {}  # 用于变更检测
    }

def save_history(history):
    history_path = get_output_path(CONFIG["history_file"])
    history["last_run"] = get_now_str()
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def generate_id(source: str, name: str) -> str:
    content = f"{source}:{name}:{get_today_str()}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def content_hash(text: str) -> str:
    """生成内容哈希用于变更检测"""
    return hashlib.md5(text.encode()).hexdigest()[:16]

# ============ 内容抓取 ============

def fetch_url_content(url: str) -> str:
    """使用kimi_fetch抓取网页内容"""
    try:
        # 尝试使用系统命令调用 kimi_fetch
        result = subprocess.run(
            ['python3', '-c', f'import sys; sys.path.insert(0, "/usr/lib/node_modules/openclaw/extensions/kimi"); from kimi_fetch import kimi_fetch; print(kimi_fetch("{url}"))'],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return result.stdout
    except:
        pass
    
    # 降级到简单提示
    return f"[内容需手动查看] {url}"

def parse_content_highlights(content: str, max_items: int = 4) -> List[str]:
    """从内容中提取亮点"""
    highlights = []
    
    # 尝试提取表格中的关键信息
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        # 匹配功能描述行
        if any(kw in line for kw in ["超帧", "ABR", "超分", "光追", "VRS", "防沉迷", "登录"]):
            if len(line) > 10 and len(line) < 100:
                highlights.append(line.replace('|', '').strip())
        # 匹配列表项
        elif line.startswith('- ') or line.startswith('• '):
            clean = line[2:].strip()
            if len(clean) > 5 and len(clean) < 80:
                highlights.append(clean)
    
    # 去重并限制数量
    seen = set()
    unique = []
    for h in highlights:
        if h not in seen:
            seen.add(h)
            unique.append(h)
            if len(unique) >= max_items:
                break
    
    return unique if unique else ["详细内容请查看原文档"]

# ============ 飞书消息生成 ============

def generate_feishu_message(items: List[Dict], has_updates: bool = False) -> str:
    """生成手机友好的飞书消息"""
    today = get_today_str()
    
    lines = [
        f"📱 **华为游戏性能日报 - {today}**",
        "",
        "━━━━━━━━━━━━━━━━━━",
    ]
    
    if has_updates:
        new_count = len([i for i in items if i.get('is_updated')])
        lines.append(f"📊 发现更新: {new_count} 条")
    else:
        lines.append(f"📊 今日采集: {len(items)} 条")
    
    lines.extend([
        "━━━━━━━━━━━━━━━━━━",
        ""
    ])
    
    for item in items:
        # 标题行
        if item.get('is_updated'):
            lines.append(f"{item['icon']} **{item['name']}** [有更新]")
        elif item.get('is_new'):
            lines.append(f"{item['icon']} **{item['name']}** [新增]")
        else:
            lines.append(f"{item['icon']} **{item['name']}**")
        
        lines.append(f"{item['brief']}")
        lines.append("")
        
        # 亮点
        for highlight in item.get('highlights', [])[:4]:
            lines.append(f"• {highlight}")
        
        lines.append("")
        lines.append(f"🔗 {item['url']}")
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("")
    
    lines.append(f"📁 完整报告: {CONFIG['output_dir']}/")
    lines.append(f"⏰ 采集时间: {get_now_str()}")
    
    return "\n".join(lines)

def generate_summary_report(items: List[Dict]) -> str:
    """生成Markdown完整报告"""
    today = get_today_str()
    
    lines = [
        f"# 华为游戏性能信息日报 - {today}",
        "",
        "## 概览",
        f"- 采集时间: {get_now_str()}",
        f"- 总条目: {len(items)} 条",
        f"- 新增: {len([i for i in items if i.get('is_new')])} 条",
        f"- 更新: {len([i for i in items if i.get('is_updated')])} 条",
        ""
    ]
    
    for item in items:
        status_tag = ""
        if item.get('is_new'):
            status_tag = " [新增]"
        elif item.get('is_updated'):
            status_tag = " [更新]"
        
        lines.append(f"## {item['icon']} {item['name']}{status_tag}")
        lines.append("")
        lines.append(f"**类别:** {item['category']}")
        lines.append("")
        lines.append(f"**简介:** {item['brief']}")
        lines.append("")
        
        if 'content_hash' in item:
            lines.append(f"**内容哈希:** `{item['content_hash']}`")
            lines.append("")
        
        lines.append("**核心亮点:**")
        for highlight in item.get('highlights', []):
            lines.append(f"- {highlight}")
        lines.append("")
        
        lines.append(f"**文档链接:** [{item['url']}]({item['url']})")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.append(f"*自动采集系统 v4.0 | {get_now_str()}*")
    
    return "\n".join(lines)

# ============ 飞书推送 ============

def send_feishu_message(message: str) -> bool:
    """发送飞书消息"""
    try:
        # 使用openclaw message命令发送
        result = subprocess.run(
            ['openclaw', 'message', 'send', 
             '--channel', 'feishu',
             '--to', CONFIG['feishu_user_id'],
             '--message', message],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"飞书发送失败: {e}")
        return False

# ============ 主采集逻辑 ============

def collect_items() -> List[Dict]:
    """采集所有数据源"""
    history = load_history()
    content_hashes = history.get("content_hashes", {})
    
    all_items = []
    
    # 处理华为官方文档
    for source_item in SOURCES["huawei_official"]["items"]:
        item_id = source_item["id"]
        
        print(f"  采集: {source_item['name']}...")
        
        # 抓取内容
        raw_content = fetch_url_content(source_item["url"])
        current_hash = content_hash(raw_content)
        
        # 检查是否更新
        is_new = item_id not in {i.get("id") for i in history["items"]}
        is_updated = not is_new and content_hashes.get(item_id) != current_hash
        
        # 解析亮点
        highlights = parse_content_highlights(raw_content)
        if not highlights:
            highlights = source_item.get("keywords", ["详细内容请查看原文档"])
        
        item = {
            "id": item_id,
            "source": "huawei_official",
            "name": source_item["name"],
            "icon": source_item["icon"],
            "category": source_item["category"],
            "url": source_item["url"],
            "brief": source_item["brief"],
            "highlights": highlights,
            "collected_at": get_now_str(),
            "content_hash": current_hash,
            "is_new": is_new,
            "is_updated": is_updated
        }
        
        all_items.append(item)
        content_hashes[item_id] = current_hash
        
        if is_new:
            print(f"    ✓ 新增")
        elif is_updated:
            print(f"    ✓ 有更新")
        else:
            print(f"    ✓ 无变化")
    
    # 更新历史
    history["items"] = [i for i in history["items"] if i["id"] not in {x["id"] for x in all_items}]
    history["items"].extend(all_items)
    history["items"] = history["items"][-CONFIG["max_history"]:]
    history["content_hashes"] = content_hashes
    save_history(history)
    
    return all_items

# ============ 主函数 ============

def main():
    print("=" * 60)
    print("  华为游戏性能数据采集系统 v4.0")
    print("  完整版 - 自动抓取/变更检测/飞书推送")
    print("=" * 60)
    print(f"运行时间: {get_now_str()}")
    
    # 采集数据
    print("\n📡 正在采集数据...")
    items = collect_items()
    
    new_count = len([i for i in items if i.get('is_new')])
    updated_count = len([i for i in items if i.get('is_updated')])
    
    print(f"\n采集完成: {len(items)} 条")
    print(f"  - 新增: {new_count} 条")
    print(f"  - 更新: {updated_count} 条")
    
    # 生成输出
    print("\n📝 生成报告...")
    
    # Markdown报告
    md_report = generate_summary_report(items)
    md_path = get_output_path(f"daily_report_{get_today_str()}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"  ✓ Markdown: {md_path}")
    
    # JSON数据
    json_data = {
        "date": get_today_str(),
        "collected_at": get_now_str(),
        "total": len(items),
        "new": new_count,
        "updated": updated_count,
        "items": items
    }
    json_path = get_output_path(f"data_{get_today_str()}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ JSON: {json_path}")
    
    # 飞书消息
    feishu_msg = generate_feishu_message(items, has_updates=(updated_count > 0))
    feishu_path = get_output_path(f"feishu_msg_{get_today_str()}.txt")
    with open(feishu_path, 'w', encoding='utf-8') as f:
        f.write(feishu_msg)
    print(f"  ✓ 飞书消息: {feishu_path}")
    
    # 推送飞书
    print("\n📤 推送飞书...")
    if send_feishu_message(feishu_msg):
        print("  ✓ 推送成功")
    else:
        print("  ✗ 推送失败，消息已保存到文件")
    
    # 输出预览
    print("\n" + "=" * 60)
    print("飞书消息预览:")
    print("=" * 60)
    print(feishu_msg[:800] + "..." if len(feishu_msg) > 800 else feishu_msg)
    
    print("\n" + "=" * 60)
    print("✓ 采集系统运行完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
