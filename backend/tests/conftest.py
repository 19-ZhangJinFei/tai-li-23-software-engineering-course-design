import os
from pathlib import Path

TEST_DB = Path(__file__).parent / "test-course-ai.db"
TEST_UPLOADS = Path(__file__).parent / "uploads"
TEST_DB.unlink(missing_ok=True)
os.environ.update({
    "DATABASE_URL": f"sqlite:///{TEST_DB.as_posix()}",
    "STORAGE_MODE": "local",
    "LOCAL_STORAGE_PATH": str(TEST_UPLOADS),
    "AI_MODE": "fake",
    "AUTO_APPROVE_REGISTRATION": "true",
    "APP_SECRET": "test-secret",
})

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def admin_headers(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@demo.com", "password": "Admin@123456"
    })
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.fixture(scope="session")
def student_headers(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "student@demo.com", "password": "Student@123456"
    })
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}
