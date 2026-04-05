# Food Log 模块

- Status: Active
- Owner: Product / Backend / Frontend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Food Log 模块主文档
- Depends On: `docs/rules/container_data_model.md`, `docs/rules/image_governance.md`
- Related Docs: `docs/system/data_lifecycle.md`, `docs/modules/image_assets_and_review.md`

## 目标

Food Log 是“显式保存的结果库”，不是自动记录所有饮食行为的流水账。

下一阶段目标是让它从平铺条目列表升级为与分层商品目录和容器语义对齐的结构化记录层。

## 接口

- `GET /food-logs`
- `GET /food-logs/{food_log_id}`
- `POST /food-logs`
- `POST /food-logs/from-estimate`
- `PATCH /food-logs/{food_log_id}`
- `DELETE /food-logs/{food_log_id}`
- `POST /food-logs/{food_log_id}/restore`

## 支持来源

- `chat_message`
- `estimate_api`
- `manual`

## 保存规则

1. 只有用户主动保存时才创建 Food Log。
2. `chat_message` 来源必须带 `session_id`。
3. Chat 只能保存结构化估算结果。
4. 文本回复与推荐回复不能直接保存。
5. `/estimate` 成功响应也不会自动保存。

## 下一阶段归档要求

1. 可保存卡片必须带分类标签和归档目标。
2. 保存动作不只保存标题和热量，还要保存目录对象语义。
3. 套餐子项需要保留 `item_role` 与所属关系。
4. 来源不明确但可估算的对象应允许进入未明确来源容器。
5. 收藏动作与保存动作必须分离。

## 幂等与去重

1. 支持 `idempotencyKey`。
2. 数据库对 `(user_id, idempotency_key)` 建唯一索引。
3. 命中已删除记录时，应先恢复再更新。

## 编辑与生命周期

1. 删除为软删除。
2. 支持恢复。
3. 前端允许编辑食材克重，并按比例重算展示营养值。
4. 列表默认只返回 `active` 条目。
