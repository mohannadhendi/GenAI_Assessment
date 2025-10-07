from sqlalchemy import Column, Integer, String, Text, DateTime, func
from server.db import Base

class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    name = Column(String, nullable=False)
    args_json = Column(Text, nullable=False)
    result_json = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
