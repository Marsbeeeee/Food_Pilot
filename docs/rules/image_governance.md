# Food Log 图片治理规则

- Status: Active
- Owner: Backend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为 Food Log 图片来源与授权治理主文档
- Related Docs: `docs/modules/food_log.md`, `docs/modules/image_assets_and_review.md`, `docs/FOOD_LOG_IMAGE_GOVERNANCE.md`

## 目标

规范图片主字段、来源审计字段与授权字段的默认补齐、校验和兼容策略。

## 字段

| 字段 | 角色 | 规则 |
| --- | --- | --- |
| `image` | 主图片地址 | 有图片时填写 |
| `imageSource` | 来源审计 | 有图时必须落库；未传时按 `sourceType` 补齐 |
| `imageLicense` | 授权审计 | 有图时必须落库；未传时默认 `user_owned` |

## 基本规则

1. 无图片时，`imageSource` 和 `imageLicense` 必须为空。
2. 有图片时，来源和授权会做规范化与枚举校验。
3. 更新图片时，若未显式传来源/授权，则补齐默认值。
4. 将 `image` 清空时，应同步清空来源和授权。
