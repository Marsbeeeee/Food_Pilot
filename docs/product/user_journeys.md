# FoodPilot 用户旅程

- Status: Draft
- Owner: Product
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为主链路与典型旅程的主文档
- Depends On: `docs/product/product_overview.md`
- Related Docs: `docs/system/system_overview.md`, `docs/system/data_lifecycle.md`

## 目标

把产品从页面列表描述成端到端旅程，明确用户如何进入、决策、保存、分析和复盘。

## 当前主链路

`注册/登录 -> 进入 Workspace -> 提交问题或商品信息 -> 获得推荐/估算/决策结果 -> 显式保存到 Food Log -> 加入 Insights 分析篮子 -> 生成日/周分析 -> 回到 Workspace 或 Profile 继续调整`

## 下一阶段目标主链路

`输入商品信息 -> 解析商品结构 -> 估算营养与置信度 -> 输出推荐等级/风险/建议 -> 用户决定是否保存、收藏或继续比较 -> 进入 Food Log / Favorites / Insights`

## 典型旅程

### 聊天问答

1. 用户在 `Workspace` 输入自然语言问题。
2. 系统分流到推荐、估算、解释或澄清。
3. 用户浏览结果，不一定保存。
4. 用户可将结构化估算结果显式保存到 Food Log。

### 点单决策

1. 用户切换到 `Decision Mode`。
2. 用户输入商品标题、商品描述或套餐文本。
3. 系统优先把输入视为商品对象，而不是普通问句。
4. 系统输出决策卡片。
5. 用户决定保存、收藏、重跑或继续比较。

### 低置信与澄清

1. 用户输入对象不明确，如“炒面热量多少”。
2. 系统发现标准化置信度不足。
3. 系统进入澄清态，追问关键缺失信息。
4. 用户补充信息后继续进入估算或决策链路。
