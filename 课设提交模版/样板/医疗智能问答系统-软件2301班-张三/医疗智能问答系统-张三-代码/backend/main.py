"""
基于RAG的医疗领域智能问答系统 - 后端入口
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from auth.router import router as auth_router
from documents.router import router as doc_router
from chat.router import router as chat_router, init_chat_engine
from rag.init_engine import initialize_rag_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    chat_engine = initialize_rag_engine()
    if chat_engine:
        init_chat_engine(chat_engine)
        print("✅ 对话引擎已注入API路由")
    else:
        print("⚠️ RAG引擎未初始化（请上传文档后重启）")
    yield
    print("🔄 应用正在关闭...")


app = FastAPI(
    title="医疗领域智能问答系统",
    description="基于RAG的医疗领域智能问答系统API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(doc_router)
app.include_router(chat_router)


@app.get("/", tags=["系统"])
async def root():
    return {"message": "医疗领域智能问答系统API正在运行", "docs": "访问 /docs 查看API文档", "version": "1.0.0"}


@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
