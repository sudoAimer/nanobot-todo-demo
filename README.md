# nanobot Todo Demo

DeepSeek Harness 风格的 `todo_write` + FastAPI + Vue 3 demo。

## 启动

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
cd ../frontend
npm install
npm run dev
```

打开 http://localhost:5173。后端会在安装并配置 `nanobot-ai` 后通过 SDK 调用 agent；未配置时聊天接口返回可验证的 demo 回复。

环境变量：`NANOBOT_CONFIG_PATH`、`TODO_STORAGE_PATH`、`TODO_ALLOW_PARALLEL_IN_PROGRESS`、`TODO_CLEAR_ON_TURN_START`、`CORS_ORIGINS`。

