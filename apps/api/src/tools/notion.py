"""
Ferramenta de integração com Notion.

Permite criar páginas, databases e gerenciar conteúdo no Notion.
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx

from .base import BaseTool


class NotionTool(BaseTool):
    """
    Ferramenta para integração com Notion.
    
    Funcionalidades:
    - Criar páginas
    - Criar entradas em databases
    - Buscar conteúdo
    - Atualizar páginas
    - Listar databases
    
    Configuração:
        Requer NOTION_TOKEN no ambiente (Integration Token).
        Opcionalmente NOTION_DEFAULT_DATABASE_ID.
    """
    
    name = "notion"
    description = "Gerencia páginas e databases no Notion"
    
    NOTION_VERSION = "2022-06-28"
    
    def __init__(
        self,
        token: Optional[str] = None,
        default_database_id: Optional[str] = None
    ):
        self.token = token or os.getenv("NOTION_TOKEN")
        self.default_database_id = default_database_id or os.getenv("NOTION_DEFAULT_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
        
        if not self.token:
            raise ValueError(
                "NOTION_TOKEN não configurado. "
                "Crie uma integração em https://www.notion.so/my-integrations"
            )
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_VERSION,
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Faz uma requisição à API do Notion."""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}/{endpoint}",
                headers=self._headers(),
                **kwargs
            )
            
            if response.status_code >= 400:
                raise Exception(f"Notion API error: {response.status_code} - {response.text}")
            
            return response.json()
    
    async def create_page(
        self,
        title: str,
        content: str,
        parent_page_id: Optional[str] = None,
        parent_database_id: Optional[str] = None,
        properties: Optional[Dict] = None,
        icon: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria uma nova página no Notion.
        
        Args:
            title: Título da página
            content: Conteúdo em markdown
            parent_page_id: ID da página pai (opcional)
            parent_database_id: ID do database pai (opcional)
            properties: Propriedades adicionais para databases
            icon: Emoji ou URL do ícone
        
        Returns:
            Dados da página criada
        """
        # Determinar parent
        if parent_database_id or self.default_database_id:
            parent = {
                "type": "database_id",
                "database_id": parent_database_id or self.default_database_id
            }
        elif parent_page_id:
            parent = {
                "type": "page_id",
                "page_id": parent_page_id
            }
        else:
            raise ValueError("Necessário parent_page_id ou parent_database_id")
        
        # Construir página
        payload: Dict[str, Any] = {
            "parent": parent,
            "properties": properties or {
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            },
            "children": self._markdown_to_blocks(content)
        }
        
        if icon:
            if icon.startswith("http"):
                payload["icon"] = {"type": "external", "external": {"url": icon}}
            else:
                payload["icon"] = {"type": "emoji", "emoji": icon}
        
        return await self._request("POST", "pages", json=payload)
    
    async def create_database_entry(
        self,
        database_id: Optional[str] = None,
        properties: Dict[str, Any] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria uma entrada em um database.
        
        Args:
            database_id: ID do database
            properties: Propriedades da entrada (formato Notion)
            content: Conteúdo opcional da página
        
        Returns:
            Dados da entrada criada
        """
        db_id = database_id or self.default_database_id
        if not db_id:
            raise ValueError("database_id necessário")
        
        payload: Dict[str, Any] = {
            "parent": {"database_id": db_id},
            "properties": properties or {},
        }
        
        if content:
            payload["children"] = self._markdown_to_blocks(content)
        
        return await self._request("POST", "pages", json=payload)
    
    async def search(
        self,
        query: str,
        filter_type: Optional[str] = None,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca conteúdo no Notion.
        
        Args:
            query: Termo de busca
            filter_type: Filtrar por tipo (page, database)
            page_size: Número de resultados
        
        Returns:
            Lista de resultados
        """
        payload: Dict[str, Any] = {
            "query": query,
            "page_size": page_size,
        }
        
        if filter_type:
            payload["filter"] = {"property": "object", "value": filter_type}
        
        data = await self._request("POST", "search", json=payload)
        return data.get("results", [])
    
    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """Obtém uma página pelo ID."""
        return await self._request("GET", f"pages/{page_id}")
    
    async def update_page(
        self,
        page_id: str,
        properties: Optional[Dict] = None,
        archived: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Atualiza uma página.
        
        Args:
            page_id: ID da página
            properties: Propriedades a atualizar
            archived: Se deve arquivar a página
        
        Returns:
            Página atualizada
        """
        payload: Dict[str, Any] = {}
        
        if properties:
            payload["properties"] = properties
        if archived is not None:
            payload["archived"] = archived
        
        return await self._request("PATCH", f"pages/{page_id}", json=payload)
    
    async def list_databases(self) -> List[Dict[str, Any]]:
        """Lista databases acessíveis."""
        data = await self._request("POST", "search", json={
            "filter": {"property": "object", "value": "database"},
            "page_size": 100
        })
        return data.get("results", [])
    
    async def query_database(
        self,
        database_id: Optional[str] = None,
        filter_obj: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Consulta um database.
        
        Args:
            database_id: ID do database
            filter_obj: Filtros no formato Notion
            sorts: Ordenação
            page_size: Tamanho da página
        
        Returns:
            Lista de entradas
        """
        db_id = database_id or self.default_database_id
        if not db_id:
            raise ValueError("database_id necessário")
        
        payload: Dict[str, Any] = {"page_size": page_size}
        
        if filter_obj:
            payload["filter"] = filter_obj
        if sorts:
            payload["sorts"] = sorts
        
        data = await self._request("POST", f"databases/{db_id}/query", json=payload)
        return data.get("results", [])
    
    def _markdown_to_blocks(self, markdown: str) -> List[Dict]:
        """Converte markdown simples para blocos Notion."""
        blocks = []
        lines = markdown.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Headers
            if line.startswith("### "):
                blocks.append({
                    "type": "heading_3",
                    "heading_3": {"rich_text": [{"text": {"content": line[4:]}}]}
                })
            elif line.startswith("## "):
                blocks.append({
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": line[3:]}}]}
                })
            elif line.startswith("# "):
                blocks.append({
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"text": {"content": line[2:]}}]}
                })
            # Bullet points
            elif line.startswith("- ") or line.startswith("* "):
                blocks.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"text": {"content": line[2:]}}]}
                })
            # Numbered lists
            elif line[0].isdigit() and line[1:3] in [". ", ") "]:
                blocks.append({
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": [{"text": {"content": line[3:]}}]}
                })
            # Code blocks
            elif line.startswith("```"):
                continue  # Simplified - skip code block markers
            # Regular paragraph
            else:
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": line}}]}
                })
        
        return blocks
    
    def run(self, action: str, **kwargs) -> str:
        """
        Executa uma ação do Notion (síncrono para compatibilidade com agentes).
        
        Args:
            action: Ação (create_page, search, query, list_databases)
            **kwargs: Argumentos da ação
        """
        import asyncio
        
        if action == "create_page":
            result = asyncio.run(self.create_page(**kwargs))
        elif action == "create_entry":
            result = asyncio.run(self.create_database_entry(**kwargs))
        elif action == "search":
            result = asyncio.run(self.search(**kwargs))
        elif action == "query":
            result = asyncio.run(self.query_database(**kwargs))
        elif action == "get_page":
            result = asyncio.run(self.get_page(**kwargs))
        elif action == "update_page":
            result = asyncio.run(self.update_page(**kwargs))
        elif action == "list_databases":
            result = asyncio.run(self.list_databases())
        else:
            return f"Ação desconhecida: {action}"
        
        return json.dumps(result, indent=2, default=str)


# Helper para criar propriedades de database
def notion_property(prop_type: str, value: Any) -> Dict:
    """
    Cria uma propriedade no formato Notion.
    
    Args:
        prop_type: Tipo (title, rich_text, number, select, date, checkbox)
        value: Valor da propriedade
    """
    if prop_type == "title":
        return {"title": [{"text": {"content": str(value)}}]}
    elif prop_type == "rich_text":
        return {"rich_text": [{"text": {"content": str(value)}}]}
    elif prop_type == "number":
        return {"number": float(value)}
    elif prop_type == "select":
        return {"select": {"name": str(value)}}
    elif prop_type == "multi_select":
        return {"multi_select": [{"name": v} for v in value]}
    elif prop_type == "date":
        return {"date": {"start": str(value)}}
    elif prop_type == "checkbox":
        return {"checkbox": bool(value)}
    elif prop_type == "url":
        return {"url": str(value)}
    elif prop_type == "email":
        return {"email": str(value)}
    else:
        return {"rich_text": [{"text": {"content": str(value)}}]}


def get_notion_tool(token: Optional[str] = None) -> NotionTool:
    """Factory para criar NotionTool."""
    return NotionTool(token=token)
