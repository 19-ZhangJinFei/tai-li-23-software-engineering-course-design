"""文档管理路由"""
import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from auth.router import get_current_user
from database import add_document, get_all_documents, get_document, delete_document, update_document_status
from config import DATA_DIR
from datetime import datetime

try:
    from rag.init_engine import rebuild_index
    from chat.router import init_chat_engine
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
router = APIRouter(prefix="/api/documents", tags=["文档管理"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    filename = file.filename
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"不支持的文件类型: {ext}，仅支持: {', '.join(ALLOWED_EXTENSIONS)}")
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + filename
        file_path = os.path.join(DATA_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    file_size = os.path.getsize(file_path)
    doc = add_document(filename=filename, file_size=file_size, file_type=ext)
    update_document_status(doc["id"], "processing")
    if RAG_AVAILABLE:
        try:
            print("🔄 文档上传后自动重建知识库...")
            chat_engine = rebuild_index()
            if chat_engine:
                init_chat_engine(chat_engine)
                update_document_status(doc["id"], "ready")
                print("✅ 知识库重建完成")
            else:
                update_document_status(doc["id"], "error")
        except Exception as e:
            print(f"⚠️ 知识库重建失败: {e}")
            update_document_status(doc["id"], "error")
    return {"id": doc["id"], "filename": filename, "file_size": file_size, "file_type": ext,
            "upload_time": doc["upload_time"], "status": doc["status"], "message": "文件上传成功，知识库已更新"}


@router.get("/")
async def list_documents(current_user: dict = Depends(get_current_user)):
    docs = get_all_documents()
    return {"total": len(docs), "documents": [
        {"id": doc["id"], "filename": doc["filename"], "file_size": doc["file_size"],
         "file_type": doc["file_type"], "upload_time": doc["upload_time"], "status": doc["status"]}
        for doc in docs
    ]}


@router.delete("/{doc_id}")
async def remove_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    doc = get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    file_path = os.path.join(DATA_DIR, doc["filename"])
    if os.path.exists(file_path):
        os.remove(file_path)
    delete_document(doc_id)
    if RAG_AVAILABLE:
        try:
            chat_engine = rebuild_index()
            if chat_engine:
                init_chat_engine(chat_engine)
        except Exception as e:
            print(f"⚠️ 删除后知识库重建失败: {e}")
    return {"message": f"文档 {doc['filename']} 已删除，知识库已更新"}


@router.get("/{doc_id}")
async def get_document_info(doc_id: str, current_user: dict = Depends(get_current_user)):
    doc = get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    return doc
