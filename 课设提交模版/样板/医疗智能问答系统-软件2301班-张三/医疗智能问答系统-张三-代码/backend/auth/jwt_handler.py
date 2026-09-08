"""JWT令牌生成与验证"""
import jwt
from datetime import datetime, timedelta, timezone
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS


def create_access_token(user_id: str, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": user_id, "username": username, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
