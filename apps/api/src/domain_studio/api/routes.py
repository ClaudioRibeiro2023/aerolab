"""
Domain Studio API Routes - FastAPI endpoints.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..core.types import DomainType, RegulationType
from ..core.registry import get_domain_registry
from ..engines.agentic_rag import AgenticRAGEngine
from ..engines.graph_rag import GraphRAGEngine
from ..engines.compliance import ComplianceEngine
from ..engines.workflow import get_workflow_engine
from ..engines.analytics import get_analytics_engine, EventType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/domain-studio", tags=["Domain Studio"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class DomainInfo(BaseModel):
    """Domain information response."""
    type: str
    name: str
    description: str
    icon: str
    color: str
    capabilities: List[str]
    agents_count: int
    workflows_count: int


class ChatRequest(BaseModel):
    """Chat request."""
    message: str
    agent: Optional[str] = None
    use_rag: bool = True
    rag_mode: str = "hybrid"


class ChatResponse(BaseModel):
    """Chat response."""
    domain: str
    agent: Optional[str]
    response: str
    confidence: float
    sources: List[Dict] = []
    compliance: Optional[Dict] = None


class RAGQueryRequest(BaseModel):
    """RAG query request."""
    query: str
    mode: str = "agentic"  # simple, hybrid, agentic, graph
    top_k: int = 10
    include_graph: bool = False


class RAGQueryResponse(BaseModel):
    """RAG query response."""
    query: str
    answer: str
    confidence: float
    sources: List[Dict]
    iterations: int = 0
    latency_ms: float


class ComplianceCheckRequest(BaseModel):
    """Compliance check request."""
    content: str
    regulations: Optional[List[str]] = None


class ComplianceCheckResponse(BaseModel):
    """Compliance check response."""
    is_compliant: bool
    score: float
    violations: List[Dict]
    warnings: List[Dict]
    suggestions: List[str]


class WorkflowExecuteRequest(BaseModel):
    """Workflow execution request."""
    workflow_id: str
    inputs: Dict[str, Any]


class WorkflowExecuteResponse(BaseModel):
    """Workflow execution response."""
    execution_id: str
    status: str
    workflow_name: str
    current_step: Optional[str]
    completed_steps: List[str]
    pending_approval: Optional[str]


# ============================================================
# DOMAIN ENDPOINTS
# ============================================================

@router.get("/domains", response_model=List[DomainInfo])
async def list_domains():
    """List all available domains."""
    registry = get_domain_registry()
    domains = registry.list_domains()
    
    return [
        DomainInfo(
            type=d.type.value,
            name=d.name,
            description=d.description,
            icon=d.icon,
            color=d.color,
            capabilities=[c.value for c in d.capabilities],
            agents_count=len(d.agents),
            workflows_count=len(d.workflows),
        )
        for d in domains
    ]


@router.get("/domains/{domain_type}", response_model=DomainInfo)
async def get_domain(domain_type: str):
    """Get domain information."""
    try:
        dt = DomainType(domain_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain_type}")
    
    registry = get_domain_registry()
    domain = registry.get_domain(dt)
    
    if not domain:
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain_type}")
    
    return DomainInfo(
        type=domain.type.value,
        name=domain.name,
        description=domain.description,
        icon=domain.icon,
        color=domain.color,
        capabilities=[c.value for c in domain.capabilities],
        agents_count=len(domain.agents),
        workflows_count=len(domain.workflows),
    )


@router.get("/domains/{domain_type}/agents")
async def list_domain_agents(domain_type: str):
    """List agents for a domain."""
    try:
        dt = DomainType(domain_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain_type}")
    
    registry = get_domain_registry()
    agents = registry.list_agents(dt)
    
    return [
        {
            "id": a.id,
            "name": a.name,
            "role": a.role,
            "description": a.description,
            "icon": a.icon,
            "capabilities": [c.value for c in a.capabilities],
        }
        for a in agents
    ]


@router.get("/domains/{domain_type}/workflows")
async def list_domain_workflows(domain_type: str):
    """List workflows for a domain."""
    try:
        dt = DomainType(domain_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain_type}")
    
    registry = get_domain_registry()
    workflows = registry.list_workflows(dt)
    
    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "icon": w.icon,
            "steps_count": len(w.steps),
            "human_checkpoints": w.human_checkpoints,
        }
        for w in workflows
    ]


# ============================================================
# CHAT ENDPOINTS
# ============================================================

@router.post("/domains/{domain_type}/chat", response_model=ChatResponse)
async def chat_with_domain(domain_type: str, request: ChatRequest):
    """Chat with a domain."""
    try:
        dt = DomainType(domain_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain_type}")
    
    # Track analytics
    analytics = get_analytics_engine()
    
    # Simulated response (in production, would use actual domain)
    response = ChatResponse(
        domain=domain_type,
        agent=request.agent or "default",
        response=f"Response from {domain_type} domain for: {request.message[:100]}",
        confidence=0.85,
        sources=[],
    )
    
    # Track event
    await analytics.track_chat(
        domain=dt,
        agent=request.agent or "default",
        response_time_ms=150.0,
        tokens=len(request.message.split()) * 4,
        confidence=response.confidence
    )
    
    return response


# ============================================================
# RAG ENDPOINTS
# ============================================================

@router.post("/domains/{domain_type}/rag/query", response_model=RAGQueryResponse)
async def query_domain_knowledge(domain_type: str, request: RAGQueryRequest):
    """Query domain knowledge using RAG."""
    try:
        dt = DomainType(domain_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain_type}")
    
    # Select RAG engine based on mode
    if request.mode == "graph" or request.include_graph:
        engine = GraphRAGEngine(domain=dt)
        result = await engine.query(
            query=request.query,
            depth=2,
            include_documents=True,
            top_k=request.top_k
        )
        return RAGQueryResponse(
            query=request.query,
            answer=result.answer,
            confidence=result.confidence,
            sources=[{"id": s.id, "content": s.content[:200]} for s in result.document_sources],
            iterations=0,
            latency_ms=result.latency_ms
        )
    else:
        engine = AgenticRAGEngine(domain=dt)
        result = await engine.query(
            query=request.query,
            max_iterations=3 if request.mode == "agentic" else 1
        )
        return RAGQueryResponse(
            query=request.query,
            answer=result.answer,
            confidence=result.confidence,
            sources=[{"id": s.id, "content": s.content[:200]} for s in result.sources],
            iterations=result.total_iterations,
            latency_ms=result.latency_ms
        )


# ============================================================
# COMPLIANCE ENDPOINTS
# ============================================================

@router.post("/domains/{domain_type}/compliance/check", response_model=ComplianceCheckResponse)
async def check_compliance(domain_type: str, request: ComplianceCheckRequest):
    """Check content compliance."""
    try:
        dt = DomainType(domain_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain_type}")
    
    engine = ComplianceEngine(domain=dt)
    
    # Parse regulations
    regulations = None
    if request.regulations:
        regulations = []
        for r in request.regulations:
            try:
                regulations.append(RegulationType(r))
            except ValueError:
                pass
    
    result = await engine.check(
        content=request.content,
        regulations=regulations,
        domain=dt
    )
    
    return ComplianceCheckResponse(
        is_compliant=result.is_compliant,
        score=result.score,
        violations=[
            {"regulation": v.regulation.value, "rule": v.rule, "severity": v.severity}
            for v in result.violations
        ],
        warnings=[
            {"regulation": w.regulation.value, "rule": w.rule, "recommendation": w.recommendation}
            for w in result.warnings
        ],
        suggestions=result.suggestions
    )


@router.post("/compliance/detect-pii")
async def detect_pii(content: str = Query(...)):
    """Detect PII in content."""
    engine = ComplianceEngine()
    result = await engine.detect_pii(content)
    
    return {
        "found": result.found,
        "types": result.types,
        "locations_count": len(result.locations),
        "redacted_preview": result.redacted_text[:200] if result.redacted_text else ""
    }


@router.post("/compliance/assess-risk")
async def assess_risk(content: str = Query(...)):
    """Assess content risk."""
    engine = ComplianceEngine()
    result = await engine.assess_risk(content)
    
    return {
        "score": result.score,
        "level": result.level,
        "factors": result.factors,
        "recommendations": result.recommendations
    }


# ============================================================
# WORKFLOW ENDPOINTS
# ============================================================

@router.post("/workflows/execute", response_model=WorkflowExecuteResponse)
async def execute_workflow(request: WorkflowExecuteRequest):
    """Execute a workflow."""
    engine = get_workflow_engine()
    
    execution = await engine.execute(
        workflow_id=request.workflow_id,
        inputs=request.inputs
    )
    
    return WorkflowExecuteResponse(
        execution_id=execution.id,
        status=execution.status.value,
        workflow_name=execution.workflow_name,
        current_step=execution.current_step,
        completed_steps=execution.completed_steps,
        pending_approval=execution.pending_approval
    )


@router.get("/workflows/executions/{execution_id}")
async def get_workflow_execution(execution_id: str):
    """Get workflow execution status."""
    engine = get_workflow_engine()
    execution = engine.get_execution(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return {
        "id": execution.id,
        "workflow_id": execution.workflow_id,
        "workflow_name": execution.workflow_name,
        "status": execution.status.value,
        "current_step": execution.current_step,
        "completed_steps": execution.completed_steps,
        "pending_approval": execution.pending_approval,
        "output": execution.output,
        "error": execution.error
    }


@router.post("/workflows/executions/{execution_id}/approve")
async def approve_workflow_step(execution_id: str, approval: Dict[str, Any]):
    """Approve a workflow step (human-in-the-loop)."""
    engine = get_workflow_engine()
    
    try:
        execution = await engine.resume(execution_id, approval)
        return {
            "id": execution.id,
            "status": execution.status.value,
            "completed_steps": execution.completed_steps
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# ANALYTICS ENDPOINTS
# ============================================================

@router.get("/analytics/summary")
async def get_analytics_summary(period_days: int = 30):
    """Get analytics summary."""
    engine = get_analytics_engine()
    summary = await engine.get_usage_summary(period_days)
    
    return {
        "total_events": summary.total_events,
        "total_users": summary.total_users,
        "events_by_domain": summary.events_by_domain,
        "events_by_type": summary.events_by_type,
        "avg_response_time_ms": summary.avg_response_time_ms,
        "total_tokens_used": summary.total_tokens_used,
        "period_start": summary.period_start.isoformat(),
        "period_end": summary.period_end.isoformat()
    }


@router.get("/analytics/domains/{domain_type}")
async def get_domain_analytics(domain_type: str, period_days: int = 30):
    """Get domain-specific analytics."""
    try:
        dt = DomainType(domain_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain_type}")
    
    engine = get_analytics_engine()
    stats = await engine.get_domain_stats(dt, period_days)
    
    return {
        "domain": domain_type,
        "total_chats": stats.total_chats,
        "total_workflows": stats.total_workflows,
        "avg_response_time_ms": stats.avg_response_time_ms,
        "avg_confidence": stats.avg_confidence,
        "most_used_agents": stats.most_used_agents
    }


@router.get("/analytics/roi/{domain_type}")
async def calculate_domain_roi(domain_type: str, period_days: int = 30):
    """Calculate ROI for a domain."""
    try:
        dt = DomainType(domain_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain not found: {domain_type}")
    
    engine = get_analytics_engine()
    roi = await engine.calculate_roi(dt, period_days)
    
    return roi


# ============================================================
# HEALTH ENDPOINT
# ============================================================

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    registry = get_domain_registry()
    stats = registry.get_stats()
    
    return {
        "status": "healthy",
        "version": "3.5.0",
        "domains": stats["total_domains"],
        "agents": stats["total_agents"],
        "workflows": stats["total_workflows"]
    }
