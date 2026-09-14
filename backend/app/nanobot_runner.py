from collections.abc import Awaitable, Callable
from .models import TodoListResponse
from .todo_store import TodoStore


class NanobotRunner:
    def __init__(self, store: TodoStore, publish: Callable[[dict], Awaitable[None]] | None = None) -> None:
        self.store, self.publish = store, publish

    async def run(self, message: str, session_key: str) -> tuple[str, TodoListResponse]:
        state = await self.store.get(session_key)
        try:
            from nanobot import Nanobot
        except ImportError:
            if not state.todos:
                from .models import TodoItem, TodoStatus
                state = await self.store.replace(session_key, [
                    TodoItem(content="设计登录页面与交互流程", status=TodoStatus.IN_PROGRESS),
                    TodoItem(content="实现登录接口和表单校验", status=TodoStatus.PENDING),
                    TodoItem(content="补充登录流程测试", status=TodoStatus.PENDING),
                ])
            return f"Demo 模式已收到：{message}", state
        # nanobot API versions may expose custom-tool registration differently;
        # keep this adapter isolated so the demo remains usable without nanobot.
        async with Nanobot.from_config() as bot:
            result = await bot.run(message, session_key=session_key)
        return result.content, await self.store.get(session_key)
