from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class HitlSession(Base):
    __tablename__ = "hitl_sessions"

    id: str = Column(String(64), primary_key=True)
    topic: str = Column(String(512), nullable=False)
    style: Optional[str] = Column(String(128), nullable=True)
    research: Optional[str] = Column(Text, nullable=True)
    final_text: Optional[str] = Column(Text, nullable=True)
    status: str = Column(String(32), default="started", nullable=False)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    actions = relationship("HitlAction", back_populates="session", cascade="all, delete-orphan")


class HitlAction(Base):
    __tablename__ = "hitl_actions"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    session_id: str = Column(String(64), ForeignKey("hitl_sessions.id"), nullable=False)
    action: str = Column(String(64), nullable=False)  # start, approve, reject, write
    payload: Optional[str] = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("HitlSession", back_populates="actions")
