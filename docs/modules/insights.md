# Insights 模块

- Status: Active
- Owner: Product / Frontend / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Insights 模块主文档
- Depends On: `docs/rules/container_data_model.md`
- Related Docs: `docs/system/state_machine.md`, `docs/system/data_lifecycle.md`

## 目标

提供日/周维度的基础聚合与 AI 分析快照，帮助用户基于已保存对象做复盘。

## 接口

- `POST /api/insights/analyze`
- `GET /api/insights/history`
- `GET /api/insights/basket`
- `PUT /api/insights/basket`

## 当前模型

Insights 采用“左侧实时聚合 + 右侧 AI 快照”的双轨模型。

### 左侧

负责展示当前已选条目的实时聚合数据。

### 右侧

负责展示显式生成的 AI 分析快照。

## 分析准入规则

1. 只有最底层菜品/商品对象才能进入分析。
2. 容器不能整体进入分析。
3. 收藏夹不能整体进入分析。
4. 未明确来源容器不能整体进入分析。

## 历史快照规则

1. 同一 `user_id + mode + date_start + date_end` 唯一。
2. 同时间范围重新分析会覆盖旧结果。
3. 当前不是多版本并存历史系统。
