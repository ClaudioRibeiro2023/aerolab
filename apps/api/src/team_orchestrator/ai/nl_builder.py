"""
Agno Team Orchestrator v2.0 - Natural Language Team Builder

Build teams from natural language descriptions.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re
import logging

from ..types import (
    TeamConfiguration, AgentProfile, Task, TaskType,
    OrchestrationMode, PersonalityTraits, Skill
)
from ..profiles import PERSONA_LIBRARY, AgentProfileManager

logger = logging.getLogger(__name__)


@dataclass
class TeamIntent:
    """Parsed intent from natural language."""
    team_name: str
    purpose: str
    size: int
    required_roles: List[str]
    task_descriptions: List[str]
    suggested_mode: OrchestrationMode
    industry: Optional[str] = None
    complexity: str = "medium"


# ============================================================
# NL TEAM BUILDER
# ============================================================

class NLTeamBuilder:
    """
    Creates teams from natural language descriptions.
    
    Examples:
    - "Crie um time para escrever artigos de blog sobre tecnologia"
    - "Preciso de um time de análise financeira com 3 especialistas"
    - "Monte um squad de desenvolvimento para criar uma API REST"
    """
    
    # Role keywords mapping
    ROLE_KEYWORDS = {
        # Research
        "pesquisa": ["senior_researcher", "data_analyst"],
        "research": ["senior_researcher", "data_analyst"],
        "análise": ["data_analyst", "business_analyst"],
        "analysis": ["data_analyst", "business_analyst"],
        "dados": ["data_analyst"],
        "data": ["data_analyst"],
        
        # Content
        "conteúdo": ["content_writer", "copywriter"],
        "content": ["content_writer", "copywriter"],
        "artigo": ["content_writer", "senior_researcher"],
        "article": ["content_writer", "senior_researcher"],
        "blog": ["content_writer", "copywriter"],
        "escrita": ["content_writer", "technical_writer"],
        "writing": ["content_writer", "technical_writer"],
        "redação": ["copywriter", "content_writer"],
        
        # Development
        "desenvolvimento": ["senior_developer", "code_reviewer"],
        "development": ["senior_developer", "code_reviewer"],
        "código": ["senior_developer", "code_reviewer"],
        "code": ["senior_developer", "code_reviewer"],
        "api": ["senior_developer", "architect"],
        "software": ["senior_developer", "architect"],
        "programação": ["senior_developer"],
        
        # Business
        "negócio": ["business_analyst", "product_manager"],
        "business": ["business_analyst", "product_manager"],
        "produto": ["product_manager", "ux_designer"],
        "product": ["product_manager", "ux_designer"],
        "projeto": ["project_manager", "team_leader"],
        "project": ["project_manager", "team_leader"],
        
        # Finance
        "financeiro": ["financial_analyst", "business_analyst"],
        "financial": ["financial_analyst", "business_analyst"],
        "finanças": ["financial_analyst"],
        "finance": ["financial_analyst"],
        
        # Legal
        "jurídico": ["legal_advisor"],
        "legal": ["legal_advisor"],
        "compliance": ["legal_advisor"],
        
        # Design
        "design": ["ux_designer", "creative_director"],
        "ux": ["ux_designer"],
        "ui": ["ux_designer"],
        
        # Marketing
        "marketing": ["marketing_strategist", "copywriter"],
        "growth": ["marketing_strategist"],
    }
    
    # Mode keywords
    MODE_KEYWORDS = {
        OrchestrationMode.SEQUENTIAL: ["sequencial", "sequential", "passo a passo", "step by step"],
        OrchestrationMode.PARALLEL: ["paralelo", "parallel", "simultâneo", "simultaneous"],
        OrchestrationMode.HIERARCHICAL: ["hierárquico", "hierarchical", "supervisor", "líder"],
        OrchestrationMode.DEBATE: ["debate", "discussão", "discussion", "argumentar"],
        OrchestrationMode.CONSENSUS: ["consenso", "consensus", "acordo", "agreement"],
        OrchestrationMode.VOTING: ["votação", "voting", "maioria", "majority"],
        OrchestrationMode.EXPERT_PANEL: ["especialistas", "experts", "painel", "panel"],
        OrchestrationMode.PIPELINE: ["pipeline", "cadeia", "chain", "etapas"],
    }
    
    def __init__(self):
        self.profile_manager = AgentProfileManager()
    
    async def build_team(self, description: str) -> TeamConfiguration:
        """
        Build team from natural language description.
        
        Args:
            description: Natural language description of desired team
            
        Returns:
            TeamConfiguration ready to execute
        """
        logger.info(f"Building team from: {description}")
        
        # 1. Parse intent
        intent = await self._analyze_intent(description)
        
        # 2. Select agents
        agents = await self._select_agents(intent)
        
        # 3. Generate tasks
        tasks = await self._generate_tasks(intent)
        
        # 4. Create configuration
        config = TeamConfiguration(
            name=intent.team_name,
            description=intent.purpose,
            agents=agents,
            tasks=tasks,
            mode=intent.suggested_mode,
            supervisor_id=agents[0].id if intent.suggested_mode == OrchestrationMode.HIERARCHICAL else None,
        )
        
        logger.info(f"Created team '{config.name}' with {len(agents)} agents, mode: {config.mode.value}")
        return config
    
    async def _analyze_intent(self, description: str) -> TeamIntent:
        """Analyze natural language to extract intent."""
        description_lower = description.lower()
        
        # Extract team name
        team_name = self._extract_team_name(description)
        
        # Identify required roles
        required_roles = self._identify_roles(description_lower)
        
        # Determine team size
        size = self._extract_size(description_lower)
        if not size:
            size = max(2, len(required_roles))
        
        # Suggest orchestration mode
        mode = self._suggest_mode(description_lower, required_roles)
        
        # Extract task descriptions
        task_descriptions = self._extract_tasks(description)
        
        # Determine complexity
        complexity = self._assess_complexity(description_lower)
        
        return TeamIntent(
            team_name=team_name,
            purpose=description,
            size=size,
            required_roles=required_roles,
            task_descriptions=task_descriptions,
            suggested_mode=mode,
            complexity=complexity,
        )
    
    async def _select_agents(self, intent: TeamIntent) -> List[AgentProfile]:
        """Select agents based on intent."""
        agents = []
        used_personas = set()
        
        # Add agents for each required role
        for role_key in intent.required_roles[:intent.size]:
            if role_key in PERSONA_LIBRARY and role_key not in used_personas:
                agent = self.profile_manager.from_persona(role_key)
                agents.append(agent)
                used_personas.add(role_key)
        
        # If need more agents, add complementary ones
        while len(agents) < intent.size:
            # Find complementary agent
            for persona_key in PERSONA_LIBRARY:
                if persona_key not in used_personas:
                    agent = self.profile_manager.from_persona(persona_key)
                    agents.append(agent)
                    used_personas.add(persona_key)
                    break
            else:
                break  # No more personas available
        
        # If hierarchical mode, ensure first agent is leadership type
        if intent.suggested_mode == OrchestrationMode.HIERARCHICAL:
            leadership_personas = ["supervisor", "team_leader", "project_manager"]
            has_leader = any(
                any(lp in a.role.lower() for lp in leadership_personas)
                for a in agents
            )
            if not has_leader and agents:
                # Add supervisor at the beginning
                supervisor = self.profile_manager.from_persona("supervisor")
                agents.insert(0, supervisor)
        
        return agents
    
    async def _generate_tasks(self, intent: TeamIntent) -> List[Task]:
        """Generate tasks based on intent."""
        tasks = []
        
        # Generate from explicit task descriptions
        for i, desc in enumerate(intent.task_descriptions):
            task = Task(
                name=f"Task {i + 1}",
                description=desc,
                type=self._infer_task_type(desc),
            )
            tasks.append(task)
        
        # If no explicit tasks, generate based on purpose
        if not tasks:
            tasks = self._generate_default_tasks(intent)
        
        # Set dependencies for sequential/pipeline modes
        if intent.suggested_mode in [OrchestrationMode.SEQUENTIAL, OrchestrationMode.PIPELINE]:
            for i in range(1, len(tasks)):
                tasks[i].dependencies = [tasks[i - 1].id]
        
        return tasks
    
    def _extract_team_name(self, description: str) -> str:
        """Extract or generate team name."""
        # Try to find quoted name
        quoted = re.findall(r'"([^"]+)"', description)
        if quoted:
            return quoted[0]
        
        # Generate from description
        words = description.split()[:4]
        return " ".join(w.capitalize() for w in words if len(w) > 2)[:30] + " Team"
    
    def _identify_roles(self, description: str) -> List[str]:
        """Identify required roles from description."""
        roles = []
        
        for keyword, persona_keys in self.ROLE_KEYWORDS.items():
            if keyword in description:
                for pk in persona_keys:
                    if pk not in roles:
                        roles.append(pk)
        
        # Default to content team if no roles found
        if not roles:
            roles = ["content_writer", "senior_researcher"]
        
        return roles
    
    def _extract_size(self, description: str) -> Optional[int]:
        """Extract team size from description."""
        # Look for numbers
        numbers = re.findall(r'\b(\d+)\s*(agentes?|membros?|pessoas?|especialistas?|agents?|members?)\b', description)
        if numbers:
            return min(10, int(numbers[0][0]))
        
        # Look for word numbers
        word_numbers = {
            "um": 1, "uma": 1, "one": 1,
            "dois": 2, "duas": 2, "two": 2,
            "três": 3, "three": 3,
            "quatro": 4, "four": 4,
            "cinco": 5, "five": 5,
        }
        
        for word, num in word_numbers.items():
            if word in description:
                return num
        
        return None
    
    def _suggest_mode(self, description: str, roles: List[str]) -> OrchestrationMode:
        """Suggest orchestration mode."""
        # Check for explicit mode keywords
        for mode, keywords in self.MODE_KEYWORDS.items():
            if any(kw in description for kw in keywords):
                return mode
        
        # Infer from roles
        if any("supervisor" in r or "leader" in r or "manager" in r for r in roles):
            return OrchestrationMode.HIERARCHICAL
        
        # Default based on task type
        if any(kw in description for kw in ["análise", "analysis", "dados", "data"]):
            return OrchestrationMode.PIPELINE
        
        if any(kw in description for kw in ["opinião", "opinion", "diferentes", "different"]):
            return OrchestrationMode.EXPERT_PANEL
        
        return OrchestrationMode.SEQUENTIAL
    
    def _extract_tasks(self, description: str) -> List[str]:
        """Extract task descriptions."""
        tasks = []
        
        # Look for task indicators
        task_patterns = [
            r'(?:tarefa|task|etapa|step|fase|phase)[\s:]+([^,.;]+)',
            r'(?:preciso|need|quero|want)[\s:]+([^,.;]+)',
        ]
        
        for pattern in task_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            tasks.extend(matches)
        
        return tasks
    
    def _infer_task_type(self, description: str) -> TaskType:
        """Infer task type from description."""
        description_lower = description.lower()
        
        type_keywords = {
            TaskType.RESEARCH: ["pesquisar", "research", "buscar", "find", "investigar"],
            TaskType.ANALYSIS: ["analisar", "analyze", "avaliar", "evaluate"],
            TaskType.CREATION: ["criar", "create", "escrever", "write", "gerar", "generate"],
            TaskType.REVIEW: ["revisar", "review", "verificar", "check"],
            TaskType.CODE: ["código", "code", "programar", "develop"],
            TaskType.DATA: ["dados", "data", "extrair", "extract"],
        }
        
        for task_type, keywords in type_keywords.items():
            if any(kw in description_lower for kw in keywords):
                return task_type
        
        return TaskType.CUSTOM
    
    def _assess_complexity(self, description: str) -> str:
        """Assess task complexity."""
        complex_keywords = ["complexo", "complex", "avançado", "advanced", "difícil", "difficult"]
        simple_keywords = ["simples", "simple", "básico", "basic", "fácil", "easy"]
        
        if any(kw in description for kw in complex_keywords):
            return "high"
        if any(kw in description for kw in simple_keywords):
            return "low"
        
        return "medium"
    
    def _generate_default_tasks(self, intent: TeamIntent) -> List[Task]:
        """Generate default tasks based on intent."""
        tasks = []
        
        # Standard workflow: Research -> Analyze -> Create -> Review
        default_workflow = [
            ("Research", "Research and gather information about the topic", TaskType.RESEARCH),
            ("Analysis", "Analyze gathered information and identify key insights", TaskType.ANALYSIS),
            ("Creation", "Create deliverable based on analysis", TaskType.CREATION),
            ("Review", "Review and refine the output", TaskType.REVIEW),
        ]
        
        for name, desc, task_type in default_workflow[:len(intent.required_roles)]:
            tasks.append(Task(
                name=name,
                description=f"{desc}: {intent.purpose}",
                type=task_type,
            ))
        
        return tasks


# ============================================================
# TEAM TEMPLATES
# ============================================================

TEAM_TEMPLATES = {
    "content_creation": {
        "name": "Content Creation Team",
        "description": "Team for creating high-quality content",
        "agents": ["senior_researcher", "content_writer", "quality_assurer"],
        "mode": OrchestrationMode.PIPELINE,
    },
    "data_analysis": {
        "name": "Data Analysis Team",
        "description": "Team for data analysis and insights",
        "agents": ["data_analyst", "business_analyst", "financial_analyst"],
        "mode": OrchestrationMode.EXPERT_PANEL,
    },
    "software_development": {
        "name": "Software Development Team",
        "description": "Team for software development",
        "agents": ["architect", "senior_developer", "code_reviewer"],
        "mode": OrchestrationMode.HIERARCHICAL,
    },
    "research": {
        "name": "Research Team",
        "description": "Team for comprehensive research",
        "agents": ["senior_researcher", "fact_checker", "data_analyst"],
        "mode": OrchestrationMode.CONSENSUS,
    },
    "marketing": {
        "name": "Marketing Team",
        "description": "Team for marketing strategy and content",
        "agents": ["marketing_strategist", "copywriter", "creative_director"],
        "mode": OrchestrationMode.DEBATE,
    },
    "product": {
        "name": "Product Team",
        "description": "Team for product development",
        "agents": ["product_manager", "ux_designer", "senior_developer"],
        "mode": OrchestrationMode.HIERARCHICAL,
    },
}
