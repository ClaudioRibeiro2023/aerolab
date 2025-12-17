"""
Domain Studio Protocols - MCP e A2A para integração avançada.
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import uuid

from .types import DomainType, MCPTool, MCPResource, A2AMessage

logger = logging.getLogger(__name__)


# ============================================================
# MCP PROTOCOL (Model Context Protocol)
# ============================================================

class MCPProtocol:
    """
    Implementação do Model Context Protocol para integração com Claude e outros.
    
    Features:
    - Tools registration
    - Resources management
    - Prompts handling
    """
    
    def __init__(self, domain: DomainType, name: str = ""):
        self.domain = domain
        self.name = name or f"{domain.value}_mcp_server"
        self._tools: Dict[str, MCPTool] = {}
        self._resources: Dict[str, MCPResource] = {}
        self._prompts: Dict[str, Dict] = {}
        
        logger.info("MCP Server initialized: %s", self.name)
    
    # ============================================================
    # TOOLS
    # ============================================================
    
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable
    ) -> None:
        """Register a tool for the MCP server."""
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler
        )
        self._tools[name] = tool
        logger.debug("Registered MCP tool: %s", name)
    
    def tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any]
    ) -> Callable:
        """Decorator to register a tool."""
        def decorator(func: Callable) -> Callable:
            self.register_tool(name, description, input_schema, func)
            return func
        return decorator
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Call a registered tool."""
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")
        
        tool = self._tools[name]
        logger.info("Calling MCP tool: %s", name)
        
        if asyncio.iscoroutinefunction(tool.handler):
            return await tool.handler(**arguments)
        return tool.handler(**arguments)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
            for tool in self._tools.values()
        ]
    
    # ============================================================
    # RESOURCES
    # ============================================================
    
    def register_resource(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str = "application/json"
    ) -> None:
        """Register a resource."""
        resource = MCPResource(
            uri=uri,
            name=name,
            description=description,
            mime_type=mime_type
        )
        self._resources[uri] = resource
        logger.debug("Registered MCP resource: %s", uri)
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource by URI."""
        if uri not in self._resources:
            raise ValueError(f"Resource not found: {uri}")
        
        resource = self._resources[uri]
        logger.info("Reading MCP resource: %s", uri)
        
        # Override in subclasses to provide actual content
        return {
            "uri": uri,
            "name": resource.name,
            "mimeType": resource.mime_type,
            "content": {}
        }
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """List all registered resources."""
        return [
            {
                "uri": res.uri,
                "name": res.name,
                "description": res.description,
                "mimeType": res.mime_type
            }
            for res in self._resources.values()
        ]
    
    # ============================================================
    # PROMPTS
    # ============================================================
    
    def register_prompt(
        self,
        name: str,
        description: str,
        arguments: List[Dict[str, Any]]
    ) -> None:
        """Register a prompt template."""
        self._prompts[name] = {
            "name": name,
            "description": description,
            "arguments": arguments
        }
        logger.debug("Registered MCP prompt: %s", name)
    
    async def get_prompt(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get a prompt with filled arguments."""
        if name not in self._prompts:
            raise ValueError(f"Prompt not found: {name}")
        
        prompt = self._prompts[name]
        return {
            "name": name,
            "description": prompt["description"],
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": json.dumps(arguments)}
                }
            ]
        }
    
    def list_prompts(self) -> List[Dict[str, Any]]:
        """List all registered prompts."""
        return list(self._prompts.values())
    
    # ============================================================
    # SERVER INFO
    # ============================================================
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "name": self.name,
            "domain": self.domain.value,
            "version": "1.0.0",
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True}
            }
        }


# ============================================================
# A2A PROTOCOL (Agent-to-Agent)
# ============================================================

class A2AProtocol:
    """
    Protocolo de comunicação Agent-to-Agent.
    
    Features:
    - Message passing between agents
    - Negotiation protocol
    - Collaboration patterns
    """
    
    def __init__(self):
        self._agents: Dict[str, A2AAgent] = {}
        self._message_queue: Dict[str, List[A2AMessage]] = {}
        self._conversations: Dict[str, List[A2AMessage]] = {}
        
        logger.info("A2A Protocol initialized")
    
    def register_agent(self, agent_id: str, agent: A2AAgent) -> None:
        """Register an agent for A2A communication."""
        self._agents[agent_id] = agent
        self._message_queue[agent_id] = []
        logger.debug("Registered A2A agent: %s", agent_id)
    
    async def send_message(
        self,
        sender: str,
        receiver: str,
        message_type: str,
        content: Dict[str, Any]
    ) -> A2AMessage:
        """Send a message from one agent to another."""
        if receiver not in self._agents:
            raise ValueError(f"Receiver agent not found: {receiver}")
        
        message = A2AMessage(
            sender=sender,
            receiver=receiver,
            type=message_type,
            content=content
        )
        
        self._message_queue[receiver].append(message)
        logger.info("A2A message sent: %s -> %s (%s)", sender, receiver, message_type)
        
        return message
    
    async def receive_messages(self, agent_id: str) -> List[A2AMessage]:
        """Receive all pending messages for an agent."""
        if agent_id not in self._message_queue:
            return []
        
        messages = self._message_queue[agent_id]
        self._message_queue[agent_id] = []
        return messages
    
    async def negotiate(
        self,
        initiator: str,
        responder: str,
        topic: str,
        initial_proposal: Dict[str, Any],
        max_rounds: int = 10
    ) -> Dict[str, Any]:
        """
        Run a negotiation between two agents.
        
        Returns the final agreed proposal or None if deadlock.
        """
        conversation_id = str(uuid.uuid4())
        self._conversations[conversation_id] = []
        
        current_proposal = initial_proposal
        current_proposer = initiator
        
        for round_num in range(max_rounds):
            # Send proposal
            message = await self.send_message(
                sender=current_proposer,
                receiver=responder if current_proposer == initiator else initiator,
                message_type="proposal" if round_num == 0 else "counter_proposal",
                content={
                    "topic": topic,
                    "proposal": current_proposal,
                    "round": round_num + 1
                }
            )
            self._conversations[conversation_id].append(message)
            
            # Get response from other agent
            other_agent = responder if current_proposer == initiator else initiator
            if other_agent in self._agents:
                response = await self._agents[other_agent].evaluate_proposal(
                    current_proposal,
                    topic
                )
                
                if response.get("accepted"):
                    logger.info("Negotiation completed: agreement reached")
                    return {
                        "status": "agreed",
                        "final_proposal": current_proposal,
                        "rounds": round_num + 1,
                        "conversation_id": conversation_id
                    }
                
                if response.get("counter_proposal"):
                    current_proposal = response["counter_proposal"]
                    current_proposer = other_agent
        
        logger.warning("Negotiation deadlocked after %d rounds", max_rounds)
        return {
            "status": "deadlock",
            "final_proposal": current_proposal,
            "rounds": max_rounds,
            "conversation_id": conversation_id
        }
    
    async def collaborate(
        self,
        agents: List[str],
        task: Dict[str, Any],
        coordinator: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a collaborative task with multiple agents.
        
        Each agent contributes to the task.
        """
        results = {}
        coordinator = coordinator or agents[0]
        
        # Coordinator distributes subtasks
        if coordinator in self._agents:
            subtasks = await self._agents[coordinator].decompose_task(task)
        else:
            subtasks = [{"agent": a, "task": task} for a in agents]
        
        # Each agent executes their subtask
        for subtask in subtasks:
            agent_id = subtask.get("agent")
            if agent_id in self._agents:
                result = await self._agents[agent_id].execute_subtask(subtask)
                results[agent_id] = result
        
        # Coordinator synthesizes results
        if coordinator in self._agents:
            final_result = await self._agents[coordinator].synthesize_results(results)
        else:
            final_result = results
        
        return {
            "status": "completed",
            "results": final_result,
            "participants": agents
        }


class A2AAgent(ABC):
    """Abstract base class for A2A-capable agents."""
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Return the agent ID."""
        pass
    
    @abstractmethod
    async def evaluate_proposal(
        self,
        proposal: Dict[str, Any],
        topic: str
    ) -> Dict[str, Any]:
        """
        Evaluate a proposal and return response.
        
        Returns:
            {"accepted": True} if accepted
            {"counter_proposal": {...}} if counter-proposing
            {"rejected": True} if rejected
        """
        pass
    
    @abstractmethod
    async def decompose_task(
        self,
        task: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Decompose a task into subtasks."""
        pass
    
    @abstractmethod
    async def execute_subtask(
        self,
        subtask: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a subtask."""
        pass
    
    @abstractmethod
    async def synthesize_results(
        self,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize results from multiple agents."""
        pass


# ============================================================
# DOMAIN MCP SERVER FACTORY
# ============================================================

def create_domain_mcp_server(domain: DomainType) -> MCPProtocol:
    """Create an MCP server for a specific domain with default tools."""
    server = MCPProtocol(domain=domain)
    
    # Register common tools
    server.register_tool(
        name="search_knowledge",
        description=f"Search the {domain.value} knowledge base",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["query"]
        },
        handler=lambda **kwargs: {"results": [], "query": kwargs.get("query")}
    )
    
    server.register_tool(
        name="check_compliance",
        description=f"Check content for {domain.value} compliance",
        input_schema={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to check"}
            },
            "required": ["content"]
        },
        handler=lambda **kwargs: {"compliant": True, "score": 100}
    )
    
    server.register_tool(
        name="run_workflow",
        description=f"Run a {domain.value} workflow",
        input_schema={
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "Workflow ID"},
                "inputs": {"type": "object", "description": "Workflow inputs"}
            },
            "required": ["workflow_id"]
        },
        handler=lambda **kwargs: {"status": "completed", "workflow_id": kwargs.get("workflow_id")}
    )
    
    # Register default resources
    server.register_resource(
        uri=f"domain://{domain.value}/config",
        name=f"{domain.value.title()} Configuration",
        description=f"Configuration for {domain.value} domain"
    )
    
    server.register_resource(
        uri=f"domain://{domain.value}/agents",
        name=f"{domain.value.title()} Agents",
        description=f"List of agents for {domain.value} domain"
    )
    
    return server
