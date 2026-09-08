from functools import lru_cache
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    app_env: str = "development"
    app_secret: str = "development-only-secret"
    database_url: str = "sqlite:////tmp/course_ai.db" if os.getenv("VERCEL") else "sqlite:///./data/course_ai.db"
    frontend_origin: str = "http://localhost:5173"
    auto_approve_registration: bool = True
    demo_admin_email: str = "admin@demo.com"
    demo_admin_password: str = "Admin@123456"
    demo_student_email: str = "student@demo.com"
    demo_student_password: str = "Student@123456"

    ai_mode: str = "fake"
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_chat_model: str = "qwen-plus"
    dashscope_embedding_model: str = "text-embedding-v4"
    embedding_dimension: int = 1024
    rag_similarity_threshold: float = 0.35

    storage_mode: str = "local"
    storage_bucket: str = "course-documents"
    storage_endpoint: str = "http://localhost:9000"
    storage_public_endpoint: str = "http://localhost:9000"
    storage_access_key: str = "minioadmin"
    storage_secret_key: str = "minioadmin"
    storage_region: str = "us-east-1"
    max_upload_mb: int = 25
    local_storage_path: Path = Path("/tmp/uploads") if os.getenv("VERCEL") else Path("./data/uploads")

    access_token_minutes: int = 30
    refresh_token_days: int = 7

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
