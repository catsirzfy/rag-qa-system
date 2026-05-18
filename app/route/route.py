"""应用工厂。"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.core.config import settings
from app.route.router_registry import CLIENT_ROUTES, BACKOFFICE_ROUTES, register_routes
from app.db.base import close_db

STATIC = os.path.join(os.path.dirname(__file__), "..", "..", "static", "index.html")

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield; await close_db()

def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    register_routes(app, CLIENT_ROUTES)
    register_routes(app, BACKOFFICE_ROUTES)

    @app.get("/")
    async def home():
        if os.path.exists(STATIC): return FileResponse(STATIC)
        return {"message": "RAG API", "docs": "/docs"}
    return app
