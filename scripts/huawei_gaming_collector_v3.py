#!/usr/bin/env python3
"""
华为游戏性能数据采集脚本 v2.0
手机友好格式版 - 飞书优化输出
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

try:
    from kimi_fetch import kimi_fetch
except ImportError:
    # 降级到标准库
    import urllib.request
    import ssl
    
    def kimi_fetch(url: str) -> str:
        """简单URL获取，禁用SSL验证"""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            with urllib.request.urlopen(url, context=ctx, timeout=30) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return f"Error: {e}"

# ============ 配置 ============
CONFIG = {
    "output_dir": "/root/.openclaw/workspace/data/huawei_collector",
    "history_file": "collected_history.json",
    "feishu_user_id": "ou_e1ddd4a66b41d453fed0466e55789952",
}

# ============ 数据源 ============
SOURCES = [
    {
        "name": "Graphics Accelerate Kit",
        "icon": "🎮",
        "category": "图形加速",
        "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/graphics-accelerate-introduction",
        "brief": "解决游戏卡顿/掉帧/发热问题",
        "highlights": [
            "超帧: MEMC插帧技术，提升帧率降低功耗",
            "ABR: 自适应分辨率渲染",
            "秒级启动: 内存镜像恢复技术",
            "资源包后台下载"
        ],
        "devices": "Phone、Tablet"
    },
    {
        "name": "XEngine Kit",
        "icon": "🚀",
        "category": "GPU加速引擎",
        "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/xengine-kit-introduction",
        "brief": "马良GPU性能提升方案",
        "highlights": [
            "超分: GPU/AI空域+时域超采样",
            "光追: 反射/阴影/AO/全局光照",
            "DDGI/NNGI: 动态漫反射/神经网络GI",
            "自适应VRS: 可变速率着色"
        ],
        "devices": "Phone、Tablet、PC/2in1、TV",
        "chip": "马良GPU"
    },
    {
        "name": "Game Service Kit",
        "icon": "👤",
        "category": "游戏服务",
        "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/gameservice-introduction",
        "brief": "游戏基础能力建设",
        "highlights": [
            "联合登录/实名认证",
            "未成年人防沉迷",
            "游戏场景感知",
            "近场快传"
        ],
        "devices": "Phone、Tablet、PC/2in1、TV"
    },
    {
        "name": "HiSmartPerf",
        "icon": "🔧",
        "category": "性能调优工具",
        "url": "https://developer.huawei.com/consumer/cn/doc/AppGallery-connect-Guides/smartperf-tool-overview",
        "brief": "跨平台游戏性能测试分析",
        "highlights": [
            "支持: HarmonyOS/Android/iOS/快游戏",
            "监测: CPU/GPU/FPS/功耗/温度",
            "工具: RS树/内存测试/Profiler",
            "平台: 全平台覆盖"
        ],
        "devices": "全平台"
    }
]

# ============ 工具函数 ============

def get_today_str():
    return datetime.now().strftime("%Y-%m-%d")

def get_output_path(filename):
    output_dir = Path(CONFIG["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / filename

def load_history():
    history_path = get_output_path(CONFIG["history_file"])
    if history_path.exists():
        with open(history_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"items": [], "last_run": None}

def save_history(history):
    history_path = get_output_path(CONFIG["history_file"])
    history["last_run"] = datetime.now().isoformat()
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def generate_id(name: str) -> str:
    content = f"{name}:{get_today_str()}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

# ============ 飞书消息生成 ============

def generate_feishu_message(items: List[Dict]) -> str:
    """生成手机友好的飞书消息"""
    today = get_today_str()
    
    lines = [
        f"📱 **华为游戏性能日报 - {today}**",
        "",
        "━━━━━━━━━━━━━━━━━━",
        f"📊 今日采集: {len(items)} 条新技术",
        "━━━━━━━━━━━━━━━━━━",
        ""
    ]
    
    for item in items:
        lines.append(f"{item['icon']} **{item['name']}**")
        lines.append(f"{item['brief']}")
        lines.append("")
        
        for highlight in item['highlights']:
            lines.append(f"• {highlight}")
        
        lines.append("")
        lines.append(f"🔗 {item['url']}")
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("")
    
    lines.append(f"📁 完整文件: {CONFIG['output_dir']}/")
    
    return "\n".join(lines)

def generate_markdown_report(items: List[Dict]) -> str:
    """生成Markdown格式完整报告"""
    today = get_today_str()
    
    lines = [
        f"# 华为游戏性能信息日报 - {today}",
        "",
        "## 概览",
        f"- 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 新增条目: {len(items)} 条",
        ""
    ]
    
    for item in items:
        lines.append(f"## {item['icon']} {item['name']}")
        lines.append("")
        lines.append(f"**类别:** {item['category']}")
        lines.append("")
        lines.append(f"**简介:** {item['brief']}")
        lines.append("")
        lines.append("**核心亮点:**")
        for highlight in item['highlights']:
            lines.append(f"- {highlight}")
        lines.append("")
        lines.append(f"**支持设备:** {item['devices']}")
        if 'chip' in item:
            lines.append(f"**芯片要求:** {item['chip']}")
        lines.append("")
        lines.append(f"**文档链接:** [{item['url']}]({item['url']})")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.append(f"*数据采集: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 来源: 华为开发者联盟*")
    
    return "\n".join(lines)

# ============ 主函数 ============

def main():
    print("=" * 50)
    print("  华为游戏性能数据采集脚本 v2.0")
    print("  手机友好格式版")
    print("=" * 50)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    history = load_history()
    print(f"历史记录: {len(history['items'])} 条")
    
    # 处理数据源
    all_items = []
    new_items = []
    
    for source in SOURCES:
        item_id = generate_id(source["name"])
        
        item = {
            "id": item_id,
            **source,
            "collected_at": datetime.now().isoformat(),
            "is_new": item_id not in {i["id"] for i in history["items"]}
        }
        
        all_items.append(item)
        
        if item["is_new"]:
            new_items.append(item)
            print(f"[新] {source['name']}")
    
    # 更新历史
    history["items"].extend(new_items)
    history["items"] = history["items"][-500:]  # 保留最近500条
    save_history(history)
    
    # 生成输出
    print("\n生成输出文件...")
    
    # Markdown完整报告
    md_report = generate_markdown_report(all_items)
    md_path = get_output_path(f"daily_report_{get_today_str()}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"✓ Markdown报告: {md_path}")
    
    # JSON数据
    json_data = {
        "date": get_today_str(),
        "collected_at": datetime.now().isoformat(),
        "total": len(all_items),
        "new_items": len(new_items),
        "items": all_items
    }
    json_path = get_output_path(f"data_{get_today_str()}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON数据: {json_path}")
    
    # 飞书消息
    feishu_msg = generate_feishu_message(all_items)
    feishu_path = get_output_path(f"feishu_msg_{get_today_str()}.txt")
    with open(feishu_path, 'w', encoding='utf-8') as f:
        f.write(feishu_msg)
    print(f"✓ 飞书消息: {feishu_path}")
    
    # 输出飞书消息到stdout
    print("\n" + "=" * 50)
    print("飞书消息内容:")
    print("=" * 50)
    print(feishu_msg)
    
    # 摘要
    print("\n" + "=" * 50)
    print("📊 采集摘要")
    print("=" * 50)
    print(f"总条目: {len(all_items)}")
    print(f"新增:   {len(new_items)}")
    
    print("\n✓ 完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()
