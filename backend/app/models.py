from pydantic import BaseModel
from nanobot_todo import TodoItem


class TodoWriteRequest(BaseModel):
    todos: list[TodoItem]
