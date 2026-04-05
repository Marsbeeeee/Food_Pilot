# FoodPilot 核心对象

- Status: Draft
- Owner: Product / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为跨模块核心对象语义定义
- Related Docs: `docs/rules/decision_card_contract.md`, `docs/rules/container_data_model.md`, `docs/system/data_lifecycle.md`

## 目标

定义在多个模块之间流动的核心对象，避免前端、后端和 PM 各自使用不同名字描述同一对象。

## 对象列表

### `raw_input`

用户提交给系统的原始输入。

典型字段：

- `mode`
- `message`
- `title`
- `description`
- `source_platform`
- `profile_id`

### `normalized_input`

输入预处理后的结果，用于进入商品理解层。

### `product_structure`

商品理解层输出的标准化商品结构。

典型字段：

- `category`
- `brand`
- `normalized_name`
- `product_scope`
- `size_or_spec`
- `addons`
- `sugar_level`
- `temperature`
- `combo_items`
- `quantity`
- `missing_fields`
- `confidence`

### `decision_card`

系统统一结果对象。

典型字段：

- `input_summary`
- `normalized_product`
- `nutrition_estimate`
- `confidence`
- `recommendation_level`
- `risk_tags`
- `adaptation_note`
- `adjustments`
- `alternatives`
- `needs_clarification`
- `save_target`
- `analysis_eligible`

### `save_target`

描述卡片若被保存，应该落到哪里以及以什么语义归档。

### `food_log_entry`

一次显式保存下来的记录项，不等于容器。

### `favorite_item`

用于复用、回看和再次决策的收藏关系对象，不等于正式分析输入。

### `analysis_item`

可被 Insights 直接消费的最底层、稳定、单一的可食用对象。

## 分层关系

1. `product_structure` 解决“它是什么”
2. `decision_card` 解决“它值不值得点、如何展示和操作”
3. `food_log_entry` 解决“它被保存成了什么记录”
4. `analysis_item` 解决“它是否能进入分析”
