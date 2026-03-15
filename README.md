# Food Pilot

Food Pilot 是一个以 `Assistant` 为主入口的营养问答与餐食分析 Web 应用。

当前 `Assistant v1` 只聚焦两类核心问题：推荐吃什么，以及这餐大概多少热量 / 营养。用户通过对话提出这两类问题，把值得保留的分析结果保存到 `Food Log`；再通过 `Profile` 让 Assistant 在之后的回复里持续参考同一个人的目标、偏好与限制。

主路径可以概括为：

`Assistant -> 保存到 Food Log -> 带着 Profile 上下文再次回来`

## 产品叙事

- `Assistant`：产品主入口。`v1` 先承担“推荐吃什么”和“这餐大概多少热量 / 营养”两类核心请求。
- `Food Log`：已保存分析结果的复用层，不是完整饮食日记。只有用户主动保存的内容才会进入这里。
- `Profile`：长期上下文层。用于告诉 Assistant“它是在为谁回答”。
- `Account / Session`：把聊天、Food Log 和 Profile 绑定到同一个账号，支持会话恢复。

## 当前已经实现

- 邮箱密码注册、登录、恢复会话、删除账户
- 聊天会话创建、续聊、重命名、删除
- 后端 AI 返回结构化餐食分析结果
- 从聊天中显式保存结果到 Food Log
- Food Log 的列表、详情、编辑、删除、恢复
- 从 Food Log 跳回来源聊天
- Profile 的创建、读取、更新
- 基于 SQLite 的本地持久化

## 当前不打算把它做成什么

- 不是完整的热量记账产品
- 不是自动记录所有饮食行为的日记系统
- 不是医疗产品
- 不是临床营养建议工具

`Food Log` 在当前产品定位里是“用户主动保存的高价值分析结果集合”，而不是“所有吃过的东西的流水账”。

## 技术栈

- 前端：React 19、TypeScript、Vite
- 后端：FastAPI
- AI：Gemini，仅从后端调用
- 存储：SQLite，数据库文件位于 `backend/database/foodpilot.db`

## 仓库结构

```text
backend/   FastAPI 服务、认证、聊天、Profile、Food Log、估算相关逻辑
frontend/  React 前端应用与界面壳层
docs/      产品说明与设计文档
```

## 快速开始

### 1. 准备环境

- Python 3
- Node.js
- npm
- 一个可用的 Gemini API Key

### 2. 配置环境变量

在仓库根目录创建 `.env` 文件：

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

可选项：

```env
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_TIMEOUT_SECONDS=20
GEMINI_SYSTEM_PROMPT=You are Food Pilot, a friendly and professional nutrition assistant.
```

认证相关配置当前走系统环境变量，未设置时会使用代码里的默认值：

```env
AUTH_SECRET=foodpilot-dev-secret
AUTH_TOKEN_EXPIRE_SECONDS=604800
PASSWORD_HASH_ITERATIONS=120000
```

需要注意：

- `GEMINI_*` 配置会自动回退读取以下文件：仓库根目录 `.env`、仓库根目录 `.env.local`、`frontend/.env.local`
- `AUTH_SECRET`、`AUTH_TOKEN_EXPIRE_SECONDS`、`PASSWORD_HASH_ITERATIONS` 当前不会自动从 `.env` 文件解析；如果你要覆盖默认值，请在系统环境变量里显式设置
- 如果没有 `GEMINI_API_KEY`，AI 分析与聊天回复不会正常工作

### 3. 启动后端

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

macOS / Linux：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

后端启动后会：

- 自动初始化 SQLite 数据库
- 监听 `http://localhost:8000`
- 提供健康检查 `GET /health`
- 提供 FastAPI 文档 `http://localhost:8000/docs`

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:3000`。

当前实现上的几个细节：

- 前端 API 模块目前直接请求 `http://localhost:8000`
- Vite 开发服务器端口固定为 `3000`
- 后端 CORS 当前允许 `http://localhost:3000`

## 核心页面

### Assistant

Assistant 是当前 UI 的主入口，支持：

- 创建新聊天
- 继续已有聊天
- 通过自然语言提出“推荐吃什么”或“这餐大概多少热量 / 营养”两类问题
- 接收结构化分析结果
- 从聊天里把某条结果保存到 Food Log

### Food Log

Food Log 只保存用户主动留下来的结果，支持：

- 查看已保存条目列表
- 查看单条结果详情
- 编辑已保存条目
- 软删除与恢复条目
- 当条目有来源聊天时跳回原始对话

后端列表接口当前支持这些筛选参数：

- `sessionId`
- `dateFrom`
- `dateTo`
- `limit`
- `meal`

### Profile

Profile 用于让 Assistant 的回复和 Food Log 中的已保存条目持续围绕同一个用户上下文展开。当前表单包括：

- 年龄、身高、体重、性别
- 活动水平、运动类型
- 目标、节奏、每日热量目标
- 饮食风格
- 过敏原与饮食避让项

### Account / Session

账号层当前负责：

- 注册与登录
- 应用启动时恢复当前会话
- 把 Profile、聊天和 Food Log 绑定到同一个用户
- 删除当前账号及其关联资料

## API 概览

当前后端主要路由包括：

### Health

- `GET /health`

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `DELETE /auth/me`

### Chat / Assistant

- `POST /chat/messages`
- `POST /chat/sessions`
- `GET /chat/sessions`
- `GET /chat/sessions/{session_id}`
- `PATCH /chat/sessions/{session_id}`
- `DELETE /chat/sessions/{session_id}`
- `POST /chat/sessions/{session_id}/messages`

### Estimate

- `POST /estimate`

说明：

- `/estimate` 当前是后端能力接口，不是产品主入口
- 成功调用 `/estimate` 或聊天分析后，不会自动写入 Food Log；保存必须是显式用户动作

### Profile

- `POST /profile`
- `GET /profile/me`
- `GET /profile/{profile_id}`
- `PUT /profile/{profile_id}`

### Food Log

- `GET /food-logs`
- `GET /food-logs/{food_log_id}`
- `POST /food-logs`
- `PATCH /food-logs/{food_log_id}`
- `POST /food-logs/from-estimate`
- `POST /food-logs/{food_log_id}/restore`
- `DELETE /food-logs/{food_log_id}`

## 开发命令

前端构建：

```bash
cd frontend
npm run build
```

前端测试：

```bash
cd frontend
npm test
```

后端测试：

```bash
python -m unittest discover backend/tests
```

## 当前范围边界

当前代码仓库聚焦的是这条主链路：

- 与 Assistant 对话
- 把有价值的结果保存到 Food Log
- 通过 Profile 让之后的回复更个性化

当前 `Assistant v1` 只聚焦两个核心意图：

- 推荐吃什么
- 这餐大概多少热量 / 营养

以下能力暂不作为 `Assistant v1` 的正式交付范围：

- 闲聊
- 解释性追问
- 复杂饮食规划
- 多轮长期 coaching

`docs/PRODUCT_SPEC.md` 里提到的日 / 周洞察等更后续的能力，目前不应被当作“已经在界面里交付”的功能来理解。

## 参考文档

- 产品说明：`docs/PRODUCT_SPEC.md`

## 免责声明

Food Pilot 提供的是估算性质的营养信息，仅用于信息参考，不构成医疗建议、诊断或治疗方案。
