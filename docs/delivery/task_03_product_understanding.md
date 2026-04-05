# Task 03: 商品理解层与分层商品目录 V1

- Status: Planned
- Owner: Product / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Task 03 当前交付说明
- Depends On: `docs/modules/product_understanding.md`

## 目标

把低结构化输入转成可计算、可归档、可复用的商品结构。

## 本期范围

1. 定义标准化商品结构
2. 建立品类 -> 品牌 -> 品牌商品目录
3. 建立品牌识别与规格/加料识别
4. 建立套餐拆分
5. 建立私有商品与未明确来源分支
6. 输出置信度和缺失字段

## 验收

1. 高频品牌和品类样本能稳定挂靠目录层级
2. 套餐能拆出主商品、饮品、配餐中的至少两个层次
3. 解析低置信时会明确暴露缺失点
