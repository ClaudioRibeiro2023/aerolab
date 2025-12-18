"""
Router de Workflows - Registry, execução e pipelines dinâmicos.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agno.agent import Agent

from src.auth.deps import get_current_user, is_auth_enabled
from src.os.middleware import setup_rate_limit, setup_security


class WorkflowStep(BaseModel):
    """Definição de um passo do workflow."""

    type: str  # "agent"
    name: str  # nome do agente
    input_template: str
    output_var: Optional[str] = None
    transitions: Optional[List[Dict[str, str]]] = None
    conditions: Optional[Dict[str, str]] = None


class WorkflowCreateRequest(BaseModel):
    """Request para criar um workflow."""

    name: str
    description: Optional[str] = None
    steps: List[WorkflowStep]


class WorkflowRunRequest(BaseModel):
    """Request para executar um workflow."""

    inputs: Dict[str, str] = {}


class LicitacoesMonitorRequest(BaseModel):
    """Request para workflow licitacoes_monitor."""

    fonte: str = "pncp"
    termo_busca: str
    uf: Optional[str] = None
    municipio: Optional[str] = None
    periodo_inicio: Optional[str] = None
    periodo_fim: Optional[str] = None
    palavras_chave: List[str] = []
    modo_execucao: str = "one_shot"


class ResearchWriteRequest(BaseModel):
    """Request para workflow research-write."""

    topic: str
    style: Optional[str] = None
    use_rag: Optional[bool] = False
    collection: Optional[str] = None
    top_k: Optional[int] = 3


def _render_template(template: str, context: Dict[str, str]) -> str:
    """Renderiza um template substituindo variáveis {{var}}."""
    result = template
    for key, value in context.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


def _get_output(agent: Agent) -> str:
    """Extrai output de um agente de forma segura."""
    try:
        out = agent.get_last_run_output()
    except Exception:
        out = None

    if isinstance(out, dict):
        return out.get("content", "")
    return getattr(out, "content", "") or ""


def create_router(app: Any) -> APIRouter:
    """
    Cria o router de workflows.

    Args:
        app: Instância do FastAPI app para acessar state.

    Returns:
        APIRouter configurado.
    """
    router = APIRouter(prefix="/workflows", tags=["workflows"])

    # Aplicar middlewares
    setup_security(router)
    setup_rate_limit(router)

    # Inicializar registry se não existir
    if not hasattr(app.state, "workflows_registry"):
        app.state.workflows_registry = {}

    # === Workflows pré-definidos ===

    @router.post("/research-write")
    async def research_write(req: ResearchWriteRequest):
        """Workflow: Pesquisar e Escrever."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        researcher = agents_map.get("Researcher")
        writer = agents_map.get("Writer")

        if not researcher or not writer:
            raise HTTPException(status_code=500, detail="Required agents not available")

        # Pesquisar
        researcher.run(f"Pesquise sobre: {req.topic}. Forneça pontos objetivos e fontes.")
        research = _get_output(researcher)

        # Opcional: enriquecer com RAG
        if req.use_rag and req.collection:
            try:
                from src.rag.service import get_rag_service

                rag = get_rag_service()
                results = rag.query(
                    collection=req.collection,
                    query_text=req.topic,
                    top_k=req.top_k or 3,
                )
                ctx = "\n\n".join(
                    [
                        f"[Fonte] {r.get('metadata', {}).get('title', 'doc')}\n{r.get('text', '')}"
                        for r in results
                    ]
                )
                if ctx:
                    research = f"{research}\n\nContexto Recuperado:\n{ctx}"
            except Exception:
                pass

        # Escrever
        writer.run(
            f"Escreva um texto claro e bem estruturado em Markdown.\n\n"
            f"Pesquisa:\n{research}\n\n"
            f"Estilo: {req.style or 'neutro'}"
        )
        content = _get_output(writer)

        return {"topic": req.topic, "research": research, "content": content}

    @router.post("/research-write-review")
    async def research_write_review(req: ResearchWriteRequest):
        """Workflow: Pesquisar, Escrever e Revisar."""
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        researcher = agents_map.get("Researcher")
        writer = agents_map.get("Writer")
        reviewer = agents_map.get("Reviewer")

        if not researcher or not writer or not reviewer:
            raise HTTPException(status_code=500, detail="Required agents not available")

        # Pesquisar
        researcher.run(f"Pesquise sobre: {req.topic}. Forneça pontos objetivos e fontes.")
        research = _get_output(researcher)

        # Escrever
        writer.run(
            f"Escreva um texto claro e bem estruturado em Markdown.\n\n"
            f"Pesquisa:\n{research}\n\n"
            f"Estilo: {req.style or 'neutro'}"
        )
        draft = _get_output(writer)

        # Revisar
        reviewer.run(
            f"Revise e melhore o texto abaixo.\n"
            f"Entregue a versão final revisada.\n\n"
            f"Estilo: {req.style or 'neutro'}\n\n"
            f"Texto:\n{draft}"
        )
        final = _get_output(reviewer)

        return {"topic": req.topic, "research": research, "draft": draft, "final": final}

    # === Registry CRUD ===

    @router.post("/registry")
    async def wf_create(req: WorkflowCreateRequest, user=Depends(get_current_user)):
        """Cria um novo workflow no registry."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        registry: Dict[str, dict] = getattr(app.state, "workflows_registry", {})

        if req.name in registry:
            raise HTTPException(status_code=409, detail="Workflow already exists")

        registry[req.name] = {
            "name": req.name,
            "description": req.description,
            "steps": [s.model_dump() for s in req.steps],
        }
        app.state.workflows_registry = registry

        return {"name": req.name, "steps": len(req.steps)}

    @router.get("/registry")
    async def wf_list():
        """Lista todos os workflows registrados."""
        registry: Dict[str, dict] = getattr(app.state, "workflows_registry", {})
        return list(registry.values())

    @router.get("/registry/{name}")
    async def wf_get(name: str):
        """Retorna um workflow específico."""
        registry: Dict[str, dict] = getattr(app.state, "workflows_registry", {})

        if name not in registry:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return registry[name]

    @router.delete("/registry/{name}")
    async def wf_delete(name: str, user=Depends(get_current_user)):
        """Remove um workflow do registry."""
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        registry: Dict[str, dict] = getattr(app.state, "workflows_registry", {})

        if name not in registry:
            raise HTTPException(status_code=404, detail="Workflow not found")

        registry.pop(name, None)
        app.state.workflows_registry = registry

        return {"deleted": name}

    @router.post("/registry/{name}/run")
    async def wf_run(name: str, req: WorkflowRunRequest):
        """Executa um workflow registrado."""
        registry: Dict[str, dict] = getattr(app.state, "workflows_registry", {})

        if name not in registry:
            raise HTTPException(status_code=404, detail="Workflow not found")

        wf = registry[name]
        steps = wf.get("steps", [])

        if not steps:
            raise HTTPException(status_code=400, detail="Workflow has no steps")

        # Indexar passos por nome
        steps_by_name: Dict[str, dict] = {}
        order_names: List[str] = []

        for step in steps:
            step_name = step.get("name")
            if not step_name:
                raise HTTPException(status_code=400, detail="Workflow step missing name")
            if step_name in steps_by_name:
                raise HTTPException(status_code=400, detail=f"Duplicate step name: {step_name}")
            steps_by_name[step_name] = step
            order_names.append(step_name)

        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        context: Dict[str, str] = {k: str(v) for k, v in (req.inputs or {}).items()}
        outputs: Dict[str, str] = {}

        current_name = order_names[0]
        visited = 0
        max_iterations = len(order_names) * 3 or 10

        while True:
            if visited > max_iterations:
                raise HTTPException(status_code=400, detail="Potential workflow loop detected")

            step = steps_by_name.get(current_name)
            if not step:
                raise HTTPException(status_code=400, detail=f"Unknown step: {current_name}")

            if step.get("type") != "agent":
                raise HTTPException(
                    status_code=400, detail=f"Unsupported step type: {step.get('type')}"
                )

            agent_name = step.get("name")
            agent = agents_map.get(agent_name)
            if not agent:
                raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_name}")

            # Renderizar e executar
            template = step.get("input_template") or ""
            prompt = _render_template(template, context)
            agent.run(prompt)
            output = _get_output(agent)

            # Salvar output
            output_var = step.get("output_var") or agent_name.lower()
            context[output_var] = output
            context["last"] = output
            outputs[output_var] = output

            visited += 1

            # Resolver próximo passo
            conditions = step.get("conditions") or {}
            transitions = step.get("transitions") or []
            next_name: Optional[str] = None

            if conditions:
                decision_key = step.get("output_var") or "last"
                decision = context.get(decision_key, "").strip().lower()
                next_name = conditions.get(decision)
                if not next_name:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No condition for decision '{decision}' in step {current_name}",
                    )
            elif transitions:
                mapping = {
                    str(t.get("label", "")).strip().lower(): t.get("to")
                    for t in transitions
                    if t.get("label") and t.get("to")
                }
                decision_key = step.get("output_var") or "last"
                decision = context.get(decision_key, "").strip().lower()
                next_name = mapping.get(decision)
                if not next_name:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No transition for decision '{decision}' in step {current_name}",
                    )

            if next_name:
                current_name = next_name
                continue

            # Seguir sequência
            try:
                idx = order_names.index(current_name)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Step order corrupted: {current_name}"
                )

            if idx + 1 >= len(order_names):
                break

            current_name = order_names[idx + 1]

        return {"workflow": name, "outputs": outputs}

    # === Workflow: Licitações Monitor ===

    @router.post("/licitacoes-monitor")
    async def licitacoes_monitor(req: LicitacoesMonitorRequest):
        """Workflow: Monitoramento & Análise de Licitações (Techdengue)."""
        try:
            from src.workflows.licitacoes import run_licitacoes_monitor
            
            result = await run_licitacoes_monitor(req.model_dump())
            return result.model_dump()
        except ImportError:
            raise HTTPException(
                status_code=501,
                detail="Workflow licitacoes_monitor não disponível"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/licitacoes-monitor/schema")
    async def licitacoes_monitor_schema():
        """Retorna schemas do workflow licitacoes_monitor."""
        return {
            "input": {
                "fonte": {"type": "string", "enum": ["pncp", "diarios_oficiais", "portais"]},
                "termo_busca": {"type": "string", "required": True},
                "uf": {"type": "string"},
                "municipio": {"type": "string"},
                "periodo_inicio": {"type": "string", "format": "date"},
                "periodo_fim": {"type": "string", "format": "date"},
                "palavras_chave": {"type": "array"},
                "modo_execucao": {"type": "string", "enum": ["one_shot", "monitor"]}
            },
            "output": {
                "status": {"type": "string"},
                "itens_encontrados": {"type": "array"},
                "triagem": {"type": "object"},
                "alertas": {"type": "array"}
            }
        }

    return router
