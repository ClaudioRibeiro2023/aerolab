"""
A/B Testing - Testes de diferentes modelos e configurações.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import random
import logging

logger = logging.getLogger(__name__)


@dataclass
class Variant:
    """Variante de um teste."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    
    # Configuração
    model: str = "gpt-4o"
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    
    # Peso (para distribuição)
    weight: float = 0.5
    
    # Métricas
    total_uses: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0
    total_latency_ms: float = 0
    
    @property
    def positive_rate(self) -> float:
        total_feedback = self.positive_feedback + self.negative_feedback
        if total_feedback == 0:
            return 0
        return self.positive_feedback / total_feedback
    
    @property
    def avg_latency_ms(self) -> float:
        if self.total_uses == 0:
            return 0
        return self.total_latency_ms / self.total_uses
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "model": self.model,
            "temperature": self.temperature,
            "weight": self.weight,
            "total_uses": self.total_uses,
            "positive_rate": round(self.positive_rate, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2)
        }


@dataclass
class ABTest:
    """Teste A/B."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Variantes
    variants: List[Variant] = field(default_factory=list)
    
    # Status
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    def select_variant(self, user_id: Optional[str] = None) -> Variant:
        """Seleciona variante baseado em pesos."""
        if not self.variants:
            raise ValueError("No variants configured")
        
        # Se tem user_id, usa hash para consistência
        if user_id:
            hash_val = hash(f"{self.id}:{user_id}") % 100
            cumulative = 0
            total_weight = sum(v.weight for v in self.variants)
            
            for variant in self.variants:
                cumulative += (variant.weight / total_weight) * 100
                if hash_val < cumulative:
                    return variant
        
        # Fallback: seleção aleatória por peso
        total_weight = sum(v.weight for v in self.variants)
        r = random.uniform(0, total_weight)
        cumulative = 0
        
        for variant in self.variants:
            cumulative += variant.weight
            if r <= cumulative:
                return variant
        
        return self.variants[-1]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "variants": [v.to_dict() for v in self.variants],
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }


class ABTester:
    """
    Gerenciador de testes A/B.
    """
    
    def __init__(self):
        self._tests: Dict[str, ABTest] = {}
        self._user_assignments: Dict[str, Dict[str, str]] = {}  # user_id -> {test_id -> variant_id}
    
    async def create_test(
        self,
        name: str,
        variants: List[Dict],
        description: str = ""
    ) -> ABTest:
        """Cria um novo teste."""
        test = ABTest(
            name=name,
            description=description,
            variants=[
                Variant(
                    name=v.get("name", f"Variant {i}"),
                    model=v.get("model", "gpt-4o"),
                    temperature=v.get("temperature", 0.7),
                    system_prompt=v.get("system_prompt"),
                    weight=v.get("weight", 1.0)
                )
                for i, v in enumerate(variants)
            ]
        )
        
        self._tests[test.id] = test
        logger.info(f"Created A/B test: {test.name} with {len(test.variants)} variants")
        
        return test
    
    async def get_variant(
        self,
        test_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Variant]:
        """Obtém variante para um usuário."""
        test = self._tests.get(test_id)
        if not test or not test.is_active:
            return None
        
        # Verificar assignment existente
        if user_id and user_id in self._user_assignments:
            variant_id = self._user_assignments[user_id].get(test_id)
            if variant_id:
                for v in test.variants:
                    if v.id == variant_id:
                        return v
        
        # Selecionar nova variante
        variant = test.select_variant(user_id)
        
        # Salvar assignment
        if user_id:
            if user_id not in self._user_assignments:
                self._user_assignments[user_id] = {}
            self._user_assignments[user_id][test_id] = variant.id
        
        variant.total_uses += 1
        return variant
    
    async def record_result(
        self,
        test_id: str,
        variant_id: str,
        feedback: Optional[str] = None,
        latency_ms: float = 0
    ) -> None:
        """Registra resultado de uma variante."""
        test = self._tests.get(test_id)
        if not test:
            return
        
        for variant in test.variants:
            if variant.id == variant_id:
                if feedback == "good":
                    variant.positive_feedback += 1
                elif feedback == "bad":
                    variant.negative_feedback += 1
                
                if latency_ms > 0:
                    variant.total_latency_ms += latency_ms
                
                break
    
    async def get_results(self, test_id: str) -> Optional[Dict]:
        """Obtém resultados de um teste."""
        test = self._tests.get(test_id)
        if not test:
            return None
        
        # Determinar vencedor
        winner = None
        best_score = -1
        
        for variant in test.variants:
            if variant.total_uses >= 10:  # Mínimo de amostras
                score = variant.positive_rate
                if score > best_score:
                    best_score = score
                    winner = variant
        
        return {
            "test": test.to_dict(),
            "winner": winner.to_dict() if winner else None,
            "statistical_significance": self._calculate_significance(test)
        }
    
    def _calculate_significance(self, test: ABTest) -> float:
        """Calcula significância estatística (simplificado)."""
        if len(test.variants) < 2:
            return 0
        
        # Placeholder: em produção usar teste chi-quadrado ou similar
        min_samples = 100
        total_samples = sum(v.total_uses for v in test.variants)
        
        return min(1.0, total_samples / min_samples)
    
    async def end_test(self, test_id: str) -> Optional[ABTest]:
        """Encerra um teste."""
        test = self._tests.get(test_id)
        if test:
            test.is_active = False
            test.ended_at = datetime.now()
            logger.info(f"Ended A/B test: {test.name}")
        return test
    
    async def list_tests(self, active_only: bool = False) -> List[ABTest]:
        """Lista todos os testes."""
        tests = list(self._tests.values())
        if active_only:
            tests = [t for t in tests if t.is_active]
        return tests


# Singleton
_ab_tester: Optional[ABTester] = None


def get_ab_tester() -> ABTester:
    global _ab_tester
    if _ab_tester is None:
        _ab_tester = ABTester()
    return _ab_tester
