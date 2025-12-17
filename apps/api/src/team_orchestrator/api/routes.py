"""
Agno Team Orchestrator v2.0 - REST API Routes

Complete REST API for team orchestration.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from ..types import (
    TeamConfiguration, TeamExecution, OrchestrationMode,
    AgentProfile, Task, TaskType, Priority
)
from ..engine import get_orchestration_engine
from ..profiles import get_profile_manager, PERSONA_LIBRARY
from ..tasks import TaskManager, TASK_TEMPLATES
from ..ai.nl_builder import NLTeamBuilder, TEAM_TEMPLATES
from ..ai.optimizer import TeamOptimizer, OptimizationObjective

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/teams", tags=["Team Orchestrator"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class CreateTeamRequest(BaseModel):
    """Request to create a team."""
    name: str
    description: str = ""
    mode: str = "sequential"
    agent_personas: List[str] = []
    max_iterations: int = 50
    timeout_seconds: int = 3600


class NLTeamRequest(BaseModel):
    """Request to create team from natural language."""
    description: str = Field(..., min_length=10)


class ExecuteTeamRequest(BaseModel):
    """Request to execute a team."""
    input: Dict[str, Any]


class CreateAgentRequest(BaseModel):
    """Request to create an agent."""
    persona: Optional[str] = None
    name: str = ""
    role: str = ""
    goal: str = ""
    backstory: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7


class CreateTaskRequest(BaseModel):
    """Request to create a task."""
    template: Optional[str] = None
    name: str = ""
    description: str = ""
    type: str = "custom"
    expected_output: str = ""
    tools_required: List[str] = []


class OptimizeRequest(BaseModel):
    """Request to optimize a team."""
    objective: str = "balanced"


# ============================================================
# TEAM ENDPOINTS
# ============================================================

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "team-orchestrator",
        "version": "2.0.0",
    }


@router.post("/create", response_model=Dict)
async def create_team(request: CreateTeamRequest):
    """Create a new team configuration."""
    try:
        profile_manager = get_profile_manager()
        
        # Create agents from personas
        agents = []
        for persona_key in request.agent_personas:
            if persona_key in PERSONA_LIBRARY:
                agent = profile_manager.from_persona(persona_key)
                agents.append(agent)
        
        # Create team config
        config = TeamConfiguration(
            name=request.name,
            description=request.description,
            agents=agents,
            mode=OrchestrationMode(request.mode),
            max_iterations=request.max_iterations,
            timeout_seconds=request.timeout_seconds,
        )
        
        return {
            "success": True,
            "team": config.to_dict(),
        }
        
    except Exception as e:
        logger.error(f"Error creating team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-from-nl", response_model=Dict)
async def create_team_from_nl(request: NLTeamRequest):
    """Create team from natural language description."""
    try:
        builder = NLTeamBuilder()
        config = await builder.build_team(request.description)
        
        return {
            "success": True,
            "team": config.to_dict(),
            "agents_count": len(config.agents),
            "mode": config.mode.value,
        }
        
    except Exception as e:
        logger.error(f"Error creating team from NL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{team_id}/execute", response_model=Dict)
async def execute_team(
    team_id: str,
    request: ExecuteTeamRequest,
    background_tasks: BackgroundTasks
):
    """Execute a team."""
    try:
        # For demo, create a simple team
        profile_manager = get_profile_manager()
        agents = [
            profile_manager.from_persona("content_writer"),
            profile_manager.from_persona("senior_researcher"),
        ]
        
        config = TeamConfiguration(
            id=team_id,
            name="Demo Team",
            agents=agents,
            mode=OrchestrationMode.SEQUENTIAL,
        )
        
        engine = get_orchestration_engine()
        execution = await engine.execute(config, request.input)
        
        return {
            "success": True,
            "execution_id": execution.id,
            "status": execution.status.value,
            "output": execution.output,
        }
        
    except Exception as e:
        logger.error(f"Error executing team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{team_id}/executions", response_model=Dict)
async def get_executions(team_id: str):
    """Get team executions."""
    engine = get_orchestration_engine()
    executions = [
        e.to_dict() for e in engine.list_executions()
        if e.team_id == team_id
    ]
    
    return {
        "team_id": team_id,
        "executions": executions,
        "count": len(executions),
    }


@router.post("/{team_id}/optimize", response_model=Dict)
async def optimize_team(team_id: str, request: OptimizeRequest):
    """Get optimization suggestions for a team."""
    try:
        # For demo, create sample config
        profile_manager = get_profile_manager()
        agents = [
            profile_manager.from_persona("content_writer"),
            profile_manager.from_persona("senior_researcher"),
        ]
        
        config = TeamConfiguration(
            id=team_id,
            name="Demo Team",
            agents=agents,
            mode=OrchestrationMode.SEQUENTIAL,
        )
        
        optimizer = TeamOptimizer()
        result = await optimizer.optimize(
            config,
            OptimizationObjective(request.objective)
        )
        
        return {
            "success": True,
            "suggestions": [
                {
                    "category": s.category,
                    "description": s.description,
                    "impact": s.impact,
                    "confidence": s.confidence,
                }
                for s in result.suggestions
            ],
            "expected_improvement": result.expected_improvement,
            "confidence": result.confidence,
        }
        
    except Exception as e:
        logger.error(f"Error optimizing team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# AGENT ENDPOINTS
# ============================================================

@router.get("/agents/personas")
async def list_personas():
    """List available agent personas."""
    personas = []
    for key, data in PERSONA_LIBRARY.items():
        personas.append({
            "key": key,
            "name": data.get("name", key),
            "role": data.get("role", ""),
            "goal": data.get("goal", "")[:100] + "..." if len(data.get("goal", "")) > 100 else data.get("goal", ""),
        })
    
    return {
        "personas": personas,
        "count": len(personas),
    }


@router.post("/agents/create", response_model=Dict)
async def create_agent(request: CreateAgentRequest):
    """Create an agent."""
    try:
        profile_manager = get_profile_manager()
        
        if request.persona:
            agent = profile_manager.from_persona(
                request.persona,
                name=request.name or None,
                model=request.model,
            )
        else:
            agent = profile_manager.create_profile(
                name=request.name,
                role=request.role,
                goal=request.goal,
                backstory=request.backstory,
                model=request.model,
                temperature=request.temperature,
            )
        
        return {
            "success": True,
            "agent": agent.to_dict(),
        }
        
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent by ID."""
    profile_manager = get_profile_manager()
    agent = profile_manager.get_profile(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent.to_dict()


# ============================================================
# TASK ENDPOINTS
# ============================================================

@router.get("/tasks/templates")
async def list_task_templates():
    """List available task templates."""
    templates = []
    for key, data in TASK_TEMPLATES.items():
        templates.append({
            "key": key,
            "name": data.get("name", key),
            "type": data.get("type", TaskType.CUSTOM).value if isinstance(data.get("type"), TaskType) else data.get("type", "custom"),
            "description": data.get("description", ""),
        })
    
    return {
        "templates": templates,
        "count": len(templates),
    }


@router.post("/tasks/create", response_model=Dict)
async def create_task(request: CreateTaskRequest):
    """Create a task."""
    try:
        task_manager = TaskManager()
        
        if request.template:
            task = task_manager.from_template(
                request.template,
                name=request.name or None,
                description=request.description or None,
            )
        else:
            task = task_manager.create_task(
                name=request.name,
                description=request.description,
                task_type=TaskType(request.type),
                expected_output=request.expected_output,
                tools_required=request.tools_required,
            )
        
        return {
            "success": True,
            "task": task.to_dict(),
        }
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ORCHESTRATION ENDPOINTS
# ============================================================

@router.get("/modes")
async def list_orchestration_modes():
    """List available orchestration modes."""
    modes = [
        {
            "value": mode.value,
            "name": mode.value.replace("_", " ").title(),
            "description": get_mode_description(mode),
        }
        for mode in OrchestrationMode
    ]
    
    return {
        "modes": modes,
        "count": len(modes),
    }


@router.get("/templates")
async def list_team_templates():
    """List available team templates."""
    templates = []
    for key, data in TEAM_TEMPLATES.items():
        templates.append({
            "key": key,
            "name": data.get("name", key),
            "description": data.get("description", ""),
            "mode": data.get("mode", OrchestrationMode.SEQUENTIAL).value,
            "agents": data.get("agents", []),
        })
    
    return {
        "templates": templates,
        "count": len(templates),
    }


def get_mode_description(mode: OrchestrationMode) -> str:
    """Get description for orchestration mode."""
    descriptions = {
        OrchestrationMode.SEQUENTIAL: "Execute agents one after another",
        OrchestrationMode.PARALLEL: "Execute all agents simultaneously",
        OrchestrationMode.HIERARCHICAL: "Supervisor delegates to workers",
        OrchestrationMode.DEBATE: "Agents debate to find best solution",
        OrchestrationMode.CONSENSUS: "Agents work towards agreement",
        OrchestrationMode.VOTING: "Agents vote on proposals",
        OrchestrationMode.EXPERT_PANEL: "Panel of experts contribute perspectives",
        OrchestrationMode.PIPELINE: "Process data through agent pipeline",
        OrchestrationMode.SWARM: "Emergent intelligence from agent swarm",
    }
    return descriptions.get(mode, "")
