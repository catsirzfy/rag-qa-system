"""客户端依赖注入 — JWT 认证。"""
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import verify_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not token: return None
    payload = verify_token(token)
    if not payload: return None
    r = await db.execute(select(User).where(User.id == int(payload["sub"])))
    return r.scalar_one_or_none()

def require_auth(user: User = Depends(get_current_user)):
    if not user: from app.exceptions import AuthenticationError; raise AuthenticationError()
    return user

def require_admin(user: User = Depends(require_auth)):
    if user.role != "admin": from app.exceptions import AuthorizationError; raise AuthorizationError()
    return user
