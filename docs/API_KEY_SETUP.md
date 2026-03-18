# API Key Setup

Food Pilot calls Gemini from the backend only.
Do not expose the Gemini API key to the frontend bundle.

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

Use `GEMINI_API_KEY` as the primary variable name.
`API_KEY` is still accepted as a fallback for older local setups.

## Replace the key

1. Open the project root `.env` file.
2. Set `GEMINI_API_KEY=...` to the new key.
3. Keep or update `GEMINI_MODEL` if needed.
4. Restart the backend server.

Example:

```env
GEMINI_API_KEY=your_new_key_here
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_TIMEOUT_SECONDS=20
```

## Verify

1. Start the backend: `uvicorn backend.main:app --reload`
2. Start the frontend: `npm run dev`
3. Sign in and send an estimate request

If the key is missing or invalid, `/estimate` returns an AI config or upstream auth error.
