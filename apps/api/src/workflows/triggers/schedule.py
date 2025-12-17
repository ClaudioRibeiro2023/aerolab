"""
Schedule Trigger - Dispara workflows via cron schedule.

Features:
- Expressões cron padrão
- Timezone support
- Backoff em caso de falha
- Histórico de execuções
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import logging

from .base import BaseTrigger, TriggerConfig, TriggerResult, TriggerType

logger = logging.getLogger(__name__)


@dataclass
class CronExpression:
    """
    Representação de expressão cron.
    
    Formato: minute hour day month weekday
    
    Exemplos:
    - "0 8 * * *" - Todo dia às 8h
    - "*/15 * * * *" - A cada 15 minutos
    - "0 0 1 * *" - Primeiro dia do mês à meia-noite
    - "0 9-17 * * 1-5" - Das 9h às 17h em dias úteis
    """
    minute: str = "*"
    hour: str = "*"
    day: str = "*"
    month: str = "*"
    weekday: str = "*"
    
    @classmethod
    def from_string(cls, expr: str) -> "CronExpression":
        """Parse expressão cron de string."""
        parts = expr.strip().split()
        
        if len(parts) < 5:
            parts.extend(["*"] * (5 - len(parts)))
        
        return cls(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            weekday=parts[4]
        )
    
    def __str__(self) -> str:
        return f"{self.minute} {self.hour} {self.day} {self.month} {self.weekday}"
    
    def matches(self, dt: datetime) -> bool:
        """Verifica se datetime matches a expressão."""
        return (
            self._matches_field(self.minute, dt.minute, 0, 59) and
            self._matches_field(self.hour, dt.hour, 0, 23) and
            self._matches_field(self.day, dt.day, 1, 31) and
            self._matches_field(self.month, dt.month, 1, 12) and
            self._matches_field(self.weekday, dt.weekday(), 0, 6)
        )
    
    def _matches_field(self, pattern: str, value: int, min_val: int, max_val: int) -> bool:
        """Verifica se valor matches o pattern."""
        if pattern == "*":
            return True
        
        # Suporte a ranges (e.g., "9-17")
        if "-" in pattern and "/" not in pattern:
            try:
                start, end = pattern.split("-")
                return int(start) <= value <= int(end)
            except ValueError:
                return False
        
        # Suporte a step (e.g., "*/15")
        if pattern.startswith("*/"):
            try:
                step = int(pattern[2:])
                return value % step == 0
            except ValueError:
                return False
        
        # Suporte a lista (e.g., "1,3,5")
        if "," in pattern:
            try:
                values = [int(v.strip()) for v in pattern.split(",")]
                return value in values
            except ValueError:
                return False
        
        # Valor exato
        try:
            return value == int(pattern)
        except ValueError:
            return False
    
    def next_run(self, after: Optional[datetime] = None) -> datetime:
        """Calcula próxima execução após uma data."""
        dt = (after or datetime.now()).replace(second=0, microsecond=0)
        dt += timedelta(minutes=1)
        
        # Buscar próximo match (máximo 1 ano)
        max_iterations = 365 * 24 * 60
        
        for _ in range(max_iterations):
            if self.matches(dt):
                return dt
            dt += timedelta(minutes=1)
        
        # Fallback: 1 hora no futuro
        return datetime.now() + timedelta(hours=1)


@dataclass
class ScheduleConfig:
    """Configuração específica para schedule."""
    cron: str = "0 * * * *"  # A cada hora
    timezone: str = "UTC"
    enabled: bool = True
    retry_on_failure: bool = True
    max_retries: int = 3
    retry_delay_seconds: int = 60
    
    def to_dict(self) -> Dict:
        return {
            "cron": self.cron,
            "timezone": self.timezone,
            "enabled": self.enabled,
            "retry_on_failure": self.retry_on_failure,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ScheduleConfig":
        return cls(
            cron=data.get("cron", "0 * * * *"),
            timezone=data.get("timezone", "UTC"),
            enabled=data.get("enabled", True),
            retry_on_failure=data.get("retry_on_failure", True),
            max_retries=data.get("max_retries", 3),
            retry_delay_seconds=data.get("retry_delay_seconds", 60)
        )


class ScheduleTrigger(BaseTrigger):
    """
    Trigger que dispara via schedule cron.
    
    Exemplo:
        trigger = ScheduleTrigger(TriggerConfig(
            id="daily-report",
            name="Daily Report Generator",
            workflow_id="generate-report",
            config={
                "cron": "0 8 * * 1-5",  # 8h em dias úteis
                "timezone": "America/Sao_Paulo"
            }
        ))
    """
    
    def __init__(self, config: TriggerConfig):
        super().__init__(config)
        self.schedule_config = ScheduleConfig.from_dict(config.config)
        self.cron = CronExpression.from_string(self.schedule_config.cron)
        self._task: Optional[asyncio.Task] = None
        self._next_run: Optional[datetime] = None
        self._running = False
    
    @property
    def trigger_type(self) -> TriggerType:
        return TriggerType.SCHEDULE
    
    @property
    def next_run(self) -> Optional[datetime]:
        """Retorna próxima execução programada."""
        return self._next_run
    
    async def start(self) -> None:
        """Inicia o scheduler."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Schedule trigger {self.config.id} started with cron: {self.cron}")
    
    async def stop(self) -> None:
        """Para o scheduler."""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        logger.info(f"Schedule trigger {self.config.id} stopped")
    
    async def _run_loop(self) -> None:
        """Loop principal do scheduler."""
        while self._running:
            try:
                # Calcular próxima execução
                self._next_run = self.cron.next_run()
                
                # Calcular tempo de espera
                now = datetime.now()
                wait_seconds = (self._next_run - now).total_seconds()
                
                if wait_seconds > 0:
                    logger.debug(f"Schedule {self.config.id} next run in {wait_seconds:.0f}s at {self._next_run}")
                    await asyncio.sleep(wait_seconds)
                
                if not self._running or not self.is_active:
                    continue
                
                # Disparar
                logger.info(f"Schedule trigger {self.config.id} firing at {datetime.now()}")
                
                result = await self.trigger(
                    inputs={
                        "scheduled_time": self._next_run.isoformat(),
                        "actual_time": datetime.now().isoformat()
                    },
                    metadata={
                        "cron": str(self.cron),
                        "timezone": self.schedule_config.timezone
                    }
                )
                
                # Retry se falhou
                if not result.success and self.schedule_config.retry_on_failure:
                    await self._retry_execution()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Schedule trigger {self.config.id} error: {e}")
                await asyncio.sleep(60)  # Esperar antes de tentar novamente
    
    async def _retry_execution(self) -> None:
        """Tenta executar novamente após falha."""
        for attempt in range(self.schedule_config.max_retries):
            logger.info(f"Schedule {self.config.id} retry attempt {attempt + 1}")
            
            await asyncio.sleep(self.schedule_config.retry_delay_seconds)
            
            result = await self.trigger(
                inputs={
                    "retry_attempt": attempt + 1,
                    "scheduled_time": self._next_run.isoformat() if self._next_run else None
                }
            )
            
            if result.success:
                return
        
        logger.error(f"Schedule {self.config.id} failed after {self.schedule_config.max_retries} retries")
    
    def update_schedule(self, cron: str) -> None:
        """Atualiza expressão cron."""
        self.schedule_config.cron = cron
        self.cron = CronExpression.from_string(cron)
        self.config.config["cron"] = cron
    
    def validate(self) -> List[str]:
        errors = super().validate()
        try:
            CronExpression.from_string(self.schedule_config.cron)
        except Exception:
            errors.append(f"Invalid cron expression: {self.schedule_config.cron}")
        return errors


# Presets comuns
SCHEDULE_PRESETS = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_15_minutes": "*/15 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "hourly": "0 * * * *",
    "daily_midnight": "0 0 * * *",
    "daily_morning": "0 8 * * *",
    "weekdays_morning": "0 8 * * 1-5",
    "weekly_monday": "0 0 * * 1",
    "monthly_first": "0 0 1 * *",
}
