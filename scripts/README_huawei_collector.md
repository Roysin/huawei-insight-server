# 华为游戏性能数据浏览器自动化采集脚本

## 文件说明

| 文件 | 说明 |
|------|------|
| `huawei_gaming_collector_v2.py` | Playwright浏览器自动化版 (推荐) |
| `huawei_gaming_collector.py` | 纯标准库版 (备用，无需安装依赖但功能受限) |

---

## 方案一：Playwright浏览器自动化版（推荐）

### 1. 安装依赖

```bash
# 安装Playwright
pip install playwright

# 安装浏览器（Chromium）
playwright install chromium
```

### 2. 运行脚本

```bash
cd /root/.openclaw/workspace
python3 scripts/huawei_gaming_collector_v2.py
```

### 3. 配置定时任务

```bash
# 编辑crontab
crontab -e

# 添加每天9点执行的定时任务
0 9 * * * cd /root/.openclaw/workspace && /usr/bin/python3 scripts/huawei_gaming_collector_v2.py >> /var/log/huawei_collector.log 2>&1
```

---

## 方案二：OpenClaw Cron定时任务（推荐集成）

创建每天自动运行的Cron任务：

```bash
openclaw cron add \
  --name "huawei-gaming-daily" \
  --schedule "0 9 * * *" \
  --command "cd /root/.openclaw/workspace && python3 scripts/huawei_gaming_collector_v2.py"
```

---

## 输出文件

运行后会生成以下文件：

```
/root/.openclaw/workspace/data/huawei_collector/
├── daily_report_YYYY-MM-DD.md    # 每日报告
├── data_YYYY-MM-DD.json          # 结构化数据
├── collected_history.json        # 采集历史（去重用）
└── screenshots/                  # 页面截图（如启用）
```

---

## 采集内容

### 华为开发者联盟
- Graphics Accelerate Kit (图形加速服务)
- XEngine Kit (GPU加速引擎)
- Game Service Kit (游戏服务)
- Game Controller Kit (游戏控制器服务)
- HiSmartPerf (游戏性能调优工具)
- 应用性能体验建议文档

### 采集字段
| 字段 | 说明 |
|------|------|
| id | 唯一标识 |
| source | 数据来源 |
| type | 内容类型 |
| title | 标题 |
| url | 链接 |
| description | 描述（部分） |
| keywords | 匹配的关键词 |
| collected_at | 采集时间 |
| is_new | 是否为新条目 |

---

## 配置修改

编辑脚本中的 `CONFIG` 变量：

```python
CONFIG = {
    "output_dir": "/your/custom/path",  # 修改输出路径
    
    "sources": {
        "huawei_dev": {
            "enabled": True,  # 启用/禁用该数据源
            "keywords": ["游戏", "GPU", ...],  # 修改关键词
        },
    },
    
    "browser": {
        "headless": True,  # False=显示浏览器窗口（调试）
        "slow_mo": 100,    # 操作延迟(毫秒)
    },
}
```

---

## 故障排查

### 问题：浏览器启动失败
```
Error: executable doesn't exist
```
**解决：** 运行 `playwright install chromium`

### 问题：页面加载超时
```
TimeoutError: Timeout 30000ms exceeded
```
**解决：** 增加 `timeout` 配置或检查网络

### 问题：无新数据
**可能原因：**
1. 页面结构变化 → 需要更新选择器
2. 已采集过所有内容 → 正常情况
3. 网络问题 → 检查日志

---

## 与纯标准库版对比

| 功能 | Playwright版 | 纯标准库版 |
|------|-------------|-----------|
| JavaScript渲染 | ✅ 支持 | ❌ 不支持 |
| 数据完整性 | ✅ 完整 | ⚠️ 受限 |
| 安装依赖 | 需要Playwright | 无需安装 |
| 运行速度 | 较慢(需启动浏览器) | 快 |
| 稳定性 | 高 | 中(依赖页面结构) |

---

## 建议

- **日常使用：** Playwright版，数据完整
- **快速验证/资源受限：** 纯标准库版
- **生产环境：** 建议先手动运行几次验证稳定性后再配置定时任务
