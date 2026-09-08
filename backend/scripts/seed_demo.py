"""Import the four supplied teaching documents into the demo course through public APIs."""
from __future__ import annotations

import mimetypes
import os
from hashlib import sha256
from pathlib import Path

import httpx


BASE_URL = os.getenv("SEED_API_URL", "http://localhost:8000/api/v1")
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "课设提交模版" / "已经学过的知识点"
FILES = ["FastAPI.docx", "Prompt Engineering核心介绍.docx", "RAG基础.docx", "llama_index框架.docx"]


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=300) as client:
        login = client.post("/auth/login", json={
            "email": os.getenv("DEMO_ADMIN_EMAIL", "admin@demo.com"),
            "password": os.getenv("DEMO_ADMIN_PASSWORD", "Admin@123456"),
        })
        login.raise_for_status()
        headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
        courses = client.get("/courses", headers=headers).json()["data"]["items"]
        course = next(item for item in courses if item["code"] == "AI-FOUNDATION")
        existing = {item["original_name"] for item in client.get(
            f"/courses/{course['id']}/documents", headers=headers
        ).json()["data"]}

        for name in FILES:
            if name in existing:
                print(f"skip: {name}")
                continue
            path = SOURCE / name
            if not path.exists():
                print(f"missing: {path}")
                continue
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            content = path.read_bytes()
            upload_spec = client.post("/documents/upload-url", headers=headers, json={
                "course_id": course["id"], "filename": path.name,
                "mime_type": mime, "size_bytes": len(content),
            })
            upload_spec.raise_for_status()
            spec = upload_spec.json()["data"]
            if spec["mode"] == "presigned":
                uploaded = httpx.put(spec["url"], content=content, headers=spec.get("headers", {}), timeout=300)
                uploaded.raise_for_status()
                response = client.post(f"/courses/{course['id']}/documents", headers=headers, json={
                    "original_name": path.name, "storage_key": spec["storage_key"],
                    "mime_type": mime, "size_bytes": len(content),
                    "checksum": sha256(content).hexdigest(),
                })
            else:
                response = client.post(
                    "/documents/upload-local", headers=headers, data={"course_id": course["id"]},
                    files={"file": (path.name, content, mime)},
                )
            response.raise_for_status()
            document = response.json()["data"]
            process = client.post(f"/documents/{document['id']}/process", headers=headers)
            process.raise_for_status()
            print(f"ready: {name} ({process.json()['data']['chunk_count']} chunks)")


if __name__ == "__main__":
    main()
