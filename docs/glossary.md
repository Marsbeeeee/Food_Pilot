# FoodPilot 术语表

- Status: Draft
- Owner: Product
- Last Updated: 2026-04-05
- Source Of Truth: 本文档是跨文档术语统一入口
- Related Docs: `docs/system/core_objects.md`, `docs/rules/decision_card_contract.md`, `docs/rules/container_data_model.md`

## 目标

统一跨产品、设计、前端、后端、测试文档中的核心术语，避免同一对象被多种叫法重复定义。

## 核心术语

### `Workspace`

主工作区。当前承接 Chat 主入口，后续同时承接点单决策模式、截图解析等场景输入。

### `Decision Mode`

`Workspace` 输入区的一种模式。用户不是在提自然语言问句，而是在提交商品标题、商品描述或套餐文本，要求系统进入商品理解和决策链路。

### `Decision Card`

统一的结果承载对象。它不是单纯的聊天文本，也不是单纯的估算结果，而是用于承载商品结构、估算、置信度、推荐等级、风险标签、建议和保存路由信息的结构化卡片。

### `Product Structure`

商品理解层输出的标准化商品结构，包括品类、品牌、商品名、规格、加料、甜度、套餐子项等。

### `Container`

保存容器。用于组织 Food Log、收藏夹或其他记录载体。容器不是分析对象。

### `Unknown Source Container`

未明确来源容器。用于承接“可估算、可保存、但暂时无法稳定挂靠正式目录”的对象。

### `Analysis Eligible`

分析准入标记。表示对象是否满足进入 Insights 分析链路的条件。它和“是否可保存”不是同一件事。

### `Clarification`

澄清态。输入不足、标准化置信度不足或对象层级不清时，系统先追问关键缺失信息，而不是直接输出伪确定结果。
