"""
Módulo do AgentOS.

Estrutura:
- builder.py: Builder original (legado, mantido para compatibilidade)
- builder_new.py: Builder modular (recomendado para novos projetos)
- routes/: Routers modulares por funcionalidade
- middleware/: Middlewares (rate limit, security)
"""

# Manter compatibilidade com builder original
try:
    from .builder import build_agent_os, build_agents, get_app  # noqa: F401
except ImportError:
    build_agent_os = None
    build_agents = None
    get_app = None

# Exportar também o builder modular
from .builder_new import get_app as get_app_modular  # noqa: F401

__all__ = [
    "build_agent_os",
    "build_agents",
    "get_app",
    "get_app_modular",
]
