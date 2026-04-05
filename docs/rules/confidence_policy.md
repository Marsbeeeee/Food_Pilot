# 置信度与澄清策略

- Status: Draft
- Owner: Product / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为结果置信度和澄清触发规则主文档
- Related Docs: `docs/modules/workspace_chat.md`, `docs/modules/product_understanding.md`, `docs/modules/decision_engine.md`

## 目标

明确系统在信息不足、对象不清和模板回退场景下如何降级、澄清和表达置信度。

## 置信度分层

1. 高置信：品牌模板命中且规格明确
2. 中置信：品类模板命中，但局部配置缺失
3. 低置信：仅能走通用模板回退，或对象层级、套餐信息、关键做法不明确

## 澄清触发场景

1. 标准菜品映射置信度不足
2. 品牌未知且对结果影响大
3. 套餐或复合菜层级不清
4. 自制菜或做法差异明显
5. 份量、甜度、加料、浇头缺失

## 表达原则

1. 低置信不等于拒绝服务。
2. 低置信可估算时，必须显示原因与回退依据。
3. 不能把低置信结果包装成高确定结论。
4. 澄清问题应具体，不用空泛表达。
