"""对话管理路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from auth.router import get_current_user

router = APIRouter(prefix="/api/chat", tags=["智能问答"])
chat_engine_instance = None


def init_chat_engine(engine):
    global chat_engine_instance
    chat_engine_instance = engine


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户的问题", examples=["阿司匹林的副作用是什么？"])
    session_id: Optional[str] = Field(None, description="会话ID，首次对话不传")


class ChatSource(BaseModel):
    filename: str
    page: Optional[str] = None
    text: str
    score: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list = Field(default=[])
    session_id: str


class SessionResponse(BaseModel):
    session_id: str
    message: str = "会话创建成功"


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    if chat_engine_instance is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="RAG引擎尚未初始化，请先上传文档并构建知识库")
    try:
        result = chat_engine_instance.chat(message=request.message, session_id=request.session_id)
        return ChatResponse(answer=result["answer"], sources=result.get("sources", []),
                            session_id=result["session_id"])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"问答处理失败: {str(e)}")


@router.post("/session", response_model=SessionResponse)
async def create_session(current_user: dict = Depends(get_current_user)):
    if chat_engine_instance is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG引擎尚未初始化")
    session_id = chat_engine_instance.create_session()
    return SessionResponse(session_id=session_id)


@router.get("/history/{session_id}")
async def get_history(session_id: str, current_user: dict = Depends(get_current_user)):
    if chat_engine_instance is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG引擎尚未初始化")
    history = chat_engine_instance.get_chat_history(session_id)
    return {"session_id": session_id, "messages": history, "total": len(history)}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str, current_user: dict = Depends(get_current_user)):
    if chat_engine_instance is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG引擎尚未初始化")
    chat_engine_instance.clear_session(session_id)
    return {"message": f"会话 {session_id} 的历史已清除"}


@router.get("/sessions")
async def list_sessions(current_user: dict = Depends(get_current_user)):
    if chat_engine_instance is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG引擎尚未初始化")
    sessions = chat_engine_instance.list_sessions()
    return {"sessions": sessions, "total": len(sessions)}


@router.get("/status")
async def get_status(current_user: dict = Depends(get_current_user)):
    if chat_engine_instance is None:
        return {"initialized": False, "message": "RAG引擎未初始化，请上传文档并构建知识库"}
    return {"initialized": True, "sessions": len(chat_engine_instance.list_sessions()), "message": "RAG引擎运行中"}
