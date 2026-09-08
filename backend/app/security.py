from datetime import datetime, timedelta, timezone
from hashlib import sha256
import jwt
from fastapi import Depends, Header
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User


password_hasher = PasswordHash.recommended()


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code, self.message, self.status_code = code, message, status_code
        super().__init__(message)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_token(user: User, kind: str, expires: timedelta) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": user.id, "role": user.role, "type": kind, "iat": now, "exp": now + expires},
        settings.app_secret,
        algorithm="HS256",
    )


def decode_token(token: str, kind: str) -> dict:
    try:
        payload = jwt.decode(token, settings.app_secret, algorithms=["HS256"])
        if payload.get("type") != kind:
            raise AppError("INVALID_TOKEN", "令牌类型无效", 401)
        return payload
    except jwt.PyJWTError as exc:
        raise AppError("INVALID_TOKEN", "登录状态已失效", 401) from exc


def token_hash(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError("UNAUTHORIZED", "请先登录", 401)
    payload = decode_token(authorization[7:], "access")
    user = db.scalar(select(User).where(User.id == payload["sub"]))
    if not user or not user.is_active or user.status != "active":
        raise AppError("ACCOUNT_UNAVAILABLE", "账号不可用或仍在审核", 403)
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise AppError("FORBIDDEN", "需要管理员权限", 403)
    return user

