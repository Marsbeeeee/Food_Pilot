# Food Pilot

![状态](https://img.shields.io/badge/status-active%20development-ff8a65)
![前端](https://img.shields.io/badge/frontend-React%2019-61dafb)
![后端](https://img.shields.io/badge/backend-FastAPI-009688)
![许可](https://img.shields.io/badge/license-not%20open%20source-lightgrey)

Food Pilot 是一个以对话为主入口的营养助手。它以真实点单场景为重要切入口，帮助用户用最小改动做出更稳妥的饮食选择；同时也服务本身就有较健康生活方式、希望持续记录、跟踪和可视化自己饮食习惯的用户。用户可以通过自然语言发起餐食推荐、热量与营养估算，并把有价值的结果保存到 `Food Log`，再进入 `Insights` 做日/周分析；`Profile` 为推荐和估算提供目标、饮食风格与过敏原等个性化上下文。

## 使用说明

本仓库公开仅用于作品展示、评审和交流，不提供开源授权；未经作者书面许可，不得复制、修改、分发、商用或二次发布。

---

## 目录

- [项目说明](#项目说明)
- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [环境要求](#环境要求)
- [安装](#安装)
- [使用方式](#使用方式)
- [API 快速参考](#api-快速参考)
- [项目状态](#项目状态)
- [路线图](#路线图)
- [协作说明](#协作说明)
- [支持与联系](#支持与联系)
- [致谢](#致谢)
- [许可说明](#许可说明)

---

## 项目说明

**产品定位**

Food Pilot 当前解决的是“营养建议有了，但难复用、难持续跟踪”的问题：

1. 通过 Chat 统一承接推荐、估算和澄清提问。
2. 将有价值的估算结果显式保存到 `Food Log`。
3. 结合 `Profile` 的目标、活动水平、饮食风格和过敏原做个性化约束。
4. 基于已保存数据进入 `Insights` 做日/周分析与历史回看。

**核心价值**

- 降低饮食管理门槛，不需要从一开始就手工维护完整饮食流水。
- 让估算结果可以复用、编辑、回看和继续分析，而不是停留在一次性聊天结果里。
- 既覆盖高频外卖和点单决策场景，也支持已经有健康习惯的用户持续记录、观察和可视化自己的饮食节奏。
- 对中国用户常见菜品做了首期知识库增强，提升中文问法下的估算与推荐稳定性。
- 通过过敏原约束、显式保存和分析快照机制，让主链路更可控。

---

## 核心功能

- 账号体系：注册、登录、会话恢复、修改显示名、删除当前账号。
- 助手主链路：基于规则分流处理 `meal_recommendation`、`meal_estimate` 和文本解释类请求。
- Chat 会话管理：新建、续聊、重命名、删除，会话消息持久化。
- 估算能力：支持结构化餐食估算、多菜品拆卡、单菜品内部成分拆解、品牌感知模板估算和保存前澄清。
- Food Log：保存、详情、编辑、软删除、恢复、关键词检索、时间范围筛选、来源回跳。
- Profile：单用户单档案，支持热量目标、活动水平、饮食风格、运动类型和过敏原配置。
- Insights：支持日/周分析、历史快照、分析篮子同步。
- 中文食物知识库：首期离线知识库、检索增强、引用透传、质量基线校验。
- 标准菜品图片能力：支持标准菜品官方图复用、后台候选图审核和生成任务编排。
- 管理员能力：可在独立审核台审批、拒绝、重新生成标准菜品图片候选图。

---

## 技术栈

- **前端**：React 19 + TypeScript + Vite
- **后端**：FastAPI + SQLite
- **AI**：DashScope Qwen（当前默认：`qwen-plus`，兼容 OpenAI 接口）
- **测试**：pytest + Node 测试运行器 + Playwright
- **认证**：Bearer Token + HMAC JWT 会话认证

---

## 项目结构

```text
backend/      FastAPI 接口、服务层、数据结构、仓储层、测试与本地数据
frontend/     React 应用（Workspace / Food Log / Insights / Profile / 管理员审核台）
docs/         产品、配置、治理与测试文档
scripts/      发布门禁与知识库校验脚本
```

---

## 环境要求

请先确保本机具备以下环境：

- Python 3.10+
- Node.js 18+
- npm 9+
- 可用的 AI API Key
- 推荐系统：Windows 10+/macOS/Linux

AI 配置说明：

- 当前默认使用 DashScope/Qwen：需要 `DASHSCOPE_API_KEY`
- 当前模型：`qwen-plus`
- 如果要启用标准菜品图片生成，需要额外配置图片模型相关环境变量

> 后端依赖来自 `requirements.txt`，前端依赖来自 `frontend/package.json`。

---

## 安装

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd Food_Pilot
```

### 2. 配置环境变量

根目录可参考 `.env.example` 创建 `.env`。

**默认 DashScope / Qwen 配置**

```env
DASHSCOPE_API_KEY=sk-xxx
AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL=qwen-plus
```

**可选功能开关**

```env
FOOD_KB_ENABLED=1
# STANDARD_DISH_IMAGE_GENERATION_ENABLED=1
# STANDARD_DISH_IMAGE_API_KEY=sk-xxx
# STANDARD_DISH_IMAGE_BASE_URL=https://api.openai.com/v1
# STANDARD_DISH_IMAGE_MODEL=gpt-image-1
# ADMIN_EMAILS=admin@example.com
```

前端如需指定后端地址，可在 `frontend/.env.local` 中设置：

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动后端

**Windows（PowerShell）**

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

如需运行后端测试：

```bash
pip install -r requirements-dev.txt
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认地址：

- 前端：`http://localhost:3000`
- 后端：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

---

## 使用方式

### 典型使用流程

1. 注册或登录账号。
2. 在 `Workspace` 中发起推荐或估算请求，例如“晚饭怎么吃更适合减脂”或“番茄炒蛋盖饭大概多少热量”。
3. 对有价值的估算结果点击保存到 `Food Log`。
4. 在 `Food Log` 中查看详情、编辑、恢复、回跳来源会话，或加入分析篮子。
5. 进入 `Insights` 查看日/周分析和历史快照。
6. 如有需要，在 `Profile` 中调整目标、饮食风格、运动信息和过敏原。

### 开发命令

**前端**

```bash
cd frontend
npm run dev
npm run build
npm test
npm run test:e2e
```

说明：

- `npm test` 使用 Node 内置测试运行器。
- `npm run test:e2e` 为 Playwright 关键流程回归。
- 当前 E2E 用例依赖实时 AI 返回；若未设置 `DASHSCOPE_API_KEY`，会自动跳过。

**后端测试**

```bash
python -m pytest backend/tests
```

**中文食物知识库质量校验**

```bash
python scripts/validate_food_kb_rag.py
```

**发布门禁（推荐）**

```powershell
.\scripts\run_release_gate.ps1
```

当前默认发布门禁包含：

- 后端测试
- 食物知识库检索质量校验
- 前端单元测试

详见 `docs/rules/test_baseline.md`。

### API 示例：健康检查

```bash
curl http://localhost:8000/health
```

### API 示例：估算

```bash
curl -X POST http://localhost:8000/estimate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d "{\"query\":\"一份牛肉汉堡和一杯无糖拿铁大概多少热量\",\"clientRequestId\":\"demo-estimate-001\"}"
```

> 当前产品策略是以 Chat 为用户主入口；`/estimate` 作为底层结构化估算能力保留，用于统一估算链路和后续复用。

---

## API 快速参考

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `PATCH /auth/me`
- `DELETE /auth/me`
- `POST /chat/sessions`
- `GET /chat/sessions`
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
- `GET /api/insights/basket`
- `PUT /api/insights/basket`
- `GET /admin/dish-images`（仅管理员）
- `GET /admin/dish-images/generation-jobs`（仅管理员）
- `GET /admin/dish-images/{dish_image_id}`（仅管理员）
- `POST /admin/dish-images/{dish_image_id}/approve`（仅管理员）
- `POST /admin/dish-images/{dish_image_id}/reject`（仅管理员）
- `POST /admin/dish-images/{dish_image_id}/regenerate`（仅管理员）
- `POST /admin/dish-images/{dish_image_id}/reject-and-regenerate`（仅管理员）

---

## 项目状态

**持续开发中**

- 核心用户主链路已可用：认证、Workspace/Chat、Food Log、Profile、Insights 已接通。
- 中文食物知识库、标准菜品图片资产和管理员审核能力已落地首期版本。
- 当前仍在持续迭代分析表达、数据覆盖、图片生成质量和整体产品收敛。

---

## 路线图

### 近期

- 继续扩充中文高频菜品、套餐、饮品和便利店场景数据覆盖。
- 继续优化 Chat 估算澄清策略和多菜品拆卡稳定性。
- 补强标准菜品图片提示词自动扩写与生成质量。
- 优化 Insights 的长期趋势表达和可解释性。

### 中期

- 扩展更长周期的趋势分析能力。
- 增强 Food Log 的数值筛选和来源聚合筛选。
- 继续收敛标准菜品数据、官方图资产和 Food Log 复用链路。

---

## 协作说明

当前仓库公开的主要目的是作品展示、评审和交流，**暂不接受外部代码复用、二次发布或未经授权的商业使用**。

如确有合作、试用、授权或评审需要，请先联系作者。

---

## 支持与联系

如需帮助，建议优先通过以下方式：

- GitHub Issues：提交 Bug、功能请求或文档问题
- 仓库维护者：如需管理员配置、环境排查或方向确认，可在仓库主页联系维护者

提问时建议附上：

- 复现步骤
- 错误日志或截图
- 运行环境信息（OS、Python、Node 版本）
- 是否已配置 AI Key 与相关环境变量

---

## 致谢

- FastAPI
- React / Vite
- 阿里云 DashScope / Qwen
- Playwright / pytest
- 所有为测试、知识库和产品文档做出贡献的参与者

---

## 许可说明

本仓库未提供开源许可证。除 GitHub 服务条款要求的有限展示与平台内 fork 权限外，其余权利均由作者保留。

---

> 免责声明：Food Pilot 提供的是估算和饮食管理辅助信息，不构成医疗建议、诊断或治疗意见。
