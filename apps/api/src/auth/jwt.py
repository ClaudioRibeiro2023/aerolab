from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt


def create_access_token(*, subject: str, role: str, secret: str, expires_minutes: int = 60) -> str:
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, *, secret: str) -> Dict[str, Any]:
    return jwt.decode(token, secret, algorithms=["HS256"])  # raises on failure
