from fastapi import APIRouter
from sqlalchemy import func
from server.db import SessionLocal
from server.models.message import Message

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/")
def list_sessions():
    """List all chat sessions, sorted by most recent message timestamp."""
    db = SessionLocal()
    try:
        # Aggregate latest message per session
        sessions = (
            db.query(
                Message.session_id,
                func.max(Message.created_at).label("last_activity"),
            )
            .group_by(Message.session_id)
            .order_by(func.max(Message.created_at).desc())
            .all()
        )

        # Return structured results
        return [
            {
                "session_id": s.session_id,
                "last_activity": s.last_activity.isoformat() if s.last_activity else None,
            }
            for s in sessions
        ]
    finally:
        db.close()
