# Task 01: 统一点单决策卡片输出契约

- Status: Planned
- Owner: Product / Frontend / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Task 01 当前交付说明
- Depends On: `docs/rules/decision_card_contract.md`

## 目标

统一 Chat、`/estimate` 和前端结果视图的结果结构。

## 本期范围

1. 设计统一 `decision_card` 契约
2. 统一 schema / service / router 输出映射
3. 建立统一前端渲染容器
4. 为关键字段补齐测试

## 验收

1. 任一商品输入都能返回统一结构
2. 低置信进入澄清态
3. 保存型卡片有完整分类标签
4. `analysis_eligible` 能区分保存与分析
