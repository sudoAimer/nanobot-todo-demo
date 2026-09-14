import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, TodoWriteRequest
from .todo_store import TodoStore
from .nanobot_runner import NanobotRunner

store = TodoStore(os.getenv("TODO_STORAGE_PATH", ".data/todos"))
app = FastAPI(title="nanobot Todo Demo")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","), allow_methods=["*"], allow_headers=["*"], allow_credentials=True)


@app.get("/health")
async def health() -> dict[str, str]: return {"status": "ok"}

@app.get("/api/sessions/{session_key}/todos")
async def get_todos(session_key: str): return await store.get(session_key)

@app.post("/api/sessions/{session_key}/todos")
async def write_todos(session_key: str, request: TodoWriteRequest): return await store.replace(session_key, request.todos)

@app.post("/api/sessions/{session_key}/chat")
async def chat(session_key: str, request: ChatRequest):
    content, todos = await NanobotRunner(store).run(request.message, session_key)
    return {"content": content, "todos": todos.todos, "counts": todos.counts}

@app.websocket("/api/sessions/{session_key}/events")
async def events(websocket: WebSocket, session_key: str):
    await websocket.accept()
    try:
        await websocket.send_json({"type": "todo.updated", "session_key": session_key, "data": (await store.get(session_key)).model_dump(mode="json")})
        while True: await websocket.receive_text()
    except WebSocketDisconnect: pass

