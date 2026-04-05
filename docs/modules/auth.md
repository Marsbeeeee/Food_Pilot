# Auth 模块

- Status: Active
- Owner: Backend / Frontend
- Last Updated: 2026-04-05
- Source Of Truth: 本文档为认证模块主文档
- Related Docs: `docs/system/system_overview.md`

## 目标

提供账号注册、登录、会话恢复与账号删除能力。

## 接口

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `DELETE /auth/me`

## 当前约束

1. 注册需要合法邮箱、非空 `displayName`、至少 8 位密码。
2. 使用 Bearer Token。
3. Token 为 HMAC JWT，包含 `sub / iat / exp`。
4. 前端会本地持久化 token 与当前用户信息。
5. 删除账号后，Profile、Chat、Food Log、Insights 等用户数据随外键级联删除。
