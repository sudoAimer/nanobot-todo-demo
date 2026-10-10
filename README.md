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


## 单文件接入 Python SDK（nanobot-ai 0.3.5）

只需复制 `backend/nanobot_todo.py` 到业务项目的 Python 导入路径。它不依赖 Demo 的 FastAPI、WebSocket 或前端。

```python
from nanobot import Nanobot
from nanobot_todo import TodoPlugin

async def on_todo_update(session_key, state):
    # state 已是可 JSON 序列化的字典，接入业务系统自己的推送通道。
    await your_event_bus.publish(session_key, {"type": "todo.updated", "data": state})

bot = Nanobot.from_config()
todo = TodoPlugin(storage_dir="./todos", on_update=on_todo_update)
todo.install(bot)

async for event in bot.stream("完成任务并通过 todo_write 更新计划", session_key="task-001"):
    ...  # 原有 SDK 事件处理

state = await todo.get("task-001")
await bot.aclose()
```

- 每个 Nanobot 实例安装一次；重复安装同一插件无副作用，名称冲突明确报错。
- 工具从 SDK 请求上下文自动取得会话 ID，无需手动绑定，也无需把会话 ID 暴露为模型参数。
- 不传 `storage_dir` 使用内存；传入则按会话哈希文件名保存 JSON，兼容原 Demo 的存储格式。
- `get`、`replace`、`clear` 返回 Pydantic 模型；推送回调收到普通字典。
- `allow_parallel=False` 限制同一列表最多一个进行中任务。
- 工具保存后直接通知，不依赖 `tool.completed`；HTTP 更新也走同一通知路径。
- 通知异常会记录日志，已保存状态仍可读取。回调应短小，只负责推送，不要调用本插件或启动新 Agent；保存与通知使用同一锁保持顺序。
- 内置存储适用于单进程服务，多个 worker 不应共享写入目录。Todo 是 Agent 的计划状态，不替代业务任务执行状态。
- SDK 注册兼容代码仅在 `install()` 中访问 `_loop.tools`；后续 nanobot 版本需重新核验。注册工具允许模型使用它，是否调用仍取决于任务和提示词。

### 验证

```bash
cd backend
pip install -e ".[test]"
python -m pytest tests -q
```
