"""
Ferramentas de LLM.

Inclui:
- PerplexityTool: Pesquisa com IA via Perplexity
- OllamaTool: LLMs locais via Ollama
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .perplexity import PerplexityTool
    from .ollama import OllamaTool

__all__ = [
    "PerplexityTool",
    "OllamaTool",
]
