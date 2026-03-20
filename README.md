# Food Pilot

![Status](https://img.shields.io/badge/status-active%20development-ff8a65)
![Frontend](https://img.shields.io/badge/frontend-React%2019-61dafb)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![License](https://img.shields.io/badge/license-not%20specified-lightgrey)

Food Pilot 是一个以对话为主入口的营养助手应用。用户可以通过自然语言询问“吃什么更合适”或“这餐大概多少热量/营养”，将有价值结果保存到 `Food Log`，并进一步做日/周饮食分析。

---

## Table of Contents

- [Project Description](#project-description)
- [Core Features](#core-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Requirements / Prerequisites](#requirements--prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [API Quick Reference](#api-quick-reference)
- [Visuals / Demo](#visuals--demo)
- [Project Status](#project-status)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Support / Contact](#support--contact)
- [Acknowledgments](#acknowledgments)
- [License](#license)

---

## Project Description

**Purpose**

Food Pilot 解决“营养建议难落地、记录难复用”的问题：

1. 用自然语言问 AI（推荐 / 估算）
2. 将有价值结果保存为可复用条目（Food Log）
3. 结合 Profile（目标、过敏原、饮食风格）持续个性化
4. 进入 Insights 做进一步分析和调整

**Why Useful**

- 降低饮食管理门槛（无需复杂手工录入）
- 让分析结果可复用，而不是一次性聊天内容
- 通过过敏原硬约束提升推荐安全性

---

## Core Features

- 账号体系：注册 / 登录 / 会话恢复 / 删除账号
- Assistant 双核心意图：
  - `meal_recommendation`（推荐吃什么）
  - `meal_estimate`（这餐大概多少热量/营养）
- `/estimate` 能力层：系统级结构化估算接口（当前不作为独立用户主入口）
- Chat 会话管理：新建、续聊、重命名、删除
- Food Log：保存、详情、编辑、删除、恢复、回跳来源聊天
- Profile：目标、热量目标、饮食风格、过敏原等约束接入
- Insights（当前为进行中模块）：日分析流程基础能力

---

## Tech Stack

- **Frontend**: React 19 + TypeScript + Vite
- **Backend**: FastAPI + SQLite
- **AI**: Qwen-plus (backend-only call)
- **Auth**: Token-based session auth

---

## Project Structure

```text
backend/      FastAPI API, services, schemas, repositories, tests
frontend/     React app (Assistant / Food Log / Insights / Profile)
docs/         Product and setup documentation
```

---

## Requirements / Prerequisites

请先确保本机具备以下环境：

- Python 3.10+
- Node.js 18+
- npm 9+
- 可用的 Qwen API Key（阿里云 DashScope）
- 推荐系统：Windows 10+/macOS/Linux

> 说明：后端依赖来自 `requirements.txt`，前端依赖来自 `frontend/package.json`。

---

## Installation

### 1) Clone project

```bash
git clone <your-repo-url>
cd Food_Pilot
```

### 2) Configure environment variables

在项目根目录创建 `.env`：

```env
DASHSCOPE_API_KEY=sk-xxx
AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL=qwen-plus
```

可选认证配置（不填则走默认）：

```env
AUTH_SECRET=foodpilot-dev-secret
AUTH_TOKEN_EXPIRE_SECONDS=604800
PASSWORD_HASH_ITERATIONS=120000
```

### 3) Setup and run backend

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**macOS / Linux**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

If you will run tests locally:

```bash
pip install -r requirements-dev.txt
```

### 4) Setup and run frontend

```bash
cd frontend
npm install
npm run dev
```

默认地址：

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## Usage

### Typical user flow

1. 注册/登录
2. 在 Assistant 输入问题：
   - “晚饭怎么吃更适合减脂？”
   - “一碗牛肉面大概多少热量？”
3. 对估算结果点击保存到 Food Log
4. 在 Food Log 中复用、编辑、回跳聊天
5. 进入 Insights 做每日/每周分析（持续迭代中）

### Dev commands

**Frontend**

```bash
cd frontend
npm run dev
npm run build
npm test
npm run test:e2e      # E2E 关键流程（无 DASHSCOPE_API_KEY 时自动 skip）
```

**E2E 测试（Playwright）**

覆盖登录、聊天、保存 Food Log、进入 Insights。运行前需确保**后端已启动**（`uvicorn backend.main:app --reload`）：

```bash
cd frontend
npm run test:e2e
```

**Backend tests**

```bash
python -m pytest backend/tests
```

**Release gate (recommended)**

```powershell
.\scripts\run_release_gate.ps1
```

See `docs/TEST_BASELINE.md` for gate scope and isolation rules.

### Example API call (health)

```bash
curl http://localhost:8000/health
```

### Example API call (estimate)

```bash
curl -X POST http://localhost:8000/estimate \
  -H "Content-Type: application/json" \
  -d '{"query":"一碗牛肉面大概多少热量？"}'
```

> 当前产品策略：用户估算入口统一走 Chat；`/estimate` 作为系统能力接口保留，用于结构化估算复用。

---

## API Quick Reference

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `DELETE /auth/me`
- `GET /chat/sessions`
- `POST /chat/sessions`
- `POST /chat/messages`
- `POST /chat/sessions/{session_id}/messages`
- `POST /estimate`
- `GET /food-logs`
- `POST /food-logs`
- `PATCH /food-logs/{food_log_id}`
- `POST /food-logs/{food_log_id}/restore`
- `DELETE /food-logs/{food_log_id}`
- `GET /profile/me`
- `POST /profile`
- `PUT /profile/{profile_id}`

---

## Project Status

**Active Development**

- 核心链路（Assistant + Food Log + Profile）可用
- Insights 与数据层能力仍在持续迭代

---

## Roadmap

### Near-term

- Insights 闭环能力（按天/按周分析 + AI建议）
- Food Log 真实图片来源接入与回填流程
- 中文饮食知识库 RAG（提升中餐估算准确度）

### Mid-term

- 趋势分析（7/30天）
- 更细粒度筛选与复用推荐
- 模型微调评估与可控上线

---

## Contributing

欢迎贡献。建议按以下流程：

1. Fork / 新建分支：`feature/xxx` 或 `fix/xxx`
2. 本地开发并保证可运行
3. 运行测试：
   - `python -m pytest backend/tests`
   - `cd frontend && npm test`
4. 提交 PR，描述：
   - 背景问题
   - 变更内容
   - 测试方式
   - 影响范围（API/UI/数据）

建议规范：

- 保持 PR 小而聚焦
- 新增接口需补最小测试
- 避免提交密钥、数据库文件等敏感内容

---

## Support / Contact

如需帮助，请优先通过：

- GitHub Issues（Bug / Feature Request）
- 项目维护者（在仓库主页维护者信息中联系）

提问时建议附上：

- 复现步骤
- 错误日志 / 截图
- 运行环境（OS、Python、Node 版本）

---

## Acknowledgments

- FastAPI
- React / Vite
- 阿里云千问 API（Qwen）
- 所有测试与文档贡献者

---

## License

当前仓库**尚未包含 LICENSE 文件**。

在你明确添加许可证（如 MIT / Apache-2.0）前，默认视为“保留所有权利（All Rights Reserved）”。
如果你计划开源，建议尽快补充 `LICENSE` 文件并在本节更新。

---

> Disclaimer: Food Pilot 提供的是估算性质信息，不构成医疗建议或诊断结论。
