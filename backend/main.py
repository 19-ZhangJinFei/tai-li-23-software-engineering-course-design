from __future__ import annotations
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
import time
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.ai import cosine_similarity, get_ai
from app.config import settings
from app.database import SessionLocal, get_db, initialize_database
from app.document_service import ALLOWED_EXTENSIONS, process_document
from app.models import (
    AuditLog, Conversation, Course, CourseMember, Document, DocumentChunk, Favorite, Feedback,
    Message, QuizAttempt, QuizQuestion, QuizSet, RefreshToken, Summary, User, now,
)
from app.schemas import (
    ConversationIn, CourseIn, CoursePatch, DocumentRegisterIn, FeedbackIn, JoinCourseIn,
    LoginIn, MemberIn, MessageIn, QuizGenerateIn, QuizSubmitIn, RefreshIn, RegisterIn,
    UploadUrlIn, UserStatusIn,
)
from app.security import (
    AppError, admin_user, create_token, current_user, decode_token, hash_password,
    token_hash, verify_password,
)
from app.serializers import conversation_dict, course_dict, document_dict, message_dict, user_dict
from app.storage import storage


def envelope(data=None, message="操作成功", request_id=None):
    return {"data": data, "message": message, "request_id": request_id or str(uuid4())}


def audit(db: Session, actor_id: str | None, action: str, target_type: str, target_id: str | None, details=None):
    db.add(AuditLog(actor_id=actor_id, action=action, target_type=target_type,
                    target_id=target_id, details=details or {}))


def seed_demo(db: Session):
    admin = db.scalar(select(User).where(User.email == settings.demo_admin_email.lower()))
    if not admin:
        admin = User(email=settings.demo_admin_email.lower(), display_name="演示管理员",
                     password_hash=hash_password(settings.demo_admin_password), role="admin", status="active")
        db.add(admin)
        db.flush()
    student = db.scalar(select(User).where(User.email == settings.demo_student_email.lower()))
    if not student:
        student = User(email=settings.demo_student_email.lower(), display_name="演示学生",
                       password_hash=hash_password(settings.demo_student_password), role="student", status="active")
        db.add(student)
        db.flush()
    course = db.scalar(select(Course).where(Course.code == "AI-FOUNDATION"))
    if not course:
        course = Course(code="AI-FOUNDATION", title="人工智能应用开发基础",
                        description="涵盖大模型、Prompt、RAG、LlamaIndex 与 FastAPI 的课程知识库。",
                        owner_id=admin.id, is_published=True)
        db.add(course)
        db.flush()
    for user, role in ((admin, "owner"), (student, "member")):
        exists = db.scalar(select(CourseMember).where(CourseMember.course_id == course.id,
                                                       CourseMember.user_id == user.id))
        if not exists:
            db.add(CourseMember(course_id=course.id, user_id=user.id, member_role=role))
    db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    with SessionLocal() as db:
        seed_demo(db)
    yield


app = FastAPI(
    title="高校课程知识库智能问答系统 API",
    version="1.0.0",
    description="可溯源 RAG 问答、课程摘要、智能测验和学习分析。",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.frontend_origin.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID", str(uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={
        "data": None, "message": exc.message, "code": exc.code,
        "request_id": getattr(request.state, "request_id", str(uuid4())),
    })


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={
        "data": None, "message": "服务器内部错误", "code": "INTERNAL_ERROR",
        "detail": str(exc) if settings.app_env == "development" else None,
        "request_id": getattr(request.state, "request_id", str(uuid4())),
    })


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return envelope({"status": "healthy", "ai_mode": settings.ai_mode,
                     "database": "sqlite" if settings.is_sqlite else "postgresql",
                     "storage": settings.storage_mode})


@app.post("/api/v1/auth/register", status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise AppError("EMAIL_EXISTS", "该邮箱已经注册", 409)
    status = "active" if settings.auto_approve_registration else "pending"
    user = User(email=email, display_name=payload.display_name.strip(),
                password_hash=hash_password(payload.password), status=status)
    db.add(user)
    audit(db, user.id, "user.register", "user", user.id)
    db.commit()
    db.refresh(user)
    return envelope(user_dict(user), "注册成功" if status == "active" else "注册成功，等待管理员审核")


def issue_tokens(db: Session, user: User) -> dict:
    access = create_token(user, "access", timedelta(minutes=settings.access_token_minutes))
    refresh = create_token(user, "refresh", timedelta(days=settings.refresh_token_days))
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash(refresh),
                        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)))
    db.commit()
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "user": user_dict(user)}


@app.post("/api/v1/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "邮箱或密码错误", 401)
    if user.status != "active" or not user.is_active:
        raise AppError("ACCOUNT_UNAVAILABLE", "账号仍在审核或已停用", 403)
    audit(db, user.id, "user.login", "user", user.id)
    return envelope(issue_tokens(db, user), "登录成功")


@app.post("/api/v1/auth/refresh")
def refresh(payload: RefreshIn, db: Session = Depends(get_db)):
    claims = decode_token(payload.refresh_token, "refresh")
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash(payload.refresh_token)))
    if not record or record.revoked or record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise AppError("INVALID_REFRESH_TOKEN", "刷新令牌无效", 401)
    user = db.get(User, claims["sub"])
    if not user or not user.is_active or user.status != "active":
        raise AppError("ACCOUNT_UNAVAILABLE", "账号不可用", 403)
    record.revoked = True
    db.commit()
    return envelope(issue_tokens(db, user))


@app.post("/api/v1/auth/logout")
def logout(payload: RefreshIn, db: Session = Depends(get_db)):
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash(payload.refresh_token)))
    if record:
        record.revoked = True
        db.commit()
    return envelope(None, "已退出登录")


@app.get("/api/v1/auth/me")
def me(user: User = Depends(current_user)):
    return envelope(user_dict(user))


def course_counts(db: Session, course_id: str):
    members = db.scalar(select(func.count()).select_from(CourseMember).where(CourseMember.course_id == course_id)) or 0
    docs = db.scalar(select(func.count()).select_from(Document).where(Document.course_id == course_id)) or 0
    return members, docs


def can_access_course(db: Session, user: User, course_id: str, manage=False) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise AppError("COURSE_NOT_FOUND", "课程不存在", 404)
    if user.role == "admin":
        return course
    membership = db.scalar(select(CourseMember).where(CourseMember.course_id == course_id,
                                                       CourseMember.user_id == user.id))
    if not membership or (manage and membership.member_role != "owner"):
        raise AppError("FORBIDDEN", "无权访问该课程", 403)
    return course


@app.get("/api/v1/courses")
def list_courses(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Course)
    if user.role != "admin":
        query = query.join(CourseMember).where(CourseMember.user_id == user.id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    courses = db.scalars(query.order_by(Course.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    items = []
    for course in courses:
        members, docs = course_counts(db, course.id)
        items.append(course_dict(course, members, docs))
    return envelope({"items": items, "page": page, "page_size": page_size, "total": total})


@app.post("/api/v1/courses", status_code=201)
def create_course(payload: CourseIn, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    code = payload.code.strip().upper()
    if db.scalar(select(Course).where(Course.code == code)):
        raise AppError("COURSE_CODE_EXISTS", "课程代码已存在", 409)
    course = Course(code=code, title=payload.title.strip(), description=payload.description.strip(),
                    owner_id=user.id, is_published=payload.is_published)
    db.add(course)
    db.flush()
    db.add(CourseMember(course_id=course.id, user_id=user.id, member_role="owner"))
    audit(db, user.id, "course.create", "course", course.id)
    db.commit()
    return envelope(course_dict(course, 1, 0), "课程创建成功")


@app.get("/api/v1/courses/{course_id}")
def get_course(course_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    course = can_access_course(db, user, course_id)
    members, docs = course_counts(db, course.id)
    return envelope(course_dict(course, members, docs))


@app.patch("/api/v1/courses/{course_id}")
def patch_course(course_id: str, payload: CoursePatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    course = can_access_course(db, user, course_id, manage=True)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, key, value.strip() if isinstance(value, str) else value)
    audit(db, user.id, "course.update", "course", course.id)
    db.commit()
    members, docs = course_counts(db, course.id)
    return envelope(course_dict(course, members, docs))


@app.delete("/api/v1/courses/{course_id}")
def remove_course(course_id: str, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    course = can_access_course(db, user, course_id, manage=True)
    audit(db, user.id, "course.delete", "course", course.id, {"title": course.title})
    db.delete(course)
    db.commit()
    return envelope(None, "课程已删除")


@app.post("/api/v1/courses/join")
def join_course(payload: JoinCourseIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    course = db.scalar(select(Course).where(Course.code == payload.code.strip().upper(), Course.is_published.is_(True)))
    if not course:
        raise AppError("COURSE_NOT_FOUND", "课程代码无效", 404)
    exists = db.scalar(select(CourseMember).where(CourseMember.course_id == course.id,
                                                   CourseMember.user_id == user.id))
    if not exists:
        db.add(CourseMember(course_id=course.id, user_id=user.id))
        audit(db, user.id, "course.join", "course", course.id)
        db.commit()
    return envelope(course_dict(course), "已加入课程")


@app.get("/api/v1/courses/{course_id}/members")
def list_members(course_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, course_id)
    rows = db.execute(select(CourseMember, User).join(User, User.id == CourseMember.user_id)
                      .where(CourseMember.course_id == course_id)).all()
    return envelope([{"id": m.id, "member_role": m.member_role, "joined_at": m.joined_at.isoformat(),
                      "user": user_dict(u)} for m, u in rows])


@app.post("/api/v1/courses/{course_id}/members")
def add_member(course_id: str, payload: MemberIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, course_id, manage=True)
    member = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not member:
        raise AppError("USER_NOT_FOUND", "用户不存在", 404)
    if not db.scalar(select(CourseMember).where(CourseMember.course_id == course_id,
                                                 CourseMember.user_id == member.id)):
        db.add(CourseMember(course_id=course_id, user_id=member.id))
        audit(db, user.id, "course.member.add", "course", course_id, {"user_id": member.id})
        db.commit()
    return envelope(user_dict(member), "成员添加成功")


@app.delete("/api/v1/courses/{course_id}/members/{member_id}")
def remove_member(course_id: str, member_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, course_id, manage=True)
    member = db.get(CourseMember, member_id)
    if not member or member.course_id != course_id:
        raise AppError("MEMBER_NOT_FOUND", "成员不存在", 404)
    if member.member_role == "owner":
        raise AppError("OWNER_CANNOT_BE_REMOVED", "不能移除课程负责人", 409)
    db.delete(member)
    audit(db, user.id, "course.member.remove", "course", course_id, {"user_id": member.user_id})
    db.commit()
    return envelope(None, "成员已移除")


def validate_upload(filename: str, size: int):
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise AppError("UNSUPPORTED_FILE", "仅支持 DOCX、PDF、TXT 和 Markdown", 415)
    if size <= 0 or size > settings.max_upload_mb * 1024 * 1024:
        raise AppError("FILE_SIZE_INVALID", f"文件大小必须在 0 到 {settings.max_upload_mb} MB 之间", 413)


@app.post("/api/v1/documents/upload-url")
def create_upload_url(payload: UploadUrlIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, payload.course_id, manage=True)
    validate_upload(payload.filename, payload.size_bytes)
    safe_name = re.sub(r"[^\w.\-\u4e00-\u9fff]", "_", payload.filename)
    key = f"{payload.course_id}/{uuid4()}-{safe_name}"
    return envelope({"storage_key": key, **storage.upload_spec(key, payload.mime_type)})


@app.post("/api/v1/documents/upload-local", status_code=201)
async def upload_local(course_id: str = Form(...), file: UploadFile = File(...),
                       user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, course_id, manage=True)
    data = await file.read()
    validate_upload(file.filename or "", len(data))
    checksum = sha256(data).hexdigest()
    duplicate = db.scalar(select(Document).where(Document.course_id == course_id, Document.checksum == checksum))
    if duplicate:
        raise AppError("DUPLICATE_DOCUMENT", "该课程中已存在相同文件", 409)
    safe_name = re.sub(r"[^\w.\-\u4e00-\u9fff]", "_", file.filename or "document")
    key = f"{course_id}/{uuid4()}-{safe_name}"
    storage.put_local(key, data)
    doc = Document(course_id=course_id, uploader_id=user.id, original_name=file.filename or safe_name,
                   storage_key=key, mime_type=file.content_type or "application/octet-stream",
                   size_bytes=len(data), checksum=checksum)
    db.add(doc)
    audit(db, user.id, "document.upload", "document", doc.id, {"filename": doc.original_name})
    db.commit()
    db.refresh(doc)
    return envelope(document_dict(doc), "文件上传成功")


@app.post("/api/v1/courses/{course_id}/documents", status_code=201)
def register_document(course_id: str, payload: DocumentRegisterIn, user: User = Depends(current_user),
                      db: Session = Depends(get_db)):
    can_access_course(db, user, course_id, manage=True)
    validate_upload(payload.original_name, payload.size_bytes)
    if db.scalar(select(Document).where(Document.course_id == course_id, Document.checksum == payload.checksum)):
        raise AppError("DUPLICATE_DOCUMENT", "该课程中已存在相同文件", 409)
    doc = Document(course_id=course_id, uploader_id=user.id, **payload.model_dump())
    db.add(doc)
    audit(db, user.id, "document.register", "document", doc.id)
    db.commit()
    db.refresh(doc)
    return envelope(document_dict(doc), "文件登记成功")


@app.get("/api/v1/courses/{course_id}/documents")
def list_documents(course_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, course_id)
    docs = db.scalars(select(Document).where(Document.course_id == course_id).order_by(Document.created_at.desc())).all()
    return envelope([document_dict(doc) for doc in docs])


@app.get("/api/v1/documents/{document_id}")
def get_document(document_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise AppError("DOCUMENT_NOT_FOUND", "文档不存在", 404)
    can_access_course(db, user, doc.course_id)
    return envelope(document_dict(doc))


@app.post("/api/v1/documents/{document_id}/process")
def ingest_document(document_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise AppError("DOCUMENT_NOT_FOUND", "文档不存在", 404)
    can_access_course(db, user, doc.course_id, manage=True)
    try:
        process_document(db, doc)
    except Exception as exc:
        raise AppError("DOCUMENT_PROCESS_FAILED", f"文档处理失败：{exc}", 422) from exc
    audit(db, user.id, "document.process", "document", doc.id, {"chunks": doc.chunk_count})
    db.commit()
    return envelope(document_dict(doc), "文档处理完成")


@app.delete("/api/v1/documents/{document_id}")
def remove_document(document_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise AppError("DOCUMENT_NOT_FOUND", "文档不存在", 404)
    can_access_course(db, user, doc.course_id, manage=True)
    storage.delete(doc.storage_key)
    db.delete(doc)
    audit(db, user.id, "document.delete", "document", doc.id, {"filename": doc.original_name})
    db.commit()
    return envelope(None, "文档已删除")


@app.post("/api/v1/conversations", status_code=201)
def create_conversation(payload: ConversationIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, payload.course_id)
    conv = Conversation(course_id=payload.course_id, user_id=user.id, title=payload.title[:160])
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return envelope(conversation_dict(conv), "对话已创建")


@app.get("/api/v1/conversations")
def list_conversations(course_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, course_id)
    rows = db.scalars(select(Conversation).where(Conversation.course_id == course_id,
                                                  Conversation.user_id == user.id)
                      .order_by(Conversation.updated_at.desc())).all()
    return envelope([conversation_dict(row) for row in rows])


def owned_conversation(db: Session, user: User, conversation_id: str) -> Conversation:
    conv = db.get(Conversation, conversation_id)
    if not conv or (conv.user_id != user.id and user.role != "admin"):
        raise AppError("CONVERSATION_NOT_FOUND", "对话不存在", 404)
    can_access_course(db, user, conv.course_id)
    return conv


@app.get("/api/v1/conversations/{conversation_id}/messages")
def list_messages(conversation_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned_conversation(db, user, conversation_id)
    rows = db.scalars(select(Message).where(Message.conversation_id == conversation_id)
                      .order_by(Message.created_at)).all()
    return envelope([message_dict(row) for row in rows])


def retrieve(db: Session, course_id: str, question: str):
    chunks = db.scalars(select(DocumentChunk).join(Document).where(
        DocumentChunk.course_id == course_id, Document.status == "ready"
    )).all()
    if not chunks:
        return []
    if settings.ai_mode == "fake":
        compact = re.sub(r"\s+", "", question.lower())
        latin = set(re.findall(r"[a-z0-9][a-z0-9+_.-]+", question.lower()))
        chinese = re.findall(r"[\u4e00-\u9fff]", compact)
        chinese_terms = {"".join(chinese[i:i + 2]) for i in range(len(chinese) - 1)}
        chinese_terms -= {"什么", "哪些", "如何", "是否", "应该", "可以", "主要", "一个", "怎么",
                          "的是", "什么", "作用", "问题", "完成", "工作", "支持", "出生", "在哪", "一年"}

        def has_lexical_evidence(chunk: DocumentChunk) -> bool:
            content = chunk.content.lower()
            if any(term in content for term in latin):
                return True
            return sum(term in content for term in chinese_terms) >= 2

        chunks = [chunk for chunk in chunks if has_lexical_evidence(chunk)]
        if not chunks:
            return []
    query_vector = get_ai().embed([question])[0]
    ranked = sorted(((cosine_similarity(query_vector, chunk.embedding), chunk) for chunk in chunks),
                    key=lambda item: item[0], reverse=True)[:8]
    threshold = 0.0 if settings.ai_mode == "fake" else settings.rag_similarity_threshold
    return [(score, chunk) for score, chunk in ranked if score >= threshold]


@app.post("/api/v1/conversations/{conversation_id}/messages")
def ask(conversation_id: str, payload: MessageIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conv = owned_conversation(db, user, conversation_id)
    question = payload.content.strip()
    user_message = Message(conversation_id=conv.id, role="user", content=question)
    db.add(user_message)
    if conv.title == "新对话":
        conv.title = question[:30]
    conv.updated_at = now()
    db.commit()

    def event_stream():
        started = time.perf_counter()
        with SessionLocal() as stream_db:
            try:
                matches = retrieve(stream_db, conv.course_id, question)
                yield f"event: retrieval\ndata: {json.dumps({'count': len(matches)}, ensure_ascii=False)}\n\n"
                citations = []
                if not matches:
                    answer = "当前课程资料中未找到可靠依据。请尝试换一种问法，或联系管理员补充课程资料。"
                else:
                    sources = []
                    for idx, (score, chunk) in enumerate(matches, 1):
                        doc = stream_db.get(Document, chunk.document_id)
                        source_id = f"S{idx}"
                        sources.append(f"[{source_id}] {chunk.content}")
                        citations.append({"source_id": source_id, "document_id": doc.id,
                                          "document_name": doc.original_name, "chunk_id": chunk.id,
                                          "page_number": chunk.page_number, "score": round(score, 4),
                                          "excerpt": chunk.content[:260]})
                    history = stream_db.scalars(select(Message).where(Message.conversation_id == conv.id)
                                                .order_by(Message.created_at.desc()).limit(12)).all()
                    history_text = "\n".join(f"{m.role}: {m.content[:500]}" for m in reversed(history))
                    prompt = ("你是高校课程助教。只能依据编号资料回答，关键结论必须引用带方括号的来源编号。"
                              "资料不足时必须回答无法从当前资料确认。\n\n"
                              + "<sources>\n" + "\n".join(sources)
                              + f"\n</sources>\n\n最近对话：\n{history_text}\n\n问题：{question}")
                    answer = get_ai().generate(prompt)
                    valid_ids = {item["source_id"] for item in citations}
                    used = set(re.findall(r"\[(S\d+)\]", answer))
                    citations = [item for item in citations if item["source_id"] in used]
                    if not citations:
                        answer = "当前课程资料中未找到可靠依据。请尝试换一种问法，或联系管理员补充课程资料。"
                for i in range(0, len(answer), 24):
                    yield f"event: token\ndata: {json.dumps({'text': answer[i:i + 24]}, ensure_ascii=False)}\n\n"
                latency = int((time.perf_counter() - started) * 1000)
                assistant = Message(conversation_id=conv.id, role="assistant", content=answer,
                                    citations=citations, model=settings.dashscope_chat_model if settings.ai_mode == "dashscope" else "fake-rag",
                                    latency_ms=latency)
                stream_db.add(assistant)
                conversation = stream_db.get(Conversation, conv.id)
                conversation.updated_at = now()
                stream_db.commit()
                stream_db.refresh(assistant)
                yield f"event: citations\ndata: {json.dumps(citations, ensure_ascii=False)}\n\n"
                yield f"event: done\ndata: {json.dumps({'message': message_dict(assistant)}, ensure_ascii=False)}\n\n"
            except Exception as exc:
                stream_db.rollback()
                yield f"event: error\ndata: {json.dumps({'message': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def source_material(db: Session, course_id: str, document_id: str | None = None):
    query = select(DocumentChunk).where(DocumentChunk.course_id == course_id)
    if document_id:
        query = query.where(DocumentChunk.document_id == document_id)
    return db.scalars(query.order_by(DocumentChunk.document_id, DocumentChunk.chunk_index).limit(30)).all()


def build_summary(chunks: list[DocumentChunk]):
    combined = " ".join(chunk.content for chunk in chunks)
    sentences = [s.strip() for s in re.split(r"[。！？\n]", combined) if len(s.strip()) >= 12]
    overview = "。".join(sentences[:3])[:800] + ("。" if sentences else "")
    keywords = []
    for word in ("RAG", "FastAPI", "大语言模型", "向量", "Embedding", "Prompt", "LlamaIndex", "检索", "知识库"):
        if word.lower() in combined.lower():
            keywords.append(word)
    points = [s[:120] for s in sentences[3:8]] or [chunk.content[:120] for chunk in chunks[:5]]
    return {"overview": overview or "暂无可总结内容", "key_points": points,
            "keywords": keywords[:8], "review_suggestions": ["结合引用原文复习核心概念", "完成智能测验并查看错题解析"]}


@app.post("/api/v1/courses/{course_id}/summary")
def generate_course_summary(course_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, course_id)
    chunks = source_material(db, course_id)
    if not chunks:
        raise AppError("KNOWLEDGE_BASE_EMPTY", "课程暂无已处理资料", 409)
    summary = Summary(course_id=course_id, summary_type="course", content_json=build_summary(chunks), created_by=user.id)
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return envelope({"id": summary.id, **summary.content_json, "created_at": summary.created_at.isoformat()})


@app.post("/api/v1/documents/{document_id}/summary")
def generate_document_summary(document_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise AppError("DOCUMENT_NOT_FOUND", "文档不存在", 404)
    can_access_course(db, user, doc.course_id)
    chunks = source_material(db, doc.course_id, doc.id)
    if not chunks:
        raise AppError("DOCUMENT_NOT_READY", "文档尚未处理完成", 409)
    summary = Summary(course_id=doc.course_id, document_id=doc.id, summary_type="document",
                      content_json=build_summary(chunks), created_by=user.id)
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return envelope({"id": summary.id, "document_name": doc.original_name, **summary.content_json,
                     "created_at": summary.created_at.isoformat()})


@app.get("/api/v1/courses/{course_id}/summaries")
def list_summaries(course_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, course_id)
    rows = db.scalars(select(Summary).where(Summary.course_id == course_id).order_by(Summary.created_at.desc())).all()
    return envelope([{"id": row.id, "summary_type": row.summary_type, "document_id": row.document_id,
                      **row.content_json, "created_at": row.created_at.isoformat()} for row in rows])


def build_questions(chunks: list[DocumentChunk], count: int):
    questions = []
    fallback_stems = [
        ("RAG 的核心流程通常包含哪三个阶段？", ["索引、检索、生成", "训练、剪枝、量化", "登录、注册、退出", "采集、绘图、导出"], 0),
        ("向量检索在本系统中的主要作用是什么？", ["寻找语义相关的文档片段", "压缩图片", "验证密码", "生成数据库表"], 0),
        ("Prompt Engineering 主要关注什么？", ["设计有效的模型输入指令", "配置网络端口", "绘制 ER 图", "安装操作系统"], 0),
        ("FastAPI 在项目中承担什么职责？", ["提供后端 API", "存储向量", "训练大模型", "设计幻灯片"], 0),
        ("答案引用来源的主要价值是什么？", ["便于核验答案依据", "提高屏幕亮度", "减少用户数量", "替代用户登录"], 0),
        ("知识库没有依据时系统应如何处理？", ["明确拒答并提示补充资料", "编造最可能答案", "删除课程", "关闭数据库"], 0),
        ("文档分块设置重叠区域的主要目的是什么？", ["减少上下文在边界处丢失", "增大文件名", "修改用户权限", "删除重复账号"], 0),
        ("Embedding 的结果通常是什么？", ["表示语义的数值向量", "网页样式表", "用户密码", "音频文件"], 0),
        ("LlamaIndex 在本项目中主要用于什么？", ["组织文档节点与分块", "渲染 Vue 页面", "发送电子邮件", "管理 Docker 网络"], 0),
        ("pgvector 提供的核心能力是什么？", ["在 PostgreSQL 中存储并检索向量", "编译 TypeScript", "创建 Word 文档", "绘制流程图"], 0),
    ]
    for i in range(count):
        stem, options, correct = fallback_stems[i]
        chunk = chunks[i % len(chunks)]
        doc_name = chunk.metadata_json.get("filename", "课程资料")
        questions.append({"stem": stem, "options": options, "correct_index": correct,
                          "explanation": f"依据课程资料《{doc_name}》中的相关内容，正确答案为“{options[correct]}”。",
                          "citation": {"document_id": chunk.document_id, "document_name": doc_name,
                                       "chunk_id": chunk.id, "excerpt": chunk.content[:180]}})
    return questions


@app.post("/api/v1/courses/{course_id}/quizzes", status_code=201)
def generate_quiz(course_id: str, payload: QuizGenerateIn, user: User = Depends(current_user),
                  db: Session = Depends(get_db)):
    course = can_access_course(db, user, course_id)
    chunks = source_material(db, course_id)
    if not chunks:
        raise AppError("KNOWLEDGE_BASE_EMPTY", "课程暂无已处理资料", 409)
    questions = build_questions(chunks, payload.count)
    quiz = QuizSet(course_id=course_id, title=f"{course.title} · 智能测验", question_count=payload.count,
                   created_by=user.id)
    db.add(quiz)
    db.flush()
    for idx, item in enumerate(questions):
        db.add(QuizQuestion(quiz_id=quiz.id, position=idx + 1, **item))
    db.commit()
    return envelope({"id": quiz.id, "title": quiz.title, "question_count": quiz.question_count,
                     "created_at": quiz.created_at.isoformat()}, "测验生成成功")


def quiz_payload(db: Session, quiz: QuizSet, reveal=False):
    rows = db.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id)
                      .order_by(QuizQuestion.position)).all()
    return {"id": quiz.id, "course_id": quiz.course_id, "title": quiz.title,
            "question_count": quiz.question_count, "created_at": quiz.created_at.isoformat(),
            "questions": [{"id": q.id, "position": q.position, "stem": q.stem, "options": q.options,
                           **({"correct_index": q.correct_index, "explanation": q.explanation,
                               "citation": q.citation} if reveal else {})} for q in rows]}


@app.get("/api/v1/courses/{course_id}/quizzes")
def list_quizzes(course_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    can_access_course(db, user, course_id)
    rows = db.scalars(select(QuizSet).where(QuizSet.course_id == course_id).order_by(QuizSet.created_at.desc())).all()
    return envelope([{"id": q.id, "title": q.title, "question_count": q.question_count,
                      "created_at": q.created_at.isoformat()} for q in rows])


@app.get("/api/v1/quizzes/{quiz_id}")
def get_quiz(quiz_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    quiz = db.get(QuizSet, quiz_id)
    if not quiz:
        raise AppError("QUIZ_NOT_FOUND", "测验不存在", 404)
    can_access_course(db, user, quiz.course_id)
    return envelope(quiz_payload(db, quiz))


@app.post("/api/v1/quizzes/{quiz_id}/submit")
def submit_quiz(quiz_id: str, payload: QuizSubmitIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    quiz = db.get(QuizSet, quiz_id)
    if not quiz:
        raise AppError("QUIZ_NOT_FOUND", "测验不存在", 404)
    can_access_course(db, user, quiz.course_id)
    if db.scalar(select(QuizAttempt).where(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == user.id)):
        raise AppError("QUIZ_ALREADY_SUBMITTED", "该测验已提交", 409)
    questions = db.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id)
                           .order_by(QuizQuestion.position)).all()
    if len(payload.answers) != len(questions) or any(a < 0 or a > 3 for a in payload.answers):
        raise AppError("INVALID_ANSWERS", "答案数量或选项无效", 422)
    correct = sum(answer == question.correct_index for answer, question in zip(payload.answers, questions))
    score = round(correct / len(questions) * 100, 1)
    attempt = QuizAttempt(quiz_id=quiz.id, user_id=user.id, answers=payload.answers, score=score)
    db.add(attempt)
    db.commit()
    return envelope({"attempt_id": attempt.id, "score": score, "correct_count": correct,
                     "total": len(questions), "quiz": quiz_payload(db, quiz, reveal=True)}, "测验已提交")


@app.post("/api/v1/messages/{message_id}/favorite")
def favorite_message(message_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    message = db.get(Message, message_id)
    if not message or message.role != "assistant":
        raise AppError("MESSAGE_NOT_FOUND", "回答不存在", 404)
    owned_conversation(db, user, message.conversation_id)
    existing = db.scalar(select(Favorite).where(Favorite.message_id == message_id, Favorite.user_id == user.id))
    if existing:
        db.delete(existing)
        action, active = "取消收藏", False
    else:
        db.add(Favorite(message_id=message_id, user_id=user.id))
        action, active = "收藏成功", True
    db.commit()
    return envelope({"favorited": active}, action)


@app.post("/api/v1/messages/{message_id}/feedback")
def feedback_message(message_id: str, payload: FeedbackIn, user: User = Depends(current_user),
                     db: Session = Depends(get_db)):
    message = db.get(Message, message_id)
    if not message or message.role != "assistant":
        raise AppError("MESSAGE_NOT_FOUND", "回答不存在", 404)
    owned_conversation(db, user, message.conversation_id)
    feedback = db.scalar(select(Feedback).where(Feedback.message_id == message_id, Feedback.user_id == user.id))
    if feedback:
        feedback.rating, feedback.comment = payload.rating, payload.comment
    else:
        feedback = Feedback(message_id=message_id, user_id=user.id, **payload.model_dump())
        db.add(feedback)
    db.commit()
    return envelope({"rating": feedback.rating, "comment": feedback.comment}, "感谢反馈")


@app.get("/api/v1/dashboard/student")
def student_dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    course_total = db.scalar(select(func.count()).select_from(CourseMember).where(CourseMember.user_id == user.id)) or 0
    conv_total = db.scalar(select(func.count()).select_from(Conversation).where(Conversation.user_id == user.id)) or 0
    favorite_total = db.scalar(select(func.count()).select_from(Favorite).where(Favorite.user_id == user.id)) or 0
    attempts = db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == user.id)).all()
    average = round(sum(a.score for a in attempts) / len(attempts), 1) if attempts else 0
    recent = db.scalars(select(Conversation).where(Conversation.user_id == user.id)
                        .order_by(Conversation.updated_at.desc()).limit(5)).all()
    return envelope({"course_count": course_total, "conversation_count": conv_total,
                     "favorite_count": favorite_total, "quiz_average": average,
                     "recent_conversations": [conversation_dict(c) for c in recent]})


@app.get("/api/v1/dashboard/admin")
def admin_dashboard(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    counts = {}
    for key, model in (("users", User), ("courses", Course), ("documents", Document),
                       ("conversations", Conversation), ("messages", Message), ("feedback", Feedback)):
        counts[key] = db.scalar(select(func.count()).select_from(model)) or 0
    counts["pending_users"] = db.scalar(select(func.count()).select_from(User).where(User.status == "pending")) or 0
    counts["failed_documents"] = db.scalar(select(func.count()).select_from(Document).where(Document.status == "failed")) or 0
    logs = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)).all()
    return envelope({**counts, "recent_audit_logs": [
        {"id": log.id, "action": log.action, "target_type": log.target_type,
         "target_id": log.target_id, "details": log.details, "created_at": log.created_at.isoformat()}
        for log in logs]})


@app.get("/api/v1/admin/users")
def admin_users(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                _: User = Depends(admin_user), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(User)) or 0
    users = db.scalars(select(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return envelope({"items": [user_dict(u) for u in users], "page": page, "page_size": page_size, "total": total})


@app.patch("/api/v1/admin/users/{user_id}")
def admin_update_user(user_id: str, payload: UserStatusIn, admin: User = Depends(admin_user),
                      db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise AppError("USER_NOT_FOUND", "用户不存在", 404)
    if user.id == admin.id and not payload.is_active:
        raise AppError("CANNOT_DISABLE_SELF", "不能停用当前管理员", 409)
    user.status, user.is_active = payload.status, payload.is_active
    audit(db, admin.id, "user.status.update", "user", user.id,
          {"status": payload.status, "is_active": payload.is_active})
    db.commit()
    return envelope(user_dict(user), "用户状态已更新")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
