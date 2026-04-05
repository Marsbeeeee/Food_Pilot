# Task 04: 品牌感知估算层 V1

- Status: Planned
- Owner: Product / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Task 04 当前交付说明
- Depends On: `docs/modules/decision_engine.md`, `docs/rules/confidence_policy.md`

## 目标

从通用菜名估算升级为“品牌模板 + 品类模板 + 配置修正”的估算体系。

## 本期范围

1. 首批高频品牌模板
2. 糖度、加料、配餐、规格修正规则
3. 品牌模板 -> 品类模板 -> 通用模板回退
4. 结果依据说明和置信度表达

## 验收

1. 高频品牌核心商品能走品牌模板
2. 配置变化会影响结果而不只是文案
3. 高低置信结果在返回中能明确区分
