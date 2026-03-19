# Food Pilot Product Specification

## 文档信息

- 文档状态：已更新，基于当前仓库实现
- 更新时间：2026-03-19
- 代码基线：`main` 工作区当前内容
- 更新原则：以代码、路由、数据结构、前端实际可达交互为准；旧文档与实现冲突时，以本文件为准

---

## 1. 产品定位

Food Pilot 是一个以对话为主入口的饮食分析助手，当前版本的主链路是：

`注册/登录 -> Chat 中提问 -> 获得估算或推荐 -> 显式保存到 Food Log -> 在 Insights 做日/周分析 -> 回到 Profile 或 Chat 调整`

当前产品不是完整的饮食日记系统，也不是医疗诊断工具。它更接近“对话式营养助手 + 可复用结果库 + 基础分析面板”。

---

## 2. 当前版本总览

### 2.1 模块完成度

| 模块 | 当前状态 | 说明 |
| --- | --- | --- |
| Auth | 已实现 | 注册、登录、会话恢复、删除账号均已接入真实后端 |
| Chat / Assistant | 已实现 | 聊天会话管理、意图分流、AI 推荐/估算、澄清提问均已落地 |
| Food Log | 已实现 | 显式保存、编辑、软删除、恢复、来源回跳已落地 |
| Profile | 已实现 | 个人目标、饮食风格、过敏原、运动等字段可维护，并参与个性化 |
| Insights | 部分实现 | 后端分析与历史持久化已落地，但选择篮子与缓存策略仍有明显边界 |
| 独立 `/estimate` API | 后端已实现，前端未主用 | API 和前端 client 已存在，但主 UI 入口仍以 Chat 估算为主 |
| 工程化 / 测试 | 部分实现 | 有较多后端单测、前端单测和 Playwright E2E，但当前测试基线并非全绿 |

### 2.2 当前主链路是否可用

- 可用：账号登录后进入 `Chat / Food Log / Insights / Profile`
- 可用：在聊天中发送问题并获得估算或推荐结果
- 可用：从聊天估算结果显式保存到 Food Log
- 可用：从 Food Log 选择条目后进入 Insights 做分析
- 可用：Profile 数据会影响推荐和估算上下文

---

## 3. 用户可见功能规格

### 3.1 Auth

当前实现：

- `POST /auth/register` 注册账号
- `POST /auth/login` 登录账号
- `GET /auth/me` 恢复当前会话
- `DELETE /auth/me` 删除当前账号

行为约束：

- 注册要求邮箱合法、密码至少 8 位、`displayName` 非空
- 前端将 token 和当前用户信息保存在 `localStorage`
- 认证方式为 Bearer Token
- Token 为后端自签名 HMAC JWT，带 `sub / iat / exp`

数据生命周期：

- 数据库层对 `users -> profiles / chat_sessions / messages / food_logs / insights_analysis` 使用级联删除
- 产品层面，删除账号应清理该用户相关数据

### 3.2 Chat / Assistant

当前实现：

- 新建空聊天会话
- 获取聊天列表
- 获取单个聊天详情
- 重命名聊天
- 永久删除聊天
- 在新会话或已有会话中发送消息

消息类型契约：

- 对外统一为 `text`
- 对外统一为 `meal_estimate`
- 对外统一为 `meal_recommendation`

兼容行为：

- 数据库内部仍保留 `estimate_result`
- Router / Schema 层会统一映射为 `meal_estimate`

意图分流规则：

- `meal_recommendation`：关键词命中“推荐/替代/选哪个/训练后吃什么”等
- `meal_estimate`：关键词命中“多少热量/多少蛋白质/营养怎么样”等
- `text`：解释、补充说明、寒暄类输入
- `_clarification`：当输入模糊且不像具体食物描述时，先返回澄清提问

当前实现特征：

- 分流规则是关键词优先，不是 LLM 分类器
- 已实现“澄清提问”分支，不应再被视为未实现
- 真实回归测试中，意图分流仍存在误判样本，稳定性不是 100%

AI 输出行为：

- 推荐请求调用推荐链路，返回标题、说明、正文
- 估算请求调用估算链路，返回标题、置信度、描述、分项食材、总热量、建议
- 多食物估算时，消息 `payload.estimates[]` 会保留每个子估算块

显式边界：

- Chat 内的估算结果不会自动写入 Food Log
- Chat 内的推荐结果不能直接保存到 Food Log

### 3.3 Recommendation 安全约束

当前实现：

- 当请求携带 `profileId`，推荐链路会读取 Profile
- 若 Profile 中存在 `allergies`，推荐结果会做关键词级过敏原拦截
- 命中过敏原时，不返回原推荐，而是返回“推荐已拦截”的安全提示消息

当前边界：

- 拦截是字符串关键词级别，不是结构化配料理解

### 3.4 独立 Estimate API

当前实现：

- `POST /estimate` 已存在
- 请求支持 `query / clientRequestId / profileId / sessionId`
- 返回 `success / data / error / clientRequestId / foodLogId / saveStatus`

当前边界：

- 该 API 只返回估算结果，不自动保存 Food Log
- 前端存在 `src/api/estimate.ts` client
- 当前主 UI 没有独立 estimate 页面或按钮直接走这条 API；主链路仍是 Chat 中估算

### 3.5 Food Log

产品定位：

- Food Log 是“显式保存的可复用结果库”
- 不是自动记录全部饮食行为的流水账

当前实现：

- 列表查询
- 单条详情
- 保存
- 从独立 estimate 结果保存
- 编辑
- 软删除
- 恢复

支持来源：

- `estimate_api`
- `chat_message`
- `manual`

保存规则：

- 只有用户主动保存时才创建 Food Log
- `chat_message` 来源必须携带 `session_id`
- `chat_message` 只能保存结构化估算结果
- 文本回复与推荐回复不能直接保存到 Food Log

去重 / 幂等规则：

- Food Log 支持 `idempotencyKey`
- 数据库对 `(user_id, idempotency_key)` 做唯一约束
- Chat 保存按钮默认使用 `message.id::title` 作为幂等键
- 独立 estimate 保存默认使用 `estimate_api:{clientRequestId}`

编辑与删除规则：

- 删除为软删除，记录保留生命周期状态
- 支持恢复已删除条目
- 前端允许编辑食材克重，并按比例重算热量和三大营养素展示

来源关联：

- Food Log 条目可保留 `sessionId` 与 `sourceMessageId`
- 删除聊天后，Food Log 记录保留，但关联聊天会被解除
- 前端会把这种状态展示为 `Source Chat Deleted`

过滤能力：

- 后端列表支持 `sessionId / dateFrom / dateTo / meal / limit`
- 当前不支持按 `sourceType` 的高级筛选

图片与来源元数据：

- Food Log 已支持 `image / imageSource / imageLicense`
- 有图片但未传来源时，后端会给默认值
- 前端对无图场景提供占位图
- 前端在详情页会展示 `imageSource / imageLicense`

### 3.6 Profile

当前实现字段：

- `age`
- `height`
- `weight`
- `sex`
- `activityLevel`
- `exerciseType`
- `goal`
- `pace`
- `kcalTarget`
- `dietStyle`
- `allergies`

当前实现：

- `POST /profile` 创建
- `GET /profile/me` 获取当前用户 Profile
- `GET /profile/{profile_id}` 获取指定 Profile
- `PUT /profile/{profile_id}` 更新 Profile

业务规则：

- 一个用户只允许一个 Profile
- 前端有完整 Profile 页面
- 前端会根据年龄、身高、体重、性别、活动水平、目标、节奏自动计算推荐热量并回填 `kcalTarget`
- 前端将 `profileId` 本地缓存，后续作为个性化上下文传给 Chat

Profile 对其他模块的影响：

- 推荐链路使用目标、热量目标、饮食风格、过敏原、活动信息
- 估算链路会把 Profile 作为建议文案的上下文

### 3.7 Insights

当前实现：

- `POST /api/insights/analyze`
- `GET /api/insights/history`

分析输入：

- `mode`: `day | week`
- `selectedLogIds`: 可选
- `dateRange.start / dateRange.end`
- `cacheKey`: 可选

分析输出：

- `aggregation`
- `entries`
- `ai.summary`
- `ai.risks`
- `ai.actions`

后端分析能力：

- 根据 `selectedLogIds` 精确分析指定 Food Log
- 若未指定 `selectedLogIds`，按日期范围查询用户 Food Log
- 聚合总热量、总蛋白、总碳水、总脂肪、三大营养素比例、条目数
- 基于聚合结果和条目摘要调用 AI 生成总结、风险、行动建议

历史持久化：

- 若请求传入 `cacheKey`，分析结果会写入 `insights_analysis`
- 以 `(user_id, cache_key)` 做 upsert
- `GET /api/insights/history` 返回该用户最近历史记录

前端当前实现：

- Insights 视图复用 `Explorer` 页面中的 `AnalysisView`
- 支持按日和按周切换
- 支持从 Food Log 把条目加入分析篮子
- 分析篮子按 `userId + date` 保存在 `localStorage`
- 篮子保存的是条目快照，因此即使 Food Log 后续取消保存，分析篮子仍可保留该快照

当前重要边界：

- 分析篮子没有后端同步接口，换设备不会同步“待分析条目”
- 只有分析结果历史可以跨设备回看，分析篮子本身不行
- 前端缓存 key 目前只按 `mode + dateRange` 生成，不包含 `selectedLogIds`
- 这意味着同一天/同一周切换不同条目集合时，存在复用旧分析结果的风险
- 当前没有 `/api/insights/selection` 之类的后端选择同步接口

---

## 4. 数据与存储规格

### 4.1 主要数据表

- `users`
- `profiles`
- `chat_sessions`
- `messages`
- `food_logs`
- `insights_analysis`

### 4.2 关键数据约束

- `chat_sessions.title` 长度 1-120
- `messages` 只允许 `text / meal_estimate / meal_recommendation` 契约
- `food_logs.source_type` 只允许 `estimate_api / chat_message / manual`
- `food_logs.status` 只允许 `active / deleted`
- `food_logs.idempotency_key` 对单用户唯一
- `insights_analysis.mode` 只允许 `day / week`

### 4.3 本地存储

前端当前使用 `localStorage` 保存：

- `foodpilot.authToken`
- `foodpilot.authUser`
- `foodpilot.profileId`
- Insights 分析篮子（按用户、按日期）

---

## 5. API 范围

当前后端公开的核心接口：

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `DELETE /auth/me`
- `GET /chat/sessions`
- `POST /chat/sessions`
- `GET /chat/sessions/{session_id}`
- `PATCH /chat/sessions/{session_id}`
- `DELETE /chat/sessions/{session_id}`
- `POST /chat/messages`
- `POST /chat/sessions/{session_id}/messages`
- `POST /estimate`
- `GET /food-logs`
- `GET /food-logs/{food_log_id}`
- `POST /food-logs`
- `POST /food-logs/from-estimate`
- `PATCH /food-logs/{food_log_id}`
- `POST /food-logs/{food_log_id}/restore`
- `DELETE /food-logs/{food_log_id}`
- `POST /profile`
- `GET /profile/me`
- `GET /profile/{profile_id}`
- `PUT /profile/{profile_id}`
- `POST /api/insights/analyze`
- `GET /api/insights/history`

---

## 6. 非功能与工程状态

### 6.1 已具备的工程能力

- 前后端接口字段别名处理较完整，中间层已经兼容部分旧命名
- 后端有较系统的 `unittest` 覆盖认证、聊天、估算、Food Log、Profile、Insights
- 前端有 Node 原生测试，覆盖消息展示、Food Log 状态、导航逻辑等
- 前端有 Playwright E2E 脚本，目标覆盖注册/聊天/保存 Food Log/进入 Insights
- 前端 API 基地址支持 `VITE_API_BASE_URL`

### 6.2 当前验证结论

2026-03-19 本地验证结果：

- `frontend`: `npm.cmd test` 通过 `11/12`
- `frontend`: 当前有 1 个失败测试，属于 `workspaceMessagePresentation` 输出结构与测试期望不一致
- `backend`: 在仓库 `.venv` 下运行单测时，可见真实失败与环境问题并存，当前不是全绿基线

当前已观察到的问题类型：

- 部分后端测试依赖 `httpx`，当前 `.venv` 未安装
- 一部分后端测试因数据库路径使用相对路径，在特定工作目录下报 `unable to open database file`
- Chat intent routing 回归测试存在误判样本
- 部分测试断言与当前 schema/实现已发生漂移

因此，当前规格不应宣称“关键测试已稳定通过”。

---

## 7. 已知边界与风险

### 7.1 产品边界

- 不提供医疗诊断与治疗建议
- 不自动记录全部饮食行为
- 不具备图片识别上传主流程；图片目前只是 Food Log 条目字段
- 不具备中文食物知识库/RAG

### 7.2 当前实现风险

- Chat 意图分流依赖规则，复杂比较句和替代类句式仍可能误分流
- Insights 缓存 key 未包含 `selectedLogIds`，可能命中错误缓存
- Insights 选择篮子仍是本地状态，不是跨设备状态
- 独立 `/estimate` API 虽已实现，但主 UI 不走该路径，产品体验仍以 Chat 为中心
- 当前测试基线存在失败项，说明实现与测试、或实现与预期之间仍有漂移

---

## 8. 当前版本应如何描述

对外或对内描述当前产品时，建议使用以下口径：

> Food Pilot 当前是一个以聊天为入口的营养助手。用户可以登录后在 Chat 中提问，获取餐食推荐或营养估算；有价值的估算结果可显式保存到 Food Log；随后在 Insights 中做基础的日/周分析。Profile 已参与个性化和过敏原约束。核心链路已具备，但 Insights 的选择同步、缓存策略和整体工程稳定性仍需继续收敛。

---

## 9. 下一阶段优先事项

按当前实现状态，建议优先级如下：

### P0

- 修正 Insights 缓存 key，仅按日期缓存会导致结果复用错误
- 为 Insights 分析篮子提供后端同步能力
- 收敛当前失败测试，恢复可作为发布门禁的稳定基线

### P1

- 强化 Chat 意图分流，降低推荐/估算误判
- 为 Food Log 增加更强的筛选能力，如来源筛选
- 补齐独立 estimate 主流程是否继续保留的产品决策

### P2

- 接入中文食物知识库 / RAG
- 引入趋势分析与更长周期的饮食反馈
- 增强图片来源治理与更完整的数据审计

---

## 10. 冻结结论

截至 2026-03-19，Food Pilot 的真实状态可以归纳为：

- 它已经不是纯 demo，认证、聊天、Food Log、Profile、Insights 都有真实后端和前端入口
- 它的主路径已经成立，但仍是“可用的早期产品”，不是“流程完全收敛的稳定产品”
- 现阶段最需要更新的不是页面数量，而是 Insights 状态模型、规则分流准确率和测试基线可信度

