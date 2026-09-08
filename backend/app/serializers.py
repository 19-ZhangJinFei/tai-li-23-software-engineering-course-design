from datetime import datetime


def iso(value):
    return value.isoformat() if isinstance(value, datetime) else value


def user_dict(user):
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "role": user.role,
            "status": user.status, "is_active": user.is_active, "created_at": iso(user.created_at)}


def course_dict(course, member_count=0, document_count=0):
    return {"id": course.id, "code": course.code, "title": course.title, "description": course.description,
            "owner_id": course.owner_id, "is_published": course.is_published, "member_count": member_count,
            "document_count": document_count, "created_at": iso(course.created_at)}


def document_dict(doc):
    return {"id": doc.id, "course_id": doc.course_id, "original_name": doc.original_name,
            "mime_type": doc.mime_type, "size_bytes": doc.size_bytes, "checksum": doc.checksum,
            "status": doc.status, "error_message": doc.error_message, "chunk_count": doc.chunk_count,
            "created_at": iso(doc.created_at), "processed_at": iso(doc.processed_at)}


def conversation_dict(conv):
    return {"id": conv.id, "course_id": conv.course_id, "title": conv.title,
            "created_at": iso(conv.created_at), "updated_at": iso(conv.updated_at)}


def message_dict(message):
    return {"id": message.id, "conversation_id": message.conversation_id, "role": message.role,
            "content": message.content, "citations": message.citations, "model": message.model,
            "latency_ms": message.latency_ms, "created_at": iso(message.created_at)}

