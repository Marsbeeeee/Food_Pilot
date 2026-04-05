# Task 02: 点单场景输入 MVP

- Status: Planned
- Owner: Product / Frontend / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Task 02 当前交付说明
- Depends On: `docs/TASK2_DECISION_MODE_SPEC.md`

## 目标

在现有 `Workspace` 主输入区上，以最小 UI 成本加入点单决策模式。

## 本期范围

1. 复用统一输入框
2. 增加模式切换入口
3. 允许商品标题、商品描述、品牌+商品名输入
4. 请求体支持 `mode` 等元信息
5. 明确异常分支

## 验收

1. 标题和描述都能稳定触发决策链路
2. 输入异常时有清晰提示
3. 点单入口以模式切换形式融入现有输入框
