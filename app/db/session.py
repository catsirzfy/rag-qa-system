"""数据库会话依赖。"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_session_local

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_local()
    async with factory() as session:
        yield session
