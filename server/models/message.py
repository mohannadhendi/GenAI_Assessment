from sqlalchemy import Column, Integer, String, Text, DateTime, func
from server.db import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String, nullable=False)  # "user" | "assistant" | "tool"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
