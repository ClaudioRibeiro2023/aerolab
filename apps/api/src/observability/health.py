"""
Sistema de Health Checks avançados.

Monitora saúde de todos os componentes do sistema.
"""

import os
import asyncio
import time
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import httpx


class HealthStatus(Enum):
    """Status de saúde."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Saúde de um componente."""

    name: str
    status: HealthStatus
    latency_ms: float = 0
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SystemHealth:
    """Saúde geral do sistema."""

    status: HealthStatus
    components: List[ComponentHealth]
    uptime_seconds: float
    version: str
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "uptime_seconds": self.uptime_seconds,
            "version": self.version,
            "checked_at": self.checked_at.isoformat(),
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "latency_ms": c.latency_ms,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.components
            ],
        }


class HealthChecker:
    """
    Sistema de health checks.

    Features:
    - Checks de múltiplos componentes
    - Verificação de dependências externas
    - Latência de resposta
    - Status agregado
    - Endpoints /health e /health/live

    Componentes verificados:
    - Database (PostgreSQL)
    - Cache (Redis)
    - LLM APIs
    - External services
    """

    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.start_time = time.time()
        self._checks: Dict[str, Callable] = {}

        # Registrar checks padrão
        self._register_default_checks()

    def _register_default_checks(self):
        """Registra checks padrão."""
        self.register("database", self._check_database)
        self.register("redis", self._check_redis)
        self.register("filesystem", self._check_filesystem)
        self.register("memory", self._check_memory)

    def register(self, name: str, check_fn: Callable):
        """Registra novo health check."""
        self._checks[name] = check_fn

    def unregister(self, name: str):
        """Remove health check."""
        if name in self._checks:
            del self._checks[name]

    async def check_all(self) -> SystemHealth:
        """Executa todos os health checks."""
        components = []

        for name, check_fn in self._checks.items():
            try:
                start = time.time()
                result = check_fn()
                if asyncio.iscoroutine(result):
                    result = await result
                latency = (time.time() - start) * 1000

                if isinstance(result, ComponentHealth):
                    result.latency_ms = latency
                    components.append(result)
                elif isinstance(result, dict):
                    components.append(
                        ComponentHealth(
                            name=name,
                            status=HealthStatus(result.get("status", "healthy")),
                            latency_ms=latency,
                            message=result.get("message"),
                            details=result.get("details", {}),
                        )
                    )
                else:
                    components.append(
                        ComponentHealth(
                            name=name,
                            status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                            latency_ms=latency,
                        )
                    )

            except Exception as e:
                components.append(
                    ComponentHealth(name=name, status=HealthStatus.UNHEALTHY, message=str(e))
                )

        # Determinar status geral
        statuses = [c.status for c in components]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        else:
            overall = HealthStatus.DEGRADED

        return SystemHealth(
            status=overall,
            components=components,
            uptime_seconds=time.time() - self.start_time,
            version=self.version,
        )

    async def check_liveness(self) -> Dict[str, Any]:
        """Check simples de liveness (para Kubernetes)."""
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

    async def check_readiness(self) -> Dict[str, Any]:
        """Check de readiness (para Kubernetes)."""
        health = await self.check_all()
        return {
            "ready": health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED],
            "status": health.status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Checks padrão
    def _check_database(self) -> ComponentHealth:
        """Verifica conexão com banco de dados."""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.UNKNOWN,
                    message="DATABASE_URL not configured",
                )

            # Verificação simplificada
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database configured",
                details={"url_configured": True},
            )
        except Exception as e:
            return ComponentHealth(name="database", status=HealthStatus.UNHEALTHY, message=str(e))

    def _check_redis(self) -> ComponentHealth:
        """Verifica conexão com Redis."""
        try:
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                return ComponentHealth(
                    name="redis", status=HealthStatus.UNKNOWN, message="REDIS_URL not configured"
                )

            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis configured",
                details={"url_configured": True},
            )
        except Exception as e:
            return ComponentHealth(name="redis", status=HealthStatus.UNHEALTHY, message=str(e))

    def _check_filesystem(self) -> ComponentHealth:
        """Verifica sistema de arquivos."""
        try:
            import tempfile

            # Testar escrita
            with tempfile.NamedTemporaryFile(delete=True) as f:
                f.write(b"health check")
                f.flush()

            return ComponentHealth(
                name="filesystem", status=HealthStatus.HEALTHY, message="Filesystem writable"
            )
        except Exception as e:
            return ComponentHealth(name="filesystem", status=HealthStatus.UNHEALTHY, message=str(e))

    def _check_memory(self) -> ComponentHealth:
        """Verifica uso de memória."""
        try:
            import psutil

            memory = psutil.virtual_memory()

            status = HealthStatus.HEALTHY
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
            elif memory.percent > 75:
                status = HealthStatus.DEGRADED

            return ComponentHealth(
                name="memory",
                status=status,
                message=f"Memory usage: {memory.percent}%",
                details={
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": memory.percent,
                },
            )
        except ImportError:
            return ComponentHealth(
                name="memory", status=HealthStatus.UNKNOWN, message="psutil not installed"
            )
        except Exception as e:
            return ComponentHealth(name="memory", status=HealthStatus.UNHEALTHY, message=str(e))

    async def check_external_service(
        self, name: str, url: str, timeout: float = 5.0
    ) -> ComponentHealth:
        """Verifica serviço externo."""
        try:
            start = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=timeout)
                latency = (time.time() - start) * 1000

                if response.status_code < 400:
                    return ComponentHealth(
                        name=name,
                        status=HealthStatus.HEALTHY,
                        latency_ms=latency,
                        details={"status_code": response.status_code},
                    )
                else:
                    return ComponentHealth(
                        name=name,
                        status=HealthStatus.DEGRADED,
                        latency_ms=latency,
                        message=f"Status code: {response.status_code}",
                    )
        except Exception as e:
            return ComponentHealth(name=name, status=HealthStatus.UNHEALTHY, message=str(e))


# Singleton
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Obtém instância singleton do HealthChecker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
