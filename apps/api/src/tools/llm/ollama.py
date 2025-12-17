"""
Ferramenta para LLMs locais via Ollama.

Ollama permite rodar modelos como Llama, Mistral, etc localmente.

Requer: Ollama instalado e rodando (ollama.ai)
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from src.tools.base import BaseTool, ToolResult, register_tool


@register_tool(domain="llm")
class OllamaTool(BaseTool):
    """
    Ferramenta para LLMs locais via Ollama.

    Funcionalidades:
    - chat: Conversar com modelo
    - generate: Gerar texto
    - list_models: Listar modelos disponíveis
    - embeddings: Gerar embeddings
    """

    name = "ollama"
    description = "LLMs locais via Ollama"
    version = "1.0.0"
    requires_auth = False

    def _setup(self) -> None:
        """Configura conexão com Ollama."""
        self.base_url = self.config.get("base_url") or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self._initialized = True

    def _execute(self, action: str, **kwargs) -> ToolResult:
        """Executa ação Ollama."""
        actions = {
            "chat": self._chat,
            "generate": self._generate,
            "list_models": self._list_models,
            "embeddings": self._embeddings,
        }

        if action not in actions:
            return ToolResult.fail(f"Ação desconhecida: {action}")

        return actions[action](**kwargs)

    def _chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3.2",
        stream: bool = False,
    ) -> ToolResult:
        """
        Conversa com modelo.

        Args:
            messages: Lista de mensagens [{"role": "user", "content": "..."}]
            model: Nome do modelo
            stream: Se deve fazer streaming

        Returns:
            ToolResult com resposta
        """
        try:
            import requests

            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": stream,
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            return ToolResult.ok({
                "model": model,
                "message": data.get("message", {}),
                "done": data.get("done"),
                "total_duration": data.get("total_duration"),
            })
        except requests.exceptions.ConnectionError:
            return ToolResult.fail("Ollama não está rodando. Inicie com: ollama serve")
        except Exception as e:
            return ToolResult.fail(f"Erro no chat: {str(e)}")

    def _generate(
        self,
        prompt: str,
        model: str = "llama3.2",
        system: Optional[str] = None,
    ) -> ToolResult:
        """
        Gera texto.

        Args:
            prompt: Prompt de entrada
            model: Nome do modelo
            system: System prompt opcional

        Returns:
            ToolResult com texto gerado
        """
        try:
            import requests

            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
            }
            if system:
                payload["system"] = system

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            return ToolResult.ok({
                "model": model,
                "response": data.get("response"),
                "done": data.get("done"),
                "context": data.get("context"),
            })
        except requests.exceptions.ConnectionError:
            return ToolResult.fail("Ollama não está rodando. Inicie com: ollama serve")
        except Exception as e:
            return ToolResult.fail(f"Erro na geração: {str(e)}")

    def _list_models(self) -> ToolResult:
        """Lista modelos disponíveis."""
        try:
            import requests

            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            models = [
                {
                    "name": m.get("name"),
                    "size": m.get("size"),
                    "modified": m.get("modified_at"),
                }
                for m in data.get("models", [])
            ]

            return ToolResult.ok({
                "models": models,
                "count": len(models),
            })
        except requests.exceptions.ConnectionError:
            return ToolResult.fail("Ollama não está rodando. Inicie com: ollama serve")
        except Exception as e:
            return ToolResult.fail(f"Erro ao listar modelos: {str(e)}")

    def _embeddings(self, text: str, model: str = "nomic-embed-text") -> ToolResult:
        """
        Gera embeddings.

        Args:
            text: Texto para embedding
            model: Modelo de embedding

        Returns:
            ToolResult com embedding
        """
        try:
            import requests

            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": model,
                    "prompt": text,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            embedding = data.get("embedding", [])

            return ToolResult.ok({
                "model": model,
                "embedding": embedding,
                "dimensions": len(embedding),
            })
        except requests.exceptions.ConnectionError:
            return ToolResult.fail("Ollama não está rodando. Inicie com: ollama serve")
        except Exception as e:
            return ToolResult.fail(f"Erro ao gerar embeddings: {str(e)}")
