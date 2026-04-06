#!/usr/bin/env python3
"""
华为游戏性能数据浏览器自动化采集脚本 v1.0
基于 Playwright，支持定时运行
"""

import json
import hashlib
import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("请先安装Playwright: pip install playwright")
    print("然后安装浏览器: playwright install chromium")
    exit(1)

# ============ 配置区 ============
CONFIG = {
    # 存储路径
    "output_dir": "/root/.openclaw/workspace/data/huawei_collector",
    "history_file": "collected_history.json",
    "screenshots_dir": "screenshots",
    
    # 采集数据源
    "sources": {
        "huawei_dev": {
            "name": "华为开发者联盟",
            "enabled": True,
            "url": "https://developer.huawei.com/consumer/cn/doc/",
            "keywords": ["游戏", "GPU", "图形", "性能", "渲染", "Game", "Graphics", "加速"],
            "timeout": 30000,
        },
        "huawei_graphics_kits": {
            "name": "华为图形加速套件",
            "enabled": True,
            "urls": [
                "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/graphics-accelerate-introduction",
                "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/xengine-kit-introduction",
                "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/gameservice-introduction",
            ],
            "keywords": ["游戏", "GPU", "性能", "加速"],
        },
    },
    
    # 浏览器配置
    "browser": {
        "headless": True,  # 无头模式
        "slow_mo": 100,    # 操作延迟(ms)
        "viewport": {"width": 1920, "height": 1080},
    },
    
    # 并发配置
    "concurrency": 2,
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

def generate_id(url: str, title: str) -> str:
    """生成唯一ID"""
    content = f"{url}:{title}"
    return hashlib.md5(content.encode()).hexdigest()[:16]

def is_new_item(item_id: str, history: dict) -> bool:
    """检查是否为新条目"""
    existing_ids = {item["id"] for item in history["items"]}
    return item_id not in existing_ids

def contains_keywords(text: str, keywords: list) -> bool:
    """检查文本是否包含关键词"""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)

def count_recent_items(history: dict, days: int = 7) -> int:
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

# ============ 浏览器采集器 ============

class HuaweiDevCollector:
    """华为开发者联盟采集器"""
    
    def __init__(self, page: Page):
        self.page = page
        self.items = []
        
    async def collect(self, history: dict) -> List[Dict]:
        """采集华为开发者文档中心"""
        print("\n[1/2] 正在采集华为开发者联盟...")
        
        source_config = CONFIG["sources"]["huawei_dev"]
        
        try:
            # 访问文档中心
            await self.page.goto(
                source_config["url"],
                timeout=source_config["timeout"],
                wait_until="networkidle"
            )
            
            # 等待页面加载
            await self.page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)  # 额外等待JS渲染
            
            # 提取所有文档链接
            links = await self._extract_doc_links()
            
            # 关键词过滤并创建条目
            for link in links[:30]:  # 限制数量
                if contains_keywords(link["title"], source_config["keywords"]):
                    item_id = generate_id(link["url"], link["title"])
                    
                    item = {
                        "id": item_id,
                        "source": "huawei_dev",
                        "type": "tech_doc",
                        "title": link["title"],
                        "url": link["url"],
                        "collected_at": datetime.now().isoformat(),
                        "keywords": [kw for kw in source_config["keywords"] 
                                    if kw.lower() in link["title"].lower()],
                        "is_new": is_new_item(item_id, history)
                    }
                    
                    self.items.append(item)
                    
                    if item["is_new"]:
                        print(f"  [新] {link['title'][:50]}...")
            
            # 特别关注的游戏性能相关链接
            await self._collect_game_performance_docs(history)
            
        except Exception as e:
            print(f"  ✗ 采集出错: {e}")
        
        print(f"  ✓ 采集完成: {len(self.items)} 条 (新: {len([i for i in self.items if i['is_new']])})")
        return self.items
    
    async def _extract_doc_links(self) -> List[Dict]:
        """提取页面中的文档链接"""
        links = await self.page.evaluate("""
            () => {
                const results = [];
                const anchors = document.querySelectorAll('a[href*="/doc/"]');
                anchors.forEach(a => {
                    const title = a.textContent?.trim() || a.getAttribute('title') || '';
                    const href = a.href;
                    if (title && href && title.length > 5) {
                        results.push({title, url: href});
                    }
                });
                return results;
            }
        """)
        
        # 去重
        seen = set()
        unique_links = []
        for link in links:
            if link["url"] not in seen:
                seen.add(link["url"])
                unique_links.append(link)
        
        return unique_links
    
    async def _collect_game_performance_docs(self, history: dict):
        """采集特定的游戏性能相关文档"""
        
        # 已知的游戏性能关键文档URL
        key_docs = [
            {
                "title": "Graphics Accelerate Kit - 图形加速服务",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/graphics-accelerate-introduction",
                "desc": "解决游戏运行不流畅、卡顿掉帧、长时间运行造成发热发烫等痛点体验问题"
            },
            {
                "title": "XEngine Kit - GPU加速引擎服务",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/xengine-kit-introduction",
                "desc": "提供基于马良GPU的性能提升方案"
            },
            {
                "title": "Game Service Kit - 游戏服务",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/gameservice-introduction",
                "desc": "提供快速、低成本构建游戏基本能力与游戏场景优化服务"
            },
            {
                "title": "Game Controller Kit - 游戏控制器服务",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/game-controller-introduction",
                "desc": "支持游戏适配控制器外设，解决玩家操控性问题"
            },
            {
                "title": "游戏性能调优 HiSmartPerf",
                "url": "https://developer.huawei.com/consumer/cn/doc/AppGallery-connect-Guides/smartperf-tool-overview",
                "desc": "依托华为芯片和操作系统的优势构建的游戏性能优化工具"
            },
            {
                "title": "应用性能体验建议",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/performance-overview",
                "desc": "应用和元服务的性能体验建议"
            },
        ]
        
        for doc in key_docs:
            item_id = generate_id(doc["url"], doc["title"])
            
            # 检查是否已存在
            existing_urls = {item["url"] for item in self.items}
            if doc["url"] in existing_urls:
                continue
            
            item = {
                "id": item_id,
                "source": "huawei_dev",
                "type": "key_doc",
                "title": doc["title"],
                "url": doc["url"],
                "description": doc["desc"],
                "collected_at": datetime.now().isoformat(),
                "keywords": ["游戏", "GPU", "性能", "图形"],
                "is_new": is_new_item(item_id, history)
            }
            
            self.items.append(item)
            
            if item["is_new"]:
                print(f"  [新-重点] {doc['title'][:40]}...")

class GraphicsKitsCollector:
    """华为图形套件详情采集器"""
    
    def __init__(self, page: Page):
        self.page = page
        self.items = []
    
    async def collect(self, history: dict) -> List[Dict]:
        """采集图形套件的详细内容"""
        print("\n[2/2] 正在采集图形套件详情...")
        
        source_config = CONFIG["sources"]["huawei_graphics_kits"]
        
        for url in source_config["urls"]:
            try:
                await self.page.goto(url, timeout=30000, wait_until="networkidle")
                await self.page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(1)
                
                # 提取页面标题和主要内容
                page_info = await self._extract_page_info()
                
                if page_info["title"]:
                    item_id = generate_id(url, page_info["title"])
                    
                    item = {
                        "id": item_id,
                        "source": "huawei_graphics_kits",
                        "type": "kit_detail",
                        "title": page_info["title"],
                        "url": url,
                        "content_snippet": page_info["content"][:500] if page_info["content"] else "",
                        "collected_at": datetime.now().isoformat(),
                        "keywords": [kw for kw in source_config["keywords"] 
                                    if kw in page_info["title"] or kw in page_info["content"]],
                        "is_new": is_new_item(item_id, history)
                    }
                    
                    self.items.append(item)
                    
                    if item["is_new"]:
                        print(f"  [新] {page_info['title'][:45]}...")
                
            except Exception as e:
                print(f"  ✗ 采集 {url[:50]}... 失败: {e}")
                continue
        
        print(f"  ✓ 采集完成: {len(self.items)} 条 (新: {len([i for i in self.items if i['is_new']])})")
        return self.items
    
    async def _extract_page_info(self) -> Dict[str, str]:
        """提取页面标题和内容"""
        return await self.page.evaluate("""
            () => {
                const title = document.querySelector('h1')?.textContent?.trim() || 
                             document.querySelector('title')?.textContent?.trim() || '';
                
                // 提取主要内容
                const contentElement = document.querySelector('.doc-content') || 
                                      document.querySelector('article') ||
                                      document.querySelector('main') ||
                                      document.body;
                
                const content = contentElement?.textContent?.trim() || '';
                
                return {title, content};
            }
        """)

# ============ 输出模块 ============

def generate_daily_report(items: List[Dict], history: dict) -> str:
    """生成日报"""
    today = get_today_str()
    new_items = [item for item in items if item.get("is_new", False)]
    
    # 按来源分组
    dev_items = [i for i in new_items if i["source"] == "huawei_dev"]
    kit_items = [i for i in new_items if i["source"] == "huawei_graphics_kits"]
    
    report = f"""# 华为游戏性能信息日报 - {today}

## 概览
- 采集时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 新增条目: {len(new_items)} 条
- 历史累计: {len(history['items']) + len(new_items)} 条

---

## 华为开发者联盟 ({len(dev_items)} 条)
"""
    
    if dev_items:
        # 分离重点文档和普通文档
        key_docs = [i for i in dev_items if i.get("type") == "key_doc"]
        normal_docs = [i for i in dev_items if i.get("type") != "key_doc"]
        
        if key_docs:
            report += "\n### 重点游戏性能文档\n"
            report += "| 标题 | 描述 | 链接 |\n"
            report += "|------|------|------|\n"
            for item in key_docs:
                desc = item.get("description", "")[:40]
                title = item["title"][:35] + "..." if len(item["title"]) > 35 else item["title"]
                report += f"| {title} | {desc} | [查看]({item['url']}) |\n"
        
        if normal_docs:
            report += "\n### 其他相关文档\n"
            report += "| 标题 | 关键词 | 链接 |\n"
            report += "|------|--------|------|\n"
            for item in normal_docs[:10]:
                keywords = ", ".join(item.get("keywords", [])[:3])
                title = item["title"][:35] + "..." if len(item["title"]) > 35 else item["title"]
                report += f"| {title} | {keywords} | [查看]({item['url']}) |\n"
    else:
        report += "\n今日无更新\n"
    
    report += f"""
---

## 图形套件详情 ({len(kit_items)} 条)
"""
    
    if kit_items:
        report += "\n| 套件名称 | 内容摘要 | 链接 |\n"
        report += "|----------|----------|------|\n"
        for item in kit_items:
            snippet = item.get("content_snippet", "")[:35] + "..." if item.get("content_snippet") else "-"
            title = item["title"][:30] + "..." if len(item["title"]) > 30 else item["title"]
            report += f"| {title} | {snippet} | [查看]({item['url']}) |\n"
    else:
        report += "\n今日无更新\n"
    
    report += f"""
---

## 历史趋势
- 最近7天新增: {count_recent_items(history, days=7) + len(new_items)} 条
- 最近30天新增: {count_recent_items(history, days=30) + len(new_items)} 条

---

## 重点关注技术
| 技术名称 | 说明 | 文档链接 |
|----------|------|----------|
| Graphics Accelerate Kit | 解决游戏卡顿、发热问题 | [查看](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/graphics-accelerate-introduction) |
| XEngine Kit | 马良GPU性能提升方案 | [查看](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/xengine-kit-introduction) |
| Game Service Kit | 游戏场景优化服务 | [查看](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/gameservice-introduction) |
| HiSmartPerf | 游戏性能调优工具 | [查看](https://developer.huawei.com/consumer/cn/doc/AppGallery-connect-Guides/smartperf-tool-overview) |

---

*自动采集脚本 v1.0 | Playwright浏览器自动化版*
"""
    
    return report

def save_json_data(items: List[Dict]):
    """保存JSON结构化数据"""
    today = get_today_str()
    filepath = get_output_path(f"data_{today}.json")
    
    data = {
        "date": today,
        "collected_at": datetime.now().isoformat(),
        "total": len(items),
        "new_items": len([i for i in items if i.get("is_new", False)]),
        "items": items
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath

# ============ 主函数 ============

async def main():
    print("=" * 65)
    print("  华为游戏性能数据采集脚本 v1.0")
    print("  Playwright浏览器自动化版")
    print("=" * 65)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 加载历史记录
    history = load_history()
    print(f"\n📚 历史记录: {len(history['items'])} 条")
    
    all_items = []
    browser: Optional[Browser] = None
    
    try:
        async with async_playwright() as p:
            # 启动浏览器
            print("\n🚀 启动浏览器...")
            browser = await p.chromium.launch(
                headless=CONFIG["browser"]["headless"],
                slow_mo=CONFIG["browser"]["slow_mo"]
            )
            
            context = await browser.new_context(
                viewport=CONFIG["browser"]["viewport"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            page = await context.new_page()
            
            # 采集华为开发者联盟
            if CONFIG["sources"]["huawei_dev"]["enabled"]:
                collector1 = HuaweiDevCollector(page)
                items1 = await collector1.collect(history)
                all_items.extend(items1)
            
            # 采集图形套件详情
            if CONFIG["sources"]["huawei_graphics_kits"]["enabled"]:
                collector2 = GraphicsKitsCollector(page)
                items2 = await collector2.collect(history)
                all_items.extend(items2)
            
            # 关闭浏览器
            await browser.close()
            browser = None
            
    except Exception as e:
        print(f"\n✗ 浏览器操作失败: {e}")
        if browser:
            await browser.close()
        return
    
    # 更新历史
    new_items = [item for item in all_items if item.get("is_new", False)]
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
    print(f"  ├─ 开发者联盟: {len([i for i in all_items if i['source']=='huawei_dev'])} 条")
    print(f"  └─ 图形套件:   {len([i for i in all_items if i['source']=='huawei_graphics_kits'])} 条")
    
    if new_items:
        print("\n" + "=" * 65)
        print("📰 新增内容预览")
        print("=" * 65)
        for item in new_items[:5]:
            source_tag = "[文档]" if item["source"] == "huawei_dev" else "[套件]"
            print(f"{source_tag} {item['title'][:55]}")
    
    print("\n" + "=" * 65)
    print("✓ 运行完成")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
