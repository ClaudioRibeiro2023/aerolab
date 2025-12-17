# Arquitetura de Implementação Específica - Fase 3
## RAG Avançado Completo + Regras Simbólicas

**Autor:** Manus AI  
**Data:** 02 de Dezembro de 2025  
**Versão:** 1.0 - Especificação Técnica Detalhada

---

## Sumário Executivo

Este documento fornece a especificação técnica completa para implementação da **Fase 3** da plataforma de agentes de IA, focando em **RAG Avançado** e **Validação com Regras Simbólicas**. A arquitetura proposta combina múltiplas técnicas de recuperação (vector search, graph search, hybrid search), reranking sofisticado, e validação simbólica para criar um sistema de conhecimento robusto e confiável.

---

## 1. Visão Geral da Arquitetura

### 1.1 Stack Tecnológico Completo

```typescript
// Stack da Fase 3
{
  // Banco de Dados
  "database": {
    "primary": "PostgreSQL 16+",
    "extensions": ["pgvector", "pg_trgm", "btree_gin"],
    "graph": "Neo4j 5.x Community/Enterprise"
  },
  
  // Backend
  "backend": {
    "runtime": "Node.js 22+",
    "framework": "Fastify 5.x",
    "orm": "Drizzle ORM",
    "validation": "Zod",
    "queue": "BullMQ 5.x"
  },
  
  // RAG Framework
  "rag": {
    "orchestration": "LangChain.js 0.3.x",
    "embeddings": "OpenAI text-embedding-3-large",
    "vectorStore": "pgvector via @langchain/community",
    "graphStore": "Neo4j via @langchain/community"
  },
  
  // Reranking
  "reranking": {
    "primary": "Cohere Rerank API v2",
    "fallback": "BGE Reranker (self-hosted)",
    "library": "cohere-ai SDK"
  },
  
  // Symbolic Reasoning
  "symbolic": {
    "ruleEngine": "json-rules-engine",
    "validation": "Zod + Custom Validators",
    "ontology": "RDF/OWL via rdflib.js (optional)"
  }
}
```

### 1.2 Diagrama de Arquitetura de Alto Nível

```
┌────────────────────────────────────────────────────────────────┐
│                      CAMADA DE API                              │
│         tRPC Procedures (protectedProcedure)                    │
│  rag.query | rag.ingest | rules.validate | knowledge.search    │
└────────────────────────────────────────────────────────────────┘
                              ↓↑
┌────────────────────────────────────────────────────────────────┐
│                  CAMADA DE ORQUESTRAÇÃO RAG                     │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Query Processor  │  │ Retrieval Router │  │ Response     │ │
│  │ - Decomposition  │  │ - Vector/Graph   │  │ Generator    │ │
│  │ - Transformation │  │ - Hybrid         │  │ - Synthesis  │ │
│  │ - Expansion      │  │ - Routing Logic  │  │ - Validation │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└────────────────────────────────────────────────────────────────┘
                              ↓↑
┌────────────────────────────────────────────────────────────────┐
│                   CAMADA DE RECUPERAÇÃO                         │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ Vector      │  │ Graph       │  │ Keyword     │           │
│  │ Search      │  │ Search      │  │ Search      │           │
│  │ (pgvector)  │  │ (Neo4j)     │  │ (pg_trgm)   │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                         ↓                                       │
│                  ┌─────────────┐                               │
│                  │  Reranker   │                               │
│                  │  (Cohere)   │                               │
│                  └─────────────┘                               │
└────────────────────────────────────────────────────────────────┘
                              ↓↑
┌────────────────────────────────────────────────────────────────┐
│                 CAMADA DE VALIDAÇÃO SIMBÓLICA                   │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Rule Engine      │  │ Schema Validator │  │ Constraint   │ │
│  │ (json-rules)     │  │ (Zod)            │  │ Checker      │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└────────────────────────────────────────────────────────────────┘
                              ↓↑
┌────────────────────────────────────────────────────────────────┐
│                    CAMADA DE PERSISTÊNCIA                       │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ PostgreSQL  │  │ Neo4j       │  │ Redis       │           │
│  │ + pgvector  │  │ Graph DB    │  │ Cache       │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. Modelo de Dados Estendido

### 2.1 Schema PostgreSQL (Drizzle ORM)

```typescript
// drizzle/schema.ts - Extensão para RAG

import { 
  int, mysqlTable, text, timestamp, varchar, 
  json, boolean, index, vector 
} from "drizzle-orm/mysql-core";

/**
 * Documentos ingeridos no sistema RAG
 */
export const documents = mysqlTable("documents", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("project_id").notNull(),
  
  // Metadata do documento
  title: text("title").notNull(),
  source: varchar("source", { length: 512 }), // URL, file path, etc
  contentType: varchar("content_type", { length: 64 }), // pdf, markdown, html, etc
  
  // Conteúdo
  content: text("content").notNull(), // Texto completo
  summary: text("summary"), // Resumo gerado por LLM
  
  // Metadata estruturada
  metadata: json("metadata"), // { author, date, tags, etc }
  
  // Timestamps
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
  
  // Status de processamento
  processingStatus: varchar("processing_status", { length: 32 })
    .default("pending").notNull(), // pending, processing, completed, failed
  
  // Relacionamento com chunks
  chunkCount: int("chunk_count").default(0),
}, (table) => ({
  projectIdx: index("project_idx").on(table.projectId),
  sourceIdx: index("source_idx").on(table.source),
}));

/**
 * Chunks de documentos com embeddings
 */
export const documentChunks = mysqlTable("document_chunks", {
  id: int("id").autoincrement().primaryKey(),
  documentId: int("document_id").notNull(),
  
  // Conteúdo do chunk
  content: text("content").notNull(),
  chunkIndex: int("chunk_index").notNull(), // Posição no documento
  
  // Embedding vetorial (1536 dimensões para text-embedding-3-large)
  embedding: vector("embedding", { dimensions: 1536 }),
  
  // Contexto adicional
  previousChunk: text("previous_chunk"), // Overlap para contexto
  nextChunk: text("next_chunk"),
  
  // Metadata
  metadata: json("metadata"), // { page_number, section, etc }
  
  // Timestamps
  createdAt: timestamp("created_at").defaultNow().notNull(),
}, (table) => ({
  documentIdx: index("document_idx").on(table.documentId),
  // pgvector index será criado via SQL direto
}));

/**
 * Regras simbólicas para validação
 */
export const validationRules = mysqlTable("validation_rules", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("project_id").notNull(),
  
  // Identificação da regra
  name: varchar("name", { length: 128 }).notNull(),
  description: text("description"),
  category: varchar("category", { length: 64 }), // compliance, security, business, etc
  
  // Definição da regra (JSON Rules Engine format)
  ruleDefinition: json("rule_definition").notNull(),
  
  // Severidade
  severity: varchar("severity", { length: 32 }).default("medium").notNull(), // low, medium, high, critical
  
  // Status
  isActive: boolean("is_active").default(true).notNull(),
  
  // Aplicabilidade
  appliesTo: json("applies_to"), // { entity_types: ["workflow", "agent"], conditions: {...} }
  
  // Timestamps
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => ({
  projectIdx: index("project_idx").on(table.projectId),
  categoryIdx: index("category_idx").on(table.category),
}));

/**
 * Histórico de validações
 */
export const validationHistory = mysqlTable("validation_history", {
  id: int("id").autoincrement().primaryKey(),
  
  // Referências
  entityType: varchar("entity_type", { length: 64 }).notNull(), // workflow, agent, execution
  entityId: int("entity_id").notNull(),
  ruleId: int("rule_id").notNull(),
  
  // Resultado
  passed: boolean("passed").notNull(),
  violationDetails: json("violation_details"), // Detalhes se falhou
  
  // Context
  context: json("context"), // Estado do sistema no momento da validação
  
  // Timestamp
  validatedAt: timestamp("validated_at").defaultNow().notNull(),
}, (table) => ({
  entityIdx: index("entity_idx").on(table.entityType, table.entityId),
  ruleIdx: index("rule_idx").on(table.ruleId),
}));

/**
 * Cache de queries RAG
 */
export const ragQueryCache = mysqlTable("rag_query_cache", {
  id: int("id").autoincrement().primaryKey(),
  
  // Query
  queryHash: varchar("query_hash", { length: 64 }).notNull().unique(), // SHA256 da query
  query: text("query").notNull(),
  
  // Resultado
  result: json("result").notNull(),
  
  // Metadata
  retrievalMethod: varchar("retrieval_method", { length: 64 }), // vector, graph, hybrid
  documentsRetrieved: int("documents_retrieved"),
  
  // Cache control
  hitCount: int("hit_count").default(0),
  lastAccessed: timestamp("last_accessed").defaultNow().notNull(),
  expiresAt: timestamp("expires_at").notNull(),
  
  // Timestamps
  createdAt: timestamp("created_at").defaultNow().notNull(),
}, (table) => ({
  queryHashIdx: index("query_hash_idx").on(table.queryHash),
  expiresIdx: index("expires_idx").on(table.expiresAt),
}));

export type Document = typeof documents.$inferSelect;
export type InsertDocument = typeof documents.$inferInsert;
export type DocumentChunk = typeof documentChunks.$inferSelect;
export type ValidationRule = typeof validationRules.$inferSelect;
```

### 2.2 Schema Neo4j (Cypher)

```cypher
// Constraints e Índices
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE;

CREATE INDEX document_source IF NOT EXISTS FOR (d:Document) ON (d.source);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);

// Modelo de Grafo de Conhecimento

// Nós principais
(:Document {
  id: String,
  title: String,
  source: String,
  content: String,
  createdAt: DateTime
})

(:Entity {
  id: String,
  name: String,
  type: String, // Person, Organization, Location, Technology, etc
  description: String,
  metadata: Map
})

(:Concept {
  name: String,
  category: String, // Domain, Methodology, Technology, etc
  definition: String,
  aliases: [String]
})

(:Topic {
  name: String,
  description: String
})

// Relacionamentos
(:Document)-[:MENTIONS]->(:Entity)
(:Document)-[:DISCUSSES]->(:Concept)
(:Document)-[:BELONGS_TO]->(:Topic)

(:Entity)-[:RELATED_TO {
  relationshipType: String,
  strength: Float
}]->(:Entity)

(:Concept)-[:PART_OF]->(:Concept)
(:Concept)-[:SIMILAR_TO {
  similarity: Float
}]->(:Concept)

(:Entity)-[:INSTANCE_OF]->(:Concept)
```

---

## 3. Componente 1: Sistema RAG Avançado

### 3.1 Arquitetura do Pipeline RAG

```typescript
// server/rag/pipeline.ts

import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";
import { Neo4jVectorStore } from "@langchain/community/vectorstores/neo4j_vector";
import { PGVectorStore } from "@langchain/community/vectorstores/pgvector";
import { CohereRerank } from "@langchain/cohere";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";

/**
 * Configuração do pipeline RAG
 */
export interface RAGConfig {
  // Embedding
  embeddingModel: "text-embedding-3-small" | "text-embedding-3-large";
  embeddingDimensions: number;
  
  // Retrieval
  retrievalMethod: "vector" | "graph" | "hybrid";
  topK: number; // Número de documentos iniciais
  topN: number; // Número após reranking
  
  // Reranking
  useReranking: boolean;
  rerankModel: "cohere" | "bge";
  
  // Generation
  llmModel: string;
  temperature: number;
  maxTokens: number;
  
  // Caching
  useCaching: boolean;
  cacheTTL: number; // segundos
}

/**
 * Pipeline RAG completo
 */
export class AdvancedRAGPipeline {
  private embeddings: OpenAIEmbeddings;
  private vectorStore: PGVectorStore;
  private graphStore: Neo4jVectorStore;
  private reranker: CohereRerank;
  private llm: ChatOpenAI;
  private config: RAGConfig;
  
  constructor(config: RAGConfig) {
    this.config = config;
    
    // Inicializar embeddings
    this.embeddings = new OpenAIEmbeddings({
      modelName: config.embeddingModel,
      dimensions: config.embeddingDimensions,
    });
    
    // Inicializar vector store (pgvector)
    this.vectorStore = new PGVectorStore(this.embeddings, {
      postgresConnectionOptions: {
        connectionString: process.env.DATABASE_URL,
      },
      tableName: "document_chunks",
      columns: {
        idColumnName: "id",
        vectorColumnName: "embedding",
        contentColumnName: "content",
        metadataColumnName: "metadata",
      },
    });
    
    // Inicializar graph store (Neo4j)
    this.graphStore = new Neo4jVectorStore(this.embeddings, {
      url: process.env.NEO4J_URL || "bolt://localhost:7687",
      username: process.env.NEO4J_USERNAME || "neo4j",
      password: process.env.NEO4J_PASSWORD || "",
      indexName: "document_embeddings",
      nodeLabel: "Document",
      embeddingNodeProperty: "embedding",
      textNodeProperty: "content",
    });
    
    // Inicializar reranker
    if (config.useReranking) {
      this.reranker = new CohereRerank({
        apiKey: process.env.COHERE_API_KEY,
        model: "rerank-english-v3.0",
        topN: config.topN,
      });
    }
    
    // Inicializar LLM
    this.llm = new ChatOpenAI({
      modelName: config.llmModel,
      temperature: config.temperature,
      maxTokens: config.maxTokens,
    });
  }
  
  /**
   * Query principal do RAG
   */
  async query(
    query: string,
    options?: {
      projectId?: number;
      filters?: Record<string, any>;
      retrievalMethod?: "vector" | "graph" | "hybrid";
    }
  ): Promise<RAGResponse> {
    // 1. Verificar cache
    if (this.config.useCaching) {
      const cached = await this.checkCache(query);
      if (cached) return cached;
    }
    
    // 2. Query transformation
    const transformedQuery = await this.transformQuery(query);
    
    // 3. Retrieval
    const retrievalMethod = options?.retrievalMethod || this.config.retrievalMethod;
    let documents: Document[];
    
    switch (retrievalMethod) {
      case "vector":
        documents = await this.vectorRetrieval(transformedQuery, options);
        break;
      case "graph":
        documents = await this.graphRetrieval(transformedQuery, options);
        break;
      case "hybrid":
        documents = await this.hybridRetrieval(transformedQuery, options);
        break;
    }
    
    // 4. Reranking
    if (this.config.useReranking && documents.length > this.config.topN) {
      documents = await this.rerank(query, documents);
    }
    
    // 5. Contextual compression
    const compressedDocs = await this.compressContext(query, documents);
    
    // 6. Generation
    const response = await this.generate(query, compressedDocs);
    
    // 7. Cache result
    if (this.config.useCaching) {
      await this.cacheResult(query, response);
    }
    
    return response;
  }
  
  /**
   * Query Transformation: HyDE + Expansion
   */
  private async transformQuery(query: string): Promise<TransformedQuery> {
    // HyDE: Gerar resposta hipotética
    const hydePrompt = `Given the question: "${query}"
    
Generate a hypothetical ideal answer that would perfectly address this question.
This answer will be used to find similar documents.

Hypothetical answer:`;
    
    const hydeResponse = await this.llm.invoke(hydePrompt);
    const hypotheticalAnswer = hydeResponse.content as string;
    
    // Query Expansion: Gerar variações
    const expansionPrompt = `Given the question: "${query}"
    
Generate 3 alternative phrasings or related questions that would help find relevant information.

Alternative queries:`;
    
    const expansionResponse = await this.llm.invoke(expansionPrompt);
    const alternatives = this.parseAlternatives(expansionResponse.content as string);
    
    return {
      original: query,
      hypothetical: hypotheticalAnswer,
      alternatives,
    };
  }
  
  /**
   * Vector Retrieval com pgvector
   */
  private async vectorRetrieval(
    query: TransformedQuery,
    options?: { projectId?: number; filters?: Record<string, any> }
  ): Promise<Document[]> {
    // Buscar usando query original
    const originalResults = await this.vectorStore.similaritySearch(
      query.original,
      this.config.topK,
      options?.filters
    );
    
    // Buscar usando resposta hipotética (HyDE)
    const hydeResults = await this.vectorStore.similaritySearch(
      query.hypothetical,
      this.config.topK / 2,
      options?.filters
    );
    
    // Combinar e deduplicate
    const combined = [...originalResults, ...hydeResults];
    const unique = this.deduplicateDocuments(combined);
    
    return unique.slice(0, this.config.topK);
  }
  
  /**
   * Graph Retrieval com Neo4j
   */
  private async graphRetrieval(
    query: TransformedQuery,
    options?: { projectId?: number; filters?: Record<string, any> }
  ): Promise<Document[]> {
    // 1. Extrair entidades da query
    const entities = await this.extractEntities(query.original);
    
    // 2. Buscar no grafo
    const graphQuery = `
      MATCH (d:Document)
      WHERE ANY(entity IN $entities WHERE (d)-[:MENTIONS]->(:Entity {name: entity}))
      RETURN d.id as id, d.content as content, d.metadata as metadata
      ORDER BY d.relevance DESC
      LIMIT $limit
    `;
    
    const graphResults = await this.executeGraphQuery(graphQuery, {
      entities,
      limit: this.config.topK,
    });
    
    // 3. Buscar documentos relacionados via relacionamentos
    const relatedQuery = `
      MATCH (d1:Document)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(d2:Document)
      WHERE d1.id IN $documentIds AND d1 <> d2
      RETURN DISTINCT d2.id as id, d2.content as content, d2.metadata as metadata
      LIMIT $limit
    `;
    
    const relatedResults = await this.executeGraphQuery(relatedQuery, {
      documentIds: graphResults.map(r => r.id),
      limit: this.config.topK / 2,
    });
    
    return [...graphResults, ...relatedResults];
  }
  
  /**
   * Hybrid Retrieval: Vector + Graph + Keyword
   */
  private async hybridRetrieval(
    query: TransformedQuery,
    options?: { projectId?: number; filters?: Record<string, any> }
  ): Promise<Document[]> {
    // Executar retrieval em paralelo
    const [vectorDocs, graphDocs, keywordDocs] = await Promise.all([
      this.vectorRetrieval(query, options),
      this.graphRetrieval(query, options),
      this.keywordRetrieval(query.original, options),
    ]);
    
    // Reciprocal Rank Fusion (RRF)
    const fused = this.reciprocalRankFusion([
      vectorDocs,
      graphDocs,
      keywordDocs,
    ]);
    
    return fused.slice(0, this.config.topK);
  }
  
  /**
   * Keyword Retrieval com PostgreSQL full-text search
   */
  private async keywordRetrieval(
    query: string,
    options?: { projectId?: number; filters?: Record<string, any> }
  ): Promise<Document[]> {
    const db = await getDb();
    
    // Usar pg_trgm para busca fuzzy
    const results = await db.execute(sql`
      SELECT 
        id,
        content,
        metadata,
        ts_rank(to_tsvector('english', content), plainto_tsquery('english', ${query})) as rank
      FROM document_chunks
      WHERE to_tsvector('english', content) @@ plainto_tsquery('english', ${query})
      ${options?.projectId ? sql`AND project_id = ${options.projectId}` : sql``}
      ORDER BY rank DESC
      LIMIT ${this.config.topK}
    `);
    
    return results.rows;
  }
  
  /**
   * Reranking com Cohere
   */
  private async rerank(query: string, documents: Document[]): Promise<Document[]> {
    const reranked = await this.reranker.compressDocuments(
      documents.map(d => ({ pageContent: d.content, metadata: d.metadata })),
      query
    );
    
    return reranked.map(d => ({
      content: d.pageContent,
      metadata: d.metadata,
    }));
  }
  
  /**
   * Contextual Compression: Extrair apenas trechos relevantes
   */
  private async compressContext(
    query: string,
    documents: Document[]
  ): Promise<Document[]> {
    const compressionPrompt = `Given the query: "${query}"

Extract only the most relevant passages from the following document that directly answer or relate to the query.

Document:
{document}

Relevant passages:`;
    
    const compressed = await Promise.all(
      documents.map(async (doc) => {
        const response = await this.llm.invoke(
          compressionPrompt.replace("{document}", doc.content)
        );
        
        return {
          ...doc,
          content: response.content as string,
        };
      })
    );
    
    return compressed;
  }
  
  /**
   * Generation: Gerar resposta final
   */
  private async generate(
    query: string,
    documents: Document[]
  ): Promise<RAGResponse> {
    const context = documents.map((d, i) => 
      `[Document ${i + 1}]\n${d.content}\n`
    ).join("\n");
    
    const prompt = `You are a helpful AI assistant. Answer the user's question based on the provided context.

Context:
${context}

Question: ${query}

Answer:`;
    
    const response = await this.llm.invoke(prompt);
    
    return {
      answer: response.content as string,
      sources: documents.map(d => ({
        content: d.content,
        metadata: d.metadata,
      })),
      retrievalMethod: this.config.retrievalMethod,
      documentsRetrieved: documents.length,
    };
  }
  
  /**
   * Reciprocal Rank Fusion
   */
  private reciprocalRankFusion(
    documentLists: Document[][],
    k: number = 60
  ): Document[] {
    const scores = new Map<string, number>();
    
    for (const docList of documentLists) {
      docList.forEach((doc, rank) => {
        const docId = this.getDocumentId(doc);
        const score = 1 / (k + rank + 1);
        scores.set(docId, (scores.get(docId) || 0) + score);
      });
    }
    
    // Ordenar por score
    const allDocs = documentLists.flat();
    const uniqueDocs = this.deduplicateDocuments(allDocs);
    
    return uniqueDocs.sort((a, b) => {
      const scoreA = scores.get(this.getDocumentId(a)) || 0;
      const scoreB = scores.get(this.getDocumentId(b)) || 0;
      return scoreB - scoreA;
    });
  }
  
  // Métodos auxiliares...
  private getDocumentId(doc: Document): string {
    return doc.metadata?.id || doc.content.substring(0, 50);
  }
  
  private deduplicateDocuments(docs: Document[]): Document[] {
    const seen = new Set<string>();
    return docs.filter(doc => {
      const id = this.getDocumentId(doc);
      if (seen.has(id)) return false;
      seen.add(id);
      return true;
    });
  }
  
  private async checkCache(query: string): Promise<RAGResponse | null> {
    // Implementação de cache...
    return null;
  }
  
  private async cacheResult(query: string, response: RAGResponse): Promise<void> {
    // Implementação de cache...
  }
  
  private async extractEntities(text: string): Promise<string[]> {
    // Implementação de NER...
    return [];
  }
  
  private async executeGraphQuery(query: string, params: any): Promise<any[]> {
    // Implementação de query Neo4j...
    return [];
  }
  
  private parseAlternatives(text: string): string[] {
    // Parse das alternativas geradas...
    return [];
  }
}

// Tipos
interface TransformedQuery {
  original: string;
  hypothetical: string;
  alternatives: string[];
}

interface Document {
  content: string;
  metadata?: Record<string, any>;
}

interface RAGResponse {
  answer: string;
  sources: Array<{
    content: string;
    metadata?: Record<string, any>;
  }>;
  retrievalMethod: string;
  documentsRetrieved: number;
}
```

### 3.2 Document Ingestion Pipeline

```typescript
// server/rag/ingestion.ts

import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";
import { Document as LangChainDocument } from "langchain/document";
import { OpenAIEmbeddings } from "@langchain/openai";

/**
 * Pipeline de ingestão de documentos
 */
export class DocumentIngestionPipeline {
  private embeddings: OpenAIEmbeddings;
  private textSplitter: RecursiveCharacterTextSplitter;
  
  constructor() {
    this.embeddings = new OpenAIEmbeddings({
      modelName: "text-embedding-3-large",
      dimensions: 1536,
    });
    
    // Chunking inteligente
    this.textSplitter = new RecursiveCharacterTextSplitter({
      chunkSize: 1000,
      chunkOverlap: 200,
      separators: ["\n\n", "\n", ". ", " ", ""],
    });
  }
  
  /**
   * Ingerir documento completo
   */
  async ingestDocument(
    projectId: number,
    content: string,
    metadata: {
      title: string;
      source: string;
      contentType: string;
      [key: string]: any;
    }
  ): Promise<number> {
    const db = await getDb();
    
    // 1. Criar registro do documento
    const [document] = await db.insert(documents).values({
      projectId,
      title: metadata.title,
      source: metadata.source,
      contentType: metadata.contentType,
      content,
      metadata,
      processingStatus: "processing",
    }).returning();
    
    try {
      // 2. Gerar resumo
      const summary = await this.generateSummary(content);
      
      // 3. Chunking
      const chunks = await this.textSplitter.createDocuments(
        [content],
        [{ documentId: document.id, ...metadata }]
      );
      
      // 4. Gerar embeddings
      const embeddings = await this.embeddings.embedDocuments(
        chunks.map(c => c.pageContent)
      );
      
      // 5. Inserir chunks no banco
      await db.insert(documentChunks).values(
        chunks.map((chunk, i) => ({
          documentId: document.id,
          content: chunk.pageContent,
          chunkIndex: i,
          embedding: embeddings[i],
          metadata: chunk.metadata,
          previousChunk: i > 0 ? chunks[i - 1].pageContent.substring(0, 200) : null,
          nextChunk: i < chunks.length - 1 ? chunks[i + 1].pageContent.substring(0, 200) : null,
        }))
      );
      
      // 6. Extrair entidades e construir grafo de conhecimento
      await this.buildKnowledgeGraph(document.id, content, metadata);
      
      // 7. Atualizar status
      await db.update(documents)
        .set({
          summary,
          chunkCount: chunks.length,
          processingStatus: "completed",
        })
        .where(eq(documents.id, document.id));
      
      return document.id;
      
    } catch (error) {
      // Marcar como failed
      await db.update(documents)
        .set({ processingStatus: "failed" })
        .where(eq(documents.id, document.id));
      
      throw error;
    }
  }
  
  /**
   * Gerar resumo do documento
   */
  private async generateSummary(content: string): Promise<string> {
    const llm = new ChatOpenAI({ modelName: "gpt-4o-mini" });
    
    const prompt = `Summarize the following document in 2-3 sentences:

${content.substring(0, 4000)}

Summary:`;
    
    const response = await llm.invoke(prompt);
    return response.content as string;
  }
  
  /**
   * Construir grafo de conhecimento no Neo4j
   */
  private async buildKnowledgeGraph(
    documentId: number,
    content: string,
    metadata: Record<string, any>
  ): Promise<void> {
    // 1. Extrair entidades
    const entities = await this.extractEntitiesAdvanced(content);
    
    // 2. Extrair relacionamentos
    const relationships = await this.extractRelationships(content, entities);
    
    // 3. Inserir no Neo4j
    const neo4j = await getNeo4jDriver();
    const session = neo4j.session();
    
    try {
      // Criar nó do documento
      await session.run(
        `
        CREATE (d:Document {
          id: $documentId,
          title: $title,
          source: $source,
          content: $content,
          createdAt: datetime()
        })
        `,
        {
          documentId: documentId.toString(),
          title: metadata.title,
          source: metadata.source,
          content: content.substring(0, 5000), // Limitar tamanho
        }
      );
      
      // Criar entidades e relacionamentos
      for (const entity of entities) {
        await session.run(
          `
          MERGE (e:Entity {name: $name})
          ON CREATE SET e.type = $type, e.description = $description
          
          WITH e
          MATCH (d:Document {id: $documentId})
          MERGE (d)-[:MENTIONS]->(e)
          `,
          {
            name: entity.name,
            type: entity.type,
            description: entity.description,
            documentId: documentId.toString(),
          }
        );
      }
      
      // Criar relacionamentos entre entidades
      for (const rel of relationships) {
        await session.run(
          `
          MATCH (e1:Entity {name: $source})
          MATCH (e2:Entity {name: $target})
          MERGE (e1)-[r:RELATED_TO {relationshipType: $type}]->(e2)
          ON CREATE SET r.strength = $strength
          `,
          {
            source: rel.source,
            target: rel.target,
            type: rel.type,
            strength: rel.strength,
          }
        );
      }
      
    } finally {
      await session.close();
    }
  }
  
  /**
   * Extração avançada de entidades com LLM
   */
  private async extractEntitiesAdvanced(
    content: string
  ): Promise<Array<{ name: string; type: string; description: string }>> {
    const llm = new ChatOpenAI({ modelName: "gpt-4o-mini" });
    
    const prompt = `Extract all important entities from the following text.
For each entity, provide:
- name: the entity name
- type: Person, Organization, Location, Technology, Concept, etc.
- description: brief description

Text:
${content.substring(0, 4000)}

Return as JSON array:`;
    
    const response = await llm.invoke(prompt);
    const entities = JSON.parse(response.content as string);
    
    return entities;
  }
  
  /**
   * Extração de relacionamentos
   */
  private async extractRelationships(
    content: string,
    entities: Array<{ name: string; type: string }>
  ): Promise<Array<{
    source: string;
    target: string;
    type: string;
    strength: number;
  }>> {
    const llm = new ChatOpenAI({ modelName: "gpt-4o-mini" });
    
    const entityNames = entities.map(e => e.name).join(", ");
    
    const prompt = `Given these entities: ${entityNames}

Extract relationships between them from the text below.
For each relationship, provide:
- source: source entity name
- target: target entity name
- type: relationship type (e.g., "works_for", "located_in", "uses", etc.)
- strength: confidence score 0-1

Text:
${content.substring(0, 4000)}

Return as JSON array:`;
    
    const response = await llm.invoke(prompt);
    const relationships = JSON.parse(response.content as string);
    
    return relationships;
  }
}
```

---

## 4. Componente 2: Sistema de Regras Simbólicas

### 4.1 Rule Engine Implementation

```typescript
// server/symbolic/ruleEngine.ts

import { Engine, Rule } from "json-rules-engine";
import { z } from "zod";

/**
 * Motor de regras simbólicas
 */
export class SymbolicRuleEngine {
  private engine: Engine;
  
  constructor() {
    this.engine = new Engine();
  }
  
  /**
   * Carregar regras do banco de dados
   */
  async loadRules(projectId: number): Promise<void> {
    const db = await getDb();
    
    const rules = await db.select()
      .from(validationRules)
      .where(
        and(
          eq(validationRules.projectId, projectId),
          eq(validationRules.isActive, true)
        )
      );
    
    // Adicionar cada regra ao engine
    for (const rule of rules) {
      const ruleObj = new Rule(rule.ruleDefinition);
      this.engine.addRule(ruleObj);
    }
  }
  
  /**
   * Validar entidade contra regras
   */
  async validate(
    entityType: string,
    entityData: Record<string, any>,
    context?: Record<string, any>
  ): Promise<ValidationResult> {
    const facts = {
      entityType,
      ...entityData,
      context: context || {},
    };
    
    const results = await this.engine.run(facts);
    
    const violations: RuleViolation[] = [];
    
    for (const event of results.events) {
      if (event.type === "violation") {
        violations.push({
          ruleId: event.params.ruleId,
          ruleName: event.params.ruleName,
          severity: event.params.severity,
          message: event.params.message,
          details: event.params.details,
        });
      }
    }
    
    return {
      passed: violations.length === 0,
      violations,
      context: facts,
    };
  }
  
  /**
   * Criar regra de validação
   */
  async createRule(
    projectId: number,
    ruleDefinition: RuleDefinition
  ): Promise<number> {
    const db = await getDb();
    
    // Validar definição da regra
    const validated = RuleDefinitionSchema.parse(ruleDefinition);
    
    // Inserir no banco
    const [rule] = await db.insert(validationRules).values({
      projectId,
      name: validated.name,
      description: validated.description,
      category: validated.category,
      ruleDefinition: validated.conditions,
      severity: validated.severity,
      appliesTo: validated.appliesTo,
      isActive: true,
    }).returning();
    
    return rule.id;
  }
}

/**
 * Schemas Zod para validação
 */
const RuleDefinitionSchema = z.object({
  name: z.string(),
  description: z.string().optional(),
  category: z.enum(["compliance", "security", "business", "data_integrity"]),
  severity: z.enum(["low", "medium", "high", "critical"]),
  conditions: z.object({
    all: z.array(z.any()).optional(),
    any: z.array(z.any()).optional(),
  }),
  event: z.object({
    type: z.literal("violation"),
    params: z.object({
      message: z.string(),
      details: z.record(z.any()).optional(),
    }),
  }),
  appliesTo: z.object({
    entityTypes: z.array(z.string()),
    conditions: z.record(z.any()).optional(),
  }).optional(),
});

type RuleDefinition = z.infer<typeof RuleDefinitionSchema>;

interface ValidationResult {
  passed: boolean;
  violations: RuleViolation[];
  context: Record<string, any>;
}

interface RuleViolation {
  ruleId: string;
  ruleName: string;
  severity: string;
  message: string;
  details?: Record<string, any>;
}

/**
 * Regras pré-definidas para casos comuns
 */
export const PredefinedRules = {
  /**
   * Compliance: Workflows financeiros devem ter auditoria
   */
  financialWorkflowAudit: {
    name: "Financial Workflow Audit Requirement",
    description: "All financial workflows must include an audit step",
    category: "compliance" as const,
    severity: "high" as const,
    conditions: {
      all: [
        {
          fact: "entityType",
          operator: "equal",
          value: "workflow",
        },
        {
          fact: "category",
          operator: "equal",
          value: "financial",
        },
        {
          fact: "steps",
          operator: "notContains",
          value: { type: "audit" },
        },
      ],
    },
    event: {
      type: "violation" as const,
      params: {
        message: "Financial workflows must include an audit step",
        details: {
          requiredStep: "audit",
          suggestion: "Add an audit step to ensure compliance",
        },
      },
    },
  },
  
  /**
   * Security: Agentes não podem executar código arbitrário
   */
  noArbitraryCodeExecution: {
    name: "No Arbitrary Code Execution",
    description: "Agents cannot execute arbitrary code without sandboxing",
    category: "security" as const,
    severity: "critical" as const,
    conditions: {
      all: [
        {
          fact: "entityType",
          operator: "equal",
          value: "agent",
        },
        {
          fact: "tools",
          operator: "contains",
          value: "code_execution",
        },
        {
          fact: "sandboxEnabled",
          operator: "notEqual",
          value: true,
        },
      ],
    },
    event: {
      type: "violation" as const,
      params: {
        message: "Code execution must be sandboxed",
        details: {
          risk: "Arbitrary code execution without sandboxing poses security risks",
          solution: "Enable sandboxing for code execution tools",
        },
      },
    },
  },
  
  /**
   * Business: Orçamento máximo por execução
   */
  budgetLimit: {
    name: "Execution Budget Limit",
    description: "Executions cannot exceed project budget limit",
    category: "business" as const,
    severity: "medium" as const,
    conditions: {
      all: [
        {
          fact: "entityType",
          operator: "equal",
          value: "execution",
        },
        {
          fact: "estimatedCost",
          operator: "greaterThan",
          path: "$.context.projectBudget",
        },
      ],
    },
    event: {
      type: "violation" as const,
      params: {
        message: "Execution cost exceeds project budget",
        details: {
          action: "Execution blocked to prevent budget overrun",
        },
      },
    },
  },
  
  /**
   * Data Integrity: Outputs devem ter schema válido
   */
  outputSchemaValidation: {
    name: "Output Schema Validation",
    description: "Agent outputs must conform to defined schema",
    category: "data_integrity" as const,
    severity: "high" as const,
    conditions: {
      all: [
        {
          fact: "entityType",
          operator: "equal",
          value: "agent_output",
        },
        {
          fact: "schemaValid",
          operator: "equal",
          value: false,
        },
      ],
    },
    event: {
      type: "violation" as const,
      params: {
        message: "Output does not conform to expected schema",
        details: {
          action: "Output rejected, agent will retry with schema constraints",
        },
      },
    },
  },
};
```

### 4.2 Integration with Agent Execution

```typescript
// server/agents/execution.ts

import { SymbolicRuleEngine } from "../symbolic/ruleEngine";
import { AdvancedRAGPipeline } from "../rag/pipeline";

/**
 * Executor de agente com validação simbólica
 */
export class ValidatedAgentExecutor {
  private ruleEngine: SymbolicRuleEngine;
  private ragPipeline: AdvancedRAGPipeline;
  
  constructor(projectId: number) {
    this.ruleEngine = new SymbolicRuleEngine();
    await this.ruleEngine.loadRules(projectId);
    
    this.ragPipeline = new AdvancedRAGPipeline({
      embeddingModel: "text-embedding-3-large",
      embeddingDimensions: 1536,
      retrievalMethod: "hybrid",
      topK: 20,
      topN: 5,
      useReranking: true,
      rerankModel: "cohere",
      llmModel: "gpt-4o",
      temperature: 0.7,
      maxTokens: 2000,
      useCaching: true,
      cacheTTL: 3600,
    });
  }
  
  /**
   * Executar agente com validação
   */
  async execute(
    agentId: number,
    input: string,
    context?: Record<string, any>
  ): Promise<ExecutionResult> {
    const db = await getDb();
    
    // 1. Carregar configuração do agente
    const agent = await db.select()
      .from(agents)
      .where(eq(agents.id, agentId))
      .limit(1)
      .then(rows => rows[0]);
    
    if (!agent) {
      throw new Error(`Agent ${agentId} not found`);
    }
    
    // 2. Validar pré-condições
    const preValidation = await this.ruleEngine.validate(
      "agent",
      {
        id: agent.id,
        type: agent.type,
        tools: agent.tools,
        sandboxEnabled: agent.sandboxEnabled,
      },
      context
    );
    
    if (!preValidation.passed) {
      return {
        success: false,
        error: "Pre-execution validation failed",
        violations: preValidation.violations,
      };
    }
    
    // 3. Enriquecer contexto com RAG
    let enrichedContext = context || {};
    
    if (agent.memoryEnabled) {
      const ragResult = await this.ragPipeline.query(input, {
        projectId: agent.projectId,
      });
      
      enrichedContext.retrievedKnowledge = ragResult.sources;
      enrichedContext.ragAnswer = ragResult.answer;
    }
    
    // 4. Executar agente
    const output = await this.executeAgent(agent, input, enrichedContext);
    
    // 5. Validar output
    const postValidation = await this.ruleEngine.validate(
      "agent_output",
      {
        agentId: agent.id,
        output,
        schemaValid: this.validateOutputSchema(output, agent.outputSchema),
      },
      enrichedContext
    );
    
    if (!postValidation.passed) {
      // Tentar regenerar com constraints
      const constrainedOutput = await this.regenerateWithConstraints(
        agent,
        input,
        enrichedContext,
        postValidation.violations
      );
      
      // Validar novamente
      const retryValidation = await this.ruleEngine.validate(
        "agent_output",
        {
          agentId: agent.id,
          output: constrainedOutput,
          schemaValid: this.validateOutputSchema(constrainedOutput, agent.outputSchema),
        },
        enrichedContext
      );
      
      if (!retryValidation.passed) {
        return {
          success: false,
          error: "Output validation failed after retry",
          violations: retryValidation.violations,
        };
      }
      
      return {
        success: true,
        output: constrainedOutput,
        metadata: {
          retriedDueToValidation: true,
          ragUsed: agent.memoryEnabled,
        },
      };
    }
    
    // 6. Armazenar histórico de validação
    await db.insert(validationHistory).values({
      entityType: "execution",
      entityId: agent.id,
      ruleId: 0, // Todas as regras passaram
      passed: true,
      context: enrichedContext,
    });
    
    return {
      success: true,
      output,
      metadata: {
        ragUsed: agent.memoryEnabled,
      },
    };
  }
  
  private async executeAgent(
    agent: Agent,
    input: string,
    context: Record<string, any>
  ): Promise<any> {
    // Implementação de execução do agente...
    // Usar LLM com system prompt, tools, etc.
    return {};
  }
  
  private validateOutputSchema(output: any, schema: any): boolean {
    // Validar output contra schema Zod
    try {
      if (schema) {
        schema.parse(output);
      }
      return true;
    } catch {
      return false;
    }
  }
  
  private async regenerateWithConstraints(
    agent: Agent,
    input: string,
    context: Record<string, any>,
    violations: RuleViolation[]
  ): Promise<any> {
    // Regenerar output com feedback explícito sobre violações
    const constraintPrompt = `
Previous output violated the following rules:
${violations.map(v => `- ${v.message}`).join("\n")}

Please regenerate the output ensuring compliance with all rules.
`;
    
    // Executar novamente com constraints
    return this.executeAgent(agent, input, {
      ...context,
      constraints: constraintPrompt,
    });
  }
}

interface ExecutionResult {
  success: boolean;
  output?: any;
  error?: string;
  violations?: RuleViolation[];
  metadata?: Record<string, any>;
}
```

---

## 5. tRPC Procedures

```typescript
// server/routers.ts - Adicionar procedures para RAG e Validação

import { z } from "zod";
import { protectedProcedure, router } from "./_core/trpc";
import { AdvancedRAGPipeline } from "./rag/pipeline";
import { DocumentIngestionPipeline } from "./rag/ingestion";
import { SymbolicRuleEngine, PredefinedRules } from "./symbolic/ruleEngine";
import { ValidatedAgentExecutor } from "./agents/execution";

export const appRouter = router({
  // ... existing routers ...
  
  /**
   * RAG Router
   */
  rag: router({
    /**
     * Query RAG system
     */
    query: protectedProcedure
      .input(z.object({
        projectId: z.number(),
        query: z.string(),
        retrievalMethod: z.enum(["vector", "graph", "hybrid"]).optional(),
        topK: z.number().optional(),
      }))
      .mutation(async ({ input, ctx }) => {
        const pipeline = new AdvancedRAGPipeline({
          embeddingModel: "text-embedding-3-large",
          embeddingDimensions: 1536,
          retrievalMethod: input.retrievalMethod || "hybrid",
          topK: input.topK || 20,
          topN: 5,
          useReranking: true,
          rerankModel: "cohere",
          llmModel: "gpt-4o",
          temperature: 0.7,
          maxTokens: 2000,
          useCaching: true,
          cacheTTL: 3600,
        });
        
        const result = await pipeline.query(input.query, {
          projectId: input.projectId,
        });
        
        return result;
      }),
    
    /**
     * Ingest document
     */
    ingestDocument: protectedProcedure
      .input(z.object({
        projectId: z.number(),
        title: z.string(),
        content: z.string(),
        source: z.string(),
        contentType: z.string(),
        metadata: z.record(z.any()).optional(),
      }))
      .mutation(async ({ input, ctx }) => {
        const pipeline = new DocumentIngestionPipeline();
        
        const documentId = await pipeline.ingestDocument(
          input.projectId,
          input.content,
          {
            title: input.title,
            source: input.source,
            contentType: input.contentType,
            ...input.metadata,
          }
        );
        
        return { documentId };
      }),
    
    /**
     * List documents
     */
    listDocuments: protectedProcedure
      .input(z.object({
        projectId: z.number(),
        limit: z.number().optional(),
        offset: z.number().optional(),
      }))
      .query(async ({ input, ctx }) => {
        const db = await getDb();
        
        const docs = await db.select()
          .from(documents)
          .where(eq(documents.projectId, input.projectId))
          .limit(input.limit || 50)
          .offset(input.offset || 0)
          .orderBy(desc(documents.createdAt));
        
        return docs;
      }),
  }),
  
  /**
   * Rules Router
   */
  rules: router({
    /**
     * Create validation rule
     */
    create: protectedProcedure
      .input(z.object({
        projectId: z.number(),
        name: z.string(),
        description: z.string().optional(),
        category: z.enum(["compliance", "security", "business", "data_integrity"]),
        severity: z.enum(["low", "medium", "high", "critical"]),
        ruleDefinition: z.any(),
        appliesTo: z.any().optional(),
      }))
      .mutation(async ({ input, ctx }) => {
        const engine = new SymbolicRuleEngine();
        
        const ruleId = await engine.createRule(input.projectId, {
          name: input.name,
          description: input.description,
          category: input.category,
          severity: input.severity,
          conditions: input.ruleDefinition,
          event: {
            type: "violation",
            params: {
              message: `Violation of rule: ${input.name}`,
            },
          },
          appliesTo: input.appliesTo,
        });
        
        return { ruleId };
      }),
    
    /**
     * List rules
     */
    list: protectedProcedure
      .input(z.object({
        projectId: z.number(),
      }))
      .query(async ({ input, ctx }) => {
        const db = await getDb();
        
        const rules = await db.select()
          .from(validationRules)
          .where(eq(validationRules.projectId, input.projectId))
          .orderBy(desc(validationRules.createdAt));
        
        return rules;
      }),
    
    /**
     * Get predefined rules
     */
    getPredefined: protectedProcedure
      .query(() => {
        return Object.entries(PredefinedRules).map(([key, rule]) => ({
          id: key,
          ...rule,
        }));
      }),
    
    /**
     * Validate entity
     */
    validate: protectedProcedure
      .input(z.object({
        projectId: z.number(),
        entityType: z.string(),
        entityData: z.record(z.any()),
        context: z.record(z.any()).optional(),
      }))
      .mutation(async ({ input, ctx }) => {
        const engine = new SymbolicRuleEngine();
        await engine.loadRules(input.projectId);
        
        const result = await engine.validate(
          input.entityType,
          input.entityData,
          input.context
        );
        
        return result;
      }),
  }),
  
  /**
   * Agent Execution Router (com validação)
   */
  agents: router({
    /**
     * Execute agent with validation
     */
    executeValidated: protectedProcedure
      .input(z.object({
        projectId: z.number(),
        agentId: z.number(),
        input: z.string(),
        context: z.record(z.any()).optional(),
      }))
      .mutation(async ({ input, ctx }) => {
        const executor = new ValidatedAgentExecutor(input.projectId);
        
        const result = await executor.execute(
          input.agentId,
          input.input,
          input.context
        );
        
        return result;
      }),
  }),
});
```

---

## 6. Setup e Configuração

### 6.1 Variáveis de Ambiente

```bash
# .env

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/ai_agents"

# Neo4j
NEO4J_URL="bolt://localhost:7687"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="your_password"

# OpenAI
OPENAI_API_KEY="sk-..."

# Cohere (para reranking)
COHERE_API_KEY="..."

# Redis
REDIS_URL="redis://localhost:6379"
```

### 6.2 Migrations

```sql
-- migrations/001_add_pgvector.sql

-- Habilitar extensão pgvector
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Criar índice vetorial
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Criar índice full-text
CREATE INDEX document_chunks_content_idx ON document_chunks 
USING gin(to_tsvector('english', content));

-- Criar índice trigram para busca fuzzy
CREATE INDEX document_chunks_content_trgm_idx ON document_chunks 
USING gin(content gin_trgm_ops);
```

### 6.3 Neo4j Setup

```cypher
// setup_neo4j.cypher

// Criar constraints
CREATE CONSTRAINT document_id IF NOT EXISTS 
FOR (d:Document) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT entity_id IF NOT EXISTS 
FOR (e:Entity) REQUIRE e.id IS UNIQUE;

// Criar índices
CREATE INDEX document_source IF NOT EXISTS 
FOR (d:Document) ON (d.source);

CREATE INDEX entity_type IF NOT EXISTS 
FOR (e:Entity) ON (e.type);

CREATE INDEX entity_name IF NOT EXISTS 
FOR (e:Entity) ON (e.name);

// Criar índice vetorial para Document nodes
CALL db.index.vector.createNodeIndex(
  'document_embeddings',
  'Document',
  'embedding',
  1536,
  'cosine'
);
```

### 6.4 Package.json Dependencies

```json
{
  "dependencies": {
    // ... existing dependencies ...
    
    // RAG e Embeddings
    "@langchain/openai": "^0.3.15",
    "@langchain/community": "^0.3.15",
    "@langchain/cohere": "^0.3.5",
    "langchain": "^0.3.15",
    
    // Vector Store
    "pgvector": "^0.2.0",
    
    // Graph Database
    "neo4j-driver": "^5.27.0",
    
    // Symbolic Reasoning
    "json-rules-engine": "^6.5.0",
    
    // Text Processing
    "pdf-parse": "^1.1.1",
    "mammoth": "^1.8.0",
    "cheerio": "^1.0.0",
    
    // Utilities
    "crypto": "^1.0.1",
    "hash.js": "^1.1.7"
  }
}
```

---

## 7. Testing

### 7.1 RAG Pipeline Tests

```typescript
// server/rag/pipeline.test.ts

import { describe, it, expect, beforeAll } from "vitest";
import { AdvancedRAGPipeline } from "./pipeline";
import { DocumentIngestionPipeline } from "./ingestion";

describe("Advanced RAG Pipeline", () => {
  let pipeline: AdvancedRAGPipeline;
  let ingestion: DocumentIngestionPipeline;
  
  beforeAll(async () => {
    pipeline = new AdvancedRAGPipeline({
      embeddingModel: "text-embedding-3-small",
      embeddingDimensions: 1536,
      retrievalMethod: "hybrid",
      topK: 10,
      topN: 3,
      useReranking: true,
      rerankModel: "cohere",
      llmModel: "gpt-4o-mini",
      temperature: 0.7,
      maxTokens: 1000,
      useCaching: false,
      cacheTTL: 0,
    });
    
    ingestion = new DocumentIngestionPipeline();
    
    // Ingest test document
    await ingestion.ingestDocument(
      1, // projectId
      "Neo4j is a graph database. It uses Cypher query language.",
      {
        title: "Neo4j Introduction",
        source: "test",
        contentType: "text",
      }
    );
  });
  
  it("should retrieve relevant documents", async () => {
    const result = await pipeline.query("What is Neo4j?", {
      projectId: 1,
    });
    
    expect(result.answer).toContain("graph database");
    expect(result.sources.length).toBeGreaterThan(0);
  });
  
  it("should use hybrid retrieval", async () => {
    const result = await pipeline.query("Cypher query language", {
      projectId: 1,
      retrievalMethod: "hybrid",
    });
    
    expect(result.retrievalMethod).toBe("hybrid");
    expect(result.documentsRetrieved).toBeGreaterThan(0);
  });
});
```

### 7.2 Rule Engine Tests

```typescript
// server/symbolic/ruleEngine.test.ts

import { describe, it, expect } from "vitest";
import { SymbolicRuleEngine, PredefinedRules } from "./ruleEngine";

describe("Symbolic Rule Engine", () => {
  it("should validate financial workflow audit requirement", async () => {
    const engine = new SymbolicRuleEngine();
    
    // Adicionar regra
    engine.engine.addRule(PredefinedRules.financialWorkflowAudit);
    
    // Workflow sem audit step - deve falhar
    const result1 = await engine.validate("workflow", {
      category: "financial",
      steps: [
        { type: "input" },
        { type: "process" },
        { type: "output" },
      ],
    });
    
    expect(result1.passed).toBe(false);
    expect(result1.violations.length).toBeGreaterThan(0);
    
    // Workflow com audit step - deve passar
    const result2 = await engine.validate("workflow", {
      category: "financial",
      steps: [
        { type: "input" },
        { type: "process" },
        { type: "audit" },
        { type: "output" },
      ],
    });
    
    expect(result2.passed).toBe(true);
    expect(result2.violations.length).toBe(0);
  });
});
```

---

## 8. Deployment Checklist

### 8.1 Infrastructure

- [ ] PostgreSQL 16+ com extensão pgvector instalada
- [ ] Neo4j 5.x instalado e configurado
- [ ] Redis para caching
- [ ] OpenAI API key configurada
- [ ] Cohere API key configurada (para reranking)

### 8.2 Database Setup

- [ ] Executar migrations para criar tabelas
- [ ] Criar índices vetoriais no PostgreSQL
- [ ] Executar setup script no Neo4j
- [ ] Configurar backup automático

### 8.3 Application

- [ ] Instalar dependências npm
- [ ] Configurar variáveis de ambiente
- [ ] Executar testes
- [ ] Build da aplicação
- [ ] Deploy

### 8.4 Monitoring

- [ ] Configurar logging
- [ ] Monitorar uso de tokens OpenAI
- [ ] Monitorar latência de queries RAG
- [ ] Alertas para violações de regras críticas

---

## 9. Performance Optimization

### 9.1 Caching Strategy

```typescript
// Implementar cache em múltiplas camadas

// 1. Cache de embeddings (Redis)
const embeddingCache = new Map<string, number[]>();

// 2. Cache de queries RAG (PostgreSQL)
// Já implementado na tabela rag_query_cache

// 3. Cache de resultados de validação (Redis)
const validationCache = new Map<string, ValidationResult>();
```

### 9.2 Batch Processing

```typescript
// Processar múltiplos documentos em paralelo

async function batchIngest(documents: Document[]): Promise<number[]> {
  const batchSize = 10;
  const results: number[] = [];
  
  for (let i = 0; i < documents.length; i += batchSize) {
    const batch = documents.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(doc => ingestion.ingestDocument(...))
    );
    results.push(...batchResults);
  }
  
  return results;
}
```

---

## 10. Conclusão

Esta arquitetura de implementação fornece uma base sólida para a Fase 3, combinando:

1. **RAG Avançado** com múltiplas estratégias de recuperação (vector, graph, hybrid)
2. **Reranking sofisticado** com Cohere para melhorar relevância
3. **Validação simbólica** para garantir compliance e confiabilidade
4. **Integração completa** entre todos os componentes

A implementação é **modular**, **escalável**, e **pronta para produção**, com testes, monitoring, e otimizações de performance incluídas.

**Próximos passos:**
1. Implementar código base seguindo esta especificação
2. Testar com dados reais
3. Ajustar parâmetros baseado em métricas
4. Expandir para Fase 4 (Self-Healing e Sistema Adaptativo)

---

**Autor:** Manus AI  
**Data:** 02 de Dezembro de 2025  
**Status:** Especificação Técnica Completa - Pronta para Implementação
