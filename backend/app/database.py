from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool
from .config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.is_sqlite else {}
engine_options = {"pool_pre_ping": True, "connect_args": connect_args}
if settings.uses_transaction_pooler:
    # Supavisor transaction mode is designed for short-lived serverless clients.
    engine_options.update({"poolclass": NullPool, "connect_args": {"prepare_threshold": None}})
engine = create_engine(settings.sqlalchemy_database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


if settings.is_sqlite:
    @event.listens_for(engine, "connect")
    def _sqlite_fk(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_database() -> None:
    if not settings.is_sqlite:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
