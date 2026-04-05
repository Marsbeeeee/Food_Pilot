# FoodPilot 数据生命周期

- Status: Draft
- Owner: Product / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为结果对象从输入到沉淀的生命周期规则
- Related Docs: `docs/system/core_objects.md`, `docs/modules/food_log.md`, `docs/modules/insights.md`, `docs/rules/container_data_model.md`

## 目标

定义对象从临时结果到正式记录、再到分析输入的完整路径。

## 生命周期主线

`raw_input -> normalized_input -> product_structure -> decision_card -> food_log_entry / favorite_item -> analysis_item -> insights_snapshot`

## Chat 结果生命周期

1. 用户提交消息或商品输入。
2. 系统返回结构化结果。
3. 结果默认只存在于会话上下文中。
4. 除非用户显式保存，否则不会自动进入 Food Log。

## 保存生命周期

1. 用户点击保存。
2. 系统根据 `save_target` 判断容器类型和归档目标。
3. 保存成功后生成或更新 `food_log_entry`。
4. 若命中幂等键且历史记录已软删除，则恢复并更新。

## 分析生命周期

1. 只有满足最底层对象条件的条目才可进入分析篮子。
2. 左侧实时聚合基于当前条目集合计算。
3. 右侧 AI 快照由显式分析动作触发并覆盖同时间范围旧结果。

## 会话删除影响

1. Chat 会话删除为永久删除。
2. 已保存 Food Log 不随会话删除而消失。
3. 与已删会话的关联应清空，前端展示 `Source Chat Deleted`。
