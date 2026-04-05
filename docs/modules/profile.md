# Profile 模块

- Status: Active
- Owner: Product / Frontend / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Profile 模块主文档
- Related Docs: `docs/modules/workspace_chat.md`, `docs/modules/decision_engine.md`

## 目标

提供个体化目标、限制和热量预算，为推荐、安全约束和决策解释提供上下文。

## 接口

- `POST /profile`
- `GET /profile/me`
- `GET /profile/{profile_id}`
- `PUT /profile/{profile_id}`

## 当前字段

- `age`
- `height`
- `weight`
- `sex`
- `activityLevel`
- `exerciseType`
- `goal`
- `pace`
- `kcalTarget`
- `dietStyle`
- `allergies`

## 当前业务规则

1. 一个用户只允许一个 Profile。
2. 前端提供完整 Profile 页面。
3. 前端会自动计算推荐热量并回填 `kcalTarget`。
4. 前端会缓存当前 Profile，并把 `profileId` 传入 Chat / Estimate。
