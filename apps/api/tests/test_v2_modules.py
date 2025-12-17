"""
Testes dos Módulos v2.0 da Plataforma Agno

Testa todos os componentes implementados:
- Rules Engine
- Self-Healing Agents
- Planning System
- Agent Studio
- Observability Tracing
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime
from typing import Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ==================== RULES ENGINE TESTS ====================

class TestRulesTypes:
    """Testes para types do Rules Engine."""
    
    def test_rule_severity_enum(self):
        """Testa enum RuleSeverity."""
        from rules.types import RuleSeverity
        
        assert RuleSeverity.INFO.value == "info"
        assert RuleSeverity.WARNING.value == "warning"
        assert RuleSeverity.ERROR.value == "error"
        assert RuleSeverity.CRITICAL.value == "critical"
    
    def test_rule_category_enum(self):
        """Testa enum RuleCategory."""
        from rules.types import RuleCategory
        
        assert RuleCategory.SECURITY.value == "security"
        assert RuleCategory.COMPLIANCE.value == "compliance"
        assert RuleCategory.CUSTOM.value == "custom"
    
    def test_rule_condition_creation(self):
        """Testa criação de RuleCondition."""
        from rules.types import RuleCondition, ConditionOperator
        
        condition = RuleCondition(
            target_field="content",
            operator=ConditionOperator.CONTAINS,
            value="test"
        )
        
        assert condition.target_field == "content"
        assert condition.operator == ConditionOperator.CONTAINS
        assert condition.value == "test"
    
    def test_rule_creation(self):
        """Testa criação de Rule."""
        from rules.types import Rule, RuleSeverity, RuleCategory, RuleCondition, ConditionOperator
        
        rule = Rule(
            id="test_rule",
            name="Test Rule",
            description="A test rule",
            severity=RuleSeverity.WARNING,
            category=RuleCategory.SECURITY,
            condition=RuleCondition(
                target_field="content",
                operator=ConditionOperator.NOT_CONTAINS,
                value="password"
            )
        )
        
        assert rule.id == "test_rule"
        assert rule.severity == RuleSeverity.WARNING
        assert rule.condition is not None
    
    def test_rule_to_dict(self):
        """Testa serialização de Rule."""
        from rules.types import Rule, RuleSeverity, RuleCategory
        
        rule = Rule(
            id="test",
            name="Test",
            severity=RuleSeverity.INFO,
            category=RuleCategory.BUSINESS
        )
        
        data = rule.to_dict()
        
        assert data["id"] == "test"
        assert data["severity"] == "info"
        assert "name" in data


class TestRulesValidators:
    """Testes para validators do Rules Engine."""
    
    def test_pii_validator_email(self):
        """Testa detecção de email."""
        from rules.validators import PIIValidator
        
        validator = PIIValidator()
        
        # Com email
        result = validator.validate("Contact me at john@example.com")
        assert len(result) > 0
        assert any("email" in v.rule_id for v in result)
        
        # Sem email
        result = validator.validate("Hello world")
        email_violations = [v for v in result if "email" in v.rule_id]
        assert len(email_violations) == 0
    
    def test_pii_validator_phone(self):
        """Testa detecção de telefone."""
        from rules.validators import PIIValidator
        
        validator = PIIValidator()
        
        # Com telefone brasileiro
        result = validator.validate("Ligue para (11) 98765-4321")
        assert len(result) > 0
    
    def test_pii_validator_cpf(self):
        """Testa detecção de CPF."""
        from rules.validators import PIIValidator
        
        validator = PIIValidator()
        
        # Com CPF
        result = validator.validate("Meu CPF é 123.456.789-00")
        cpf_violations = [v for v in result if "cpf" in v.rule_id]
        assert len(cpf_violations) > 0
    
    def test_security_validator_sql_injection(self):
        """Testa detecção de SQL injection."""
        from rules.validators import SecurityValidator
        
        validator = SecurityValidator()
        
        # Com SQL injection
        result = validator.validate("SELECT * FROM users WHERE id = '1' OR '1'='1'")
        sql_violations = [v for v in result if "sql" in v.rule_id.lower()]
        assert len(sql_violations) > 0
        
        # Texto normal
        result = validator.validate("Hello, this is a normal message")
        sql_violations = [v for v in result if "sql" in v.rule_id.lower()]
        assert len(sql_violations) == 0
    
    def test_format_validator_length(self):
        """Testa validação de comprimento."""
        from rules.validators import FormatValidator
        
        validator = FormatValidator(max_length=10)
        
        # Texto longo
        result = validator.validate("This is a very long text that exceeds the limit")
        length_violations = [v for v in result if "length" in v.rule_id]
        assert len(length_violations) > 0
        
        # Texto curto
        result = validator.validate("Short")
        length_violations = [v for v in result if "length" in v.rule_id]
        assert len(length_violations) == 0


class TestRulesEngine:
    """Testes para o RulesEngine."""
    
    def test_engine_creation(self):
        """Testa criação do engine."""
        from rules.engine import RulesEngine
        
        engine = RulesEngine()
        
        assert engine is not None
        assert len(engine._rules) >= 0
    
    def test_add_rule(self):
        """Testa adição de regra."""
        from rules.engine import RulesEngine
        from rules.types import Rule, RuleSeverity, RuleCategory, RuleCondition, ConditionOperator
        
        engine = RulesEngine()
        initial_count = len(engine._rules)
        
        rule = Rule(
            id="custom_rule",
            name="Custom Rule",
            severity=RuleSeverity.WARNING,
            category=RuleCategory.BUSINESS,
            condition=RuleCondition(
                target_field="content",
                operator=ConditionOperator.NOT_CONTAINS,
                value="forbidden"
            )
        )
        
        engine.add_rule(rule)
        
        assert len(engine._rules) == initial_count + 1
        assert engine.get_rule("custom_rule") is not None
    
    def test_validate_content(self):
        """Testa validação de conteúdo."""
        from rules.engine import RulesEngine
        import asyncio
        import inspect
        
        engine = RulesEngine()
        
        # Verificar se é async ou não
        validate_method = engine.validate
        if inspect.iscoroutinefunction(validate_method):
            result = asyncio.run(engine.validate("My email is test@example.com"))
        else:
            result = engine.validate("My email is test@example.com")
        
        assert result is not None
        assert hasattr(result, "passed")
        assert hasattr(result, "violations")
    
    def test_factory_rules(self):
        """Testa verificação de regra por id."""
        from rules.engine import RulesEngine
        from rules.types import Rule, RuleSeverity, RuleCategory
        
        engine = RulesEngine()
        
        # Adicionar regra primeiro
        engine.add_rule(Rule(
            id="test_rule_factory",
            name="Test Rule",
            severity=RuleSeverity.INFO,
            category=RuleCategory.CUSTOM
        ))
        
        # Obter regra
        rule = engine.get_rule("test_rule_factory")
        
        assert rule is not None
        assert rule.id == "test_rule_factory"


class TestRulesFeedback:
    """Testes para o FeedbackGenerator."""
    
    def test_feedback_generator_creation(self):
        """Testa criação do gerador de feedback."""
        from rules.feedback import FeedbackGenerator
        
        generator = FeedbackGenerator()
        
        assert generator is not None
    
    def test_generate_feedback(self):
        """Testa geração de feedback."""
        from rules.feedback import FeedbackGenerator
        from rules.types import Violation, RuleSeverity, RuleCategory, ValidationResult
        
        generator = FeedbackGenerator()
        
        violation = Violation(
            rule_id="pii_email",
            rule_name="Email Detection",
            severity=RuleSeverity.WARNING,
            category=RuleCategory.SECURITY,
            message="Email detected",
            matched_content="test@example.com"
        )
        
        # Criar resultado de validação
        result = ValidationResult(passed=False)
        result.add_violation(violation)
        
        # Gerar feedback
        import asyncio
        feedback = asyncio.run(generator.generate(result, "My email is test@example.com"))
        
        assert feedback is not None
    
    def test_feedback_generator_templates(self):
        """Testa que o gerador tem templates configurados."""
        from rules.feedback import FeedbackGenerator
        
        generator = FeedbackGenerator()
        
        # Verificar que tem templates de explicação
        assert hasattr(generator, 'EXPLANATION_TEMPLATES')
        assert len(generator.EXPLANATION_TEMPLATES) > 0


# ==================== SELF-HEALING TESTS ====================

class TestSelfHealingTypes:
    """Testes para tipos do Self-Healing."""
    
    def test_error_type_enum(self):
        """Testa enum ErrorType."""
        import sys
        sys.path.insert(0, 'src')
        from src.agents.self_healing import ErrorType
        
        assert ErrorType.TIMEOUT.value == "timeout"
        assert ErrorType.RATE_LIMIT.value == "rate_limit"
        assert ErrorType.API_ERROR.value == "api_error"
    
    def test_recovery_strategy_enum(self):
        """Testa enum RecoveryStrategy."""
        from src.agents.self_healing import RecoveryStrategy
        
        assert RecoveryStrategy.RETRY.value == "retry"
        assert RecoveryStrategy.RETRY_WITH_BACKOFF.value == "retry_with_backoff"
        assert RecoveryStrategy.FALLBACK_MODEL.value == "fallback_model"
    
    def test_circuit_state_enum(self):
        """Testa enum CircuitState."""
        from src.agents.self_healing import CircuitState
        
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestErrorDetector:
    """Testes para ErrorDetector."""
    
    def test_detect_timeout(self):
        """Testa detecção de timeout."""
        from src.agents.self_healing import ErrorDetector, ErrorType
        
        detector = ErrorDetector()
        
        error = Exception("Connection timed out")
        context = detector.detect(error)
        
        assert context.error_type == ErrorType.TIMEOUT
    
    def test_detect_rate_limit(self):
        """Testa detecção de rate limit."""
        from src.agents.self_healing import ErrorDetector, ErrorType
        
        detector = ErrorDetector()
        
        error = Exception("Rate limit exceeded - too many requests")
        context = detector.detect(error)
        
        assert context.error_type == ErrorType.RATE_LIMIT
    
    def test_detect_unknown(self):
        """Testa erro desconhecido."""
        from src.agents.self_healing import ErrorDetector, ErrorType
        
        detector = ErrorDetector()
        
        error = Exception("Some random error")
        context = detector.detect(error)
        
        assert context.error_type == ErrorType.UNKNOWN


class TestDiagnosisEngine:
    """Testes para DiagnosisEngine."""
    
    def test_diagnose_timeout(self):
        """Testa diagnóstico de timeout."""
        from src.agents.self_healing import DiagnosisEngine, ErrorContext, ErrorType, RecoveryStrategy
        
        engine = DiagnosisEngine()
        
        error = ErrorContext(
            error_type=ErrorType.TIMEOUT,
            message="Request timed out"
        )
        
        diagnosis = engine.diagnose(error)
        
        assert diagnosis.is_transient == True
        assert RecoveryStrategy.RETRY_WITH_BACKOFF in diagnosis.recommended_strategies
    
    def test_diagnose_permission(self):
        """Testa diagnóstico de erro de permissão."""
        from src.agents.self_healing import DiagnosisEngine, ErrorContext, ErrorType
        
        engine = DiagnosisEngine()
        
        error = ErrorContext(
            error_type=ErrorType.PERMISSION,
            message="Unauthorized access"
        )
        
        diagnosis = engine.diagnose(error)
        
        assert diagnosis.is_recoverable == False


class TestCircuitBreaker:
    """Testes para CircuitBreaker."""
    
    def test_initial_state_closed(self):
        """Testa estado inicial."""
        from src.agents.self_healing import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() == True
    
    def test_opens_after_failures(self):
        """Testa abertura após falhas."""
        from src.agents.self_healing import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(failure_threshold=3)
        
        # Registrar falhas
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() == False
    
    def test_success_resets_counter(self):
        """Testa que sucesso reseta contador."""
        from src.agents.self_healing import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(failure_threshold=3)
        
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0


# ==================== PLANNING TESTS ====================

class TestPlanningTypes:
    """Testes para tipos do Planning System."""
    
    def test_planning_strategy_enum(self):
        """Testa enum PlanningStrategy."""
        from src.agents.planning import PlanningStrategy
        
        assert PlanningStrategy.REACT.value == "react"
        assert PlanningStrategy.COT.value == "cot"
        assert PlanningStrategy.TOT.value == "tot"
    
    def test_step_status_enum(self):
        """Testa enum StepStatus."""
        from src.agents.planning import StepStatus
        
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.IN_PROGRESS.value == "in_progress"
        assert StepStatus.COMPLETED.value == "completed"


class TestPlanStep:
    """Testes para PlanStep."""
    
    def test_plan_step_creation(self):
        """Testa criação de PlanStep."""
        from src.agents.planning import PlanStep, StepStatus
        
        step = PlanStep(
            id=1,
            description="Analyze the problem",
            reasoning="Need to understand before solving"
        )
        
        assert step.id == 1
        assert step.status == StepStatus.PENDING
        assert step.result is None
    
    def test_plan_step_to_dict(self):
        """Testa serialização de PlanStep."""
        from src.agents.planning import PlanStep
        
        step = PlanStep(id=1, description="Test step")
        
        data = step.to_dict()
        
        assert data["id"] == 1
        assert data["description"] == "Test step"
        assert data["status"] == "pending"


class TestPlan:
    """Testes para Plan."""
    
    def test_plan_creation(self):
        """Testa criação de Plan."""
        from src.agents.planning import Plan, PlanningStrategy
        
        plan = Plan(
            goal="Complete the task",
            strategy=PlanningStrategy.REACT
        )
        
        assert plan.goal == "Complete the task"
        assert plan.strategy == PlanningStrategy.REACT
        assert len(plan.steps) == 0
    
    def test_plan_add_step(self):
        """Testa adição de step."""
        from src.agents.planning import Plan, PlanStep, PlanningStrategy
        
        plan = Plan(goal="Test", strategy=PlanningStrategy.DECOMPOSE)
        
        step = PlanStep(id=0, description="First step")
        plan.add_step(step)
        
        assert len(plan.steps) == 1
        assert plan.steps[0].id == 1  # ID é atribuído automaticamente
    
    def test_plan_advance(self):
        """Testa avanço de steps."""
        from src.agents.planning import Plan, PlanStep, PlanningStrategy
        
        plan = Plan(goal="Test", strategy=PlanningStrategy.DECOMPOSE)
        plan.add_step(PlanStep(id=0, description="Step 1"))
        plan.add_step(PlanStep(id=0, description="Step 2"))
        
        assert plan.current_step == 0
        
        result = plan.advance()
        
        assert result == True
        assert plan.current_step == 1


# ==================== STUDIO TESTS ====================

class TestStudioTypes:
    """Testes para tipos do Studio."""
    
    def test_node_type_enum(self):
        """Testa enum NodeType."""
        from studio.types import NodeType
        
        assert NodeType.AGENT.value == "agent"
        assert NodeType.TOOL.value == "tool"
        assert NodeType.CONDITION.value == "condition"
    
    def test_workflow_state_enum(self):
        """Testa enum WorkflowState."""
        from studio.types import WorkflowState
        
        assert WorkflowState.DRAFT.value == "draft"
        assert WorkflowState.PUBLISHED.value == "published"
    
    def test_position_creation(self):
        """Testa criação de Position."""
        from studio.types import Position
        
        pos = Position(x=100, y=200)
        
        assert pos.x == 100
        assert pos.y == 200
        
        data = pos.to_dict()
        assert data == {"x": 100, "y": 200}
    
    def test_port_creation(self):
        """Testa criação de Port."""
        from studio.types import Port, PortType, DataType
        
        port = Port(
            name="input",
            type=PortType.INPUT,
            data_type=DataType.STRING,
            required=True
        )
        
        assert port.name == "input"
        assert port.type == PortType.INPUT
        assert port.required == True


class TestNode:
    """Testes para Node."""
    
    def test_node_creation(self):
        """Testa criação de Node."""
        from studio.types import Node, NodeType
        
        node = Node(
            type=NodeType.AGENT,
            name="My Agent"
        )
        
        assert node.type == NodeType.AGENT
        assert node.name == "My Agent"
        assert len(node.id) > 0
    
    def test_node_add_ports(self):
        """Testa adição de portas."""
        from studio.types import Node, NodeType, DataType
        
        node = Node(type=NodeType.AGENT, name="Test")
        
        input_port = node.add_input("message", DataType.STRING, required=True)
        output_port = node.add_output("response", DataType.STRING)
        
        assert len(node.inputs) == 1
        assert len(node.outputs) == 1
        assert node.get_input_port("message") is not None
        assert node.get_output_port("response") is not None


class TestWorkflow:
    """Testes para Workflow."""
    
    def test_workflow_creation(self):
        """Testa criação de Workflow."""
        from studio.types import Workflow
        
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow"
        )
        
        assert workflow.name == "Test Workflow"
        assert len(workflow.nodes) == 0
        assert len(workflow.connections) == 0
    
    def test_workflow_add_node(self):
        """Testa adição de nó."""
        from studio.types import Workflow, Node, NodeType
        
        workflow = Workflow(name="Test")
        node = Node(type=NodeType.AGENT, name="Agent")
        
        workflow.add_node(node)
        
        assert len(workflow.nodes) == 1
        assert workflow.get_node(node.id) is not None
    
    def test_workflow_remove_node(self):
        """Testa remoção de nó."""
        from studio.types import Workflow, Node, NodeType
        
        workflow = Workflow(name="Test")
        node = Node(type=NodeType.AGENT, name="Agent")
        workflow.add_node(node)
        
        result = workflow.remove_node(node.id)
        
        assert result == True
        assert len(workflow.nodes) == 0
    
    def test_workflow_validate_empty(self):
        """Testa validação de workflow vazio."""
        from studio.types import Workflow
        
        workflow = Workflow(name="Empty")
        
        errors = workflow.validate()
        
        assert len(errors) > 0
        assert any("Input" in e for e in errors)


class TestNodes:
    """Testes para nós especializados."""
    
    def test_input_node(self):
        """Testa InputNode."""
        from studio.nodes import InputNode
        from studio.types import NodeType
        
        node = InputNode(name="User Input")
        
        assert node.type == NodeType.INPUT
        assert len(node.outputs) >= 1
    
    def test_output_node(self):
        """Testa OutputNode."""
        from studio.nodes import OutputNode
        from studio.types import NodeType
        
        node = OutputNode(name="Result")
        
        assert node.type == NodeType.OUTPUT
        assert len(node.inputs) >= 1
    
    def test_agent_node(self):
        """Testa AgentNode."""
        from studio.nodes import AgentNode
        from studio.types import NodeType
        
        node = AgentNode(
            name="Assistant",
            model="gpt-4o",
            instructions="You are helpful"
        )
        
        assert node.type == NodeType.AGENT
        assert node.config["model"] == "gpt-4o"
        assert node.config["instructions"] == "You are helpful"
    
    def test_condition_node(self):
        """Testa ConditionNode."""
        from studio.nodes import ConditionNode
        from studio.types import NodeType
        
        node = ConditionNode(
            name="Route",
            condition="'billing' in value"
        )
        
        assert node.type == NodeType.CONDITION
        assert node.config["condition"] == "'billing' in value"
        assert len(node.outputs) >= 2  # true e false
    
    def test_create_node_factory(self):
        """Testa factory function."""
        from studio.nodes import create_node
        from studio.types import NodeType
        
        node = create_node("agent", name="Test Agent", model="gpt-4o")
        
        assert node.type == NodeType.AGENT


class TestWorkflowBuilder:
    """Testes para WorkflowBuilder."""
    
    def test_builder_creation(self):
        """Testa criação do builder."""
        from studio.builder import WorkflowBuilder
        
        builder = WorkflowBuilder("My Workflow")
        
        assert builder.workflow.name == "My Workflow"
    
    def test_builder_add_nodes(self):
        """Testa adição de nós."""
        from studio.builder import WorkflowBuilder
        
        builder = WorkflowBuilder("Test")
        
        input_node = builder.add_input("Input")
        agent_node = builder.add_agent("Agent", model="gpt-4o")
        output_node = builder.add_output("Output")
        
        assert len(builder.workflow.nodes) == 3
    
    def test_builder_connect(self):
        """Testa conexão de nós."""
        from studio.builder import WorkflowBuilder
        
        builder = WorkflowBuilder("Test")
        
        input_node = builder.add_input("Input")
        output_node = builder.add_output("Output")
        
        conn = builder.connect(input_node, output_node)
        
        assert len(builder.workflow.connections) == 1
        assert conn.source_node_id == input_node.id
        assert conn.target_node_id == output_node.id
    
    def test_builder_chain(self):
        """Testa encadeamento de nós."""
        from studio.builder import WorkflowBuilder
        
        builder = WorkflowBuilder("Test")
        
        n1 = builder.add_input("Input")
        n2 = builder.add_agent("Agent")
        n3 = builder.add_output("Output")
        
        builder.chain(n1, n2, n3)
        
        assert len(builder.workflow.connections) == 2
    
    def test_builder_build_valid(self):
        """Testa build de workflow válido."""
        from studio.builder import WorkflowBuilder
        
        builder = WorkflowBuilder("Valid Workflow")
        
        input_node = builder.add_input("Input")
        output_node = builder.add_output("Output")
        builder.connect(input_node, output_node)
        
        workflow = builder.build(validate=True)
        
        assert workflow is not None
        assert workflow.name == "Valid Workflow"
    
    def test_builder_to_json(self):
        """Testa exportação JSON."""
        from studio.builder import WorkflowBuilder
        import json
        
        builder = WorkflowBuilder("JSON Test")
        builder.add_input("Input")
        builder.add_output("Output")
        
        json_str = builder.to_json()
        data = json.loads(json_str)
        
        assert data["name"] == "JSON Test"
        assert len(data["nodes"]) == 2


class TestTemplateLibrary:
    """Testes para TemplateLibrary."""
    
    def test_library_creation(self):
        """Testa criação da biblioteca."""
        from studio.templates import TemplateLibrary
        
        library = TemplateLibrary()
        
        assert library is not None
    
    def test_builtin_templates(self):
        """Testa templates built-in."""
        from studio.templates import get_template_library
        
        library = get_template_library()
        
        templates = library.list_templates()
        
        assert len(templates) >= 5  # Pelo menos 5 templates
    
    def test_get_customer_support_template(self):
        """Testa template de customer support."""
        from studio.templates import get_template_library
        
        library = get_template_library()
        
        template = library.get_template("customer_support")
        
        assert template is not None
        assert template.name == "Customer Support"
        assert len(template.workflow.nodes) >= 4
    
    def test_get_rag_qa_template(self):
        """Testa template de RAG Q&A."""
        from studio.templates import get_template_library
        
        library = get_template_library()
        
        template = library.get_template("rag_qa")
        
        assert template is not None
        assert "RAG" in template.name
    
    def test_get_categories(self):
        """Testa listagem de categorias."""
        from studio.templates import get_template_library
        
        library = get_template_library()
        
        categories = library.get_categories()
        
        assert len(categories) >= 3


# ==================== TRACING TESTS ====================

class TestTracingTypes:
    """Testes para tipos do Tracing."""
    
    def test_span_kind_enum(self):
        """Testa enum SpanKind."""
        from observability.tracing import SpanKind
        
        assert SpanKind.INTERNAL.value == "internal"
        assert SpanKind.CLIENT.value == "client"
        assert SpanKind.SERVER.value == "server"
    
    def test_span_status_enum(self):
        """Testa enum SpanStatus."""
        from observability.tracing import SpanStatus
        
        assert SpanStatus.OK.value == "ok"
        assert SpanStatus.ERROR.value == "error"
        assert SpanStatus.UNSET.value == "unset"


class TestSpanContext:
    """Testes para SpanContext."""
    
    def test_span_context_creation(self):
        """Testa criação de SpanContext."""
        from observability.tracing import SpanContext
        
        context = SpanContext(
            trace_id="trace123",
            span_id="span456"
        )
        
        assert context.trace_id == "trace123"
        assert context.span_id == "span456"
        assert context.parent_span_id is None
    
    def test_span_context_serialization(self):
        """Testa serialização de SpanContext."""
        from observability.tracing import SpanContext
        
        context = SpanContext(
            trace_id="trace123",
            span_id="span456",
            baggage={"user": "test"}
        )
        
        data = context.to_dict()
        
        assert data["trace_id"] == "trace123"
        assert data["baggage"]["user"] == "test"


class TestSpan:
    """Testes para Span."""
    
    def test_span_creation(self):
        """Testa criação de Span."""
        from observability.tracing import Span, SpanContext, SpanKind, SpanStatus
        
        context = SpanContext(trace_id="t1", span_id="s1")
        span = Span(name="test_operation", context=context)
        
        assert span.name == "test_operation"
        assert span.status == SpanStatus.UNSET
        assert span.is_recording == True
    
    def test_span_set_attribute(self):
        """Testa definição de atributos."""
        from observability.tracing import Span, SpanContext
        
        span = Span(
            name="test",
            context=SpanContext(trace_id="t1", span_id="s1")
        )
        
        span.set_attribute("key", "value")
        span.set_attributes({"a": 1, "b": 2})
        
        assert span.attributes["key"] == "value"
        assert span.attributes["a"] == 1
    
    def test_span_add_event(self):
        """Testa adição de eventos."""
        from observability.tracing import Span, SpanContext
        
        span = Span(
            name="test",
            context=SpanContext(trace_id="t1", span_id="s1")
        )
        
        span.add_event("checkpoint", {"step": 1})
        
        assert len(span.events) == 1
        assert span.events[0].name == "checkpoint"
    
    def test_span_record_exception(self):
        """Testa registro de exceção."""
        from observability.tracing import Span, SpanContext, SpanStatus
        
        span = Span(
            name="test",
            context=SpanContext(trace_id="t1", span_id="s1")
        )
        
        span.record_exception(ValueError("Test error"))
        
        assert span.status == SpanStatus.ERROR
        assert len(span.events) == 1
        assert span.events[0].name == "exception"
    
    def test_span_end(self):
        """Testa finalização de span."""
        from observability.tracing import Span, SpanContext
        
        span = Span(
            name="test",
            context=SpanContext(trace_id="t1", span_id="s1")
        )
        
        assert span.is_recording == True
        
        span.end()
        
        assert span.is_recording == False
        assert span.end_time is not None


class TestTracer:
    """Testes para Tracer."""
    
    def test_tracer_creation(self):
        """Testa criação do Tracer."""
        from observability.tracing import Tracer
        
        tracer = Tracer(service_name="test_service")
        
        assert tracer.service_name == "test_service"
    
    def test_tracer_start_span(self):
        """Testa criação de span via context manager."""
        from observability.tracing import Tracer, SpanStatus
        
        tracer = Tracer()
        
        with tracer.start_span("test_operation") as span:
            span.set_attribute("test", True)
        
        # Span deve estar finalizado
        assert span.is_recording == False
        assert span.status == SpanStatus.OK
    
    def test_tracer_nested_spans(self):
        """Testa spans aninhados."""
        from observability.tracing import Tracer
        
        tracer = Tracer()
        
        with tracer.start_span("parent") as parent:
            parent_trace_id = parent.context.trace_id
            
            with tracer.start_span("child") as child:
                # Child deve ter mesmo trace_id
                assert child.context.trace_id == parent_trace_id
                # Child deve ter parent_span_id
                assert child.context.parent_span_id == parent.context.span_id
    
    def test_tracer_exception_handling(self):
        """Testa tratamento de exceção."""
        from observability.tracing import Tracer, SpanStatus
        
        tracer = Tracer()
        
        span_ref = None
        
        try:
            with tracer.start_span("failing_operation") as span:
                span_ref = span
                raise ValueError("Test error")
        except ValueError:
            pass
        
        assert span_ref.status == SpanStatus.ERROR
        assert len(span_ref.events) == 1


class TestSpanExporters:
    """Testes para exportadores de spans."""
    
    def test_in_memory_exporter(self):
        """Testa InMemorySpanExporter."""
        from observability.tracing import InMemorySpanExporter, Span, SpanContext
        
        exporter = InMemorySpanExporter()
        
        span = Span(
            name="test",
            context=SpanContext(trace_id="t1", span_id="s1")
        )
        span.end()
        
        exporter.export([span])
        
        spans = exporter.get_spans()
        
        assert len(spans) == 1
        assert spans[0].name == "test"
    
    def test_in_memory_exporter_limit(self):
        """Testa limite de spans."""
        from observability.tracing import InMemorySpanExporter, Span, SpanContext
        
        exporter = InMemorySpanExporter(max_spans=5)
        
        for i in range(10):
            span = Span(
                name=f"span_{i}",
                context=SpanContext(trace_id="t1", span_id=f"s{i}")
            )
            exporter.export([span])
        
        spans = exporter.get_spans()
        
        assert len(spans) == 5
    
    def test_in_memory_exporter_get_traces(self):
        """Testa agrupamento em traces."""
        from observability.tracing import InMemorySpanExporter, Span, SpanContext
        
        exporter = InMemorySpanExporter()
        
        # Criar spans de dois traces
        exporter.export([
            Span(name="s1", context=SpanContext(trace_id="t1", span_id="s1")),
            Span(name="s2", context=SpanContext(trace_id="t1", span_id="s2")),
            Span(name="s3", context=SpanContext(trace_id="t2", span_id="s3"))
        ])
        
        traces = exporter.get_traces()
        
        assert len(traces) == 2


# ==================== MAIN ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
