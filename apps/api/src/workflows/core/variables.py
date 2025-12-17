"""
Sistema de Variáveis e Expressões para Workflows.

Suporta:
- Interpolação de variáveis: ${variable}
- Expressões JMESPath: ${data.items[0].name}
- Funções built-in: ${upper(name)}, ${now()}, ${len(items)}
- Operadores: ${count > 10}, ${status == 'active'}
"""

import re
import json
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
import operator


# Funções built-in disponíveis
BUILTIN_FUNCTIONS: Dict[str, Callable] = {
    # String
    "upper": lambda x: str(x).upper(),
    "lower": lambda x: str(x).lower(),
    "trim": lambda x: str(x).strip(),
    "len": lambda x: len(x) if hasattr(x, "__len__") else 0,
    "substr": lambda s, start, end=None: str(s)[start:end],
    "replace": lambda s, old, new: str(s).replace(old, new),
    "split": lambda s, sep=" ": str(s).split(sep),
    "join": lambda items, sep=", ": sep.join(str(i) for i in items),
    
    # Numeric
    "int": lambda x: int(x),
    "float": lambda x: float(x),
    "abs": lambda x: abs(x),
    "round": lambda x, n=0: round(x, n),
    "min": lambda *args: min(args),
    "max": lambda *args: max(args),
    "sum": lambda items: sum(items),
    
    # Date/Time
    "now": lambda: datetime.now().isoformat(),
    "today": lambda: datetime.now().date().isoformat(),
    "timestamp": lambda: int(datetime.now().timestamp()),
    "format_date": lambda d, fmt="%Y-%m-%d": datetime.fromisoformat(d).strftime(fmt) if isinstance(d, str) else d.strftime(fmt),
    
    # JSON
    "json_parse": lambda s: json.loads(s),
    "json_dump": lambda obj: json.dumps(obj),
    
    # Collections
    "first": lambda items: items[0] if items else None,
    "last": lambda items: items[-1] if items else None,
    "unique": lambda items: list(set(items)),
    "sort": lambda items: sorted(items),
    "reverse": lambda items: list(reversed(items)),
    "filter_empty": lambda items: [i for i in items if i],
    
    # Type
    "type": lambda x: type(x).__name__,
    "str": lambda x: str(x),
    "bool": lambda x: bool(x),
    "default": lambda x, default: x if x is not None else default,
    "coalesce": lambda *args: next((a for a in args if a is not None), None),
}

# Operadores suportados
OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "and": lambda a, b: a and b,
    "or": lambda a, b: a or b,
    "not": lambda a: not a,
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "%": operator.mod,
    "in": lambda a, b: a in b,
    "contains": lambda a, b: b in a,
}


@dataclass
class Expression:
    """Uma expressão avaliável."""
    raw: str
    parsed: Optional[Any] = None
    
    def evaluate(self, context: Dict[str, Any]) -> Any:
        """Avalia a expressão no contexto dado."""
        return ExpressionEvaluator.evaluate(self.raw, context)
    
    def is_truthy(self, context: Dict[str, Any]) -> bool:
        """Avalia se expressão é verdadeira."""
        result = self.evaluate(context)
        return bool(result)


class ExpressionEvaluator:
    """
    Avaliador de expressões.
    
    Sintaxe suportada:
    - ${variable} - Acessa variável
    - ${obj.prop} - Acessa propriedade
    - ${arr[0]} - Acessa índice
    - ${func(arg)} - Chama função
    - ${a == b} - Comparação
    - ${a > 10 and b < 5} - Expressão lógica
    """
    
    # Pattern para detectar expressões ${...}
    EXPRESSION_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    # Pattern para chamada de função
    FUNCTION_PATTERN = re.compile(r'^(\w+)\((.*)\)$')
    
    @classmethod
    def evaluate(cls, expression: str, context: Dict[str, Any]) -> Any:
        """
        Avalia uma expressão.
        
        Args:
            expression: Expressão a avaliar
            context: Contexto de variáveis
            
        Returns:
            Resultado da avaliação
        """
        # Se a expressão é só ${...}, avalia e retorna
        if expression.startswith("${") and expression.endswith("}"):
            inner = expression[2:-1].strip()
            return cls._evaluate_inner(inner, context)
        
        # Senão, faz interpolação de strings
        def replacer(match):
            inner = match.group(1).strip()
            result = cls._evaluate_inner(inner, context)
            return str(result) if result is not None else ""
        
        return cls.EXPRESSION_PATTERN.sub(replacer, expression)
    
    @classmethod
    def _evaluate_inner(cls, expr: str, context: Dict[str, Any]) -> Any:
        """Avalia expressão interna."""
        expr = expr.strip()
        
        # Verificar operadores de comparação/lógicos
        for op_str, op_func in OPERATORS.items():
            # Evitar confusão com operadores dentro de strings
            if f" {op_str} " in expr:
                parts = expr.split(f" {op_str} ", 1)
                if len(parts) == 2:
                    left = cls._evaluate_inner(parts[0].strip(), context)
                    right = cls._evaluate_inner(parts[1].strip(), context)
                    return op_func(left, right)
        
        # Verificar chamada de função
        func_match = cls.FUNCTION_PATTERN.match(expr)
        if func_match:
            func_name = func_match.group(1)
            args_str = func_match.group(2)
            
            if func_name in BUILTIN_FUNCTIONS:
                args = cls._parse_function_args(args_str, context)
                return BUILTIN_FUNCTIONS[func_name](*args)
        
        # Verificar literal
        literal = cls._try_parse_literal(expr)
        if literal is not None:
            return literal
        
        # Resolver path de variável
        return cls._resolve_path(expr, context)
    
    @classmethod
    def _parse_function_args(cls, args_str: str, context: Dict[str, Any]) -> List[Any]:
        """Parse argumentos de função."""
        if not args_str.strip():
            return []
        
        args = []
        current = ""
        depth = 0
        in_string = False
        string_char = None
        
        for char in args_str + ",":
            if char in ('"', "'") and (not in_string or string_char == char):
                in_string = not in_string
                string_char = char if in_string else None
                current += char
            elif char == "(" and not in_string:
                depth += 1
                current += char
            elif char == ")" and not in_string:
                depth -= 1
                current += char
            elif char == "," and depth == 0 and not in_string:
                args.append(cls._evaluate_inner(current.strip(), context))
                current = ""
            else:
                current += char
        
        return args
    
    @classmethod
    def _try_parse_literal(cls, value: str) -> Optional[Any]:
        """Tenta parsear como literal."""
        value = value.strip()
        
        # String
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        
        # Boolean
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        
        # Null
        if value.lower() in ("null", "none"):
            return None
        
        # Number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Array
        if value.startswith("[") and value.endswith("]"):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # Object
        if value.startswith("{") and value.endswith("}"):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        return None
    
    @classmethod
    def _resolve_path(cls, path: str, context: Dict[str, Any]) -> Any:
        """Resolve um path de variável (e.g., data.items[0].name)."""
        parts = []
        current = ""
        in_bracket = False
        
        for char in path:
            if char == "." and not in_bracket:
                if current:
                    parts.append(current)
                    current = ""
            elif char == "[":
                if current:
                    parts.append(current)
                    current = ""
                in_bracket = True
            elif char == "]":
                if current:
                    parts.append(("index", current))
                    current = ""
                in_bracket = False
            else:
                current += char
        
        if current:
            parts.append(current)
        
        # Navegar pelo contexto
        result = context
        for part in parts:
            if result is None:
                return None
            
            if isinstance(part, tuple) and part[0] == "index":
                idx = part[1]
                try:
                    idx = int(idx)
                    result = result[idx]
                except (ValueError, IndexError, KeyError, TypeError):
                    return None
            elif isinstance(result, dict):
                result = result.get(part)
            elif hasattr(result, part):
                result = getattr(result, part)
            else:
                return None
        
        return result


class VariableResolver:
    """
    Resolvedor de variáveis para templates.
    
    Exemplo:
        resolver = VariableResolver()
        context = {"user": {"name": "João"}, "count": 5}
        
        # Interpolação simples
        result = resolver.resolve("Olá ${user.name}!", context)
        # "Olá João!"
        
        # Com funções
        result = resolver.resolve("Total: ${count * 2}", context)
        # "Total: 10"
    """
    
    def __init__(self):
        self._evaluator = ExpressionEvaluator
    
    def resolve(self, template: str, context: Dict[str, Any]) -> str:
        """Resolve template com variáveis."""
        return self._evaluator.evaluate(template, context)
    
    def resolve_dict(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve todas as strings em um dict."""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.resolve(value, context)
            elif isinstance(value, dict):
                result[key] = self.resolve_dict(value, context)
            elif isinstance(value, list):
                result[key] = self.resolve_list(value, context)
            else:
                result[key] = value
        return result
    
    def resolve_list(self, data: List[Any], context: Dict[str, Any]) -> List[Any]:
        """Resolve todas as strings em uma lista."""
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(self.resolve(item, context))
            elif isinstance(item, dict):
                result.append(self.resolve_dict(item, context))
            elif isinstance(item, list):
                result.append(self.resolve_list(item, context))
            else:
                result.append(item)
        return result
    
    def evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Avalia condição como boolean."""
        result = self._evaluator.evaluate(condition, context)
        return bool(result)


# Singleton global
_resolver: Optional[VariableResolver] = None


def get_resolver() -> VariableResolver:
    """Obtém resolver global."""
    global _resolver
    if _resolver is None:
        _resolver = VariableResolver()
    return _resolver


def resolve(template: str, context: Dict[str, Any]) -> str:
    """Atalho para resolver template."""
    return get_resolver().resolve(template, context)


def evaluate(expression: str, context: Dict[str, Any]) -> Any:
    """Atalho para avaliar expressão."""
    return ExpressionEvaluator.evaluate(expression, context)
