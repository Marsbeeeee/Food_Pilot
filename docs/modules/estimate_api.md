# Estimate API 模块

- Status: Active
- Owner: Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为独立 `/estimate` 能力层说明
- Related Docs: `docs/modules/workspace_chat.md`, `docs/rules/decision_card_contract.md`

## 目标

作为系统级结构化估算能力接口，为 Chat、Food Log 和未来快速录入能力提供原子估算支撑。

## 接口

- `POST /estimate`

## 产品定位

1. `/estimate` 是能力层，不是当前主入口。
2. Chat 是用户主入口，负责意图理解、澄清和结果组织。
3. `/estimate` 负责单次结构化估算计算。

## 与 Chat 的关系

1. Chat 命中估算意图时，应复用统一估算链路，而不是发展独立估算逻辑。
2. 低置信时先由 Chat 发起澄清，再进入估算。
3. 对品牌未知或自制对象，应优先走品类模板或通用模板，而不是直接中断。

## 当前请求与返回

请求支持：

- `query`
- `clientRequestId`
- `profileId`
- `sessionId`

返回结构包含：

- `success`
- `data`
- `error`
- `clientRequestId`
- `foodLogId`
- `saveStatus`
