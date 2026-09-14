from collections.abc import Awaitable, Callable
from .models import TodoListResponse

try:
    from nanobot.agent import AgentHook, AgentHookContext
except ImportError:
    class AgentHook: pass
    AgentHookContext = object


class TodoHook(AgentHook):
    def __init__(self, on_update: Callable[[TodoListResponse], Awaitable[None]] | None = None) -> None:
        self.on_update = on_update

    async def publish(self, state: TodoListResponse) -> None:
        if self.on_update:
            await self.on_update(state)

