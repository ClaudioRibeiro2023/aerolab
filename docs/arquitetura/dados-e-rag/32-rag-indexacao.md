# RAG - Indexação e Retrieval

> Como funciona o sistema RAG (Retrieval-Augmented Generation) da plataforma.

---

## Visão Geral

O sistema RAG permite:

1. **Indexar documentos** - Transformar texto em embeddings
2. **Buscar contexto** - Encontrar chunks relevantes
3. **Gerar respostas** - Usar contexto para respostas fundamentadas

---

## Arquitetura RAG

```
┌─────────────────────────────────────────────────────────────┐
│                    INGEST PIPELINE                          │
│                                                             │
│  Document → Chunking → Embedding → ChromaDB                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    QUERY PIPELINE                           │
│                                                             │
│  Query → Embedding → Search → Context → LLM → Response      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Chunking

### Estratégia Padrão

O sistema divide documentos em chunks de tamanho fixo com overlap:

```python
# src/rag/chunking.py
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```

### Parâmetros

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `chunk_size` | 1000 | Tamanho máximo do chunk |
| `overlap` | 200 | Sobreposição entre chunks |

---

## Embeddings

### Provider Padrão

OpenAI embeddings (`text-embedding-ada-002`):

```python
# Configuração
EMBEDDING_PROVIDER=openai
OPENAI_EMBED_MODEL=text-embedding-ada-002
OPENAI_API_KEY=sk-...
```

### Dimensionalidade

| Provider | Modelo | Dimensões |
|----------|--------|-----------|
| OpenAI | text-embedding-ada-002 | 1536 |
| OpenAI | text-embedding-3-small | 1536 |
| OpenAI | text-embedding-3-large | 3072 |

---

## ChromaDB

### Configuração Local

```python
import chromadb

# Client persistente local
client = chromadb.PersistentClient(path="./data/chroma")
```

### Configuração Servidor

```python
# Client HTTP
client = chromadb.HttpClient(
    host="chroma-server",
    port=8000
)
```

### Collections

Cada domínio/projeto pode ter sua própria collection:

```python
# Criar/obter collection
collection = client.get_or_create_collection(
    name="my-docs",
    embedding_function=openai_embedding
)

# Adicionar documentos
collection.add(
    ids=["doc-1", "doc-2"],
    documents=["Text 1...", "Text 2..."],
    metadatas=[{"source": "file1"}, {"source": "file2"}]
)
```

---

## Indexação (Ingest)

### API

```http
POST /rag/ingest
Authorization: Bearer <token>
Content-Type: application/json

{
  "collection": "my-docs",
  "texts": ["Document 1 content...", "Document 2 content..."],
  "metadatas": [
    {"source": "doc1.pdf", "page": 1},
    {"source": "doc2.pdf", "page": 1}
  ]
}
```

### Response

```json
{
  "added": 2,
  "collection": "my-docs"
}
```

### Ingest de URL

```http
POST /rag/ingest/url
Content-Type: application/json

{
  "collection": "my-docs",
  "url": "https://example.com/page",
  "metadata": {"source": "web"}
}
```

### Ingest de PDF

```http
POST /rag/ingest/pdf
Content-Type: multipart/form-data

file: <pdf-file>
collection: my-docs
```

---

## Query

### API

```http
POST /rag/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "collection": "my-docs",
  "query": "What is the main topic?",
  "top_k": 5,
  "with_context": true
}
```

### Response

```json
{
  "answer": "Based on the documents, the main topic is...",
  "sources": [
    {
      "content": "Relevant chunk 1...",
      "metadata": {"source": "doc1.pdf", "page": 3},
      "score": 0.89
    },
    {
      "content": "Relevant chunk 2...",
      "metadata": {"source": "doc2.pdf", "page": 1},
      "score": 0.85
    }
  ]
}
```

---

## RAG Engines Especializados

O Domain Studio oferece engines especializados:

### Agentic RAG

RAG com planejamento autônomo:

```python
from src.domain_studio.engines.agentic_rag import AgenticRAGEngine

engine = AgenticRAGEngine(
    collection="docs",
    planning_model="groq:llama-3.3-70b-versatile"
)
result = await engine.query("Complex multi-step question")
```

### Graph RAG

RAG com knowledge graph:

```python
from src.domain_studio.engines.graph_rag import GraphRAGEngine

engine = GraphRAGEngine(collection="docs")
result = await engine.query("Query with relationships")
```

---

## Metadados

### Metadados Padrão

| Campo | Descrição |
|-------|-----------|
| `source` | Origem do documento |
| `page` | Número da página (PDFs) |
| `url` | URL de origem |
| `timestamp` | Data de indexação |
| `chunk_index` | Índice do chunk |

### Filtros por Metadados

```http
POST /rag/query
{
  "collection": "my-docs",
  "query": "...",
  "filter": {
    "source": "important-doc.pdf"
  }
}
```

---

## Performance

### Índices

ChromaDB usa HNSW (Hierarchical Navigable Small World) para busca aproximada.

### Otimizações

1. **Batch ingest** - Indexar múltiplos documentos de uma vez
2. **Async queries** - Queries não bloqueiam
3. **Caching** - Cache de embeddings frequentes

---

## Referências

- [Código: src/rag/](../../src/rag/)
- [Domain Studio Engines](../../src/domain_studio/engines/)
- [ChromaDB Docs](https://docs.trychroma.com/)
