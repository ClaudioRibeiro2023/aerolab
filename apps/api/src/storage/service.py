from __future__ import annotations

from typing import List

from src.config import get_settings


class LocalStorageService:
    def __init__(self) -> None:
        s = get_settings()
        base = s.KNOWLEDGE_DIR
        base.mkdir(parents=True, exist_ok=True)
        self.base = base

    def save_text(self, name: str, content: str) -> str:
        # sanitize name basic
        safe_name = name.replace("..", "_").replace("/", "_").replace("\\", "_")
        path = self.base / safe_name
        path.write_text(content, encoding="utf-8")
        return str(path)

    def list_files(self) -> List[str]:
        return [str(p) for p in self.base.glob("**/*") if p.is_file()]

    def delete_file(self, name: str) -> bool:
        # sanitize name basic and delete if exists
        safe_name = name.replace("..", "_").replace("/", "_").replace("\\", "_")
        path = self.base / safe_name
        if path.exists() and path.is_file():
            try:
                path.unlink()
                return True
            except Exception:
                return False
        return False


def get_storage() -> LocalStorageService:
    return LocalStorageService()
