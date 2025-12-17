"""
Sistema de RBAC (Role-Based Access Control) granular.

Suporta permissões por:
- Recurso (agents, teams, workflows, rag, etc)
- Ação (read, write, run, delete, admin)
- Domínio (geo, finance, legal, corporate, etc)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class Action(str, Enum):
    """Ações disponíveis no sistema."""
    READ = "read"
    WRITE = "write"
    RUN = "run"
    DELETE = "delete"
    ADMIN = "admin"


class Resource(str, Enum):
    """Recursos do sistema."""
    AGENTS = "agents"
    TEAMS = "teams"
    WORKFLOWS = "workflows"
    RAG = "rag"
    STORAGE = "storage"
    MEMORY = "memory"
    HITL = "hitl"
    METRICS = "metrics"
    CONFIG = "config"


class Domain(str, Enum):
    """Domínios especializados."""
    GENERAL = "general"
    GEO = "geo"
    DATA = "data"
    DEVOPS = "devops"
    FINANCE = "finance"
    LEGAL = "legal"
    CORPORATE = "corporate"


@dataclass
class Permission:
    """Representa uma permissão específica."""
    resource: Resource
    action: Action
    domain: Optional[Domain] = None  # None = todos os domínios

    def __str__(self) -> str:
        if self.domain:
            return f"{self.resource.value}:{self.action.value}:{self.domain.value}"
        return f"{self.resource.value}:{self.action.value}"

    @classmethod
    def from_string(cls, perm_str: str) -> "Permission":
        """Cria permissão a partir de string."""
        parts = perm_str.split(":")
        if len(parts) == 2:
            return cls(
                resource=Resource(parts[0]),
                action=Action(parts[1]),
            )
        elif len(parts) == 3:
            return cls(
                resource=Resource(parts[0]),
                action=Action(parts[1]),
                domain=Domain(parts[2]),
            )
        raise ValueError(f"Formato inválido: {perm_str}")


@dataclass
class Role:
    """Representa um papel com conjunto de permissões."""
    name: str
    description: str = ""
    permissions: Set[str] = field(default_factory=set)
    domains: Set[Domain] = field(default_factory=set)  # Domínios permitidos

    def has_permission(self, resource: Resource, action: Action, domain: Optional[Domain] = None) -> bool:
        """Verifica se o papel tem a permissão."""
        # Wildcard
        if "*" in self.permissions:
            return True

        # Permissão exata com domínio
        if domain:
            perm_with_domain = f"{resource.value}:{action.value}:{domain.value}"
            if perm_with_domain in self.permissions:
                return True

            # Verificar se tem permissão para o domínio
            if domain not in self.domains and self.domains:
                return False

        # Permissão sem domínio (aplica a todos)
        perm_base = f"{resource.value}:{action.value}"
        if perm_base in self.permissions:
            return True

        # Permissão por recurso (todas as ações)
        perm_resource = f"{resource.value}:*"
        if perm_resource in self.permissions:
            return True

        return False


# Papéis pré-definidos
ROLES: Dict[str, Role] = {
    "admin": Role(
        name="admin",
        description="Administrador com acesso total",
        permissions={"*"},
        domains=set(Domain),
    ),
    "analyst": Role(
        name="analyst",
        description="Analista com acesso de leitura e execução",
        permissions={
            "agents:read",
            "agents:run",
            "teams:read",
            "teams:run",
            "workflows:read",
            "workflows:run",
            "rag:read",
            "rag:run",
            "memory:read",
            "metrics:read",
        },
        domains=set(Domain),
    ),
    "viewer": Role(
        name="viewer",
        description="Visualizador apenas leitura",
        permissions={
            "agents:read",
            "teams:read",
            "workflows:read",
            "rag:read",
            "metrics:read",
        },
        domains=set(Domain),
    ),
    "geo_analyst": Role(
        name="geo_analyst",
        description="Analista especializado em geolocalização",
        permissions={
            "agents:read",
            "agents:run",
            "teams:read",
            "teams:run",
            "rag:read",
            "rag:run",
        },
        domains={Domain.GEO, Domain.GENERAL},
    ),
    "finance_analyst": Role(
        name="finance_analyst",
        description="Analista especializado em finanças",
        permissions={
            "agents:read",
            "agents:run",
            "teams:read",
            "teams:run",
            "rag:read",
            "rag:run",
        },
        domains={Domain.FINANCE, Domain.GENERAL},
    ),
    "legal_analyst": Role(
        name="legal_analyst",
        description="Analista especializado em jurídico",
        permissions={
            "agents:read",
            "agents:run",
            "teams:read",
            "teams:run",
            "rag:read",
            "rag:run",
        },
        domains={Domain.LEGAL, Domain.GENERAL},
    ),
    "developer": Role(
        name="developer",
        description="Desenvolvedor com acesso a DevOps",
        permissions={
            "agents:read",
            "agents:run",
            "agents:write",
            "teams:read",
            "teams:run",
            "teams:write",
            "workflows:read",
            "workflows:run",
            "workflows:write",
            "rag:read",
            "rag:run",
            "storage:read",
            "storage:write",
        },
        domains={Domain.DEVOPS, Domain.DATA, Domain.GENERAL},
    ),
}


def get_role(role_name: str) -> Optional[Role]:
    """Obtém um papel pelo nome."""
    return ROLES.get(role_name.lower())


def check_permission(
    user_role: str,
    resource: Resource,
    action: Action,
    domain: Optional[Domain] = None,
) -> bool:
    """
    Verifica se um usuário tem permissão.

    Args:
        user_role: Nome do papel do usuário
        resource: Recurso sendo acessado
        action: Ação sendo executada
        domain: Domínio (opcional)

    Returns:
        True se permitido, False caso contrário
    """
    role = get_role(user_role)
    if not role:
        return False
    return role.has_permission(resource, action, domain)


def get_user_domains(user_role: str) -> Set[Domain]:
    """Retorna os domínios permitidos para um papel."""
    role = get_role(user_role)
    if not role:
        return set()
    if not role.domains:
        return set(Domain)  # Todos os domínios
    return role.domains


def list_roles() -> List[Dict]:
    """Lista todos os papéis disponíveis."""
    return [
        {
            "name": role.name,
            "description": role.description,
            "permissions": list(role.permissions),
            "domains": [d.value for d in role.domains],
        }
        for role in ROLES.values()
    ]


def add_custom_role(
    name: str,
    description: str,
    permissions: Set[str],
    domains: Optional[Set[Domain]] = None,
) -> Role:
    """
    Adiciona um papel customizado.

    Args:
        name: Nome único do papel
        description: Descrição
        permissions: Conjunto de permissões
        domains: Domínios permitidos

    Returns:
        Role criado
    """
    role = Role(
        name=name,
        description=description,
        permissions=permissions,
        domains=domains or set(Domain),
    )
    ROLES[name.lower()] = role
    return role
