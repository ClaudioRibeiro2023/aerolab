"""
Sistema de Benchmarks para Agentes.

Permite avaliar e comparar agentes em diferentes dimensões:
- Performance (latência, throughput)
- Qualidade (accuracy, relevance, coherence)
- Custo (tokens, pricing)
- Robustez (error handling, edge cases)

Inclui benchmarks pré-definidos por domínio e suporte a benchmarks customizados.

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                    Benchmark System                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Benchmark    │  │ Evaluator    │  │ Leaderboard  │      │
│  │ Suite        │  │              │  │              │      │
│  │              │  │ - Metrics    │  │ - Ranking    │      │
│  │ - Tasks      │  │ - Scoring    │  │ - Compare    │      │
│  │ - Datasets   │  │ - Aggregate  │  │ - History    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
"""

import json
import time
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Awaitable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import statistics


class BenchmarkCategory(Enum):
    """Categorias de benchmark."""
    GENERAL = "general"
    REASONING = "reasoning"
    CODING = "coding"
    CREATIVE = "creative"
    FACTUAL = "factual"
    INSTRUCTION_FOLLOWING = "instruction_following"
    CONVERSATION = "conversation"
    MULTILINGUAL = "multilingual"


class MetricType(Enum):
    """Tipos de métrica."""
    LATENCY = "latency"
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
    COST = "cost"
    TOKENS = "tokens"
    ERROR_RATE = "error_rate"


@dataclass
class BenchmarkTask:
    """Uma tarefa de benchmark."""
    id: str
    category: BenchmarkCategory
    prompt: str
    expected_output: Optional[str] = None
    expected_keywords: List[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "prompt": self.prompt,
            "expected_keywords": self.expected_keywords,
            "difficulty": self.difficulty
        }


@dataclass
class TaskResult:
    """Resultado de uma tarefa de benchmark."""
    task_id: str
    success: bool
    response: str
    latency_ms: float
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    scores: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "latency_ms": self.latency_ms,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost_usd": self.cost_usd,
            "scores": self.scores,
            "error": self.error
        }


@dataclass
class BenchmarkResult:
    """Resultado agregado de um benchmark."""
    benchmark_id: str
    agent_id: str
    model_id: str
    timestamp: datetime
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    
    # Métricas agregadas
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    
    # Scores
    accuracy_score: float = 0.0
    relevance_score: float = 0.0
    coherence_score: float = 0.0
    overall_score: float = 0.0
    
    # Detalhes
    task_results: List[TaskResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "agent_id": self.agent_id,
            "model_id": self.model_id,
            "timestamp": self.timestamp.isoformat(),
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "avg_latency_ms": self.avg_latency_ms,
            "p50_latency_ms": self.p50_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "accuracy_score": self.accuracy_score,
            "relevance_score": self.relevance_score,
            "coherence_score": self.coherence_score,
            "overall_score": self.overall_score
        }


class BenchmarkEvaluator:
    """
    Avaliador de respostas de benchmark.
    """
    
    def __init__(self):
        self._weights = {
            "accuracy": 0.4,
            "relevance": 0.3,
            "coherence": 0.2,
            "efficiency": 0.1
        }
    
    def evaluate_response(
        self,
        task: BenchmarkTask,
        response: str,
        latency_ms: float
    ) -> Dict[str, float]:
        """
        Avalia uma resposta.
        
        Returns:
            Dict com scores por dimensão
        """
        scores = {}
        
        # Accuracy (baseada em keywords esperadas)
        if task.expected_keywords:
            found = sum(1 for kw in task.expected_keywords if kw.lower() in response.lower())
            scores["accuracy"] = found / len(task.expected_keywords)
        elif task.expected_output:
            # Comparação simplificada
            similarity = self._simple_similarity(response, task.expected_output)
            scores["accuracy"] = similarity
        else:
            scores["accuracy"] = 0.7  # Default se não há expectativa
        
        # Relevance (heurística)
        prompt_words = set(w.lower() for w in task.prompt.split() if len(w) > 3)
        response_words = set(w.lower() for w in response.split() if len(w) > 3)
        if prompt_words:
            overlap = len(prompt_words & response_words) / len(prompt_words)
            scores["relevance"] = min(1.0, overlap * 2)
        else:
            scores["relevance"] = 0.5
        
        # Coherence (baseada em estrutura)
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        if sentences:
            avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
            if 5 <= avg_len <= 25:
                scores["coherence"] = 0.9
            elif 3 <= avg_len <= 35:
                scores["coherence"] = 0.7
            else:
                scores["coherence"] = 0.5
        else:
            scores["coherence"] = 0.3
        
        # Efficiency (baseada em latência)
        if latency_ms < 1000:
            scores["efficiency"] = 1.0
        elif latency_ms < 3000:
            scores["efficiency"] = 0.8
        elif latency_ms < 5000:
            scores["efficiency"] = 0.6
        else:
            scores["efficiency"] = 0.4
        
        return scores
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade simples entre textos."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """Calcula score geral ponderado."""
        total = sum(
            scores.get(dim, 0) * weight
            for dim, weight in self._weights.items()
        )
        return total


class BenchmarkSuite:
    """
    Suite de benchmark com tarefas predefinidas.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        category: BenchmarkCategory = BenchmarkCategory.GENERAL
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.tasks: List[BenchmarkTask] = []
        self.evaluator = BenchmarkEvaluator()
    
    def add_task(self, task: BenchmarkTask) -> "BenchmarkSuite":
        """Adiciona tarefa ao benchmark."""
        self.tasks.append(task)
        return self
    
    def add_tasks(self, tasks: List[BenchmarkTask]) -> "BenchmarkSuite":
        """Adiciona múltiplas tarefas."""
        self.tasks.extend(tasks)
        return self
    
    async def run(
        self,
        agent_runner: Callable[[str], Awaitable[str]],
        agent_id: str = "unknown",
        model_id: str = "unknown",
        parallel: bool = False,
        max_concurrent: int = 5
    ) -> BenchmarkResult:
        """
        Executa o benchmark.
        
        Args:
            agent_runner: Função que executa o agente
            agent_id: ID do agente
            model_id: ID do modelo
            parallel: Executar em paralelo
            max_concurrent: Máximo de tarefas concorrentes
        """
        result = BenchmarkResult(
            benchmark_id=self.id,
            agent_id=agent_id,
            model_id=model_id,
            timestamp=datetime.now(),
            total_tasks=len(self.tasks)
        )
        
        task_results = []
        latencies = []
        
        if parallel:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def run_with_semaphore(task):
                async with semaphore:
                    return await self._run_task(task, agent_runner)
            
            task_results = await asyncio.gather(*[
                run_with_semaphore(task) for task in self.tasks
            ])
        else:
            for task in self.tasks:
                task_result = await self._run_task(task, agent_runner)
                task_results.append(task_result)
        
        # Agregar resultados
        for tr in task_results:
            result.task_results.append(tr)
            
            if tr.success:
                result.completed_tasks += 1
                latencies.append(tr.latency_ms)
            else:
                result.failed_tasks += 1
            
            result.total_tokens += tr.tokens_in + tr.tokens_out
            result.total_cost_usd += tr.cost_usd
        
        # Calcular métricas de latência
        if latencies:
            result.avg_latency_ms = statistics.mean(latencies)
            result.p50_latency_ms = statistics.median(latencies)
            sorted_latencies = sorted(latencies)
            p95_idx = int(len(sorted_latencies) * 0.95)
            result.p95_latency_ms = sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)]
        
        # Calcular scores agregados
        if result.completed_tasks > 0:
            accuracy_scores = [tr.scores.get("accuracy", 0) for tr in task_results if tr.success]
            relevance_scores = [tr.scores.get("relevance", 0) for tr in task_results if tr.success]
            coherence_scores = [tr.scores.get("coherence", 0) for tr in task_results if tr.success]
            
            result.accuracy_score = statistics.mean(accuracy_scores) if accuracy_scores else 0
            result.relevance_score = statistics.mean(relevance_scores) if relevance_scores else 0
            result.coherence_score = statistics.mean(coherence_scores) if coherence_scores else 0
            
            result.overall_score = self.evaluator.calculate_overall_score({
                "accuracy": result.accuracy_score,
                "relevance": result.relevance_score,
                "coherence": result.coherence_score,
                "efficiency": 1 - (result.failed_tasks / result.total_tasks) if result.total_tasks > 0 else 0
            })
        
        return result
    
    async def _run_task(
        self,
        task: BenchmarkTask,
        agent_runner: Callable[[str], Awaitable[str]]
    ) -> TaskResult:
        """Executa uma tarefa individual."""
        start_time = time.time()
        
        try:
            response = await asyncio.wait_for(
                agent_runner(task.prompt),
                timeout=60.0
            )
            latency_ms = (time.time() - start_time) * 1000
            
            # Avaliar resposta
            scores = self.evaluator.evaluate_response(task, response, latency_ms)
            
            return TaskResult(
                task_id=task.id,
                success=True,
                response=response,
                latency_ms=latency_ms,
                scores=scores
            )
            
        except asyncio.TimeoutError:
            return TaskResult(
                task_id=task.id,
                success=False,
                response="",
                latency_ms=(time.time() - start_time) * 1000,
                error="Timeout"
            )
        except Exception as e:
            return TaskResult(
                task_id=task.id,
                success=False,
                response="",
                latency_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )


class Leaderboard:
    """
    Leaderboard para comparar resultados de benchmarks.
    """
    
    def __init__(self, benchmark_id: str):
        self.benchmark_id = benchmark_id
        self.entries: List[BenchmarkResult] = []
    
    def add_result(self, result: BenchmarkResult) -> None:
        """Adiciona resultado ao leaderboard."""
        if result.benchmark_id == self.benchmark_id:
            self.entries.append(result)
            self._sort()
    
    def _sort(self) -> None:
        """Ordena por overall_score descendente."""
        self.entries.sort(key=lambda x: x.overall_score, reverse=True)
    
    def get_ranking(self, top_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retorna ranking."""
        entries = self.entries[:top_n] if top_n else self.entries
        
        return [
            {
                "rank": i + 1,
                "agent_id": entry.agent_id,
                "model_id": entry.model_id,
                "overall_score": entry.overall_score,
                "accuracy": entry.accuracy_score,
                "latency_ms": entry.avg_latency_ms,
                "cost_usd": entry.total_cost_usd,
                "timestamp": entry.timestamp.isoformat()
            }
            for i, entry in enumerate(entries)
        ]
    
    def compare(self, agent_ids: List[str]) -> Dict[str, Any]:
        """Compara agentes específicos."""
        filtered = [e for e in self.entries if e.agent_id in agent_ids]
        
        return {
            "benchmark_id": self.benchmark_id,
            "comparison": [
                {
                    "agent_id": e.agent_id,
                    "model_id": e.model_id,
                    "overall_score": e.overall_score,
                    "accuracy": e.accuracy_score,
                    "relevance": e.relevance_score,
                    "coherence": e.coherence_score,
                    "avg_latency_ms": e.avg_latency_ms,
                    "total_cost_usd": e.total_cost_usd
                }
                for e in filtered
            ]
        }


# Benchmarks pré-definidos
def create_general_benchmark() -> BenchmarkSuite:
    """Cria benchmark geral."""
    suite = BenchmarkSuite(
        id="general_v1",
        name="General Intelligence Benchmark",
        description="Avalia capacidades gerais do agente",
        category=BenchmarkCategory.GENERAL
    )
    
    suite.add_tasks([
        BenchmarkTask(
            id="gen_01",
            category=BenchmarkCategory.GENERAL,
            prompt="Qual é a capital do Brasil e qual sua população aproximada?",
            expected_keywords=["Brasília", "milhões"],
            difficulty="easy"
        ),
        BenchmarkTask(
            id="gen_02",
            category=BenchmarkCategory.GENERAL,
            prompt="Explique brevemente o que é machine learning.",
            expected_keywords=["aprendizado", "dados", "modelo", "padrões"],
            difficulty="easy"
        ),
        BenchmarkTask(
            id="gen_03",
            category=BenchmarkCategory.REASONING,
            prompt="Se hoje é quarta-feira, que dia será daqui a 10 dias?",
            expected_keywords=["sábado"],
            difficulty="medium"
        ),
        BenchmarkTask(
            id="gen_04",
            category=BenchmarkCategory.INSTRUCTION_FOLLOWING,
            prompt="Liste exatamente 5 frutas tropicais, uma por linha.",
            expected_keywords=["manga", "abacaxi", "banana", "mamão", "maracujá"],
            difficulty="medium"
        ),
        BenchmarkTask(
            id="gen_05",
            category=BenchmarkCategory.CREATIVE,
            prompt="Escreva um haiku sobre tecnologia.",
            expected_keywords=[],  # Criativo, sem keywords específicas
            difficulty="medium"
        ),
    ])
    
    return suite


def create_coding_benchmark() -> BenchmarkSuite:
    """Cria benchmark de coding."""
    suite = BenchmarkSuite(
        id="coding_v1",
        name="Coding Proficiency Benchmark",
        description="Avalia capacidades de programação",
        category=BenchmarkCategory.CODING
    )
    
    suite.add_tasks([
        BenchmarkTask(
            id="code_01",
            category=BenchmarkCategory.CODING,
            prompt="Escreva uma função Python que retorna o fatorial de um número.",
            expected_keywords=["def", "return", "factorial", "*"],
            difficulty="easy"
        ),
        BenchmarkTask(
            id="code_02",
            category=BenchmarkCategory.CODING,
            prompt="Escreva uma função que verifica se uma string é um palíndromo.",
            expected_keywords=["def", "return", "[::-1]"],
            difficulty="easy"
        ),
        BenchmarkTask(
            id="code_03",
            category=BenchmarkCategory.CODING,
            prompt="Implemente uma classe Python para uma pilha (stack) com métodos push e pop.",
            expected_keywords=["class", "def", "push", "pop", "self"],
            difficulty="medium"
        ),
        BenchmarkTask(
            id="code_04",
            category=BenchmarkCategory.CODING,
            prompt="Escreva uma função que encontra o segundo maior número em uma lista.",
            expected_keywords=["def", "return", "sorted", "max"],
            difficulty="medium"
        ),
        BenchmarkTask(
            id="code_05",
            category=BenchmarkCategory.CODING,
            prompt="Implemente o algoritmo de busca binária em Python.",
            expected_keywords=["def", "while", "mid", "left", "right", "return"],
            difficulty="hard"
        ),
    ])
    
    return suite


def create_reasoning_benchmark() -> BenchmarkSuite:
    """Cria benchmark de reasoning."""
    suite = BenchmarkSuite(
        id="reasoning_v1",
        name="Reasoning & Logic Benchmark",
        description="Avalia capacidades de raciocínio lógico",
        category=BenchmarkCategory.REASONING
    )
    
    suite.add_tasks([
        BenchmarkTask(
            id="reason_01",
            category=BenchmarkCategory.REASONING,
            prompt="Se todos os gatos são mamíferos e todos os mamíferos são animais, o que podemos concluir sobre os gatos?",
            expected_keywords=["animais"],
            difficulty="easy"
        ),
        BenchmarkTask(
            id="reason_02",
            category=BenchmarkCategory.REASONING,
            prompt="Um trem viaja a 60 km/h. Quantas horas leva para percorrer 180 km?",
            expected_keywords=["3", "horas"],
            difficulty="easy"
        ),
        BenchmarkTask(
            id="reason_03",
            category=BenchmarkCategory.REASONING,
            prompt="Maria é mais alta que João. João é mais alto que Pedro. Quem é o mais baixo?",
            expected_keywords=["Pedro"],
            difficulty="medium"
        ),
        BenchmarkTask(
            id="reason_04",
            category=BenchmarkCategory.REASONING,
            prompt="Se 5 máquinas produzem 5 peças em 5 minutos, quantas peças 100 máquinas produzem em 100 minutos?",
            expected_keywords=["2000"],
            difficulty="hard"
        ),
        BenchmarkTask(
            id="reason_05",
            category=BenchmarkCategory.REASONING,
            prompt="Em uma sala há 3 lâmpadas desligadas. Fora da sala há 3 interruptores. Você pode entrar na sala apenas uma vez. Como descobrir qual interruptor controla qual lâmpada?",
            expected_keywords=["acender", "quente", "fria", "temperatura"],
            difficulty="hard"
        ),
    ])
    
    return suite


# Factory
_benchmarks: Dict[str, BenchmarkSuite] = {}


def get_benchmark(benchmark_id: str) -> Optional[BenchmarkSuite]:
    """Obtém benchmark por ID."""
    if not _benchmarks:
        _benchmarks["general_v1"] = create_general_benchmark()
        _benchmarks["coding_v1"] = create_coding_benchmark()
        _benchmarks["reasoning_v1"] = create_reasoning_benchmark()
    
    return _benchmarks.get(benchmark_id)


def list_benchmarks() -> List[Dict[str, Any]]:
    """Lista benchmarks disponíveis."""
    if not _benchmarks:
        _benchmarks["general_v1"] = create_general_benchmark()
        _benchmarks["coding_v1"] = create_coding_benchmark()
        _benchmarks["reasoning_v1"] = create_reasoning_benchmark()
    
    return [
        {
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "category": b.category.value,
            "task_count": len(b.tasks)
        }
        for b in _benchmarks.values()
    ]


async def run_benchmark(
    benchmark_id: str,
    agent_runner: Callable[[str], Awaitable[str]],
    agent_id: str = "unknown",
    model_id: str = "unknown"
) -> Optional[BenchmarkResult]:
    """
    Executa um benchmark.
    
    Exemplo:
        result = await run_benchmark(
            "general_v1",
            agent_runner=my_agent.run,
            agent_id="my_agent",
            model_id="gpt-5.1"
        )
    """
    benchmark = get_benchmark(benchmark_id)
    if not benchmark:
        return None
    
    return await benchmark.run(agent_runner, agent_id, model_id)
