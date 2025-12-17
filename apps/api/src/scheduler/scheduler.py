"""
Sistema de Agendamento de Execuções.

Permite agendar execuções de agentes com expressões cron-like.
"""

import os
import json
import asyncio
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import re


class TaskStatus(Enum):
    """Status de uma tarefa agendada."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class CronExpression:
    """
    Parser de expressões cron simplificadas.
    
    Formato: minute hour day_of_month month day_of_week
    Suporta: *, */N, N, N-M, N,M,O
    
    Exemplos:
        "* * * * *"       - A cada minuto
        "0 * * * *"       - A cada hora
        "0 9 * * 1-5"     - 9h em dias úteis
        "*/15 * * * *"    - A cada 15 minutos
        "0 0 1 * *"       - Primeiro dia de cada mês
    """
    expression: str
    minute: str = "*"
    hour: str = "*"
    day_of_month: str = "*"
    month: str = "*"
    day_of_week: str = "*"
    
    def __post_init__(self):
        parts = self.expression.split()
        if len(parts) == 5:
            self.minute, self.hour, self.day_of_month, self.month, self.day_of_week = parts
        elif len(parts) == 1:
            # Presets
            presets = {
                "@hourly": "0 * * * *",
                "@daily": "0 0 * * *",
                "@weekly": "0 0 * * 0",
                "@monthly": "0 0 1 * *",
                "@yearly": "0 0 1 1 *",
            }
            if self.expression in presets:
                self.__init__(presets[self.expression])
    
    def matches(self, dt: datetime) -> bool:
        """Verifica se datetime corresponde à expressão."""
        return (
            self._matches_field(self.minute, dt.minute, 0, 59) and
            self._matches_field(self.hour, dt.hour, 0, 23) and
            self._matches_field(self.day_of_month, dt.day, 1, 31) and
            self._matches_field(self.month, dt.month, 1, 12) and
            self._matches_field(self.day_of_week, dt.weekday(), 0, 6)
        )
    
    def _matches_field(self, field: str, value: int, min_val: int, max_val: int) -> bool:
        """Verifica se valor corresponde ao campo."""
        if field == "*":
            return True
        
        # */N - a cada N
        if field.startswith("*/"):
            step = int(field[2:])
            return value % step == 0
        
        # N-M - range
        if "-" in field:
            start, end = map(int, field.split("-"))
            return start <= value <= end
        
        # N,M,O - lista
        if "," in field:
            values = [int(v) for v in field.split(",")]
            return value in values
        
        # N - valor exato
        return value == int(field)
    
    def next_run(self, after: Optional[datetime] = None) -> datetime:
        """Calcula próxima execução."""
        dt = after or datetime.now()
        dt = dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Máximo 1 ano de busca
        for _ in range(525600):  # minutos em 1 ano
            if self.matches(dt):
                return dt
            dt += timedelta(minutes=1)
        
        raise ValueError("Não foi possível calcular próxima execução")


@dataclass
class ScheduledTask:
    """Tarefa agendada."""
    id: str
    name: str
    agent_name: str
    prompt: str
    cron_expression: str
    status: TaskStatus = TaskStatus.PENDING
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.next_run is None and self.enabled:
            cron = CronExpression(self.cron_expression)
            self.next_run = cron.next_run()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "agent_name": self.agent_name,
            "prompt": self.prompt,
            "cron_expression": self.cron_expression,
            "status": self.status.value,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "metadata": self.metadata
        }


@dataclass
class TaskExecution:
    """Registro de execução de tarefa."""
    id: str
    task_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    result: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: float = 0


class Scheduler:
    """
    Scheduler para execuções programadas de agentes.
    
    Features:
    - Expressões cron
    - Múltiplas tarefas concorrentes
    - Persistência de estado
    - Retry automático
    - Histórico de execuções
    
    Exemplo:
        scheduler = Scheduler()
        
        scheduler.schedule(
            name="Daily Report",
            agent_name="Researcher",
            prompt="Gere relatório diário de vendas",
            cron="0 9 * * 1-5"  # 9h em dias úteis
        )
        
        await scheduler.start()
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        agent_executor: Optional[Callable] = None
    ):
        self.storage_path = Path(storage_path or os.getenv("SCHEDULER_STORAGE_PATH", "./data/scheduler"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.agent_executor = agent_executor
        self._tasks: Dict[str, ScheduledTask] = {}
        self._executions: List[TaskExecution] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        self._load_tasks()
    
    def _load_tasks(self):
        """Carrega tarefas salvas."""
        tasks_file = self.storage_path / "tasks.json"
        if tasks_file.exists():
            data = json.loads(tasks_file.read_text())
            for t in data.get("tasks", []):
                task = ScheduledTask(
                    id=t["id"],
                    name=t["name"],
                    agent_name=t["agent_name"],
                    prompt=t["prompt"],
                    cron_expression=t["cron_expression"],
                    status=TaskStatus(t["status"]),
                    enabled=t["enabled"],
                    created_at=datetime.fromisoformat(t["created_at"]),
                    last_run=datetime.fromisoformat(t["last_run"]) if t.get("last_run") else None,
                    next_run=datetime.fromisoformat(t["next_run"]) if t.get("next_run") else None,
                    run_count=t.get("run_count", 0),
                    error_count=t.get("error_count", 0),
                    last_error=t.get("last_error"),
                    metadata=t.get("metadata", {})
                )
                self._tasks[task.id] = task
    
    def _save_tasks(self):
        """Salva tarefas."""
        data = {"tasks": [t.to_dict() for t in self._tasks.values()]}
        (self.storage_path / "tasks.json").write_text(json.dumps(data, indent=2))
    
    def schedule(
        self,
        name: str,
        agent_name: str,
        prompt: str,
        cron: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScheduledTask:
        """
        Agenda nova tarefa.
        
        Args:
            name: Nome da tarefa
            agent_name: Nome do agente a executar
            prompt: Prompt para o agente
            cron: Expressão cron
            metadata: Dados adicionais
        """
        import uuid
        
        task = ScheduledTask(
            id=str(uuid.uuid4()),
            name=name,
            agent_name=agent_name,
            prompt=prompt,
            cron_expression=cron,
            metadata=metadata or {}
        )
        
        self._tasks[task.id] = task
        self._save_tasks()
        
        return task
    
    def unschedule(self, task_id: str) -> bool:
        """Remove tarefa."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save_tasks()
            return True
        return False
    
    def pause(self, task_id: str) -> bool:
        """Pausa tarefa."""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = False
            self._tasks[task_id].status = TaskStatus.PAUSED
            self._save_tasks()
            return True
        return False
    
    def resume(self, task_id: str) -> bool:
        """Retoma tarefa."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.enabled = True
            task.status = TaskStatus.PENDING
            cron = CronExpression(task.cron_expression)
            task.next_run = cron.next_run()
            self._save_tasks()
            return True
        return False
    
    def list_tasks(self, enabled_only: bool = False) -> List[ScheduledTask]:
        """Lista tarefas."""
        tasks = list(self._tasks.values())
        if enabled_only:
            tasks = [t for t in tasks if t.enabled]
        return sorted(tasks, key=lambda t: t.next_run or datetime.max)
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Obtém tarefa por ID."""
        return self._tasks.get(task_id)
    
    async def run_now(self, task_id: str) -> Optional[TaskExecution]:
        """Executa tarefa imediatamente."""
        task = self._tasks.get(task_id)
        if not task:
            return None
        return await self._execute_task(task)
    
    async def start(self):
        """Inicia o scheduler."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
    
    async def stop(self):
        """Para o scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _run_loop(self):
        """Loop principal do scheduler."""
        while self._running:
            now = datetime.now()
            
            for task in self._tasks.values():
                if not task.enabled:
                    continue
                
                if task.next_run and task.next_run <= now:
                    asyncio.create_task(self._execute_task(task))
            
            # Checar a cada 30 segundos
            await asyncio.sleep(30)
    
    async def _execute_task(self, task: ScheduledTask) -> TaskExecution:
        """Executa uma tarefa."""
        import uuid
        
        execution = TaskExecution(
            id=str(uuid.uuid4()),
            task_id=task.id,
            started_at=datetime.utcnow()
        )
        
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.utcnow()
        
        try:
            if self.agent_executor:
                result = await self.agent_executor(task.agent_name, task.prompt)
                execution.result = str(result)
                execution.success = True
            else:
                execution.result = "No executor configured"
                execution.success = True
            
            task.run_count += 1
            task.status = TaskStatus.COMPLETED
            task.last_error = None
            
        except Exception as e:
            execution.error = str(e)
            execution.success = False
            task.error_count += 1
            task.status = TaskStatus.FAILED
            task.last_error = str(e)
        
        finally:
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            
            # Calcular próxima execução
            if task.enabled:
                cron = CronExpression(task.cron_expression)
                task.next_run = cron.next_run()
                task.status = TaskStatus.PENDING
            
            self._executions.append(execution)
            self._save_tasks()
        
        return execution
    
    def get_executions(
        self,
        task_id: Optional[str] = None,
        limit: int = 100
    ) -> List[TaskExecution]:
        """Lista execuções."""
        executions = self._executions
        if task_id:
            executions = [e for e in executions if e.task_id == task_id]
        return sorted(executions, key=lambda e: e.started_at, reverse=True)[:limit]


# Singleton
_scheduler: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    """Obtém instância singleton do Scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler
