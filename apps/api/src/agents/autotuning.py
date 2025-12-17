"""
Sistema de Auto-tuning de Parâmetros para Agentes.

Otimiza automaticamente parâmetros como temperature, top_p,
max_tokens baseado em feedback e métricas de performance.
"""

import os
import json
import random
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import math


@dataclass
class ParameterConfig:
    """Configuração de um parâmetro para tuning."""
    name: str
    min_value: float
    max_value: float
    current_value: float
    step: float = 0.1
    is_integer: bool = False
    
    def get_neighbors(self) -> List[float]:
        """Retorna valores vizinhos para exploração."""
        neighbors = []
        
        # Valor menor
        lower = max(self.min_value, self.current_value - self.step)
        if lower != self.current_value:
            neighbors.append(lower)
        
        # Valor maior
        upper = min(self.max_value, self.current_value + self.step)
        if upper != self.current_value:
            neighbors.append(upper)
        
        if self.is_integer:
            neighbors = [round(v) for v in neighbors]
        
        return neighbors
    
    def random_value(self) -> float:
        """Gera valor aleatório no range."""
        value = random.uniform(self.min_value, self.max_value)
        return round(value) if self.is_integer else value


@dataclass
class TuningResult:
    """Resultado de uma execução de tuning."""
    parameters: Dict[str, float]
    score: float
    metrics: Dict[str, float]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TuningHistory:
    """Histórico de tuning."""
    results: List[TuningResult] = field(default_factory=list)
    best_result: Optional[TuningResult] = None
    iterations: int = 0


class AutoTuner:
    """
    Auto-tuning de parâmetros de agentes.
    
    Features:
    - Otimização bayesiana simplificada
    - Hill climbing
    - Grid search
    - Random search
    - Persistência de histórico
    - Múltiplas métricas de avaliação
    
    Exemplo:
        tuner = AutoTuner(
            parameters={
                "temperature": ParameterConfig("temperature", 0.0, 2.0, 0.7),
                "top_p": ParameterConfig("top_p", 0.0, 1.0, 0.9),
            }
        )
        
        best_params = await tuner.optimize(
            evaluate_fn=my_evaluate_function,
            iterations=20
        )
    """
    
    def __init__(
        self,
        parameters: Dict[str, ParameterConfig],
        storage_path: Optional[str] = None,
        agent_name: Optional[str] = None
    ):
        self.parameters = parameters
        self.agent_name = agent_name or "default"
        self.storage_path = Path(storage_path or os.getenv("TUNING_STORAGE_PATH", "./data/tuning"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.history = self._load_history()
    
    def _history_file(self) -> Path:
        return self.storage_path / f"{self.agent_name}_history.json"
    
    def _load_history(self) -> TuningHistory:
        """Carrega histórico de tuning."""
        file = self._history_file()
        if file.exists():
            data = json.loads(file.read_text())
            return TuningHistory(
                results=[TuningResult(**r) for r in data.get("results", [])],
                best_result=TuningResult(**data["best_result"]) if data.get("best_result") else None,
                iterations=data.get("iterations", 0)
            )
        return TuningHistory()
    
    def _save_history(self):
        """Salva histórico de tuning."""
        data = {
            "results": [asdict(r) for r in self.history.results[-100:]],  # Últimos 100
            "best_result": asdict(self.history.best_result) if self.history.best_result else None,
            "iterations": self.history.iterations
        }
        self._history_file().write_text(json.dumps(data, indent=2))
    
    def get_current_params(self) -> Dict[str, float]:
        """Retorna parâmetros atuais."""
        return {name: p.current_value for name, p in self.parameters.items()}
    
    def set_params(self, params: Dict[str, float]):
        """Define novos valores de parâmetros."""
        for name, value in params.items():
            if name in self.parameters:
                self.parameters[name].current_value = value
    
    async def optimize(
        self,
        evaluate_fn: Callable[[Dict[str, float]], float],
        iterations: int = 20,
        method: str = "hill_climbing",
        early_stop_rounds: int = 5
    ) -> Dict[str, float]:
        """
        Executa otimização de parâmetros.
        
        Args:
            evaluate_fn: Função que avalia parâmetros e retorna score (maior = melhor)
            iterations: Número de iterações
            method: Método de otimização (hill_climbing, random, grid)
            early_stop_rounds: Parar se não melhorar após N rounds
        
        Returns:
            Melhores parâmetros encontrados
        """
        if method == "random":
            return await self._random_search(evaluate_fn, iterations)
        elif method == "grid":
            return await self._grid_search(evaluate_fn)
        else:
            return await self._hill_climbing(evaluate_fn, iterations, early_stop_rounds)
    
    async def _hill_climbing(
        self,
        evaluate_fn: Callable,
        iterations: int,
        early_stop_rounds: int
    ) -> Dict[str, float]:
        """Otimização por hill climbing."""
        current_params = self.get_current_params()
        current_score = await self._evaluate_and_record(evaluate_fn, current_params)
        
        best_params = current_params.copy()
        best_score = current_score
        rounds_without_improvement = 0
        
        for i in range(iterations):
            # Explorar vizinhos
            improved = False
            
            for param_name, param_config in self.parameters.items():
                for neighbor_value in param_config.get_neighbors():
                    test_params = current_params.copy()
                    test_params[param_name] = neighbor_value
                    
                    score = await self._evaluate_and_record(evaluate_fn, test_params)
                    
                    if score > current_score:
                        current_params = test_params.copy()
                        current_score = score
                        improved = True
                        
                        if score > best_score:
                            best_params = test_params.copy()
                            best_score = score
                            rounds_without_improvement = 0
            
            if not improved:
                rounds_without_improvement += 1
                if rounds_without_improvement >= early_stop_rounds:
                    break
                
                # Adicionar perturbação aleatória
                param_name = random.choice(list(self.parameters.keys()))
                current_params[param_name] = self.parameters[param_name].random_value()
        
        # Aplicar melhores parâmetros
        self.set_params(best_params)
        self._save_history()
        
        return best_params
    
    async def _random_search(
        self,
        evaluate_fn: Callable,
        iterations: int
    ) -> Dict[str, float]:
        """Busca aleatória."""
        best_params = self.get_current_params()
        best_score = float("-inf")
        
        for _ in range(iterations):
            test_params = {
                name: config.random_value()
                for name, config in self.parameters.items()
            }
            
            score = await self._evaluate_and_record(evaluate_fn, test_params)
            
            if score > best_score:
                best_params = test_params.copy()
                best_score = score
        
        self.set_params(best_params)
        self._save_history()
        
        return best_params
    
    async def _grid_search(
        self,
        evaluate_fn: Callable,
        grid_points: int = 5
    ) -> Dict[str, float]:
        """Busca em grade."""
        import itertools
        
        # Gerar grid para cada parâmetro
        param_grids = {}
        for name, config in self.parameters.items():
            step = (config.max_value - config.min_value) / (grid_points - 1)
            values = [config.min_value + i * step for i in range(grid_points)]
            if config.is_integer:
                values = list(set(round(v) for v in values))
            param_grids[name] = values
        
        # Gerar todas combinações
        keys = list(param_grids.keys())
        combinations = list(itertools.product(*[param_grids[k] for k in keys]))
        
        best_params = self.get_current_params()
        best_score = float("-inf")
        
        for combo in combinations:
            test_params = dict(zip(keys, combo))
            score = await self._evaluate_and_record(evaluate_fn, test_params)
            
            if score > best_score:
                best_params = test_params.copy()
                best_score = score
        
        self.set_params(best_params)
        self._save_history()
        
        return best_params
    
    async def _evaluate_and_record(
        self,
        evaluate_fn: Callable,
        params: Dict[str, float]
    ) -> float:
        """Avalia parâmetros e registra no histórico."""
        try:
            # Executar função de avaliação
            result = evaluate_fn(params)
            if hasattr(result, "__await__"):
                result = await result
            
            # Extrair score e métricas
            if isinstance(result, dict):
                score = result.get("score", 0.0)
                metrics = result
            else:
                score = float(result)
                metrics = {"score": score}
            
            # Registrar resultado
            tuning_result = TuningResult(
                parameters=params,
                score=score,
                metrics=metrics
            )
            
            self.history.results.append(tuning_result)
            self.history.iterations += 1
            
            # Atualizar melhor resultado
            if self.history.best_result is None or score > self.history.best_result.score:
                self.history.best_result = tuning_result
            
            return score
            
        except Exception as e:
            # Penalizar erros
            return float("-inf")
    
    def get_recommendations(self) -> Dict[str, Any]:
        """
        Retorna recomendações baseadas no histórico.
        """
        if not self.history.results:
            return {"status": "no_data", "recommendations": []}
        
        recommendations = []
        
        # Analisar parâmetros mais impactantes
        for param_name in self.parameters:
            param_scores = [
                (r.parameters.get(param_name, 0), r.score)
                for r in self.history.results
            ]
            
            if len(param_scores) > 5:
                # Calcular correlação simples
                values = [p[0] for p in param_scores]
                scores = [p[1] for p in param_scores]
                
                mean_v = sum(values) / len(values)
                mean_s = sum(scores) / len(scores)
                
                correlation = sum((v - mean_v) * (s - mean_s) for v, s in param_scores)
                
                if abs(correlation) > 0.5:
                    direction = "aumentar" if correlation > 0 else "diminuir"
                    recommendations.append({
                        "parameter": param_name,
                        "suggestion": f"Considere {direction} {param_name}",
                        "correlation": correlation
                    })
        
        return {
            "status": "ok",
            "best_score": self.history.best_result.score if self.history.best_result else None,
            "best_params": self.history.best_result.parameters if self.history.best_result else None,
            "total_iterations": self.history.iterations,
            "recommendations": recommendations
        }


# Parâmetros padrão para LLMs
DEFAULT_LLM_PARAMETERS = {
    "temperature": ParameterConfig("temperature", 0.0, 2.0, 0.7, step=0.1),
    "top_p": ParameterConfig("top_p", 0.0, 1.0, 0.9, step=0.05),
    "top_k": ParameterConfig("top_k", 1, 100, 40, step=10, is_integer=True),
    "max_tokens": ParameterConfig("max_tokens", 100, 4000, 1000, step=200, is_integer=True),
    "frequency_penalty": ParameterConfig("frequency_penalty", 0.0, 2.0, 0.0, step=0.1),
    "presence_penalty": ParameterConfig("presence_penalty", 0.0, 2.0, 0.0, step=0.1),
}


def create_tuner(
    agent_name: str,
    parameters: Optional[Dict[str, ParameterConfig]] = None
) -> AutoTuner:
    """
    Factory para criar AutoTuner.
    
    Args:
        agent_name: Nome do agente
        parameters: Parâmetros customizados (usa defaults se None)
    """
    params = parameters or DEFAULT_LLM_PARAMETERS.copy()
    return AutoTuner(parameters=params, agent_name=agent_name)
