"""Scheduler para execução de jobs do Núcleo Licitações."""

import asyncio
from datetime import datetime, timezone, time
from typing import Callable, Any
from dataclasses import dataclass, field
import logging
import uuid

from .models import FlowConfig, FlowResult, StatusFluxo
from .flows import run_daily_monitor, MonitorFlowState

logger = logging.getLogger(__name__)

_scheduler_lock: asyncio.Lock | None = None
_last_run: dict[str, datetime] = {}


@dataclass
class JobConfig:
    """Configuração de um job agendado."""

    job_id: str
    name: str
    schedule_time: time  # Horário de execução (UTC)
    enabled: bool = True
    max_retries: int = 3
    retry_delay_seconds: int = 60
    flow_config: FlowConfig = field(default_factory=FlowConfig)


@dataclass
class JobResult:
    """Resultado de execução de um job."""

    job_id: str
    run_id: str
    started_at: datetime
    finished_at: datetime | None = None
    status: str = "running"
    retries: int = 0
    flow_result: FlowResult | None = None
    error: str | None = None


class LicitacoesScheduler:
    """
    Scheduler para jobs do núcleo de licitações.

    Executa jobs em horários agendados com:
    - Lock para evitar execução duplicada
    - Retry com limite
    - Logging estruturado
    """

    def __init__(self):
        self.jobs: dict[str, JobConfig] = {}
        self.results: list[JobResult] = []
        self._lock = asyncio.Lock()
        self._running = False

    def register_job(self, config: JobConfig) -> None:
        """Registra um novo job."""
        self.jobs[config.job_id] = config
        logger.info(f"Job registered: {config.job_id} ({config.name}) at {config.schedule_time}")

    def unregister_job(self, job_id: str) -> None:
        """Remove um job."""
        if job_id in self.jobs:
            del self.jobs[job_id]
            logger.info(f"Job unregistered: {job_id}")

    async def run_job(self, job_id: str) -> JobResult:
        """
        Executa um job manualmente ou via schedule.

        Args:
            job_id: ID do job a executar

        Returns:
            JobResult com status da execução
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")

        config = self.jobs[job_id]
        run_id = f"{job_id}-{uuid.uuid4().hex[:8]}"

        result = JobResult(
            job_id=job_id,
            run_id=run_id,
            started_at=datetime.now(timezone.utc),
        )

        async with self._lock:
            if not config.enabled:
                result.status = "skipped"
                result.error = "Job disabled"
                result.finished_at = datetime.now(timezone.utc)
                return result

            last = _last_run.get(job_id)
            if last:
                elapsed = (datetime.now(timezone.utc) - last).total_seconds()
                if elapsed < 300:  # 5 minutos mínimo entre execuções
                    result.status = "skipped"
                    result.error = f"Too soon since last run ({elapsed:.0f}s ago)"
                    result.finished_at = datetime.now(timezone.utc)
                    return result

            _last_run[job_id] = datetime.now(timezone.utc)

        logger.info(f"[{run_id}] Starting job: {config.name}")

        for attempt in range(config.max_retries + 1):
            try:
                result.retries = attempt

                if job_id == "daily_monitor":
                    state, flow_result = await run_daily_monitor(config=config.flow_config)
                    result.flow_result = flow_result

                    if flow_result.status == StatusFluxo.SUCCESS:
                        result.status = "success"
                        break
                    elif flow_result.status == StatusFluxo.PARTIAL:
                        result.status = "partial"
                        break
                    else:
                        raise Exception(f"Flow failed: {flow_result.errors}")
                else:
                    raise ValueError(f"Unknown job type: {job_id}")

            except Exception as e:
                logger.error(f"[{run_id}] Job failed (attempt {attempt + 1}): {e}")
                result.error = str(e)

                if attempt < config.max_retries:
                    logger.info(f"[{run_id}] Retrying in {config.retry_delay_seconds}s...")
                    await asyncio.sleep(config.retry_delay_seconds)
                else:
                    result.status = "failed"

        result.finished_at = datetime.now(timezone.utc)
        self.results.append(result)

        logger.info(f"[{run_id}] Job finished: {result.status}")
        return result

    def should_run(self, job_id: str) -> bool:
        """Verifica se um job deve ser executado agora."""
        if job_id not in self.jobs:
            return False

        config = self.jobs[job_id]
        if not config.enabled:
            return False

        now = datetime.now(timezone.utc)
        scheduled = config.schedule_time

        # Verifica se está no horário (margem de 5 minutos)
        current_minutes = now.hour * 60 + now.minute
        scheduled_minutes = scheduled.hour * 60 + scheduled.minute

        diff = abs(current_minutes - scheduled_minutes)
        if diff > 5:
            return False

        # Verifica se já rodou hoje
        last = _last_run.get(job_id)
        if last and last.date() == now.date():
            return False

        return True

    def get_status(self) -> dict[str, Any]:
        """Retorna status do scheduler."""
        return {
            "jobs": {
                job_id: {
                    "name": config.name,
                    "schedule_time": config.schedule_time.isoformat(),
                    "enabled": config.enabled,
                    "last_run": _last_run.get(job_id, None),
                }
                for job_id, config in self.jobs.items()
            },
            "recent_results": [
                {
                    "job_id": r.job_id,
                    "run_id": r.run_id,
                    "status": r.status,
                    "started_at": r.started_at.isoformat(),
                    "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                }
                for r in self.results[-10:]
            ],
        }


def create_default_scheduler() -> LicitacoesScheduler:
    """Cria scheduler com jobs padrão."""
    scheduler = LicitacoesScheduler()

    # Job: daily_monitor às 07:00 UTC
    scheduler.register_job(JobConfig(
        job_id="daily_monitor",
        name="Daily Monitor - Licitações",
        schedule_time=time(7, 0),  # 07:00 UTC
        enabled=True,
        max_retries=3,
        retry_delay_seconds=60,
        flow_config=FlowConfig(
            janela_dias=7,
            limite_itens=100,
            keywords=["dengue", "drone", "geotecnologia", "arbovirose"],
        ),
    ))

    return scheduler


# Singleton global
_scheduler: LicitacoesScheduler | None = None


def get_scheduler() -> LicitacoesScheduler:
    """Obtém instância singleton do scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = create_default_scheduler()
    return _scheduler
