"""后台管理 API — 用户管理 + 审计日志 + 文档管理。"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.user import User
from app.models.chat_history import ChatHistory
from app.api.client.deps import require_admin
from app.services import rag_service

router = APIRouter()


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    r = await db.execute(select(User).order_by(User.id))
    users = r.scalars().all()
    return {"code": 200, "data": [
        {"id": u.id, "username": u.username, "email": u.email, "role": u.role, "is_active": u.is_active}
        for u in users
    ]}


@router.get("/stats")
async def stats(admin=Depends(require_admin)):
    docs = rag_service.get_documents()
    return {"code": 200, "data": docs}


# ================================================================
# 审计日志：谁在什么时候问了什么问题
# ================================================================
@router.get("/audit")
async def audit_log(db: AsyncSession = Depends(get_db), admin=Depends(require_admin),
                     page: int = 1, per_page: int = 50):
    total = await db.scalar(select(func.count()).select_from(ChatHistory))
    offset = (page - 1) * per_page
    r = await db.execute(
        select(ChatHistory).order_by(ChatHistory.id.desc()).offset(offset).limit(per_page)
    )
    records = r.scalars().all()
    return {"code": 200, "data": {
        "total": total,
        "items": [
            {"id": h.id, "username": h.username, "question": h.question,
             "answer": h.answer[:200], "time": h.created_at.isoformat() if h.created_at else None}
            for h in records
        ],
    }}
