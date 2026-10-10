"""可复制到业务系统的 nanobot 0.3.5 Todo 插件，仅依赖 nanobot 和 Pydantic。"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from collections.abc import Awaitable, Callable
from enum import StrEnum
from pathlib import Path
from tempfile import NamedTemporaryFile

from nanobot.agent.tools.base import Tool
from nanobot.agent.tools.context import current_request_session_key
from pydantic import BaseModel, ConfigDict, Field


class TodoStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TodoItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=500)
    status: TodoStatus


class TodoCounts(BaseModel):
    pending: int = 0
    in_progress: int = 0
    completed: int = 0


class TodoListResponse(BaseModel):
    session_key: str
    todos: list[TodoItem]
    counts: TodoCounts


class TodoPlugin:
    """单进程存储及更新通知；每个 Nanobot 实例安装一次。"""

    def __init__(
        self,
        storage_dir: str | Path | None = None,
        on_update: Callable[[str, dict], Awaitable[None]] | None = None,
        allow_parallel: bool = True,
    ) -> None:
        self.root = Path(storage_dir) if storage_dir is not None else None
        self.on_update = on_update
        self.allow_parallel = allow_parallel
        self._memory: dict[str, list[dict]] = {}
        self._lock = asyncio.Lock()
        self.tool = TodoWriteTool(self)

    def install(self, bot) -> None:
        # 0.3.5 尚无公开的 SDK 注册方法，兼容访问集中在此处。
        registry = getattr(getattr(bot, "_loop", None), "tools", None)
        if registry is None or not callable(getattr(registry, "register", None)):
            raise RuntimeError("不兼容的 Nanobot SDK：找不到工具注册接口")
        existing = registry.get(self.tool.name)
        if existing is self.tool:
            return
        if existing is not None:
            raise ValueError("todo_write 已注册，请避免覆盖其他工具")
        registry.register(self.tool)

    def _path(self, session_key: str) -> Path:
        assert self.root is not None
        return self.root / (hashlib.sha256(session_key.encode()).hexdigest() + ".json")

    @staticmethod
    def _response(session_key: str, data: list[dict]) -> TodoListResponse:
        todos = [TodoItem.model_validate(item) for item in data]
        counts = TodoCounts()
        for item in todos:
            setattr(counts, item.status.value, getattr(counts, item.status.value) + 1)
        return TodoListResponse(session_key=session_key, todos=todos, counts=counts)

    async def get(self, session_key: str) -> TodoListResponse:
        async with self._lock:
            if self.root is None:
                data = self._memory.get(session_key, [])
            else:
                path = self._path(session_key)
                data = json.loads(path.read_text(encoding="utf-8"))["todos"] if path.exists() else []
            return self._response(session_key, data)

    async def replace(self, session_key: str, todos: list[TodoItem | dict]) -> TodoListResponse:
        if not session_key:
            raise ValueError("session_key 不能为空")
        items = [TodoItem.model_validate(item) for item in todos]
        if not self.allow_parallel and sum(item.status == TodoStatus.IN_PROGRESS for item in items) > 1:
            raise ValueError("Only one todo may be in_progress")
        data = [item.model_dump(mode="json") for item in items]
        async with self._lock:
            if self.root is None:
                self._memory[session_key] = data
            else:
                self.root.mkdir(parents=True, exist_ok=True)
                path = self._path(session_key)
                tmp = None
                try:
                    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.root, suffix=".tmp", delete=False) as file:
                        tmp = Path(file.name)
                        json.dump({"version": 1, "todos": data}, file, ensure_ascii=False)
                    os.replace(tmp, path)
                finally:
                    if tmp is not None:
                        tmp.unlink(missing_ok=True)
            state = self._response(session_key, data)
            # 保持保存和通知顺序。回调只能负责推送，不要回调本插件或启动新一轮 Agent。
            if self.on_update is not None:
                try:
                    await self.on_update(session_key, state.model_dump(mode="json"))
                except Exception:
                    logging.getLogger(__name__).exception("Todo 已保存，更新通知失败：%s", session_key)
            return state

    async def clear(self, session_key: str) -> TodoListResponse:
        return await self.replace(session_key, [])


class TodoWriteTool(Tool):
    name = "todo_write"
    description = "Replace the complete task list. Use for multi-step tasks and update progress as work proceeds. Status: pending, in_progress, completed."
    _plugin_discoverable = False

    def __init__(self, plugin: TodoPlugin) -> None:
        self.plugin = plugin

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"todos": {"type": "array", "items": TodoItem.model_json_schema()}}, "required": ["todos"], "additionalProperties": False}

    async def execute(self, **kwargs) -> str:
        session_key = current_request_session_key()
        if not session_key:
            raise ValueError("todo_write requires an active Nanobot request session")
        state = await self.plugin.replace(session_key, kwargs["todos"])
        return state.model_dump_json()
