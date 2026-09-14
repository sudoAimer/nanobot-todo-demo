import pytest
from app.models import TodoItem, TodoStatus
from app.todo_store import TodoStore

@pytest.mark.asyncio
async def test_replace_and_isolate(tmp_path):
    store = TodoStore(tmp_path)
    item = TodoItem(content="build", status=TodoStatus.IN_PROGRESS)
    result = await store.replace("a", [item])
    assert result.counts.in_progress == 1
    assert (await store.get("b")).todos == []
    assert (await store.get("a")).todos == [item]

