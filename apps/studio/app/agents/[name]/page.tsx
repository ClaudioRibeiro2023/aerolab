"use client";
import React, { useState, useEffect } from "react";
import Protected from "../../../components/Protected";
import Link from "next/link";
import { useParams } from "next/navigation";
import api from "../../../lib/api";
import { toast } from "sonner";
import { getHistoryByFilter, getHistoryStats, ExecutionRecord } from "../../../lib/executionHistory";

const Icons = {
  back: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>),
  edit: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>),
  chat: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>),
  spinner: (<svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>),
  cpu: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>),
  clock: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  chart: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>),
  check: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
};

interface AgentData {
  name: string;
  role?: string;
  model_provider?: string;
  model_id?: string;
  instructions?: string[];
  use_database?: boolean;
  add_history_to_context?: boolean;
  markdown?: boolean;
  debug_mode?: boolean;
}

interface HistoryItem {
  id: string;
  prompt: string;
  result: string;
  timestamp: Date;
  duration: number;
  status: "success" | "error";
}

export default function AgentDetailsPage() {
  const params = useParams();
  const agentName = decodeURIComponent((params?.name as string) || "");

  const [loading, setLoading] = useState(true);
  const [agent, setAgent] = useState<AgentData | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // Métricas reais do histórico
  const stats = getHistoryStats({ type: "agent", name: agentName });
  const metrics = {
    executions: stats.total,
    avgTime: stats.avgDuration.toFixed(2),
    successRate: stats.successRate.toFixed(1),
    errors: stats.error,
  };

  useEffect(() => {
    loadAgent();
    loadHistory();
  }, [agentName]);

  const loadHistory = () => {
    const records = getHistoryByFilter({ type: "agent", name: agentName });
    setHistory(records.map(r => ({
      id: r.id,
      prompt: r.prompt,
      result: r.result,
      timestamp: new Date(r.timestamp),
      duration: r.duration,
      status: r.status,
    })));
  };

  const loadAgent = async () => {
    if (!agentName) return;
    setLoading(true);
    try {
      const res = await api.get(`/agents/${encodeURIComponent(agentName)}`);
      setAgent(res.data);
    } catch (e: any) {
      toast.error("Erro ao carregar agente");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Protected>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            {Icons.spinner}
            <p className="mt-2 text-gray-500">Carregando...</p>
          </div>
        </div>
      </Protected>
    );
  }

  if (!agent) {
    return (
      <Protected>
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Agente não encontrado</h2>
          <Link href="/agents" className="text-blue-600 mt-2 inline-block">← Voltar para agentes</Link>
        </div>
      </Protected>
    );
  }

  return (
    <Protected>
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Link href="/agents" className="p-2 text-gray-500 hover:text-blue-600 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Voltar">{Icons.back}</Link>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{agent.name}</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm">{agent.role || "Agente genérico"}</p>
          </div>
          <div className="flex items-center gap-2">
            <Link href={`/chat?agent=${encodeURIComponent(agent.name)}`} className="btn-secondary flex items-center gap-2">
              {Icons.chat} Chat
            </Link>
            <Link href={`/agents/${encodeURIComponent(agent.name)}/edit`} className="btn-primary flex items-center gap-2">
              {Icons.edit} Editar
            </Link>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600">{Icons.chart}</div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Execuções</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{metrics.executions}</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600">{Icons.clock}</div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Tempo Médio</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{metrics.avgTime}s</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-600">{Icons.check}</div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Taxa de Sucesso</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{metrics.successRate}%</p>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-600">{Icons.cpu}</div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Erros</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{metrics.errors}</p>
          </div>
        </div>

        {/* Config Info */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Modelo */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Configuração do Modelo</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Provedor</span>
                <span className="font-medium text-gray-900 dark:text-white capitalize">{agent.model_provider || "openai"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Modelo</span>
                <span className="font-medium text-gray-900 dark:text-white">{agent.model_id || "gpt-4.1"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Database</span>
                <span className={`px-2 py-1 rounded-full text-xs ${agent.use_database ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-gray-400"}`}>
                  {agent.use_database ? "Ativo" : "Inativo"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Histórico</span>
                <span className={`px-2 py-1 rounded-full text-xs ${agent.add_history_to_context ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-gray-400"}`}>
                  {agent.add_history_to_context ? "Ativo" : "Inativo"}
                </span>
              </div>
            </div>
          </div>

          {/* Instruções */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Instruções ({agent.instructions?.length || 0})</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {agent.instructions && agent.instructions.length > 0 ? (
                agent.instructions.map((inst, i) => (
                  <div key={i} className="p-3 bg-gray-50 dark:bg-slate-900 rounded-lg text-sm text-gray-700 dark:text-gray-300">
                    {inst}
                  </div>
                ))
              ) : (
                <p className="text-gray-400 italic">Nenhuma instrução definida</p>
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Ações Rápidas</h3>
          <div className="flex flex-wrap gap-3">
            <Link href={`/chat?agent=${encodeURIComponent(agent.name)}`} className="px-4 py-2 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors text-sm font-medium">
              💬 Iniciar Conversa
            </Link>
            <Link href={`/agents/${encodeURIComponent(agent.name)}/edit`} className="px-4 py-2 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors text-sm font-medium">
              ✏️ Editar Configurações
            </Link>
            <Link href="/agents/new" className="px-4 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-lg hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors text-sm font-medium">
              📋 Criar Variante
            </Link>
            <Link href="/logs" className="px-4 py-2 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors text-sm font-medium">
              📊 Ver Logs
            </Link>
          </div>
        </div>
      </div>
    </Protected>
  );
}
