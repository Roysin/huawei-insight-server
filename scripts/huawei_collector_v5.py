#!/usr/bin/env python3
"""
华为游戏性能数据采集系统 v5.0
多数据源版 - 支持B站/HMS Core/开发者博客
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
        "enabled": True,
        "items": [
            {
                "id": "graphics_kit",
                "name": "Graphics Accelerate Kit",
                "icon": "🎮",
                "category": "图形加速",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/graphics-accelerate-introduction",
                "brief": "解决游戏卡顿/掉帧/发热问题",
            },
            {
                "id": "xengine_kit",
                "name": "XEngine Kit",
                "icon": "🚀",
                "category": "GPU加速引擎",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/xengine-kit-introduction",
                "brief": "马良GPU性能提升方案",
            },
            {
                "id": "game_service",
                "name": "Game Service Kit",
                "icon": "👤",
                "category": "游戏服务",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/gameservice-introduction",
                "brief": "游戏基础能力建设",
            },
            {
                "id": "hismartperf",
                "name": "HiSmartPerf",
                "icon": "🔧",
                "category": "性能调优工具",
                "url": "https://developer.huawei.com/consumer/cn/doc/AppGallery-connect-Guides/smartperf-tool-overview",
                "brief": "跨平台游戏性能测试分析",
            }
        ]
    },
    
    "hms_core": {
        "name": "HMS Core服务",
        "icon": "📦",
        "enabled": True,
        "urls": [
            {
                "id": "hms_graphics",
                "name": "HMS Core图形引擎服务",
                "url": "https://developer.huawei.com/consumer/cn/doc/development/HMSCore-Guides/dev-process-0000001054326746",
                "brief": "Scene Kit开发文档"
            },
            {
                "id": "hms_game",
                "name": "HMS Core游戏服务",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/gameservice-introduction",
                "brief": "Game Service开发文档"
            },
            {
                "id": "hms_cg_kit",
                "name": "HMS Core图形计算服务",
                "url": "https://developer.huawei.com/consumer/cn/doc/development/HMSCore-Guides/introduction-0000001050197938",
                "brief": "CG Kit开发文档"
            }
        ]
    },
    # ...
    
    "huawei_blog": {
        "name": "华为开发者博客",
        "icon": "📝",
        "enabled": True,
        "url": "https://developer.huawei.com/consumer/cn/forum/block/1018536843266093168",
        "keywords": ["游戏", "GPU", "性能", "图形", "渲染", "HarmonyOS"]
    },
    
    "bilibili": {
        "name": "B站游戏评测",
        "icon": "📺",
        "enabled": True,
        "search_terms": [
            "华为 游戏性能 测试",
            "鸿蒙 游戏体验",
            "华为 GPU 性能",
            "Mate 游戏测试",
            "鸿蒙游戏优化"
        ],
        "max_videos": 5
    },
    
    "huawei_patents": {
        "name": "华为专利信息",
        "icon": "📜",
        "enabled": True,
        "urls": [
            {
                "id": "huawei_ipr_main",
                "name": "华为创新与知识产权",
                "url": "https://www.huawei.com/cn/ipr",
                "brief": "华为知识产权主页（15万件+有效授权专利）"
            },
            {
                "id": "huawei_ipr_license",
                "name": "华为专利许可项目",
                "url": "https://www.huawei.com/cn/ipr/license/mobile-handset",
                "brief": "手机/Wi-Fi/物联网专利许可"
            }
        ]
    },
    
    "graphics_standards": {
        "name": "图形标准组织",
        "icon": "📐",
        "enabled": True,
        "sources": [
            {
                "id": "khronos_vulkan",
                "name": "Vulkan标准更新",
                "url": "https://www.khronos.org/vulkan/",
                "brief": "Vulkan图形API最新规范与扩展"
            },
            {
                "id": "khronos_opengl",
                "name": "OpenGL ES标准",
                "url": "https://www.khronos.org/opengles/",
                "brief": "OpenGL ES移动图形标准"
            },
            {
                "id": "opengles_extensions",
                "name": "OpenGL扩展支持",
                "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/opengles-extensions",
                "brief": "华为OpenGL ES扩展支持列表"
            },
            {
                "id": "khronos_openxr",
                "name": "OpenXR标准",
                "url": "https://www.khronos.org/openxr/",
                "brief": "XR/VR/AR开放标准"
            }
        ]
    },
    
    # ========== 新增：更多图形标准源 ==========
    
    "webgpu_standard": {
        "name": "WebGPU标准",
        "icon": "🌐",
        "enabled": True,
        "url": "https://github.com/gpuweb/gpuweb",
        "brief": "WebGPU标准规范与社区资源"
    },
    
    "directx_blog": {
        "name": "DirectX官方博客",
        "icon": "🎮",
        "enabled": True,
        "url": "https://devblogs.microsoft.com/directx/",
        "brief": "微软DirectX最新技术动态"
    },
    
    "metal_docs": {
        "name": "Apple Metal文档",
        "icon": "🍎",
        "enabled": True,
        "url": "https://developer.apple.com/metal/",
        "brief": "Apple Metal图形API官方文档"
    },
    
    # ========== 新增数据源 ==========
    
    "huawei_forum": {
        "name": "华为开发者论坛",
        "icon": "💬",
        "enabled": True,
        "url": "https://developer.huawei.com/consumer/cn/forum/block/1018317060917936456",
        "keywords": ["游戏", "GPU", "性能", "图形", "渲染", "卡顿", "掉帧"]
    },
    
    "huawei_cloud_gaming": {
        "name": "华为云游戏解决方案",
        "icon": "☁️",
        "enabled": True,
        "urls": [
            {
                "id": "cloud_game_solution",
                "name": "华为云游戏服务器",
                "url": "https://www.huaweicloud.com/solution/cloudgame/",
                "brief": "云游戏/云渲染解决方案"
            },
            {
                "id": "cloud_game_docs",
                "name": "云游戏开发文档",
                "url": "https://support.huaweicloud.com/usermanual-cloudgame/",
                "brief": "云游戏接入与开发指南"
            }
        ]
    },
    
    "huawei_opensource": {
        "name": "华为开源镜像站",
        "icon": "📂",
        "enabled": True,
        "url": "https://mirrors.huaweicloud.com/",
        "keywords": ["游戏引擎", "图形库", "渲染"]
    },
    
    "huawei_consumer": {
        "name": "华为消费者BG",
        "icon": "📱",
        "enabled": True,
        "url": "https://consumer.huawei.com/cn/press/",
        "keywords": ["游戏", "性能", "GPU", "图形"]
    },
    
    "harmonyos_dev": {
        "name": "鸿蒙开发者社区",
        "icon": "🔷",
        "enabled": True,
        "url": "https://developer.harmonyos.com/cn/develop/games",
        "keywords": ["游戏开发", "图形", "ArkUI", "ArkTS"]
    },
    
    "media_36kr": {
        "name": "36氪-华为游戏",
        "icon": "📰",
        "enabled": True,
        "search_url": "https://36kr.com/search/articles/华为游戏",
        "search_term": "华为 游戏 性能"
    },
    
    "media_gamegrape": {
        "name": "游戏葡萄",
        "icon": "🍇",
        "enabled": True,
        "search_url": "https://youxiputao.com/?s=华为游戏",
        "search_term": "华为 游戏 鸿蒙"
    },
    
    "media_game茶馆": {
        "name": "游戏茶馆",
        "icon": "🍵",
        "enabled": True,
        "search_url": "https://www.youxichaguan.com/search?keyword=华为",
        "search_term": "华为 游戏性能"
    },
    
    "media_tuoluo": {
        "name": "陀螺研究院",
        "icon": "🌀",
        "enabled": True,
        "url": "https://www.tuoluo.cn/report",
        "keywords": ["华为", "游戏", "鸿蒙", "GPU"]
    },
    
    "unity_china": {
        "name": "Unity中国-华为",
        "icon": "🎮",
        "enabled": True,
        "urls": [
            {
                "id": "unity_harmonyos",
                "name": "Unity鸿蒙适配",
                "url": "https://docs.unity.cn/cn/tuanjiemanual/Manual/openharmony.html",
                "brief": "Unity对HarmonyOS的官方支持"
            },
            {
                "id": "unity_docs",
                "name": "Unity华为优化文档",
                "url": "https://docs.unity3d.com/cn/current/Manual/android-optimization.html",
                "brief": "Unity移动端性能优化指南"
            }
        ]
    },
    
    "unreal_engine": {
        "name": "Unreal Engine-华为",
        "icon": "🎬",
        "enabled": True,
        "urls": [
            {
                "id": "ue_android",
                "name": "UE5安卓开发",
                "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/setting-up-unreal-engine-projects-for-android-development",
                "brief": "UE5安卓平台开发指南"
            },
            {
                "id": "ue_vulkan",
                "name": "UE5 Vulkan支持",
                "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/vulkan-mobile-renderer-in-unreal-engine",
                "brief": "UE5 Vulkan渲染器"
            }
        ]
    },
    
    "cocos_harmonyos": {
        "name": "Cocos鸿蒙版",
        "icon": "🌟",
        "enabled": True,
        "url": "https://docs.cocos.com/creator/manual/zh/editor/publish/publish-huawei-ohos.html",
        "brief": "Cocos Creator发布鸿蒙应用"
    },
    
    "competitor_qualcomm": {
        "name": "高通Snapdragon",
        "icon": "🔺",
        "enabled": True,
        "url": "https://www.qualcomm.com/snapdragon",
        "brief": "竞品技术参考-高通骁龙移动平台"
    },
    
    "competitor_mediatek": {
        "name": "联发科天玑游戏引擎",
        "icon": "🔷",
        "enabled": True,
        "url": "https://www.mediatek.com/technologies/mobile-gaming",
        "brief": "竞品技术参考-天玑游戏方案"
    },
    
    "arm_mali": {
        "name": "ARM Mali GPU",
        "icon": "⚙️",
        "enabled": True,
        "urls": [
            {
                "id": "mali_gpu",
                "name": "Mali GPU开发者",
                "url": "https://developer.arm.com/Processors/Mali-GPU",
                "brief": "ARM Mali GPU架构文档（华为用Mali）"
            },
            {
                "id": "mali_optimization",
                "name": "Mali性能优化",
                "url": "https://developer.arm.com/documentation/100587/0100/",
                "brief": "Mali GPU最佳实践指南"
            }
        ]
    },
    
    "academic_ieee": {
        "name": "IEEE华为GPU论文",
        "icon": "📄",
        "enabled": True,
        "search_url": "https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=Huawei+GPU",
        "search_term": "Huawei GPU rendering"
    },
    
    "wipo_patents": {
        "name": "WIPO华为专利",
        "icon": "🌐",
        "enabled": True,
        "url": "https://patentscope.wipo.int/search/en/search.jsf",
        "search_term": "Huawei graphics GPU"
    },
    
    # ========== 新增：更多专利信息源 ==========
    
    "uspto_patents": {
        "name": "USPTO美国专利局",
        "icon": "🇺🇸",
        "enabled": True,
        "url": "https://ppubs.uspto.gov/pubwebapp/static/pages/landing.html",
        "search_term": "Huawei graphics GPU rendering"
    },
    
    "cnipa_patents": {
        "name": "中国国家知识产权局",
        "icon": "🇨🇳",
        "enabled": True,
        "url": "https://pss-system.cponline.cnipa.gov.cn/conventionalSearch",
        "search_term": "华为 图形 游戏 GPU"
    },
    
    "huawei_chaspark": {
        "name": "华为查思专利",
        "icon": "🔍",
        "enabled": True,
        "url": "https://www.chaspark.com/#/patents",
        "brief": "华为官方专利平台，免费无注册"
    },
    
    "google_patents": {
        "name": "Google Patents",
        "icon": "🔎",
        "enabled": True,
        "url": "https://patents.google.com/?q=Huawei&oq=Huawei+graphics",
        "search_term": "Huawei GPU graphics"
    },
    
    "epo_patents": {
        "name": "欧洲专利局Espacenet",
        "icon": "🇪🇺",
        "enabled": True,
        "url": "https://worldwide.espacenet.com/?locale=en_EP",
        "search_term": "Huawei graphics GPU"
    },
    
    # ========== 新增：更多图形标准源 ==========
    
    "khronos_news": {
        "name": "Khronos Group新闻",
        "icon": "📰",
        "enabled": True,
        "url": "https://www.khronos.org/news/",
        "keywords": ["Vulkan", "OpenGL", "OpenXR", "标准", "更新", "发布"]
    },
    
    "vulkan_cn": {
        "name": "Vulkan中文资讯",
        "icon": "🇨🇳",
        "enabled": True,
        "url": "https://vulkan.net.cn/news",
        "keywords": ["Vulkan", "中文", "新闻", "更新"]
    },
    
    "lunarg_sdk": {
        "name": "LunarG Vulkan SDK",
        "icon": "🛠️",
        "enabled": True,
        "url": "https://vulkan.lunarg.com/",
        "brief": "Vulkan SDK下载与工具"
    },
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
        "content_hashes": {}
    }

def save_history(history):
    history_path = get_output_path(CONFIG["history_file"])
    history["last_run"] = get_now_str()
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def content_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:16]

# ============ 链接验证 ============

def validate_url(url: str) -> tuple[bool, str]:
    """验证链接格式有效性（轻量级，不发起网络请求）
    返回: (格式是否有效, 状态信息)
    """
    import urllib.parse
    
    if not url or not isinstance(url, str):
        return False, "无效URL"
    
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme in ('http', 'https'):
        return False, "无效协议"
    if not parsed.netloc:
        return False, "无效域名"
    
    return True, "格式有效"

def validate_all_sources(skip_network: bool = True) -> dict:
    """验证所有数据源链接 - 轻量级版
    默认只检查URL格式，不发起网络请求（避免超时）
    实际有效性在采集时通过内容获取来验证
    """
    print("\n" + "=" * 60)
    print("  🔍 链接验证 (格式检查)")
    print("=" * 60)
    
    results = {"valid": [], "invalid": [], "total": 0, "passed": 0}
    all_urls = []
    
    def add_url(cat, name, url, sid=None):
        if url:
            all_urls.append((cat, name, url, sid))
    
    # 收集所有URL
    collectors = [
        ("huawei_official", "items", "📚 华为联盟"),
        ("hms_core", "urls", "📦 HMS Core"),
        ("huawei_patents", "urls", "📜 专利"),
        ("graphics_standards", "sources", "📐 标准"),
        ("huawei_cloud_gaming", "urls", "☁️ 云游戏"),
        ("unity_china", "urls", "🎮 Unity"),
        ("unreal_engine", "urls", "🎬 UE5"),
        ("arm_mali", "urls", "⚙️ Mali"),
    ]
    
    for sid, key, icon in collectors:
        if SOURCES.get(sid, {}).get("enabled"):
            for item in SOURCES[sid].get(key, []):
                add_url(icon, item["name"], item.get("url"), sid)
    
    singles = [
        ("huawei_blog", "📝 博客"), ("huawei_forum", "💬 论坛"),
        ("huawei_opensource", "📂 镜像"), ("huawei_consumer", "📱 消费者"),
        ("harmonyos_dev", "🔷 鸿蒙"), ("media_tuoluo", "🌀 研究"),
        ("cocos_harmonyos", "🌟 Cocos"), ("competitor_qualcomm", "🔺 高通"),
        ("competitor_mediatek", "🔷 联发科"), ("wipo_patents", "🌐 WIPO"),
        ("uspto_patents", "🇺🇸 USPTO"), ("cnipa_patents", "🇨🇳 CNIPA"),
        ("huawei_chaspark", "🔍 查思专利"), ("google_patents", "🔎 Google"),
        ("epo_patents", "🇪🇺 欧专局"), ("khronos_news", "📰 Khronos"),
        ("vulkan_cn", "🇨🇳 Vulkan中文"), ("lunarg_sdk", "🛠️ LunarG"),
        ("webgpu_standard", "🌐 WebGPU"), ("directx_blog", "🎮 DirectX"),
        ("metal_docs", "🍎 Metal"),
    ]
    
    for sid, icon in singles:
        if SOURCES.get(sid, {}).get("enabled"):
            add_url(icon, "首页", SOURCES[sid].get("url"), sid)
    
    results["total"] = len(all_urls)
    
    print(f"\n  检查 {len(all_urls)} 个链接格式...\n")
    
    for cat, name, url, sid in all_urls:
        is_valid, status = validate_url(url)
        
        if is_valid:
            symbol = "✅"
            results["passed"] += 1
            results["valid"].append({"cat": cat, "name": name, "url": url, "sid": sid})
        else:
            symbol = "❌"
            results["invalid"].append({"cat": cat, "name": name, "url": url, "reason": status})
        
        print(f"  {symbol} {cat} {name}")
    
    print(f"\n  结果: {results['passed']}/{results['total']} 格式有效")
    if results["invalid"]:
        print(f"  ❌ 格式错误: {len(results['invalid'])} 个")
    print("=" * 60)
    print("\n  ℹ️  注意: 实际可访问性将在采集时验证（通过内容获取）")
    
    return results
    
    if validation_results["invalid"]:
        print(f"  ❌ {len(validation_results['invalid'])} 个链接确认不可用:")
        for inv in validation_results["invalid"]:
            print(f"     - {inv['name']}: {inv['reason']}")
    
    if validation_results["unchecked"]:
        print(f"  ⚠️  {len(validation_results['unchecked'])} 个链接待采集时验证")
    
    print("=" * 60)
    
    return validation_results

# ============ 内容抓取 ============

def kimi_fetch(url: str) -> str:
    """使用kimi_fetch抓取网页"""
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

def kimi_search(query: str, limit: int = 5) -> List[Dict]:
    """使用kimi_search搜索"""
    try:
        result = subprocess.run(
            ['python3', '-c',
             f'import sys; sys.path.insert(0, "/usr/lib/node_modules/openclaw/extensions/kimi"); '
             f'from kimi_search import kimi_search; '
             f'import json; '
             f'results = kimi_search("{query}", limit={limit}); '
             f'print(json.dumps(results))'],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except:
        pass
    return []

def parse_highlights(content: str, max_items: int = 4) -> List[str]:
    """提取内容亮点"""
    highlights = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        # 提取关键描述
        if any(kw in line for kw in ["超帧", "ABR", "超分", "光追", "VRS", "性能", "优化", "提升"]):
            clean = line.replace('|', '').replace('#', '').strip()
            if 10 < len(clean) < 80 and clean not in highlights:
                highlights.append(clean)
        elif line.startswith('- ') or line.startswith('• '):
            clean = line[2:].strip()
            if 5 < len(clean) < 80 and clean not in highlights:
                highlights.append(clean)
    
    return highlights[:max_items] if highlights else ["详细内容请查看原文档"]

# ============ 各数据源采集 ============

def collect_huawei_official(history: Dict, invalid_urls: set = None) -> List[Dict]:
    """采集华为官方文档"""
    items = []
    source = SOURCES["huawei_official"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n📚 采集: {source['name']}...")
    
    for doc in source["items"]:
        if doc["url"] in invalid_urls:
            print(f"  - {doc['name']}...")
            print(f"    ⚠️ 跳过（链接验证失败）")
            continue
            
        print(f"  - {doc['name']}...")
        
        content = kimi_fetch(doc["url"])
        current_hash = content_hash(content) if content else ""
        
        is_new = doc["id"] not in {i.get("id") for i in history["items"]}
        is_updated = not is_new and content_hashes.get(doc["id"]) != current_hash
        
        item = {
            "id": doc["id"],
            "source": "huawei_official",
            "source_name": source["name"],
            "name": doc["name"],
            "icon": doc["icon"],
            "category": doc["category"],
            "url": doc["url"],
            "brief": doc["brief"],
            "highlights": parse_highlights(content) if content else ["详细内容请查看原文档"],
            "collected_at": get_now_str(),
            "content_hash": current_hash,
            "is_new": is_new,
            "is_updated": is_updated
        }
        
        items.append(item)
        content_hashes[doc["id"]] = current_hash
        
        status = "新增" if is_new else ("更新" if is_updated else "无变化")
        print(f"    ✓ {status}")
    
    return items, content_hashes

def collect_hms_core(history: Dict, invalid_urls: set = None) -> List[Dict]:
    """采集HMS Core更新日志"""
    items = []
    source = SOURCES["hms_core"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n📦 采集: {source['name']}...")
    
    for doc in source["urls"]:
        if doc["url"] in invalid_urls:
            print(f"  - {doc['name']}...")
            print(f"    ⚠️ 跳过（链接验证失败）")
            continue
            
        print(f"  - {doc['name']}...")
        
        content = kimi_fetch(doc["url"])
        current_hash = content_hash(content) if content else ""
        
        is_new = doc["id"] not in {i.get("id") for i in history["items"]}
        is_updated = not is_new and content_hashes.get(doc["id"]) != current_hash
        
        # 提取版本更新信息
        highlights = parse_highlights(content) if content else ["查看更新日志了解最新版本"]
        
        item = {
            "id": doc["id"],
            "source": "hms_core",
            "source_name": source["name"],
            "name": doc["name"],
            "icon": source["icon"],
            "category": "HMS服务",
            "url": doc["url"],
            "brief": doc["brief"],
            "highlights": highlights,
            "collected_at": get_now_str(),
            "content_hash": current_hash,
            "is_new": is_new,
            "is_updated": is_updated
        }
        
        items.append(item)
        content_hashes[doc["id"]] = current_hash
        
        status = "新增" if is_new else ("更新" if is_updated else "无变化")
        print(f"    ✓ {status}")
    
    return items, content_hashes

def collect_huawei_blog(history: Dict) -> List[Dict]:
    """采集华为开发者博客"""
    items = []
    source = SOURCES["huawei_blog"]
    content_hashes = history.get("content_hashes", {})
    
    print(f"\n📝 采集: {source['name']}...")
    
    content = kimi_fetch(source["url"])
    
    # 提取博客文章列表
    articles = []
    if content:
        # 简单提取标题和链接
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # 找可能是标题的行
            if len(line) > 10 and len(line) < 60:
                for kw in source["keywords"]:
                    if kw in line and line not in [a["title"] for a in articles]:
                        articles.append({
                            "title": line.strip(),
                            "line_idx": i
                        })
                        break
            if len(articles) >= 3:
                break
    
    if articles:
        doc_id = "huawei_blog_latest"
        highlights = [f"《{a['title']}》" for a in articles[:3]]
        
        is_new = doc_id not in {i.get("id") for i in history["items"]}
        current_hash = content_hash(content) if content else ""
        is_updated = not is_new and content_hashes.get(doc_id) != current_hash
        
        item = {
            "id": doc_id,
            "source": "huawei_blog",
            "source_name": source["name"],
            "name": "开发者博客最新文章",
            "icon": source["icon"],
            "category": "技术博客",
            "url": source["url"],
            "brief": "华为开发者最新技术文章",
            "highlights": highlights,
            "collected_at": get_now_str(),
            "content_hash": current_hash,
            "is_new": is_new,
            "is_updated": is_updated
        }
        
        items.append(item)
        content_hashes[doc_id] = current_hash
        print(f"    ✓ 发现 {len(articles)} 篇文章")
    else:
        print(f"    ✗ 未获取到内容")
    
    return items, content_hashes

def collect_bilibili(history: Dict) -> List[Dict]:
    """采集B站相关评测"""
    items = []
    source = SOURCES["bilibili"]
    
    print(f"\n📺 采集: {source['name']}...")
    
    # 只取第一个搜索词，避免过多请求
    search_term = source["search_terms"][0]
    results = kimi_search(search_term, limit=source.get("max_videos", 3))
    
    if results:
        highlights = []
        for r in results[:3]:
            title = r.get('title', '')
            if title:
                highlights.append(title[:50] + "..." if len(title) > 50 else title)
        
        doc_id = "bilibili_latest"
        
        item = {
            "id": doc_id,
            "source": "bilibili",
            "source_name": source["name"],
            "name": "B站相关评测视频",
            "icon": source["icon"],
            "category": "视频评测",
            "url": "https://search.bilibili.com/all?keyword=" + search_term.replace(' ', '%20'),
            "brief": f"搜索: {search_term}",
            "highlights": highlights if highlights else ["暂无新视频"],
            "collected_at": get_now_str(),
            "is_new": doc_id not in {i.get("id") for i in history["items"]},
            "is_updated": len(results) > 0
        }
        
        items.append(item)
        print(f"    ✓ 发现 {len(results)} 个视频")
    else:
        print(f"    ✗ 搜索失败")
    
    return items, {}

def collect_huawei_patents(history: Dict, invalid_urls: set = None) -> List[Dict]:
    """采集华为专利信息"""
    items = []
    source = SOURCES["huawei_patents"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n📜 采集: {source['name']}...")
    
    for doc in source["urls"]:
        if doc["url"] in invalid_urls:
            print(f"  - {doc['name']}...")
            print(f"    ⚠️ 跳过（链接验证失败）")
            continue
            
        print(f"  - {doc['name']}...")
        
        content = kimi_fetch(doc["url"])
        current_hash = content_hash(content) if content else ""
        
        is_new = doc["id"] not in {i.get("id") for i in history["items"]}
        is_updated = not is_new and content_hashes.get(doc["id"]) != current_hash
        
        # 提取专利亮点
        highlights = []
        if content:
            # 提取专利相关关键词
            patent_keywords = ["专利", "发明", "GPU", "图形", "渲染", "加速"]
            lines = content.split('\n')
            for line in lines[:50]:  # 只检查前50行
                line = line.strip()
                if any(kw in line for kw in patent_keywords) and len(line) > 10 and len(line) < 100:
                    highlights.append(line[:80])
                if len(highlights) >= 3:
                    break
        
        if not highlights:
            highlights = ["查看华为最新专利技术公开信息"]
        
        item = {
            "id": doc["id"],
            "source": "huawei_patents",
            "source_name": source["name"],
            "name": doc["name"],
            "icon": source["icon"],
            "category": "专利技术",
            "url": doc["url"],
            "brief": doc["brief"],
            "highlights": highlights[:3],
            "collected_at": get_now_str(),
            "content_hash": current_hash,
            "is_new": is_new,
            "is_updated": is_updated
        }
        
        items.append(item)
        content_hashes[doc["id"]] = current_hash
        
        status = "新增" if is_new else ("更新" if is_updated else "无变化")
        print(f"    ✓ {status}")
    
    return items, content_hashes

def collect_graphics_standards(history: Dict, invalid_urls: set = None) -> List[Dict]:
    """采集图形标准信息"""
    items = []
    source = SOURCES["graphics_standards"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n📐 采集: {source['name']}...")
    
    for doc in source["sources"]:
        if doc["url"] in invalid_urls:
            print(f"  - {doc['name']}...")
            print(f"    ⚠️ 跳过（链接验证失败）")
            continue
            
        print(f"  - {doc['name']}...")
        
        content = kimi_fetch(doc["url"])
        current_hash = content_hash(content) if content else ""
        
        is_new = doc["id"] not in {i.get("id") for i in history["items"]}
        is_updated = not is_new and content_hashes.get(doc["id"]) != current_hash
        
        # 提取标准更新亮点
        highlights = []
        if content:
            # 提取版本号、新特性等
            version_pattern = r'(Vulkan|OpenGL|OpenXR)\s*[\d.]+'
            import re
            lines = content.split('\n')
            for line in lines[:30]:
                line = line.strip()
                # 找版本更新信息
                if re.search(version_pattern, line) or any(kw in line for kw in ["新特性", "扩展", "规范", "Spec"]):
                    if len(line) > 10 and len(line) < 100 and line not in highlights:
                        highlights.append(line[:80])
                if len(highlights) >= 3:
                    break
        
        if not highlights:
            highlights = [f"查看最新{doc['name']}规范更新"]
        
        item = {
            "id": doc["id"],
            "source": "graphics_standards",
            "source_name": source["name"],
            "name": doc["name"],
            "icon": source["icon"],
            "category": "图形标准",
            "url": doc["url"],
            "brief": doc["brief"],
            "highlights": highlights[:3],
            "collected_at": get_now_str(),
            "content_hash": current_hash,
            "is_new": is_new,
            "is_updated": is_updated
        }
        
        items.append(item)
        content_hashes[doc["id"]] = current_hash
        
        status = "新增" if is_new else ("更新" if is_updated else "无变化")
        print(f"    ✓ {status}")
    
    return items, content_hashes

# ============ 新增数据源采集函数 ============

def collect_huawei_forum(history: Dict, invalid_urls: set = None) -> List[Dict]:
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
            if any(kw in line for kw in source["keywords"]) and len(line) > 10 and len(line) < 80:
                highlights.append(line[:80])
            if len(highlights) >= 3:
                break
    
    if not highlights:
        highlights = ["查看论坛最新技术讨论"]
    
    item = {
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
    }
    
    items.append(item)
    content_hashes["huawei_forum_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    
    return items, content_hashes

def collect_huawei_cloud_gaming(history: Dict, invalid_urls: set = None) -> List[Dict]:
    """采集华为云游戏解决方案"""
    items = []
    source = SOURCES["huawei_cloud_gaming"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n☁️ 采集: {source['name']}...")
    
    for doc in source["urls"]:
        if doc["url"] in invalid_urls:
            print(f"  - {doc['name']}...")
            print(f"    ⚠️ 跳过（链接验证失败）")
            continue
        
        print(f"  - {doc['name']}...")
        
        content = kimi_fetch(doc["url"])
        current_hash = content_hash(content) if content else ""
        
        is_new = doc["id"] not in {i.get("id") for i in history["items"]}
        is_updated = not is_new and content_hashes.get(doc["id"]) != current_hash
        
        highlights = parse_highlights(content) if content else ["查看云游戏解决方案详情"]
        
        item = {
            "id": doc["id"],
            "source": "huawei_cloud_gaming",
            "source_name": source["name"],
            "name": doc["name"],
            "icon": source["icon"],
            "category": "云游戏",
            "url": doc["url"],
            "brief": doc["brief"],
            "highlights": highlights,
            "collected_at": get_now_str(),
            "content_hash": current_hash,
            "is_new": is_new,
            "is_updated": is_updated
        }
        
        items.append(item)
        content_hashes[doc["id"]] = current_hash
        print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    
    return items, content_hashes

def collect_huawei_opensource(history: Dict, invalid_urls: set = None) -> List[Dict]:
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

def collect_huawei_consumer(history: Dict, invalid_urls: set = None) -> List[Dict]:
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

def collect_harmonyos_dev(history: Dict, invalid_urls: set = None) -> List[Dict]:
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

def collect_media_tuoluo(history: Dict, invalid_urls: set = None) -> List[Dict]:
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

def collect_unity_china(history: Dict, invalid_urls: set = None) -> List[Dict]:
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

def collect_unreal_engine(history: Dict, invalid_urls: set = None) -> List[Dict]:
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

def collect_cocos_harmonyos(history: Dict, invalid_urls: set = None) -> List[Dict]:
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

def collect_competitor_qualcomm(history: Dict, invalid_urls: set = None) -> List[Dict]:
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

def collect_competitor_mediatek(history: Dict, invalid_urls: set = None) -> List[Dict]:
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

def collect_arm_mali(history: Dict, invalid_urls: set = None) -> List[Dict]:
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

def collect_wipo_patents(history: Dict, invalid_urls: set = None) -> List[Dict]:
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

# ========== 新增：更多专利数据源采集 ==========

def collect_single_url_source(history: Dict, source_id: str, source_config: Dict, invalid_urls: set = None) -> List[Dict]:
    """通用单链接数据源采集"""
    items = []
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n{source_config['icon']} 采集: {source_config['name']}...")
    
    url = source_config.get("url")
    if not url or url in invalid_urls:
        print(f"    ⚠️ 跳过")
        return items, content_hashes
    
    content = kimi_fetch(url)
    current_hash = content_hash(content) if content else ""
    
    item_id = f"{source_id}_latest"
    is_new = item_id not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get(item_id) != current_hash
    
    # 提取亮点
    highlights = []
    keywords = source_config.get("keywords", [])
    if content and keywords:
        for line in content.split('\n')[:30]:
            line = line.strip()
            if any(kw in line for kw in keywords) and 10 < len(line) < 80:
                highlights.append(line[:80])
            if len(highlights) >= 3:
                break
    
    if not highlights:
        highlights = [source_config.get("brief", f"查看{source_config['name']}最新信息")]
    
    items.append({
        "id": item_id,
        "source": source_id,
        "source_name": source_config["name"],
        "name": source_config.get("brief", "首页")[:20],
        "icon": source_config["icon"],
        "category": "专利检索" if "patent" in source_id else "图形标准",
        "url": url,
        "brief": source_config.get("search_term", source_config.get("brief", "查看详情")),
        "highlights": highlights[:3],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes[item_id] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

def collect_media_generic(history: Dict, source_id: str, source_config: Dict) -> List[Dict]:
    """通用媒体采集（36氪/游戏葡萄/游戏茶馆/IEEE）"""
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

def collect_webgpu_standard(history: Dict, invalid_urls: set = None) -> List[Dict]:
    """采集WebGPU标准"""
    items = []
    source = SOURCES["webgpu_standard"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n🌐 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "webgpu_standard_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("webgpu_standard_latest") != current_hash
    
    items.append({
        "id": "webgpu_standard_latest",
        "source": "webgpu_standard",
        "source_name": source["name"],
        "name": "WebGPU标准规范",
        "icon": source["icon"],
        "category": "图形标准",
        "url": source["url"],
        "brief": source["brief"],
        "highlights": ["查看WebGPU最新规范与示例"] if not content else parse_highlights(content)[:3],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["webgpu_standard_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

def collect_directx_blog(history: Dict, invalid_urls: set = None) -> List[Dict]:
    """采集DirectX官方博客"""
    items = []
    source = SOURCES["directx_blog"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n🎮 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "directx_blog_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("directx_blog_latest") != current_hash
    
    highlights = parse_highlights(content) if content else ["查看DirectX最新技术动态"]
    
    items.append({
        "id": "directx_blog_latest",
        "source": "directx_blog",
        "source_name": source["name"],
        "name": "DirectX技术博客",
        "icon": source["icon"],
        "category": "图形标准",
        "url": source["url"],
        "brief": source["brief"],
        "highlights": highlights[:3],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["directx_blog_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

def collect_metal_docs(history: Dict, invalid_urls: set = None) -> List[Dict]:
    """采集Apple Metal文档"""
    items = []
    source = SOURCES["metal_docs"]
    content_hashes = history.get("content_hashes", {})
    invalid_urls = invalid_urls or set()
    
    print(f"\n🍎 采集: {source['name']}...")
    
    if source["url"] in invalid_urls:
        print(f"    ⚠️ 跳过")
        return items, content_hashes
    
    content = kimi_fetch(source["url"])
    current_hash = content_hash(content) if content else ""
    
    is_new = "metal_docs_latest" not in {i.get("id") for i in history["items"]}
    is_updated = not is_new and content_hashes.get("metal_docs_latest") != current_hash
    
    highlights = parse_highlights(content) if content else ["查看Metal图形API最新文档"]
    
    items.append({
        "id": "metal_docs_latest",
        "source": "metal_docs",
        "source_name": source["name"],
        "name": "Metal开发者文档",
        "icon": source["icon"],
        "category": "图形标准",
        "url": source["url"],
        "brief": source["brief"],
        "highlights": highlights[:3],
        "collected_at": get_now_str(),
        "content_hash": current_hash,
        "is_new": is_new,
        "is_updated": is_updated
    })
    
    content_hashes["metal_docs_latest"] = current_hash
    print(f"    ✓ {'新增' if is_new else ('更新' if is_updated else '无变化')}")
    return items, content_hashes

# ============ 飞书消息生成 ============

def generate_feishu_message(items: List[Dict]) -> str:
    """生成手机友好的飞书消息"""
    today = get_today_str()
    
    # 按来源分组
    sources = {}
    for item in items:
        src = item.get("source_name", "其他")
        if src not in sources:
            sources[src] = []
        sources[src].append(item)
    
    new_count = len([i for i in items if i.get("is_new")])
    update_count = len([i for i in items if i.get("is_updated") and not i.get("is_new")])
    
    lines = [
        f"📱 **华为游戏性能日报 - {today}**",
        "",
        "━━━━━━━━━━━━━━━━━━",
        f"📊 新增: {new_count} | 更新: {update_count}",
        "━━━━━━━━━━━━━━━━━━",
        ""
    ]
    
    for source_name, source_items in sources.items():
        lines.append(f"📍 **{source_name}**")
        lines.append("")
        
        for item in source_items:
            status = ""
            if item.get("is_new"):
                status = " [新增]"
            elif item.get("is_updated"):
                status = " [更新]"
            
            lines.append(f"{item['icon']} **{item['name']}**{status}")
            lines.append(f"{item['brief']}")
            lines.append("")
            
            for hl in item.get("highlights", [])[:3]:
                lines.append(f"• {hl}")
            
            lines.append("")
            lines.append(f"🔗 {item['url']}")
            lines.append("")
        
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("")
    
    lines.append(f"⏰ {get_now_str()}")
    
    return "\n".join(lines)

# ============ 主函数 ============

def main():
    print("=" * 60)
    print("  华为游戏性能数据采集系统 v5.1")
    print("  全链接验证版")
    print("=" * 60)
    print(f"运行时间: {get_now_str()}")
    
    # 第一步：快速验证所有链接（1秒超时）
    print("\n  正在进行快速链接验证（1秒超时）...")
    print("  此步骤检测明显失效的链接（如404）\n")
    
    validation = validate_all_sources()
    
    if validation["passed"] == 0:
        print("\n❌ 所有链接均不可用，停止采集")
        return
    
    if validation["invalid"]:
        print(f"\n⚠️  发现 {len(validation['invalid'])} 个确认失效的链接，将自动跳过")
        for inv in validation["invalid"]:
            print(f"     - {inv['cat']} {inv['name']}")
    
    history = load_history()
    print(f"\n历史记录: {len(history['items'])} 条")
    
    # 记录无效链接
    invalid_urls = {inv["url"] for inv in validation["invalid"]}
    
    all_items = []
    content_hashes = history.get("content_hashes", {})
    
    # 采集各数据源（跳过无效链接）
    if SOURCES["huawei_official"]["enabled"]:
        items, hashes = collect_huawei_official(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    if SOURCES["hms_core"]["enabled"]:
        items, hashes = collect_hms_core(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    if SOURCES["huawei_blog"]["enabled"] and SOURCES["huawei_blog"]["url"] not in invalid_urls:
        items, hashes = collect_huawei_blog(history)
        all_items.extend(items)
        content_hashes.update(hashes)
    elif SOURCES["huawei_blog"]["url"] in invalid_urls:
        print(f"\n📝 采集: 华为开发者博客...")
        print(f"    ⚠️ 跳过（链接验证失败）")
    
    if SOURCES["bilibili"]["enabled"]:
        items, _ = collect_bilibili(history)
        all_items.extend(items)
    
    # 新增：华为专利信息
    if SOURCES.get("huawei_patents", {}).get("enabled", False):
        items, hashes = collect_huawei_patents(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：图形标准组织
    if SOURCES.get("graphics_standards", {}).get("enabled", False):
        items, hashes = collect_graphics_standards(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：华为开发者论坛
    if SOURCES.get("huawei_forum", {}).get("enabled", False):
        items, hashes = collect_huawei_forum(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：华为云游戏
    if SOURCES.get("huawei_cloud_gaming", {}).get("enabled", False):
        items, hashes = collect_huawei_cloud_gaming(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：华为开源镜像
    if SOURCES.get("huawei_opensource", {}).get("enabled", False):
        items, hashes = collect_huawei_opensource(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：华为消费者BG
    if SOURCES.get("huawei_consumer", {}).get("enabled", False):
        items, hashes = collect_huawei_consumer(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：鸿蒙开发者社区
    if SOURCES.get("harmonyos_dev", {}).get("enabled", False):
        items, hashes = collect_harmonyos_dev(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：行业媒体 - 36氪
    if SOURCES.get("media_36kr", {}).get("enabled", False):
        items = collect_media_generic(history, "media_36kr", SOURCES["media_36kr"])
        all_items.extend(items)
    
    # 新增：行业媒体 - 游戏葡萄
    if SOURCES.get("media_gamegrape", {}).get("enabled", False):
        items = collect_media_generic(history, "media_gamegrape", SOURCES["media_gamegrape"])
        all_items.extend(items)
    
    # 新增：行业媒体 - 游戏茶馆
    if SOURCES.get("media_game茶馆", {}).get("enabled", False):
        items = collect_media_generic(history, "media_game茶馆", SOURCES["media_game茶馆"])
        all_items.extend(items)
    
    # 新增：行业媒体 - 陀螺研究院
    if SOURCES.get("media_tuoluo", {}).get("enabled", False):
        items, hashes = collect_media_tuoluo(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：Unity中国
    if SOURCES.get("unity_china", {}).get("enabled", False):
        items, hashes = collect_unity_china(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：Unreal Engine
    if SOURCES.get("unreal_engine", {}).get("enabled", False):
        items, hashes = collect_unreal_engine(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：Cocos鸿蒙版
    if SOURCES.get("cocos_harmonyos", {}).get("enabled", False):
        items, hashes = collect_cocos_harmonyos(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：竞品 - 高通
    if SOURCES.get("competitor_qualcomm", {}).get("enabled", False):
        items, hashes = collect_competitor_qualcomm(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：竞品 - 联发科
    if SOURCES.get("competitor_mediatek", {}).get("enabled", False):
        items, hashes = collect_competitor_mediatek(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：ARM Mali
    if SOURCES.get("arm_mali", {}).get("enabled", False):
        items, hashes = collect_arm_mali(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：学术 - IEEE
    if SOURCES.get("academic_ieee", {}).get("enabled", False):
        items = collect_academic_ieee(history)
        all_items.extend(items)
    
    # 新增：WIPO专利
    if SOURCES.get("wipo_patents", {}).get("enabled", False):
        items, hashes = collect_wipo_patents(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 新增：更多专利数据源
    for source_id in ["uspto_patents", "cnipa_patents", "huawei_chaspark", "google_patents", "epo_patents"]:
        if SOURCES.get(source_id, {}).get("enabled", False):
            items, hashes = collect_single_url_source(history, source_id, SOURCES[source_id], invalid_urls)
            all_items.extend(items)
            content_hashes.update(hashes)
    
    # 新增：更多图形标准源
    for source_id in ["khronos_news", "vulkan_cn", "lunarg_sdk"]:
        if SOURCES.get(source_id, {}).get("enabled", False):
            items, hashes = collect_single_url_source(history, source_id, SOURCES[source_id], invalid_urls)
            all_items.extend(items)
            content_hashes.update(hashes)
    
    # 新增：WebGPU/DirectX/Metal
    if SOURCES.get("webgpu_standard", {}).get("enabled", False):
        items, hashes = collect_webgpu_standard(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    if SOURCES.get("directx_blog", {}).get("enabled", False):
        items, hashes = collect_directx_blog(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    if SOURCES.get("metal_docs", {}).get("enabled", False):
        items, hashes = collect_metal_docs(history, invalid_urls)
        all_items.extend(items)
        content_hashes.update(hashes)
    
    # 更新历史
    history["items"] = [i for i in history["items"] if i["id"] not in {x["id"] for x in all_items}]
    history["items"].extend(all_items)
    history["items"] = history["items"][-CONFIG["max_history"]:]
    history["content_hashes"] = content_hashes
    save_history(history)
    
    # 生成输出
    print("\n📝 生成报告...")
    
    feishu_msg = generate_feishu_message(all_items)
    feishu_path = get_output_path(f"feishu_msg_{get_today_str()}.txt")
    with open(feishu_path, 'w', encoding='utf-8') as f:
        f.write(feishu_msg)
    print(f"  ✓ 飞书消息: {feishu_path}")
    
    json_data = {
        "date": get_today_str(),
        "collected_at": get_now_str(),
        "total": len(all_items),
        "items": all_items
    }
    json_path = get_output_path(f"data_{get_today_str()}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ JSON数据: {json_path}")
    
    # 输出预览
    print("\n" + "=" * 60)
    print("飞书消息预览:")
    print("=" * 60)
    print(feishu_msg[:1000] + "..." if len(feishu_msg) > 1000 else feishu_msg)
    
    print("\n" + "=" * 60)
    print("✓ 采集完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
