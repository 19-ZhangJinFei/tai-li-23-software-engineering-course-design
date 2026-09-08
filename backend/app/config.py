from functools import lru_cache
import os
from pathlib import Path
from urllib.parse import urlsplit
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
    storage_endpoint: str = ""
    storage_public_endpoint: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    storage_region: str = "us-east-1"
    max_upload_mb: int = 25
    local_storage_path: Path = Path("/tmp/uploads") if os.getenv("VERCEL") else Path("./data/uploads")

    access_token_minutes: int = 30
    refresh_token_days: int = 7

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def sqlalchemy_database_url(self) -> str:
        """Use psycopg 3 when a provider returns a generic PostgreSQL URL."""
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url

    @property
    def uses_transaction_pooler(self) -> bool:
        if self.is_sqlite:
            return False
        parsed = urlsplit(self.sqlalchemy_database_url.replace("postgresql+psycopg", "postgresql", 1))
        return parsed.port == 6543 or ".pooler.supabase.com" in (parsed.hostname or "")

    def validate_runtime(self) -> None:
        if os.getenv("VERCEL") and self.app_env == "production" and self.is_sqlite:
            raise RuntimeError("Production on Vercel requires a persistent PostgreSQL DATABASE_URL")
        if self.app_env == "production" and (self.app_secret == "development-only-secret" or len(self.app_secret) < 32):
            raise RuntimeError("Production requires APP_SECRET with at least 32 characters")
        if self.ai_mode == "dashscope" and not self.dashscope_api_key:
            raise RuntimeError("AI_MODE=dashscope requires DASHSCOPE_API_KEY")
        if self.storage_mode == "s3":
            missing = [
                name for name, value in {
                    "STORAGE_BUCKET": self.storage_bucket,
                    "STORAGE_ENDPOINT": self.storage_endpoint,
                    "STORAGE_PUBLIC_ENDPOINT": self.storage_public_endpoint,
                    "STORAGE_ACCESS_KEY": self.storage_access_key,
                    "STORAGE_SECRET_KEY": self.storage_secret_key,
                }.items() if not value
            ]
            if missing:
                raise RuntimeError(f"Missing S3 configuration: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
