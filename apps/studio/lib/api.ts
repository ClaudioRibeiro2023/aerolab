import axios, { type InternalAxiosRequestConfig } from "axios";

function getBaseURL() {
  // Base URL primária: produção (NEXT_PUBLIC_API_URL) ou fallback para AGENTOS_API_BASE e, por fim, localhost
  let baseURL =
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_AGENTOS_API_BASE ||
    "http://127.0.0.1:8000";

  // Se o frontend estiver rodando em HTTPS, evitar Mixed Content fazendo upgrade automático http -> https
  if (typeof window !== "undefined" && window.location.protocol === "https:" && baseURL.startsWith("http://")) {
    baseURL = "https://" + baseURL.slice("http://".length);
  }

  return baseURL;
}

const api = axios.create({
  baseURL: getBaseURL(),
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers = config.headers ?? {};
      (config.headers as Record<string, string>).Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (typeof window !== "undefined" && status === 401) {
      try {
        localStorage.removeItem("access_token");
        localStorage.removeItem("role");
        localStorage.removeItem("username");
      } catch {}
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

// RAG helpers
export async function ragIngestTexts(params: { collection: string; texts: string[]; metadatas?: any[] }) {
  const { collection, texts, metadatas } = params;
  const { data } = await api.post("/rag/ingest-texts", { collection, texts, metadatas });
  return data as { added: number };
}

export async function ragIngestUrls(params: { collection: string; urls: string[] }) {
  const { collection, urls } = params;
  const { data } = await api.post("/rag/ingest-urls", { collection, urls });
  return data as { added: number };
}

export async function ragIngestFiles(params: { collection: string; files: File[] }) {
  const { collection, files } = params;
  const fd = new FormData();
  fd.append("collection", collection);
  for (const f of files) fd.append("files", f);
  const { data } = await api.post("/rag/ingest-files", fd, { headers: { "Content-Type": "multipart/form-data" } });
  return data as { added: number };
}

export async function ragQuery(params: { collection: string; queryText: string; topK?: number }) {
  const { collection, queryText, topK = 5 } = params;
  const { data } = await api.post("/rag/query", { collection, query_text: queryText, top_k: topK });
  return data as { results: Array<{ text: string; metadata?: any }> };
}

export async function ragCollections() {
  const { data } = await api.get("/rag/collections");
  return data as { collections: string[] };
}

export async function ragListDocs(collection: string) {
  const { data } = await api.get(`/rag/collections/${encodeURIComponent(collection)}/docs`);
  return data as { docs: any[] };
}

export async function ragDeleteCollection(collection: string) {
  const { data } = await api.delete(`/rag/collections/${encodeURIComponent(collection)}`);
  return data as { deleted: string };
}

export async function ragDeleteDoc(params: { collection: string; docId: string }) {
  const { collection, docId } = params;
  const { data } = await api.delete(`/rag/collections/${encodeURIComponent(collection)}/docs/${encodeURIComponent(docId)}`);
  return data as { deleted: string };
}

// HITL helpers
export async function hitlStart(params: { topic: string; style?: string | null }) {
  const { topic, style } = params;
  const { data } = await api.post("/hitl/start", { topic, style });
  return data as { session_id: string; topic: string; research?: string };
}

export async function hitlComplete(params: { session_id: string; approve: boolean; feedback?: string | null }) {
  const { session_id, approve, feedback } = params;
  const { data } = await api.post("/hitl/complete", { session_id, approve, feedback });
  return data as { status: string; session_id: string; content?: string };
}

export async function hitlGet(session_id: string) {
  const { data } = await api.get(`/hitl/${encodeURIComponent(session_id)}`);
  return data as { session: any; actions: any[] };
}

export async function hitlList(params?: { status?: string; limit?: number; offset?: number }) {
  const { status, limit = 50, offset = 0 } = params || {};
  const search = new URLSearchParams();
  if (status) search.set("status", status);
  if (limit != null) search.set("limit", String(limit));
  if (offset != null) search.set("offset", String(offset));
  const qs = search.toString();
  const { data } = await api.get(`/hitl${qs ? `?${qs}` : ""}`);
  return data as { items: any[]; count: number };
}

export async function hitlCancel(params: { session_id: string; reason?: string | null }) {
  const { session_id, reason } = params;
  const { data } = await api.post("/hitl/cancel", { session_id, reason });
  return data as { status: string; session_id: string };
}

export default api;
