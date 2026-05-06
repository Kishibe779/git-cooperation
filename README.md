# CareerPilot

CareerPilot is a FastAPI + vanilla JavaScript product prototype for resume optimization and job matching.

## Features

- Resume and job description matching
- Local rule-based analysis with DeepSeek provider support
- Server-side API key handling
- Login and registration
- Saved analysis history
- Billing plan demo flow
- Markdown report export
- Backend serves the frontend from the same port

## Start

Recommended:

```powershell
cd E:\LXH_EX
.\start_backend.bat
```

Then open:

```text
http://127.0.0.1:8000/?v=20260428-10
```

Manual command:

```powershell
cd E:\LXH_EX
$env:PYTHONDONTWRITEBYTECODE="1"
D:\Anaconda3\envs\FFFOP\python.exe -B -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Do not add `--reload` on this Windows/Anaconda setup. It can trigger `PermissionError: [WinError 5]` from Python multiprocessing.

## DeepSeek

Create or edit `backend/.env`:

```env
DEEPSEEK_API_KEY=your_real_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
APP_DEFAULT_PROVIDER=deepseek
LLM_ENABLE_FALLBACK=true
```

If DeepSeek is unavailable, the app falls back to local rule-based output so the demo still works.

For verification, choose `deepseek strict (no fallback)` in the frontend provider selector. This mode must call DeepSeek directly. If DeepSeek is not configured or the request fails, the API returns an error instead of using the local template.

## API

- `GET /api/v1/health`
- `GET /api/v1/meta`
- `POST /api/v1/analyze`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/plans`
- `POST /api/v1/billing/checkout`
- `GET /api/v1/analyses`

Demo data is stored in `.runtime/app_store.json`.

## Test

```powershell
cd E:\LXH_EX
$env:PYTHONDONTWRITEBYTECODE="1"
D:\Anaconda3\envs\FFFOP\python.exe -B -m pytest backend\tests -q
```
