"""
AI Workflow Assistant.

Assistente inteligente para:
- Gerar workflows a partir de descrição
- Sugerir próximos steps
- Detectar problemas
- Documentar automaticamente
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass
class StepSuggestion:
    """Sugestão de step."""
    step_type: str
    name: str
    description: str
    config: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8
    reason: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "step_type": self.step_type,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "confidence": self.confidence,
            "reason": self.reason
        }


@dataclass
class WorkflowSuggestion:
    """Sugestão de workflow completo."""
    name: str
    description: str
    steps: List[Dict[str, Any]]
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "triggers": self.triggers,
            "metadata": self.metadata
        }


@dataclass
class ProblemDetection:
    """Problema detectado no workflow."""
    severity: str  # error, warning, info
    message: str
    step_id: Optional[str] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "severity": self.severity,
            "message": self.message,
            "step_id": self.step_id,
            "suggestion": self.suggestion
        }


class WorkflowAssistant:
    """
    Assistente AI para construção de workflows.
    
    Exemplo:
        assistant = WorkflowAssistant()
        
        # Gerar workflow de descrição
        workflow = assistant.generate_from_description(
            "Quando receber email, analisar sentimento e responder"
        )
        
        # Sugerir próximos steps
        suggestions = assistant.suggest_next_steps(current_workflow)
        
        # Detectar problemas
        problems = assistant.detect_problems(workflow)
    """
    
    # Templates de workflows comuns
    WORKFLOW_TEMPLATES = {
        "email_handler": {
            "keywords": ["email", "mensagem", "inbox", "mail"],
            "template": {
                "name": "Email Handler",
                "steps": [
                    {"id": "receive", "type": "trigger", "name": "Receive Email"},
                    {"id": "analyze", "type": "agent", "name": "Analyze Content"},
                    {"id": "respond", "type": "agent", "name": "Generate Response"},
                    {"id": "send", "type": "action", "name": "Send Reply"}
                ]
            }
        },
        "data_pipeline": {
            "keywords": ["data", "etl", "extract", "transform", "load", "pipeline"],
            "template": {
                "name": "Data Pipeline",
                "steps": [
                    {"id": "extract", "type": "action", "name": "Extract Data"},
                    {"id": "validate", "type": "condition", "name": "Validate Data"},
                    {"id": "transform", "type": "agent", "name": "Transform Data"},
                    {"id": "load", "type": "action", "name": "Load to Destination"}
                ]
            }
        },
        "content_creation": {
            "keywords": ["content", "escrever", "write", "artigo", "blog", "post"],
            "template": {
                "name": "Content Creation",
                "steps": [
                    {"id": "research", "type": "agent", "name": "Research Topic"},
                    {"id": "outline", "type": "agent", "name": "Create Outline"},
                    {"id": "write", "type": "agent", "name": "Write Content"},
                    {"id": "review", "type": "agent", "name": "Review & Edit"}
                ]
            }
        },
        "customer_support": {
            "keywords": ["support", "suporte", "ticket", "help", "customer", "cliente"],
            "template": {
                "name": "Customer Support",
                "steps": [
                    {"id": "classify", "type": "agent", "name": "Classify Request"},
                    {"id": "route", "type": "condition", "name": "Route by Type"},
                    {"id": "resolve", "type": "agent", "name": "Generate Solution"},
                    {"id": "escalate", "type": "condition", "name": "Check Escalation"}
                ]
            }
        },
        "approval_flow": {
            "keywords": ["approval", "aprovação", "review", "validar", "autorizar"],
            "template": {
                "name": "Approval Flow",
                "steps": [
                    {"id": "submit", "type": "action", "name": "Submit Request"},
                    {"id": "validate", "type": "agent", "name": "Validate Request"},
                    {"id": "approve", "type": "condition", "name": "Approval Decision"},
                    {"id": "notify", "type": "action", "name": "Notify Requester"}
                ]
            }
        }
    }
    
    # Step types e quando usá-los
    STEP_PATTERNS = {
        "agent": {
            "keywords": ["analisar", "analyze", "escrever", "write", "gerar", "generate", 
                        "resumir", "summarize", "traduzir", "translate", "classificar"],
            "description": "Executa um agente LLM para processar texto"
        },
        "condition": {
            "keywords": ["se", "if", "quando", "when", "verificar", "check", "decidir",
                        "decision", "routing", "encaminhar"],
            "description": "Branching condicional baseado em regras"
        },
        "parallel": {
            "keywords": ["paralelo", "parallel", "simultâneo", "simultaneous", "todos",
                        "all", "multiple"],
            "description": "Executa múltiplos steps em paralelo"
        },
        "loop": {
            "keywords": ["cada", "each", "para", "for", "repetir", "repeat", "iterar",
                        "iterate", "while"],
            "description": "Itera sobre uma lista de items"
        },
        "multi_agent": {
            "keywords": ["equipe", "team", "crew", "debate", "colaborar", "collaborate",
                        "múltiplos agentes", "multiple agents"],
            "description": "Orquestra múltiplos agentes trabalhando juntos"
        },
        "action": {
            "keywords": ["enviar", "send", "salvar", "save", "http", "api", "webhook",
                        "notificar", "notify", "email"],
            "description": "Executa uma ação externa (HTTP, DB, etc)"
        }
    }
    
    def __init__(self):
        self._history: List[Dict] = []
    
    def generate_from_description(
        self,
        description: str,
        available_agents: Optional[List[str]] = None
    ) -> WorkflowSuggestion:
        """
        Gera workflow a partir de descrição em linguagem natural.
        
        Args:
            description: Descrição do que o workflow deve fazer
            available_agents: Lista de agentes disponíveis
        """
        description_lower = description.lower()
        
        # Tentar match com templates
        best_template = None
        best_score = 0
        
        for template_name, template_data in self.WORKFLOW_TEMPLATES.items():
            score = sum(
                1 for keyword in template_data["keywords"]
                if keyword in description_lower
            )
            if score > best_score:
                best_score = score
                best_template = template_data["template"]
        
        if best_template and best_score >= 2:
            # Usar template como base
            steps = []
            for i, step in enumerate(best_template["steps"]):
                steps.append({
                    "id": step["id"],
                    "type": step["type"],
                    "name": step["name"],
                    "config": self._generate_step_config(step["type"], description)
                })
            
            return WorkflowSuggestion(
                name=best_template["name"],
                description=description,
                steps=steps,
                metadata={"source": "template", "template_match_score": best_score}
            )
        
        # Gerar workflow genérico baseado em análise
        steps = self._analyze_and_generate_steps(description)
        
        return WorkflowSuggestion(
            name=self._generate_workflow_name(description),
            description=description,
            steps=steps,
            metadata={"source": "generated"}
        )
    
    def suggest_next_steps(
        self,
        current_steps: List[Dict],
        context: Optional[str] = None
    ) -> List[StepSuggestion]:
        """
        Sugere próximos steps baseado no workflow atual.
        """
        suggestions = []
        
        if not current_steps:
            # Sugerir step inicial
            suggestions.append(StepSuggestion(
                step_type="agent",
                name="Process Input",
                description="Processar entrada inicial",
                confidence=0.9,
                reason="Todo workflow precisa de um step inicial para processar entrada"
            ))
            return suggestions
        
        last_step = current_steps[-1]
        last_type = last_step.get("type", "agent")
        
        # Sugestões baseadas no último step
        if last_type == "agent":
            suggestions.extend([
                StepSuggestion(
                    step_type="condition",
                    name="Validate Result",
                    description="Validar resultado do agente",
                    confidence=0.8,
                    reason="Comum verificar resultado de agente antes de prosseguir"
                ),
                StepSuggestion(
                    step_type="action",
                    name="Save Result",
                    description="Salvar resultado em sistema externo",
                    confidence=0.7,
                    reason="Resultados de agentes frequentemente precisam ser persistidos"
                )
            ])
        
        elif last_type == "condition":
            suggestions.extend([
                StepSuggestion(
                    step_type="agent",
                    name="Process Branch",
                    description="Processar branch selecionado",
                    confidence=0.85,
                    reason="Branches de condição geralmente levam a processamento específico"
                )
            ])
        
        elif last_type == "parallel":
            suggestions.extend([
                StepSuggestion(
                    step_type="agent",
                    name="Aggregate Results",
                    description="Combinar resultados paralelos",
                    confidence=0.9,
                    reason="Resultados paralelos precisam ser agregados"
                )
            ])
        
        # Sugestão de finalização
        if len(current_steps) >= 3:
            suggestions.append(StepSuggestion(
                step_type="action",
                name="Complete Workflow",
                description="Finalizar e notificar conclusão",
                confidence=0.6,
                reason="Workflow pode estar pronto para finalização"
            ))
        
        return suggestions
    
    def detect_problems(self, workflow: Dict) -> List[ProblemDetection]:
        """
        Detecta problemas no workflow.
        """
        problems = []
        steps = workflow.get("steps", [])
        
        if not steps:
            problems.append(ProblemDetection(
                severity="error",
                message="Workflow não tem steps definidos"
            ))
            return problems
        
        # Verificar step IDs únicos
        ids = [s.get("id") for s in steps]
        if len(ids) != len(set(ids)):
            problems.append(ProblemDetection(
                severity="error",
                message="IDs de steps duplicados encontrados"
            ))
        
        # Verificar steps órfãos
        step_ids = set(ids)
        for step in steps:
            next_step = step.get("next_step")
            if next_step and next_step not in step_ids:
                problems.append(ProblemDetection(
                    severity="error",
                    message=f"Step referencia next_step inexistente: {next_step}",
                    step_id=step.get("id"),
                    suggestion=f"Remover referência ou criar step '{next_step}'"
                ))
        
        # Verificar configurações
        for step in steps:
            step_type = step.get("type", "")
            config = step.get("config", {})
            
            if step_type == "agent" and not config.get("prompt") and not config.get("agent_id"):
                problems.append(ProblemDetection(
                    severity="warning",
                    message="Agent step sem prompt ou agent_id configurado",
                    step_id=step.get("id"),
                    suggestion="Adicionar prompt ou especificar agent_id"
                ))
            
            if step_type == "condition" and not config.get("branches") and not config.get("cases"):
                problems.append(ProblemDetection(
                    severity="warning",
                    message="Condition step sem branches definidos",
                    step_id=step.get("id"),
                    suggestion="Adicionar branches ou cases para a condição"
                ))
        
        # Verificar loops infinitos potenciais
        for step in steps:
            if step.get("next_step") == step.get("id"):
                problems.append(ProblemDetection(
                    severity="error",
                    message="Step aponta para si mesmo (loop infinito)",
                    step_id=step.get("id"),
                    suggestion="Corrigir next_step para apontar para outro step"
                ))
        
        return problems
    
    def generate_documentation(self, workflow: Dict) -> str:
        """
        Gera documentação automática do workflow.
        """
        lines = []
        
        name = workflow.get("name", "Workflow")
        description = workflow.get("description", "")
        
        lines.append(f"# {name}\n")
        
        if description:
            lines.append(f"{description}\n")
        
        lines.append("## Steps\n")
        
        for i, step in enumerate(workflow.get("steps", []), 1):
            step_id = step.get("id", f"step_{i}")
            step_type = step.get("type", "unknown")
            step_name = step.get("name", step_id)
            
            lines.append(f"### {i}. {step_name}")
            lines.append(f"- **ID**: `{step_id}`")
            lines.append(f"- **Type**: `{step_type}`")
            
            config = step.get("config", {})
            if config:
                lines.append("- **Config**:")
                for key, value in config.items():
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    lines.append(f"  - {key}: {value}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_workflow_name(self, description: str) -> str:
        """Gera nome do workflow a partir da descrição."""
        words = description.split()[:4]
        return " ".join(word.capitalize() for word in words)
    
    def _analyze_and_generate_steps(self, description: str) -> List[Dict]:
        """Analisa descrição e gera steps."""
        steps = []
        description_lower = description.lower()
        
        # Identificar steps pela descrição
        step_index = 0
        
        for step_type, patterns in self.STEP_PATTERNS.items():
            for keyword in patterns["keywords"]:
                if keyword in description_lower:
                    step_index += 1
                    steps.append({
                        "id": f"step_{step_index}",
                        "type": step_type,
                        "name": f"{keyword.capitalize()} Step",
                        "config": self._generate_step_config(step_type, description)
                    })
                    break
        
        # Se não encontrou nada, criar workflow genérico
        if not steps:
            steps = [
                {"id": "input", "type": "agent", "name": "Process Input", "config": {}},
                {"id": "process", "type": "agent", "name": "Main Process", "config": {}},
                {"id": "output", "type": "action", "name": "Generate Output", "config": {}}
            ]
        
        return steps
    
    def _generate_step_config(self, step_type: str, context: str) -> Dict:
        """Gera configuração básica para um tipo de step."""
        if step_type == "agent":
            return {
                "prompt": f"Process the following based on: {context[:100]}...",
                "output_variable": "result"
            }
        elif step_type == "condition":
            return {
                "branches": [
                    {"condition": "${result.success} == true", "next_step": "success"},
                    {"condition": "${result.success} == false", "next_step": "failure"}
                ]
            }
        elif step_type == "parallel":
            return {
                "join_strategy": "all",
                "branches": []
            }
        elif step_type == "loop":
            return {
                "loop_type": "for_each",
                "items_variable": "items",
                "item_variable": "item"
            }
        return {}


# Singleton
_assistant: Optional[WorkflowAssistant] = None


def get_assistant() -> WorkflowAssistant:
    """Obtém assistant global."""
    global _assistant
    if _assistant is None:
        _assistant = WorkflowAssistant()
    return _assistant


def create_assistant() -> WorkflowAssistant:
    """Cria novo assistant."""
    return WorkflowAssistant()
