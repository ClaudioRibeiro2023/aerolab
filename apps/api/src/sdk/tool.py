"""
Agno SDK - Tool System

Sistema de ferramentas para agentes.
Permite criar tools customizadas de forma simples.

Uso:
```python
from agno import Tool, tool

# Usando decorator
@tool
def search(query: str) -> str:
    '''Search for information.'''
    return f"Results for: {query}"

# Usando classe
class Calculator(Tool):
    name = "calculator"
    description = "Perform calculations"
    
    def run(self, expression: str) -> str:
        return str(eval(expression))
```
"""

import inspect
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any, Callable, get_type_hints, Union
from functools import wraps
import asyncio


@dataclass
class ToolParameter:
    """Parâmetro de ferramenta."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = True
    default: Any = None
    enum: Optional[list] = None


@dataclass
class ToolResult:
    """
    Resultado de execução de ferramenta.
    
    Attributes:
        content: Conteúdo do resultado
        is_error: Se é um erro
        error_message: Mensagem de erro
    """
    content: Any
    is_error: bool = False
    error_message: Optional[str] = None
    
    def __str__(self) -> str:
        if self.is_error:
            return f"Error: {self.error_message}"
        return str(self.content)
    
    @classmethod
    def success(cls, content: Any) -> "ToolResult":
        """Cria resultado de sucesso."""
        return cls(content=content)
    
    @classmethod
    def error(cls, message: str) -> "ToolResult":
        """Cria resultado de erro."""
        return cls(content=None, is_error=True, error_message=message)


class Tool(ABC):
    """
    Base class para ferramentas.
    
    Pode ser estendida para criar tools customizadas
    ou usada via decorator @tool.
    
    Attributes:
        name: Nome da ferramenta
        description: Descrição da ferramenta
        parameters: Lista de parâmetros
    """
    name: str = ""
    description: str = ""
    parameters: list[ToolParameter] = field(default_factory=list)
    
    # Configurações
    requires_confirmation: bool = False
    timeout: float = 30.0
    
    def __init__(self):
        if not self.name:
            self.name = self.__class__.__name__.lower()
        if not self.description:
            self.description = self.__doc__ or ""
    
    @abstractmethod
    def run(self, **kwargs) -> Any:
        """
        Executa a ferramenta.
        
        Deve ser implementado por subclasses.
        """
        pass
    
    async def arun(self, **kwargs) -> Any:
        """
        Executa a ferramenta de forma assíncrona.
        
        Por padrão, executa run() em thread pool.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.run(**kwargs))
    
    def __call__(self, **kwargs) -> ToolResult:
        """Permite chamar a tool diretamente."""
        try:
            result = self.run(**kwargs)
            return ToolResult.success(result)
        except Exception as e:
            return ToolResult.error(str(e))
    
    def to_dict(self) -> dict:
        """Converte para formato de função OpenAI."""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {"type": param.type}
            if param.description:
                prop["description"] = param.description
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


class FunctionTool(Tool):
    """
    Tool wrapper para funções Python.
    
    Criada automaticamente pelo decorator @tool.
    """
    
    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None
    ):
        self._func = func
        self._is_async = asyncio.iscoroutinefunction(func)
        
        # Extrair metadata da função
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        
        # Extrair parâmetros
        self.parameters = self._extract_parameters(func)
        
        # Não chamar super().__init__() pois já setamos os atributos
    
    def _extract_parameters(self, func: Callable) -> list[ToolParameter]:
        """Extrai parâmetros da assinatura da função."""
        sig = inspect.signature(func)
        type_hints = get_type_hints(func) if hasattr(func, '__annotations__') else {}
        
        params = []
        
        for name, param in sig.parameters.items():
            if name == 'self':
                continue
            
            # Tipo do parâmetro
            type_hint = type_hints.get(name, Any)
            param_type = self._python_type_to_json(type_hint)
            
            # Descrição do docstring
            description = self._extract_param_description(func, name)
            
            # Default
            has_default = param.default != inspect.Parameter.empty
            default = param.default if has_default else None
            
            params.append(ToolParameter(
                name=name,
                type=param_type,
                description=description,
                required=not has_default,
                default=default
            ))
        
        return params
    
    def _python_type_to_json(self, type_hint: Any) -> str:
        """Converte tipo Python para JSON Schema type."""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            type(None): "null"
        }
        
        # Extrair tipo base para Union/Optional
        origin = getattr(type_hint, '__origin__', None)
        if origin is Union:
            args = getattr(type_hint, '__args__', ())
            # Para Optional[X], pegar o primeiro tipo não-None
            for arg in args:
                if arg is not type(None):
                    return self._python_type_to_json(arg)
        
        return type_map.get(type_hint, "string")
    
    def _extract_param_description(self, func: Callable, param_name: str) -> Optional[str]:
        """Extrai descrição do parâmetro do docstring."""
        if not func.__doc__:
            return None
        
        # Tentar extrair do formato Google/NumPy docstring
        lines = func.__doc__.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(f'{param_name}:') or stripped.startswith(f'{param_name} '):
                # Próximas linhas até o próximo parâmetro
                desc_parts = [stripped.split(':', 1)[-1].strip() if ':' in stripped else '']
                for next_line in lines[i+1:]:
                    if next_line.strip() and not next_line.strip()[0].isalpha():
                        desc_parts.append(next_line.strip())
                    else:
                        break
                return ' '.join(desc_parts).strip() or None
        
        return None
    
    def run(self, **kwargs) -> Any:
        """Executa a função."""
        if self._is_async:
            # Se for async, rodar em event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Se já estamos em um loop, criar task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self._func(**kwargs))
                    return future.result()
            else:
                return loop.run_until_complete(self._func(**kwargs))
        else:
            return self._func(**kwargs)
    
    async def arun(self, **kwargs) -> Any:
        """Executa a função de forma assíncrona."""
        if self._is_async:
            return await self._func(**kwargs)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._func(**kwargs))


def tool(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Union[FunctionTool, Callable[[Callable], FunctionTool]]:
    """
    Decorator para criar uma Tool a partir de uma função.
    
    Uso:
    ```python
    @tool
    def search(query: str) -> str:
        '''Search for information.'''
        return f"Results for: {query}"
    
    @tool(name="custom_name", description="Custom description")
    def my_tool(x: int) -> int:
        return x * 2
    ```
    
    Args:
        func: Função a decorar
        name: Nome customizado da tool
        description: Descrição customizada
        
    Returns:
        FunctionTool wrapping a função
    """
    def decorator(f: Callable) -> FunctionTool:
        return FunctionTool(f, name=name, description=description)
    
    if func is not None:
        return decorator(func)
    
    return decorator


class ToolRegistry:
    """
    Registry de ferramentas.
    
    Gerencia coleção de tools disponíveis.
    """
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Registra uma ferramenta."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """Obtém ferramenta por nome."""
        return self._tools.get(name)
    
    def list(self) -> list[Tool]:
        """Lista todas as ferramentas."""
        return list(self._tools.values())
    
    def to_openai_format(self) -> list[dict]:
        """Converte todas as tools para formato OpenAI."""
        return [tool.to_dict() for tool in self._tools.values()]
    
    async def execute(self, name: str, arguments: dict) -> ToolResult:
        """
        Executa uma ferramenta pelo nome.
        
        Args:
            name: Nome da ferramenta
            arguments: Argumentos
            
        Returns:
            ToolResult
        """
        tool = self.get(name)
        if not tool:
            return ToolResult.error(f"Tool not found: {name}")
        
        try:
            result = await tool.arun(**arguments)
            return ToolResult.success(result)
        except Exception as e:
            return ToolResult.error(str(e))


# Tools built-in

@tool
def python_repl(code: str) -> str:
    """
    Execute Python code and return the result.
    
    Args:
        code: Python code to execute
        
    Returns:
        Output of the code execution
    """
    import io
    import sys
    
    # Capturar stdout
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        exec(code)
        output = sys.stdout.getvalue()
        return output if output else "Code executed successfully (no output)"
    except Exception as e:
        return f"Error: {e}"
    finally:
        sys.stdout = old_stdout


@tool
def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web for information.
    
    Args:
        query: Search query
        num_results: Number of results to return
        
    Returns:
        Search results
    """
    # Placeholder - integraria com API de busca real
    return f"Search results for '{query}' (placeholder - integrate with real search API)"


@tool
def read_file(path: str) -> str:
    """
    Read contents of a file.
    
    Args:
        path: Path to the file
        
    Returns:
        File contents
    """
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        path: Path to the file
        content: Content to write
        
    Returns:
        Success message
    """
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


# Registry global de tools built-in
_builtin_tools = ToolRegistry()
_builtin_tools.register(python_repl)
_builtin_tools.register(web_search)
_builtin_tools.register(read_file)
_builtin_tools.register(write_file)


def get_builtin_tools() -> ToolRegistry:
    """Retorna registry de tools built-in."""
    return _builtin_tools
