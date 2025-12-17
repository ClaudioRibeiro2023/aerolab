"""
Agno Flow Studio v3.0 - API Routes

REST API endpoints for workflow management.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from ..types import Workflow, Execution, ExecutionStatus
from ..engine import get_workflow_engine
from ..validation import WorkflowValidator
from ..ai.nl_designer import NLWorkflowDesigner
from ..ai.optimizer import WorkflowOptimizer
from ..ai.predictor import CostPredictor, ExecutionPredictor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/flow-studio", tags=["Flow Studio"])

# In-memory storage (replace with database in production)
workflows_db: Dict[str, dict] = {}
executions_db: Dict[str, dict] = {}


# ============================================================
# Request/Response Models
# ============================================================

class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    nodes: List[dict] = []
    edges: List[dict] = []


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[dict]] = None
    edges: Optional[List[dict]] = None
    status: Optional[str] = None


class ExecuteRequest(BaseModel):
    input: Dict[str, Any] = {}


class NLDesignRequest(BaseModel):
    description: str
    language: str = "en"


class OptimizeRequest(BaseModel):
    workflow_id: str


# ============================================================
# Workflow CRUD
# ============================================================

@router.get("/workflows")
async def list_workflows(
    status: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List all workflows."""
    workflows = list(workflows_db.values())
    
    if status:
        workflows = [w for w in workflows if w.get("status") == status]
    if tag:
        workflows = [w for w in workflows if tag in w.get("tags", [])]
    
    return {
        "items": workflows[offset:offset+limit],
        "total": len(workflows),
        "limit": limit,
        "offset": offset,
    }


@router.post("/workflows")
async def create_workflow(data: WorkflowCreate):
    """Create a new workflow."""
    workflow = Workflow(
        name=data.name,
        description=data.description,
    )
    
    # Parse nodes and edges
    for node_data in data.nodes:
        from ..types import Node
        workflow.nodes.append(Node.from_dict(node_data))
    
    for edge_data in data.edges:
        from ..types import Connection
        workflow.edges.append(Connection.from_dict(edge_data))
    
    # Store
    workflow_dict = workflow.to_dict()
    workflows_db[workflow.id] = workflow_dict
    
    return workflow_dict


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a workflow by ID."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflows_db[workflow_id]


@router.put("/workflows/{workflow_id}")
async def update_workflow(workflow_id: str, data: WorkflowUpdate):
    """Update a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows_db[workflow_id]
    
    if data.name is not None:
        workflow["name"] = data.name
    if data.description is not None:
        workflow["description"] = data.description
    if data.nodes is not None:
        workflow["nodes"] = data.nodes
    if data.edges is not None:
        workflow["edges"] = data.edges
    if data.status is not None:
        workflow["status"] = data.status
    
    from datetime import datetime
    workflow["updatedAt"] = datetime.now().isoformat()
    
    workflows_db[workflow_id] = workflow
    return workflow


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del workflows_db[workflow_id]
    return {"deleted": True}


# ============================================================
# Validation
# ============================================================

@router.post("/workflows/{workflow_id}/validate")
async def validate_workflow(workflow_id: str):
    """Validate a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = Workflow.from_dict(workflows_db[workflow_id])
    validator = WorkflowValidator()
    result = validator.validate(workflow)
    
    return result.to_dict()


# ============================================================
# Execution
# ============================================================

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    data: ExecuteRequest,
    background_tasks: BackgroundTasks
):
    """Execute a workflow."""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = Workflow.from_dict(workflows_db[workflow_id])
    
    # Validate first
    validator = WorkflowValidator()
    validation = validator.validate(workflow)
    
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow validation failed: {[e.message for e in validation.errors]}"
        )
    
    # Create execution
    execution = Execution(
        workflow_id=workflow_id,
        status=ExecutionStatus.PENDING,
        input_data=data.input,
    )
    executions_db[execution.id] = execution.to_dict()
    
    # Run in background
    async def run_execution():
        engine = get_workflow_engine()
        result = await engine.execute(workflow, data.input)
        executions_db[execution.id] = result.to_dict()
    
    background_tasks.add_task(run_execution)
    
    return {
        "executionId": execution.id,
        "status": "started",
        "message": "Execution started in background",
    }


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str):
    """Get execution status and result."""
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")
    return executions_db[execution_id]


@router.post("/executions/{execution_id}/stop")
async def stop_execution(execution_id: str):
    """Stop a running execution."""
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    engine = get_workflow_engine()
    engine.stop(execution_id)
    
    return {"stopped": True}


# ============================================================
# AI Features
# ============================================================

@router.post("/ai/design")
async def design_workflow_from_nl(data: NLDesignRequest):
    """Generate workflow from natural language description."""
    designer = NLWorkflowDesigner()
    suggestion = await designer.design_workflow(
        description=data.description,
        language=data.language
    )
    
    return suggestion.to_dict()


@router.post("/ai/optimize")
async def optimize_workflow(data: OptimizeRequest):
    """Get optimization suggestions for a workflow."""
    if data.workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = Workflow.from_dict(workflows_db[data.workflow_id])
    optimizer = WorkflowOptimizer()
    suggestions = optimizer.analyze(workflow)
    
    return {
        "suggestions": [s.to_dict() for s in suggestions],
        "count": len(suggestions),
    }


@router.post("/ai/predict-cost")
async def predict_cost(data: OptimizeRequest):
    """Predict workflow execution cost."""
    if data.workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = Workflow.from_dict(workflows_db[data.workflow_id])
    predictor = CostPredictor()
    prediction = predictor.predict(workflow)
    
    return prediction.to_dict()


@router.post("/ai/predict-time")
async def predict_execution_time(data: OptimizeRequest):
    """Predict workflow execution time."""
    if data.workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = Workflow.from_dict(workflows_db[data.workflow_id])
    predictor = ExecutionPredictor()
    prediction = predictor.predict(workflow)
    
    return prediction.to_dict()


# ============================================================
# Templates
# ============================================================

@router.get("/templates")
async def list_templates():
    """List available workflow templates."""
    from ..ai.nl_designer import NLWorkflowDesigner
    
    templates = []
    for intent, template in NLWorkflowDesigner.TEMPLATES.items():
        templates.append({
            "id": intent.value,
            "name": template["name"],
            "nodeCount": len(template.get("nodes", [])),
            "category": intent.value,
        })
    
    return {"templates": templates}


@router.post("/templates/{template_id}/create")
async def create_from_template(template_id: str, name: Optional[str] = None):
    """Create a workflow from a template."""
    from ..ai.nl_designer import NLWorkflowDesigner, IntentType
    
    try:
        intent = IntentType(template_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = NLWorkflowDesigner.TEMPLATES.get(intent)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    designer = NLWorkflowDesigner()
    workflow = designer._generate_from_template(
        template,
        name or template["name"],
        intent
    )
    workflow.name = name or template["name"]
    
    # Store
    workflow_dict = workflow.to_dict()
    workflows_db[workflow.id] = workflow_dict
    
    return workflow_dict


# ============================================================
# Health & Stats
# ============================================================

@router.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "service": "flow-studio",
        "version": "3.0.0",
    }


@router.get("/stats")
async def stats():
    """Get service statistics."""
    return {
        "workflowCount": len(workflows_db),
        "executionCount": len(executions_db),
        "activeExecutions": sum(
            1 for e in executions_db.values()
            if e.get("status") == "running"
        ),
    }
