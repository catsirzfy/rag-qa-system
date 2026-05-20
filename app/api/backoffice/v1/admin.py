"""后台管理 API — 用户 CRUD + 审计日志 + 文档管理。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.models.user import User
from app.models.chat_history import ChatHistory
from app.api.client.deps import require_admin
from app.core.security import hash_password
from app.services import rag_service

router = APIRouter()


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    r = await db.execute(select(User).order_by(User.id))
    users = r.scalars().all()
    return {"code": 200, "data": [
        {"id": u.id, "username": u.username, "email": u.email, "role": u.role, "is_active": u.is_active}
        for u in users
    ]}


@router.post("/users")
async def create_user(data: CreateUserRequest, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    existing = await db.scalar(select(User).where(User.username == data.username))
    if existing:
        raise HTTPException(400, "用户名已存在")
    user = User(username=data.username, email=data.email, password=hash_password(data.password), role=data.role)
    db.add(user)
    await db.commit()
    return {"code": 200, "message": "创建成功", "data": {"id": user.id}}


@router.put("/users/{user_id}")
async def update_user(user_id: int, data: UpdateUserRequest, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    if data.username is not None: user.username = data.username
    if data.email is not None: user.email = data.email
    if data.password is not None: user.password = hash_password(data.password)
    if data.role is not None: user.role = data.role
    if data.is_active is not None: user.is_active = data.is_active
    await db.commit()
    return {"code": 200, "message": "更新成功"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    await db.delete(user)
    await db.commit()
    return {"code": 200, "message": "删除成功"}


@router.get("/stats")
async def stats(admin=Depends(require_admin)):
    docs = rag_service.get_documents()
    return {"code": 200, "data": docs}


# ================================================================
# 审计日志
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


@router.delete("/audit/{record_id}")
async def delete_audit_item(record_id: int, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    record = await db.get(ChatHistory, record_id)
    if record:
        await db.delete(record)
        await db.commit()
    return {"code": 200, "message": "删除成功"}


@router.delete("/audit")
async def clear_audit(db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    await db.execute(delete(ChatHistory))
    await db.commit()
    return {"code": 200, "message": "审计日志已清空"}
