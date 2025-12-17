"""
⚠️ DEPRECATED: Use server.py instead.

Este arquivo será removido em versões futuras.
Execute: python server.py

Minimal AgentOS app to run with uvicorn or FastAPI CLI.

Run options:
- fastapi dev app.py
- uvicorn app:app --reload --port 8000
"""
import warnings
import os

warnings.warn(
    "app.py está DEPRECATED. Use 'python server.py' como entry point principal.",
    DeprecationWarning,
    stacklevel=2
)
from src.os.builder_new import get_app as build_app

# Build AgentOS FastAPI app a partir do builder central
app = build_app()

# CORS opcional via env (ex.: "http://localhost:3000,https://os.agno.com")
cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
if cors_origins:
    try:
        from fastapi.middleware.cors import CORSMiddleware

        origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    except Exception:
        # CORS é opcional; se fastapi.middleware.cors não existir, ignora
        pass

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("AGENTOS_HOST", "0.0.0.0")
    port = int(os.getenv("AGENTOS_PORT", "8000"))
    uvicorn.run("app:app", host=host, port=port, reload=True)
