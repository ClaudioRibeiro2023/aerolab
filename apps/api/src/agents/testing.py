"""
Framework de Testes para Agentes.

Permite testar agentes de forma sistemática com:
- Test suites com casos de uso esperados
- Assertions sobre formato de resposta
- Evaluation metrics (relevance, factuality, coherence)
- Regression testing entre versões
- Benchmarking comparativo

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                    Agent Testing Framework                   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Test Suite   │  │ Evaluator    │  │ Reporter     │      │
│  │              │  │              │  │              │      │
│  │ - Cases      │  │ - Metrics    │  │ - Results    │      │
│  │ - Fixtures   │  │ - Assertions │  │ - Comparison │      │
│  │ - Setup      │  │ - Scoring    │  │ - Export     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
"""

import json
import time
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Awaitable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re


class TestStatus(Enum):
    """Status de um teste."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class AssertionType(Enum):
    """Tipos de assertion."""
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES_REGEX = "matches_regex"
    JSON_VALID = "json_valid"
    JSON_SCHEMA = "json_schema"
    LENGTH_MIN = "length_min"
    LENGTH_MAX = "length_max"
    RESPONSE_TIME = "response_time"
    CUSTOM = "custom"


@dataclass
class Assertion:
    """Uma assertion de teste."""
    type: AssertionType
    value: Any
    message: Optional[str] = None
    
    def check(self, response: str, response_time: float = 0) -> tuple[bool, str]:
        """
        Verifica a assertion.
        
        Returns:
            (passed, message)
        """
        try:
            if self.type == AssertionType.CONTAINS:
                passed = self.value.lower() in response.lower()
                msg = f"Resposta deve conter '{self.value}'"
            
            elif self.type == AssertionType.NOT_CONTAINS:
                passed = self.value.lower() not in response.lower()
                msg = f"Resposta não deve conter '{self.value}'"
            
            elif self.type == AssertionType.MATCHES_REGEX:
                passed = bool(re.search(self.value, response))
                msg = f"Resposta deve corresponder ao padrão '{self.value}'"
            
            elif self.type == AssertionType.JSON_VALID:
                try:
                    json.loads(response)
                    passed = True
                except json.JSONDecodeError:
                    passed = False
                msg = "Resposta deve ser JSON válido"
            
            elif self.type == AssertionType.JSON_SCHEMA:
                try:
                    data = json.loads(response)
                    passed = self._validate_schema(data, self.value)
                except json.JSONDecodeError:
                    passed = False
                msg = "Resposta deve seguir o schema JSON"
            
            elif self.type == AssertionType.LENGTH_MIN:
                passed = len(response) >= self.value
                msg = f"Resposta deve ter no mínimo {self.value} caracteres"
            
            elif self.type == AssertionType.LENGTH_MAX:
                passed = len(response) <= self.value
                msg = f"Resposta deve ter no máximo {self.value} caracteres"
            
            elif self.type == AssertionType.RESPONSE_TIME:
                passed = response_time <= self.value
                msg = f"Tempo de resposta deve ser <= {self.value}ms (foi {response_time:.0f}ms)"
            
            else:
                passed = True
                msg = "Assertion customizada"
            
            return passed, self.message or msg
            
        except Exception as e:
            return False, f"Erro na assertion: {str(e)}"
    
    def _validate_schema(self, data: Any, schema: Dict) -> bool:
        """Validação básica de schema."""
        if "type" in schema:
            expected = schema["type"]
            if expected == "object" and not isinstance(data, dict):
                return False
            if expected == "array" and not isinstance(data, list):
                return False
            if expected == "string" and not isinstance(data, str):
                return False
        
        if "required" in schema and isinstance(data, dict):
            for field in schema["required"]:
                if field not in data:
                    return False
        
        return True


@dataclass
class TestCase:
    """Um caso de teste."""
    id: str
    name: str
    prompt: str
    expected_behavior: str
    assertions: List[Assertion] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    timeout: int = 60000  # ms
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "prompt": self.prompt,
            "expected_behavior": self.expected_behavior,
            "tags": self.tags,
            "timeout": self.timeout
        }


@dataclass
class TestResult:
    """Resultado de um teste."""
    test_case: TestCase
    status: TestStatus
    response: Optional[str] = None
    response_time_ms: float = 0
    assertions_passed: int = 0
    assertions_failed: int = 0
    assertion_results: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_case.id,
            "test_name": self.test_case.name,
            "status": self.status.value,
            "response_time_ms": self.response_time_ms,
            "assertions_passed": self.assertions_passed,
            "assertions_failed": self.assertions_failed,
            "assertion_results": self.assertion_results,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None
        }


@dataclass
class TestSuiteResult:
    """Resultado de uma suite de testes."""
    suite_name: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total_time_ms: float = 0
    results: List[TestResult] = field(default_factory=list)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0
        return self.passed / self.total_tests
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suite_name": self.suite_name,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "success_rate": self.success_rate,
            "total_time_ms": self.total_time_ms,
            "results": [r.to_dict() for r in self.results],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None
        }


class TestSuite:
    """
    Suite de testes para um agente.
    
    Exemplo:
        suite = TestSuite("CustomerSupport Tests")
        
        suite.add_case(TestCase(
            id="greeting",
            name="Saudação inicial",
            prompt="Olá, preciso de ajuda",
            expected_behavior="Responder com saudação cordial",
            assertions=[
                Assertion(AssertionType.CONTAINS, "olá"),
                Assertion(AssertionType.LENGTH_MIN, 20),
            ]
        ))
        
        results = await suite.run(agent_runner)
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.cases: List[TestCase] = []
        self.setup_fn: Optional[Callable] = None
        self.teardown_fn: Optional[Callable] = None
    
    def add_case(self, case: TestCase) -> "TestSuite":
        """Adiciona um caso de teste."""
        self.cases.append(case)
        return self
    
    def add_cases(self, cases: List[TestCase]) -> "TestSuite":
        """Adiciona múltiplos casos de teste."""
        self.cases.extend(cases)
        return self
    
    def setup(self, fn: Callable) -> "TestSuite":
        """Define função de setup."""
        self.setup_fn = fn
        return self
    
    def teardown(self, fn: Callable) -> "TestSuite":
        """Define função de teardown."""
        self.teardown_fn = fn
        return self
    
    def filter_by_tags(self, tags: List[str]) -> List[TestCase]:
        """Filtra casos por tags."""
        return [c for c in self.cases if any(t in c.tags for t in tags)]
    
    async def run(
        self,
        agent_runner: Callable[[str], Awaitable[str]],
        filter_tags: Optional[List[str]] = None,
        parallel: bool = False
    ) -> TestSuiteResult:
        """
        Executa a suite de testes.
        
        Args:
            agent_runner: Função async que executa o agente e retorna resposta
            filter_tags: Filtrar por tags específicas
            parallel: Executar testes em paralelo
            
        Returns:
            TestSuiteResult
        """
        result = TestSuiteResult(suite_name=self.name)
        result.started_at = datetime.now()
        
        cases = self.filter_by_tags(filter_tags) if filter_tags else self.cases
        result.total_tests = len(cases)
        
        # Setup
        if self.setup_fn:
            try:
                if asyncio.iscoroutinefunction(self.setup_fn):
                    await self.setup_fn()
                else:
                    self.setup_fn()
            except Exception as e:
                print(f"Erro no setup: {e}")
        
        # Run tests
        if parallel:
            tasks = [self._run_case(case, agent_runner) for case in cases]
            test_results = await asyncio.gather(*tasks)
        else:
            test_results = []
            for case in cases:
                test_result = await self._run_case(case, agent_runner)
                test_results.append(test_result)
        
        # Aggregate results
        for test_result in test_results:
            result.results.append(test_result)
            result.total_time_ms += test_result.response_time_ms
            
            if test_result.status == TestStatus.PASSED:
                result.passed += 1
            elif test_result.status == TestStatus.FAILED:
                result.failed += 1
            elif test_result.status == TestStatus.SKIPPED:
                result.skipped += 1
            elif test_result.status == TestStatus.ERROR:
                result.errors += 1
        
        # Teardown
        if self.teardown_fn:
            try:
                if asyncio.iscoroutinefunction(self.teardown_fn):
                    await self.teardown_fn()
                else:
                    self.teardown_fn()
            except Exception as e:
                print(f"Erro no teardown: {e}")
        
        result.finished_at = datetime.now()
        return result
    
    async def _run_case(
        self,
        case: TestCase,
        agent_runner: Callable[[str], Awaitable[str]]
    ) -> TestResult:
        """Executa um caso de teste."""
        result = TestResult(test_case=case, status=TestStatus.RUNNING)
        result.started_at = datetime.now()
        
        try:
            # Execute agent
            start_time = time.time()
            response = await asyncio.wait_for(
                agent_runner(case.prompt),
                timeout=case.timeout / 1000
            )
            result.response_time_ms = (time.time() - start_time) * 1000
            result.response = response
            
            # Check assertions
            all_passed = True
            for assertion in case.assertions:
                passed, message = assertion.check(response, result.response_time_ms)
                result.assertion_results.append({
                    "type": assertion.type.value,
                    "passed": passed,
                    "message": message
                })
                if passed:
                    result.assertions_passed += 1
                else:
                    result.assertions_failed += 1
                    all_passed = False
            
            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            
        except asyncio.TimeoutError:
            result.status = TestStatus.ERROR
            result.error = f"Timeout após {case.timeout}ms"
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error = str(e)
        
        result.finished_at = datetime.now()
        return result


class QualityEvaluator:
    """
    Avaliador de qualidade de respostas.
    
    Métricas:
    - Relevância: Resposta é relevante ao prompt
    - Coerência: Resposta é lógica e bem estruturada
    - Completude: Resposta aborda todos os pontos
    - Concisão: Resposta é direta sem ser muito longa
    """
    
    def __init__(self):
        self._weights = {
            "relevance": 0.35,
            "coherence": 0.25,
            "completeness": 0.25,
            "conciseness": 0.15
        }
    
    def evaluate(
        self,
        prompt: str,
        response: str,
        expected_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Avalia qualidade da resposta.
        
        Returns:
            Dict com scores por dimensão e score final
        """
        scores = {}
        
        # Relevância (baseada em keywords)
        if expected_keywords:
            found = sum(1 for kw in expected_keywords if kw.lower() in response.lower())
            scores["relevance"] = found / len(expected_keywords)
        else:
            # Heurística: overlap de palavras significativas
            prompt_words = set(w.lower() for w in prompt.split() if len(w) > 3)
            response_words = set(w.lower() for w in response.split() if len(w) > 3)
            if prompt_words:
                overlap = len(prompt_words & response_words) / len(prompt_words)
                scores["relevance"] = min(1.0, overlap * 2)  # Escalar
            else:
                scores["relevance"] = 0.5
        
        # Coerência (heurística baseada em estrutura)
        sentences = response.split('.')
        avg_sentence_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        # Sentenças muito curtas ou muito longas indicam má coerência
        if 5 <= avg_sentence_len <= 25:
            scores["coherence"] = 0.9
        elif 3 <= avg_sentence_len <= 35:
            scores["coherence"] = 0.7
        else:
            scores["coherence"] = 0.5
        
        # Completude (baseada em tamanho)
        response_len = len(response)
        if response_len < 50:
            scores["completeness"] = 0.3
        elif response_len < 200:
            scores["completeness"] = 0.6
        elif response_len < 1000:
            scores["completeness"] = 0.9
        else:
            scores["completeness"] = 0.8  # Muito longo pode indicar verbosidade
        
        # Concisão (penalizar respostas muito longas para prompts curtos)
        prompt_len = len(prompt)
        ratio = response_len / max(prompt_len, 1)
        if ratio < 2:
            scores["conciseness"] = 0.6
        elif ratio < 10:
            scores["conciseness"] = 0.9
        elif ratio < 30:
            scores["conciseness"] = 0.7
        else:
            scores["conciseness"] = 0.4
        
        # Score final ponderado
        final_score = sum(
            scores[dim] * weight 
            for dim, weight in self._weights.items()
        )
        
        return {
            "scores": scores,
            "final_score": final_score,
            "grade": self._score_to_grade(final_score)
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Converte score para grade."""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"


class BenchmarkRunner:
    """
    Runner para benchmarks comparativos entre agentes/versões.
    """
    
    def __init__(self, test_suite: TestSuite):
        self.test_suite = test_suite
        self.results: Dict[str, TestSuiteResult] = {}
    
    async def run_benchmark(
        self,
        agents: Dict[str, Callable[[str], Awaitable[str]]],
        iterations: int = 1
    ) -> Dict[str, Any]:
        """
        Executa benchmark comparativo.
        
        Args:
            agents: Dict de nome -> runner function
            iterations: Número de iterações por teste
            
        Returns:
            Comparação entre agentes
        """
        for agent_name, runner in agents.items():
            all_results = []
            for _ in range(iterations):
                result = await self.test_suite.run(runner)
                all_results.append(result)
            
            # Agregar resultados
            self.results[agent_name] = self._aggregate_results(all_results)
        
        return self._generate_comparison()
    
    def _aggregate_results(self, results: List[TestSuiteResult]) -> TestSuiteResult:
        """Agrega múltiplas execuções."""
        if not results:
            return TestSuiteResult(suite_name=self.test_suite.name)
        
        aggregated = TestSuiteResult(suite_name=self.test_suite.name)
        aggregated.total_tests = results[0].total_tests
        aggregated.passed = sum(r.passed for r in results) // len(results)
        aggregated.failed = sum(r.failed for r in results) // len(results)
        aggregated.total_time_ms = sum(r.total_time_ms for r in results) / len(results)
        
        return aggregated
    
    def _generate_comparison(self) -> Dict[str, Any]:
        """Gera comparação entre agentes."""
        comparison = {
            "suite_name": self.test_suite.name,
            "agents": {}
        }
        
        for agent_name, result in self.results.items():
            comparison["agents"][agent_name] = {
                "success_rate": result.success_rate,
                "avg_time_ms": result.total_time_ms / max(result.total_tests, 1),
                "passed": result.passed,
                "failed": result.failed
            }
        
        # Ranking
        ranked = sorted(
            comparison["agents"].items(),
            key=lambda x: (x[1]["success_rate"], -x[1]["avg_time_ms"]),
            reverse=True
        )
        comparison["ranking"] = [name for name, _ in ranked]
        
        return comparison


class TestReporter:
    """
    Gerador de relatórios de teste.
    """
    
    def generate_console_report(self, result: TestSuiteResult) -> str:
        """Gera relatório para console."""
        lines = [
            "=" * 60,
            f"Test Suite: {result.suite_name}",
            "=" * 60,
            f"Total: {result.total_tests} | Passed: {result.passed} | Failed: {result.failed} | Errors: {result.errors}",
            f"Success Rate: {result.success_rate * 100:.1f}%",
            f"Total Time: {result.total_time_ms:.0f}ms",
            "-" * 60,
        ]
        
        for test_result in result.results:
            status_icon = {
                TestStatus.PASSED: "✅",
                TestStatus.FAILED: "❌",
                TestStatus.ERROR: "💥",
                TestStatus.SKIPPED: "⏭️"
            }.get(test_result.status, "❓")
            
            lines.append(f"{status_icon} {test_result.test_case.name} ({test_result.response_time_ms:.0f}ms)")
            
            if test_result.status == TestStatus.FAILED:
                for ar in test_result.assertion_results:
                    if not ar["passed"]:
                        lines.append(f"   ❌ {ar['message']}")
            
            if test_result.error:
                lines.append(f"   💥 Error: {test_result.error}")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def generate_json_report(self, result: TestSuiteResult) -> str:
        """Gera relatório JSON."""
        return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    
    def generate_html_report(self, result: TestSuiteResult) -> str:
        """Gera relatório HTML."""
        status_class = "success" if result.success_rate > 0.9 else "warning" if result.success_rate > 0.7 else "danger"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Report: {result.suite_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1a1a2e; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }}
        .stat {{ background: #f5f5f5; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; }}
        .test {{ border: 1px solid #ddd; border-radius: 8px; margin-bottom: 10px; overflow: hidden; }}
        .test-header {{ padding: 15px; display: flex; justify-content: space-between; align-items: center; }}
        .passed {{ background: #d4edda; }}
        .failed {{ background: #f8d7da; }}
        .error {{ background: #fff3cd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{result.suite_name}</h1>
        <p>Executed at {result.started_at.strftime('%Y-%m-%d %H:%M:%S') if result.started_at else 'N/A'}</p>
    </div>
    
    <div class="stats">
        <div class="stat"><div class="stat-value">{result.total_tests}</div>Total</div>
        <div class="stat"><div class="stat-value" style="color: green;">{result.passed}</div>Passed</div>
        <div class="stat"><div class="stat-value" style="color: red;">{result.failed}</div>Failed</div>
        <div class="stat"><div class="stat-value">{result.success_rate * 100:.1f}%</div>Success Rate</div>
    </div>
    
    <h2>Test Results</h2>
"""
        
        for tr in result.results:
            status_class = "passed" if tr.status == TestStatus.PASSED else "failed" if tr.status == TestStatus.FAILED else "error"
            html += f"""
    <div class="test">
        <div class="test-header {status_class}">
            <span><strong>{tr.test_case.name}</strong></span>
            <span>{tr.response_time_ms:.0f}ms</span>
        </div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html
    
    def save_report(self, result: TestSuiteResult, path: str, format: str = "json"):
        """Salva relatório em arquivo."""
        if format == "json":
            content = self.generate_json_report(result)
        elif format == "html":
            content = self.generate_html_report(result)
        else:
            content = self.generate_console_report(result)
        
        Path(path).write_text(content, encoding="utf-8")


# Predefined test cases for common scenarios
def create_basic_test_suite(agent_type: str = "general") -> TestSuite:
    """
    Cria suite de testes básica.
    """
    suite = TestSuite(f"Basic {agent_type} Tests")
    
    if agent_type == "support":
        suite.add_cases([
            TestCase(
                id="greeting",
                name="Saudação",
                prompt="Olá, preciso de ajuda",
                expected_behavior="Responder cordialmente",
                assertions=[
                    Assertion(AssertionType.LENGTH_MIN, 20),
                    Assertion(AssertionType.RESPONSE_TIME, 5000),
                ]
            ),
            TestCase(
                id="problem_understanding",
                name="Entendimento do Problema",
                prompt="Meu pedido não chegou e já fazem 10 dias",
                expected_behavior="Demonstrar empatia e pedir informações",
                assertions=[
                    Assertion(AssertionType.LENGTH_MIN, 50),
                    Assertion(AssertionType.RESPONSE_TIME, 5000),
                ],
                tags=["critical"]
            ),
        ])
    
    elif agent_type == "coding":
        suite.add_cases([
            TestCase(
                id="code_generation",
                name="Geração de Código",
                prompt="Escreva uma função Python que calcula fatorial",
                expected_behavior="Retornar código Python válido",
                assertions=[
                    Assertion(AssertionType.CONTAINS, "def"),
                    Assertion(AssertionType.CONTAINS, "return"),
                    Assertion(AssertionType.RESPONSE_TIME, 10000),
                ]
            ),
            TestCase(
                id="code_explanation",
                name="Explicação de Código",
                prompt="Explique o que faz: list(map(lambda x: x**2, range(10)))",
                expected_behavior="Explicar compreensão de lista/map",
                assertions=[
                    Assertion(AssertionType.LENGTH_MIN, 100),
                ],
                tags=["explanation"]
            ),
        ])
    
    else:  # general
        suite.add_cases([
            TestCase(
                id="basic_qa",
                name="Q&A Básico",
                prompt="Qual é a capital do Brasil?",
                expected_behavior="Responder corretamente",
                assertions=[
                    Assertion(AssertionType.CONTAINS, "Brasília"),
                    Assertion(AssertionType.RESPONSE_TIME, 3000),
                ]
            ),
            TestCase(
                id="instruction_following",
                name="Seguir Instruções",
                prompt="Liste 3 cores primárias",
                expected_behavior="Listar exatamente 3 cores",
                assertions=[
                    Assertion(AssertionType.LENGTH_MIN, 10),
                ]
            ),
        ])
    
    return suite


# Factory
def create_test_suite(
    name: str,
    cases: Optional[List[Dict]] = None
) -> TestSuite:
    """
    Cria suite de testes a partir de configuração.
    """
    suite = TestSuite(name)
    
    if cases:
        for case_dict in cases:
            assertions = []
            for a in case_dict.get("assertions", []):
                assertions.append(Assertion(
                    type=AssertionType(a["type"]),
                    value=a["value"],
                    message=a.get("message")
                ))
            
            suite.add_case(TestCase(
                id=case_dict["id"],
                name=case_dict["name"],
                prompt=case_dict["prompt"],
                expected_behavior=case_dict.get("expected", ""),
                assertions=assertions,
                tags=case_dict.get("tags", [])
            ))
    
    return suite
