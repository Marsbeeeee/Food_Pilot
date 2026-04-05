# Workspace / Chat 模块

- Status: Active
- Owner: Product / Frontend / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Workspace 与 Chat 模块主文档
- Depends On: `docs/rules/decision_card_contract.md`, `docs/rules/confidence_policy.md`
- Related Docs: `docs/TASK2_DECISION_MODE_SPEC.md`, `docs/modules/estimate_api.md`

## 目标

作为用户主入口，承接会话、消息发送、模式切换、结果展示与结果操作。

## 会话接口

- `POST /chat/sessions`
- `GET /chat/sessions`
- `GET /chat/sessions/{session_id}`
- `PATCH /chat/sessions/{session_id}`
- `DELETE /chat/sessions/{session_id}`
- `POST /chat/messages`
- `POST /chat/sessions/{session_id}/messages`

## 当前会话行为

1. 支持新建空会话。
2. 支持在空会话中直接发送首条消息并自动生成会话。
3. 首条用户消息会用于更新默认标题。
4. 删除会话为永久删除，不做软删除。
5. 删除会话后，已保存的 Food Log 仍保留，但关联 `session_id` 被清空。

## 消息类型契约

对外消息类型统一为：

- `text`
- `meal_estimate`
- `meal_recommendation`

兼容历史值：

- `estimate_result` 统一映射为 `meal_estimate`

## 意图分流

当前以规则分流为主，不使用 LLM 分类器。

分流结果：

- `meal_estimate`
- `meal_recommendation`
- `text`
- `_clarification`

关键规则：

1. 估算优先级高于推荐。
2. 解释型追问优先走 `text`。
3. 标准化置信度不足时优先走澄清。
4. 对品牌未知、自制、做法不明对象，先追问关键缺失信息。

## Assistant 输出边界

1. Chat 内估算结果不会自动写入 Food Log。
2. 推荐结果不能直接保存到 Food Log。
3. 单菜品场景必须保持单外层卡，内部再展示组成项。
4. 多菜品场景允许一菜一卡。
5. 无法稳定判断对象层级时必须先澄清。

## 推荐安全约束

1. 当请求携带 `profileId` 时，推荐链路会读取 Profile。
2. 若命中过敏原或显式限制，返回安全拦截提示而不是原推荐。
3. 当前仍是关键词级约束，不是结构化配料理解。

## Decision Mode

第一阶段原则：

1. 复用现有统一输入区。
2. 增加模式切换，而不是新做独立页面。
3. `Decision Mode` 下优先把输入当作商品对象处理。
4. 下一阶段应优先返回统一 `decision_card`。
