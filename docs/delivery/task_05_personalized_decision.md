# Task 05: 个体化决策层与建议层 V1

- Status: Planned
- Owner: Product / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Task 05 当前交付说明
- Depends On: `docs/modules/decision_engine.md`, `docs/modules/profile.md`

## 目标

让系统从“告诉你热量”升级为“告诉你对你是否值得点、风险在哪、怎么改更合理”。

## 本期范围

1. 整理 Profile 上下文
2. 设计推荐等级规则
3. 设计风险标签体系
4. 设计改配与替代建议
5. 增加节奏友好说明

## 验收

1. 同一商品面对不同 Profile 时结论有合理差异
2. 风险标签与估算和规则一致
3. 系统能给出“允许但有边界”的建议
