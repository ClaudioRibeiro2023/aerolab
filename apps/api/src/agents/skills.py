"""
Biblioteca de Skills para Agentes.

Skills são capacidades modulares e reutilizáveis que podem ser
compostas para criar agentes especializados.

Categorias de Skills:
- Text Processing: Resumo, extração, análise
- Data Analysis: Estatísticas, visualização, insights
- Code: Geração, review, documentação
- Communication: Email, mensagens, relatórios
- Research: Busca, síntese, citações

Arquitetura:
┌─────────────────────────────────────────────────────────────┐
│                    Skills Library                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Skill        │  │ Skill        │  │ Skill        │      │
│  │ Registry     │  │ Composer     │  │ Executor     │      │
│  │              │  │              │  │              │      │
│  │ - Catalog    │  │ - Combine    │  │ - Run        │      │
│  │ - Search     │  │ - Chain      │  │ - Validate   │      │
│  │ - Metadata   │  │ - Inject     │  │ - Cache      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
"""

from typing import Optional, List, Dict, Any, Callable, Awaitable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import re
import json


class SkillCategory(Enum):
    """Categorias de skills."""
    TEXT_PROCESSING = "text_processing"
    DATA_ANALYSIS = "data_analysis"
    CODE = "code"
    COMMUNICATION = "communication"
    RESEARCH = "research"
    REASONING = "reasoning"
    CREATIVITY = "creativity"


class SkillComplexity(Enum):
    """Complexidade de skills."""
    SIMPLE = "simple"       # Operação atômica
    MODERATE = "moderate"   # Algumas etapas
    COMPLEX = "complex"     # Multi-step, pode chamar outras skills


@dataclass
class SkillMetadata:
    """Metadados de uma skill."""
    id: str
    name: str
    description: str
    category: SkillCategory
    complexity: SkillComplexity
    version: str = "1.0.0"
    author: str = "system"
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    examples: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "complexity": self.complexity.value,
            "version": self.version,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "examples": self.examples
        }


@dataclass
class SkillResult:
    """Resultado da execução de uma skill."""
    success: bool
    output: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "metadata": self.metadata,
            "error": self.error
        }


class Skill(ABC):
    """
    Classe base para skills.
    
    Cada skill deve implementar:
    - execute: Lógica principal da skill
    - get_prompt_injection: Instruções para injetar no prompt do agente
    """
    
    def __init__(self, metadata: SkillMetadata):
        self.metadata = metadata
    
    @abstractmethod
    async def execute(self, input_data: Any, context: Optional[Dict] = None) -> SkillResult:
        """Executa a skill."""
        pass
    
    @abstractmethod
    def get_prompt_injection(self) -> str:
        """Retorna instruções para injetar no prompt do agente."""
        pass
    
    def validate_input(self, input_data: Any) -> bool:
        """Valida o input da skill."""
        return True
    
    def __repr__(self) -> str:
        return f"Skill({self.metadata.id})"


# ==================== TEXT PROCESSING SKILLS ====================

class SummarizeSkill(Skill):
    """Skill de resumo de textos."""
    
    def __init__(self, style: str = "bullet_points", max_length: int = 500):
        super().__init__(SkillMetadata(
            id="summarize",
            name="Resumir Texto",
            description="Resume textos longos em formato conciso",
            category=SkillCategory.TEXT_PROCESSING,
            complexity=SkillComplexity.SIMPLE,
            tags=["resumo", "síntese", "texto"],
            examples=[
                {"input": "Texto longo...", "output": "- Ponto 1\n- Ponto 2"}
            ]
        ))
        self.style = style
        self.max_length = max_length
    
    async def execute(self, input_data: str, context: Optional[Dict] = None) -> SkillResult:
        # Em produção, isso chamaria o LLM
        # Aqui retornamos uma simulação
        return SkillResult(
            success=True,
            output=f"Resumo do texto ({len(input_data)} chars original)",
            metadata={"style": self.style, "original_length": len(input_data)}
        )
    
    def get_prompt_injection(self) -> str:
        if self.style == "bullet_points":
            return """
Ao resumir textos:
- Extraia os pontos principais em bullet points
- Limite a no máximo 5-7 pontos
- Use linguagem clara e direta
- Mantenha informações críticas (datas, números, nomes)
"""
        else:
            return f"""
Ao resumir textos:
- Crie um parágrafo conciso de no máximo {self.max_length} caracteres
- Capture a essência do conteúdo
- Mantenha o tom original
"""


class ExtractEntitiesSkill(Skill):
    """Skill de extração de entidades."""
    
    def __init__(self, entity_types: Optional[List[str]] = None):
        super().__init__(SkillMetadata(
            id="extract_entities",
            name="Extrair Entidades",
            description="Extrai entidades nomeadas do texto (pessoas, lugares, datas, etc.)",
            category=SkillCategory.TEXT_PROCESSING,
            complexity=SkillComplexity.SIMPLE,
            tags=["NER", "entidades", "extração"]
        ))
        self.entity_types = entity_types or ["PERSON", "ORG", "DATE", "MONEY", "LOCATION"]
    
    async def execute(self, input_data: str, context: Optional[Dict] = None) -> SkillResult:
        # Extração básica com regex (em produção usaria NER)
        entities = {
            "dates": re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', input_data),
            "emails": re.findall(r'\b[\w.-]+@[\w.-]+\.\w+\b', input_data),
            "money": re.findall(r'R\$\s*[\d.,]+|USD\s*[\d.,]+', input_data),
        }
        
        return SkillResult(
            success=True,
            output=entities,
            metadata={"entity_types": self.entity_types}
        )
    
    def get_prompt_injection(self) -> str:
        return f"""
Ao analisar texto, identifique e extraia:
- Entidades: {', '.join(self.entity_types)}
- Formate como JSON com categorias claras
- Inclua contexto quando relevante
"""


class SentimentAnalysisSkill(Skill):
    """Skill de análise de sentimento."""
    
    def __init__(self):
        super().__init__(SkillMetadata(
            id="sentiment_analysis",
            name="Análise de Sentimento",
            description="Analisa o sentimento do texto (positivo, negativo, neutro)",
            category=SkillCategory.TEXT_PROCESSING,
            complexity=SkillComplexity.SIMPLE,
            tags=["sentimento", "opinião", "análise"]
        ))
    
    async def execute(self, input_data: str, context: Optional[Dict] = None) -> SkillResult:
        # Análise simplificada
        positive_words = ["bom", "ótimo", "excelente", "adorei", "maravilhoso"]
        negative_words = ["ruim", "péssimo", "horrível", "detestei", "terrível"]
        
        text_lower = input_data.lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        if pos_count > neg_count:
            sentiment = "positive"
            score = 0.5 + (pos_count * 0.1)
        elif neg_count > pos_count:
            sentiment = "negative"
            score = 0.5 - (neg_count * 0.1)
        else:
            sentiment = "neutral"
            score = 0.5
        
        return SkillResult(
            success=True,
            output={"sentiment": sentiment, "score": min(1, max(0, score))},
            metadata={"method": "keyword_matching"}
        )
    
    def get_prompt_injection(self) -> str:
        return """
Ao analisar sentimento:
- Classifique como: positivo, negativo ou neutro
- Forneça um score de confiança (0-1)
- Identifique palavras-chave que influenciaram a classificação
- Considere contexto e sarcasmo
"""


# ==================== DATA ANALYSIS SKILLS ====================

class DataInsightsSkill(Skill):
    """Skill de geração de insights de dados."""
    
    def __init__(self):
        super().__init__(SkillMetadata(
            id="data_insights",
            name="Gerar Insights de Dados",
            description="Analisa dados e gera insights acionáveis",
            category=SkillCategory.DATA_ANALYSIS,
            complexity=SkillComplexity.MODERATE,
            tags=["dados", "insights", "análise", "BI"]
        ))
    
    async def execute(self, input_data: Any, context: Optional[Dict] = None) -> SkillResult:
        # Em produção, analisaria dados reais
        return SkillResult(
            success=True,
            output={
                "insights": [
                    "Tendência de crescimento detectada",
                    "Outliers identificados nos dados"
                ],
                "recommendations": [
                    "Investigar causa do pico em X",
                    "Considerar segmentação por Y"
                ]
            }
        )
    
    def get_prompt_injection(self) -> str:
        return """
Ao analisar dados:
- Identifique padrões, tendências e anomalias
- Calcule métricas relevantes (média, mediana, desvio)
- Gere insights acionáveis, não apenas descrições
- Sugira próximos passos baseados nos dados
- Use visualizações quando apropriado
"""


# ==================== CODE SKILLS ====================

class CodeGenerationSkill(Skill):
    """Skill de geração de código."""
    
    def __init__(self, language: str = "python", style_guide: Optional[str] = None):
        super().__init__(SkillMetadata(
            id="code_generation",
            name="Gerar Código",
            description="Gera código limpo e documentado",
            category=SkillCategory.CODE,
            complexity=SkillComplexity.MODERATE,
            tags=["código", "programação", "desenvolvimento"]
        ))
        self.language = language
        self.style_guide = style_guide
    
    async def execute(self, input_data: str, context: Optional[Dict] = None) -> SkillResult:
        return SkillResult(
            success=True,
            output=f"# Generated {self.language} code\n# Based on: {input_data[:50]}...",
            metadata={"language": self.language}
        )
    
    def get_prompt_injection(self) -> str:
        return f"""
Ao gerar código {self.language}:
- Escreva código limpo, legível e bem documentado
- Inclua docstrings/comentários explicativos
- Siga PEP8/convenções da linguagem
- Considere edge cases e error handling
- Prefira soluções simples e idiomáticas
- Inclua type hints quando aplicável
{f'- Siga o guia de estilo: {self.style_guide}' if self.style_guide else ''}
"""


class CodeReviewSkill(Skill):
    """Skill de revisão de código."""
    
    def __init__(self, focus_areas: Optional[List[str]] = None):
        super().__init__(SkillMetadata(
            id="code_review",
            name="Revisar Código",
            description="Revisa código buscando bugs, melhorias e boas práticas",
            category=SkillCategory.CODE,
            complexity=SkillComplexity.MODERATE,
            tags=["code review", "qualidade", "bugs"]
        ))
        self.focus_areas = focus_areas or ["bugs", "performance", "security", "readability"]
    
    async def execute(self, input_data: str, context: Optional[Dict] = None) -> SkillResult:
        return SkillResult(
            success=True,
            output={
                "issues": [],
                "suggestions": [],
                "overall_quality": "good"
            }
        )
    
    def get_prompt_injection(self) -> str:
        return f"""
Ao revisar código, analise:
{chr(10).join(f'- {area.title()}' for area in self.focus_areas)}

Para cada issue encontrado:
- Indique a severidade (critical, high, medium, low)
- Explique o problema
- Sugira a correção
- Seja construtivo e educacional
"""


# ==================== REASONING SKILLS ====================

class StepByStepReasoningSkill(Skill):
    """Skill de raciocínio passo a passo."""
    
    def __init__(self):
        super().__init__(SkillMetadata(
            id="step_by_step",
            name="Raciocínio Passo a Passo",
            description="Resolve problemas com raciocínio estruturado",
            category=SkillCategory.REASONING,
            complexity=SkillComplexity.COMPLEX,
            tags=["raciocínio", "lógica", "chain-of-thought"]
        ))
    
    async def execute(self, input_data: str, context: Optional[Dict] = None) -> SkillResult:
        return SkillResult(
            success=True,
            output={
                "steps": [
                    "Passo 1: Entender o problema",
                    "Passo 2: Identificar variáveis",
                    "Passo 3: Aplicar lógica",
                    "Passo 4: Verificar resultado"
                ],
                "conclusion": "Resultado final"
            }
        )
    
    def get_prompt_injection(self) -> str:
        return """
Ao resolver problemas:
1. Primeiro, entenda completamente o problema
2. Quebre em partes menores
3. Resolva cada parte passo a passo
4. Mostre seu raciocínio explicitamente
5. Verifique sua resposta
6. Considere casos especiais

Use o formato:
Pensamento: [seu raciocínio]
Ação: [próximo passo]
Resultado: [conclusão]
"""


# ==================== SKILL REGISTRY ====================

class SkillRegistry:
    """
    Registro central de skills.
    
    Exemplo:
        registry = SkillRegistry()
        
        # Registrar skills
        registry.register(SummarizeSkill())
        registry.register(CodeGenerationSkill("python"))
        
        # Buscar skills
        text_skills = registry.search(category=SkillCategory.TEXT_PROCESSING)
        
        # Obter skill
        summarize = registry.get("summarize")
    """
    
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._register_builtin_skills()
    
    def _register_builtin_skills(self):
        """Registra skills padrão."""
        builtins = [
            SummarizeSkill(),
            SummarizeSkill(style="paragraph"),
            ExtractEntitiesSkill(),
            SentimentAnalysisSkill(),
            DataInsightsSkill(),
            CodeGenerationSkill("python"),
            CodeGenerationSkill("javascript"),
            CodeReviewSkill(),
            StepByStepReasoningSkill(),
        ]
        
        for skill in builtins:
            self.register(skill)
    
    def register(self, skill: Skill) -> None:
        """Registra uma skill."""
        self._skills[skill.metadata.id] = skill
    
    def get(self, skill_id: str) -> Optional[Skill]:
        """Obtém uma skill por ID."""
        return self._skills.get(skill_id)
    
    def list_all(self) -> List[SkillMetadata]:
        """Lista todas as skills."""
        return [s.metadata for s in self._skills.values()]
    
    def search(
        self,
        query: Optional[str] = None,
        category: Optional[SkillCategory] = None,
        tags: Optional[List[str]] = None
    ) -> List[Skill]:
        """Busca skills."""
        results = list(self._skills.values())
        
        if category:
            results = [s for s in results if s.metadata.category == category]
        
        if tags:
            results = [s for s in results if any(t in s.metadata.tags for t in tags)]
        
        if query:
            query_lower = query.lower()
            results = [s for s in results if 
                query_lower in s.metadata.name.lower() or
                query_lower in s.metadata.description.lower()
            ]
        
        return results
    
    def get_by_category(self, category: SkillCategory) -> List[Skill]:
        """Obtém skills por categoria."""
        return [s for s in self._skills.values() if s.metadata.category == category]


class SkillComposer:
    """
    Compositor de skills para agentes.
    
    Combina múltiplas skills em um conjunto coeso de instruções.
    """
    
    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or SkillRegistry()
    
    def compose_prompt(self, skill_ids: List[str]) -> str:
        """
        Compõe prompt com múltiplas skills.
        
        Args:
            skill_ids: Lista de IDs de skills
            
        Returns:
            Prompt combinado com instruções de todas as skills
        """
        parts = ["# Capacidades do Agente\n"]
        parts.append("Você possui as seguintes habilidades:\n")
        
        for skill_id in skill_ids:
            skill = self.registry.get(skill_id)
            if skill:
                parts.append(f"\n## {skill.metadata.name}")
                parts.append(skill.get_prompt_injection())
        
        return "\n".join(parts)
    
    def create_skill_agent_instructions(
        self,
        base_role: str,
        skill_ids: List[str]
    ) -> List[str]:
        """
        Cria instruções completas para um agente com skills.
        
        Returns:
            Lista de instruções
        """
        instructions = [base_role]
        
        for skill_id in skill_ids:
            skill = self.registry.get(skill_id)
            if skill:
                injection = skill.get_prompt_injection().strip()
                if injection:
                    instructions.append(injection)
        
        return instructions


# Factory e helpers
_default_registry: Optional[SkillRegistry] = None

def get_skill_registry() -> SkillRegistry:
    """Obtém o registro global de skills."""
    global _default_registry
    if _default_registry is None:
        _default_registry = SkillRegistry()
    return _default_registry


def get_skill(skill_id: str) -> Optional[Skill]:
    """Obtém uma skill do registro global."""
    return get_skill_registry().get(skill_id)


def list_skills(category: Optional[str] = None) -> List[Dict]:
    """Lista skills disponíveis."""
    registry = get_skill_registry()
    
    if category:
        try:
            cat = SkillCategory(category)
            skills = registry.get_by_category(cat)
        except ValueError:
            skills = registry.search(query=category)
    else:
        skills = list(registry._skills.values())
    
    return [s.metadata.to_dict() for s in skills]


def compose_agent_with_skills(
    agent_role: str,
    skills: List[str]
) -> List[str]:
    """
    Cria instruções de agente com skills.
    
    Exemplo:
        instructions = compose_agent_with_skills(
            "Você é um assistente de análise de dados",
            ["summarize", "data_insights", "step_by_step"]
        )
    """
    composer = SkillComposer()
    return composer.create_skill_agent_instructions(agent_role, skills)
