"""
Personas API - CRUD endpoints for chat personas.

Personas são templates de personalidade que orientam as respostas do chat.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personas", tags=["Personas"])

# ============================================
# IN-MEMORY STORAGE
# ============================================

_personas_store: Dict[str, Dict] = {}

# Default personas
DEFAULT_PERSONAS = [
    {
        "id": "default-assistant",
        "name": "Assistente Geral",
        "description": "Um assistente inteligente e prestativo para tarefas gerais.",
        "system_prompt": """Você é um assistente inteligente e prestativo. 
Responda de forma clara, concisa e útil. 
Seja educado e profissional.
Se não souber algo, admita honestamente.""",
        "avatar_emoji": "🤖",
        "is_public": True,
        "is_default": True,
        "default_model": "llama-3.1-8b-instant",
        "temperature": 0.7,
        "max_tokens": 4096,
        "tags": ["geral", "assistente"],
    },
    {
        "id": "cto-senior",
        "name": "CTO Sênior",
        "description": "Especialista em arquitetura de software e decisões técnicas estratégicas.",
        "system_prompt": """Você é um CTO Sênior com 20+ anos de experiência em tecnologia.
Especialidades: arquitetura de sistemas, escalabilidade, DevOps, cloud, segurança.
Responda com profundidade técnica, mas explique conceitos quando necessário.
Considere trade-offs, custos e impacto no negócio em suas recomendações.
Use exemplos práticos e cite tecnologias/padrões específicos quando relevante.""",
        "avatar_emoji": "👨‍💻",
        "is_public": True,
        "is_default": False,
        "default_model": "claude-haiku-4-5",
        "temperature": 0.5,
        "max_tokens": 8192,
        "tags": ["tech", "arquitetura", "liderança"],
    },
    {
        "id": "data-analyst",
        "name": "Analista de Dados",
        "description": "Especialista em análise de dados, SQL, Python e visualização.",
        "system_prompt": """Você é um Analista de Dados Sênior especializado em:
- SQL avançado e otimização de queries
- Python (pandas, numpy, scikit-learn)
- Visualização de dados (matplotlib, seaborn, plotly)
- Estatística e machine learning básico
- Business Intelligence e métricas

Sempre forneça código quando relevante.
Explique sua metodologia e assunções.
Sugira visualizações apropriadas para os dados.""",
        "avatar_emoji": "📊",
        "is_public": True,
        "is_default": False,
        "default_model": "gpt-5-mini",
        "temperature": 0.3,
        "max_tokens": 4096,
        "tags": ["dados", "analytics", "sql", "python"],
    },
    {
        "id": "geo-ai-expert",
        "name": "Especialista GeoAI",
        "description": "Expert em geoprocessamento, sensoriamento remoto e IA geoespacial.",
        "system_prompt": """Você é um especialista em GeoAI e Geoprocessamento com expertise em:
- Sensoriamento remoto e análise de imagens de satélite
- GIS (QGIS, ArcGIS, PostGIS)
- Python geoespacial (geopandas, rasterio, shapely, GDAL)
- Machine learning para dados geoespaciais
- Análise territorial e ambiental

Forneça código Python quando relevante.
Cite fontes de dados geoespaciais (Sentinel, Landsat, OSM).
Considere aspectos de projeção e sistemas de coordenadas.""",
        "avatar_emoji": "🌍",
        "is_public": True,
        "is_default": False,
        "default_model": "claude-haiku-4-5",
        "temperature": 0.4,
        "max_tokens": 8192,
        "tags": ["geo", "gis", "remote-sensing", "ai"],
    },
    {
        "id": "code-reviewer",
        "name": "Code Reviewer",
        "description": "Especialista em revisão de código e boas práticas.",
        "system_prompt": """Você é um Code Reviewer experiente focado em:
- Clean Code e SOLID principles
- Design Patterns apropriados
- Performance e otimização
- Segurança e vulnerabilidades
- Testabilidade e manutenibilidade

Seja construtivo nas críticas.
Sugira melhorias específicas com exemplos de código.
Priorize issues por severidade (crítico, importante, sugestão).
Elogie boas práticas quando encontrar.""",
        "avatar_emoji": "🔍",
        "is_public": True,
        "is_default": False,
        "default_model": "claude-haiku-4-5",
        "temperature": 0.3,
        "max_tokens": 4096,
        "tags": ["code", "review", "quality"],
    },
]

# Initialize with defaults
for persona in DEFAULT_PERSONAS:
    _personas_store[persona["id"]] = {
        **persona,
        "user_id": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


# ============================================
# MODELS
# ============================================

class PersonaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    system_prompt: str = Field(..., min_length=10)
    avatar_emoji: str = "🤖"
    is_public: bool = False
    default_model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=4096, ge=100, le=32000)
    tags: List[str] = []


class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    avatar_emoji: Optional[str] = None
    is_public: Optional[bool] = None
    default_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tags: Optional[List[str]] = None


class PersonaResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    system_prompt: str
    avatar_emoji: str
    is_public: bool
    is_default: bool
    default_model: Optional[str]
    temperature: float
    max_tokens: int
    tags: List[str]
    user_id: Optional[str]
    created_at: str
    updated_at: str


# ============================================
# ENDPOINTS
# ============================================

@router.get("", response_model=List[PersonaResponse])
async def list_personas(
    user_id: str = Query(default="default_user"),
    include_public: bool = True,
    tag: Optional[str] = None,
):
    """List personas available to user."""
    personas = []
    
    for p in _personas_store.values():
        # Include if: public, or owned by user
        if p.get("is_public") or p.get("user_id") == user_id:
            # Filter by tag if specified
            if tag and tag not in p.get("tags", []):
                continue
            personas.append(p)
    
    # Sort: defaults first, then by name
    personas.sort(key=lambda x: (not x.get("is_default", False), x.get("name", "")))
    
    return personas


@router.post("", response_model=PersonaResponse)
async def create_persona(
    data: PersonaCreate,
    user_id: str = Query(default="default_user"),
):
    """Create a new persona."""
    persona_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    persona = {
        "id": persona_id,
        "name": data.name,
        "description": data.description,
        "system_prompt": data.system_prompt,
        "avatar_emoji": data.avatar_emoji,
        "is_public": data.is_public,
        "is_default": False,
        "default_model": data.default_model,
        "temperature": data.temperature,
        "max_tokens": data.max_tokens or 4096,
        "tags": data.tags,
        "user_id": user_id,
        "created_at": now,
        "updated_at": now,
    }
    
    _personas_store[persona_id] = persona
    logger.info(f"Created persona {persona_id} for user {user_id}")
    
    return persona


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: str):
    """Get a specific persona."""
    if persona_id not in _personas_store:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    return _personas_store[persona_id]


@router.patch("/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: str,
    data: PersonaUpdate,
    user_id: str = Query(default="default_user"),
):
    """Update a persona."""
    if persona_id not in _personas_store:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    persona = _personas_store[persona_id]
    
    # Check ownership (can't edit public defaults unless admin)
    if persona.get("is_default") and persona.get("user_id") is None:
        raise HTTPException(status_code=403, detail="Cannot edit default personas")
    
    if persona.get("user_id") and persona.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this persona")
    
    # Update fields
    if data.name is not None:
        persona["name"] = data.name
    if data.description is not None:
        persona["description"] = data.description
    if data.system_prompt is not None:
        persona["system_prompt"] = data.system_prompt
    if data.avatar_emoji is not None:
        persona["avatar_emoji"] = data.avatar_emoji
    if data.is_public is not None:
        persona["is_public"] = data.is_public
    if data.default_model is not None:
        persona["default_model"] = data.default_model
    if data.temperature is not None:
        persona["temperature"] = data.temperature
    if data.max_tokens is not None:
        persona["max_tokens"] = data.max_tokens
    if data.tags is not None:
        persona["tags"] = data.tags
    
    persona["updated_at"] = datetime.now().isoformat()
    
    logger.info(f"Updated persona {persona_id}")
    return persona


@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: str,
    user_id: str = Query(default="default_user"),
):
    """Delete a persona."""
    if persona_id not in _personas_store:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    persona = _personas_store[persona_id]
    
    # Check ownership
    if persona.get("is_default"):
        raise HTTPException(status_code=403, detail="Cannot delete default personas")
    
    if persona.get("user_id") and persona.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this persona")
    
    del _personas_store[persona_id]
    logger.info(f"Deleted persona {persona_id}")
    
    return {"deleted": persona_id}


@router.get("/defaults/list")
async def list_default_personas():
    """List only default personas."""
    return [p for p in _personas_store.values() if p.get("is_default")]
