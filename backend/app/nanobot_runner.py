import asyncio
import os
import uuid
from collections import defaultdict
from typing import Any
from .todo_store import TodoStore
from .todo_tool import SessionTodoTool


class AgentService:
    def __init__(self, store: TodoStore) -> None:
        self.store, self.bot = store, None
        self.connections: dict[str, set[Any]] = defaultdict(set)
        self.runs: dict[str, asyncio.Task[None]] = {}
        self.run_ids: dict[str, str] = {}
        self.lock = asyncio.Lock()

    async def startup(self) -> None:
        try:
            from nanobot import Nanobot
            kwargs: dict[str, Any] = {}
            if value := os.getenv("NANOBOT_CONFIG_PATH"): kwargs["config_path"] = value
            if value := os.getenv("NANOBOT_WORKSPACE"): kwargs["workspace"] = value
            self.bot = Nanobot.from_config(**kwargs)
        except ImportError:
            self.bot = None

    async def shutdown(self) -> None:
        for task in self.runs.values(): task.cancel()
        if self.bot is not None: await self.bot.aclose()

    async def emit(self, session: str, event: dict[str, Any]) -> None:
        for ws in tuple(self.connections.get(session, ())):
            try: await ws.send_json(event)
            except Exception: self.disconnect(session, ws)

    async def connect(self, session: str, ws: Any) -> None:
        self.connections[session].add(ws)
        await ws.send_json({"type": "connection.ready", "session_key": session})
        state = await self.store.get(session)
        await self.emit(session, {"type": "todo.updated", "session_key": session, "data": state.model_dump(mode="json")})

    def disconnect(self, session: str, ws: Any) -> None:
        self.connections[session].discard(ws)
        if not self.connections[session]: self.connections.pop(session, None)

    async def start(self, session: str, message: str) -> str:
        async with self.lock:
            if session in self.runs and not self.runs[session].done(): raise RuntimeError("该会话已有 Agent 正在运行")
            run_id = f"run-{uuid.uuid4().hex[:12]}"
            self.runs[session] = asyncio.create_task(self._run(session, run_id, message)); self.run_ids[session] = run_id
            return run_id

    async def cancel(self, session: str, run_id: str | None = None) -> None:
        task = self.runs.get(session)
        if task and not task.done() and (run_id is None or self.run_ids.get(session) == run_id): task.cancel()

    async def _run(self, session: str, run_id: str, message: str) -> None:
        await self.emit(session, {"type": "run.started", "run_id": run_id})
        if self.bot is None:
            await self.emit(session, {"type": "run.failed", "run_id": run_id, "error": "nanobot-ai 未安装或未配置，请先安装并运行 nanobot onboard。"}); return
        try:
            registry = getattr(getattr(self.bot, "_loop", None), "tools", None)
            if registry is not None and hasattr(registry, "register"):
                if "todo_write" not in getattr(registry, "_tools", {}):
                    registry.register(SessionTodoTool(self.store, "", os.getenv("TODO_ALLOW_PARALLEL_IN_PROGRESS", "true").lower() == "true"))
            token = SessionTodoTool.bind(session)
            async for event in self.bot.stream(message, session_key=session, channel="web", chat_id=session):
                kind = str(event.type); kind = "message.delta" if kind == "text.delta" else kind
                payload = {"type": kind, "run_id": run_id}
                for key in ("delta", "name", "content", "error", "input", "output", "usage", "metadata"):
                    if getattr(event, key, None) is not None: payload[key] = getattr(event, key)
                await self.emit(session, payload)
                if kind == "tool.completed" and payload.get("name") == "todo_write":
                    state = await self.store.get(session)
                    await self.emit(session, {"type": "todo.updated", "run_id": run_id, "data": state.model_dump(mode="json")})
            from .todo_tool import _active_session
            _active_session.reset(token)
        except asyncio.CancelledError:
            await self.emit(session, {"type": "run.cancelled", "run_id": run_id})
        except Exception as exc:
            await self.emit(session, {"type": "run.failed", "run_id": run_id, "error": str(exc)})
        finally:
            if self.run_ids.get(session) == run_id: self.runs.pop(session, None); self.run_ids.pop(session, None)
