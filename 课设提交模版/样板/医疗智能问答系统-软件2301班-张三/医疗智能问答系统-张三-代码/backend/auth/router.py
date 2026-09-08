"""认证路由"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth.models import UserCreate, UserLogin, UserOut, Token
from auth.password import hash_password, verify_password
from auth.jwt_handler import create_access_token, decode_access_token
from database import create_user, get_user_by_username, get_user_by_id

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token无效或已过期",
                            headers={"WWW-Authenticate": "Bearer"})
    user_id = payload.get("sub")
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    existing_user = get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    password_hash = hash_password(user.password)
    new_user = create_user(user.username, password_hash)
    return new_user


@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    db_user = get_user_by_username(user.username)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    access_token = create_access_token(db_user["id"], db_user["username"])
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
