"use client";

import React, { useMemo, useState } from "react";
import Protected from "../../../components/Protected";
import { Button } from "@/components/ui/button";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ragCollections, ragListDocs, ragDeleteCollection, ragDeleteDoc } from "@/lib/api";
import { toast } from "sonner";
import { PageHeader } from "../../../components/PageHeader";
import { PageSection } from "../../../components/PageSection";
import { CardListSkeleton } from "../../../components/CardListSkeleton";
import EmptyState from "../../../components/EmptyState";
import { Badge } from "../../../components/Badge";

export default function RagCollectionsPage() {
  const qc = useQueryClient();
  const [selected, setSelected] = useState<string>("");

  const { data: colsData, isLoading: colsLoading } = useQuery({
    queryKey: ["rag", "collections"],
    queryFn: () => ragCollections(),
  });

  const collections = colsData?.collections || [];
  const hasSelected = useMemo(() => !!selected, [selected]);

  const { data: docsData, isLoading: docsLoading } = useQuery({
    queryKey: ["rag", "docs", selected],
    queryFn: () => ragListDocs(selected),
    enabled: hasSelected,
  });

  const delCollection = useMutation({
    mutationFn: (name: string) => ragDeleteCollection(name),
    onSuccess: async (res, name) => {
      toast.success(`Coleção removida: ${name}`);
      setSelected("");
      await qc.invalidateQueries({ queryKey: ["rag", "collections"] });
      await qc.invalidateQueries({ queryKey: ["rag", "docs"] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || "Erro ao remover coleção");
    },
  });

  const delDoc = useMutation({
    mutationFn: ({ collection, docId }: { collection: string; docId: string }) => ragDeleteDoc({ collection, docId }),
    onSuccess: async () => {
      toast.success("Documento removido");
      if (selected) await qc.invalidateQueries({ queryKey: ["rag", "docs", selected] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || "Erro ao remover documento");
    },
  });

  const onDeleteCollection = (name: string) => {
    if (!name) return;
    if (!window.confirm(`Tem certeza que deseja remover a coleção "${name}"?`)) return;
    delCollection.mutate(name);
  };

  const onDeleteDoc = (docId: string) => {
    if (!selected || !docId) return;
    if (!window.confirm(`Remover doc ${docId}?`)) return;
    delDoc.mutate({ collection: selected, docId });
  };

  return (
    <Protected>
      <div className="space-y-4">
        <PageHeader
          title="RAG · Coleções"
          subtitle="Gerencie coleções e documentos indexados."
        />

        <div className="grid gap-4 md:grid-cols-2">
          <PageSection title="Coleções" className="h-full">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-medium">Coleções</h2>
              {colsLoading && <span className="text-xs text-gray-500">Carregando...</span>}
            </div>
            {colsLoading ? (
              <CardListSkeleton count={3} />
            ) : collections.length === 0 ? (
              <EmptyState
                icon="🗂️"
                title="Nenhuma coleção ainda"
                description="Ingere documentos em RAG · Ingest para criar coleções de conhecimento."
                action={{ label: "Ingerir documentos", href: "/rag/ingest" }}
              />
            ) : (
              <ul className="divide-y text-sm">
                {collections.map((c: string) => (
                  <li key={c} className="py-2 flex items-center justify-between">
                    <button
                      className={`text-left ${selected === c ? "font-semibold" : ""}`}
                      onClick={() => setSelected(c)}
                      title={`Abrir coleção ${c}`}
                    >
                      {c}
                    </button>
                    <Button variant="outline" onClick={() => onDeleteCollection(c)}>Remover</Button>
                  </li>
                ))}
              </ul>
            )}
          </PageSection>

          <PageSection title="Documentos" className="h-full">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-medium flex items-center gap-2">
                Documentos
                {selected && (
                  <Badge variant="info" className="text-[11px]">
                    {selected}
                  </Badge>
                )}
              </h2>
              {docsLoading && hasSelected && <span className="text-xs text-gray-500">Carregando...</span>}
            </div>
            {!hasSelected ? (
              <EmptyState
                icon="📂"
                title="Nenhuma coleção selecionada"
                description="Escolha uma coleção na lista ao lado para visualizar seus documentos."
              />
            ) : docsLoading ? (
              <CardListSkeleton count={3} />
            ) : !docsData?.docs || docsData.docs.length === 0 ? (
              <EmptyState
                icon="📄"
                title="Sem documentos"
                description="Esta coleção ainda não possui documentos indexados."
                action={{ label: "Ingerir documentos", href: "/rag/ingest" }}
              />
            ) : (
              <ul className="divide-y text-sm">
                {docsData.docs.map((d: any, idx: number) => (
                  <li key={d.id || idx} className="py-2 flex items-center justify-between">
                    <div className="truncate max-w-[70%]">
                      <div className="font-medium truncate">{d.id || d.metadata?.title || `doc-${idx + 1}`}</div>
                      {d.metadata && (
                        <div className="text-xs text-gray-500 truncate">{JSON.stringify(d.metadata)}</div>
                      )}
                    </div>
                    <Button variant="outline" onClick={() => onDeleteDoc(d.id || String(idx))}>Remover</Button>
                  </li>
                ))}
              </ul>
            )}
          </PageSection>
        </div>
      </div>
    </Protected>
  );
}
