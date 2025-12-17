"use client";
import React, { useState } from "react";
import Protected from "../../../components/Protected";
import { ragQuery } from "@/lib/api";
import { toast } from "sonner";
import { PageHeader } from "../../../components/PageHeader";
import { PageSection } from "../../../components/PageSection";
import EmptyState from "../../../components/EmptyState";

const Icons = {
  search: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>),
  spinner: (<svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>),
  doc: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>),
};

export default function RagQueryPage() {
  const [collection, setCollection] = useState("");
  const [queryText, setQueryText] = useState("");
  const [topK, setTopK] = useState(5);
  const [results, setResults] = useState<Array<{ text: string; metadata?: any }>>([]);
  const [loading, setLoading] = useState(false);

  const onQuery = async () => {
    if (!collection || !queryText) { toast.error("Preencha collection e query"); return; }
    setLoading(true);
    try {
      const data = await ragQuery({ collection, queryText, topK });
      setResults(data.results || []);
      toast.success(`Encontrados ${data.results?.length || 0} resultados`);
    } catch (err: any) { toast.error(err?.response?.data?.detail || "Erro na consulta"); }
    finally { setLoading(false); }
  };

  return (
    <Protected>
      <div className="space-y-6">
        <PageHeader
          title="RAG · Query"
          subtitle="Consulte documentos indexados via busca semântica."
        />

        <PageSection title="Consulta">
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Collection</label>
              <input type="text" placeholder="nome-da-collection" value={collection} onChange={(e) => setCollection(e.target.value)} className="input-modern" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Query</label>
              <input type="text" placeholder="Digite sua pergunta..." value={queryText} onChange={(e) => setQueryText(e.target.value)} className="input-modern" onKeyDown={(e) => e.key === "Enter" && onQuery()} />
            </div>
            <div className="flex items-end gap-2">
              <div className="w-20">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Top K</label>
                <input type="number" min={1} max={20} value={topK} onChange={(e) => setTopK(parseInt(e.target.value || "5", 10))} className="input-modern text-center" placeholder="5" title="Número de resultados" />
              </div>
              <button onClick={onQuery} disabled={loading} className="btn-primary flex-1 flex items-center justify-center gap-2">
                {loading ? Icons.spinner : Icons.search} {loading ? "..." : "Buscar"}
              </button>
            </div>
          </div>
        </PageSection>

        <PageSection title="Resultados">
          {results.length === 0 ? (
            <EmptyState
              icon="📄"
              title="Nenhum resultado ainda"
              description="Faça uma consulta para ver trechos relevantes dos documentos indexados."
            />
          ) : (
            <ul className="space-y-3">
              {results.map((r, idx) => (
                <li key={idx} className="p-4 bg-gray-50 dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-700">
                  <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{r.text}</p>
                  {r.metadata && <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 font-mono">{JSON.stringify(r.metadata)}</div>}
                </li>
              ))}
            </ul>
          )}
        </PageSection>
      </div>
    </Protected>
  );
}
