"""
Agno Flow Studio v3.0 - Workflow Tests

Comprehensive tests for workflow creation, validation, and execution.
"""

import pytest
import asyncio
from datetime import datetime

from ..types import (
    Workflow, Node, Connection, Port, Position,
    NodeType, NodeCategory, DataType, PortType,
    WorkflowStatus, ExecutionStatus
)
from ..validation import WorkflowValidator, ValidationSeverity
from ..engine import WorkflowEngine, get_workflow_engine
from ..executor import register_default_executors
from ..ai.nl_designer import NLWorkflowDesigner, IntentType
from ..ai.optimizer import WorkflowOptimizer
from ..ai.predictor import CostPredictor, ExecutionPredictor


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def simple_workflow():
    """Create a simple input -> agent -> output workflow."""
    workflow = Workflow(
        name="Test Workflow",
        description="A simple test workflow",
    )
    
    # Input node
    input_node = Node(
        id="input_1",
        label="Input",
        node_type=NodeType.INPUT,
        category=NodeCategory.INPUT,
        position=Position(x=100, y=100),
        outputs=[Port(id="out_1", name="data", type=PortType.OUTPUT, data_type=DataType.ANY)],
    )
    
    # Agent node
    agent_node = Node(
        id="agent_1",
        label="AI Agent",
        node_type=NodeType.AGENT,
        category=NodeCategory.AGENTS,
        position=Position(x=350, y=100),
        inputs=[Port(id="in_1", name="message", type=PortType.INPUT, data_type=DataType.MESSAGE, required=True)],
        outputs=[Port(id="out_1", name="response", type=PortType.OUTPUT, data_type=DataType.STRING)],
        config={"model": "gpt-4o-mini", "instructions": "You are a helpful assistant."},
    )
    
    # Output node
    output_node = Node(
        id="output_1",
        label="Output",
        node_type=NodeType.OUTPUT,
        category=NodeCategory.OUTPUT,
        position=Position(x=600, y=100),
        inputs=[Port(id="in_1", name="data", type=PortType.INPUT, data_type=DataType.ANY, required=True)],
    )
    
    workflow.nodes = [input_node, agent_node, output_node]
    
    # Connections
    workflow.edges = [
        Connection(id="edge_1", source="input_1", target="agent_1"),
        Connection(id="edge_2", source="agent_1", target="output_1"),
    ]
    
    return workflow


@pytest.fixture
def complex_workflow():
    """Create a more complex workflow with conditions and loops."""
    workflow = Workflow(
        name="Complex Workflow",
        description="A workflow with conditions and multiple paths",
    )
    
    # Input
    input_node = Node(
        id="input_1",
        label="Input",
        node_type=NodeType.INPUT,
        category=NodeCategory.INPUT,
        position=Position(x=100, y=200),
        outputs=[Port(id="out_1", name="data", type=PortType.OUTPUT, data_type=DataType.ANY)],
    )
    
    # Condition
    condition_node = Node(
        id="condition_1",
        label="Check Type",
        node_type=NodeType.CONDITION,
        category=NodeCategory.LOGIC,
        position=Position(x=300, y=200),
        inputs=[Port(id="in_1", name="value", type=PortType.INPUT, data_type=DataType.ANY, required=True)],
        outputs=[
            Port(id="out_true", name="true", type=PortType.OUTPUT, data_type=DataType.ANY),
            Port(id="out_false", name="false", type=PortType.OUTPUT, data_type=DataType.ANY),
        ],
        config={"condition": "value.get('type') == 'premium'"},
    )
    
    # Agent 1 (premium path)
    agent_premium = Node(
        id="agent_premium",
        label="Premium Agent",
        node_type=NodeType.AGENT,
        category=NodeCategory.AGENTS,
        position=Position(x=500, y=100),
        inputs=[Port(id="in_1", name="message", type=PortType.INPUT, data_type=DataType.MESSAGE, required=True)],
        outputs=[Port(id="out_1", name="response", type=PortType.OUTPUT, data_type=DataType.STRING)],
        config={"model": "gpt-4o", "instructions": "Premium service agent."},
    )
    
    # Agent 2 (standard path)
    agent_standard = Node(
        id="agent_standard",
        label="Standard Agent",
        node_type=NodeType.AGENT,
        category=NodeCategory.AGENTS,
        position=Position(x=500, y=300),
        inputs=[Port(id="in_1", name="message", type=PortType.INPUT, data_type=DataType.MESSAGE, required=True)],
        outputs=[Port(id="out_1", name="response", type=PortType.OUTPUT, data_type=DataType.STRING)],
        config={"model": "gpt-4o-mini", "instructions": "Standard service agent."},
    )
    
    # Output
    output_node = Node(
        id="output_1",
        label="Output",
        node_type=NodeType.OUTPUT,
        category=NodeCategory.OUTPUT,
        position=Position(x=700, y=200),
        inputs=[Port(id="in_1", name="data", type=PortType.INPUT, data_type=DataType.ANY, required=True)],
    )
    
    workflow.nodes = [input_node, condition_node, agent_premium, agent_standard, output_node]
    
    workflow.edges = [
        Connection(id="edge_1", source="input_1", target="condition_1"),
        Connection(id="edge_2", source="condition_1", source_handle="out_true", target="agent_premium"),
        Connection(id="edge_3", source="condition_1", source_handle="out_false", target="agent_standard"),
        Connection(id="edge_4", source="agent_premium", target="output_1"),
        Connection(id="edge_5", source="agent_standard", target="output_1"),
    ]
    
    return workflow


@pytest.fixture
def engine():
    """Create a workflow engine with default executors."""
    engine = WorkflowEngine()
    register_default_executors(engine)
    return engine


# ============================================================
# Type Tests
# ============================================================

class TestTypes:
    """Test type serialization and deserialization."""
    
    def test_node_to_dict(self, simple_workflow):
        """Test node serialization."""
        node = simple_workflow.nodes[1]  # Agent node
        data = node.to_dict()
        
        assert data["id"] == "agent_1"
        assert data["data"]["label"] == "AI Agent"
        assert data["data"]["nodeType"] == "agent"
        assert data["data"]["config"]["model"] == "gpt-4o-mini"
    
    def test_node_from_dict(self):
        """Test node deserialization."""
        data = {
            "id": "test_node",
            "type": "custom",
            "position": {"x": 100, "y": 200},
            "data": {
                "label": "Test Node",
                "nodeType": "transform",
                "category": "data",
                "inputs": [{"id": "in_1", "name": "data", "type": "input", "dataType": "any"}],
                "outputs": [{"id": "out_1", "name": "result", "type": "output", "dataType": "any"}],
                "config": {"code": "data * 2"},
            }
        }
        
        node = Node.from_dict(data)
        
        assert node.id == "test_node"
        assert node.label == "Test Node"
        assert node.node_type == NodeType.TRANSFORM
        assert len(node.inputs) == 1
        assert node.config["code"] == "data * 2"
    
    def test_workflow_to_dict(self, simple_workflow):
        """Test workflow serialization."""
        data = simple_workflow.to_dict()
        
        assert data["name"] == "Test Workflow"
        assert len(data["nodes"]) == 3
        assert len(data["edges"]) == 2
    
    def test_workflow_from_dict(self, simple_workflow):
        """Test workflow deserialization."""
        data = simple_workflow.to_dict()
        workflow = Workflow.from_dict(data)
        
        assert workflow.name == "Test Workflow"
        assert len(workflow.nodes) == 3
        assert len(workflow.edges) == 2


# ============================================================
# Validation Tests
# ============================================================

class TestValidation:
    """Test workflow validation."""
    
    def test_valid_workflow(self, simple_workflow):
        """Test validation of a valid workflow."""
        validator = WorkflowValidator()
        result = validator.validate(simple_workflow)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_missing_input_node(self):
        """Test validation fails without input node."""
        workflow = Workflow(name="No Input")
        workflow.nodes = [
            Node(id="agent_1", label="Agent", node_type=NodeType.AGENT, category=NodeCategory.AGENTS),
            Node(id="output_1", label="Output", node_type=NodeType.OUTPUT, category=NodeCategory.OUTPUT),
        ]
        
        validator = WorkflowValidator()
        result = validator.validate(workflow)
        
        assert not result.is_valid
        assert any("Input" in e.message for e in result.errors)
    
    def test_missing_output_node(self):
        """Test validation fails without output node."""
        workflow = Workflow(name="No Output")
        workflow.nodes = [
            Node(id="input_1", label="Input", node_type=NodeType.INPUT, category=NodeCategory.INPUT),
            Node(id="agent_1", label="Agent", node_type=NodeType.AGENT, category=NodeCategory.AGENTS),
        ]
        
        validator = WorkflowValidator()
        result = validator.validate(workflow)
        
        assert not result.is_valid
        assert any("Output" in e.message for e in result.errors)
    
    def test_orphan_node_warning(self, simple_workflow):
        """Test warning for orphan nodes."""
        # Add an unconnected node
        orphan = Node(
            id="orphan_1",
            label="Orphan",
            node_type=NodeType.TRANSFORM,
            category=NodeCategory.DATA,
        )
        simple_workflow.nodes.append(orphan)
        
        validator = WorkflowValidator()
        result = validator.validate(simple_workflow)
        
        assert any(
            w.severity == ValidationSeverity.WARNING and "not connected" in w.message
            for w in result.issues
        )


# ============================================================
# NL Designer Tests
# ============================================================

class TestNLDesigner:
    """Test natural language workflow designer."""
    
    def test_intent_detection(self):
        """Test intent detection from description."""
        designer = NLWorkflowDesigner()
        
        assert designer._detect_intent("Create an AI chatbot") == IntentType.AI_AGENT
        assert designer._detect_intent("Process and transform data") == IntentType.DATA_PROCESSING
        assert designer._detect_intent("Customer support automation") == IntentType.CUSTOMER_SERVICE
        assert designer._detect_intent("Generate blog content") == IntentType.CONTENT_GENERATION
    
    @pytest.mark.asyncio
    async def test_workflow_generation(self):
        """Test workflow generation from description."""
        designer = NLWorkflowDesigner()
        
        suggestion = await designer.design_workflow(
            "Create an AI agent that answers questions about products"
        )
        
        assert suggestion.workflow is not None
        assert len(suggestion.workflow.nodes) > 0
        assert suggestion.confidence > 0.5
        assert suggestion.explanation is not None
    
    def test_template_generation(self):
        """Test workflow generation from template."""
        designer = NLWorkflowDesigner()
        template = designer.TEMPLATES[IntentType.AI_AGENT]
        
        workflow = designer._generate_from_template(
            template, "Test agent", IntentType.AI_AGENT
        )
        
        assert workflow.name == "AI Agent Workflow"
        assert len(workflow.nodes) == 3
        assert len(workflow.edges) == 2


# ============================================================
# Optimizer Tests
# ============================================================

class TestOptimizer:
    """Test workflow optimizer."""
    
    def test_cost_optimization(self, simple_workflow):
        """Test cost optimization suggestions."""
        # Use expensive model
        simple_workflow.nodes[1].config["model"] = "gpt-4o"
        
        optimizer = WorkflowOptimizer()
        suggestions = optimizer.analyze(simple_workflow)
        
        cost_suggestions = [s for s in suggestions if s.type.value == "cost"]
        assert len(cost_suggestions) > 0
    
    def test_reliability_suggestions(self, complex_workflow):
        """Test reliability optimization suggestions."""
        # Add HTTP node without retry
        http_node = Node(
            id="http_1",
            label="API Call",
            node_type=NodeType.HTTP,
            category=NodeCategory.INTEGRATIONS,
            config={"url": "https://api.example.com"},
        )
        complex_workflow.nodes.append(http_node)
        
        optimizer = WorkflowOptimizer()
        suggestions = optimizer.analyze(complex_workflow)
        
        reliability_suggestions = [s for s in suggestions if s.type.value == "reliability"]
        assert len(reliability_suggestions) > 0


# ============================================================
# Predictor Tests
# ============================================================

class TestPredictor:
    """Test cost and execution predictors."""
    
    def test_cost_prediction(self, simple_workflow):
        """Test cost prediction."""
        predictor = CostPredictor()
        prediction = predictor.predict(simple_workflow)
        
        assert prediction.total_cost >= 0
        assert prediction.confidence > 0
        assert len(prediction.assumptions) > 0
    
    def test_execution_prediction(self, simple_workflow):
        """Test execution time prediction."""
        predictor = ExecutionPredictor()
        prediction = predictor.predict(simple_workflow)
        
        assert prediction.estimated_duration_ms > 0
        assert prediction.min_duration_ms < prediction.max_duration_ms
    
    def test_resource_prediction(self, complex_workflow):
        """Test resource usage prediction."""
        predictor = ExecutionPredictor()
        resources = predictor.predict_resources(complex_workflow)
        
        assert resources.estimated_tokens > 0
        assert resources.estimated_api_calls > 0


# ============================================================
# Engine Tests
# ============================================================

class TestEngine:
    """Test workflow execution engine."""
    
    def test_topological_sort(self, engine, simple_workflow):
        """Test topological sorting of nodes."""
        order = engine._topological_sort(simple_workflow)
        
        assert len(order) == 3
        assert order.index("input_1") < order.index("agent_1")
        assert order.index("agent_1") < order.index("output_1")
    
    def test_breakpoints(self, engine):
        """Test breakpoint management."""
        engine.add_breakpoint("node_1")
        assert "node_1" in engine._breakpoints
        
        engine.remove_breakpoint("node_1")
        assert "node_1" not in engine._breakpoints
        
        engine.add_breakpoint("node_2")
        engine.clear_breakpoints()
        assert len(engine._breakpoints) == 0


# ============================================================
# Integration Tests
# ============================================================

class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_simple_workflow_e2e(self, simple_workflow):
        """Test simple workflow end-to-end."""
        # Validate
        validator = WorkflowValidator()
        validation = validator.validate(simple_workflow)
        assert validation.is_valid
        
        # Get predictions
        cost_predictor = CostPredictor()
        cost = cost_predictor.predict(simple_workflow)
        assert cost.total_cost >= 0
        
        exec_predictor = ExecutionPredictor()
        time = exec_predictor.predict(simple_workflow)
        assert time.estimated_duration_ms > 0
        
        # Get optimizations
        optimizer = WorkflowOptimizer()
        suggestions = optimizer.analyze(simple_workflow)
        # Suggestions may or may not exist
    
    @pytest.mark.asyncio
    async def test_nl_to_workflow_e2e(self):
        """Test natural language to workflow end-to-end."""
        # Design
        designer = NLWorkflowDesigner()
        suggestion = await designer.design_workflow(
            "Create a customer service bot that routes inquiries to the right department"
        )
        
        workflow = suggestion.workflow
        
        # Validate
        validator = WorkflowValidator()
        validation = validator.validate(workflow)
        # May have warnings but should be structurally valid
        
        # Optimize
        optimizer = WorkflowOptimizer()
        optimizations = optimizer.analyze(workflow)
        
        # Predict
        cost_predictor = CostPredictor()
        cost = cost_predictor.predict(workflow)
        
        assert workflow is not None
        assert cost.total_cost >= 0


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
