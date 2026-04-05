# FoodPilot 前后端交互契约

- Status: Draft
- Owner: Product / Frontend / Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为跨模块前后端行为字段和请求/响应角色定义
- Related Docs: `docs/modules/workspace_chat.md`, `docs/modules/estimate_api.md`, `docs/rules/decision_card_contract.md`

## 目标

统一前端状态驱动字段和后端结构化输出字段，避免“接口能返回，但前端不知道怎么用”。

## 入口请求契约

### 普通对话

```json
{
  "message": "今天晚饭推荐什么",
  "profileId": 123
}
```

### 点单决策

```json
{
  "message": "霸王茶姬 伯牙绝弦 大杯 三分糖",
  "mode": "decision",
  "profileId": 123
}
```

未来可扩展为：

```json
{
  "mode": "decision",
  "title": "霸王茶姬 伯牙绝弦 大杯 三分糖",
  "description": "",
  "sourcePlatform": "taobao_flash_buy",
  "profileId": 123
}
```

## 前端必须依赖的驱动字段

1. `needs_clarification`
2. `confidence_level`
3. `container_type`
4. `save_container_key`
5. `analysis_eligible`
6. `item_role`
7. `product_scope`

## 行为原则

1. 这些字段不是装饰字段，而是动作字段。
2. 前端不能自行猜测保存去向，应以结构化字段为准。
3. 后端不应只返回自然语言说明，必须返回支持 UI 和动作的稳定字段。
