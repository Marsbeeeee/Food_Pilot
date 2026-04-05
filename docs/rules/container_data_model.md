# 容器与分析对象规则

- Status: Active
- Owner: Product / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为容器体系、记录项与分析对象的主文档
- Related Docs: `docs/CONTAINER_DATA_MODEL_SPEC.md`, `docs/system/core_objects.md`, `docs/modules/food_log.md`, `docs/modules/insights.md`

## 目标

明确以下三层语义：

1. 哪些对象可以保存
2. 哪些对象可以收藏
3. 哪些对象可以进入分析

## 设计原则

1. 保存宽于分析。
2. 容器不等于分析对象。
3. 最底层对象才可分析。
4. 低置信不等于不可保存。
5. 数据模型需预留扩展位。

## 核心分层

1. 商品目录层
2. 保存容器层
3. 记录项层
4. 分析对象层

## 容器类型

1. 正式分类容器
2. 未明确来源容器
3. 收藏夹容器

## 规则

1. 记录项不是容器。
2. 一条记录项应绑定一个主容器。
3. 收藏建议通过单独关系表达，而不是复制记录。
4. 可进入 Insights 的对象必须是单个具体可食用对象，并有稳定营养快照。
