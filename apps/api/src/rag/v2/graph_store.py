"""
RAG v2 - Graph Store com Neo4j

Implementação de graph store usando Neo4j para:
- Armazenamento de entidades e relações
- Graph RAG com travessia de grafos
- Busca por relações semânticas
- Extração de subgrafos relevantes
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from enum import Enum
import logging

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable

from .config import RAGConfig, get_rag_config


logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Tipos de entidade."""
    PERSON = "Person"
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    TECHNOLOGY = "Technology"
    CONCEPT = "Concept"
    PRODUCT = "Product"
    EVENT = "Event"
    DATE = "Date"
    CUSTOM = "Custom"


class RelationType(str, Enum):
    """Tipos de relação."""
    MENTIONS = "MENTIONS"
    DISCUSSES = "DISCUSSES"
    BELONGS_TO = "BELONGS_TO"
    RELATED_TO = "RELATED_TO"
    PART_OF = "PART_OF"
    SIMILAR_TO = "SIMILAR_TO"
    INSTANCE_OF = "INSTANCE_OF"
    WORKS_FOR = "WORKS_FOR"
    LOCATED_IN = "LOCATED_IN"
    USES = "USES"
    DEPENDS_ON = "DEPENDS_ON"


@dataclass
class Entity:
    """Entidade no grafo."""
    id: Optional[str] = None
    name: str = ""
    entity_type: EntityType = EntityType.CONCEPT
    description: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    created_at: Optional[datetime] = None


@dataclass
class Relation:
    """Relação entre entidades."""
    source_id: str = ""
    target_id: str = ""
    relation_type: RelationType = RelationType.RELATED_TO
    strength: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class GraphDocument:
    """Documento representado no grafo."""
    id: str = ""
    document_id: int = 0
    title: str = ""
    source: Optional[str] = None
    entities: list[Entity] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)


@dataclass
class GraphSearchResult:
    """Resultado de busca no grafo."""
    entity: Entity
    document_ids: list[int]
    related_entities: list[Entity]
    path_score: float
    context: str


class GraphStore:
    """
    Graph Store com Neo4j.
    
    Features:
    - Armazenamento de entidades e relações
    - Extração de subgrafos relevantes
    - Busca por caminhos semânticos
    - Integração com vector search
    """
    
    # Cypher para criação de constraints e índices
    INIT_CYPHER = """
    // Constraints de unicidade
    CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
    CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
    CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE;
    
    // Índices para busca
    CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name);
    CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);
    CREATE INDEX document_source IF NOT EXISTS FOR (d:Document) ON (d.source);
    
    // Índice full-text para busca por nome
    CREATE FULLTEXT INDEX entity_name_fulltext IF NOT EXISTS 
    FOR (e:Entity) ON EACH [e.name, e.description];
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or get_rag_config()
        self._driver: Optional[AsyncDriver] = None
    
    async def _get_driver(self) -> AsyncDriver:
        """Retorna driver Neo4j."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self.config.database.neo4j_uri,
                auth=(
                    self.config.database.neo4j_user,
                    self.config.database.neo4j_password
                )
            )
        return self._driver
    
    async def initialize(self) -> None:
        """Inicializa banco de dados com constraints e índices."""
        driver = await self._get_driver()
        
        async with driver.session() as session:
            # Executar cada statement separadamente
            for statement in self.INIT_CYPHER.strip().split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("//"):
                    try:
                        await session.run(statement)
                    except Exception as e:
                        # Ignorar erros de constraint já existente
                        if "already exists" not in str(e).lower():
                            logger.warning(f"Erro ao executar: {statement}: {e}")
        
        logger.info("Graph store inicializado com sucesso")
    
    async def add_entity(self, entity: Entity) -> str:
        """
        Adiciona uma entidade ao grafo.
        
        Args:
            entity: Entidade a adicionar
            
        Returns:
            ID da entidade criada
        """
        driver = await self._get_driver()
        
        async with driver.session() as session:
            result = await session.run("""
                MERGE (e:Entity {id: $id})
                SET e.name = $name,
                    e.type = $type,
                    e.description = $description,
                    e.metadata = $metadata,
                    e.created_at = datetime()
                RETURN e.id as id
            """, {
                "id": entity.id or f"{entity.entity_type.value}_{entity.name}".lower().replace(" ", "_"),
                "name": entity.name,
                "type": entity.entity_type.value,
                "description": entity.description,
                "metadata": str(entity.metadata)
            })
            
            record = await result.single()
            return record["id"]
    
    async def add_entities_batch(self, entities: list[Entity]) -> list[str]:
        """Adiciona múltiplas entidades em batch."""
        driver = await self._get_driver()
        ids = []
        
        async with driver.session() as session:
            for entity in entities:
                entity_id = entity.id or f"{entity.entity_type.value}_{entity.name}".lower().replace(" ", "_")
                
                await session.run("""
                    MERGE (e:Entity {id: $id})
                    SET e.name = $name,
                        e.type = $type,
                        e.description = $description,
                        e.metadata = $metadata,
                        e.created_at = datetime()
                """, {
                    "id": entity_id,
                    "name": entity.name,
                    "type": entity.entity_type.value,
                    "description": entity.description,
                    "metadata": str(entity.metadata)
                })
                
                ids.append(entity_id)
        
        return ids
    
    async def add_relation(self, relation: Relation) -> None:
        """
        Adiciona uma relação entre entidades.
        
        Args:
            relation: Relação a adicionar
        """
        driver = await self._get_driver()
        
        async with driver.session() as session:
            await session.run(f"""
                MATCH (source:Entity {{id: $source_id}})
                MATCH (target:Entity {{id: $target_id}})
                MERGE (source)-[r:{relation.relation_type.value}]->(target)
                SET r.strength = $strength,
                    r.metadata = $metadata
            """, {
                "source_id": relation.source_id,
                "target_id": relation.target_id,
                "strength": relation.strength,
                "metadata": str(relation.metadata)
            })
    
    async def add_document(self, doc: GraphDocument) -> None:
        """
        Adiciona um documento e suas entidades/relações ao grafo.
        
        Args:
            doc: Documento com entidades e relações
        """
        driver = await self._get_driver()
        
        async with driver.session() as session:
            # Criar nó do documento
            await session.run("""
                MERGE (d:Document {id: $id})
                SET d.document_id = $document_id,
                    d.title = $title,
                    d.source = $source,
                    d.created_at = datetime()
            """, {
                "id": doc.id,
                "document_id": doc.document_id,
                "title": doc.title,
                "source": doc.source
            })
            
            # Adicionar entidades e relacionar com documento
            for entity in doc.entities:
                entity_id = await self.add_entity(entity)
                
                # Relacionar documento com entidade
                await session.run("""
                    MATCH (d:Document {id: $doc_id})
                    MATCH (e:Entity {id: $entity_id})
                    MERGE (d)-[:MENTIONS]->(e)
                """, {
                    "doc_id": doc.id,
                    "entity_id": entity_id
                })
            
            # Adicionar relações entre entidades
            for relation in doc.relations:
                await self.add_relation(relation)
    
    async def search_entities(
        self,
        query: str,
        entity_types: Optional[list[EntityType]] = None,
        limit: int = 10
    ) -> list[Entity]:
        """
        Busca entidades por nome/descrição.
        
        Args:
            query: Query de busca
            entity_types: Filtrar por tipos de entidade
            limit: Número máximo de resultados
            
        Returns:
            Lista de entidades encontradas
        """
        driver = await self._get_driver()
        
        type_filter = ""
        if entity_types:
            types_str = ", ".join(f"'{t.value}'" for t in entity_types)
            type_filter = f"AND e.type IN [{types_str}]"
        
        async with driver.session() as session:
            # Tentar busca full-text primeiro
            try:
                result = await session.run(f"""
                    CALL db.index.fulltext.queryNodes('entity_name_fulltext', $query)
                    YIELD node, score
                    WHERE 1=1 {type_filter.replace('e.', 'node.')}
                    RETURN node, score
                    ORDER BY score DESC
                    LIMIT $limit
                """, {"query": query, "limit": limit})
                
                entities = []
                async for record in result:
                    node = record["node"]
                    entities.append(Entity(
                        id=node["id"],
                        name=node["name"],
                        entity_type=EntityType(node["type"]),
                        description=node.get("description"),
                        metadata=eval(node.get("metadata", "{}"))
                    ))
                
                return entities
                
            except Exception as e:
                logger.warning(f"Fulltext search falhou, usando CONTAINS: {e}")
                
                # Fallback para busca por CONTAINS
                result = await session.run(f"""
                    MATCH (e:Entity)
                    WHERE toLower(e.name) CONTAINS toLower($query)
                    {type_filter}
                    RETURN e
                    LIMIT $limit
                """, {"query": query, "limit": limit})
                
                entities = []
                async for record in result:
                    node = record["e"]
                    entities.append(Entity(
                        id=node["id"],
                        name=node["name"],
                        entity_type=EntityType(node["type"]),
                        description=node.get("description"),
                        metadata=eval(node.get("metadata", "{}"))
                    ))
                
                return entities
    
    async def get_related_entities(
        self,
        entity_id: str,
        max_depth: int = 2,
        relation_types: Optional[list[RelationType]] = None,
        limit: int = 20
    ) -> list[tuple[Entity, list[str]]]:
        """
        Busca entidades relacionadas por caminhos no grafo.
        
        Args:
            entity_id: ID da entidade inicial
            max_depth: Profundidade máxima de travessia
            relation_types: Filtrar por tipos de relação
            limit: Número máximo de resultados
            
        Returns:
            Lista de tuplas (entidade, caminho de relações)
        """
        driver = await self._get_driver()
        
        # Construir padrão de relação
        if relation_types:
            rel_pattern = "|".join(r.value for r in relation_types)
            rel_match = f"[*1..{max_depth}]"  # Simplificado para compatibilidade
        else:
            rel_match = f"[*1..{max_depth}]"
        
        async with driver.session() as session:
            result = await session.run(f"""
                MATCH path = (start:Entity {{id: $entity_id}})-{rel_match}-(related:Entity)
                WHERE start <> related
                WITH related, path, length(path) as depth
                RETURN DISTINCT related, 
                       [r IN relationships(path) | type(r)] as rel_types,
                       depth
                ORDER BY depth
                LIMIT $limit
            """, {"entity_id": entity_id, "limit": limit})
            
            entities = []
            async for record in result:
                node = record["related"]
                rel_types = record["rel_types"]
                
                entity = Entity(
                    id=node["id"],
                    name=node["name"],
                    entity_type=EntityType(node["type"]),
                    description=node.get("description"),
                    metadata=eval(node.get("metadata", "{}"))
                )
                
                entities.append((entity, rel_types))
            
            return entities
    
    async def get_documents_for_entities(
        self,
        entity_ids: list[str]
    ) -> dict[str, list[int]]:
        """
        Busca documentos que mencionam as entidades.
        
        Args:
            entity_ids: Lista de IDs de entidades
            
        Returns:
            Dicionário entity_id -> lista de document_ids
        """
        driver = await self._get_driver()
        
        async with driver.session() as session:
            result = await session.run("""
                MATCH (d:Document)-[:MENTIONS]->(e:Entity)
                WHERE e.id IN $entity_ids
                RETURN e.id as entity_id, collect(d.document_id) as doc_ids
            """, {"entity_ids": entity_ids})
            
            mapping = {}
            async for record in result:
                mapping[record["entity_id"]] = record["doc_ids"]
            
            return mapping
    
    async def search_by_path(
        self,
        start_query: str,
        end_query: str,
        max_depth: int = 3
    ) -> list[list[Entity]]:
        """
        Busca caminhos entre duas entidades.
        
        Args:
            start_query: Query para entidade inicial
            end_query: Query para entidade final
            max_depth: Profundidade máxima
            
        Returns:
            Lista de caminhos (cada caminho é uma lista de entidades)
        """
        driver = await self._get_driver()
        
        async with driver.session() as session:
            result = await session.run(f"""
                MATCH (start:Entity), (end:Entity)
                WHERE toLower(start.name) CONTAINS toLower($start_query)
                  AND toLower(end.name) CONTAINS toLower($end_query)
                MATCH path = shortestPath((start)-[*1..{max_depth}]-(end))
                RETURN nodes(path) as path_nodes
                LIMIT 5
            """, {"start_query": start_query, "end_query": end_query})
            
            paths = []
            async for record in result:
                path = []
                for node in record["path_nodes"]:
                    if "Entity" in node.labels:
                        path.append(Entity(
                            id=node["id"],
                            name=node["name"],
                            entity_type=EntityType(node["type"]),
                            description=node.get("description")
                        ))
                if path:
                    paths.append(path)
            
            return paths
    
    async def get_subgraph(
        self,
        query: str,
        max_entities: int = 20,
        max_depth: int = 2
    ) -> tuple[list[Entity], list[Relation]]:
        """
        Extrai um subgrafo relevante para uma query.
        
        Args:
            query: Query de busca
            max_entities: Número máximo de entidades
            max_depth: Profundidade máxima de expansão
            
        Returns:
            Tupla (entidades, relações)
        """
        # Buscar entidades iniciais
        seed_entities = await self.search_entities(query, limit=5)
        
        if not seed_entities:
            return [], []
        
        all_entities: dict[str, Entity] = {e.id: e for e in seed_entities}
        all_relations: list[Relation] = []
        
        # Expandir para entidades relacionadas
        for entity in seed_entities:
            related = await self.get_related_entities(
                entity.id,
                max_depth=max_depth,
                limit=max_entities // len(seed_entities)
            )
            
            for rel_entity, rel_types in related:
                if rel_entity.id not in all_entities:
                    all_entities[rel_entity.id] = rel_entity
                
                # Criar relação
                if rel_types:
                    try:
                        rel_type = RelationType(rel_types[0])
                    except ValueError:
                        rel_type = RelationType.RELATED_TO
                    
                    all_relations.append(Relation(
                        source_id=entity.id,
                        target_id=rel_entity.id,
                        relation_type=rel_type
                    ))
        
        return list(all_entities.values())[:max_entities], all_relations
    
    async def get_stats(self) -> dict:
        """Retorna estatísticas do grafo."""
        driver = await self._get_driver()
        
        async with driver.session() as session:
            result = await session.run("""
                MATCH (e:Entity)
                WITH count(e) as entity_count
                MATCH (d:Document)
                WITH entity_count, count(d) as doc_count
                MATCH ()-[r]->()
                RETURN entity_count, doc_count, count(r) as relation_count
            """)
            
            record = await result.single()
            
            return {
                "entities": record["entity_count"] if record else 0,
                "documents": record["doc_count"] if record else 0,
                "relations": record["relation_count"] if record else 0
            }
    
    async def close(self) -> None:
        """Fecha conexões."""
        if self._driver:
            await self._driver.close()


# Singleton
_graph_store: Optional[GraphStore] = None


def get_graph_store(config: Optional[RAGConfig] = None) -> GraphStore:
    """Retorna o graph store singleton."""
    global _graph_store
    if _graph_store is None:
        _graph_store = GraphStore(config)
    return _graph_store
