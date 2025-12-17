"""
GraphRAG Engine - RAG baseado em Knowledge Graph com Neo4j.

Sprint 3: GraphRAG + Neo4j Integration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from ..core.types import DomainType, RAGSource

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Entidade no Knowledge Graph."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@dataclass
class Relationship:
    """Relacionamento entre entidades."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    type: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


@dataclass
class SubGraph:
    """Subgrafo extraído para contexto."""
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    central_entity: Optional[Entity] = None
    depth: int = 0


@dataclass
class GraphRAGResult:
    """Resultado do GraphRAG."""
    query: str = ""
    answer: str = ""
    
    # Graph context
    entities_found: List[Entity] = field(default_factory=list)
    subgraph: Optional[SubGraph] = None
    
    # Document sources
    document_sources: List[RAGSource] = field(default_factory=list)
    
    # Metrics
    confidence: float = 0.0
    entity_coverage: float = 0.0
    relationship_coverage: float = 0.0
    
    # Performance
    latency_ms: float = 0.0


class GraphRAGEngine:
    """
    Engine de GraphRAG - combina Knowledge Graph com RAG tradicional.
    
    Features:
    - Entity extraction from queries
    - Subgraph retrieval
    - Multi-hop reasoning
    - Graph + Vector hybrid search
    - Entity-aware answer generation
    """
    
    def __init__(
        self,
        domain: DomainType,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None
    ):
        self.domain = domain
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        # In-memory graph for development
        self._entities: Dict[str, Entity] = {}
        self._relationships: Dict[str, Relationship] = {}
        self._entity_index: Dict[str, Set[str]] = {}  # type -> entity_ids
        
        # Components
        self.entity_extractor = EntityExtractor()
        self.graph_traverser = GraphTraverser(self)
        self.hybrid_ranker = HybridRanker()
        
        logger.info("GraphRAGEngine initialized for domain: %s", domain.value)
    
    # ============================================================
    # GRAPH OPERATIONS
    # ============================================================
    
    def add_entity(self, entity: Entity) -> str:
        """Add entity to the graph."""
        self._entities[entity.id] = entity
        
        # Index by type
        if entity.type not in self._entity_index:
            self._entity_index[entity.type] = set()
        self._entity_index[entity.type].add(entity.id)
        
        logger.debug("Added entity: %s (%s)", entity.name, entity.type)
        return entity.id
    
    def add_relationship(self, relationship: Relationship) -> str:
        """Add relationship to the graph."""
        self._relationships[relationship.id] = relationship
        logger.debug("Added relationship: %s -[%s]-> %s",
                    relationship.source_id, relationship.type, relationship.target_id)
        return relationship.id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self._entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a type."""
        ids = self._entity_index.get(entity_type, set())
        return [self._entities[eid] for eid in ids if eid in self._entities]
    
    def get_neighbors(
        self,
        entity_id: str,
        relationship_types: Optional[List[str]] = None,
        direction: str = "both"  # in, out, both
    ) -> List[Tuple[Entity, Relationship]]:
        """Get neighboring entities."""
        neighbors = []
        
        for rel in self._relationships.values():
            if relationship_types and rel.type not in relationship_types:
                continue
            
            if direction in ("out", "both") and rel.source_id == entity_id:
                target = self._entities.get(rel.target_id)
                if target:
                    neighbors.append((target, rel))
            
            if direction in ("in", "both") and rel.target_id == entity_id:
                source = self._entities.get(rel.source_id)
                if source:
                    neighbors.append((source, rel))
        
        return neighbors
    
    def get_subgraph(
        self,
        seed_entity_ids: List[str],
        depth: int = 2,
        max_nodes: int = 50
    ) -> SubGraph:
        """Extract subgraph around seed entities."""
        visited = set(seed_entity_ids)
        entities = [self._entities[eid] for eid in seed_entity_ids if eid in self._entities]
        relationships = []
        
        frontier = list(seed_entity_ids)
        
        for d in range(depth):
            if len(entities) >= max_nodes:
                break
            
            new_frontier = []
            for entity_id in frontier:
                neighbors = self.get_neighbors(entity_id)
                for neighbor, rel in neighbors:
                    if neighbor.id not in visited and len(entities) < max_nodes:
                        visited.add(neighbor.id)
                        entities.append(neighbor)
                        relationships.append(rel)
                        new_frontier.append(neighbor.id)
            
            frontier = new_frontier
        
        return SubGraph(
            entities=entities,
            relationships=relationships,
            central_entity=entities[0] if entities else None,
            depth=depth
        )
    
    # ============================================================
    # QUERY
    # ============================================================
    
    async def query(
        self,
        query: str,
        depth: int = 2,
        include_documents: bool = True,
        top_k: int = 10
    ) -> GraphRAGResult:
        """
        Execute GraphRAG query.
        
        1. Extract entities from query
        2. Find matching entities in graph
        3. Retrieve relevant subgraph
        4. Combine with document search
        5. Generate answer with graph context
        """
        start_time = datetime.now()
        result = GraphRAGResult(query=query)
        
        logger.info("GraphRAG query: %s", query[:100])
        
        # Step 1: Extract entities from query
        extracted_entities = await self.entity_extractor.extract(query)
        logger.debug("Extracted %d entities from query", len(extracted_entities))
        
        # Step 2: Find matching entities in graph
        matched_entities = self._match_entities(extracted_entities)
        result.entities_found = matched_entities
        logger.debug("Matched %d entities in graph", len(matched_entities))
        
        # Step 3: Retrieve subgraph if entities found
        if matched_entities:
            entity_ids = [e.id for e in matched_entities]
            subgraph = self.get_subgraph(entity_ids, depth=depth)
            result.subgraph = subgraph
            logger.debug("Retrieved subgraph with %d entities", len(subgraph.entities))
        
        # Step 4: Search documents (if enabled)
        if include_documents:
            doc_sources = await self._search_documents(query, top_k)
            result.document_sources = doc_sources
        
        # Step 5: Generate answer
        answer = await self._generate_answer(
            query=query,
            subgraph=result.subgraph,
            documents=result.document_sources
        )
        result.answer = answer["text"]
        result.confidence = answer["confidence"]
        
        # Calculate coverage metrics
        if result.subgraph:
            result.entity_coverage = len(matched_entities) / max(len(extracted_entities), 1)
            result.relationship_coverage = len(result.subgraph.relationships) / max(len(matched_entities), 1)
        
        # Calculate latency
        result.latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info("GraphRAG completed: %d entities, confidence=%.2f, latency=%.0fms",
                   len(matched_entities), result.confidence, result.latency_ms)
        
        return result
    
    def _match_entities(self, extracted: List[Dict]) -> List[Entity]:
        """Match extracted entities to graph entities."""
        matched = []
        
        for ext in extracted:
            name = ext.get("name", "").lower()
            entity_type = ext.get("type", "")
            
            # Search by name similarity
            for entity in self._entities.values():
                if name in entity.name.lower() or entity.name.lower() in name:
                    matched.append(entity)
                    break
        
        return matched
    
    async def _search_documents(
        self,
        query: str,
        top_k: int
    ) -> List[RAGSource]:
        """Search documents (simulated)."""
        # In production, this would use vector search
        return [
            RAGSource(
                id=f"doc_{i}",
                content=f"Document content related to '{query[:30]}...'",
                score=0.9 - (i * 0.1),
                metadata={"source": "graph_rag"}
            )
            for i in range(min(top_k, 3))
        ]
    
    async def _generate_answer(
        self,
        query: str,
        subgraph: Optional[SubGraph],
        documents: List[RAGSource]
    ) -> Dict:
        """Generate answer with graph context."""
        # Build context
        context_parts = []
        
        if subgraph and subgraph.entities:
            entity_context = "Entities found:\n"
            for entity in subgraph.entities[:10]:
                entity_context += f"- {entity.name} ({entity.type})\n"
            context_parts.append(entity_context)
            
            if subgraph.relationships:
                rel_context = "Relationships:\n"
                for rel in subgraph.relationships[:10]:
                    source = self._entities.get(rel.source_id)
                    target = self._entities.get(rel.target_id)
                    if source and target:
                        rel_context += f"- {source.name} --[{rel.type}]--> {target.name}\n"
                context_parts.append(rel_context)
        
        if documents:
            doc_context = "Document sources:\n"
            for doc in documents[:5]:
                doc_context += f"- {doc.content[:100]}...\n"
            context_parts.append(doc_context)
        
        # Generate answer (simulated)
        answer = f"Based on the knowledge graph and documents about '{query[:50]}':\n\n"
        if subgraph:
            answer += f"Found {len(subgraph.entities)} related entities "
            answer += f"with {len(subgraph.relationships)} relationships. "
        answer += "The analysis indicates comprehensive coverage of the topic."
        
        return {
            "text": answer,
            "confidence": 0.85 if subgraph else 0.65
        }
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_entities": len(self._entities),
            "total_relationships": len(self._relationships),
            "entity_types": list(self._entity_index.keys()),
            "entities_by_type": {
                t: len(ids) for t, ids in self._entity_index.items()
            }
        }


# ============================================================
# SUPPORTING CLASSES
# ============================================================

class EntityExtractor:
    """Extracts entities from text."""
    
    async def extract(self, text: str) -> List[Dict]:
        """Extract entities from text."""
        # Simple extraction (in production, use NER model)
        entities = []
        
        # Look for capitalized words as potential entities
        words = text.split()
        for word in words:
            if word and word[0].isupper() and len(word) > 2:
                entities.append({
                    "name": word.strip(".,!?"),
                    "type": "unknown"
                })
        
        return entities


class GraphTraverser:
    """Traverses knowledge graph for relevant context."""
    
    def __init__(self, engine: GraphRAGEngine):
        self.engine = engine
    
    async def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 3
    ) -> List[List[str]]:
        """Find paths between two entities."""
        paths = []
        
        def dfs(current: str, target: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            if current == target:
                paths.append(path.copy())
                return
            
            neighbors = self.engine.get_neighbors(current, direction="out")
            for neighbor, rel in neighbors:
                if neighbor.id not in path:
                    path.append(neighbor.id)
                    dfs(neighbor.id, target, path, depth + 1)
                    path.pop()
        
        dfs(source_id, target_id, [source_id], 0)
        return paths


class HybridRanker:
    """Ranks results combining graph and vector scores."""
    
    def rank(
        self,
        graph_entities: List[Entity],
        vector_results: List[RAGSource],
        alpha: float = 0.5  # Weight for graph vs vector
    ) -> List[Dict]:
        """Hybrid ranking of results."""
        results = []
        
        # Score graph entities
        for entity in graph_entities:
            results.append({
                "id": entity.id,
                "type": "entity",
                "name": entity.name,
                "score": alpha * 0.8  # Base entity score
            })
        
        # Score vector results
        for source in vector_results:
            results.append({
                "id": source.id,
                "type": "document",
                "content": source.content[:100],
                "score": (1 - alpha) * source.score
            })
        
        # Sort by combined score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results


# ============================================================
# FACTORY
# ============================================================

def create_graph_rag(domain: DomainType, **kwargs) -> GraphRAGEngine:
    """Factory function to create GraphRAG engine."""
    return GraphRAGEngine(domain=domain, **kwargs)
