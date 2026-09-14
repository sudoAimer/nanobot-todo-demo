from enum import StrEnum
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
    pending: int
    in_progress: int
    completed: int


class TodoWriteRequest(BaseModel):
    todos: list[TodoItem]


class TodoListResponse(BaseModel):
    session_key: str
    todos: list[TodoItem]
    counts: TodoCounts


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)

