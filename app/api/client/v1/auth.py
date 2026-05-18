"""用户认证 API。"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.auth_service import AuthService
from app.api.client.deps import get_current_user

router = APIRouter()

@router.post("/register")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await AuthService.register(db, data.username, data.email, data.password)
    return {"code": 200, "data": {"id": user.id, "username": user.username}}

@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return {"code": 200, "data": await AuthService.login(db, data.username, data.password)}

@router.get("/me")
async def me(user = Depends(get_current_user)):
    if not user: return {"code": 401, "message": "未登录"}
    return {"code": 200, "data": {"id": user.id, "username": user.username, "email": user.email, "role": user.role}}
