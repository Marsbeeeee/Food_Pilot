# API Key Setup

Food Pilot calls AI from the backend only.
Do not expose the API key to the frontend bundle.

## Frontend API base URL

The frontend reads `VITE_API_BASE_URL` from environment files. If unset, it defaults to `http://localhost:8000`.

- **Development**: Set in `frontend/.env.local` or leave unset for localhost.
- **Production**: Set in `frontend/.env.production` before `npm run build`.

Example:

```env
VITE_API_BASE_URL=http://localhost:8000
```

For production, use your deployed API URL (e.g. `https://api.your-domain.com`).

## Files the backend reads

The backend checks these files in order:

1. `.env`
2. `.env.local`
3. `frontend/.env.local`

## 支持的 AI 提供商

### 1. Google Gemini（默认）

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_TIMEOUT_SECONDS=20
```

`API_KEY` 仍可作为兼容旧配置的备选变量名。

### 2. 阿里云千问（可选）

参考 [阿里云百炼首次调用千问 API](https://help.aliyun.com/zh/model-studio/first-api-call-to-qwen) 获取 API Key。

```env
DASHSCOPE_API_KEY=sk-xxx
AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL=qwen-plus
```

- 若只设置 `DASHSCOPE_API_KEY` 而未设置 `AI_BASE_URL`，会自动使用千问默认地址。
- 可选的模型：`qwen-plus`、`qwen-max`、`qwen-turbo` 等，见 [模型列表](https://help.aliyun.com/zh/model-studio/models)。

## 更换 Key / 模型

1. 编辑项目根目录 `.env` 或 `.env.local`。
2. 若用 Gemini：更新 `GEMINI_API_KEY` 和 `GEMINI_MODEL`。
3. 若用千问：更新 `DASHSCOPE_API_KEY` 和 `AI_MODEL`。
4. **重启后端服务**。

## Verify

1. Start the backend: `uvicorn backend.main:app --reload`
2. Start the frontend: `npm run dev`
3. Sign in and send an estimate request

If the key is missing or invalid, `/estimate` returns an AI config or upstream auth error.
