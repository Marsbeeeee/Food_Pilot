# Task 07: 截图识别与 OCR 入口

- Status: Planned
- Owner: Product / Frontend / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Task 07 当前交付说明
- Depends On: `docs/modules/product_understanding.md`

## 目标

在标题/描述输入稳定后，增加真实平台截图解析能力。

## 本期范围

1. 设计上传入口与限制
2. 定义 OCR 中间结构
3. 增加人工确认步骤
4. 明确失败和噪声场景
5. 复用商品理解层

## 验收

1. 截图上传后至少能提取主体文本并进入确认流程
2. OCR 低质量时会要求确认
3. 文本入口和截图入口汇聚到同一种标准化结构
