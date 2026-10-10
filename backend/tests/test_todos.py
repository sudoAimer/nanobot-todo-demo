import asyncio
import json
from types import SimpleNamespace

import pytest
from nanobot import Nanobot, StreamEvent, LLMUsage
from nanobot.agent.tools.context import RequestContext, request_context
from nanobot.agent.tools.registry import ToolRegistry
from nanobot_todo import TodoPlugin
from app.nanobot_runner import AgentService


@pytest.mark.asyncio
async def test_restore_and_isolate(tmp_path):
    plugin = TodoPlugin(tmp_path)
    result = await plugin.replace('a', [{'content': 'build', 'status': 'in_progress'}])
    assert result.counts.in_progress == 1
    assert (await plugin.get('b')).todos == []
    assert (await TodoPlugin(tmp_path).get('a')).todos == result.todos
    result.todos[0].content = 'mutated'
    assert (await plugin.get('a')).todos[0].content == 'build'


@pytest.mark.asyncio
async def test_context_registration_and_notifications():
    updates = []
    async def notify(session, state):
        updates.append((session, state))
    plugin = TodoPlugin(on_update=notify)
    registry = ToolRegistry()
    bot = SimpleNamespace(_loop=SimpleNamespace(tools=registry))
    plugin.install(bot)
    plugin.install(bot)
    with pytest.raises(ValueError):
        TodoPlugin().install(bot)
    async def run(session):
        with request_context(RequestContext(channel='web', chat_id=session, session_key=session)):
            result = await registry.execute('todo_write', {'todos': [{'content': session, 'status': 'pending'}]})
            assert json.loads(result)['session_key'] == session
    await asyncio.gather(run('a'), run('b'))
    assert (await plugin.get('a')).todos[0].content == 'a'
    assert (await plugin.get('b')).todos[0].content == 'b'
    assert len(updates) == 2
    with pytest.raises(ValueError):
        await plugin.tool.execute(todos=[])


@pytest.mark.asyncio
async def test_validation_and_notification_failure():
    async def fail(*args):
        raise RuntimeError('offline')
    plugin = TodoPlugin(allow_parallel=False, on_update=fail)
    with pytest.raises(ValueError):
        await plugin.replace('a', [{'content': 'x', 'status': 'in_progress'}] * 2)
    with pytest.raises(ValueError):
        await plugin.replace('a', [{'content': '', 'status': 'pending'}])
    await plugin.replace('a', [{'content': 'saved', 'status': 'completed'}])
    assert (await plugin.get('a')).counts.completed == 1


@pytest.mark.asyncio
async def test_sdk_events_are_json_serializable():
    service = AgentService(TodoPlugin())
    class Bot:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type='tool.started', name='todo_write', arguments={'todos': []}, tool_call_id='call1')
            yield StreamEvent(type='run.completed', usage=LLMUsage(input_tokens=2, output_tokens=1, total_tokens=3, reported_tokens=3))
    class Socket:
        def __init__(self):
            self.events = []
        async def send_json(self, event):
            json.dumps(event)
            self.events.append(event)
    socket = Socket()
    service.bot = Bot()
    await service.connect('a', socket)
    await service._run('a', 'run1', 'hello')
    assert socket.events[-1]['type'] == 'run.completed'
    assert socket.events[-1]['usage']['total_tokens'] == 3
    assert socket.events[-2]['arguments'] == {'todos': []}
    assert socket in service.connections['a']
