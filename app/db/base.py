"""数据库引擎。"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

class Base(DeclarativeBase): pass

_engine = None; _SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        url = settings.DATABASE_URL
        if "sqlite" in url:
            _engine = create_async_engine(url, echo=False)
        else:
            _engine = create_async_engine(url, echo=False, pool_pre_ping=True, pool_recycle=1800, pool_size=20)
    return _engine

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = async_sessionmaker(bind=get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _SessionLocal

async def close_db():
    if _engine: await _engine.dispose()
