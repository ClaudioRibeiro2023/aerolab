from typing import List, Optional, Dict
import time
from collections import deque
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agno.os import AgentOS
from agno.agent import Agent
from agno.team import Team

from src.agents import BaseAgent
from src.config import get_settings
from src.hitl.repo import get_repo
from src.auth.deps import is_auth_enabled, get_current_user, create_access_token
from src.storage.service import get_storage
from src.utils.logger import get_logger


def build_agents() -> List[Agent]:
    settings = get_settings()

    # Agente padrão (genérico)
    default_agent = BaseAgent.create(
        name=(settings.AGENTOS_AGENT_NAME or "Template Agent"),
        role=(settings.AGENTOS_AGENT_ROLE or "Você é um assistente útil do template"),
        instructions=[
            "Responda em português",
            "Seja conciso e claro",
        ],
        model_provider=settings.DEFAULT_MODEL_PROVIDER,
        model_id=settings.DEFAULT_MODEL_ID,
        use_database=True,
        markdown=True,
        enable_session_summaries=True,
    )

    # Agente especializado: Pesquisador
    researcher = BaseAgent.create(
        name="Researcher",
        role="Pesquisador que busca informações confiáveis e organiza insights",
        instructions=[
            "Cite fontes quando possível",
            "Organize em tópicos",
            "Seja objetivo",
        ],
        model_provider=settings.DEFAULT_MODEL_PROVIDER,
        model_id=settings.DEFAULT_MODEL_ID,
        use_database=True,
        markdown=True,
        enable_session_summaries=True,
    )

    # Agente especializado: Escritor
    writer = BaseAgent.create(
        name="Writer",
        role="Escritor que produz conteúdo claro e bem estruturado a partir de pesquisa fornecida",
        instructions=[
            "Escreva em Markdown",
            "Use títulos e seções",
            "Seja didático e conciso",
        ],
        model_provider=settings.DEFAULT_MODEL_PROVIDER,
        model_id=settings.DEFAULT_MODEL_ID,
        use_database=True,
        markdown=True,
        enable_session_summaries=True,
    )
    
    # Agente especializado: Revisor
    reviewer = BaseAgent.create(
        name="Reviewer",
        role="Revisor que avalia clareza, coesão, gramática e consistência; sugere melhorias",
        instructions=[
            "Aponte problemas de clareza e consistência",
            "Sugira melhorias objetivas",
            "Quando solicitado, entregue versão revisada",
        ],
        model_provider=settings.DEFAULT_MODEL_PROVIDER,
        model_id=settings.DEFAULT_MODEL_ID,
        use_database=True,
        markdown=True,
        enable_session_summaries=True,
    )

    return [default_agent, researcher, writer, reviewer]


def build_agent_os(agents: Optional[List[Agent]] = None) -> AgentOS:
    agents = agents or build_agents()
    return AgentOS(agents=agents)


class ResearchWriteRequest(BaseModel):
    topic: str
    style: Optional[str] = None
    use_rag: Optional[bool] = False
    collection: Optional[str] = None
    top_k: Optional[int] = 3


def _setup_security_and_rate_limit(router: APIRouter):
    settings = get_settings()

    # Basic Auth (opcional)
    if settings.BASIC_AUTH_USERNAME and settings.BASIC_AUTH_PASSWORD:
        from fastapi.security import HTTPBasic, HTTPBasicCredentials

        security = HTTPBasic()

        def _basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
            if not (
                credentials.username == settings.BASIC_AUTH_USERNAME
                and credentials.password == settings.BASIC_AUTH_PASSWORD
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthorized",
                    headers={"WWW-Authenticate": "Basic"},
                )
            return True

        router.dependencies.append(Depends(_basic_auth))

    if settings.RATE_LIMIT_ENABLED:
        window = getattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)
        buckets: Dict[str, deque] = {}

        def _route_group(path: str) -> str:
            if path.startswith("/rag/query"):
                return "rag_query"
            if path.startswith("/rag/ingest"):
                return "rag_ingest"
            if path.startswith("/auth/"):
                return "auth"
            if path.startswith("/teams/"):
                return "teams"
            if path.startswith("/workflows/"):
                return "workflows"
            return "default"

        def _limit_for(group: str) -> int:
            if group == "rag_query":
                return getattr(settings, "RATE_LIMIT_RAG_QUERY", 60)
            if group == "rag_ingest":
                return getattr(settings, "RATE_LIMIT_RAG_INGEST", 10)
            if group == "auth":
                return getattr(settings, "RATE_LIMIT_AUTH", 30)
            if group in ("teams", "workflows"):
                return getattr(settings, "RATE_LIMIT_AGENTICS", 30)
            return getattr(settings, "RATE_LIMIT_DEFAULT", 120)

        def _rate_limit(request: Request):
            now = time.time()
            path = request.url.path
            group = _route_group(path)
            limit = _limit_for(group)
            auth = request.headers.get("authorization", "")
            key = None
            if auth.lower().startswith("bearer "):
                key = auth.split(" ", 1)[1].strip()
            if not key:
                key = request.client.host if request.client else "unknown"
            bucket_key = f"{group}:{key}"
            dq = buckets.setdefault(bucket_key, deque())
            while dq and (now - dq[0]) > window:
                dq.popleft()
            if len(dq) >= limit:
                retry_after = max(1, int(window - (now - dq[0]))) if dq else window
                raise HTTPException(status_code=429, detail="Rate limit exceeded", headers={"Retry-After": str(retry_after)})
            dq.append(now)
            return True

        router.dependencies.append(Depends(_rate_limit))


def get_app():
    agents = build_agents()
    os_ = build_agent_os(agents)
    app = os_.get_app()

    # Compartilhar agentes com a app (para rotas customizadas)
    try:
        app.state.agents = {a.name: a for a in agents}
    except Exception:
        pass

    # Logger estruturado (reutiliza utilitário do projeto)
    try:
        app.state.logger = get_logger("api")
    except Exception:
        app.state.logger = None

    # Marca inicial para uptime
    try:
        if not hasattr(app.state, "started_at"):
            app.state.started_at = time.time()
    except Exception:
        pass

    # Teams nativos: compor um time simples (Researcher -> Writer)
    try:
        researcher = app.state.agents.get("Researcher")
        writer = app.state.agents.get("Writer")
        teams: Dict[str, Team] = {}
        if researcher and writer:
            content_team = Team(
                members=[researcher, writer],
                name="ContentTeam",
                description="Time que pesquisa e escreve conteúdos",
                markdown=True,
            )
            teams["content"] = content_team
        app.state.teams = teams
    except Exception:
        pass

    # Repositório HITL (persistência em SQLite)
    try:
        app.state.hitl_repo = get_repo()
    except Exception:
        pass

    # Router de workflows simples (pesquisar -> escrever)
    router = APIRouter(prefix="/workflows", tags=["workflows"])
    _setup_security_and_rate_limit(router)

    @router.post("/research-write")
    async def research_write(req: ResearchWriteRequest):
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        researcher = agents_map.get("Researcher")
        writer = agents_map.get("Writer")
        if not researcher or not writer:
            raise HTTPException(status_code=500, detail="Required agents not available")

        # Execução sequencial (workflow simples)
        researcher.run(f"Pesquise sobre: {req.topic}. Forneça pontos objetivos e fontes.")
        _res = None
        try:
            _res = researcher.get_last_run_output()
        except Exception:
            _res = None
        research_text = (_res.get("content") if isinstance(_res, dict) else getattr(_res, "content", None)) or ""

        # Opcional: enriquecer com RAG
        if req.use_rag and req.collection:
            try:
                from src.rag.service import get_rag_service  # lazy import
                rag = get_rag_service()
                results = rag.query(collection=req.collection, query_text=req.topic, top_k=req.top_k or 3)
                ctx = "\n\n".join([
                    f"[Fonte] {r.get('metadata',{}).get('title','doc')}\n{r.get('text','')}" for r in results
                ])
                if ctx:
                    research_text = f"{research_text}\n\nContexto Recuperado:\n{ctx}"
            except Exception:
                # Se RAG não estiver disponível, seguimos apenas com a pesquisa do agente
                pass

        writer.run(
            (
                "Escreva um texto claro e bem estruturado em Markdown, baseado na pesquisa a seguir.\n\n"
                f"Pesquisa:\n{research_text}\n\n"
                f"Estilo: {req.style or 'neutro'}\n"
            )
        )
        _wout = None
        try:
            _wout = writer.get_last_run_output()
        except Exception:
            _wout = None
        final_text = (_wout.get("content") if isinstance(_wout, dict) else getattr(_wout, "content", None)) or ""

        return {"topic": req.topic, "research": research_text, "content": final_text}

    # app.include_router(router)  # movido para o final para incluir rotas HITL

    # ===== Registry de workflows (CRUD + run) =====
    if not hasattr(app.state, "workflows_registry"):
        app.state.workflows_registry = {}

    class WorkflowStep(BaseModel):
        type: str  # "agent"
        name: str  # nome do agente
        input_template: str
        output_var: Optional[str] = None
        transitions: Optional[List[Dict[str, str]]] = None
        conditions: Optional[Dict[str, str]] = None

    class WorkflowCreateRequest(BaseModel):
        name: str
        steps: List[WorkflowStep]

    class WorkflowRunRequest(BaseModel):
        inputs: Dict[str, str] = {}

    def _render_template(tpl: str, ctx: Dict[str, str]) -> str:
        out = tpl
        try:
            for k, v in ctx.items():
                out = out.replace(f"{{{{{k}}}}}", str(v))
        except Exception:
            pass
        return out

    wf_reg_router = APIRouter(prefix="/workflows/registry", tags=["workflows"]) 
    _setup_security_and_rate_limit(wf_reg_router)

    @wf_reg_router.post("/")
    async def wf_create(req: WorkflowCreateRequest, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        reg: Dict[str, dict] = getattr(app.state, "workflows_registry", {})
        key = req.name
        if key in reg:
            raise HTTPException(status_code=409, detail="Workflow already exists")
        reg[key] = {"name": req.name, "steps": [s.model_dump() for s in req.steps]}
        app.state.workflows_registry = reg
        return {"name": req.name, "steps": len(req.steps)}

    @wf_reg_router.post("")
    async def wf_create_no_slash(req: WorkflowCreateRequest, user=Depends(get_current_user)):
        """Alias para permitir POST em /workflows/registry sem barra final."""
        return await wf_create(req, user=user)

    @wf_reg_router.get("/")
    async def wf_list():
        reg: Dict[str, dict] = getattr(app.state, "workflows_registry", {})
        return list(reg.values())

    @wf_reg_router.get("")
    async def wf_list_no_slash():
        """Alias para permitir GET em /workflows/registry sem barra final."""
        return await wf_list()

    @wf_reg_router.get("/{name}")
    async def wf_get(name: str):
        reg: Dict[str, dict] = getattr(app.state, "workflows_registry", {})
        if name not in reg:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return reg[name]

    @wf_reg_router.delete("/{name}")
    async def wf_delete(name: str, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        reg: Dict[str, dict] = getattr(app.state, "workflows_registry", {})
        if name not in reg:
            raise HTTPException(status_code=404, detail="Workflow not found")
        reg.pop(name, None)
        app.state.workflows_registry = reg
        return {"deleted": name}

    @wf_reg_router.post("/{name}/run")
    async def wf_run(name: str, req: WorkflowRunRequest):
        reg: Dict[str, dict] = getattr(app.state, "workflows_registry", {})
        if name not in reg:
            raise HTTPException(status_code=404, detail="Workflow not found")
        wf = reg[name]
        steps = wf.get("steps", [])
        if not steps:
            raise HTTPException(status_code=400, detail="Workflow has no steps")

        # Índice por nome para permitir saltos condicionais
        steps_by_name: Dict[str, dict] = {}
        order_names: List[str] = []
        for s in steps:
            nm = s.get("name")
            if not nm:
                raise HTTPException(status_code=400, detail="Workflow step missing name")
            if nm in steps_by_name:
                raise HTTPException(status_code=400, detail=f"Duplicate step name: {nm}")
            steps_by_name[nm] = s
            order_names.append(nm)

        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        ctx: Dict[str, str] = {k: (str(v) if not isinstance(v, str) else v) for k, v in (req.inputs or {}).items()}
        outputs: Dict[str, str] = {}

        current_name = order_names[0]
        visited = 0
        max_steps = len(order_names) * 3 or 10

        while True:
            if visited > max_steps:
                raise HTTPException(status_code=400, detail="Potential workflow loop detected")

            step = steps_by_name.get(current_name)
            if not step:
                raise HTTPException(status_code=400, detail=f"Unknown step in graph: {current_name}")

            if step.get("type") != "agent":
                raise HTTPException(status_code=400, detail=f"Unsupported step type: {step.get('type')}")

            ag_name = step.get("name")
            ag = agents_map.get(ag_name)
            if not ag:
                raise HTTPException(status_code=400, detail=f"Unknown agent: {ag_name}")

            templ = step.get("input_template") or ""
            prompt = _render_template(templ, ctx)
            ag.run(prompt)
            _o = None
            try:
                _o = ag.get_last_run_output()
            except Exception:
                _o = None
            out_text = (_o.get("content") if isinstance(_o, dict) else getattr(_o, "content", None)) or ""

            key = step.get("output_var") or (ag_name.lower() if isinstance(ag_name, str) and ag_name else None) or f"step_{len(outputs)}"
            ctx[key] = out_text
            ctx["last"] = out_text
            outputs[key] = out_text

            visited += 1

            # Resolver próximo passo: conditions > transitions > sequência
            conds = step.get("conditions") or {}
            trans = step.get("transitions") or []

            next_name: Optional[str] = None

            if conds:
                decision_key = step.get("output_var") or "last"
                raw = ctx.get(decision_key, "")
                decision = str(raw).strip().lower()
                if not decision:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No decision value found for step {current_name} (key '{decision_key}')",
                    )
                # conditions já é um mapeamento label -> nome do próximo passo
                next_name = conds.get(decision)
                if not next_name:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No condition for decision '{decision}' in step {current_name}",
                    )
            elif trans:
                mapping: Dict[str, str] = {}
                for t in trans:
                    lbl = str((t.get("label") or "")).strip().lower()
                    to = t.get("to")
                    if lbl and to and lbl not in mapping:
                        mapping[lbl] = to
                decision_key = step.get("output_var") or "last"
                raw = ctx.get(decision_key, "")
                decision = str(raw).strip().lower()
                if not decision:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No decision value found for step {current_name} (key '{decision_key}')",
                    )
                next_name = mapping.get(decision)
                if not next_name:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No transition for decision '{decision}' in step {current_name}",
                    )

            if next_name:
                current_name = next_name
                continue

            # Sem conditions/transitions: seguir sequência declarada
            try:
                idx = order_names.index(current_name)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Step order corrupted for: {current_name}")

            if idx + 1 >= len(order_names):
                break
            current_name = order_names[idx + 1]

        return {"workflow": name, "outputs": outputs}

    app.include_router(wf_reg_router)

    # Router de teams nativos
    teams_router = APIRouter(prefix="/teams", tags=["teams"])
    _setup_security_and_rate_limit(teams_router)

    class TeamRunRequest(BaseModel):
        prompt: str

    @teams_router.post("/{team_name}/run")
    async def team_run(team_name: str, req: TeamRunRequest):
        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        team = teams_map.get(team_name.lower())
        if not team:
            # Tratar nomes reservados para evitar conflito com rota dinâmica
            if team_name.lower() == "review":
                agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
                reviewer = agents_map.get("Reviewer")
                if not reviewer:
                    raise HTTPException(status_code=500, detail="Reviewer agent not available")
                try:
                    reviewer.run(
                        (
                            "Revise o texto a seguir, melhorando clareza, coesão e gramática.\n"
                            "Entregue uma seção com Comentários e outra com Versão Revisada.\n\n"
                            f"Texto:\n{req.prompt}\n"
                        )
                    )
                    _rv = None
                    try:
                        _rv = reviewer.get_last_run_output()
                    except Exception:
                        _rv = None
                    out_text = (_rv.get("content") if isinstance(_rv, dict) else getattr(_rv, "content", None)) or ""
                except Exception:
                    out_text = ""
                if not out_text:
                    tmpl = agents_map.get("Template Agent") or next(iter(agents_map.values()), None)
                    if tmpl:
                        try:
                            tmpl.run(
                                (
                                    "Faça uma breve revisão do texto a seguir e proponha melhorias.\n\n"
                                    f"Texto:\n{req.prompt}\n"
                                )
                            )
                            _to = None
                            try:
                                _to = tmpl.get_last_run_output()
                            except Exception:
                                _to = None
                            out_text = (_to.get("content") if isinstance(_to, dict) else getattr(_to, "content", None)) or out_text
                        except Exception:
                            pass
                return {"team": "review", "output": out_text}

            if team_name.lower() == "content-pro":
                agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
                researcher = agents_map.get("Researcher")
                writer = agents_map.get("Writer")
                reviewer = agents_map.get("Reviewer")
                if not researcher or not writer or not reviewer:
                    raise HTTPException(status_code=500, detail="Required agents not available")
                # Pesquisar
                researcher.run(f"Pesquise sobre: {req.prompt}. Forneça pontos objetivos e fontes.")
                _r = None
                try:
                    _r = researcher.get_last_run_output()
                except Exception:
                    _r = None
                research_text = (_r.get("content") if isinstance(_r, dict) else getattr(_r, "content", None)) or ""
                # Escrever
                writer.run(
                    (
                        "Escreva um texto claro e bem estruturado em Markdown, baseado na pesquisa a seguir.\n\n"
                        f"Pesquisa:\n{research_text}\n\n"
                        f"Estilo: neutro\n"
                    )
                )
                _w = None
                try:
                    _w = writer.get_last_run_output()
                except Exception:
                    _w = None
                draft_text = (_w.get("content") if isinstance(_w, dict) else getattr(_w, "content", None)) or ""
                # Revisar
                reviewer.run(
                    (
                        "Revise e melhore o texto abaixo, mantendo o estilo indicado.\n"
                        "Entregue a versão final revisada.\n\n"
                        f"Estilo: neutro\n\n"
                        f"Texto:\n{draft_text}\n"
                    )
                )
                _rev = None
                try:
                    _rev = reviewer.get_last_run_output()
                except Exception:
                    _rev = None
                final_text = (_rev.get("content") if isinstance(_rev, dict) else getattr(_rev, "content", None)) or ""
                if not final_text:
                    tmpl = agents_map.get("Template Agent") or next(iter(agents_map.values()), None)
                    if tmpl:
                        try:
                            tmpl.run(
                                (
                                    "Escreva um texto claro e bem estruturado em Markdown.\n\n"
                                    f"Tópico: {req.prompt}\n"
                                    "Estilo: neutro\n"
                                )
                            )
                            _tf = None
                            try:
                                _tf = tmpl.get_last_run_output()
                            except Exception:
                                _tf = None
                            final_text = (_tf.get("content") if isinstance(_tf, dict) else getattr(_tf, "content", None)) or final_text
                        except Exception:
                            pass
                return {"team": "content-pro", "output": final_text}

            raise HTTPException(status_code=404, detail="Team not found")
        team.run(req.prompt)
        _out = None
        try:
            _out = team.get_last_run_output()
        except Exception:
            _out = None
        out_text = (_out.get("content") if isinstance(_out, dict) else getattr(_out, "content", None)) or ""

        # Fallback: pipeline manual Researcher -> Writer se saída estiver vazia
        if not out_text and team_name.lower() == "content":
            agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
            researcher = agents_map.get("Researcher")
            writer = agents_map.get("Writer")
            if researcher and writer:
                try:
                    researcher.run(f"Pesquise sobre: {req.prompt}. Forneça pontos objetivos e fontes.")
                    _res = None
                    try:
                        _res = researcher.get_last_run_output()
                    except Exception:
                        _res = None
                    research_text = (_res.get("content") if isinstance(_res, dict) else getattr(_res, "content", None)) or ""
                    writer.run(
                        (
                            "Escreva um texto claro e bem estruturado em Markdown, baseado na pesquisa a seguir.\n\n"
                            f"Pesquisa:\n{research_text}\n\n"
                            f"Estilo: neutro\n"
                        )
                    )
                    _wout = None
                    try:
                        _wout = writer.get_last_run_output()
                    except Exception:
                        _wout = None
                    out_text = (_wout.get("content") if isinstance(_wout, dict) else getattr(_wout, "content", None)) or out_text
                except Exception:
                    pass

        # Fallback final: usar Template Agent diretamente
        if not out_text:
            agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
            tmpl = agents_map.get("Template Agent") or next(iter(agents_map.values()), None)
            if tmpl:
                try:
                    tmpl.run(
                        (
                            "Escreva um parágrafo curto e claro, em português, sobre: \n"
                            f"{req.prompt}\n"
                        )
                    )
                    _tout = None
                    try:
                        _tout = tmpl.get_last_run_output()
                    except Exception:
                        _tout = None
                    out_text = (_tout.get("content") if isinstance(_tout, dict) else getattr(_tout, "content", None)) or out_text
                except Exception:
                    pass

        return {"team": team_name, "output": out_text}

    # Novo: revisão dedicada por agente Reviewer
    class TeamReviewRequest(BaseModel):
        prompt: str

    @teams_router.post("/review/run")
    async def team_review_run(req: TeamReviewRequest):
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        reviewer = agents_map.get("Reviewer")
        if not reviewer:
            raise HTTPException(status_code=500, detail="Reviewer agent not available")
        try:
            reviewer.run(
                (
                    "Revise o texto a seguir, melhorando clareza, coesão e gramática.\n"
                    "Entregue uma seção com Comentários e outra com Versão Revisada.\n\n"
                    f"Texto:\n{req.prompt}\n"
                )
            )
            _rv = None
            try:
                _rv = reviewer.get_last_run_output()
            except Exception:
                _rv = None
            out_text = (_rv.get("content") if isinstance(_rv, dict) else getattr(_rv, "content", None)) or ""
        except Exception:
            out_text = ""

        if not out_text:
            # Fallback: Template Agent gera breve revisão
            agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
            tmpl = agents_map.get("Template Agent") or next(iter(agents_map.values()), None)
            if tmpl:
                try:
                    tmpl.run(
                        (
                            "Faça uma breve revisão do texto a seguir e proponha melhorias.\n\n"
                            f"Texto:\n{req.prompt}\n"
                        )
                    )
                    _to = None
                    try:
                        _to = tmpl.get_last_run_output()
                    except Exception:
                        _to = None
                    out_text = (_to.get("content") if isinstance(_to, dict) else getattr(_to, "content", None)) or out_text
                except Exception:
                    pass
        return {"team": "review", "output": out_text}

    # Novo: time content-pro (Researcher -> Writer -> Reviewer)
    class TeamContentProRequest(BaseModel):
        prompt: str
        style: Optional[str] = None

    @teams_router.post("/content-pro/run")
    async def team_content_pro_run(req: TeamContentProRequest):
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        researcher = agents_map.get("Researcher")
        writer = agents_map.get("Writer")
        reviewer = agents_map.get("Reviewer")
        if not researcher or not writer or not reviewer:
            raise HTTPException(status_code=500, detail="Required agents not available")

        # Pesquisar
        researcher.run(f"Pesquise sobre: {req.prompt}. Forneça pontos objetivos e fontes.")
        _r = None
        try:
            _r = researcher.get_last_run_output()
        except Exception:
            _r = None
        research_text = (_r.get("content") if isinstance(_r, dict) else getattr(_r, "content", None)) or ""

        # Escrever
        writer.run(
            (
                "Escreva um texto claro e bem estruturado em Markdown, baseado na pesquisa a seguir.\n\n"
                f"Pesquisa:\n{research_text}\n\n"
                f"Estilo: {req.style or 'neutro'}\n"
            )
        )
        _w = None
        try:
            _w = writer.get_last_run_output()
        except Exception:
            _w = None
        draft_text = (_w.get("content") if isinstance(_w, dict) else getattr(_w, "content", None)) or ""

        # Revisar
        reviewer.run(
            (
                "Revise e melhore o texto abaixo, mantendo o estilo indicado.\n"
                "Entregue a versão final revisada.\n\n"
                f"Estilo: {req.style or 'neutro'}\n\n"
                f"Texto:\n{draft_text}\n"
            )
        )
        _rev = None
        try:
            _rev = reviewer.get_last_run_output()
        except Exception:
            _rev = None
        final_text = (_rev.get("content") if isinstance(_rev, dict) else getattr(_rev, "content", None)) or ""

        # Fallback final se vazio
        if not final_text:
            tmpl = agents_map.get("Template Agent") or next(iter(agents_map.values()), None)
            if tmpl:
                try:
                    tmpl.run(
                        (
                            "Escreva um texto claro e bem estruturado em Markdown.\n\n"
                            f"Tópico: {req.prompt}\n"
                            f"Estilo: {req.style or 'neutro'}\n"
                        )
                    )
                    _tf = None
                    try:
                        _tf = tmpl.get_last_run_output()
                    except Exception:
                        _tf = None
                    final_text = (_tf.get("content") if isinstance(_tf, dict) else getattr(_tf, "content", None)) or final_text
                except Exception:
                    pass
        return {"team": "content-pro", "output": final_text}

    # ===== Times: gestão (CRUD + membros) =====
    class TeamCreateRequest(BaseModel):
        name: str
        members: Optional[List[str]] = None
        description: Optional[str] = None

    @teams_router.post("")
    async def teams_create(req: TeamCreateRequest, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        key = req.name.lower()
        if key in teams_map:
            raise HTTPException(status_code=409, detail="Team already exists")
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        members: List[Agent] = []
        if req.members:
            for m in req.members:
                ag = agents_map.get(m)
                if not ag:
                    raise HTTPException(status_code=400, detail=f"Unknown agent: {m}")
                members.append(ag)
        team = Team(members=members, name=req.name, description=req.description or "", markdown=True)
        teams_map[key] = team
        app.state.teams = teams_map
        return {"name": req.name, "members": [getattr(a, "name", None) for a in members]}

    @teams_router.get("")
    async def teams_list():
        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        items = []
        for name, team in teams_map.items():
            try:
                mems = [getattr(a, "name", None) for a in getattr(team, "members", [])]
            except Exception:
                mems = []
            items.append({"name": name, "members": mems})
        return items

    @teams_router.get("/{team_name}")
    async def teams_get(team_name: str):
        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        team = teams_map.get(team_name.lower())
        if not team:
            # nomes reservados não têm instância fixa
            if team_name.lower() in ("review", "content-pro"):
                return {"name": team_name.lower(), "members": []}
            raise HTTPException(status_code=404, detail="Team not found")
        try:
            mems = [getattr(a, "name", None) for a in getattr(team, "members", [])]
        except Exception:
            mems = []
        return {"name": team_name, "members": mems}

    class TeamMemberAddRequest(BaseModel):
        agent: str

    @teams_router.post("/{team_name}/members")
    async def teams_add_member(team_name: str, req: TeamMemberAddRequest, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        team = teams_map.get(team_name.lower())
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        ag = agents_map.get(req.agent)
        if not ag:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {req.agent}")
        try:
            getattr(team, "members", []).append(ag)
        except Exception:
            raise HTTPException(status_code=500, detail="Unable to add member")
        return {"name": team_name, "added": req.agent}

    @teams_router.delete("/{team_name}/members/{agent_name}")
    async def teams_remove_member(team_name: str, agent_name: str, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        team = teams_map.get(team_name.lower())
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        try:
            mems = getattr(team, "members", [])
            idx = None
            for i, m in enumerate(mems):
                if getattr(m, "name", None) == agent_name:
                    idx = i
                    break
            if idx is None:
                raise HTTPException(status_code=404, detail="Agent not in team")
            mems.pop(idx)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail="Unable to remove member")
        return {"name": team_name, "removed": agent_name}

    @teams_router.delete("/{team_name}")
    async def teams_delete(team_name: str, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
        key = team_name.lower()
        if key not in teams_map:
            raise HTTPException(status_code=404, detail="Team not found")
        teams_map.pop(key, None)
        app.state.teams = teams_map
        return {"deleted": team_name}

    app.include_router(teams_router)

    # Auth router (JWT opcional)
    auth_router = APIRouter(prefix="/auth", tags=["auth"])

    class LoginRequest(BaseModel):
        username: str

    @auth_router.post("/login")
    async def login(req: LoginRequest):
        s = get_settings()
        if not s.JWT_SECRET:
            raise HTTPException(status_code=400, detail="JWT not configured")
        admins = {u.strip() for u in (s.ADMIN_USERS or "").split(",") if u.strip()}
        role = "admin" if req.username in admins else "user"
        token = create_access_token(subject=req.username, role=role, secret=s.JWT_SECRET, expires_minutes=s.JWT_EXPIRES_MIN)
        return {"access_token": token, "token_type": "bearer", "role": role}

    @auth_router.get("/me")
    async def me(user=Depends(get_current_user)):
        return user

    app.include_router(auth_router)

    # RAG router
    rag_router = APIRouter(prefix="/rag", tags=["rag"]) 
    _setup_security_and_rate_limit(rag_router)
    # RBAC opcional: restringe ingest/query a usuários autenticados (admin para ingest)
    if is_auth_enabled():
        rag_router.dependencies.append(Depends(get_current_user))

    class IngestTextsRequest(BaseModel):
        collection: str
        texts: List[str]
        metadatas: Optional[List[Dict]] = None

    class QueryRequest(BaseModel):
        collection: str
        query_text: str
        top_k: Optional[int] = 5

    @rag_router.post("/ingest-texts")
    async def rag_ingest_texts(req: IngestTextsRequest, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        try:
            from src.rag.service import get_rag_service  # lazy import
        except Exception:
            raise HTTPException(status_code=503, detail="RAG não habilitado. Instale o extra: pip install -e .[rag]")
        rag = get_rag_service()
        res = rag.add_texts(collection=req.collection, texts=req.texts, metadatas=req.metadatas)
        return res

    @rag_router.post("/query")
    async def rag_query(req: QueryRequest):
        try:
            from src.rag.service import get_rag_service  # lazy import
        except Exception:
            raise HTTPException(status_code=503, detail="RAG não habilitado. Instale o extra: pip install -e .[rag]")
        rag = get_rag_service()
        res = rag.query(collection=req.collection, query_text=req.query_text, top_k=req.top_k or 5)
        return {"results": res}

    class IngestUrlsRequest(BaseModel):
        collection: str
        urls: List[str]

    @rag_router.post("/ingest-urls")
    async def rag_ingest_urls(req: IngestUrlsRequest, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        try:
            from src.rag.service import get_rag_service  # lazy import
        except Exception:
            raise HTTPException(status_code=503, detail="RAG não habilitado. Instale o extra: pip install -e .[rag]")
        rag = get_rag_service()
        res = await rag.ingest_urls(collection=req.collection, urls=req.urls)
        return res

    # app.include_router(rag_router)  # mover para depois de definir todas as rotas RAG
    
    # Ingestão de arquivos (PDF/MD)
    class IngestFilesRequest(BaseModel):
        collection: str

    @rag_router.post("/ingest-files")
    async def rag_ingest_files(collection: str = Form(...), files: List[UploadFile] = File(...), user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        try:
            from src.rag.service import get_rag_service  # lazy import
        except Exception:
            raise HTTPException(status_code=503, detail="RAG não habilitado. Instale o extra: pip install -e .[rag]")
        rag = get_rag_service()
        payload: List[tuple[str, bytes]] = []
        for f in files:
            data = await f.read()
            payload.append((f.filename, data))
        if not payload:
            return {"added": 0}
        res = rag.ingest_files(collection=collection, files=payload)
        return res

    # RAG: gestão de coleções e documentos (se suportado pelo backend RAG)
    @rag_router.get("/collections")
    async def rag_collections():
        try:
            from src.rag.service import get_rag_service  # lazy import
        except Exception:
            raise HTTPException(status_code=503, detail="RAG não habilitado. Instale o extra: pip install -e .[rag]")
        rag = get_rag_service()
        if hasattr(rag, "list_collections"):
            return {"collections": rag.list_collections()}
        raise HTTPException(status_code=501, detail="Operação não suportada pelo backend RAG atual")

    @rag_router.get("/collections/{collection}/docs")
    async def rag_list_docs(collection: str):
        try:
            from src.rag.service import get_rag_service  # lazy import
        except Exception:
            raise HTTPException(status_code=503, detail="RAG não habilitado. Instale o extra: pip install -e .[rag]")
        rag = get_rag_service()
        if hasattr(rag, "list_docs"):
            return {"docs": rag.list_docs(collection=collection)}
        raise HTTPException(status_code=501, detail="Operação não suportada pelo backend RAG atual")

    @rag_router.delete("/collections/{collection}")
    async def rag_delete_collection(collection: str, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        try:
            from src.rag.service import get_rag_service  # lazy import
        except Exception:
            raise HTTPException(status_code=503, detail="RAG não habilitado. Instale o extra: pip install -e .[rag]")
        rag = get_rag_service()
        if hasattr(rag, "delete_collection"):
            ok = rag.delete_collection(collection=collection)
            if not ok:
                raise HTTPException(status_code=404, detail="Collection not found")
            return {"deleted": collection}
        raise HTTPException(status_code=501, detail="Operação não suportada pelo backend RAG atual")

    @rag_router.delete("/collections/{collection}/docs/{doc_id}")
    async def rag_delete_doc(collection: str, doc_id: str, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        try:
            from src.rag.service import get_rag_service  # lazy import
        except Exception:
            raise HTTPException(status_code=503, detail="RAG não habilitado. Instale o extra: pip install -e .[rag]")
        rag = get_rag_service()
        if hasattr(rag, "delete_doc"):
            ok = rag.delete_doc(collection=collection, doc_id=doc_id)
            if not ok:
                raise HTTPException(status_code=404, detail="Document not found")
            return {"deleted": doc_id}
        raise HTTPException(status_code=501, detail="Operação não suportada pelo backend RAG atual")

    app.include_router(rag_router)

    # Storage router (local)
    storage_router = APIRouter(prefix="/storage", tags=["storage"]) 
    _setup_security_and_rate_limit(storage_router)
    # RBAC opcional: restringe upload/list a usuários autenticados (upload só admin)
    if is_auth_enabled():
        storage_router.dependencies.append(Depends(get_current_user))

    class UploadTextRequest(BaseModel):
        name: str
        content: str

    @storage_router.post("/upload-text")
    async def storage_upload_text(req: UploadTextRequest, user=Depends(get_current_user)):
        # Se auth estiver habilitada, exigir admin
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        st = get_storage()
        path = st.save_text(req.name, req.content)
        return {"path": path}

    @storage_router.get("/list")
    async def storage_list():
        st = get_storage()
        return {"files": st.list_files()}

    @storage_router.delete("/{name}")
    async def storage_delete(name: str, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        st = get_storage()
        ok = st.delete_file(name)
        if not ok:
            raise HTTPException(status_code=404, detail="File not found")
        return {"deleted": name}

    app.include_router(storage_router)

    agents_router = APIRouter(prefix="/agents", tags=["agents"]) 
    _setup_security_and_rate_limit(agents_router)

    class AgentCreateRequest(BaseModel):
        name: str
        role: Optional[str] = None
        model_provider: Optional[str] = None
        model_id: Optional[str] = None
        use_database: Optional[bool] = False
        instructions: Optional[List[str]] = None
        markdown: Optional[bool] = True
        add_history_to_context: Optional[bool] = True
        debug_mode: Optional[bool] = False

    class AgentRunRequest(BaseModel):
        prompt: str

    @agents_router.post("")
    async def agents_create(req: AgentCreateRequest, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        if req.name in agents_map:
            raise HTTPException(status_code=409, detail="Agent already exists")
        agent = BaseAgent.create(
            name=req.name,
            role=req.role,
            instructions=req.instructions or [],
            model_provider=req.model_provider or get_settings().DEFAULT_MODEL_PROVIDER,
            model_id=req.model_id or get_settings().DEFAULT_MODEL_ID,
            use_database=bool(req.use_database),
            add_history_to_context=bool(req.add_history_to_context),
            markdown=bool(req.markdown),
            debug_mode=bool(req.debug_mode),
        )
        agents_map[req.name] = agent
        app.state.agents = agents_map
        return {"name": req.name, "role": getattr(agent, "role", None)}

    @agents_router.get("")
    async def agents_list():
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        return [{"name": k, "role": getattr(v, "role", None)} for k, v in agents_map.items()]

    @agents_router.get("/{name}")
    async def agents_get(name: str):
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        ag = agents_map.get(name)
        if not ag:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"name": name, "role": getattr(ag, "role", None)}

    @agents_router.post("/{name}/run")
    async def agents_run(name: str, req: AgentRunRequest):
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        ag = agents_map.get(name)
        if not ag:
            raise HTTPException(status_code=404, detail="Agent not found")
        ag.run(req.prompt)
        _out = None
        try:
            _out = ag.get_last_run_output()
        except Exception:
            _out = None
        out_text = (_out.get("content") if isinstance(_out, dict) else getattr(_out, "content", None)) or ""
        return {"agent": name, "output": out_text}

    @agents_router.delete("/{name}")
    async def agents_delete(name: str, user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        if name not in agents_map:
            raise HTTPException(status_code=404, detail="Agent not found")
        agents_map.pop(name, None)
        app.state.agents = agents_map
        return {"deleted": name}

    app.include_router(agents_router)

    # Métricas middleware e endpoint
    if not hasattr(app.state, "metrics"):
        app.state.metrics = {
            "requests": 0,
            "per_route": {},           # {route: {count, total_ms}}
            "per_status": {},          # {status: count}
            "per_route_status": {},    # {route: {status: count}}
        }

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.time()
        req_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        method = request.method
        path = request.url.path
        ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "-")
        auth_present = bool(request.headers.get("authorization"))

        response = None
        try:
            # Interceptar GET /workflows/registry (com ou sem barra final)
            normalized_path = request.url.path.rstrip("/")
            if method == "GET" and normalized_path == "/workflows/registry":
                reg = getattr(app.state, "workflows_registry", {})
                response = JSONResponse(list(reg.values()))
                return response

            response = await call_next(request)
            return response
        finally:
            dur = (time.time() - start) * 1000.0
            status_code = getattr(response, "status_code", 500) if response else 500
            try:
                if response is not None:
                    response.headers["x-request-id"] = req_id
            except Exception:
                pass

            # Atualizar métricas
            m = app.state.metrics
            m["requests"] += 1
            pr = m["per_route"].setdefault(path, {"count": 0, "total_ms": 0.0})
            pr["count"] += 1
            pr["total_ms"] += dur
            m["per_status"][status_code] = m["per_status"].get(status_code, 0) + 1
            prs = m["per_route_status"].setdefault(path, {})
            prs[status_code] = prs.get(status_code, 0) + 1

            # Log estruturado por requisição
            logger = getattr(app.state, "logger", None)
            if logger:
                try:
                    logger.info(
                        {
                            "event": "request",
                            "id": req_id,
                            "method": method,
                            "path": path,
                            "status": status_code,
                            "duration_ms": round(dur, 2),
                            "ip": ip,
                            "user_agent": ua,
                            "authenticated": auth_present,
                            "rate_limited": bool(status_code == 429),
                        }
                    )
                except Exception:
                    # Se o logger não suportar objetos, serialize como string
                    try:
                        logger.info(f"event=request id={req_id} method={method} path={path} status={status_code} duration_ms={round(dur,2)} ip={ip} auth={auth_present}")
                    except Exception:
                        pass

    metrics_router = APIRouter(prefix="/metrics", tags=["metrics"]) 

    @metrics_router.get("")
    async def metrics_get():
        per_route = {}
        for k, v in app.state.metrics["per_route"].items():
            avg = (v["total_ms"] / v["count"]) if v["count"] else 0.0
            per_route[k] = {"count": v["count"], "avg_ms": round(avg, 2)}
        return {
            "requests": app.state.metrics["requests"],
            "per_route": per_route,
            "per_status": app.state.metrics.get("per_status", {}),
            "per_route_status": app.state.metrics.get("per_route_status", {}),
        }

    app.include_router(metrics_router)

    # Health e Admin
    health_router = APIRouter(tags=["health"]) 

    @health_router.get("/health")
    async def health():
        now = time.time()
        started = getattr(app.state, "started_at", None)
        uptime = (now - started) if started else None
        return {"status": "ok", "uptime_s": round(uptime, 2) if uptime else None}

    app.include_router(health_router)

    admin_router = APIRouter(prefix="/admin", tags=["admin"]) 

    @admin_router.get("/config")
    async def admin_config(user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        s = get_settings()
        return {
            "DEFAULT_MODEL_PROVIDER": s.DEFAULT_MODEL_PROVIDER,
            "DEFAULT_MODEL_ID": s.DEFAULT_MODEL_ID,
            "CORS_ALLOW_ORIGINS": s.CORS_ALLOW_ORIGINS,
            "RATE_LIMIT_ENABLED": getattr(s, "RATE_LIMIT_ENABLED", False),
            "RATE_LIMIT_WINDOW_SECONDS": getattr(s, "RATE_LIMIT_WINDOW_SECONDS", 60),
            "RATE_LIMIT_RAG_QUERY": getattr(s, "RATE_LIMIT_RAG_QUERY", None),
            "RATE_LIMIT_RAG_INGEST": getattr(s, "RATE_LIMIT_RAG_INGEST", None),
            "RATE_LIMIT_AUTH": getattr(s, "RATE_LIMIT_AUTH", None),
            "RATE_LIMIT_AGENTICS": getattr(s, "RATE_LIMIT_AGENTICS", None),
            "RATE_LIMIT_DEFAULT": getattr(s, "RATE_LIMIT_DEFAULT", None),
            "DEBUG": s.DEBUG,
            "LOG_LEVEL": s.LOG_LEVEL,
        }

    @admin_router.get("/rate-limit/status")
    async def admin_rate_limit_status(user=Depends(get_current_user)):
        if is_auth_enabled():
            role = (user or {}).get("role", "user")
            if role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")
        s = get_settings()
        return {
            "enabled": getattr(s, "RATE_LIMIT_ENABLED", False),
            "window_seconds": getattr(s, "RATE_LIMIT_WINDOW_SECONDS", 60),
            "limits": {
                "rag_query": getattr(s, "RATE_LIMIT_RAG_QUERY", None),
                "rag_ingest": getattr(s, "RATE_LIMIT_RAG_INGEST", None),
                "auth": getattr(s, "RATE_LIMIT_AUTH", None),
                "agentics": getattr(s, "RATE_LIMIT_AGENTICS", None),
                "default": getattr(s, "RATE_LIMIT_DEFAULT", None),
            },
            "counters_hint": "Use /metrics para contadores por rota e status.",
        }

    app.include_router(admin_router)

    # Memory endpoints (básico)
    memory_router = APIRouter(prefix="/memory", tags=["memory"]) 

    @memory_router.get("/agent/{agent_name}/history")
    async def memory_history(agent_name: str):
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        ag = agents_map.get(agent_name)
        if not ag:
            raise HTTPException(status_code=404, detail="Agent not found")
        try:
            hist = ag.get_chat_history()
        except Exception:
            hist = []
        return {"agent": agent_name, "history": hist}

    @memory_router.get("/agent/{agent_name}/summary")
    async def memory_summary(agent_name: str):
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        ag = agents_map.get(agent_name)
        if not ag:
            raise HTTPException(status_code=404, detail="Agent not found")
        try:
            summ = ag.get_session_summary()
        except Exception:
            summ = None
        return {"agent": agent_name, "summary": summ}

    @memory_router.post("/agent/{agent_name}/reset")
    async def memory_reset(agent_name: str):
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        ag = agents_map.get(agent_name)
        if not ag:
            raise HTTPException(status_code=404, detail="Agent not found")
        try:
            ag.delete_session()
        except Exception:
            pass
        return {"agent": agent_name, "status": "reset"}

    class MemoryPruneRequest(BaseModel):
        max_messages: Optional[int] = None
        max_tokens: Optional[int] = None

    @memory_router.post("/agent/{agent_name}/prune")
    async def memory_prune(agent_name: str, req: MemoryPruneRequest):
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        ag = agents_map.get(agent_name)
        if not ag:
            raise HTTPException(status_code=404, detail="Agent not found")
        try:
            hist = ag.get_chat_history() or []
        except Exception:
            hist = []
        count = len(hist)
        content_len = 0
        try:
            for m in hist:
                content = getattr(m, "content", "")
                if isinstance(content, str):
                    content_len += len(content)
        except Exception:
            pass
        approx_tokens = max(1, content_len // 4) if content_len > 0 else 0
        should_prune = False
        if req.max_messages is not None and count > req.max_messages:
            should_prune = True
        if req.max_tokens is not None and approx_tokens > req.max_tokens:
            should_prune = True
        if should_prune:
            # Gerar/obter resumo curto antes do reset
            summary_text = None
            try:
                summary_text = ag.get_session_summary()
            except Exception:
                summary_text = None

            if not summary_text:
                # Fallback: pedir um resumo curto ao agente com base nas últimas mensagens
                try:
                    preview_messages = []
                    try:
                        preview_messages = hist[-10:]
                    except Exception:
                        preview_messages = hist
                    joined = "\n\n".join([str(getattr(m, "content", ""))[:500] for m in preview_messages])
                    prompt = (
                        "Resuma a conversa do agente em no máximo 8 bullets, mantendo fatos essenciais e decisões.\n"
                        "Ignore saídas técnicas ou ruído.\n\n"
                        f"Contexto:\n{joined}"
                    )
                    ag.run(prompt)
                    summary_text = ag.get_last_run_output() or ""
                except Exception:
                    summary_text = ""

            # Persistir o resumo em arquivo simples
            try:
                from src.storage.service import get_storage
                st = get_storage()
                sid = getattr(ag, "session_id", None) or str(uuid.uuid4())
                fname = f"summary_{agent_name}_{sid}.md"
                content = f"# Resumo da sessão ({agent_name})\n\n{summary_text or 'Sem resumo gerado.'}"
                path = st.save_text(fname, content)
            except Exception:
                path = None

            # Resetar sessão
            try:
                # delete_session exige session_id em algumas versões; tente com e sem
                sid = getattr(ag, "session_id", None)
                if sid:
                    ag.delete_session(sid)
                else:
                    ag.delete_session()  # type: ignore
            except Exception:
                pass
            return {"agent": agent_name, "pruned": True, "prev_messages": count, "approx_tokens": approx_tokens, "summary_path": path}
        return {"agent": agent_name, "pruned": False, "messages": count, "approx_tokens": approx_tokens}

    app.include_router(memory_router)

    # Evals simples
    evals_router = APIRouter(prefix="/evals", tags=["evals"]) 

    class EvalRunRequest(BaseModel):
        prompt: str
        team: Optional[str] = None

    @evals_router.post("/run")
    async def eval_run(req: EvalRunRequest):
        start = time.time()
        out = None
        if req.team:
            teams_map: Dict[str, Team] = getattr(app.state, "teams", {})
            team = teams_map.get(req.team.lower())
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
            team.run(req.prompt)
            out = team.get_last_run_output()
        else:
            agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
            ag = agents_map.get("Template Agent") or next(iter(agents_map.values()), None)
            if not ag:
                raise HTTPException(status_code=500, detail="No agent available")
            ag.run(req.prompt)
            out = ag.get_last_run_output()
        dur_ms = (time.time() - start) * 1000.0
        return {"latency_ms": round(dur_ms, 2), "output": out}

    app.include_router(evals_router)

    # HITL: fluxo em duas etapas (start -> review -> complete)
    class HITLStartRequest(BaseModel):
        topic: str
        style: Optional[str] = None

    class HITLCompleteRequest(BaseModel):
        session_id: str
        approve: bool = True
        feedback: Optional[str] = None

    @router.post("/hitl/start")
    async def hitl_start(req: HITLStartRequest):
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        researcher = agents_map.get("Researcher")
        if not researcher:
            raise HTTPException(status_code=500, detail="Researcher agent not available")

        # Executar pesquisa
        researcher.run(f"Pesquise sobre: {req.topic}. Forneça pontos objetivos e fontes.")
        _r = None
        try:
            _r = researcher.get_last_run_output()
        except Exception:
            _r = None
        research_text = (_r.get("content") if isinstance(_r, dict) else getattr(_r, "content", None)) or ""

        # Fallback simples: tentar novamente com prompt alternativo; usar Template Agent se ainda vazio
        if not research_text:
            try:
                researcher.run(f"Liste 5 pontos objetivos sobre: {req.topic} com 1-2 fontes.")
                _r2 = None
                try:
                    _r2 = researcher.get_last_run_output()
                except Exception:
                    _r2 = None
                research_text = (_r2.get("content") if isinstance(_r2, dict) else getattr(_r2, "content", None)) or research_text
            except Exception:
                pass
        if not research_text:
            try:
                tmpl = agents_map.get("Template Agent")
                if tmpl:
                    tmpl.run(f"Pesquise sobre: {req.topic}. Forneça pontos objetivos e fontes.")
                    _rt = None
                    try:
                        _rt = tmpl.get_last_run_output()
                    except Exception:
                        _rt = None
                    research_text = (_rt.get("content") if isinstance(_rt, dict) else getattr(_rt, "content", None)) or research_text
            except Exception:
                pass
        if not research_text:
            research_text = f"Não foi possível gerar pesquisa automática sobre: {req.topic}."

        # Persistir sessão
        repo = getattr(app.state, "hitl_repo", None)
        if not repo:
            raise HTTPException(status_code=500, detail="HITL repository unavailable")
        sess = repo.create_session(topic=req.topic, style=req.style, research=research_text)
        return {"session_id": sess.id, "topic": sess.topic, "research": sess.research}

    @router.post("/hitl/complete")
    async def hitl_complete(req: HITLCompleteRequest):
        repo = getattr(app.state, "hitl_repo", None)
        if not repo:
            raise HTTPException(status_code=500, detail="HITL repository unavailable")

        # Buscar sessão para obter estilo/pesquisa
        sess = repo.get(req.session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Invalid session_id")

        if not req.approve:
            sess = repo.reject(req.session_id)
            return {"status": sess.status, "session_id": sess.id}

        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        writer = agents_map.get("Writer")
        if not writer:
            raise HTTPException(status_code=500, detail="Writer agent not available")

        style = (sess.style or "neutro")
        research_text = (sess.research or "")
        feedback = req.feedback or ""

        writer.run(
            (
                "Escreva um texto claro e bem estruturado em Markdown, baseado na pesquisa a seguir.\n\n"
                f"Pesquisa:\n{research_text}\n\n"
                f"Estilo: {style}\n"
                f"Observações do revisor: {feedback}\n"
            )
        )
        _wf = None
        try:
            _wf = writer.get_last_run_output()
        except Exception:
            _wf = None
        final_text = (_wf.get("content") if isinstance(_wf, dict) else getattr(_wf, "content", None)) or ""

        # Fallback final: Template Agent para produzir conteúdo se ainda estiver vazio
        if not final_text:
            try:
                agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
                tmpl = agents_map.get("Template Agent") or next(iter(agents_map.values()), None)
                if tmpl:
                    tmpl.run(
                        (
                            "Escreva um texto claro e bem estruturado em Markdown, baseado na pesquisa a seguir.\n\n"
                            f"Pesquisa:\n{research_text}\n\n"
                            f"Estilo: {style}\n"
                            f"Observações do revisor: {feedback}\n"
                        )
                    )
                    _tf = None
                    try:
                        _tf = tmpl.get_last_run_output()
                    except Exception:
                        _tf = None
                    final_text = (_tf.get("content") if isinstance(_tf, dict) else getattr(_tf, "content", None)) or final_text
            except Exception:
                pass

        sess = repo.approve(req.session_id, final_text=final_text, feedback=feedback)
        return {"status": sess.status, "session_id": sess.id, "content": sess.final_text}

    # HITL extras: list, get, cancel
    class HITLCancelRequest(BaseModel):
        session_id: str
        reason: Optional[str] = None

    def _hitl_session_to_dict(sess):
        try:
            return {
                "id": sess.id,
                "topic": getattr(sess, "topic", None),
                "style": getattr(sess, "style", None),
                "status": getattr(sess, "status", None),
                "created_at": getattr(sess, "created_at", None).isoformat() if getattr(sess, "created_at", None) else None,
                "research": getattr(sess, "research", None),
                "final_text": getattr(sess, "final_text", None),
            }
        except Exception:
            return {"id": getattr(sess, "id", None)}

    def _hitl_action_to_dict(act):
        try:
            return {
                "id": getattr(act, "id", None),
                "session_id": getattr(act, "session_id", None),
                "action": getattr(act, "action", None),
                "payload": getattr(act, "payload", None),
                "created_at": getattr(act, "created_at", None).isoformat() if getattr(act, "created_at", None) else None,
            }
        except Exception:
            return {"id": getattr(act, "id", None)}

    @router.get("/hitl/{session_id}")
    async def hitl_get(session_id: str):
        repo = getattr(app.state, "hitl_repo", None)
        if not repo:
            raise HTTPException(status_code=500, detail="HITL repository unavailable")
        sess = repo.get(session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Invalid session_id")
        actions = repo.actions(session_id)
        return {"session": _hitl_session_to_dict(sess), "actions": [_hitl_action_to_dict(a) for a in actions]}

    @router.get("/hitl")
    async def hitl_list(status: Optional[str] = None, limit: int = 50, offset: int = 0):
        repo = getattr(app.state, "hitl_repo", None)
        if not repo:
            raise HTTPException(status_code=500, detail="HITL repository unavailable")
        rows = repo.list(status=status, limit=limit, offset=offset)
        return {"items": [_hitl_session_to_dict(s) for s in rows], "count": len(rows)}

    @router.post("/hitl/cancel")
    async def hitl_cancel(req: HITLCancelRequest):
        repo = getattr(app.state, "hitl_repo", None)
        if not repo:
            raise HTTPException(status_code=500, detail="HITL repository unavailable")
        try:
            sess = repo.cancel(req.session_id, reason=req.reason)
        except ValueError:
            raise HTTPException(status_code=404, detail="Invalid session_id")
        return {"status": sess.status, "session_id": sess.id}

    # Novo workflow: research -> write -> review
    @router.post("/research-write-review")
    async def research_write_review(req: ResearchWriteRequest):
        agents_map: Dict[str, Agent] = getattr(app.state, "agents", {})
        researcher = agents_map.get("Researcher")
        writer = agents_map.get("Writer")
        reviewer = agents_map.get("Reviewer")
        if not researcher or not writer or not reviewer:
            raise HTTPException(status_code=500, detail="Required agents not available")

        # Pesquisa
        researcher.run(f"Pesquise sobre: {req.topic}. Forneça pontos objetivos e fontes.")
        _res = None
        try:
            _res = researcher.get_last_run_output()
        except Exception:
            _res = None
        research_text = (_res.get("content") if isinstance(_res, dict) else getattr(_res, "content", None)) or ""

        # Opcional: enriquecer com RAG
        if req.use_rag and req.collection:
            try:
                from src.rag.service import get_rag_service  # lazy import
                rag = get_rag_service()
                results = rag.query(collection=req.collection, query_text=req.topic, top_k=req.top_k or 3)
                ctx = "\n\n".join([
                    f"[Fonte] {r.get('metadata',{}).get('title','doc')}\n{r.get('text','')}" for r in results
                ])
                if ctx:
                    research_text = f"{research_text}\n\nContexto Recuperado:\n{ctx}"
            except Exception:
                pass

        # Escrita
        writer.run(
            (
                "Escreva um texto claro e bem estruturado em Markdown, baseado na pesquisa a seguir.\n\n"
                f"Pesquisa:\n{research_text}\n\n"
                f"Estilo: {req.style or 'neutro'}\n"
            )
        )
        _wout = None
        try:
            _wout = writer.get_last_run_output()
        except Exception:
            _wout = None
        draft_text = (_wout.get("content") if isinstance(_wout, dict) else getattr(_wout, "content", None)) or ""

        # Revisão
        reviewer.run(
            (
                "Revise e melhore o texto abaixo, mantendo o estilo indicado.\n"
                "Entregue a versão final revisada.\n\n"
                f"Estilo: {req.style or 'neutro'}\n\n"
                f"Texto:\n{draft_text}\n"
            )
        )
        _rv = None
        try:
            _rv = reviewer.get_last_run_output()
        except Exception:
            _rv = None
        final_text = (_rv.get("content") if isinstance(_rv, dict) else getattr(_rv, "content", None)) or ""

        # Fallback final via Template Agent se vazio
        if not final_text:
            tmpl = agents_map.get("Template Agent") or next(iter(agents_map.values()), None)
            if tmpl:
                try:
                    tmpl.run(
                        (
                            "Escreva um texto claro e bem estruturado em Markdown.\n\n"
                            f"Tópico: {req.topic}\n"
                            f"Estilo: {req.style or 'neutro'}\n"
                        )
                    )
                    _tf = None
                    try:
                        _tf = tmpl.get_last_run_output()
                    except Exception:
                        _tf = None
                    final_text = (_tf.get("content") if isinstance(_tf, dict) else getattr(_tf, "content", None)) or final_text
                except Exception:
                    pass

        return {
            "topic": req.topic,
            "research": research_text,
            "draft": draft_text,
            "final": final_text,
        }

    # Incluir router de workflows (inclui research-write e rotas HITL)
    app.include_router(router)
    return app
