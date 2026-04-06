#!/usr/bin/env python3
"""
华为游戏性能数据简化采集脚本 v0.2 (纯标准库版)
功能：每日采集华为开发者联盟技术文档 + B站相关评测
输出：Markdown日报 + JSON结构化数据
无需外部依赖，仅使用Python标准库
"""

import json
import hashlib
import os
import re
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, quote

# ============ 配置区 ============
CONFIG = {
    # 存储路径
    "output_dir": "/root/.openclaw/workspace/data/huawei_collector",
    "history_file": "collected_history.json",
    
    # 采集数据源
    "sources": {
        "huawei_dev": {
            "name": "华为开发者联盟",
            "enabled": True,
            "base_url": "https://developer.huawei.com",
            "doc_pages": [
                "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/",
                "https://developer.huawei.com/consumer/cn/doc/harmonyos-references/",
            ],
            "keywords": ["游戏", "GPU", "图形", "性能", "渲染", "HarmonyOS", "graphics", "gaming"],
        },
        "bilibili": {
            "name": "B站评测",
            "enabled": True,
            "search_urls": [
                "https://search.bilibili.com/all?keyword=华为%20游戏%20性能",
                "https://search.bilibili.com/all?keyword=华为%20麒麟%20原神",
            ],
        }
    },
    
    # 请求配置
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    "timeout": 30,
    "retry_times": 3,
}

# ============ 工具函数 ============

def get_today_str():
    return datetime.now().strftime("%Y-%m-%d")

def get_output_path(filename):
    """获取输出文件路径"""
    output_dir = Path(CONFIG["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / filename

def load_history():
    """加载已采集历史"""
    history_path = get_output_path(CONFIG["history_file"])
    if history_path.exists():
        with open(history_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"items": [], "last_run": None}

def save_history(history):
    """保存采集历史"""
    history_path = get_output_path(CONFIG["history_file"])
    history["last_run"] = datetime.now().isoformat()
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def generate_id(url, title):
    """生成唯一ID"""
    content = f"{url}:{title}"
    return hashlib.md5(content.encode()).hexdigest()[:16]

def is_new_item(item_id, history):
    """检查是否为新条目"""
    existing_ids = {item["id"] for item in history["items"]}
    return item_id not in existing_ids

def contains_keywords(text, keywords):
    """检查文本是否包含关键词"""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)

def fetch_url(url, retry=3):
    """带重试的HTTP请求"""
    # 确保URL正确编码
    if isinstance(url, str):
        # 对中文进行编码，但保留已编码的部分
        try:
            parts = url.split('?')
            if len(parts) == 2:
                base, query = parts
                # 对查询参数进行编码
                encoded_query = quote(query, safe='=&')
                url = base + '?' + encoded_query
        except:
            pass
    
    req = urllib.request.Request(url, headers=CONFIG["headers"])
    
    for i in range(retry):
        try:
            with urllib.request.urlopen(req, timeout=CONFIG["timeout"]) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"  请求失败 ({i+1}/{retry}): {url[:60]}... - {e}")
            if i < retry - 1:
                import time
                time.sleep(2)
    return None

def extract_links_from_html(html, base_url, keyword_filter=None):
    """从HTML中提取链接和标题"""
    links = []
    
    # 使用正则提取<a>标签
    pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    
    for href, title_html in matches:
        # 清理标题中的HTML标签
        title = re.sub(r'<[^>]+>', '', title_html).strip()
        title = re.sub(r'\s+', ' ', title)
        
        if not title or len(title) < 5:
            continue
        
        # 补全URL
        if href.startswith('/'):
            href = urljoin(base_url, href)
        elif not href.startswith('http'):
            href = urljoin(base_url, href)
        
        # 过滤条件
        if keyword_filter and not contains_keywords(title, keyword_filter):
            continue
        
        links.append({
            "title": title,
            "url": href
        })
    
    return links

def extract_bilibili_videos(html):
    """从B站搜索结果中提取视频信息"""
    videos = []
    
    # 尝试多种B站视频卡片格式
    patterns = [
        # 视频卡片格式1
        r'<div[^>]*class=["\'][^"\']*video-list-item[^"\']*["\'][^>]*>.*?<a[^>]*href=["\']([^"\']*video[^"\']*)["\'][^>]*>.*?<h3[^>]*>(.*?)</h3>',
        # 视频卡片格式2  
        r'<li[^>]*class=["\'][^"\']*video-list-item[^"\']*["\'][^>]*>.*?<a[^>]*href=["\']([^"\']*video[^"\']*)["\'][^>]*title=["\']([^"\']+)["\']',
        # 简化格式
        r'href=["\']([^"\']*video[^"\']*BV[^"\']*)["\'][^>]*title=["\']([^"\']+)["\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        for href, title in matches:
            # 清理标题
            title = re.sub(r'<[^>]+>', '', title).strip()
            title = re.sub(r'\s+', ' ', title)
            
            if not title or len(title) < 5:
                continue
            
            # 补全URL
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = 'https://www.bilibili.com' + href
            
            # 关键词过滤
            keywords = ["华为", "麒麟", "鸿蒙", "游戏", "性能", "评测", "原神", "王者", "mate", "p60", "p70"]
            if not contains_keywords(title, keywords):
                continue
            
            videos.append({
                "title": title,
                "url": href,
                "up_name": "未知"  # 简化版不提取UP主
            })
    
    # 去重
    seen = set()
    unique_videos = []
    for v in videos:
        if v["url"] not in seen:
            seen.add(v["url"])
            unique_videos.append(v)
    
    return unique_videos[:15]  # 限制数量

# ============ 采集器 ============

def collect_huawei_dev(history):
    """采集华为开发者联盟"""
    print("\n[1/2] 正在采集华为开发者联盟...")
    items = []
    source_config = CONFIG["sources"]["huawei_dev"]
    
    for doc_url in source_config["doc_pages"]:
        print(f"  访问: {doc_url[:60]}...")
        html = fetch_url(doc_url)
        if not html:
            continue
        
        links = extract_links_from_html(
            html, 
            source_config["base_url"],
            keyword_filter=source_config["keywords"]
        )
        
        for link in links[:15]:  # 限制数量
            item_id = generate_id(link["url"], link["title"])
            
            item = {
                "id": item_id,
                "source": "huawei_dev",
                "type": "tech_doc",
                "title": link["title"],
                "url": link["url"],
                "collected_at": datetime.now().isoformat(),
                "keywords": [kw for kw in source_config["keywords"] if kw.lower() in link["title"].lower()],
                "is_new": is_new_item(item_id, history)
            }
            
            items.append(item)
            
            if item["is_new"]:
                print(f"    [新] {link['title'][:45]}...")
    
    print(f"  ✓ 采集完成: {len(items)} 条 (新: {len([i for i in items if i['is_new']])})")
    return items

def collect_bilibili(history):
    """采集B站华为游戏评测"""
    print("\n[2/2] 正在采集B站评测...")
    items = []
    source_config = CONFIG["sources"]["bilibili"]
    
    for search_url in source_config["search_urls"]:
        print(f"  访问: {search_url[:60]}...")
        html = fetch_url(search_url)
        if not html:
            continue
        
        videos = extract_bilibili_videos(html)
        
        for video in videos:
            item_id = generate_id(video["url"], video["title"])
            
            item = {
                "id": item_id,
                "source": "bilibili",
                "type": "video_review",
                "title": video["title"],
                "url": video["url"],
                "up_name": video.get("up_name", "未知"),
                "collected_at": datetime.now().isoformat(),
                "keywords": [kw for kw in ["华为", "麒麟", "鸿蒙", "游戏", "性能", "评测"] if kw in video["title"]],
                "is_new": is_new_item(item_id, history)
            }
            
            items.append(item)
            
            if item["is_new"]:
                print(f"    [新] {video['title'][:45]}...")
    
    print(f"  ✓ 采集完成: {len(items)} 条 (新: {len([i for i in items if i['is_new']])})")
    return items

# ============ 输出模块 ============

def generate_daily_report(items, history):
    """生成日报"""
    today = get_today_str()
    new_items = [item for item in items if item["is_new"]]
    
    # 按来源分组
    huawei_items = [i for i in new_items if i["source"] == "huawei_dev"]
    bili_items = [i for i in new_items if i["source"] == "bilibili"]
    
    report = f"""# 华为游戏性能信息日报 - {today}

## 概览
- 采集时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 新增条目: {len(new_items)} 条
- 历史累计: {len(history['items']) + len(new_items)} 条

---

## 华为开发者联盟 ({len(huawei_items)} 条)
"""
    
    if huawei_items:
        report += "\n| 序号 | 标题 | 关键词 | 链接 |\n"
        report += "|------|------|--------|------|\n"
        for idx, item in enumerate(huawei_items[:15], 1):
            keywords = ", ".join(item["keywords"][:3]) if item["keywords"] else "-"
            title = item["title"][:40] + "..." if len(item["title"]) > 40 else item["title"]
            report += f"| {idx} | {title} | {keywords} | [查看]({item['url']}) |\n"
        if len(huawei_items) > 15:
            report += f"\n*还有 {len(huawei_items) - 15} 条未显示*\n"
    else:
        report += "\n今日无更新\n"
    
    report += f"\n---\n\n## B站评测 ({len(bili_items)} 条)\n"
    
    if bili_items:
        report += "\n| 序号 | 标题 | 关键词 | 链接 |\n"
        report += "|------|------|--------|------|\n"
        for idx, item in enumerate(bili_items[:15], 1):
            keywords = ", ".join(item["keywords"][:3]) if item["keywords"] else "-"
            title = item["title"][:40] + "..." if len(item["title"]) > 40 else item["title"]
            report += f"| {idx} | {title} | {keywords} | [B站]({item['url']}) |\n"
        if len(bili_items) > 15:
            report += f"\n*还有 {len(bili_items) - 15} 条未显示*\n"
    else:
        report += "\n今日无更新\n"
    
    report += f"""
---

## 历史趋势
- 最近7天新增: {count_recent_items(history, days=7) + len(new_items)} 条
- 最近30天新增: {count_recent_items(history, days=30) + len(new_items)} 条

---

*自动采集脚本 v0.2 | 纯标准库版 | 简化验证*
"""
    
    return report

def count_recent_items(history, days=7):
    """统计最近N天的新增条目"""
    cutoff = datetime.now() - timedelta(days=days)
    count = 0
    for item in history.get("items", []):
        try:
            item_time = datetime.fromisoformat(item.get("collected_at", ""))
            if item_time > cutoff:
                count += 1
        except:
            continue
    return count

def save_json_data(items):
    """保存JSON结构化数据"""
    today = get_today_str()
    filepath = get_output_path(f"data_{today}.json")
    
    data = {
        "date": today,
        "collected_at": datetime.now().isoformat(),
        "total": len(items),
        "new_items": len([i for i in items if i["is_new"]]),
        "items": items
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath

# ============ 主函数 ============

def main():
    print("=" * 65)
    print("  华为游戏性能数据采集脚本 v0.2")
    print("  纯标准库版 | 简化验证 | 无需外部依赖")
    print("=" * 65)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 加载历史记录
    history = load_history()
    print(f"\n📚 历史记录: {len(history['items'])} 条")
    
    all_items = []
    
    # 采集各数据源
    try:
        if CONFIG["sources"]["huawei_dev"]["enabled"]:
            huawei_items = collect_huawei_dev(history)
            all_items.extend(huawei_items)
    except Exception as e:
        print(f"  ✗ 华为开发者联盟采集出错: {e}")
    
    try:
        if CONFIG["sources"]["bilibili"]["enabled"]:
            bili_items = collect_bilibili(history)
            all_items.extend(bili_items)
    except Exception as e:
        print(f"  ✗ B站采集出错: {e}")
    
    # 更新历史
    new_items = [item for item in all_items if item["is_new"]]
    history["items"].extend(new_items)
    # 只保留最近1000条历史
    history["items"] = history["items"][-1000:]
    save_history(history)
    
    # 生成输出
    print("\n" + "=" * 65)
    print("正在生成输出文件...")
    
    # 1. Markdown日报
    report = generate_daily_report(all_items, history)
    report_path = get_output_path(f"daily_report_{get_today_str()}.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ 日报已保存: {report_path}")
    
    # 2. JSON数据
    json_path = save_json_data(all_items)
    print(f"✓ 数据已保存: {json_path}")
    
    # 3. 控制台输出摘要
    print("\n" + "=" * 65)
    print("📊 采集摘要")
    print("=" * 65)
    print(f"总条目:     {len(all_items)}")
    print(f"新增条目:   {len(new_items)}")
    print(f"  ├─ 华为开发者联盟: {len([i for i in all_items if i['source']=='huawei_dev'])} 条")
    print(f"  └─ B站评测:        {len([i for i in all_items if i['source']=='bilibili'])} 条")
    
    if new_items:
        print("\n" + "=" * 65)
        print("📰 新增内容预览")
        print("=" * 65)
        for item in new_items[:5]:
            source_tag = "[华为]" if item['source'] == 'huawei_dev' else "[B站]"
            print(f"{source_tag} {item['title'][:55]}")
    
    print("\n" + "=" * 65)
    print("✓ 运行完成")
    print("=" * 65)
    
    return all_items

if __name__ == "__main__":
    main()
