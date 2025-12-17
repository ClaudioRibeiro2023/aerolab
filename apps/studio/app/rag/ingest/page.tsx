"use client";

import React, { useState } from "react";
import Protected from "../../../components/Protected";
import { ragIngestTexts, ragIngestUrls, ragIngestFiles } from "@/lib/api";
import { useAuth } from "@/store/auth";
import { toast } from "sonner";
import { PageHeader } from "../../../components/PageHeader";
import { PageSection } from "../../../components/PageSection";

const Icons = {
  upload: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>),
  text: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>),
  link: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>),
  file: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>),
  spinner: (<svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>),
};

export default function RagIngestPage() {
  const { role } = useAuth();
  const isAdmin = role === "admin";
  const [collection, setCollection] = useState("");
  const [texts, setTexts] = useState("");
  const [urls, setUrls] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  const onIngestTexts = async () => {
    if (!isAdmin || !collection || !texts.trim()) { toast.error("Preencha os campos"); return; }
    setLoading("texts");
    try {
      const list = texts.split("\n").map(t => t.trim()).filter(Boolean);
      const res = await ragIngestTexts({ collection, texts: list });
      toast.success(`Textos adicionados: ${res.added}`);
    } catch (err: any) { toast.error("Erro ao ingerir"); }
    finally { setLoading(null); }
  };

  const onIngestUrls = async () => {
    if (!isAdmin || !collection || !urls.trim()) { toast.error("Preencha os campos"); return; }
    setLoading("urls");
    try {
      const list = urls.split("\n").map(t => t.trim()).filter(Boolean);
      const res = await ragIngestUrls({ collection, urls: list });
      toast.success(`URLs adicionadas: ${res.added}`);
    } catch (err: any) { toast.error("Erro ao ingerir"); }
    finally { setLoading(null); }
  };

  const onIngestFiles = async () => {
    if (!isAdmin || !collection || !files?.length) { toast.error("Preencha os campos"); return; }
    setLoading("files");
    try {
      const res = await ragIngestFiles({ collection, files: Array.from(files) });
      toast.success(`Arquivos processados: ${res.added}`);
    } catch (err: any) { toast.error("Erro ao ingerir"); }
    finally { setLoading(null); }
  };

  return (
    <Protected>
      <div className="space-y-6">
        <PageHeader
          title="RAG · Ingest"
          subtitle="Adicione documentos à base de conhecimento."
        />

        {!isAdmin && (
          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200 p-4 rounded-xl text-sm">
            Apenas administradores podem ingerir conteúdo.
          </div>
        )}

        <PageSection title="Collection">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Collection</label>
          <input type="text" placeholder="nome-da-collection" value={collection} onChange={(e) => setCollection(e.target.value)} className="input-modern max-w-md" />
        </PageSection>

        <div className="grid gap-6 md:grid-cols-3">
          {/* Texts */}
          <PageSection title="Textos">
            <div className="flex items-center gap-2 mb-4 text-blue-600 dark:text-blue-400">{Icons.text}<h3 className="font-semibold text-gray-900 dark:text-white">Textos</h3></div>
            <textarea value={texts} onChange={(e) => setTexts(e.target.value)} placeholder="Um texto por linha..." className="input-modern min-h-[120px] text-sm mb-3" />
            <button onClick={onIngestTexts} disabled={!isAdmin || loading === "texts"} className="btn-primary w-full flex items-center justify-center gap-2">
              {loading === "texts" ? Icons.spinner : Icons.upload} {loading === "texts" ? "Enviando..." : "Ingerir Textos"}
            </button>
          </PageSection>

          {/* URLs */}
          <PageSection title="URLs">
            <div className="flex items-center gap-2 mb-4 text-purple-600 dark:text-purple-400">{Icons.link}<h3 className="font-semibold text-gray-900 dark:text-white">URLs</h3></div>
            <textarea value={urls} onChange={(e) => setUrls(e.target.value)} placeholder="https://exemplo.com..." className="input-modern min-h-[120px] text-sm mb-3" />
            <button onClick={onIngestUrls} disabled={!isAdmin || loading === "urls"} className="btn-primary w-full flex items-center justify-center gap-2">
              {loading === "urls" ? Icons.spinner : Icons.upload} {loading === "urls" ? "Enviando..." : "Ingerir URLs"}
            </button>
          </PageSection>

          {/* Files */}
          <PageSection title="Arquivos">
            <div className="flex items-center gap-2 mb-4 text-green-600 dark:text-green-400">{Icons.file}<h3 className="font-semibold text-gray-900 dark:text-white">Arquivos</h3></div>
            <div className="border-2 border-dashed border-gray-200 dark:border-slate-600 rounded-xl p-4 text-center mb-3">
              <input id="ingest-files" type="file" multiple onChange={(e) => setFiles(e.target.files)} className="hidden" />
              <label htmlFor="ingest-files" className="cursor-pointer text-sm text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                {files?.length ? `${files.length} arquivo(s) selecionado(s)` : "Clique para selecionar PDF, MD, TXT"}
              </label>
            </div>
            <button onClick={onIngestFiles} disabled={!isAdmin || loading === "files"} className="btn-primary w-full flex items-center justify-center gap-2">
              {loading === "files" ? Icons.spinner : Icons.upload} {loading === "files" ? "Enviando..." : "Ingerir Arquivos"}
            </button>
          </PageSection>
        </div>
      </div>
    </Protected>
  );
}
