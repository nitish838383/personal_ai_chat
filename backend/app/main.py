"""
Personal AI OS — FastAPI application entrypoint.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db, close_db, engine, init_db

from app.api import auth as auth_router
from app.api import chat as chat_router
from app.api import memory as memory_router
from app.api import tasks as tasks_router
from app.api import activity as activity_router
from app.api import integrations as integrations_router
from app.api import planner as planner_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} ({settings.APP_ENV})")
    if settings.APP_ENV == "development":
        try:
            await init_db()
            print("✅ Database tables ensured (development mode)")
        except Exception as e:
            print(f"⚠️  Could not initialize DB tables: {e}")
    yield
    await close_db()
    print("👋 Database connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.2.0",
    description="Personal AI OS — One AI interface for your entire digital life.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.API_V1_PREFIX
app.include_router(auth_router.router, prefix=prefix)
app.include_router(chat_router.router, prefix=prefix)
app.include_router(memory_router.router, prefix=prefix)
app.include_router(tasks_router.router, prefix=prefix)
app.include_router(activity_router.router, prefix=prefix)
app.include_router(integrations_router.router, prefix=prefix)
app.include_router(planner_router.router, prefix=prefix)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Personal AI OS",
        "version": "0.2.0",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar_one()
        return {
            "status": "healthy",
            "database": "connected",
            "engine": str(engine.url).split("@")[-1] if "@" in str(engine.url) else "unknown",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)[:200],
        }
