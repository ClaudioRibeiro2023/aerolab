"""
Self-Healing Agent - Agente Auto-Corretivo

Implementa capacidade de detecção e correção automática de erros,
permitindo que agentes se recuperem de falhas.

Features:
- Detecção de erros em tempo real
- Análise de causa raiz
- Estratégias de recuperação
- Aprendizado de falhas
- Circuit breaker

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                   Self-Healing Agent                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Error       │  │ Diagnosis   │  │ Recovery    │         │
│  │ Detector    │  │ Engine      │  │ Strategies  │         │
│  │             │  │             │  │             │         │
│  │ - Parse     │→│ - Classify  │→│ - Retry     │         │
│  │ - Validate  │  │ - Root cause│  │ - Fallback  │         │
│  │ - Monitor   │  │ - Pattern   │  │ - Escalate  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │  Learning │                            │
│                    │  - Store  │                            │
│                    │  - Analyze│                            │
│                    │  - Prevent│                            │
│                    └───────────┘                            │
└─────────────────────────────────────────────────────────────┘
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Any, Callable, Awaitable
from enum import Enum
import logging
import traceback
import re


logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """Tipos de erro."""
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    VALIDATION = "validation"
    TOOL_ERROR = "tool_error"
    PARSE_ERROR = "parse_error"
    CONTEXT_OVERFLOW = "context_overflow"
    PERMISSION = "permission"
    NETWORK = "network"
    UNKNOWN = "unknown"


class RecoveryStrategy(str, Enum):
    """Estratégias de recuperação."""
    RETRY = "retry"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK_MODEL = "fallback_model"
    SIMPLIFY_REQUEST = "simplify_request"
    SPLIT_REQUEST = "split_request"
    USE_CACHE = "use_cache"
    ESCALATE = "escalate"
    ABORT = "abort"


class CircuitState(str, Enum):
    """Estados do circuit breaker."""
    CLOSED = "closed"      # Normal
    OPEN = "open"          # Bloqueando
    HALF_OPEN = "half_open"  # Testando


@dataclass
class ErrorContext:
    """Contexto de um erro."""
    error_type: ErrorType
    message: str
    original_exception: Optional[Exception] = None
    
    # Contexto da requisição
    request_id: Optional[str] = None
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    
    # Detalhes
    traceback: Optional[str] = None
    input_data: Optional[dict] = None
    
    # Timing
    occurred_at: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0
    
    # Tentativas
    attempt_number: int = 1
    max_attempts: int = 3
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "occurred_at": self.occurred_at.isoformat(),
            "attempt_number": self.attempt_number
        }


@dataclass
class RecoveryAction:
    """Ação de recuperação."""
    strategy: RecoveryStrategy
    parameters: dict = field(default_factory=dict)
    
    # Resultado
    success: bool = False
    result: Any = None
    error: Optional[str] = None
    
    # Timing
    executed_at: Optional[datetime] = None
    duration_ms: float = 0


@dataclass
class DiagnosisResult:
    """Resultado de diagnóstico."""
    error_context: ErrorContext
    root_cause: str = ""
    recommended_strategies: list[RecoveryStrategy] = field(default_factory=list)
    confidence: float = 0.0
    
    # Análise
    is_transient: bool = False
    is_recoverable: bool = True
    similar_errors_count: int = 0


class ErrorDetector:
    """
    Detector de erros.
    
    Classifica exceções e erros em tipos conhecidos
    para facilitar recuperação.
    """
    
    # Padrões de erro por tipo
    ERROR_PATTERNS = {
        ErrorType.TIMEOUT: [
            r"timeout",
            r"timed out",
            r"deadline exceeded"
        ],
        ErrorType.RATE_LIMIT: [
            r"rate limit",
            r"too many requests",
            r"429",
            r"quota exceeded"
        ],
        ErrorType.API_ERROR: [
            r"api error",
            r"500",
            r"502",
            r"503",
            r"service unavailable"
        ],
        ErrorType.VALIDATION: [
            r"validation",
            r"invalid",
            r"malformed"
        ],
        ErrorType.TOOL_ERROR: [
            r"tool.*error",
            r"function.*failed",
            r"execution.*failed"
        ],
        ErrorType.PARSE_ERROR: [
            r"parse",
            r"json",
            r"syntax"
        ],
        ErrorType.CONTEXT_OVERFLOW: [
            r"context.*length",
            r"token.*limit",
            r"maximum.*context"
        ],
        ErrorType.PERMISSION: [
            r"permission",
            r"unauthorized",
            r"forbidden",
            r"401",
            r"403"
        ],
        ErrorType.NETWORK: [
            r"network",
            r"connection",
            r"dns",
            r"socket"
        ]
    }
    
    def detect(self, exception: Exception) -> ErrorContext:
        """
        Detecta e classifica um erro.
        
        Args:
            exception: Exceção a analisar
            
        Returns:
            ErrorContext com classificação
        """
        message = str(exception).lower()
        error_type = self._classify_error(message)
        
        return ErrorContext(
            error_type=error_type,
            message=str(exception),
            original_exception=exception,
            traceback=traceback.format_exc()
        )
    
    def _classify_error(self, message: str) -> ErrorType:
        """Classifica erro baseado na mensagem."""
        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return error_type
        
        return ErrorType.UNKNOWN


class DiagnosisEngine:
    """
    Motor de diagnóstico.
    
    Analisa erros para determinar causa raiz
    e recomendar estratégias de recuperação.
    """
    
    # Mapeamento de tipo de erro para estratégias
    STRATEGY_MAP = {
        ErrorType.TIMEOUT: [
            RecoveryStrategy.RETRY_WITH_BACKOFF,
            RecoveryStrategy.SIMPLIFY_REQUEST,
            RecoveryStrategy.FALLBACK_MODEL
        ],
        ErrorType.RATE_LIMIT: [
            RecoveryStrategy.RETRY_WITH_BACKOFF,
            RecoveryStrategy.USE_CACHE
        ],
        ErrorType.API_ERROR: [
            RecoveryStrategy.RETRY,
            RecoveryStrategy.FALLBACK_MODEL,
            RecoveryStrategy.ESCALATE
        ],
        ErrorType.VALIDATION: [
            RecoveryStrategy.SIMPLIFY_REQUEST,
            RecoveryStrategy.ABORT
        ],
        ErrorType.TOOL_ERROR: [
            RecoveryStrategy.RETRY,
            RecoveryStrategy.ESCALATE
        ],
        ErrorType.PARSE_ERROR: [
            RecoveryStrategy.RETRY,
            RecoveryStrategy.SIMPLIFY_REQUEST
        ],
        ErrorType.CONTEXT_OVERFLOW: [
            RecoveryStrategy.SPLIT_REQUEST,
            RecoveryStrategy.SIMPLIFY_REQUEST
        ],
        ErrorType.PERMISSION: [
            RecoveryStrategy.ESCALATE,
            RecoveryStrategy.ABORT
        ],
        ErrorType.NETWORK: [
            RecoveryStrategy.RETRY_WITH_BACKOFF,
            RecoveryStrategy.ABORT
        ],
        ErrorType.UNKNOWN: [
            RecoveryStrategy.RETRY,
            RecoveryStrategy.ESCALATE
        ]
    }
    
    # Erros transientes (podem se resolver sozinhos)
    TRANSIENT_ERRORS = {
        ErrorType.TIMEOUT,
        ErrorType.RATE_LIMIT,
        ErrorType.API_ERROR,
        ErrorType.NETWORK
    }
    
    def __init__(self):
        self._error_history: list[ErrorContext] = []
    
    def diagnose(self, error: ErrorContext) -> DiagnosisResult:
        """
        Diagnostica um erro.
        
        Args:
            error: Contexto do erro
            
        Returns:
            DiagnosisResult com análise
        """
        # Adicionar ao histórico
        self._error_history.append(error)
        
        # Análise básica
        is_transient = error.error_type in self.TRANSIENT_ERRORS
        strategies = self.STRATEGY_MAP.get(
            error.error_type,
            [RecoveryStrategy.RETRY]
        )
        
        # Verificar erros similares recentes
        similar = self._find_similar_errors(error)
        
        # Ajustar estratégias baseado no histórico
        if len(similar) >= 3:
            # Muitos erros similares, escalar
            strategies = [RecoveryStrategy.ESCALATE] + strategies
        
        # Determinar causa raiz
        root_cause = self._determine_root_cause(error, similar)
        
        # Calcular confiança
        confidence = 0.7 if error.error_type != ErrorType.UNKNOWN else 0.3
        
        return DiagnosisResult(
            error_context=error,
            root_cause=root_cause,
            recommended_strategies=strategies,
            confidence=confidence,
            is_transient=is_transient,
            is_recoverable=error.error_type != ErrorType.PERMISSION,
            similar_errors_count=len(similar)
        )
    
    def _find_similar_errors(
        self,
        error: ErrorContext,
        window_minutes: int = 5
    ) -> list[ErrorContext]:
        """Encontra erros similares recentes."""
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        
        return [
            e for e in self._error_history
            if e.error_type == error.error_type
            and e.occurred_at > cutoff
            and e != error
        ]
    
    def _determine_root_cause(
        self,
        error: ErrorContext,
        similar: list[ErrorContext]
    ) -> str:
        """Determina causa raiz provável."""
        if error.error_type == ErrorType.RATE_LIMIT:
            return "Rate limit exceeded - too many requests in short period"
        elif error.error_type == ErrorType.TIMEOUT:
            return "Request took too long - possibly due to complex query or server load"
        elif error.error_type == ErrorType.CONTEXT_OVERFLOW:
            return "Input too large - exceeds model's context window"
        elif error.error_type == ErrorType.API_ERROR:
            if len(similar) > 2:
                return "Persistent API issues - service may be experiencing problems"
            return "Temporary API error - likely transient"
        elif error.error_type == ErrorType.NETWORK:
            return "Network connectivity issue"
        
        return f"Error of type {error.error_type.value}"


class RecoveryExecutor:
    """
    Executor de estratégias de recuperação.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        # Fallback models
        self.fallback_models = ["gpt-4o-mini", "gpt-3.5-turbo"]
        
        # Cache simples
        self._cache: dict[str, Any] = {}
    
    async def execute(
        self,
        strategy: RecoveryStrategy,
        original_fn: Callable[..., Awaitable[Any]],
        error_context: ErrorContext,
        *args,
        **kwargs
    ) -> RecoveryAction:
        """
        Executa estratégia de recuperação.
        
        Args:
            strategy: Estratégia a executar
            original_fn: Função original que falhou
            error_context: Contexto do erro
            *args, **kwargs: Argumentos da função original
            
        Returns:
            RecoveryAction com resultado
        """
        action = RecoveryAction(strategy=strategy)
        action.executed_at = datetime.now()
        
        start = datetime.now()
        
        try:
            if strategy == RecoveryStrategy.RETRY:
                action.result = await original_fn(*args, **kwargs)
                action.success = True
                
            elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
                delay = min(
                    self.base_delay * (2 ** error_context.attempt_number),
                    self.max_delay
                )
                await asyncio.sleep(delay)
                action.result = await original_fn(*args, **kwargs)
                action.success = True
                
            elif strategy == RecoveryStrategy.FALLBACK_MODEL:
                # Tentar com modelo alternativo
                for fallback in self.fallback_models:
                    try:
                        kwargs['model'] = fallback
                        action.result = await original_fn(*args, **kwargs)
                        action.success = True
                        action.parameters['used_model'] = fallback
                        break
                    except Exception:
                        continue
                
            elif strategy == RecoveryStrategy.SIMPLIFY_REQUEST:
                # Simplificar input
                if 'messages' in kwargs:
                    messages = kwargs['messages']
                    # Manter apenas últimas mensagens
                    kwargs['messages'] = messages[-5:]
                action.result = await original_fn(*args, **kwargs)
                action.success = True
                
            elif strategy == RecoveryStrategy.SPLIT_REQUEST:
                # Dividir requisição grande
                action.error = "Split request not implemented for this context"
                action.success = False
                
            elif strategy == RecoveryStrategy.USE_CACHE:
                # Tentar usar cache
                cache_key = str(args) + str(kwargs)
                if cache_key in self._cache:
                    action.result = self._cache[cache_key]
                    action.success = True
                    action.parameters['from_cache'] = True
                else:
                    action.error = "No cached result available"
                    action.success = False
                
            elif strategy == RecoveryStrategy.ESCALATE:
                action.error = "Escalation required - manual intervention needed"
                action.success = False
                
            elif strategy == RecoveryStrategy.ABORT:
                action.error = "Operation aborted due to unrecoverable error"
                action.success = False
                
        except Exception as e:
            action.success = False
            action.error = str(e)
        
        action.duration_ms = (datetime.now() - start).total_seconds() * 1000
        
        return action


class CircuitBreaker:
    """
    Circuit breaker para proteção contra falhas cascata.
    
    Estados:
    - CLOSED: Normal, permitindo requisições
    - OPEN: Bloqueando requisições após muitas falhas
    - HALF_OPEN: Permitindo uma requisição de teste
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
    
    @property
    def state(self) -> CircuitState:
        """Estado atual do circuit breaker."""
        if self._state == CircuitState.OPEN:
            # Verificar se deve transitar para HALF_OPEN
            if self._last_failure_time:
                elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
        
        return self._state
    
    def can_execute(self) -> bool:
        """Verifica se pode executar uma requisição."""
        state = self.state
        
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.half_open_max_calls
        else:
            return False
    
    def record_success(self) -> None:
        """Registra sucesso."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.half_open_max_calls:
                self._reset()
        else:
            self._failure_count = 0
    
    def record_failure(self) -> None:
        """Registra falha."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
    
    def _reset(self) -> None:
        """Reseta para estado inicial."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0


class SelfHealingAgent:
    """
    Wrapper que adiciona capacidades de self-healing a um agente.
    
    Uso:
    ```python
    from agents import Agent
    from agents.self_healing import SelfHealingAgent
    
    base_agent = Agent(name="assistant", model="gpt-4o")
    healing_agent = SelfHealingAgent(base_agent)
    
    # Executa com recuperação automática
    response = await healing_agent.run("Hello")
    ```
    """
    
    def __init__(
        self,
        agent: Any,  # Agent do SDK
        max_retries: int = 3,
        enable_circuit_breaker: bool = True
    ):
        self.agent = agent
        self.max_retries = max_retries
        
        # Componentes
        self.detector = ErrorDetector()
        self.diagnosis = DiagnosisEngine()
        self.executor = RecoveryExecutor(max_retries=max_retries)
        
        self.circuit_breaker: Optional[CircuitBreaker] = None
        if enable_circuit_breaker:
            self.circuit_breaker = CircuitBreaker()
        
        # Métricas
        self.total_executions = 0
        self.total_recoveries = 0
        self.failed_recoveries = 0
        
        # Histórico
        self._recovery_history: list[tuple[ErrorContext, RecoveryAction]] = []
    
    async def run(
        self,
        user_input: str,
        context: Optional[dict] = None
    ) -> Any:
        """
        Executa agente com recuperação automática.
        
        Args:
            user_input: Input do usuário
            context: Contexto opcional
            
        Returns:
            Resposta do agente
        """
        self.total_executions += 1
        
        # Verificar circuit breaker
        if self.circuit_breaker and not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is open - service temporarily unavailable")
        
        attempt = 0
        last_error: Optional[ErrorContext] = None
        
        while attempt < self.max_retries:
            attempt += 1
            
            try:
                # Executar agente
                result = await self.agent.arun(user_input, context)
                
                # Sucesso
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()
                
                return result
                
            except Exception as e:
                # Detectar e diagnosticar erro
                error_ctx = self.detector.detect(e)
                error_ctx.attempt_number = attempt
                error_ctx.max_attempts = self.max_retries
                error_ctx.agent_id = self.agent.name
                
                diagnosis = self.diagnosis.diagnose(error_ctx)
                
                logger.warning(
                    f"Error detected (attempt {attempt}/{self.max_retries}): "
                    f"{error_ctx.error_type.value} - {error_ctx.message[:100]}"
                )
                
                # Registrar falha no circuit breaker
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
                
                # Tentar recuperação se possível
                if diagnosis.is_recoverable and attempt < self.max_retries:
                    for strategy in diagnosis.recommended_strategies:
                        action = await self.executor.execute(
                            strategy,
                            self.agent.arun,
                            error_ctx,
                            user_input,
                            context
                        )
                        
                        self._recovery_history.append((error_ctx, action))
                        
                        if action.success:
                            self.total_recoveries += 1
                            
                            if self.circuit_breaker:
                                self.circuit_breaker.record_success()
                            
                            logger.info(
                                f"Recovery successful using {strategy.value}"
                            )
                            return action.result
                
                last_error = error_ctx
        
        # Todas as tentativas falharam
        self.failed_recoveries += 1
        
        error_msg = last_error.message if last_error else "Unknown error"
        raise Exception(f"All recovery attempts failed: {error_msg}")
    
    def get_metrics(self) -> dict:
        """Retorna métricas."""
        return {
            "total_executions": self.total_executions,
            "total_recoveries": self.total_recoveries,
            "failed_recoveries": self.failed_recoveries,
            "recovery_rate": self.total_recoveries / max(self.total_executions, 1),
            "circuit_breaker_state": self.circuit_breaker.state.value if self.circuit_breaker else None
        }
    
    def get_recovery_history(self, limit: int = 10) -> list[dict]:
        """Retorna histórico de recuperações."""
        return [
            {
                "error": ctx.to_dict(),
                "action": {
                    "strategy": action.strategy.value,
                    "success": action.success,
                    "duration_ms": action.duration_ms
                }
            }
            for ctx, action in self._recovery_history[-limit:]
        ]
