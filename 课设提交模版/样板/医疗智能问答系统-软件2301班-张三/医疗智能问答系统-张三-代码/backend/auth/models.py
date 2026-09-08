"""认证数据模型"""
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="用户名，3-20个字符", examples=["admin"])
    password: str = Field(..., min_length=6, max_length=50, description="密码，6-50个字符", examples=["123456"])


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserOut(BaseModel):
    id: str
    username: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
