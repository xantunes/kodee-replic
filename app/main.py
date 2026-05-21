from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Kodee Replica",
    description="AI Agent with MCP - Hostinger Kodee Replica",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chat service instance
chat_service = ChatService()


@app.get("/health", tags=["health"])
async def health_check() -> JSONResponse:
    return JSONResponse(
        content={
            "status": "healthy",
            "environment": settings.APP_ENV,
            "version": app.version,
        }
    )


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Process a chat message and return an assistant response."""
    result = await chat_service.process_message(
        user_id=request.user_id,
        message=request.message,
        session_id=request.session_id,
    )
    return ChatResponse(
        message=result["message"],
        actions=result["actions"],
        session_id=result["session_id"],
    )


@app.websocket("/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str) -> None:
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            session_id = data.get("session_id")

            result = await chat_service.process_message(
                user_id=user_id,
                message=message,
                session_id=session_id,
            )
            await websocket.send_json(result)
    except WebSocketDisconnect:
        pass
