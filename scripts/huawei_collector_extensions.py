#!/usr/bin/env python3
"""
华为游戏性能数据采集系统 v5.0 - 扩展采集函数
新增20+数据源采集实现
"""

from typing import List, Dict, Set
from huawei_collector_v5 import SOURCES, kimi_fetch, content_hash, parse_highlights, get_now_str

def collect_huawei_forum(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集华为开发者论坛"""
    items = []
    source = SOURCES["huawei_forum"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n💬 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过（链接验证失败）")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "huawei_forum_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("huawei_forum_latest") != current_hash
    
    highlights = []
    if content:
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if any(kw in line for kw in source["keywords"]) and 10 < len(line) < 80:
                highlights.append(line[:80])
            if len(highlights) >= 3:
                break
    
    if not highlights:
        highlights = ["查看论坛最新技术讨论"]
    
    items.append({
        "id": "huawei_forum_latest",
        "source": "huawei_forum",
        "source_name": source["name"],
        "name": "开发者论坛热帖",
        "icon": source["icon"],
        "category": "社区讨论",
        "url": source["url"],
        "brief": "华为开发者游戏/图形技术讨论",
        "highlights": highlights[:3],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["huawei_forum_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

def collect_huawei_cloud_gaming(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集华为云游戏解决方案"""
    items = []
    source = SOURCES["huawei_cloud_gaming"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n☁️ 采集: {source['name']}...")
    
    for doc in source["urls"]:
        if doc["url"] in invalid_urls:
            print(f"  - {doc['name']}... ⚠️ 跳过")
            continue
        
        print(f"  - {doc['name']}...")
        content = kimi_fetch(doc["url"])
        current_hash = content_hash(content) if content else ""
        
        is_new = doc["id"] not in {i.get("id") for i in history["items"]}
        is_updated = not is_new and content_hashes.get(doc["id"]) != current_hash
        
        items.append({
            "id": doc["id"],
            "source": "huawei_cloud_gaming",
            "source_name": source["name"],
            "name": doc["name"],
            "icon": source["icon"],
            "category": "云游戏",
            "url": doc["url"],
            "brief": doc["brief"],
            "highlights": parse_highlights(content) if content else ["查看云游戏解决方案详情"],
            "collected_at": get_now_str(),
            "content_hash": current_hash,
            "is_new": is_new,
            "is_updated": is_updated
        })
        content_hashes[doc["id"]] = current_hash
        print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    
    return items, content_hashes

def collect_huawei_opensource(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集华为开源镜像站"""
    items = []
    source = SOURCES["huawei_opensource"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n📂 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过（链接验证失败）")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "huawei_opensource_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("huawei_opensource_latest") != current_hash
    
    items.append({
        "id": "huawei_opensource_latest",
        "source": "huawei_opensource",
        "source_name": source["name"],
        "name": "开源镜像站",
        "icon": source["icon"],
        "category": "开源资源",
        "url": source["url"],
        "brief": "游戏引擎/图形库开源镜像",
        "highlights": ["华为开源镜像站资源更新"],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["huawei_opensource_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

def collect_huawei_consumer(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集华为消费者BG新闻"""
    items = []
    source = SOURCES["huawei_consumer"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n📱 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "huawei_consumer_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("huawei_consumer_latest") != current_hash
    
    highlights = []
    if content:
        for line in content.split('\n'):
            line = line.strip()
            if any(kw in line for kw in source["keywords"]) and 10 < len(line) < 80:
                highlights.append(line[:80])
            if len(highlights) >= 3:
                break
    
    items.append({
        "id": "huawei_consumer_latest",
        "source": "huawei_consumer",
        "source_name": source["name"],
        "name": "消费者BG新闻",
        "icon": source["icon"],
        "category": "产品动态",
        "url": source["url"],
        "brief": "华为产品游戏性能相关新闻",
        "highlights": highlights[:3] if highlights else ["查看华为消费者业务最新动态"],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["huawei_consumer_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

def collect_harmonyos_dev(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集鸿蒙开发者社区"""
    items = []
    source = SOURCES["harmonyos_dev"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n🔷 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "harmonyos_dev_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("harmonyos_dev_latest") != current_hash
    
    highlights = []
    if content:
        for line in content.split('\n'):
            line = line.strip()
            if any(kw in line for kw in source["keywords"]) and 10 < len(line) < 80:
                highlights.append(line[:80])
            if len(highlights) >= 3:
                break
    
    items.append({
        "id": "harmonyos_dev_latest",
        "source": "harmonyos_dev",
        "source_name": source["name"],
        "name": "鸿蒙游戏开发",
        "icon": source["icon"],
        "category": "鸿蒙生态",
        "url": source["url"],
        "brief": "HarmonyOS游戏开发官方文档",
        "highlights": highlights[:3] if highlights else ["查看鸿蒙游戏开发最新资源"],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["harmonyos_dev_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

def collect_media_tuoluo(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集陀螺研究院报告"""
    items = []
    source = SOURCES["media_tuoluo"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n🌀 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "media_tuoluo_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("media_tuoluo_latest") != current_hash
    
    items.append({
        "id": "media_tuoluo_latest",
        "source": "media_tuoluo",
        "source_name": source["name"],
        "name": "行业研究报告",
        "icon": source["icon"],
        "category": "行业分析",
        "url": source["url"],
        "brief": "游戏行业深度分析报告",
        "highlights": ["查看游戏行业研究报告"],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["media_tuoluo_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

def collect_unity_china(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集Unity中国华为适配"""
    items = []
    source = SOURCES["unity_china"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n🎮 采集: {source['name']}...")
    
    for doc in source["urls"]:
        if doc["url"] in invalid_urls:
            print(f"  - {doc['name']}... ⚠️ 跳过")
            continue
        
        print(f"  - {doc['name']}...")
        content = kimi_fetch(doc["url"])
        current_hash = content_hash(content) if content else ""
        
        is_new = doc["id"] not in {i.get("id") for i in history["items"]}
        is_updated = not is_new and content_hashes.get(doc["id"]) != current_hash
        
        items.append({
            "id": doc["id"],
            "source": "unity_china",
            "source_name": source["name"],
            "name": doc["name"],
            "icon": source["icon"],
            "category": "游戏引擎",
            "url": doc["url"],
            "brief": doc["brief"],
            "highlights": parse_highlights(content) if content else ["查看Unity华为适配文档"],
            "collected_at": get_now_str(),
            "content_hash": current_hash,
            "is_new": is_new,
            "is_updated": is_updated
        })
        content_hashes[doc["id"]] = current_hash
        print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    
    return items, content_hashes

def collect_unreal_engine(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集Unreal Engine华为适配"""
    items = []
    source = SOURCES["unreal_engine"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n🎬 采集: {source['name']}...")
    
    for doc in source["urls"]:
        if doc["url"] in invalid_urls:
            print(f"  - {doc['name']}... ⚠️ 跳过")
            continue
        
        print(f"  - {doc['name']}...")
        content = kimi_fetch(doc["url"])
        current_hash = content_hash(content) if content else ""
        
        is_new = doc["id"] not in {i.get("id") for i in history["items"]}
        is_updated = not is_new and content_hashes.get(doc["id"]) != current_hash
        
        items.append({
            "id": doc["id"],
            "source": "unreal_engine",
            "source_name": source["name"],
            "name": doc["name"],
            "icon": source["icon"],
            "category": "游戏引擎",
            "url": doc["url"],
            "brief": doc["brief"],
            "highlights": parse_highlights(content) if content else ["查看UE5移动端开发文档"],
            "collected_at": get_now_str(),
            "content_hash": current_hash,
            "is_new": is_new,
            "is_updated": is_updated
        })
        content_hashes[doc["id"]] = current_hash
        print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    
    return items, content_hashes

def collect_cocos_harmonyos(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集Cocos鸿蒙版"""
    items = []
    source = SOURCES["cocos_harmonyos"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n🌟 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "cocos_harmonyos_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("cocos_harmonyos_latest") != current_hash
    
    items.append({
        "id": "cocos_harmonyos_latest",
        "source": "cocos_harmonyos",
        "source_name": source["name"],
        "name": "Cocos鸿蒙支持",
        "icon": source["icon"],
        "category": "游戏引擎",
        "url": source["url"],
        "brief": source["brief"],
        "highlights": parse_highlights(content) if content else ["查看Cocos鸿蒙发布指南"],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["cocos_harmonyos_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

def collect_competitor_qualcomm(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集高通竞品信息"""
    items = []
    source = SOURCES["competitor_qualcomm"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n🔺 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "competitor_qualcomm_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("competitor_qualcomm_latest") != current_hash
    
    items.append({
        "id": "competitor_qualcomm_latest",
        "source": "competitor_qualcomm",
        "source_name": source["name"],
        "name": "高通游戏方案",
        "icon": source["icon"],
        "category": "竞品参考",
        "url": source["url"],
        "brief": source["brief"],
        "highlights": parse_highlights(content) if content else ["查看高通游戏技术方案"],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["competitor_qualcomm_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

def collect_competitor_mediatek(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集联发科竞品信息"""
    items = []
    source = SOURCES["competitor_mediatek"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n🔷 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "competitor_mediatek_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("competitor_mediatek_latest") != current_hash
    
    items.append({
        "id": "competitor_mediatek_latest",
        "source": "competitor_mediatek",
        "source_name": source["name"],
        "name": "联发科游戏引擎",
        "icon": source["icon"],
        "category": "竞品参考",
        "url": source["url"],
        "brief": source["brief"],
        "highlights": parse_highlights(content) if content else ["查看联发科游戏引擎技术"],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["competitor_mediatek_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

def collect_arm_mali(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集ARM Mali GPU信息"""
    items = []
    source = SOURCES["arm_mali"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n⚙️ 采集: {source['name']}...")
    
    for doc in source["urls"]:
        if doc["url"] in invalid_urls:
            print(f"  - {doc['name']}... ⚠️ 跳过")
            continue
        
        print(f"  - {doc['name']}...")
        content = kimi_fetch(doc["url"])
        current_hash = content_hash(content) if content else ""
        
        is_new = doc["id"] not in {i.get("id") for i in history["items"]}
        is_updated = not is_new and content_hashes.get(doc["id"]) != current_hash
        
        items.append({
            "id": doc["id"],
            "source": "arm_mali",
            "source_name": source["name"],
            "name": doc["name"],
            "icon": source["icon"],
            "category": "GPU架构",
            "url": doc["url"],
            "brief": doc["brief"],
            "highlights": parse_highlights(content) if content else ["查看Mali GPU技术文档"],
            "collected_at": get_now_str(),
            "content_hash": current_hash,
            "is_new": is_new,
            "is_updated": is_updated
        })
        content_hashes[doc["id"]] = current_hash
        print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    
    return items, content_hashes

def collect_wipo_patents(history: Dict, invalid_urls: Set = None) -> List[Dict]:
    """采集WIPO华为专利"""
    items = []
    source = SOURCES["wipo_patents"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n🌐 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "wipo_patents_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("wipo_patents_latest") != current_hash
    
    items.append({
        "id": "wipo_patents_latest",
        "source": "wipo_patents",
        "source_name": source["name"],
        "name": "国际专利检索",
        "icon": source["icon"],
        "category": "专利文献",
        "url": source["url"],
        "brief": f"搜索: {source.get('search_term', 'Huawei graphics')}",
        "highlights": ["WIPO国际专利数据库"],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["wipo_patents_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

# 通用媒体采集（36氪/游戏葡萄/游戏茶馆/IEEE）
from huawei_collector_v5 import kimi_search

def collect_media_generic(history: Dict, source_id: str, source_config: Dict) -> List[Dict]:
    """通用媒体采集"""
    items = []
    
    print(f"\n{source_config['icon']} 采集: {source_config['name']}...")
    
    search_term = source_config.get("search_term", "华为游戏")
    results = kimi_search(search_term, limit=3)
    
    if results:
        highlights = [r.get('title', '')[:60] + "..." if len(r.get('title', '')) > 60 else r.get('title', '') for r in results[:3] if r.get('title')]
        
        items.append({
            "id": f"{source_id}_latest",
            "source": source_id,
            "source_name": source_config["name"],
            "name": "最新报道",
            "icon": source_config["icon"],
            "category": "行业媒体",
            "url": source_config.get("search_url", "https://www.google.com/search?q=" + search_term.replace(' ', '+')),
            "brief": f"搜索: {search_term}",
            "highlights": highlights if highlights else ["暂无新文章"],
            "collected_at": get_now_str(),
            "is_new": f"{source_id}_latest" not in {i.get("id") for i in history["items"]},
            "is_updated": len(results) > 0
        })
        print(f"    ✓ 发现 {len(results)} 篇文章")
    else:
        print(f"    ✗ 搜索失败")
    
    return items

def collect_academic_ieee(history: Dict) -> List[Dict]:
    """采集IEEE学术文献"""
    return collect_media_generic(history, "academic_ieee", SOURCES["academic_ieee"])
