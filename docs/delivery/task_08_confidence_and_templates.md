# Task 08: 模板、配置与置信度机制

- Status: Planned
- Owner: Product / Backend / Data
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Task 08 当前交付说明
- Depends On: `docs/rules/confidence_policy.md`

## 目标

补强高频品牌模板、配置规则和统一置信度表达。

## 本期范围

1. 扩充高频品牌模板覆盖
2. 补强冰量、糖度、奶基底、加料、份量变化等规则
3. 定义高/中/低置信度机制
4. 前端展示置信度与原因
5. 建立模板维护清单与版本记录

## 验收

1. 用户能看到高/中/低置信度及原因
2. 不同置信度触发不同 UI 和建议策略
3. 扩容模板不会显著破坏已有回归样本
