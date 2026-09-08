"""简化版数据存储（使用内存字典）"""
from datetime import datetime
import uuid

users_db: dict[str, dict] = {}
documents_db: dict[str, dict] = {}
username_to_id: dict[str, str] = {}


def create_user(username: str, password_hash: str) -> dict:
    user_id = str(uuid.uuid4())
    user = {"id": user_id, "username": username, "password_hash": password_hash, "created_at": datetime.now()}
    users_db[user_id] = user
    username_to_id[username] = user_id
    return user


def get_user_by_username(username: str) -> dict | None:
    user_id = username_to_id.get(username)
    return users_db.get(user_id) if user_id else None


def get_user_by_id(user_id: str) -> dict | None:
    return users_db.get(user_id)


def add_document(filename: str, file_size: int, file_type: str) -> dict:
    doc_id = str(uuid.uuid4())
    doc = {"id": doc_id, "filename": filename, "file_size": file_size, "file_type": file_type,
           "upload_time": datetime.now(), "status": "pending"}
    documents_db[doc_id] = doc
    return doc


def get_all_documents() -> list[dict]:
    return list(documents_db.values())


def get_document(doc_id: str) -> dict | None:
    return documents_db.get(doc_id)


def delete_document(doc_id: str) -> bool:
    if doc_id in documents_db:
        del documents_db[doc_id]
        return True
    return False


def update_document_status(doc_id: str, status: str):
    if doc_id in documents_db:
        documents_db[doc_id]["status"] = status
