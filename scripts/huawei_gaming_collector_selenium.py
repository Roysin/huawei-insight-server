#!/usr/bin/env python3
"""
华为游戏性能数据Selenium自动化采集脚本 v1.0
使用系统已有Chrome，无需额外下载浏览器
"""

import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
except ImportError:
    print("请先安装Selenium: pip3 install selenium --break-system-packages")
    exit(1)

# ============ 配置区 ============
CONFIG = {
    "output_dir": "/root/.openclaw/workspace/data/huawei_collector",
    "history_file": "collected_history.json",
    
    "sources": {
        "huawei_dev": {
            "name": "华为开发者联盟",
            "enabled": True,
            "url": "https://developer.huawei.com/consumer/cn/doc/",
            "keywords": ["游戏", "GPU", "图形", "性能", "渲染", "Game", "Graphics", "加速", "game"],
            "timeout": 30,
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
    
    "chrome_options": [
        "--headless",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--window-size=1920,1080",
        "--disable-blink-features=AutomationControlled",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ]
}

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

def generate_id(url: str, title: str) -> str:
    content = f"{url}:{title}"
    return hashlib.md5(content.encode()).hexdigest()[:16]

def is_new_item(item_id: str, history: dict) -> bool:
    existing_ids = {item["id"] for item in history["items"]}
    return item_id not in existing_ids

def contains_keywords(text: str, keywords: list) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)

def count_recent_items(history: dict, days: int = 7) -> int:
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

# ============ Selenium采集器 ============

class SeleniumCollector:
    """Selenium浏览器采集器"""
    
    def __init__(self):
        self.driver = None
        
    def init_driver(self):
        """初始化Chrome浏览器"""
        chrome_options = Options()
        for opt in CONFIG["chrome_options"]:
            chrome_options.add_argument(opt)
        
        # 尝试找到chrome驱动
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except WebDriverException as e:
            print(f"Chrome启动失败: {e}")
            print("尝试安装ChromeDriver...")
            # 尝试使用webdriver-manager
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except:
                raise Exception("无法启动Chrome，请检查Chrome和ChromeDriver安装")
        
        self.driver.set_page_load_timeout(30)
        return self.driver
    
    def close(self):
        if self.driver:
            self.driver.quit()
    
    def collect_huawei_dev(self, history: dict) -> List[Dict]:
        """采集华为开发者联盟"""
        print("\n[1/2] 正在采集华为开发者联盟...")
        items = []
        source_config = CONFIG["sources"]["huawei_dev"]
        
        try:
            self.driver.get(source_config["url"])
            
            # 等待页面加载
            WebDriverWait(self.driver, source_config["timeout"]).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 提取所有文档链接
            links_data = self._extract_doc_links()
            
            # 关键词过滤
            for link in links_data[:30]:
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
                    
                    items.append(item)
                    
                    if item["is_new"]:
                        print(f"  [新] {link['title'][:50]}...")
            
            # 添加关键游戏性能文档
            self._add_key_docs(items, history)
            
        except TimeoutException:
            print("  ✗ 页面加载超时")
        except Exception as e:
            print(f"  ✗ 采集出错: {e}")
        
        print(f"  ✓ 采集完成: {len(items)} 条 (新: {len([i for i in items if i['is_new']])})")
        return items
    
    def _extract_doc_links(self) -> List[Dict]:
        """提取页面中的文档链接"""
        links = []
        
        # 使用多种选择器尝试提取链接
        selectors = [
            'a[href*="/doc/"]',
            '.doc-list a',
            '.content a',
            'article a',
            'main a'
        ]
        
        seen_urls = set()
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        title = elem.text.strip() or elem.get_attribute("title") or ""
                        href = elem.get_attribute("href") or ""
                        
                        if title and href and len(title) > 5 and href not in seen_urls:
                            seen_urls.add(href)
                            links.append({"title": title, "url": href})
                    except:
                        continue
            except:
                continue
        
        return links
    
    def _add_key_docs(self, items: List[Dict], history: dict):
        """添加重点游戏性能文档"""
        
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
        
        existing_urls = {item["url"] for item in items}
        
        for doc in key_docs:
            if doc["url"] in existing_urls:
                continue
            
            item_id = generate_id(doc["url"], doc["title"])
            
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
            
            items.append(item)
            
            if item["is_new"]:
                print(f"  [新-重点] {doc['title'][:40]}...")
    
    def collect_graphics_kits(self, history: dict) -> List[Dict]:
        """采集图形套件详情"""
        print("\n[2/2] 正在采集图形套件详情...")
        items = []
        source_config = CONFIG["sources"]["huawei_graphics_kits"]
        
        for url in source_config["urls"]:
            try:
                self.driver.get(url)
                
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                )
                
                # 提取标题
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1")
                    title = title_elem.text.strip()
                except:
                    title = self.driver.title or "Unknown"
                
                # 提取内容摘要
                try:
                    content_elem = self.driver.find_element(By.CSS_SELECTOR, ".doc-content, article, main, body")
                    content = content_elem.text.strip()[:500]
                except:
                    content = ""
                
                if title:
                    item_id = generate_id(url, title)
                    
                    item = {
                        "id": item_id,
                        "source": "huawei_graphics_kits",
                        "type": "kit_detail",
                        "title": title,
                        "url": url,
                        "content_snippet": content,
                        "collected_at": datetime.now().isoformat(),
                        "keywords": [kw for kw in source_config["keywords"] 
                                    if kw in title or kw in content],
                        "is_new": is_new_item(item_id, history)
                    }
                    
                    items.append(item)
                    
                    if item["is_new"]:
                        print(f"  [新] {title[:45]}...")
                
            except Exception as e:
                print(f"  ✗ 采集 {url[:50]}... 失败: {e}")
                continue
        
        print(f"  ✓ 采集完成: {len(items)} 条 (新: {len([i for i in items if i['is_new']])})")
        return items

# ============ 输出模块 ============

def generate_daily_report(items: List[Dict], history: dict) -> str:
    today = get_today_str()
    new_items = [item for item in items if item.get("is_new", False)]
    
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

*自动采集脚本 v1.0 | Selenium浏览器自动化版*
"""
    
    return report

def save_json_data(items: List[Dict]):
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

def main():
    print("=" * 65)
    print("  华为游戏性能数据采集脚本 v1.0")
    print("  Selenium浏览器自动化版")
    print("=" * 65)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    history = load_history()
    print(f"\n📚 历史记录: {len(history['items'])} 条")
    
    all_items = []
    collector = SeleniumCollector()
    
    try:
        print("\n🚀 启动Chrome浏览器...")
        collector.init_driver()
        print("✓ 浏览器启动成功")
        
        # 采集各数据源
        if CONFIG["sources"]["huawei_dev"]["enabled"]:
            items1 = collector.collect_huawei_dev(history)
            all_items.extend(items1)
        
        if CONFIG["sources"]["huawei_graphics_kits"]["enabled"]:
            items2 = collector.collect_graphics_kits(history)
            all_items.extend(items2)
        
    except Exception as e:
        print(f"\n✗ 运行失败: {e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        collector.close()
    
    # 更新历史
    new_items = [item for item in all_items if item.get("is_new", False)]
    history["items"].extend(new_items)
    history["items"] = history["items"][-1000:]
    save_history(history)
    
    # 生成输出
    print("\n" + "=" * 65)
    print("正在生成输出文件...")
    
    report = generate_daily_report(all_items, history)
    report_path = get_output_path(f"daily_report_{get_today_str()}.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ 日报已保存: {report_path}")
    
    json_path = save_json_data(all_items)
    print(f"✓ 数据已保存: {json_path}")
    
    # 摘要
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
    main()
