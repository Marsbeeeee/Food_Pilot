# 当前交付路线

- Status: Active
- Owner: Product
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为当前阶段交付计划主文档
- Related Docs: `docs/product/roadmap.md`

## 当前目标

把 FoodPilot 从“以聊天为主入口的营养助手”升级为“面向点单场景的 AI 饮食决策助手”。

## 当前主链路

`输入商品信息 -> 解析商品结构 -> 估算营养与置信度 -> 输出推荐等级/风险/建议 -> 用户决定是否保存或继续比较`

## 当前设计原则

1. 优先复用现有 Chat / Estimate / Profile / Food Log / Insights 能力。
2. 先做标题/描述输入到决策输出的最小闭环。
3. 所有新能力必须有结构化输出契约。
4. 优先建设目录结构、商品映射和私有补充能力。

## 任务顺序

1. Task 1：统一决策卡片契约
2. Task 2：点单场景输入 MVP
3. Task 3：商品理解层与目录 V1
4. Task 4：品牌感知估算层 V1
5. Task 5：个体化决策层 V1
6. Task 6：决策工作台前端 V1
7. Task 7：截图识别与 OCR
8. Task 8：模板、配置与置信度机制
9. Task 9：比较、保存与长期链路
10. Task 10：评估与运营机制
