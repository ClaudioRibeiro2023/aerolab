"""
Agent Routing - Roteamento inteligente para agentes.

Determina qual agente deve responder baseado em:
- Intent do usuário
- Contexto da conversa
- Capacidades dos agentes
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Estratégias de roteamento."""
    INTENT = "intent"           # Por intenção detectada
    KEYWORD = "keyword"         # Por palavras-chave
    ROUND_ROBIN = "round_robin" # Alternado
    LOAD_BALANCE = "load_balance"  # Por carga
    SKILL_MATCH = "skill_match"    # Por habilidades
    LLM_ROUTER = "llm_router"      # LLM decide


@dataclass
class AgentProfile:
    """Perfil de um agente para roteamento."""
    id: str
    name: str
    description: str = ""
    skills: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    intents: List[str] = field(default_factory=list)
    priority: int = 0
    is_available: bool = True
    current_load: int = 0
    max_concurrent: int = 10
    
    def matches_intent(self, intent: str) -> bool:
        return intent.lower() in [i.lower() for i in self.intents]
    
    def matches_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.keywords)


@dataclass
class RoutingDecision:
    """Decisão de roteamento."""
    agent_id: str
    confidence: float = 1.0
    reason: str = ""
    alternative_agents: List[str] = field(default_factory=list)


class AgentRouter:
    """
    Roteador de agentes.
    
    Determina qual agente deve responder a uma mensagem.
    """
    
    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.INTENT):
        self.strategy = strategy
        self._agents: Dict[str, AgentProfile] = {}
        self._default_agent_id: Optional[str] = None
        self._round_robin_index = 0
    
    def register_agent(self, profile: AgentProfile) -> None:
        """Registra um agente."""
        self._agents[profile.id] = profile
        if not self._default_agent_id:
            self._default_agent_id = profile.id
    
    def set_default_agent(self, agent_id: str) -> None:
        """Define o agente padrão."""
        self._default_agent_id = agent_id
    
    async def route(
        self,
        message: str,
        context: Optional[Dict] = None,
        current_agent_id: Optional[str] = None
    ) -> RoutingDecision:
        """
        Roteia uma mensagem para o agente apropriado.
        
        Args:
            message: Mensagem do usuário
            context: Contexto da conversa
            current_agent_id: Agente atual (se houver)
            
        Returns:
            RoutingDecision com o agente escolhido
        """
        available_agents = [
            a for a in self._agents.values()
            if a.is_available and a.current_load < a.max_concurrent
        ]
        
        if not available_agents:
            return RoutingDecision(
                agent_id=self._default_agent_id or "",
                confidence=0.5,
                reason="No available agents, using default"
            )
        
        if self.strategy == RoutingStrategy.KEYWORD:
            return await self._route_by_keyword(message, available_agents)
        
        elif self.strategy == RoutingStrategy.ROUND_ROBIN:
            return await self._route_round_robin(available_agents)
        
        elif self.strategy == RoutingStrategy.LOAD_BALANCE:
            return await self._route_by_load(available_agents)
        
        elif self.strategy == RoutingStrategy.SKILL_MATCH:
            return await self._route_by_skills(message, available_agents)
        
        elif self.strategy == RoutingStrategy.LLM_ROUTER:
            return await self._route_by_llm(message, available_agents, context)
        
        else:  # INTENT
            return await self._route_by_intent(message, available_agents)
    
    async def _route_by_keyword(
        self,
        message: str,
        agents: List[AgentProfile]
    ) -> RoutingDecision:
        """Roteia por palavras-chave."""
        for agent in sorted(agents, key=lambda a: a.priority, reverse=True):
            if agent.matches_keywords(message):
                return RoutingDecision(
                    agent_id=agent.id,
                    confidence=0.8,
                    reason=f"Matched keywords for {agent.name}"
                )
        
        return RoutingDecision(
            agent_id=self._default_agent_id or agents[0].id,
            confidence=0.5,
            reason="No keyword match, using default"
        )
    
    async def _route_round_robin(
        self,
        agents: List[AgentProfile]
    ) -> RoutingDecision:
        """Roteia em round-robin."""
        agent = agents[self._round_robin_index % len(agents)]
        self._round_robin_index += 1
        
        return RoutingDecision(
            agent_id=agent.id,
            confidence=1.0,
            reason="Round-robin selection"
        )
    
    async def _route_by_load(
        self,
        agents: List[AgentProfile]
    ) -> RoutingDecision:
        """Roteia pelo agente com menor carga."""
        agent = min(agents, key=lambda a: a.current_load)
        
        return RoutingDecision(
            agent_id=agent.id,
            confidence=0.9,
            reason=f"Lowest load ({agent.current_load})"
        )
    
    async def _route_by_skills(
        self,
        message: str,
        agents: List[AgentProfile]
    ) -> RoutingDecision:
        """Roteia por match de skills."""
        # Simplificado: verificar skills nas palavras da mensagem
        message_words = set(message.lower().split())
        
        best_match = None
        best_score = 0
        
        for agent in agents:
            skill_words = set(' '.join(agent.skills).lower().split())
            match_score = len(message_words & skill_words)
            
            if match_score > best_score:
                best_score = match_score
                best_match = agent
        
        if best_match:
            return RoutingDecision(
                agent_id=best_match.id,
                confidence=min(0.5 + best_score * 0.1, 0.95),
                reason=f"Skill match score: {best_score}"
            )
        
        return RoutingDecision(
            agent_id=self._default_agent_id or agents[0].id,
            confidence=0.5,
            reason="No skill match, using default"
        )
    
    async def _route_by_intent(
        self,
        message: str,
        agents: List[AgentProfile]
    ) -> RoutingDecision:
        """Roteia por intenção detectada."""
        # Em produção: usar classificador de intenção
        intent = await self._detect_intent(message)
        
        for agent in agents:
            if agent.matches_intent(intent):
                return RoutingDecision(
                    agent_id=agent.id,
                    confidence=0.85,
                    reason=f"Intent match: {intent}"
                )
        
        return RoutingDecision(
            agent_id=self._default_agent_id or agents[0].id,
            confidence=0.5,
            reason=f"No intent match for: {intent}"
        )
    
    async def _route_by_llm(
        self,
        message: str,
        agents: List[AgentProfile],
        context: Optional[Dict]
    ) -> RoutingDecision:
        """Roteia usando LLM para decidir."""
        # Em produção: chamar LLM com descrições dos agentes
        # Por agora, usa keyword como fallback
        return await self._route_by_keyword(message, agents)
    
    async def _detect_intent(self, message: str) -> str:
        """Detecta intenção de uma mensagem."""
        # Simplificado: heurísticas
        message_lower = message.lower()
        
        if any(w in message_lower for w in ['code', 'program', 'debug', 'develop']):
            return 'coding'
        if any(w in message_lower for w in ['write', 'draft', 'article', 'blog']):
            return 'writing'
        if any(w in message_lower for w in ['analyze', 'data', 'report', 'chart']):
            return 'analysis'
        if any(w in message_lower for w in ['search', 'find', 'look up']):
            return 'search'
        if any(w in message_lower for w in ['help', 'support', 'issue', 'problem']):
            return 'support'
        
        return 'general'


# Singleton
_agent_router: Optional[AgentRouter] = None


def get_agent_router() -> AgentRouter:
    global _agent_router
    if _agent_router is None:
        _agent_router = AgentRouter()
    return _agent_router
