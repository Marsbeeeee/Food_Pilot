# Decision Card 契约

- Status: Draft
- Owner: Product / Frontend / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为统一决策卡片结构主文档
- Depends On: `docs/system/core_objects.md`
- Related Docs: `docs/modules/workspace_chat.md`, `docs/modules/estimate_api.md`, `docs/modules/decision_engine.md`

## 目标

统一 Chat、Estimate、前端结果容器与保存动作的结果对象，避免不同入口返回不同格式。

## 卡片必须承载的信息

1. 原始输入摘要
2. 标准化商品结构
3. 分类标签
4. 营养估算结果
5. 置信度
6. 推荐等级
7. 风险标签
8. 个体适配说明
9. 调整建议
10. 替代建议
11. 是否需要澄清
12. 保存去向与分析资格

## 最小字段建议

- `inputSummary`
- `normalizedProduct`
- `categoryId / categoryName`
- `brandId / brandName`
- `productId / productName`
- `productScope`
- `itemRole`
- `nutritionEstimate`
- `confidenceLevel`
- `recommendationLevel`
- `riskTags`
- `adaptationNote`
- `adjustments`
- `alternatives`
- `needsClarification`
- `saveContainerKey`
- `containerType`
- `analysisEligible`

## 契约原则

1. 低置信或输入不足时，应通过结构化字段进入澄清态。
2. 字段不仅服务展示，也要服务保存、收藏和分析动作。
3. `analysis_eligible` 必须区分“可保存”和“可进入分析”。
4. 新入口应复用此契约，不另造结果对象。
