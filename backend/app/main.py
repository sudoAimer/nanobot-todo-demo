import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, TodoWriteRequest
from .todo_store import TodoStore
from .nanobot_runner import AgentService

store = TodoStore(os.getenv("TODO_STORAGE_PATH", ".data/todos"))
app = FastAPI(title="nanobot Todo Demo")
agent = AgentService(store)

@app.on_event("startup")
async def startup(): await agent.startup()

@app.on_event("shutdown")
async def shutdown(): await agent.shutdown()
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","), allow_methods=["*"], allow_headers=["*"], allow_credentials=True)


@app.get("/health")
async def health() -> dict[str, str]: return {"status": "ok"}

@app.get("/api/sessions/{session_key}/todos")
async def get_todos(session_key: str): return await store.get(session_key)

@app.post("/api/sessions/{session_key}/todos")
async def write_todos(session_key: str, request: TodoWriteRequest): return await store.replace(session_key, request.todos)

@app.websocket("/api/sessions/{session_key}/ws")
async def events(websocket: WebSocket, session_key: str):
    await websocket.accept()
    await agent.connect(session_key, websocket)
    try:
        while True:
            payload = await websocket.receive_json()
            kind = payload.get("type")
            if kind == "run.start":
                try: await agent.start(session_key, payload["message"])
                except (KeyError, RuntimeError) as exc: await websocket.send_json({"type":"run.failed", "error":str(exc)})
            elif kind == "run.cancel": await agent.cancel(session_key, payload.get("run_id"))
            elif kind == "ping": await websocket.send_json({"type":"pong"})
    except WebSocketDisconnect: pass
    finally: agent.disconnect(session_key, websocket)
