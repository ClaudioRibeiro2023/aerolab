"""
Testes para os novos componentes implementados nas Fases 1-4.
"""

import pytest


# ==================== TESTES DE RBAC ====================

def test_rbac_admin_has_all_permissions():
    """Admin deve ter acesso total."""
    from src.auth.rbac import check_permission, Resource, Action, Domain

    assert check_permission("admin", Resource.AGENTS, Action.RUN) is True
    assert check_permission("admin", Resource.AGENTS, Action.DELETE) is True
    assert check_permission("admin", Resource.RAG, Action.WRITE, Domain.FINANCE) is True


def test_rbac_viewer_read_only():
    """Viewer só pode ler."""
    from src.auth.rbac import check_permission, Resource, Action

    assert check_permission("viewer", Resource.AGENTS, Action.READ) is True
    assert check_permission("viewer", Resource.AGENTS, Action.WRITE) is False
    assert check_permission("viewer", Resource.AGENTS, Action.DELETE) is False


def test_rbac_domain_analyst_restricted():
    """Analista de domínio só acessa seu domínio."""
    from src.auth.rbac import check_permission, Resource, Action, Domain, get_user_domains

    # geo_analyst pode acessar domínio GEO
    assert check_permission("geo_analyst", Resource.AGENTS, Action.RUN, Domain.GEO) is True

    # geo_analyst não pode acessar domínio FINANCE
    domains = get_user_domains("geo_analyst")
    assert Domain.GEO in domains
    assert Domain.FINANCE not in domains


def test_rbac_list_roles():
    """Deve listar todos os papéis."""
    from src.auth.rbac import list_roles

    roles = list_roles()
    names = [r["name"] for r in roles]

    assert "admin" in names
    assert "viewer" in names
    assert "geo_analyst" in names
    assert "finance_analyst" in names


# ==================== TESTES DE AUDIT ====================

def test_audit_logger_creation():
    """AuditLogger deve ser criado sem erros."""
    from src.audit import get_audit_logger

    logger = get_audit_logger()
    assert logger is not None


def test_audit_event_creation():
    """AuditEvent deve ser criado corretamente."""
    from src.audit import AuditEvent, EventType

    event = AuditEvent(
        event_type=EventType.AGENT_RUN,
        user="test@example.com",
        resource="agents",
        action="run",
        status="success",
    )

    assert event.event_type == EventType.AGENT_RUN
    assert event.user == "test@example.com"


def test_audit_event_to_dict():
    """AuditEvent deve converter para dict."""
    from src.audit import AuditEvent, EventType

    event = AuditEvent(
        event_type=EventType.LOGIN,
        user="user@test.com",
    )

    d = event.to_dict()
    assert d["event_type"] == "login"
    assert d["user"] == "user@test.com"


def test_audit_event_types():
    """Todos os tipos de evento devem existir."""
    from src.audit import EventType

    assert EventType.LOGIN.value == "login"
    assert EventType.AGENT_RUN.value == "agent_run"
    assert EventType.ACCESS_DENIED.value == "access_denied"


# ==================== TESTES DE TOOLS BASE ====================

def test_tool_result_ok():
    """ToolResult.ok deve criar resultado de sucesso."""
    from src.tools.base import ToolResult

    result = ToolResult.ok({"data": "test"}, extra="info")

    assert result.success is True
    assert result.data == {"data": "test"}
    assert result.metadata["extra"] == "info"


def test_tool_result_fail():
    """ToolResult.fail deve criar resultado de falha."""
    from src.tools.base import ToolResult

    result = ToolResult.fail("Erro de teste")

    assert result.success is False
    assert result.error == "Erro de teste"


def test_base_tool_abstract():
    """BaseTool é abstrato e não pode ser instanciado diretamente."""
    from src.tools.base import BaseTool

    with pytest.raises(TypeError):
        BaseTool()  # Deve falhar pois _execute é abstrato


# ==================== TESTES DE TOOLS DE DOMÍNIO ====================

def test_spatial_tool_distance():
    """SpatialTool deve calcular distância corretamente."""
    from src.tools.geo.spatial import SpatialTool

    tool = SpatialTool()
    result = tool.run(
        action="distance",
        point1=(-23.5505, -46.6333),  # São Paulo
        point2=(-22.9068, -43.1729),  # Rio de Janeiro
    )

    assert result.success is True
    # Distância SP-RJ é aproximadamente 360km
    assert 350 < result.data["distance_km"] < 400


def test_analytics_tool_describe():
    """AnalyticsTool deve gerar estatísticas."""
    pytest.importorskip("pandas")
    from src.tools.database.analytics import AnalyticsTool

    tool = AnalyticsTool()
    data = [
        {"name": "A", "value": 10},
        {"name": "B", "value": 20},
        {"name": "C", "value": 30},
    ]

    result = tool.run(action="describe", data=data)

    assert result.success is True
    assert result.data["rows"] == 3


def test_strategy_tool_swot():
    """StrategyTool deve retornar template SWOT."""
    from src.tools.corporate.strategy import StrategyTool

    tool = StrategyTool()
    result = tool.run(action="swot", context="Empresa de tecnologia")

    assert result.success is True
    assert "template" in result.data
    assert "strengths" in result.data["template"]


# ==================== TESTES DE AGENTES ====================

def test_geo_agent_instructions():
    """GeoAgent deve ter instruções padrão."""
    from src.agents.domains.geo import GeoAgent

    assert len(GeoAgent.DEFAULT_INSTRUCTIONS) > 0
    assert "geoespacial" in " ".join(GeoAgent.DEFAULT_INSTRUCTIONS).lower()


def test_finance_agent_instructions():
    """FinanceAgent deve ter instruções padrão."""
    from src.agents.domains.finance import FinanceAgent

    assert len(FinanceAgent.DEFAULT_INSTRUCTIONS) > 0
    assert "financeira" in " ".join(FinanceAgent.DEFAULT_INSTRUCTIONS).lower()


# ==================== TESTES DE TEAMS ====================

def test_base_team_config():
    """TeamConfig deve ser criado corretamente."""
    from src.teams.base_team import TeamConfig

    config = TeamConfig(
        name="TestTeam",
        description="Time de teste",
        members=["Agent1", "Agent2"],
    )

    assert config.name == "TestTeam"
    assert len(config.members) == 2


def test_team_registry():
    """TeamRegistry deve funcionar."""
    from src.teams.base_team import TeamRegistry

    registry = TeamRegistry()
    assert registry.list_teams() == []


# ==================== TESTES DE MIDDLEWARE ====================

def test_rate_limiter():
    """RateLimiter deve funcionar corretamente."""
    from src.os.middleware.rate_limit import RateLimiter

    limiter = RateLimiter(window_seconds=60)

    # Primeira requisição deve passar
    assert limiter.check("user1", "default") is True


def test_rate_limiter_blocking():
    """RateLimiter deve bloquear após exceder limite."""
    from src.os.middleware.rate_limit import RateLimiter

    limiter = RateLimiter(window_seconds=60)

    # Simular muitas requisições
    for _ in range(200):
        limiter.check("user_test", "default")

    # Próxima deve ser bloqueada (limite padrão é 120)
    assert limiter.check("user_test", "default") is False
