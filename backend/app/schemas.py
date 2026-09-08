from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=72)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class CourseIn(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    is_published: bool = True


class CoursePatch(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    is_published: bool | None = None


class JoinCourseIn(BaseModel):
    code: str


class MemberIn(BaseModel):
    email: EmailStr


class UploadUrlIn(BaseModel):
    course_id: str
    filename: str
    mime_type: str
    size_bytes: int


class DocumentRegisterIn(BaseModel):
    original_name: str
    storage_key: str
    mime_type: str
    size_bytes: int
    checksum: str


class ConversationIn(BaseModel):
    course_id: str
    title: str = "新对话"


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class QuizGenerateIn(BaseModel):
    count: Literal[5, 10] = 5


class QuizSubmitIn(BaseModel):
    answers: list[int]


class FeedbackIn(BaseModel):
    rating: Literal[-1, 1]
    comment: str = Field(default="", max_length=500)


class UserStatusIn(BaseModel):
    status: Literal["pending", "active", "rejected"]
    is_active: bool = True

