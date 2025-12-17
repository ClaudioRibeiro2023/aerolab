from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.utils import embedding_functions
import httpx
from bs4 import BeautifulSoup
import io
from pypdf import PdfReader
import re

from src.config import get_settings


class RagService:
    def __init__(self) -> None:
        s = get_settings()
        # Usa HttpClient se CHROMA_HOST estiver definido, caso contrário usa PersistentClient
        if s.CHROMA_HOST:
            self.client = chromadb.HttpClient(host=s.CHROMA_HOST.replace("http://", "").replace("https://", "").split(":")[0],
                                               port=int(s.CHROMA_HOST.split(":")[-1]) if ":" in s.CHROMA_HOST.replace("http://", "").replace("https://", "") else 8000)
        else:
            self.client = chromadb.PersistentClient(path=s.CHROMA_DB_PATH)
        self.provider = s.EMBEDDING_PROVIDER
        self.model = s.OPENAI_EMBED_MODEL
        self._embed_fn = None

    def _get_embed_fn(self):
        if self._embed_fn is not None:
            return self._embed_fn
        s = get_settings()
        if self.provider == "openai":
            # Use built-in OpenAI embedding function adapter
            self._embed_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=s.OPENAI_API_KEY or "",
                model_name=self.model,
            )
        else:
            raise ValueError(f"Embedding provider not supported: {self.provider}")
        return self._embed_fn

    def get_collection(self, name: str):
        return self.client.get_or_create_collection(name=name, embedding_function=self._get_embed_fn())

    def add_texts(self, *, collection: str, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
        col = self.get_collection(collection)
        ids = [f"doc-{i}" for i in range(col.count() + 1, col.count() + 1 + len(texts))]
        col.add(ids=ids, documents=texts, metadatas=metadatas)
        return {"added": len(texts)}

    def query(self, *, collection: str, query_text: str, top_k: int = 5):
        col = self.get_collection(collection)
        res = col.query(query_texts=[query_text], n_results=top_k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return [{"text": d, "metadata": m} for d, m in zip(docs, metas)]

    async def ingest_urls(self, *, collection: str, urls: List[str]) -> Dict[str, Any]:
        texts: List[str] = []
        metas: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=20) as client:
            for url in urls:
                try:
                    r = await client.get(url)
                    r.raise_for_status()
                    soup = BeautifulSoup(r.text, "html.parser")
                    title = (soup.title.string.strip() if soup.title and soup.title.string else url)
                    for tag in soup(["script", "style", "noscript"]):
                        tag.decompose()
                    text = "\n".join(t.strip() for t in soup.get_text("\n").splitlines() if t.strip())
                    text = self._normalize_text(text)
                    if text:
                        texts.append(text)
                        metas.append({"source": url, "title": title})
                except Exception:
                    # pula URL com erro
                    continue
        if not texts:
            return {"added": 0}
        return self.add_texts(collection=collection, texts=texts, metadatas=metas)

    def _chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
        chunks: List[str] = []
        start = 0
        n = len(text)
        if chunk_size <= 0:
            return [text]
        while start < n:
            end = min(start + chunk_size, n)
            chunk = text[start:end]
            chunk = chunk.strip()
            if chunk:
                chunks.append(chunk)
            if end >= n:
                break
            start = max(end - overlap, start + 1)
        return chunks

    def _extract_pdf_pages(self, data: bytes) -> List[str]:
        try:
            reader = PdfReader(io.BytesIO(data))
            pages: List[str] = []
            for p in reader.pages:
                try:
                    t = p.extract_text() or ""
                except Exception:
                    t = ""
                if t:
                    pages.append(t)
            return pages
        except Exception:
            return []

    def _extract_markdown_text(self, data: bytes) -> str:
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _split_markdown_by_headings(self, text: str) -> List[Tuple[str, str]]:
        """Divide markdown por headings (#, ##, ### ...) retornando pares (heading, conteudo)."""
        lines = text.splitlines()
        sections: List[Tuple[str, List[str]]] = []
        current_title = "root"
        current: List[str] = []
        heading_re = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$")
        for ln in lines:
            m = heading_re.match(ln)
            if m:
                # inicia nova seção
                if current:
                    sections.append((current_title, current))
                current_title = m.group(1).strip() or "section"
                current = []
            else:
                current.append(ln)
        if current:
            sections.append((current_title, current))
        return [(title, "\n".join(body).strip()) for title, body in sections if "\n".join(body).strip()]

    def _normalize_text(self, text: str) -> str:
        """Normaliza texto removendo boilerplate simples e tabelas markdown/separadores."""
        table_sep_re = re.compile(r"^\s*\|?[-+:| ]+\|?\s*$")
        cleaned_lines: List[str] = []
        for ln in text.splitlines():
            s = ln.strip("\u200b\ufeff ")
            if not s:
                cleaned_lines.append("")
                continue
            if table_sep_re.match(s):
                continue
            cleaned_lines.append(s)
        cleaned = "\n".join(cleaned_lines)
        # Colapsa múltiplas linhas em branco
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def ingest_files(self, *, collection: str, files: List[Tuple[str, bytes]]) -> Dict[str, Any]:
        texts: List[str] = []
        metas: List[Dict[str, Any]] = []
        for name, data in files:
            lower = name.lower()
            if lower.endswith(".pdf"):
                pages = self._extract_pdf_pages(data)
                for pidx, page_text in enumerate(pages):
                    page_text = self._normalize_text(page_text)
                    for cidx, ch in enumerate(self._chunk_text(page_text)):
                        texts.append(ch)
                        metas.append({"source": name, "page": pidx + 1, "chunk": cidx + 1})
                continue
            if lower.endswith(".md") or lower.endswith(".markdown"):
                md = self._extract_markdown_text(data)
                for title, body in self._split_markdown_by_headings(md):
                    body = self._normalize_text(body)
                    for cidx, ch in enumerate(self._chunk_text(body)):
                        texts.append(ch)
                        metas.append({"source": name, "section": title, "chunk": cidx + 1})
                continue
            if lower.endswith(".txt"):
                txt = self._extract_markdown_text(data)
                txt = self._normalize_text(txt)
                for cidx, ch in enumerate(self._chunk_text(txt)):
                    texts.append(ch)
                    metas.append({"source": name, "chunk": cidx + 1})
                continue
            # Unsupported
            continue
        if not texts:
            return {"added": 0}
        return self.add_texts(collection=collection, texts=texts, metadatas=metas)

    def list_collections(self) -> List[str]:
        """Lista todas as coleções disponíveis."""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception:
            return []

    def list_docs(self, *, collection: str) -> List[Dict[str, Any]]:
        """Lista documentos de uma coleção."""
        try:
            col = self.get_collection(collection)
            result = col.get()
            ids = result.get("ids", [])
            docs = result.get("documents", [])
            metas = result.get("metadatas", [])
            return [
                {"id": doc_id, "text": doc[:200] + "..." if len(doc) > 200 else doc, "metadata": meta}
                for doc_id, doc, meta in zip(ids, docs, metas)
            ]
        except Exception:
            return []

    def delete_collection(self, *, collection: str) -> bool:
        """Remove uma coleção."""
        try:
            self.client.delete_collection(name=collection)
            return True
        except Exception:
            return False

    def delete_doc(self, *, collection: str, doc_id: str) -> bool:
        """Remove um documento específico de uma coleção."""
        try:
            col = self.get_collection(collection)
            col.delete(ids=[doc_id])
            return True
        except Exception:
            return False


def get_rag_service() -> RagService:
    return RagService()
