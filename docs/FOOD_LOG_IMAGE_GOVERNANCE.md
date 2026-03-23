# Food Log 图片来源治理规则

更新时间：2026-03-23

## 字段定位

| 字段 | 角色 | 是否必填 | 规则 |
| --- | --- | --- | --- |
| `image` | 主图片地址 | 条件必填 | 仅在有图片时填写；空字符串会被归一化为空值 |
| `imageSource` / `image_source` | 来源审计字段 | 默认补齐 | 有图片时必须落库；未传时按 `sourceType` 自动补齐 |
| `imageLicense` / `image_license` | 授权审计字段 | 默认补齐 | 有图片时必须落库；未传时默认 `user_owned` |

说明：
- 无图片时，`imageSource` 与 `imageLicense` 必须为空。
- 输出层（`response_model_exclude_none=True`）会在字段为空时自动隐藏图片相关字段。

## 允许值（规范化后）

### `imageSource`

- `estimate_api`
- `chat_message`
- `manual`
- `user_upload`
- `camera_capture`
- `gallery_upload`
- `third_party`
- `unknown`

兼容别名：
- `estimate` / `estimateapi` -> `estimate_api`
- `chat` / `chatmessage` -> `chat_message`
- `manual_entry` -> `manual`
- `upload` / `local_upload` -> `user_upload`
- `camera` -> `camera_capture`
- `gallery` -> `gallery_upload`
- `thirdparty` -> `third_party`

### `imageLicense`

- `user_owned`
- `licensed`
- `cc0`
- `cc_by`
- `cc_by_sa`
- `public_domain`
- `unknown`

兼容别名：
- `owned` / `user` -> `user_owned`
- `copyright` / `copyrighted` -> `licensed`
- `publicdomain` -> `public_domain`

## 保存行为

### 新增（`save_food_log` / `create_food_log` / `from-estimate`）

- `image` 有值：
  - `imageSource` 缺失 -> 使用 `sourceType`
  - `imageLicense` 缺失 -> 使用 `user_owned`
  - `imageSource` 与 `imageLicense` 会做小写+下划线规范化与枚举校验
- `image` 为空：
  - 若仍传 `imageSource` 或 `imageLicense` -> 拒绝保存（400）

### 更新（`patch_food_log_entry`）

- 仅更新非图片字段：图片三字段保持原样
- 更新图片但未显式传来源/授权：
  - `imageSource` 按 `sourceType` 补齐
  - `imageLicense` 默认 `user_owned`
- 将 `image` 设为空字符串：视为清空图片，同时清空来源与授权

## 兼容性策略

- 不新增数据库列，不做重迁移，保持现有 `food_logs.image/image_source/image_license` 结构。
- 规则收敛在 service 层，避免不同 API 入口出现不一致默认值。
