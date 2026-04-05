# FoodPilot 系统协作总览

- Status: Draft
- Owner: Product / Engineering
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为跨模块协作、系统主链路与边界的主文档
- Depends On: `docs/product/product_overview.md`, `docs/product/user_journeys.md`
- Related Docs: `docs/system/core_objects.md`, `docs/system/frontend_backend_contracts.md`, `docs/system/data_lifecycle.md`

## 目标

定义 FoodPilot 作为一个系统如何由多个模块协作，而不是只把功能拆成独立任务。

## 模块地图

### 入口层

1. `Workspace / Chat`
2. `Explorer / Food Log`
3. `Insights`
4. `Profile`

### 能力层

1. `Chat routing`
2. `Product understanding`
3. `Estimate API`
4. `Decision engine`
5. `Food KB / retrieval`
6. `Image assets and review`

### 沉淀层

1. `Food Log`
2. `Favorites / containers`
3. `Insights snapshots`
4. `Profile`

## 主协作链路

`输入层 -> 商品理解层 -> 估算层 -> 决策层 -> 结果卡片 -> 保存 / 收藏 / 分析 -> 历史沉淀与复用`

### 输入层

负责承接自然语言、商品标题、商品描述和未来的截图文本，不直接决定最终归档语义。

### 商品理解层

负责将低结构化输入转为标准化商品结构，输出品类、品牌、商品、规格、套餐、缺失信息和置信度。

### 估算层

负责营养估算、模板回退和依据说明，不负责前端渲染和长周期历史沉淀。

### 决策层

负责结合 `Profile` 与估算结果，输出推荐等级、风险标签、节奏友好说明、建议和替代方案。

### 结果承载层

统一由 `decision_card` 承载，避免 `Chat`、`/estimate`、前端卡片、保存动作使用不同对象语义。

### 沉淀层

`Food Log` 负责显式保存与归档；`Favorites` 负责复用和回看；`Insights` 只消费满足准入规则的最底层对象。

## 模块职责边界

### Workspace / Chat

负责输入承接、会话、结果展示和二次操作入口；不负责长期沉淀语义。

### Product Understanding

负责“把输入变成商品对象”；不负责最终推荐话术。

### Estimate API

负责原子估算能力；不是当前主入口。

### Decision Engine

负责生成决策结论；不负责会话管理和历史快照存储。

### Food Log

负责保存、归档、编辑、恢复；不负责重新推导推荐。

### Insights

负责聚合与 AI 快照分析；不直接接受上层容器对象。

### Profile

负责提供目标与约束；不应成为主链路硬阻塞。

## 关键协作原则

1. 一切新入口最终都应汇聚到同一商品理解层。
2. 一切可操作结果最终都应收敛到同一决策卡片契约。
3. 保存、收藏、分析是三种动作，不是同一种状态。
4. “可保存”与“可分析”必须分离。
5. 低置信时优先澄清，不直接生成伪确定结果。
6. 目录对象、容器对象、记录项对象、分析对象必须语义分层。
