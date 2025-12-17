"""
Sistema de Ensemble de Agentes.

Permite executar múltiplos agentes em paralelo ou sequência
e combinar seus resultados para respostas mais robustas.
"""

import asyncio
from typing import Optional, List, Dict, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class EnsembleStrategy(Enum):
    """Estratégias de combinação de resultados."""
    VOTING = "voting"           # Votação por maioria
    WEIGHTED = "weighted"       # Média ponderada
    BEST_SCORE = "best_score"   # Melhor score
    CONSENSUS = "consensus"     # Consenso (todos concordam)
    CHAIN = "chain"             # Execução em cadeia
    PARALLEL = "parallel"       # Execução paralela, todos os resultados
    FALLBACK = "fallback"       # Tenta próximo se falhar


@dataclass
class AgentResult:
    """Resultado de um agente individual."""
    agent_name: str
    response: str
    confidence: float = 1.0
    duration: float = 0.0
    tokens: int = 0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsembleResult:
    """Resultado do ensemble."""
    final_response: str
    strategy: EnsembleStrategy
    agent_results: List[AgentResult]
    confidence: float
    total_duration: float
    total_tokens: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentEnsemble:
    """
    Orquestra múltiplos agentes para respostas mais robustas.
    
    Features:
    - Múltiplas estratégias de combinação
    - Execução paralela ou sequencial
    - Pesos configuráveis por agente
    - Fallback automático
    - Consenso e votação
    
    Exemplo:
        ensemble = AgentEnsemble(
            agents=[researcher, analyst, writer],
            strategy=EnsembleStrategy.CHAIN
        )
        result = await ensemble.run("Analise o mercado de IA")
    """
    
    def __init__(
        self,
        agents: List[Any],
        strategy: EnsembleStrategy = EnsembleStrategy.PARALLEL,
        weights: Optional[Dict[str, float]] = None,
        timeout: float = 60.0,
        min_confidence: float = 0.5
    ):
        self.agents = agents
        self.strategy = strategy
        self.weights = weights or {}
        self.timeout = timeout
        self.min_confidence = min_confidence
    
    async def run(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EnsembleResult:
        """
        Executa o ensemble com o prompt fornecido.
        
        Args:
            prompt: Prompt para os agentes
            context: Contexto adicional
        
        Returns:
            Resultado combinado do ensemble
        """
        start_time = datetime.utcnow()
        
        if self.strategy == EnsembleStrategy.CHAIN:
            results = await self._run_chain(prompt, context)
        elif self.strategy == EnsembleStrategy.FALLBACK:
            results = await self._run_fallback(prompt, context)
        else:
            results = await self._run_parallel(prompt, context)
        
        # Combinar resultados
        final_response, confidence = self._combine_results(results)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        total_tokens = sum(r.tokens for r in results)
        
        return EnsembleResult(
            final_response=final_response,
            strategy=self.strategy,
            agent_results=results,
            confidence=confidence,
            total_duration=duration,
            total_tokens=total_tokens,
            metadata={"prompt": prompt, "context": context}
        )
    
    async def _run_parallel(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> List[AgentResult]:
        """Executa agentes em paralelo."""
        tasks = [
            self._execute_agent(agent, prompt, context)
            for agent in self.agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Converter exceções em resultados de erro
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed.append(AgentResult(
                    agent_name=getattr(self.agents[i], "name", f"agent_{i}"),
                    response="",
                    success=False,
                    error=str(result)
                ))
            else:
                processed.append(result)
        
        return processed
    
    async def _run_chain(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> List[AgentResult]:
        """Executa agentes em cadeia, passando resultado anterior."""
        results = []
        current_prompt = prompt
        accumulated_context = context or {}
        
        for agent in self.agents:
            result = await self._execute_agent(agent, current_prompt, accumulated_context)
            results.append(result)
            
            if not result.success:
                break
            
            # Passar resultado para próximo agente
            accumulated_context["previous_response"] = result.response
            accumulated_context["previous_agent"] = result.agent_name
            
            # Modificar prompt para incluir contexto
            current_prompt = f"""
Contexto do agente anterior ({result.agent_name}):
{result.response}

Prompt original: {prompt}

Continue a partir desta análise.
"""
        
        return results
    
    async def _run_fallback(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> List[AgentResult]:
        """Executa agentes em sequência até um sucesso."""
        results = []
        
        for agent in self.agents:
            result = await self._execute_agent(agent, prompt, context)
            results.append(result)
            
            if result.success and result.confidence >= self.min_confidence:
                break
        
        return results
    
    async def _execute_agent(
        self,
        agent: Any,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> AgentResult:
        """Executa um agente individual."""
        start = datetime.utcnow()
        agent_name = getattr(agent, "name", str(agent))
        
        try:
            # Tentar diferentes interfaces de agente
            if hasattr(agent, "arun"):
                response = await agent.arun(prompt)
            elif hasattr(agent, "run"):
                response = agent.run(prompt)
            elif hasattr(agent, "__call__"):
                response = agent(prompt)
            else:
                raise ValueError(f"Agent {agent_name} não tem método de execução")
            
            # Extrair resposta se for objeto
            if hasattr(response, "content"):
                response_text = response.content
            elif isinstance(response, dict):
                response_text = response.get("response", str(response))
            else:
                response_text = str(response)
            
            duration = (datetime.utcnow() - start).total_seconds()
            
            return AgentResult(
                agent_name=agent_name,
                response=response_text,
                confidence=self._estimate_confidence(response_text),
                duration=duration,
                tokens=len(response_text.split()) * 2,  # Estimativa
                success=True
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start).total_seconds()
            return AgentResult(
                agent_name=agent_name,
                response="",
                confidence=0.0,
                duration=duration,
                success=False,
                error=str(e)
            )
    
    def _combine_results(
        self,
        results: List[AgentResult]
    ) -> tuple[str, float]:
        """Combina resultados baseado na estratégia."""
        successful = [r for r in results if r.success]
        
        if not successful:
            return "Nenhum agente conseguiu processar a requisição.", 0.0
        
        if self.strategy == EnsembleStrategy.VOTING:
            return self._voting_combine(successful)
        elif self.strategy == EnsembleStrategy.WEIGHTED:
            return self._weighted_combine(successful)
        elif self.strategy == EnsembleStrategy.BEST_SCORE:
            return self._best_score_combine(successful)
        elif self.strategy == EnsembleStrategy.CONSENSUS:
            return self._consensus_combine(successful)
        elif self.strategy == EnsembleStrategy.CHAIN:
            # Retorna último resultado da cadeia
            return successful[-1].response, successful[-1].confidence
        elif self.strategy == EnsembleStrategy.FALLBACK:
            # Retorna primeiro sucesso
            return successful[0].response, successful[0].confidence
        else:
            # PARALLEL - retorna todos concatenados
            combined = "\n\n---\n\n".join([
                f"**{r.agent_name}:**\n{r.response}"
                for r in successful
            ])
            avg_confidence = sum(r.confidence for r in successful) / len(successful)
            return combined, avg_confidence
    
    def _voting_combine(self, results: List[AgentResult]) -> tuple[str, float]:
        """Votação por similaridade de respostas."""
        # Simplificado: retorna resposta mais comum ou mais longa
        responses = [r.response for r in results]
        
        # Se houver respostas iguais, usar essa
        from collections import Counter
        counts = Counter(responses)
        most_common = counts.most_common(1)[0]
        
        if most_common[1] > 1:
            confidence = most_common[1] / len(results)
            return most_common[0], confidence
        
        # Senão, usar a mais longa (geralmente mais completa)
        longest = max(results, key=lambda r: len(r.response))
        return longest.response, longest.confidence
    
    def _weighted_combine(self, results: List[AgentResult]) -> tuple[str, float]:
        """Combinação ponderada por pesos."""
        # Usar resposta do agente com maior peso
        weighted = []
        for r in results:
            weight = self.weights.get(r.agent_name, 1.0)
            weighted.append((r, weight * r.confidence))
        
        best = max(weighted, key=lambda x: x[1])
        return best[0].response, best[0].confidence
    
    def _best_score_combine(self, results: List[AgentResult]) -> tuple[str, float]:
        """Retorna resultado com maior confidence."""
        best = max(results, key=lambda r: r.confidence)
        return best.response, best.confidence
    
    def _consensus_combine(self, results: List[AgentResult]) -> tuple[str, float]:
        """Verifica consenso entre agentes."""
        if len(results) < 2:
            return results[0].response, results[0].confidence
        
        # Verificar se respostas são similares
        responses = [r.response.lower().strip() for r in results]
        
        # Consenso simplificado: verificar palavras-chave comuns
        word_sets = [set(r.split()) for r in responses]
        common = word_sets[0]
        for ws in word_sets[1:]:
            common = common.intersection(ws)
        
        similarity = len(common) / max(len(ws) for ws in word_sets)
        
        if similarity > 0.5:
            # Há consenso
            return results[0].response, min(1.0, similarity + 0.3)
        else:
            # Sem consenso, indicar divergência
            return (
                "Os agentes apresentaram perspectivas divergentes:\n\n" +
                "\n\n".join([f"**{r.agent_name}:** {r.response[:200]}..." for r in results]),
                similarity
            )
    
    def _estimate_confidence(self, response: str) -> float:
        """Estima confiança baseado na resposta."""
        if not response:
            return 0.0
        
        # Heurísticas simples
        confidence = 0.7  # Base
        
        # Respostas mais longas geralmente são mais completas
        if len(response) > 500:
            confidence += 0.1
        if len(response) > 1000:
            confidence += 0.1
        
        # Penalizar incerteza
        uncertain_phrases = ["não tenho certeza", "talvez", "possivelmente", "não sei"]
        for phrase in uncertain_phrases:
            if phrase in response.lower():
                confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))


def create_ensemble(
    agents: List[Any],
    strategy: str = "parallel",
    **kwargs
) -> AgentEnsemble:
    """
    Factory para criar ensemble.
    
    Args:
        agents: Lista de agentes
        strategy: Nome da estratégia
        **kwargs: Argumentos adicionais
    """
    strategy_map = {
        "voting": EnsembleStrategy.VOTING,
        "weighted": EnsembleStrategy.WEIGHTED,
        "best_score": EnsembleStrategy.BEST_SCORE,
        "consensus": EnsembleStrategy.CONSENSUS,
        "chain": EnsembleStrategy.CHAIN,
        "parallel": EnsembleStrategy.PARALLEL,
        "fallback": EnsembleStrategy.FALLBACK,
    }
    
    return AgentEnsemble(
        agents=agents,
        strategy=strategy_map.get(strategy, EnsembleStrategy.PARALLEL),
        **kwargs
    )
