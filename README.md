# Huawei Insight Server

华为游戏性能数据采集系统 - 服务端代码

## 项目结构

```
.
├── scripts/                    # 采集脚本
│   ├── huawei_collector_v5.py         # 主采集脚本（技术文档/专利/标准周报）
│   ├── huawei_forum_collector.py      # 开发者论坛日报采集
│   ├── huawei_collector_extensions.py # 扩展功能
│   └── ...
├── data/                       # 采集数据
│   ├── huawei_collector/       # 周报数据
│   └── huawei_forum/           # 论坛日报数据
└── reports/                    # 生成的报告
```

## 数据源

### 每周采集
- 华为开发者联盟（Graphics Kit, XEngine Kit, Game Service Kit, HiSmartPerf）
- HMS Core 图形引擎服务
- 华为专利信息
- 图形标准组织（Vulkan, OpenGL, OpenXR, WebGPU）
- 竞品参考（高通、联发科、ARM Mali）

### 每日采集
- 华为开发者论坛游戏/图形技术热帖

## 定时任务

| 任务 | 频率 | 时间 |
|------|------|------|
| 技术文档周报 | 每周一 | 9:17 AM |
| 开发者论坛日报 | 每天 | 9:27 AM |

## License

Private
