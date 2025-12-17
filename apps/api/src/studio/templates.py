"""
Agent Studio - Template Library

Biblioteca de templates de workflows pré-construídos.
"""

from dataclasses import dataclass, field
from typing import Optional
import json

from .types import Workflow, Node, Connection, WorkflowState
from .nodes import (
    InputNode, OutputNode, AgentNode, ToolNode,
    ConditionNode, MemoryReadNode, RAGSearchNode
)


@dataclass
class WorkflowTemplate:
    """Template de workflow."""
    id: str
    name: str
    description: str
    category: str
    
    # Workflow base
    workflow: Workflow
    
    # Metadados
    tags: list[str] = field(default_factory=list)
    author: str = "Agno Team"
    version: str = "1.0.0"
    
    # Preview
    preview_image: Optional[str] = None
    
    @property
    def nodes(self) -> list[Node]:
        return self.workflow.nodes
    
    @property
    def connections(self) -> list[Connection]:
        return self.workflow.connections
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "workflow": self.workflow.to_dict(),
            "tags": self.tags,
            "author": self.author,
            "version": self.version
        }


class TemplateLibrary:
    """
    Biblioteca de templates de workflows.
    
    Fornece templates pré-construídos para casos de uso comuns.
    """
    
    def __init__(self):
        self._templates: dict[str, WorkflowTemplate] = {}
        self._load_builtin_templates()
    
    def _load_builtin_templates(self) -> None:
        """Carrega templates built-in."""
        # 1. Customer Support
        self._templates["customer_support"] = self._create_customer_support_template()
        
        # 2. RAG Q&A
        self._templates["rag_qa"] = self._create_rag_qa_template()
        
        # 3. Content Generator
        self._templates["content_generator"] = self._create_content_generator_template()
        
        # 4. Research Assistant
        self._templates["research_assistant"] = self._create_research_assistant_template()
        
        # 5. Data Processor
        self._templates["data_processor"] = self._create_data_processor_template()
        
        # 6. Multi-Agent Debate
        self._templates["debate"] = self._create_debate_template()
    
    def _create_customer_support_template(self) -> WorkflowTemplate:
        """Template de suporte ao cliente."""
        workflow = Workflow(
            name="Customer Support",
            description="AI-powered customer support with classification and routing"
        )
        
        # Nodes
        input_node = InputNode(name="Customer Message")
        input_node.position.x = 50
        input_node.position.y = 200
        
        classifier = AgentNode(
            name="Intent Classifier",
            model="gpt-4o-mini",
            instructions="Classify the customer message into: billing, technical, general, complaint"
        )
        classifier.position.x = 300
        classifier.position.y = 200
        
        condition = ConditionNode(
            name="Route by Intent",
            condition="'billing' in value.lower()"
        )
        condition.position.x = 550
        condition.position.y = 200
        
        billing_agent = AgentNode(
            name="Billing Support",
            model="gpt-4o",
            instructions="You are a billing support specialist. Help customers with billing issues."
        )
        billing_agent.position.x = 800
        billing_agent.position.y = 100
        
        general_agent = AgentNode(
            name="General Support",
            model="gpt-4o",
            instructions="You are a general support agent. Help customers with their questions."
        )
        general_agent.position.x = 800
        general_agent.position.y = 300
        
        output_node = OutputNode(name="Response")
        output_node.position.x = 1050
        output_node.position.y = 200
        
        # Add to workflow
        for node in [input_node, classifier, condition, billing_agent, general_agent, output_node]:
            workflow.add_node(node)
        
        # Connections
        workflow.add_connection(Connection(
            source_node_id=input_node.id,
            source_port_id=input_node.outputs[0].id,
            target_node_id=classifier.id,
            target_port_id=classifier.inputs[0].id
        ))
        workflow.add_connection(Connection(
            source_node_id=classifier.id,
            source_port_id=classifier.outputs[0].id,
            target_node_id=condition.id,
            target_port_id=condition.inputs[0].id
        ))
        workflow.add_connection(Connection(
            source_node_id=condition.id,
            source_port_id=condition.outputs[0].id,  # true
            target_node_id=billing_agent.id,
            target_port_id=billing_agent.inputs[0].id
        ))
        workflow.add_connection(Connection(
            source_node_id=condition.id,
            source_port_id=condition.outputs[1].id,  # false
            target_node_id=general_agent.id,
            target_port_id=general_agent.inputs[0].id
        ))
        workflow.add_connection(Connection(
            source_node_id=billing_agent.id,
            source_port_id=billing_agent.outputs[0].id,
            target_node_id=output_node.id,
            target_port_id=output_node.inputs[0].id
        ))
        workflow.add_connection(Connection(
            source_node_id=general_agent.id,
            source_port_id=general_agent.outputs[0].id,
            target_node_id=output_node.id,
            target_port_id=output_node.inputs[0].id
        ))
        
        return WorkflowTemplate(
            id="customer_support",
            name="Customer Support",
            description="AI-powered customer support with intent classification and routing to specialized agents",
            category="Support",
            workflow=workflow,
            tags=["support", "classification", "routing"]
        )
    
    def _create_rag_qa_template(self) -> WorkflowTemplate:
        """Template de Q&A com RAG."""
        workflow = Workflow(
            name="RAG Q&A",
            description="Question answering with document retrieval"
        )
        
        # Nodes
        input_node = InputNode(name="Question")
        input_node.position.x = 50
        input_node.position.y = 200
        
        rag_search = RAGSearchNode(name="Search Documents")
        rag_search.position.x = 300
        rag_search.position.y = 200
        
        qa_agent = AgentNode(
            name="Q&A Agent",
            model="gpt-4o",
            instructions="Answer questions based on the provided context. If the context doesn't contain the answer, say so."
        )
        qa_agent.position.x = 550
        qa_agent.position.y = 200
        
        output_node = OutputNode(name="Answer")
        output_node.position.x = 800
        output_node.position.y = 200
        
        for node in [input_node, rag_search, qa_agent, output_node]:
            workflow.add_node(node)
        
        # Connections
        workflow.add_connection(Connection(
            source_node_id=input_node.id,
            source_port_id=input_node.outputs[0].id,
            target_node_id=rag_search.id,
            target_port_id=rag_search.inputs[0].id
        ))
        workflow.add_connection(Connection(
            source_node_id=rag_search.id,
            source_port_id=rag_search.outputs[1].id,  # context
            target_node_id=qa_agent.id,
            target_port_id=qa_agent.inputs[1].id  # context
        ))
        workflow.add_connection(Connection(
            source_node_id=input_node.id,
            source_port_id=input_node.outputs[1].id,  # message
            target_node_id=qa_agent.id,
            target_port_id=qa_agent.inputs[0].id  # message
        ))
        workflow.add_connection(Connection(
            source_node_id=qa_agent.id,
            source_port_id=qa_agent.outputs[0].id,
            target_node_id=output_node.id,
            target_port_id=output_node.inputs[0].id
        ))
        
        return WorkflowTemplate(
            id="rag_qa",
            name="RAG Q&A",
            description="Question answering system with document retrieval for context",
            category="RAG",
            workflow=workflow,
            tags=["rag", "qa", "documents"]
        )
    
    def _create_content_generator_template(self) -> WorkflowTemplate:
        """Template de geração de conteúdo."""
        workflow = Workflow(
            name="Content Generator",
            description="Multi-step content generation with research and writing"
        )
        
        input_node = InputNode(name="Topic")
        input_node.position.x = 50
        input_node.position.y = 200
        
        researcher = AgentNode(
            name="Researcher",
            model="gpt-4o",
            instructions="Research the given topic and provide key facts and insights."
        )
        researcher.position.x = 300
        researcher.position.y = 200
        
        writer = AgentNode(
            name="Writer",
            model="gpt-4o",
            instructions="Write engaging content based on the research provided."
        )
        writer.position.x = 550
        writer.position.y = 200
        
        editor = AgentNode(
            name="Editor",
            model="gpt-4o",
            instructions="Edit and improve the content for clarity, grammar, and style."
        )
        editor.position.x = 800
        editor.position.y = 200
        
        output_node = OutputNode(name="Content")
        output_node.position.x = 1050
        output_node.position.y = 200
        
        for node in [input_node, researcher, writer, editor, output_node]:
            workflow.add_node(node)
        
        # Chain connections
        nodes = [input_node, researcher, writer, editor, output_node]
        for i in range(len(nodes) - 1):
            workflow.add_connection(Connection(
                source_node_id=nodes[i].id,
                source_port_id=nodes[i].outputs[0].id,
                target_node_id=nodes[i+1].id,
                target_port_id=nodes[i+1].inputs[0].id
            ))
        
        return WorkflowTemplate(
            id="content_generator",
            name="Content Generator",
            description="Multi-agent pipeline for content research, writing, and editing",
            category="Content",
            workflow=workflow,
            tags=["content", "writing", "research"]
        )
    
    def _create_research_assistant_template(self) -> WorkflowTemplate:
        """Template de assistente de pesquisa."""
        workflow = Workflow(
            name="Research Assistant",
            description="Research assistant with memory and RAG"
        )
        
        input_node = InputNode(name="Query")
        input_node.position.x = 50
        input_node.position.y = 200
        
        memory_read = MemoryReadNode(name="Recall Context")
        memory_read.position.x = 300
        memory_read.position.y = 100
        
        rag_search = RAGSearchNode(name="Search Knowledge")
        rag_search.position.x = 300
        rag_search.position.y = 300
        
        researcher = AgentNode(
            name="Research Agent",
            model="gpt-4o",
            instructions="You are a research assistant. Use the context and documents to answer questions thoroughly."
        )
        researcher.position.x = 550
        researcher.position.y = 200
        
        output_node = OutputNode(name="Answer")
        output_node.position.x = 800
        output_node.position.y = 200
        
        for node in [input_node, memory_read, rag_search, researcher, output_node]:
            workflow.add_node(node)
        
        # Connections
        workflow.add_connection(Connection(
            source_node_id=input_node.id,
            source_port_id=input_node.outputs[0].id,
            target_node_id=memory_read.id,
            target_port_id=memory_read.inputs[0].id
        ))
        workflow.add_connection(Connection(
            source_node_id=input_node.id,
            source_port_id=input_node.outputs[0].id,
            target_node_id=rag_search.id,
            target_port_id=rag_search.inputs[0].id
        ))
        workflow.add_connection(Connection(
            source_node_id=memory_read.id,
            source_port_id=memory_read.outputs[1].id,
            target_node_id=researcher.id,
            target_port_id=researcher.inputs[1].id
        ))
        workflow.add_connection(Connection(
            source_node_id=rag_search.id,
            source_port_id=rag_search.outputs[1].id,
            target_node_id=researcher.id,
            target_port_id=researcher.inputs[1].id
        ))
        workflow.add_connection(Connection(
            source_node_id=input_node.id,
            source_port_id=input_node.outputs[1].id,
            target_node_id=researcher.id,
            target_port_id=researcher.inputs[0].id
        ))
        workflow.add_connection(Connection(
            source_node_id=researcher.id,
            source_port_id=researcher.outputs[0].id,
            target_node_id=output_node.id,
            target_port_id=output_node.inputs[0].id
        ))
        
        return WorkflowTemplate(
            id="research_assistant",
            name="Research Assistant",
            description="Research assistant with memory context and document retrieval",
            category="Research",
            workflow=workflow,
            tags=["research", "memory", "rag"]
        )
    
    def _create_data_processor_template(self) -> WorkflowTemplate:
        """Template de processamento de dados."""
        workflow = Workflow(
            name="Data Processor",
            description="Process and transform data with AI"
        )
        
        input_node = InputNode(name="Data")
        input_node.position.x = 50
        input_node.position.y = 200
        
        from .nodes import TransformNode
        
        validator = TransformNode(
            name="Validate",
            code="result = {'valid': True, 'data': data}"
        )
        validator.position.x = 300
        validator.position.y = 200
        
        processor = AgentNode(
            name="AI Processor",
            model="gpt-4o-mini",
            instructions="Process and analyze the data. Extract key insights."
        )
        processor.position.x = 550
        processor.position.y = 200
        
        formatter = TransformNode(
            name="Format Output",
            code="result = {'processed': True, 'output': data}"
        )
        formatter.position.x = 800
        formatter.position.y = 200
        
        output_node = OutputNode(name="Result")
        output_node.position.x = 1050
        output_node.position.y = 200
        
        for node in [input_node, validator, processor, formatter, output_node]:
            workflow.add_node(node)
        
        nodes = [input_node, validator, processor, formatter, output_node]
        for i in range(len(nodes) - 1):
            workflow.add_connection(Connection(
                source_node_id=nodes[i].id,
                source_port_id=nodes[i].outputs[0].id,
                target_node_id=nodes[i+1].id,
                target_port_id=nodes[i+1].inputs[0].id
            ))
        
        return WorkflowTemplate(
            id="data_processor",
            name="Data Processor",
            description="Pipeline for data validation, AI processing, and formatting",
            category="Data",
            workflow=workflow,
            tags=["data", "processing", "etl"]
        )
    
    def _create_debate_template(self) -> WorkflowTemplate:
        """Template de debate multi-agente."""
        workflow = Workflow(
            name="Multi-Agent Debate",
            description="Two agents debate a topic"
        )
        
        input_node = InputNode(name="Topic")
        input_node.position.x = 50
        input_node.position.y = 200
        
        from .nodes import TeamNode
        
        debate_team = TeamNode(
            name="Debate Team",
            workflow="debate"
        )
        debate_team.config["agents"] = [
            {"name": "Pro", "instructions": "Argue in favor of the topic"},
            {"name": "Con", "instructions": "Argue against the topic"}
        ]
        debate_team.position.x = 300
        debate_team.position.y = 200
        
        moderator = AgentNode(
            name="Moderator",
            model="gpt-4o",
            instructions="Summarize the debate and provide a balanced conclusion."
        )
        moderator.position.x = 550
        moderator.position.y = 200
        
        output_node = OutputNode(name="Conclusion")
        output_node.position.x = 800
        output_node.position.y = 200
        
        for node in [input_node, debate_team, moderator, output_node]:
            workflow.add_node(node)
        
        workflow.add_connection(Connection(
            source_node_id=input_node.id,
            source_port_id=input_node.outputs[0].id,
            target_node_id=debate_team.id,
            target_port_id=debate_team.inputs[0].id
        ))
        workflow.add_connection(Connection(
            source_node_id=debate_team.id,
            source_port_id=debate_team.outputs[0].id,
            target_node_id=moderator.id,
            target_port_id=moderator.inputs[0].id
        ))
        workflow.add_connection(Connection(
            source_node_id=moderator.id,
            source_port_id=moderator.outputs[0].id,
            target_node_id=output_node.id,
            target_port_id=output_node.inputs[0].id
        ))
        
        return WorkflowTemplate(
            id="debate",
            name="Multi-Agent Debate",
            description="Two agents debate a topic with a moderator providing the conclusion",
            category="Multi-Agent",
            workflow=workflow,
            tags=["debate", "multi-agent", "discussion"]
        )
    
    # ==================== Public API ====================
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Obtém template pelo ID."""
        return self._templates.get(template_id)
    
    def list_templates(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None
    ) -> list[WorkflowTemplate]:
        """Lista templates disponíveis."""
        templates = list(self._templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tag:
            templates = [t for t in templates if tag in t.tags]
        
        return templates
    
    def get_categories(self) -> list[str]:
        """Lista categorias disponíveis."""
        return list(set(t.category for t in self._templates.values()))
    
    def add_template(self, template: WorkflowTemplate) -> None:
        """Adiciona um template customizado."""
        self._templates[template.id] = template
    
    def remove_template(self, template_id: str) -> bool:
        """Remove um template."""
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False
    
    def export_template(self, template_id: str) -> Optional[str]:
        """Exporta template como JSON."""
        template = self.get_template(template_id)
        if template:
            return json.dumps(template.to_dict(), indent=2, default=str)
        return None
    
    def import_template(self, json_str: str) -> WorkflowTemplate:
        """Importa template de JSON."""
        data = json.loads(json_str)
        
        workflow = Workflow.from_dict(data.get("workflow", {}))
        
        template = WorkflowTemplate(
            id=data.get("id", "imported"),
            name=data.get("name", "Imported Template"),
            description=data.get("description", ""),
            category=data.get("category", "Custom"),
            workflow=workflow,
            tags=data.get("tags", []),
            author=data.get("author", "User"),
            version=data.get("version", "1.0.0")
        )
        
        self.add_template(template)
        return template


# Singleton
_template_library: Optional[TemplateLibrary] = None


def get_template_library() -> TemplateLibrary:
    """Retorna a biblioteca de templates singleton."""
    global _template_library
    if _template_library is None:
        _template_library = TemplateLibrary()
    return _template_library
