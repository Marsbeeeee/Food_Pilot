# Food Pilot 产品规格说明

## 文档信息

- 文档状态：已按当前仓库实现重整
- 更新时间：2026-03-20
- 事实来源：以后端路由、服务层、前端页面、数据库初始化脚本、测试基线为准
- 适用范围：`backend/`、`frontend/`、`docs/` 当前实现

---

## 1. 产品定位

Food Pilot 是一个以对话为主入口的营养助手。当前版本的核心价值不是“自动记全量饮食流水”，而是：

1. 用户通过 Chat 提问，获得餐食推荐或营养估算。
2. 用户将有价值的结果显式保存到 Food Log。
3. 用户基于保存结果进入 Insights 做日/周分析。
4. Profile 为推荐、估算和安全约束提供个性化上下文。

当前产品更接近：

`对话式营养助手 + 显式保存的结果库 + 基础饮食分析面板`

而不是：

- 自动饮食日记
- 医疗诊断工具
- 完整的多模态拍照识别产品

---

## 2. 当前信息架构

前端当前实际由四个一级视图组成：

- `WORKSPACE`：Chat 主工作区
- `EXPLORER`：Food Log 列表与详情
- `INSIGHTS`：复用 Explorer 内的分析视图
- `PROFILE`：个人档案

主链路为：

`注册/登录 -> Chat 提问 -> 获得推荐/估算 -> 显式保存到 Food Log -> 加入 Insights 分析篮子 -> 生成日/周分析 -> 回到 Chat 或 Profile 继续调整`

---

## 3. 当前版本模块状态

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| Auth | 已实现 | 注册、登录、会话恢复、删除当前账号均已接后端 |
| Chat / Assistant | 已实现 | 会话管理、消息发送、规则分流、推荐/估算/澄清已落地 |
| Food Log | 已实现 | 保存、查询、详情、编辑、软删除、恢复、来源回跳已落地 |
| Profile | 已实现 | 单用户单档案、热量目标计算、过敏与饮食风格已落地 |
| Insights | 已实现核心闭环 | 分析、历史快照、分析篮子后端同步已落地 |
| 独立 `/estimate` API | 已实现（系统能力层） | 作为结构化估算能力保留，不作为当前版本主入口 |
| 测试基线 | 已定义 | 发布门禁为后端测试 + 前端单测，E2E 作为条件性集成验证 |

---

## 4. 功能规格

### 4.1 Auth

后端接口：

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `DELETE /auth/me`

当前约束：

- 注册需要合法邮箱、非空 `displayName`、至少 8 位密码。
- 使用 Bearer Token。
- Token 为后端自签 HMAC JWT，包含 `sub / iat / exp`。
- 前端会将 token 与当前用户信息保存在本地。
- 删除账号后，数据库通过外键级联删除该用户相关 Profile、Chat、Food Log、Insights 数据。

### 4.2 Chat / Assistant

#### 4.2.1 会话能力

后端接口：

- `POST /chat/sessions`
- `GET /chat/sessions`
- `GET /chat/sessions/{session_id}`
- `PATCH /chat/sessions/{session_id}`
- `DELETE /chat/sessions/{session_id}`
- `POST /chat/messages`
- `POST /chat/sessions/{session_id}/messages`

当前行为：

- 支持新建空会话。
- 支持在空会话中直接发首条消息并自动生成会话。
- 首条用户消息会用于更新默认标题。
- 删除会话为永久删除，不做软删除。
- 删除会话后，Food Log 记录仍保留，但关联的 `session_id` 会被清空，前端展示为 `Source Chat Deleted`。

#### 4.2.2 消息类型契约

对外消息类型统一为：

- `text`
- `meal_estimate`
- `meal_recommendation`

兼容规则：

- 数据库内部仍可能存储历史值 `estimate_result`
- Router / Schema 层统一映射为 `meal_estimate`

#### 4.2.3 意图分流

当前实现是“规则分流”，不是 LLM 分类器。

分流结果：

- `meal_estimate`：命中“多少热量 / 多少蛋白质 / 营养怎么样 / 大概多少”等估算关键词
- `meal_recommendation`：命中“推荐 / 替代 / 选哪个 / 训练后吃什么 / 怎么优化”等推荐关键词
- `text`：命中解释、说明、区别、为什么等文本类关键词
- `_clarification`：输入模糊、像问题但又不像具体食物描述时，先返回澄清提问

补充说明：

- 估算优先级高于推荐。
- 解释型追问会优先走 `text`，避免把“为什么推荐这个”误判成新的推荐请求。
- 当前规则对高频中文问法已有回归测试覆盖，但复杂表述仍存在误分流风险。

#### 4.2.4 Assistant 输出边界

- Chat 内估算结果不会自动写入 Food Log。
- Chat 内推荐结果不能直接保存到 Food Log。
- 多食物估算时，消息 `payload.estimates[]` 会保留每个子估算块，前端可逐块展示。

#### 4.2.5 推荐安全约束

当前实现：

- 当请求携带 `profileId` 时，推荐链路会读取 Profile。
- 如果 Profile 中存在 `allergies`，系统会对推荐结果做关键词级过敏原拦截。
- 命中过敏原时，不返回原推荐，而返回“推荐已拦截”的安全提示。

当前边界：

- 这是关键词级拦截，不是结构化配料理解。

### 4.3 独立 Estimate API（系统能力层）

后端接口：

- `POST /estimate`

#### 4.3.1 产品定位

`/estimate` 是系统级的结构化营养估算能力接口，不作为当前版本的用户主入口。

其主要职责：

- 为 Chat 提供底层估算能力
- 为 Food Log 提供结构化数据来源
- 为未来快速录入、批量估算和外部接入提供能力基础

#### 4.3.2 与 Chat 的关系

- Chat 是用户主入口，负责意图理解、澄清和结果组织。
- `/estimate` 是原子能力层，仅负责单次估算计算。
- Chat 在命中 `meal_estimate` 时，应通过统一估算链路调用 `/estimate` 对应能力，而不是发展独立估算逻辑分支。

#### 4.3.3 当前入口策略

- 当前版本不提供独立 Estimate 页面或主按钮入口。
- 所有用户估算行为优先通过 Chat 触发。
- `/estimate` 仅作为内部能力和前端 client 保留。

#### 4.3.4 后续演进方向（非当前版本）

未来可能扩展为：

- Quick Add（无对话快速录入）
- 批量食物估算入口
- 第三方 API / 多端复用能力

#### 4.3.5 不做事项（当前阶段）

- 不作为 Chat 的替代入口
- 不提供与 Chat 重叠的推荐或解释能力
- 不在 UI 中形成与 Chat 并列的主功能模块

#### 4.3.6 请求与返回结构

请求支持：

- `query`
- `clientRequestId`
- `profileId`
- `sessionId`

返回结构包含：

- `success`
- `data`
- `error`
- `clientRequestId`
- `foodLogId`
- `saveStatus`

### 4.4 Food Log

#### 4.4.1 产品定位

Food Log 是“显式保存的结果库”，不是自动记录所有饮食行为的流水账。

#### 4.4.2 支持来源

当前支持三类来源：

- `chat_message`
- `estimate_api`
- `manual`

#### 4.4.3 保存规则

- 只有用户主动保存时，才创建 Food Log。
- `chat_message` 来源必须带 `session_id`。
- `chat_message` 只能保存结构化估算结果。
- 文本回复与推荐回复不能直接保存到 Food Log。
- `/estimate` 成功响应也不会自动保存，仍需显式调用保存接口。

#### 4.4.4 幂等与去重

- Food Log 支持 `idempotencyKey`。
- 数据库对 `(user_id, idempotency_key)` 建唯一索引。
- Chat 保存默认使用消息相关 key。
- 独立 estimate 保存默认使用 `estimate_api:{clientRequestId}`。
- 如果命中已删除记录，系统会先恢复再更新，而不是新建重复条目。

#### 4.4.5 列表与检索

后端接口：

- `GET /food-logs`
- `GET /food-logs/{food_log_id}`
- `POST /food-logs`
- `POST /food-logs/from-estimate`
- `PATCH /food-logs/{food_log_id}`
- `DELETE /food-logs/{food_log_id}`
- `POST /food-logs/{food_log_id}/restore`

当前列表过滤能力：

- `sessionId`
- `dateFrom`
- `dateTo`
- `query`
- `sort`
- `limit`

当前排序能力：

- `created_desc`
- `created_asc`

当前状态判断：

- “优化 Food Log 的检索与筛选能力”最轻量级部分已完成。
- 现阶段已从仅按 meal 过滤，升级为支持关键词查询与排序。
- 更复杂的多维筛选仍未进入当前实现。

#### 4.4.6 编辑与生命周期

- 删除为软删除。
- 支持恢复已删除条目。
- 前端允许编辑食材克重，并按比例重算热量和三大营养素展示。
- 列表默认只返回 `active` 条目。

#### 4.4.7 图片与元数据

Food Log 当前已支持：

- `image`
- `imageSource`
- `imageLicense`

当前行为：

- 若有图片但未传来源，后端会给默认来源值。
- 若有图片但未传授权，后端默认 `user_owned`。
- 前端无图时展示占位图。
- 详情页展示来源与授权信息。

### 4.5 Profile

后端接口：

- `POST /profile`
- `GET /profile/me`
- `GET /profile/{profile_id}`
- `PUT /profile/{profile_id}`

当前字段：

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

当前业务规则：

- 一个用户只允许一个 Profile。
- 前端有完整 Profile 页面。
- 前端会根据年龄、身高、体重、性别、活动水平、目标、节奏自动计算推荐热量并回填 `kcalTarget`。
- 前端会本地缓存当前 Profile，并把 `profileId` 传入 Chat / Estimate。

Profile 对其他模块的影响：

- 推荐链路使用目标、热量目标、饮食风格、过敏原和活动信息。
- 估算链路会把 Profile 作为建议文案上下文。
- 过敏原会参与推荐安全拦截。

### 4.6 Insights

后端接口：

- `POST /api/insights/analyze`
- `GET /api/insights/history`
- `GET /api/insights/basket`
- `PUT /api/insights/basket`

#### 4.6.1 当前模型

Insights 当前已经从“临时实时分析”调整为“历史快照优先”的模型。

核心原则：

- 分析结果是显式生成的 snapshot。
- Food Log 后续发生变化时，不会自动重算已有分析。
- 用户需要通过“生成 AI 分析 / 重新分析”主动生成新结果。
- 历史结果优先于页面初始化时的实时分析。

#### 4.6.2 分析维度

当前支持：

- `day`
- `week`

分析输入：

- `mode`
- `dateRange`
- `selectedLogIds`（可选）
- `cacheKey`（前端可传）

分析输出：

- `aggregation`：总热量、蛋白、碳水、脂肪、比例、条目数
- `entries`：参与分析的简要条目
- `ai`：`summary / risks / actions`

#### 4.6.3 历史快照与唯一性

持久化层当前规则：

- `insights_analysis` 以 `user_id + mode + date_start + date_end` 唯一。
- 同一时间范围下重新分析，会覆盖旧结果。
- `selectedLogIds` 会被保存，但不会形成同一时间范围下的多版本并存。

这意味着：

- 当前版本的产品语义是“每个时间范围保留最新分析快照”。
- 它不是“同一天/同一周可保存多套筛选版本”的历史版本系统。

#### 4.6.4 页面加载逻辑

当前前端行为：

1. 先读取 `GET /api/insights/history`
2. 若当前时间范围已有历史结果，则直接展示
3. 若没有历史结果，则展示空状态并提供“生成 AI 分析”入口
4. 分析成功后更新本地缓存，并作为该时间范围的最新快照

#### 4.6.5 分析篮子同步

当前实现已支持分析篮子后端同步：

- 前端本地仍保留 basket 状态，保证交互即时性
- 同时通过 `/api/insights/basket` 做账号级同步
- 换设备或重新登录后，可恢复已同步的 basket 项

当前边界：

- basket 是“待分析条目选择状态”，不是正式分析历史
- 它没有版本比较或多人协作语义

#### 4.6.6 周分析展示状态

当前周分析已经具备日/周双模式、历史快照和 AI 文本输出能力，但仍不是完整的趋势分析产品。

现阶段更接近：

- 基础周视图
- 基础聚合结果
- AI 周期总结

尚未形成更强的趋势洞察能力，例如：

- 更长周期对比
- 多版本对比
- 明确的过期标记
- 结构化趋势结论

---

## 5. 技术与工程现状

### 5.1 技术栈

- 前端：React 19 + TypeScript + Vite
- 后端：FastAPI + SQLite
- AI 调用：后端统一发起
- 认证：Bearer Token + HMAC JWT

### 5.2 AI 配置现状

当前后端支持两类配置：

- Gemini 风格配置
- DashScope / Qwen 的 OpenAI 兼容配置

本仓库文档和 `.env.example` 的主推荐路径更偏向：

- `DASHSCOPE_API_KEY`
- `AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `AI_MODEL=qwen-plus`

### 5.3 数据库约束

当前数据库关键约束：

- `users.email` 唯一
- `profiles.user_id` 唯一，保证单用户单档案
- `food_logs(user_id, idempotency_key)` 唯一
- `insights_analysis(user_id, mode, date_start, date_end)` 唯一
- `chat_sessions / messages / food_logs / insights_*` 都与 `users` 存在明确外键关系

### 5.4 测试基线

当前 `docs/TEST_BASELINE.md` 定义的默认发布门禁为：

1. `python -m pytest backend/tests`
2. `cd frontend && npm test`

补充说明：

- Playwright E2E 存在，但不是默认强制门禁。
- 是否执行 E2E 取决于 AI key 环境。

---

## 6. 当前边界与已知限制

1. Chat 意图分流仍是规则驱动，复杂中文表达仍可能误判。
2. 推荐安全拦截仍是关键词级，不是结构化配料识别。
3. Chat 和 `/estimate` 的成功结果都不会自动写入 Food Log。
4. 独立 `/estimate` API 已实现，但没有正式主 UI 入口。
5. Insights 只保留同一时间范围下的最新快照，不保留多版本并存历史。
6. Food Log 已有基础检索与排序，但还不是完整的可组合高级筛选系统。
7. 图片能力当前只体现在 Food Log 字段与展示层，没有进入主上传识别流程。
8. 当前项目没有中文食物知识库 / RAG。

---

## 7. 当前版本对外描述建议

建议对内对外统一描述为：

> Food Pilot 当前是一款以聊天为主入口的营养助手。用户登录后可在 Chat 中获取餐食推荐或营养估算，把值得保留的结果显式保存到 Food Log，并在 Insights 中做日/周分析。Profile 用于个性化与过敏约束。当前核心闭环已成立，重点优化方向集中在意图分流准确率、Insights 趋势表达、独立 estimate 路径定位和更强的中文食物知识支持。

---

## 8. 下一阶段行动计划

任务 1（已完成）：提升 Chat 意图分流准确率

结论（2026-03-20）：

- 已复盘并优化推荐、估算、普通文本、澄清提问之间的判定逻辑。
- 已补充典型误判样本回归测试，优先覆盖比较句、替代问法、解释型追问和估算问法变体。
- 在保持消息契约与主流程兼容的前提下，修正了已知高频误判。

任务 2（已完成）：明确独立 `/estimate` API 的产品定位

结论（2026-03-20）：

- `/estimate` 定位为系统能力，不是当前版本用户主入口。
- Chat 作为统一用户入口；`/estimate` 负责原子化估算能力。
- 当前版本不新增独立 Estimate 主入口页面；保留 API 与前端 client 作为内部能力。
- 后续如扩展 Quick Add、批量估算、第三方复用，基于该能力层演进。

任务 3（已完成）：增强 Insights 周分析的趋势表达与可解释性

结论（2026-03-20）：

- 已在不改动 `/api/insights/analyze` 接口与主数据结构前提下，增强周分析的趋势表达，新增周趋势、波动、周期特征与一周热量轨迹展示。
- 已复用既有聚合结果、历史快照优先与重新分析流程，保持空状态、历史命中、重新分析等核心路径行为一致。
- 已补充周分析展示逻辑与模式状态切换相关前端测试，并补充后端周模式提示词趋势上下文测试。
- 周模式相较日模式具备明确区分：日模式强调单日摄入差距，周模式强调趋势变化与工作日/周末节律。

任务 4（已完成）：继续补强 Food Log 的检索与筛选能力

结论（2026-03-21）：

- 已将 Food Log 检索能力从“基础列表浏览”推进为“以搜索与筛选为中心”的使用路径，保留既有页面结构与交互心智。
- 已稳定支持关键词检索、排序切换与时间范围筛选的组合使用，能够覆盖高频历史条目定位场景。
- 已在轻量交互前提下补强筛选效率，避免引入重型筛选面板，保持上手成本可控。
- 已将筛选能力定位为“可复用结果库”导向，弱化餐次维度在检索流程中的优先级。
- Food Log 的保存、编辑、恢复与来源回跳主流程保持兼容，未引入行为回归。
- 当前能力已满足阶段目标；后续扩展方向聚焦数值范围与来源聚合筛选等增强项。

任务 5：为 Insights 增加更明确的结果时效提示

背景：
当前 Insights 使用快照模型，Food Log 变化后不会自动更新已有分析结果。虽然这是明确的产品设计，但用户仍可能把结果误解为实时状态。

要求：
- 梳理当前 Insights 页面中历史结果、重新分析和 Food Log 变更之间的关系
- 增加更明确的“数据可能已变化，请重新分析”提示
- 在不改变快照模型的前提下，优化时效性反馈与用户预期管理
- 保持历史结果优先的页面加载逻辑不变
- 补充相关前端状态与展示测试

验收标准：
- 用户能明确理解 Insights 结果是快照而不是实时同步结果
- 页面不会因为提示增强而改变现有分析数据来源逻辑
- 历史结果、空状态和重新分析流程保持一致
- 相关测试通过

任务 6：规范图片来源治理与审计字段

背景：
当前 Food Log 已支持 `image / imageSource / imageLicense`，但这些字段的治理规则仍偏轻量，后续如果图片使用增加，容易出现来源不清、授权信息不完整、审计维度不足的问题。

要求：
- 梳理当前图片字段、来源字段和默认值处理逻辑
- 明确哪些字段属于必填、默认补齐还是仅展示用途
- 规范图片来源、授权信息和关键元数据的记录规则
- 保持与现有 Food Log 数据结构兼容，避免不必要的大迁移
- 补充相关校验与测试

验收标准：
- 图片来源和授权信息的记录规则清晰且可落地
- 关键图片元数据具备稳定、一致的保存行为
- 不影响当前 Food Log 主链路
- 相关测试通过

任务 7：引入中文食物知识库 / RAG

背景：
当前系统不具备中文食物知识库或 RAG 能力，在中文食材、菜品和本地化营养知识覆盖上存在明显缺口，限制了估算质量、推荐质量和后续扩展空间。

要求：
- 明确中文食物知识库 / RAG 的目标场景和接入边界
- 评估数据来源、数据质量和知识更新机制
- 设计与现有推荐、估算或问答链路的集成方式
- 控制首期范围，优先覆盖高价值中文食物知识场景
- 补充针对知识检索与引用结果的验证方案

验收标准：
- 系统可在约定范围内使用中文食物知识完成检索增强
- 接入后不会破坏现有主链路稳定性
- 有可执行的验证方式评估知识覆盖和效果

任务 8：扩展更长周期的趋势分析能力

背景：
当前 Insights 主要支持日/周分析，缺少更长周期的趋势观察与反馈能力，难以支撑用户对阶段性饮食变化的复盘和长期模式观察。

要求：
- 梳理现有日/周分析的数据结构与可复用能力
- 设计更长周期趋势分析所需的聚合维度、展示方式和反馈内容
- 保证趋势分析建立在可解释的数据汇总基础上，而不是仅生成泛化文案
- 控制首期范围，优先覆盖最有价值的趋势指标
- 补充趋势计算与展示的测试或验证方案

验收标准：
- 用户可查看约定周期内的核心饮食趋势变化
- 趋势结果与底层聚合数据一致、可解释
- 不破坏现有日/周分析主链路
- 相关测试或验证通过

---

## 9. 结论

截至 2026-03-20，Food Pilot 已经不是纯 demo。

它已经具备：

- 真实账号体系
- 真实 Chat 会话与消息持久化
- 显式保存的 Food Log
- 可用的 Profile 个性化能力
- 历史快照优先的 Insights 分析闭环

当前最需要继续收敛的不是“再加多少页面”，而是：

- Chat 规则分流的稳定性
- Insights 的分析表达与状态模型
- 独立 estimate 路径与 Chat 统一链路的工程收敛
- 更可靠的中文食物知识支撑
