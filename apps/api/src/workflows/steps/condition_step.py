"""
Condition Step - Branching condicional.

Suporta:
- Expressões condicionais
- Múltiplos branches (if/elif/else)
- Switch/case pattern
"""

from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, field
import logging

from .base import BaseStep, StepHandler
from ..core.execution import ExecutionContext
from ..core.registry import WorkflowStep

logger = logging.getLogger(__name__)


@dataclass
class Branch:
    """Define um branch condicional."""
    condition: str  # Expressão a avaliar
    next_step: str  # Step a executar se condição for verdadeira
    label: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "condition": self.condition,
            "next_step": self.next_step,
            "label": self.label
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Branch":
        return cls(
            condition=data["condition"],
            next_step=data["next_step"],
            label=data.get("label")
        )


@dataclass
class ConditionStep(BaseStep):
    """
    Step de branching condicional.
    
    Suporta:
    - if/elif/else: Múltiplos branches com condições
    - switch: Match de valor com cases
    
    Exemplo if/else:
        step = ConditionStep(
            id="route",
            name="Route by sentiment",
            branches=[
                Branch("${sentiment} == 'positive'", "positive_handler"),
                Branch("${sentiment} == 'negative'", "negative_handler"),
            ],
            default_step="neutral_handler"
        )
    
    Exemplo switch:
        step = ConditionStep(
            id="route",
            name="Route by type",
            switch_variable="request_type",
            cases={
                "support": "support_flow",
                "sales": "sales_flow",
                "billing": "billing_flow"
            },
            default_step="general_flow"
        )
    """
    branches: List[Branch] = field(default_factory=list)
    default_step: Optional[str] = None
    
    # Switch mode
    switch_variable: Optional[str] = None
    cases: Dict[str, str] = field(default_factory=dict)
    
    # Output
    output_variable: Optional[str] = None  # Guarda qual branch foi tomado
    
    @property
    def step_type(self) -> str:
        return "condition"
    
    async def execute(self, context: ExecutionContext) -> Any:
        """Avalia condições e retorna próximo step."""
        result = {
            "step_id": self.id,
            "evaluated": [],
            "selected_branch": None,
            "next_step": None
        }
        
        # Switch mode
        if self.switch_variable and self.cases:
            value = context.get_variable(self.switch_variable)
            value_str = str(value).strip() if value else ""
            
            result["switch_value"] = value_str
            
            if value_str in self.cases:
                result["selected_branch"] = value_str
                result["next_step"] = self.cases[value_str]
            elif self.default_step:
                result["selected_branch"] = "_default"
                result["next_step"] = self.default_step
            
            logger.info(f"Condition {self.id}: switch({self.switch_variable}={value_str}) -> {result['next_step']}")
        
        # If/else mode
        else:
            for branch in self.branches:
                is_true = context.evaluate_condition(branch.condition)
                result["evaluated"].append({
                    "condition": branch.condition,
                    "result": is_true
                })
                
                if is_true:
                    result["selected_branch"] = branch.label or branch.condition
                    result["next_step"] = branch.next_step
                    break
            
            # Default se nenhum match
            if not result["next_step"] and self.default_step:
                result["selected_branch"] = "_default"
                result["next_step"] = self.default_step
            
            logger.info(f"Condition {self.id}: {result['selected_branch']} -> {result['next_step']}")
        
        # Salvar resultado
        if self.output_variable:
            context.set_variable(self.output_variable, result)
        
        # Definir próximo step no contexto
        if result["next_step"]:
            context.set_variable("_condition_next", result["next_step"])
        
        return result
    
    def get_config(self) -> Dict[str, Any]:
        config = super().get_config()
        config.update({
            "branches": [b.to_dict() for b in self.branches],
            "default_step": self.default_step,
            "switch_variable": self.switch_variable,
            "cases": self.cases,
            "output_variable": self.output_variable
        })
        return config
    
    def validate(self) -> List[str]:
        errors = super().validate()
        
        # Deve ter branches ou switch
        if not self.branches and not (self.switch_variable and self.cases):
            errors.append("Must have branches or switch_variable+cases")
        
        # Branches devem ter condition e next_step
        for i, branch in enumerate(self.branches):
            if not branch.condition:
                errors.append(f"Branch {i} missing condition")
            if not branch.next_step:
                errors.append(f"Branch {i} missing next_step")
        
        return errors


class ConditionStepHandler(StepHandler):
    """Handler para ConditionStep."""
    
    @property
    def step_type(self) -> str:
        return "condition"
    
    async def execute(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> Any:
        """Executa step de condição."""
        config = step.config
        
        # Parse branches
        branches = []
        for b in config.get("branches", []):
            if isinstance(b, dict):
                branches.append(Branch.from_dict(b))
        
        # Suporte a formato legado (conditions)
        conditions = config.get("conditions", {})
        for value, next_step in conditions.items():
            branches.append(Branch(
                condition=f"${{_last}} == '{value}'",
                next_step=next_step,
                label=value
            ))
        
        # Parse transitions (outro formato legado)
        transitions = config.get("transitions", [])
        for t in transitions:
            if isinstance(t, dict) and t.get("label") and t.get("to"):
                branches.append(Branch(
                    condition=f"${{_last}} == '{t['label']}'",
                    next_step=t["to"],
                    label=t["label"]
                ))
        
        condition_step = ConditionStep(
            id=step.id,
            name=step.name,
            branches=branches,
            default_step=config.get("default_step"),
            switch_variable=config.get("switch_variable"),
            cases=config.get("cases", {}),
            output_variable=config.get("output_variable")
        )
        
        return await condition_step.execute(context)
