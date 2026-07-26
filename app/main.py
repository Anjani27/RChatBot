"""FastAPI application factory — entry point for the LangGraph AI Chatbot."""
import os
import uvicorn
from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles

from app.core.config import UPLOAD_DIR
from app.core.database import init_db
from app.api import conversations, chat, uploads, auth
from app.exceptions.handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""    
    init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="LangGraph AI Chatbot API",
        description="Full-stack AI chatbot with RAG (Chroma DB), streaming, and PDF upload.",
        version="2.0.0",
        lifespan=lifespan,
    )

    # ── CORS ──────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Static files (HTML/CSS/JS frontend) ──────────────────────
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    # ── Routers ───────────────────────────
    app.include_router(auth.router)
    app.include_router(conversations.router)
    app.include_router(chat.router)
    app.include_router(uploads.router)

    # ── Exception handlers ─────────
    register_exception_handlers(app)

    # ── Serve index.html at root ───
    @app.get("/")
    def serve_root():
        return FileResponse("frontend/index.html")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
