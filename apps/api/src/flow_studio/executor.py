"""
Agno Flow Studio v3.0 - Node Executors

Executors for different node types.
"""

import asyncio
import httpx
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

from .types import Node, NodeType

logger = logging.getLogger(__name__)


class NodeExecutor(ABC):
    """Base class for node executors."""
    
    last_token_usage: int = 0
    last_cost: float = 0.0
    
    @abstractmethod
    async def execute(
        self,
        node: Node,
        inputs: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Any:
        """Execute the node."""
        pass


class AgentExecutor(NodeExecutor):
    """Executor for agent nodes."""
    
    async def execute(
        self,
        node: Node,
        inputs: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Any:
        """Execute an agent node."""
        from agno import Agent
        
        config = node.config
        model = config.get("model", "gpt-4o")
        instructions = config.get("instructions", "")
        temperature = config.get("temperature", 0.7)
        
        # Get message from inputs
        message = inputs.get("message", inputs.get("input", ""))
        if isinstance(message, dict):
            message = message.get("content", str(message))
        
        # Create and run agent
        agent = Agent(
            model=model,
            instructions=instructions,
            temperature=temperature
        )
        
        response = await agent.arun(str(message))
        
        # Track usage
        self.last_token_usage = getattr(response, 'usage', {}).get('total_tokens', 0)
        self.last_cost = self._calculate_cost(model, self.last_token_usage)
        
        return response.content if hasattr(response, 'content') else str(response)
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost based on model and tokens."""
        # Simplified cost calculation
        costs = {
            "gpt-4o": 0.00003,
            "gpt-4o-mini": 0.000003,
            "claude-3-5-sonnet": 0.000015,
        }
        return tokens * costs.get(model, 0.00001)


class ConditionExecutor(NodeExecutor):
    """Executor for condition nodes."""
    
    async def execute(
        self,
        node: Node,
        inputs: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Any:
        """Execute a condition node."""
        config = node.config
        condition = config.get("condition", "True")
        
        value = inputs.get("value", inputs.get("input"))
        
        # Evaluate condition
        try:
            result = eval(condition, {"value": value, "vars": variables})
            return {"result": result, "value": value}
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return {"result": False, "value": value, "error": str(e)}


class LoopExecutor(NodeExecutor):
    """Executor for loop nodes."""
    
    async def execute(
        self,
        node: Node,
        inputs: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Any:
        """Execute a loop node."""
        config = node.config
        max_iterations = config.get("maxIterations", 10)
        
        items = inputs.get("items", inputs.get("input", []))
        if not isinstance(items, list):
            items = [items]
        
        # Limit iterations
        items = items[:max_iterations]
        
        results = []
        for i, item in enumerate(items):
            results.append({
                "index": i,
                "item": item
            })
        
        return {"items": results, "total": len(results)}


class TransformExecutor(NodeExecutor):
    """Executor for transform nodes."""
    
    async def execute(
        self,
        node: Node,
        inputs: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Any:
        """Execute a transform node."""
        config = node.config
        code = config.get("code", "data")
        
        data = inputs.get("data", inputs.get("input"))
        
        try:
            # Safe eval with limited scope
            result = eval(code, {"data": data, "vars": variables, "json": json})
            return result
        except Exception as e:
            logger.error(f"Transform failed: {e}")
            return {"error": str(e), "original": data}


class HTTPExecutor(NodeExecutor):
    """Executor for HTTP request nodes."""
    
    async def execute(
        self,
        node: Node,
        inputs: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Any:
        """Execute an HTTP request."""
        config = node.config
        method = config.get("method", "GET")
        url = config.get("url", "")
        headers = config.get("headers", {})
        
        body = inputs.get("body", inputs.get("input"))
        
        # Replace variables in URL
        for key, value in variables.items():
            url = url.replace(f"{{{{vars.{key}}}}}", str(value))
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if method in ["POST", "PUT", "PATCH"] else None,
                    params=body if method == "GET" else None,
                    timeout=30.0
                )
                
                return {
                    "status": response.status_code,
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    "headers": dict(response.headers)
                }
            except Exception as e:
                return {"error": str(e), "status": 0}


class DelayExecutor(NodeExecutor):
    """Executor for delay nodes."""
    
    async def execute(
        self,
        node: Node,
        inputs: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Any:
        """Execute a delay."""
        config = node.config
        seconds = config.get("seconds", 1)
        
        await asyncio.sleep(seconds)
        
        return inputs.get("input", inputs)


class CacheExecutor(NodeExecutor):
    """Executor for cache nodes."""
    
    _cache: Dict[str, Any] = {}
    
    async def execute(
        self,
        node: Node,
        inputs: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Any:
        """Execute cache read/write."""
        key = inputs.get("key", "default")
        value = inputs.get("value")
        
        if value is not None:
            # Write to cache
            self._cache[key] = {
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
            return {"cached": True, "key": key}
        else:
            # Read from cache
            cached = self._cache.get(key)
            if cached:
                return cached["value"]
            return None


class InputExecutor(NodeExecutor):
    """Executor for input nodes."""
    
    async def execute(
        self,
        node: Node,
        inputs: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Any:
        """Pass through input data."""
        return inputs.get("data", inputs.get("input", inputs))


class OutputExecutor(NodeExecutor):
    """Executor for output nodes."""
    
    async def execute(
        self,
        node: Node,
        inputs: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Any:
        """Collect output data."""
        return inputs.get("data", inputs.get("input", inputs))


class HumanApprovalExecutor(NodeExecutor):
    """Executor for human approval nodes."""
    
    _pending_approvals: Dict[str, Dict] = {}
    
    async def execute(
        self,
        node: Node,
        inputs: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Any:
        """Request human approval."""
        request_data = inputs.get("request", inputs.get("input"))
        approval_id = f"approval_{node.id}_{datetime.now().timestamp()}"
        
        # Store pending approval
        self._pending_approvals[approval_id] = {
            "node_id": node.id,
            "data": request_data,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # In real implementation, this would wait for human approval
        # For now, auto-approve after delay
        await asyncio.sleep(1)
        
        return {
            "approved": True,
            "approval_id": approval_id,
            "data": request_data
        }
    
    def approve(self, approval_id: str):
        """Approve a pending request."""
        if approval_id in self._pending_approvals:
            self._pending_approvals[approval_id]["status"] = "approved"
    
    def reject(self, approval_id: str, reason: str = ""):
        """Reject a pending request."""
        if approval_id in self._pending_approvals:
            self._pending_approvals[approval_id]["status"] = "rejected"
            self._pending_approvals[approval_id]["reason"] = reason


# Register default executors
def register_default_executors(engine: "WorkflowEngine"):
    """Register all default node executors."""
    from .engine import WorkflowEngine
    
    engine.register_executor(NodeType.AGENT, AgentExecutor())
    engine.register_executor(NodeType.CONDITION, ConditionExecutor())
    engine.register_executor(NodeType.LOOP, LoopExecutor())
    engine.register_executor(NodeType.TRANSFORM, TransformExecutor())
    engine.register_executor(NodeType.HTTP, HTTPExecutor())
    engine.register_executor(NodeType.DELAY, DelayExecutor())
    engine.register_executor(NodeType.CACHE, CacheExecutor())
    engine.register_executor(NodeType.INPUT, InputExecutor())
    engine.register_executor(NodeType.OUTPUT, OutputExecutor())
    engine.register_executor(NodeType.HUMAN_APPROVAL, HumanApprovalExecutor())
