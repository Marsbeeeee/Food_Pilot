# FoodPilot 状态机

- Status: Draft
- Owner: Product / Frontend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为主链路状态与异常分支定义
- Related Docs: `docs/system/frontend_backend_contracts.md`, `docs/modules/workspace_chat.md`, `docs/modules/food_log.md`

## 目标

定义主链路上的关键状态，避免前端和后端对“当前处于什么状态”各自理解。

## 输入与结果状态

1. `idle`
2. `submitting`
3. `clarification_required`
4. `success_low_confidence`
5. `success_ready_to_save`
6. `success_not_analysis_eligible`
7. `error`

## 保存相关状态

1. `save_available`
2. `saving`
3. `save_succeeded`
4. `save_failed`

## Insights 相关状态

1. 左侧实时聚合应随篮子和条目变化即时更新。
2. 右侧 AI 快照只有显式触发时才更新。
3. 左右输入不一致时进入 `snapshot_stale` 提示态。

## 状态规则

1. `clarification_required` 不能伪装成成功态。
2. `save_available` 不代表 `analysis_eligible`。
3. `save_succeeded` 不意味着应自动刷新 AI 快照。
4. 低置信场景可继续，但 UI 必须与高置信成功态不同。
