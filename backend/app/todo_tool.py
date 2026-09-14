from .models import TodoItem, TodoListResponse
from contextvars import ContextVar
from .todo_store import TodoStore

try:
    from nanobot.agent.tools.base import Tool
except ImportError:
    class Tool: pass


class TodoTool(Tool):
    name = "todo_write"
    description = "Replace the complete task list. Each item status is pending, in_progress, or completed."

    def __init__(self, store: TodoStore, session_key: str, allow_parallel: bool = True) -> None:
        self.store, self.session_key, self.allow_parallel = store, session_key, allow_parallel

    async def __call__(self, todos: list[TodoItem]) -> TodoListResponse:
        if not self.allow_parallel and sum(x.status.value == "in_progress" for x in todos) > 1:
            raise ValueError("Only one todo may be in_progress")
        return await self.store.replace(self.session_key, todos)

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"todos": {"type": "array", "items": {"type": "object", "properties": {"content": {"type": "string"}, "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}}, "required": ["content", "status"]}}}, "required": ["todos"]}

    async def execute(self, **kwargs):
        return (await self([TodoItem.model_validate(item) for item in kwargs.get("todos", [])])).model_dump(mode="json")


_active_session: ContextVar[str | None] = ContextVar("todo_session", default=None)


class SessionTodoTool(TodoTool):
    """One registry-safe tool whose target session is supplied per run."""
    async def __call__(self, todos: list[TodoItem]) -> TodoListResponse:
        session = _active_session.get()
        if session is None:
            raise ValueError("todo_write requires an active session")
        self.session_key = session
        return await super().__call__(todos)

    @classmethod
    def bind(cls, session_key: str):
        return _active_session.set(session_key)
