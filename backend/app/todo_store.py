import asyncio
import hashlib
import json
import os
from pathlib import Path
from .models import TodoCounts, TodoItem, TodoListResponse


class TodoStore:
    def __init__(self, root: str | Path = ".data/todos") -> None:
        self.root = Path(root)
        self._lock = asyncio.Lock()

    def _path(self, session_key: str) -> Path:
        digest = hashlib.sha256(session_key.encode()).hexdigest()
        return self.root / f"{digest}.json"

    @staticmethod
    def _response(session_key: str, todos: list[TodoItem]) -> TodoListResponse:
        values = {"pending": 0, "in_progress": 0, "completed": 0}
        for item in todos:
            values[item.status.value] += 1
        return TodoListResponse(session_key=session_key, todos=todos, counts=TodoCounts(**values))

    async def get(self, session_key: str) -> TodoListResponse:
        path = self._path(session_key)
        if not path.exists():
            return self._response(session_key, [])
        data = json.loads(path.read_text(encoding="utf-8"))
        return self._response(session_key, [TodoItem.model_validate(x) for x in data["todos"]])

    async def replace(self, session_key: str, todos: list[TodoItem]) -> TodoListResponse:
        async with self._lock:
            self.root.mkdir(parents=True, exist_ok=True)
            path = self._path(session_key)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"version": 1, "todos": [x.model_dump(mode="json") for x in todos]}, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, path)
        return self._response(session_key, todos)

    async def clear(self, session_key: str) -> TodoListResponse:
        return await self.replace(session_key, [])

