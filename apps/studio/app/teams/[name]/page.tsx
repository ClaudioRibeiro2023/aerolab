"use client";
import React, { useState, useEffect } from "react";
import Protected from "../../../components/Protected";
import Link from "next/link";
import { useParams } from "next/navigation";
import api from "../../../lib/api";
import { toast } from "sonner";
import { useAuth } from "../../../store/auth";
import { getHistoryByFilter, getHistoryStats, ExecutionRecord } from "../../../lib/executionHistory";

const Icons = {
  back: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>),
  edit: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>),
  play: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /></svg>),
  user: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>),
  team: (<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>),
  clock: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  check: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>),
  chart: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>),
  arrow: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>),
  spinner: (<svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>),
};

interface TeamData {
  name: string;
  members: string[];
  description?: string;
}

interface ExecutionHistory {
  id: string;
  prompt: string;
  result: string;
  timestamp: Date;
  duration: number;
  status: "success" | "error";
}

export default function TeamDetailsPage() {
  const params = useParams();
  const { role } = useAuth();
  const teamName = decodeURIComponent((params?.name as string) || "");

  const [team, setTeam] = useState<TeamData | null>(null);
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<ExecutionHistory[]>([]);

  useEffect(() => {
    loadTeam();
    loadHistory();
  }, [teamName]);

  const loadTeam = async () => {
    if (!teamName) return;
    setLoading(true);
    try {
      const { data } = await api.get(`/teams/${encodeURIComponent(teamName)}`);
      setTeam(data);
    } catch (e) {
      toast.error("Erro ao carregar time");
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = () => {
    // Carregar histórico do utilitário executionHistory
    const records = getHistoryByFilter({ type: "team", name: teamName });
    setHistory(records.map(r => ({
      id: r.id,
      prompt: r.prompt,
      result: r.result,
      timestamp: new Date(r.timestamp),
      duration: r.duration,
      status: r.status,
    })));
  };

  // Métricas reais do histórico
  const stats = getHistoryStats({ type: "team", name: teamName });
  const metrics = {
    totalRuns: stats.total,
    successRate: stats.successRate,
    avgDuration: stats.avgDuration.toFixed(1),
    lastRun: history.length > 0 ? history[0].timestamp : null,
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

  if (!team) {
    return (
      <Protected>
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Time não encontrado</h2>
          <Link href="/teams" className="text-blue-600 mt-2 inline-block">← Voltar</Link>
        </div>
      </Protected>
    );
  }

  return (
    <Protected>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/teams" className="p-2 text-gray-500 hover:text-purple-600 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Voltar">{Icons.back}</Link>
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white shadow-lg">
              {Icons.team}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{team.name}</h1>
              <p className="text-gray-500 dark:text-gray-400">{team.description || `${team.members.length} membros`}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {role === "admin" && (
              <Link
                href={`/teams/${encodeURIComponent(team.name)}/edit`}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
              >
                {Icons.edit} Editar
              </Link>
            )}
            <Link
              href={`/teams/${encodeURIComponent(team.name)}/run`}
              className="btn-primary flex items-center gap-2"
            >
              {Icons.play} Executar
            </Link>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-gray-100 dark:border-slate-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg text-purple-600 dark:text-purple-400">{Icons.chart}</div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{metrics.totalRuns}</p>
                <p className="text-sm text-gray-500">Execuções</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-gray-100 dark:border-slate-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg text-green-600 dark:text-green-400">{Icons.check}</div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{metrics.successRate}%</p>
                <p className="text-sm text-gray-500">Taxa de Sucesso</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-gray-100 dark:border-slate-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg text-blue-600 dark:text-blue-400">{Icons.clock}</div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{metrics.avgDuration}s</p>
                <p className="text-sm text-gray-500">Tempo Médio</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-gray-100 dark:border-slate-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg text-orange-600 dark:text-orange-400">{Icons.user}</div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{team.members.length}</p>
                <p className="text-sm text-gray-500">Membros</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Pipeline */}
          <div className="md:col-span-2 bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Pipeline de Execução</h3>
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {team.members.map((member, i) => (
                <React.Fragment key={member}>
                  <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-gray-100 dark:bg-slate-700 min-w-fit">
                    <div className="w-8 h-8 rounded-lg bg-purple-500 text-white flex items-center justify-center text-sm font-bold">
                      {i + 1}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{member}</p>
                      <p className="text-xs text-gray-500">Agente</p>
                    </div>
                  </div>
                  {i < team.members.length - 1 && (
                    <div className="text-gray-400 dark:text-gray-500 flex-shrink-0">{Icons.arrow}</div>
                  )}
                </React.Fragment>
              ))}
            </div>
            {team.members.length === 0 && (
              <p className="text-gray-500 text-center py-4">Nenhum membro no time</p>
            )}
          </div>

          {/* Quick Actions */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Ações Rápidas</h3>
            <div className="space-y-2">
              <Link
                href={`/teams/${encodeURIComponent(team.name)}/run`}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400 hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors"
              >
                {Icons.play}
                <span>Executar Time</span>
              </Link>
              {role === "admin" && (
                <Link
                  href={`/teams/${encodeURIComponent(team.name)}/edit`}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-gray-50 dark:bg-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-600 transition-colors"
                >
                  {Icons.edit}
                  <span>Editar Configurações</span>
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Execution History */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-white">Histórico de Execuções</h3>
            <span className="text-sm text-gray-500">{history.length} execução(ões)</span>
          </div>
          
          {history.length === 0 ? (
            <p className="text-gray-500 text-center py-8">Nenhuma execução registrada</p>
          ) : (
            <div className="space-y-3">
              {history.slice(0, 5).map((exec) => (
                <div key={exec.id} className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 dark:bg-slate-700/50">
                  <div className={`w-3 h-3 rounded-full ${exec.status === "success" ? "bg-green-500" : "bg-red-500"}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{exec.prompt}</p>
                    <p className="text-xs text-gray-500">
                      {exec.timestamp.toLocaleDateString("pt-BR")} às {exec.timestamp.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })} • {exec.duration}s
                    </p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${exec.status === "success" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"}`}>
                    {exec.status === "success" ? "Sucesso" : "Erro"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Protected>
  );
}
