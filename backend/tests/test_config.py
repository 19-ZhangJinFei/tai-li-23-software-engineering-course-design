from app.config import Settings


def test_generic_postgres_url_uses_psycopg_and_detects_transaction_pooler():
    config = Settings(database_url=(
        "postgresql://postgres.example:password@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
    ))

    assert config.sqlalchemy_database_url.startswith("postgresql+psycopg://")
    assert config.uses_transaction_pooler is True


def test_production_rejects_weak_secret(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    config = Settings(
        app_env="production",
        database_url="postgresql://user:password@db.example.com:5432/postgres",
        app_secret="too-short",
    )

    try:
        config.validate_runtime()
    except RuntimeError as exc:
        assert "APP_SECRET" in str(exc)
    else:
        raise AssertionError("weak production secret should be rejected")
