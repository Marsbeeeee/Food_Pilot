# 标准菜品图片资产与审核模块

- Status: Active
- Owner: Backend / Admin Ops
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为标准菜品图片生成、审核、复用规则主文档
- Depends On: `docs/rules/image_governance.md`
- Related Docs: `docs/modules/food_log.md`

## 目标

为高置信命中标准菜品的记录提供统一、稳定、可复用的官方图，并通过审核链路保证质量与治理。

## 核心策略

1. 图像资产的粒度是 `standard_dish`，不是 `food_log`。
2. 同一道标准菜品复用同一张官方图。
3. AI 生成结果必须先进入审核队列，不能直接面向用户。
4. 图片补齐不阻塞 Food Log 主保存流程。

## 审核流程

1. 系统生成候选图。
2. 候选图进入后台审核队列。
3. 管理员查看、通过、拒绝或重生成。
4. 通过后写回官方图字段。
