"""
Módulo de Agentes - Agentes Base e Avançados

Inclui:
- BaseAgent: Agente base da plataforma
- AgentBuilder: Builder fluent para agentes avançados
- SelfHealingAgent: Agente com auto-recuperação
- PlanningAgent: Agente com capacidades de planejamento
- MemoryManager: Sistema de memória (short/long term, episodic)
- AgentTelemetry: Sistema de telemetria e métricas
- AutoTuner: Auto-tuning de parâmetros
- AgentEnsemble: Orquestração de múltiplos agentes
- AgentVersionManager: Versionamento de agentes
"""

# Imports condicionais para evitar erros de importação circular
__all__ = []

# Core
try:
    from .base_agent import BaseAgent
    __all__.append("BaseAgent")
except ImportError:
    pass

try:
    from .builder import AgentBuilder, quick_agent, research_agent, coding_agent, support_agent
    __all__.extend(["AgentBuilder", "quick_agent", "research_agent", "coding_agent", "support_agent"])
except ImportError:
    pass

# Advanced Features
try:
    from .self_healing import SelfHealingAgent
    __all__.append("SelfHealingAgent")
except ImportError:
    pass

try:
    from .planning import PlanningAgent
    __all__.append("PlanningAgent")
except ImportError:
    pass

try:
    from .memory import MemoryManager, ShortTermMemory, LongTermMemory, EpisodicMemory
    __all__.extend(["MemoryManager", "ShortTermMemory", "LongTermMemory", "EpisodicMemory"])
except ImportError:
    pass

try:
    from .telemetry import AgentTelemetry, get_telemetry
    __all__.extend(["AgentTelemetry", "get_telemetry"])
except ImportError:
    pass

try:
    from .autotuning import AutoTuner, create_tuner
    __all__.extend(["AutoTuner", "create_tuner"])
except ImportError:
    pass

try:
    from .ensemble import AgentEnsemble, create_ensemble
    __all__.extend(["AgentEnsemble", "create_ensemble"])
except ImportError:
    pass

try:
    from .versioning import AgentVersionManager, get_version_manager
    __all__.extend(["AgentVersionManager", "get_version_manager"])
except ImportError:
    pass

try:
    from .guardrails import Guardrails, GuardrailsConfig, create_guardrails
    __all__.extend(["Guardrails", "GuardrailsConfig", "create_guardrails"])
except ImportError:
    pass

try:
    from .testing import TestSuite, TestCase, TestResult, create_test_suite, create_basic_test_suite
    __all__.extend(["TestSuite", "TestCase", "TestResult", "create_test_suite", "create_basic_test_suite"])
except ImportError:
    pass

try:
    from .skills import Skill, SkillRegistry, SkillComposer, get_skill_registry, list_skills, compose_agent_with_skills
    __all__.extend(["Skill", "SkillRegistry", "SkillComposer", "get_skill_registry", "list_skills", "compose_agent_with_skills"])
except ImportError:
    pass

try:
    from .benchmarks import BenchmarkSuite, BenchmarkResult, Leaderboard, get_benchmark, list_benchmarks, run_benchmark
    __all__.extend(["BenchmarkSuite", "BenchmarkResult", "Leaderboard", "get_benchmark", "list_benchmarks", "run_benchmark"])
except ImportError:
    pass

try:
    from .dynamic_tuning import DynamicTuner, TuningStrategy, get_tuner, create_tuner
    __all__.extend(["DynamicTuner", "TuningStrategy", "get_tuner", "create_tuner"])
except ImportError:
    pass
