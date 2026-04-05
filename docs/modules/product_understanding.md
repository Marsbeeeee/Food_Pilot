# Product Understanding 模块

- Status: Planned
- Owner: Product / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为商品理解层主文档
- Related Docs: `docs/modules/decision_engine.md`, `docs/rules/confidence_policy.md`, `docs/delivery/task_03_product_understanding.md`

## 目标

把低结构化输入转成可计算、可归档、可复用的商品结构，并为后续估算、保存和分析提供稳定中间层。

## 主要职责

1. 识别品类、品牌、品牌商品和私有商品。
2. 识别规格、甜度、温度、加料、配餐和套餐结构。
3. 输出缺失字段与置信度。
4. 当对象不明确时，驱动澄清而不是直接产出伪确定结果。

## 最小标准化结构

- `category`
- `brand`
- `normalized_name`
- `product_scope`
- `size/spec`
- `addons`
- `sugar_level`
- `temperature`
- `combo_items`
- `quantity`

## 处理分支

1. 命中正式目录对象
2. 命中品类/品牌但未命中商品
3. 仅命中品类
4. 来源不明确但仍可估算
5. 品牌未知或自制，需要澄清后继续估算
