from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, HitlSession, HitlAction
from src.config import get_settings


@dataclass
class HitlRepository:
    session_factory: sessionmaker

    def create_session(self, topic: str, style: Optional[str], research: Optional[str]) -> HitlSession:
        sid = uuid.uuid4().hex
        with self.session_factory() as db:  # type: Session
            sess = HitlSession(id=sid, topic=topic, style=style, research=research, status="started")
            db.add(sess)
            db.add(HitlAction(session_id=sid, action="start", payload=topic))
            db.commit()
            db.refresh(sess)
            return sess

    def approve(self, session_id: str, final_text: str, feedback: Optional[str]) -> HitlSession:
        with self.session_factory() as db:  # type: Session
            sess = db.get(HitlSession, session_id)
            if not sess:
                raise ValueError("invalid session_id")
            sess.final_text = final_text
            sess.status = "completed"
            db.add(HitlAction(session_id=session_id, action="approve", payload=feedback or ""))
            db.add(HitlAction(session_id=session_id, action="write", payload=str(len(final_text))))
            db.commit()
            db.refresh(sess)
            return sess

    def reject(self, session_id: str) -> HitlSession:
        with self.session_factory() as db:  # type: Session
            sess = db.get(HitlSession, session_id)
            if not sess:
                raise ValueError("invalid session_id")
            sess.status = "rejected"
            db.add(HitlAction(session_id=session_id, action="reject"))
            db.commit()
            db.refresh(sess)
            return sess

    def get(self, session_id: str) -> Optional[HitlSession]:
        with self.session_factory() as db:  # type: Session
            return db.get(HitlSession, session_id)

    def list(self, status: Optional[str] = None, limit: int = 50, offset: int = 0):
        with self.session_factory() as db:  # type: Session
            q = db.query(HitlSession)
            if status:
                q = q.filter(HitlSession.status == status)
            q = q.order_by(HitlSession.created_at.desc()).offset(offset).limit(limit)
            return list(q.all())

    def actions(self, session_id: str):
        with self.session_factory() as db:  # type: Session
            sess = db.get(HitlSession, session_id)
            if not sess:
                return []
            # materializar ações antes de fechar a sessão
            acts = list(db.query(HitlAction).filter(HitlAction.session_id == session_id).order_by(HitlAction.created_at.asc()).all())
            return acts

    def cancel(self, session_id: str, reason: Optional[str] = None) -> HitlSession:
        with self.session_factory() as db:  # type: Session
            sess = db.get(HitlSession, session_id)
            if not sess:
                raise ValueError("invalid session_id")
            sess.status = "cancelled"
            db.add(HitlAction(session_id=session_id, action="cancel", payload=reason or ""))
            db.commit()
            db.refresh(sess)
            return sess


def _make_sqlite_url() -> str:
    s = get_settings()
    base = s.BASE_DIR
    db_rel = Path(s.DEFAULT_DB_FILE)
    db_path = (base / db_rel).resolve()
    # Ensure parent dirs exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


def get_repo() -> HitlRepository:
    engine = create_engine(_make_sqlite_url(), future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return HitlRepository(session_factory=SessionLocal)
