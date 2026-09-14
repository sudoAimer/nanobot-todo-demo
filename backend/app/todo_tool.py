from .models import TodoItem, TodoListResponse
from .todo_store import TodoStore


class TodoTool:
    name = "todo_write"
    description = "Replace the complete task list. Each item status is pending, in_progress, or completed."

    def __init__(self, store: TodoStore, session_key: str, allow_parallel: bool = True) -> None:
        self.store, self.session_key, self.allow_parallel = store, session_key, allow_parallel

    async def __call__(self, todos: list[TodoItem]) -> TodoListResponse:
        if not self.allow_parallel and sum(x.status.value == "in_progress" for x in todos) > 1:
            raise ValueError("Only one todo may be in_progress")
        return await self.store.replace(self.session_key, todos)

