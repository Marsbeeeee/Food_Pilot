# Decision Engine 模块

- Status: Planned
- Owner: Product / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为决策层主文档
- Depends On: `docs/modules/product_understanding.md`, `docs/modules/profile.md`
- Related Docs: `docs/rules/decision_card_contract.md`, `docs/delivery/task_01_decision_card.md`, `docs/delivery/task_04_brand_estimation.md`, `docs/delivery/task_05_personalized_decision.md`

## 目标

把“商品是什么”和“营养大概多少”进一步升级为“对当前用户是否值得点、风险在哪、怎么改更合理”。

## 主要职责

1. 承接商品理解层的标准化对象。
2. 承接估算层的营养与置信度。
3. 结合 Profile 输出推荐等级、风险标签、适配说明与建议。
4. 统一返回决策卡片，而不是散落在多个接口中的自由文本。

## 组成能力

1. 品牌感知估算
2. 配置修正规则
3. 风险标签体系
4. 推荐等级体系
5. 替代和调整建议
6. 节奏友好说明
