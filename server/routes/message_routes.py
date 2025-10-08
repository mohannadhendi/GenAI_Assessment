from fastapi import APIRouter
from server.db import SessionLocal
from server.models.message import Message

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.get("/{session_id}")
def get_messages(session_id: str):
    """Return structured messages for a session."""
    db = SessionLocal()
    try:
        messages = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        return [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in messages
        ]
    finally:
        db.close()
