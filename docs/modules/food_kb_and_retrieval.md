# 中文食物知识库与检索模块

- Status: Active
- Owner: Backend / Data
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为食物知识库、检索增强与质量基线主文档
- Related Docs: `docs/food_kb_task2/`, `docs/rules/test_baseline.md`

## 目标

为中文食物理解、估算与引用透传提供版本化数据集、检索增强和固定质量基线。

## 当前状态

1. 已有版本化离线数据集。
2. 已支持规则检索与引用透传。
3. 已建立固定评估集和质量基线。
4. 当前仍属于离线规则增强阶段，不是持续运营型在线主数据库。

## 已完成进展

1. RAG prompt 已收敛为：`system rules -> profile context -> retrieved knowledge -> output contract`
2. 检索上下文已结构化输出冲突处理语义与引用字段。
3. 数据集已扩展到更高覆盖的中文真实场景。
4. 维护方式仍是“版本化离线数据集 + 固定评估集 + 检索质量基线”。
