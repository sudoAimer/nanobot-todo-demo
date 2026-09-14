# Nanobot Agent Web Harness

Vue 3 + FastAPI agent workspace. Agent turns run through the Nanobot Python SDK and stream over WebSocket; Todo updates are exposed as the `todo_write` tool and appear in real time.

## Setup

```bash
cd backend
pip install -e ".[test]"
nanobot onboard
python -m uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Optional environment variables: `NANOBOT_CONFIG_PATH`, `NANOBOT_WORKSPACE`, `TODO_STORAGE_PATH`, `TODO_ALLOW_PARALLEL_IN_PROGRESS`, `CORS_ORIGINS`, and `VITE_API_URL`.

## WebSocket protocol

Connect to `ws://localhost:8000/api/sessions/{session_key}/ws`, then send JSON such as `{"type":"run.start","message":"实现登录模块"}` or `{"type":"run.cancel"}`. The server streams `run.started`, `message.delta`, `reasoning.delta`, `tool.*`, `todo.updated`, `run.completed`, `run.failed`, and `run.cancelled` events. HTTP is used only for health and Todo reads/writes.

If Nanobot is not installed or configured, the server reports a clear `run.failed` event instead of returning a fake response.
