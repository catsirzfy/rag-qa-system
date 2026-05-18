"""JWT 认证 + 密码哈希。"""
import hashlib, os
from datetime import datetime, timedelta, UTC
from typing import Optional
import uuid
from jose import jwt, JWTError
from app.core.config import settings

def hash_password(password: str) -> str:
    salt = os.urandom(32).hex()
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    return f"{salt}${h}"

def verify_password(plain: str, hashed: str) -> bool:
    if '$' not in hashed: return False
    salt, h = hashed.split('$', 1)
    return h == hashlib.pbkdf2_hmac('sha256', plain.encode(), salt.encode(), 100000).hex()

def create_access_token(user_id: int, role: str = "user") -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({
        "exp": expire, "sub": str(user_id), "role": role, "jti": str(uuid.uuid4()),
    }, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
