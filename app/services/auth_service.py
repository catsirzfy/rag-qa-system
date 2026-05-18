"""认证服务 — 注册、登录。"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.exceptions import AuthenticationError, ValidationError

class AuthService:
    @staticmethod
    async def register(db: AsyncSession, username: str, email: str, password: str) -> User:
        # 检查用户名
        r = await db.execute(select(User).where(User.username == username))
        if r.scalar_one_or_none():
            raise ValidationError("用户名已存在")
        # 检查邮箱
        r = await db.execute(select(User).where(User.email == email))
        if r.scalar_one_or_none():
            raise ValidationError("邮箱已注册")
        user = User(username=username, email=email, password=hash_password(password), role="user")
        db.add(user); await db.commit(); await db.refresh(user)
        return user

    @staticmethod
    async def login(db: AsyncSession, username: str, password: str) -> dict:
        r = await db.execute(select(User).where(User.username == username))
        user = r.scalar_one_or_none()
        if not user or not verify_password(password, user.password):
            raise AuthenticationError("用户名或密码错误")
        if not user.is_active:
            raise AuthenticationError("账号已停用")
        return {
            "access_token": create_access_token(user.id, user.role),
            "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role},
        }

    @staticmethod
    async def list_users(db: AsyncSession) -> list[User]:
        r = await db.execute(select(User).order_by(User.id))
        return r.scalars().all()
