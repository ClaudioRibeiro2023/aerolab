"use client";
import React, { useEffect, useState } from "react";
import Protected from "../../components/Protected";
import { PageHeader } from "../../components/PageHeader";
import { hitlStart, hitlComplete, hitlList, hitlGet, hitlCancel } from "@/lib/api";
import { toast } from "sonner";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

type HitlSessionItem = {
  id: string;
  topic: string;
  status: string;
};

type HitlListResponse = {
  items: HitlSessionItem[];
};

type HitlAction = {
  id: string;
  action: string;
  created_at: string;
  payload?: string;
};

type HitlDetailResponse = {
  session?: {
    research?: string;
    final_text?: string;
  };
  actions?: HitlAction[];
};

type ApiError = {
  response?: {
    data?: {
      detail?: string;
    };
  };
};

function getErrorMessage(err: unknown, fallback: string): string {
  const apiError = err as ApiError;
  const detail = apiError.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  return fallback;
}

const Icons = {
  play: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  check: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  x: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  refresh: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>),
  spinner: (<svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>),
  shield: (<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>),
};

const statusColors: Record<string, string> = {
  started: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  completed: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  rejected: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  cancelled: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
};

export default function HitlPage() {
  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [research, setResearch] = useState<string>("");
  const [feedback, setFeedback] = useState("");
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const qc = useQueryClient();

  // Lista de sessões
  const {
    data: listData,
    isLoading: listLoading,
    refetch: refetchList,
  } = useQuery<HitlListResponse>({
    queryKey: ["hitl", "list", statusFilter],
    queryFn: () => hitlList({ status: statusFilter }),
  });

  // Detalhe da sessão selecionada
  const { data: detailData } = useQuery<HitlDetailResponse>({
    queryKey: ["hitl", "detail", sessionId],
    queryFn: () => hitlGet(sessionId as string),
    enabled: !!sessionId,
  });

  useEffect(() => {
    if (detailData?.session) {
      setResearch(detailData.session?.research || "");
      setContent(detailData.session?.final_text || "");
    }
  }, [detailData]);

  // Mutations
  const startMutation = useMutation({
    mutationFn: hitlStart,
    onSuccess: async (data) => {
      setSessionId(data.session_id);
      setResearch(data.research || "");
      setContent("");
      toast.success("Sessão iniciada");
      await qc.invalidateQueries({ queryKey: ["hitl", "list"] });
    },
    onError: (err: unknown) => {
      toast.error(getErrorMessage(err, "Erro ao iniciar sessão"));
    },
  });

  const onStart = async () => {
    if (!topic.trim()) {
      toast.error("Informe um tópico");
      return;
    }
    setLoading("start");
    startMutation.mutate({ topic, style: style || undefined }, { onSettled: () => setLoading(null) });
  };

  const completeMutation = useMutation({
    mutationFn: hitlComplete,
    onSuccess: async (data) => {
      if (data?.content) setContent(data.content);
      toast.success("Ação concluída");
      await qc.invalidateQueries({ queryKey: ["hitl", "list"] });
      if (sessionId) await qc.invalidateQueries({ queryKey: ["hitl", "detail", sessionId] });
    },
    onError: (err: unknown) => {
      toast.error(getErrorMessage(err, "Erro na ação"));
    },
  });

  const onApprove = async () => {
    if (!sessionId) return;
    setLoading("approve");
    completeMutation.mutate({ session_id: sessionId, approve: true, feedback: feedback || undefined }, { onSettled: () => setLoading(null) });
  };

  const onReject = async () => {
    if (!sessionId) return;
    setLoading("reject");
    completeMutation.mutate({ session_id: sessionId, approve: false }, { onSettled: () => setLoading(null) });
  };

  const onSelectSession = (id: string) => {
    setSessionId(id);
  };

  const cancelMutation = useMutation({
    mutationFn: hitlCancel,
    onSuccess: async () => {
      toast.success("Sessão cancelada");
      await qc.invalidateQueries({ queryKey: ["hitl", "list"] });
      if (sessionId) await qc.invalidateQueries({ queryKey: ["hitl", "detail", sessionId] });
    },
    onError: (err: unknown) => {
      toast.error(getErrorMessage(err, "Erro ao cancelar"));
    },
  });

  const onCancel = async () => {
    if (!sessionId) return;
    setLoading("cancel");
    cancelMutation.mutate({ session_id: sessionId }, { onSettled: () => setLoading(null) });
  };

  return (
    <Protected>
      <div className="space-y-6">
        <PageHeader
          title="Human-in-the-Loop"
          subtitle="Revisão humana para conteúdos gerados por IA"
          leadingAction={
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white">
              {Icons.shield}
            </div>
          }
          breadcrumbs={[
            { label: "Workflows", href: "/workflows" },
            { label: "HITL" },
          ]}
        />

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Criar Sessão */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">{Icons.play} Nova Sessão</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tópico</label>
                <input type="text" placeholder="Ex: Artigo sobre IA" value={topic} onChange={(e) => setTopic(e.target.value)} className="input-modern" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Estilo (opcional)</label>
                <input type="text" placeholder="Ex: Formal, Técnico, Casual" value={style} onChange={(e) => setStyle(e.target.value)} className="input-modern" />
              </div>
              <button onClick={onStart} disabled={loading === "start"} className="btn-primary w-full flex items-center justify-center gap-2">
                {loading === "start" ? Icons.spinner : Icons.play} {loading === "start" ? "Iniciando..." : "Iniciar Sessão"}
              </button>
            </div>

            {research && (
              <div className="pt-4 border-t border-gray-100 dark:border-slate-700">
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">📊 Pesquisa</h3>
                <pre className="text-sm whitespace-pre-wrap p-4 bg-gray-50 dark:bg-slate-900 rounded-xl text-gray-700 dark:text-gray-300 max-h-48 overflow-y-auto">{research}</pre>
              </div>
            )}

            {sessionId && (
              <div className="pt-4 border-t border-gray-100 dark:border-slate-700 space-y-3">
                <h3 className="font-medium text-gray-900 dark:text-white">✍️ Revisão</h3>
                <textarea placeholder="Feedback do revisor (opcional)" value={feedback} onChange={(e) => setFeedback(e.target.value)} className="input-modern min-h-[80px]" />
                <div className="flex gap-2">
                  <button onClick={onApprove} disabled={loading === "approve"} className="btn-primary flex-1 flex items-center justify-center gap-2">
                    {loading === "approve" ? Icons.spinner : Icons.check} Aprovar
                  </button>
                  <button onClick={onReject} disabled={loading === "reject"} className="btn-secondary flex-1 flex items-center justify-center gap-2">
                    {Icons.x} Rejeitar
                  </button>
                  <button onClick={onCancel} disabled={loading === "cancel"} className="btn-secondary px-3" title="Cancelar">
                    ✕
                  </button>
                </div>
              </div>
            )}

            {content && (
              <div className="pt-4 border-t border-gray-100 dark:border-slate-700">
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">📝 Conteúdo Final</h3>
                <pre className="text-sm whitespace-pre-wrap p-4 bg-green-50 dark:bg-green-900/20 rounded-xl text-gray-700 dark:text-gray-300 max-h-48 overflow-y-auto">{content}</pre>
              </div>
            )}

            {sessionId && (detailData?.actions?.length ?? 0) > 0 && (
              <div className="pt-4 border-t border-gray-100 dark:border-slate-700">
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">🕒 Histórico</h3>
                <ul className="space-y-2">
                  {detailData?.actions?.map((a) => (
                    <li key={a.id} className="p-3 bg-gray-50 dark:bg-slate-900 rounded-xl text-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-gray-900 dark:text-white">{a.action}</span>
                        <span className="text-xs text-gray-500">{a.created_at}</span>
                      </div>
                      {a.payload && <div className="mt-1 text-gray-600 dark:text-gray-400 text-xs">{a.payload}</div>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Lista de Sessões */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Sessões</h2>
              <div className="flex items-center gap-2">
                <select aria-label="Filtrar" className="input-modern py-1.5 text-sm" value={statusFilter || ""} onChange={(e) => setStatusFilter(e.target.value || undefined)}>
                  <option value="">Todas</option>
                  <option value="started">Iniciadas</option>
                  <option value="completed">Concluídas</option>
                  <option value="rejected">Rejeitadas</option>
                  <option value="cancelled">Canceladas</option>
                </select>
                <button onClick={() => refetchList()} className="p-2 text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors" title="Atualizar">
                  {Icons.refresh}
                </button>
              </div>
            </div>

            {listLoading ? (
              <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="h-16 bg-gray-100 dark:bg-slate-700 rounded-xl animate-pulse" />)}</div>
            ) : !listData?.items?.length ? (
              <div className="text-center py-8 text-gray-400">
                <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-gray-100 dark:bg-slate-700 flex items-center justify-center">{Icons.shield}</div>
                <p>Nenhuma sessão encontrada</p>
              </div>
            ) : (
              <ul className="space-y-2 max-h-[500px] overflow-y-auto">
                {listData.items.map((it) => (
                  <li key={it.id} onClick={() => onSelectSession(it.id)} className={`p-4 rounded-xl cursor-pointer transition-all border ${sessionId === it.id ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" : "border-transparent bg-gray-50 dark:bg-slate-900 hover:bg-gray-100 dark:hover:bg-slate-700"}`}>
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-gray-900 dark:text-white">{it.topic}</div>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${statusColors[it.status] || "bg-gray-100 text-gray-800"}`}>{it.status}</span>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 font-mono">{it.id}</div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </Protected>
  );
}
