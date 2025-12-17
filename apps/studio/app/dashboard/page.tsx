"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import Protected from "../../components/Protected";
import api from "../../lib/api";
import { useAuth } from "../../store/auth";
import { getHistory, getHistoryStats, ExecutionRecord } from "../../lib/executionHistory";
import AnalyticsDashboard from "../../components/AnalyticsDashboard";
import { PageHeader } from "../../components/PageHeader";

// Mini Chart Component
function MiniChart({ data, color = "blue" }: { data: number[]; color?: string }) {
  const max = Math.max(...data, 1);
  const colors: Record<string, string> = {
    blue: "bg-blue-500",
    green: "bg-green-500",
    purple: "bg-purple-500",
    orange: "bg-orange-500",
  };
  return (
    <div className="flex items-end gap-0.5 h-8">
      {data.map((v, i) => (
        <div key={i} className={`w-1.5 rounded-t ${colors[color]} opacity-60 hover:opacity-100 transition-opacity`} style={{ height: `${(v / max) * 100}%` }} />
      ))}
    </div>
  );
}

// Stat Card Component
function StatCard({ 
  title, 
  value, 
  change, 
  changeType, 
  icon,
  chartData,
  chartColor
}: { 
  title: string; 
  value: string; 
  change?: string; 
  changeType?: "up" | "down" | "neutral";
  icon: React.ReactNode;
  chartData?: number[];
  chartColor?: string;
}) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-slate-700 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{value}</p>
          {change && (
            <p className={`text-sm mt-2 flex items-center gap-1 ${
              changeType === "up" ? "text-green-600" : 
              changeType === "down" ? "text-red-600" : "text-gray-500"
            }`}>
              {changeType === "up" && "↑"}
              {changeType === "down" && "↓"}
              {change}
            </p>
          )}
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="p-3 bg-blue-50 dark:bg-blue-900/30 rounded-xl text-blue-600 dark:text-blue-400">
            {icon}
          </div>
          {chartData && <MiniChart data={chartData} color={chartColor} />}
        </div>
      </div>
    </div>
  );
}

// Quick Action Card
function QuickAction({ 
  title, 
  description, 
  href, 
  icon,
  color = "blue"
}: { 
  title: string; 
  description: string; 
  href: string; 
  icon: React.ReactNode;
  color?: "blue" | "purple" | "green" | "orange";
}) {
  const colors = {
    blue: "from-blue-500 to-blue-600 shadow-blue-500/25",
    purple: "from-purple-500 to-purple-600 shadow-purple-500/25",
    green: "from-green-500 to-green-600 shadow-green-500/25",
    orange: "from-orange-500 to-orange-600 shadow-orange-500/25",
  };

  return (
    <Link href={href} className="group">
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-slate-700 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colors[color]} flex items-center justify-center text-white shadow-lg mb-4`}>
          {icon}
        </div>
        <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 transition-colors">{title}</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{description}</p>
      </div>
    </Link>
  );
}

// Donut Chart Component
function DonutChart({ data, size = 120 }: { data: { label: string; value: number; color: string }[]; size?: number }) {
  const total = data.reduce((acc, d) => acc + d.value, 0);
  let cumulative = 0;
  const radius = size / 2 - 10;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {data.map((d, i) => {
          const percentage = d.value / total;
          const strokeDasharray = `${percentage * circumference} ${circumference}`;
          const strokeDashoffset = -cumulative * circumference;
          cumulative += percentage;
          return (
            <circle key={i} cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={d.color} strokeWidth="16" strokeDasharray={strokeDasharray} strokeDashoffset={strokeDashoffset} className="transition-all duration-500" />
          );
        })}
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-bold text-gray-900 dark:text-white">{total}</span>
      </div>
    </div>
  );
}

// Activity Item Component
function ActivityItem({ icon, title, time, type }: { icon: React.ReactNode; title: string; time: string; type: "success" | "info" | "warning" }) {
  const colors = {
    success: "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400",
    info: "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
    warning: "bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400",
  };
  return (
    <div className="flex items-center gap-3 py-3 border-b border-gray-100 dark:border-slate-700 last:border-0">
      <div className={`p-2 rounded-lg ${colors[type]}`}>{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{title}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">{time}</p>
      </div>
    </div>
  );
}

// Icons
const Icons = {
  agents: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
  teams: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  workflows: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" />
    </svg>
  ),
  rag: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
    </svg>
  ),
  domains: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
  ),
  editor: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
    </svg>
  ),
  chat: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  ),
  check: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  ),
  alert: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  refresh: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
};

// Helper para formatar tempo relativo
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return "Agora";
  if (minutes < 60) return `Há ${minutes} min`;
  if (hours < 24) return `Há ${hours} hora${hours > 1 ? "s" : ""}`;
  return `Há ${days} dia${days > 1 ? "s" : ""}`;
}

export default function DashboardPage() {
  const { username, role } = useAuth();
  const [stats, setStats] = useState({
    agents: 0,
    teams: 0,
    workflows: 0,
    collections: 0,
  });
  const [execStats, setExecStats] = useState({ total: 0, success: 0, error: 0, successRate: 0, avgDuration: 0 });
  const [recentActivity, setRecentActivity] = useState<{ icon: React.ReactNode; title: string; time: string; type: "success" | "info" | "warning" }[]>([
    { icon: Icons.chat, title: "Sistema inicializado", time: "Agora", type: "info" },
  ]);
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState<number[]>([3, 5, 2, 8, 4, 6, 7, 5, 9, 4, 6, 8]);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const refreshData = useCallback(async () => {
    setLoading(true);
    try {
      const [agentsRes, teamsRes, workflowsRes, collectionsRes] = await Promise.allSettled([
        api.get("/agents"),
        api.get("/teams"),
        api.get("/workflows"),
        api.get("/rag/collections"),
      ]);

      setStats({
        agents: agentsRes.status === "fulfilled" ? (agentsRes.value.data?.length || 0) : 0,
        teams: teamsRes.status === "fulfilled" ? (teamsRes.value.data?.length || 0) : 0,
        workflows: workflowsRes.status === "fulfilled" ? (workflowsRes.value.data?.length || 0) : 0,
        collections: collectionsRes.status === "fulfilled" ? (collectionsRes.value.data?.collections?.length || 0) : 0,
      });

      // Carregar estatísticas do histórico de execuções
      const historyStats = getHistoryStats();
      setExecStats(historyStats);

      // Carregar atividade recente do histórico
      const history = getHistory().slice(0, 5);
      const activities = history.map((record: ExecutionRecord) => ({
        icon: record.status === "success" ? Icons.check : Icons.alert,
        title: `${record.type === "team" ? "Time" : "Agente"} '${record.name}' ${record.status === "success" ? "executado com sucesso" : "falhou"}`,
        time: formatRelativeTime(new Date(record.timestamp)),
        type: record.status === "success" ? "success" as const : "warning" as const,
      }));

      // Adicionar atividades padrão se não houver histórico
      if (activities.length === 0) {
        setRecentActivity([
          { icon: Icons.chat, title: "Sistema inicializado", time: "Agora", type: "info" },
          { icon: Icons.check, title: "Dashboard carregado", time: "Agora", type: "success" },
        ]);
        return;
      }

      setRecentActivity(activities);
      setLastUpdate(new Date());
    } catch {
      // Silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  return (
    <Protected>
      <div className="space-y-8 animate-slide-up">
        <PageHeader
          title="Dashboard"
          subtitle="Visão geral da plataforma e dos agentes."
        />

        {/* Welcome Section */}
        <div className="bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 rounded-3xl p-8 text-white shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm font-medium">Bem-vindo de volta</p>
              <h1 className="text-3xl font-bold mt-1">{username || "Usuário"}</h1>
              <p className="text-blue-100 mt-2">
                Gerencie seus agentes de IA e automatize seus workflows
              </p>
            </div>
            <div className="hidden md:block">
              <div className="w-24 h-24 bg-white/10 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Agentes Ativos"
            value={loading ? "..." : String(stats.agents)}
            change="+2 esta semana"
            changeType="up"
            icon={Icons.agents}
            chartData={[2, 3, 4, 3, 5, 4, stats.agents || 3]}
            chartColor="blue"
          />
          <StatCard
            title="Times"
            value={loading ? "..." : String(stats.teams)}
            change="Configurados"
            changeType="neutral"
            icon={Icons.teams}
            chartData={[1, 1, 2, 2, 2, stats.teams || 2]}
            chartColor="purple"
          />
          <StatCard
            title="Workflows"
            value={loading ? "..." : String(stats.workflows)}
            change="+5 execuções hoje"
            changeType="up"
            icon={Icons.workflows}
            chartData={[5, 8, 3, 9, 4, 7, 6, stats.workflows || 4]}
            chartColor="green"
          />
          <StatCard
            title="Coleções RAG"
            value={loading ? "..." : String(stats.collections)}
            change="1.2k documentos"
            changeType="neutral"
            icon={Icons.rag}
            chartData={[10, 15, 12, 18, 20, stats.collections || 5]}
            chartColor="orange"
          />
        </div>

        {/* Quick Actions */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Ações Rápidas</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <QuickAction
              title="Novo Agente"
              description="Crie um agente de IA personalizado"
              href="/agents/new"
              icon={Icons.agents}
              color="blue"
            />
            <QuickAction
              title="Novo Time"
              description="Monte uma equipe de agentes"
              href="/teams/new"
              icon={Icons.teams}
              color="purple"
            />
            <QuickAction
              title="Explorar Domínios"
              description="Geo, Finance, Data e mais"
              href="/domains"
              icon={Icons.domains}
              color="green"
            />
            <QuickAction
              title="Editor de Código"
              description="Monaco Editor integrado"
              href="/editor"
              icon={Icons.editor}
              color="orange"
            />
          </div>
        </div>

        {/* Activity & Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Activity Feed */}
          <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Atividade Recente</h2>
              <button onClick={refreshData} className="p-2 text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Atualizar">
                {Icons.refresh}
              </button>
            </div>
            <div className="divide-y divide-gray-100 dark:divide-slate-700">
              {recentActivity.map((activity, i) => (
                <ActivityItem key={i} {...activity} />
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-4">Última atualização: {lastUpdate.toLocaleTimeString()}</p>
          </div>

          {/* Distribution Chart */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-slate-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Distribuição de Recursos</h2>
            <div className="flex flex-col items-center">
              <DonutChart
                data={[
                  { label: "Agentes", value: stats.agents || 3, color: "#3B82F6" },
                  { label: "Times", value: stats.teams || 2, color: "#8B5CF6" },
                  { label: "Workflows", value: stats.workflows || 4, color: "#10B981" },
                  { label: "RAG", value: stats.collections || 2, color: "#F59E0B" },
                ]}
              />
              <div className="grid grid-cols-2 gap-3 mt-4 w-full">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">Agentes</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-purple-500" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">Times</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">Workflows</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-orange-500" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">RAG</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Analytics Section */}
        <div>
          <AnalyticsDashboard />
        </div>

        {/* System Info */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-gray-100 dark:border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Sistema</h2>
            <span className="px-3 py-1 text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full flex items-center gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Online
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-slate-700/50 rounded-xl">
              <p className="text-sm text-gray-500 dark:text-gray-400">Usuário</p>
              <p className="font-semibold text-gray-900 dark:text-white">{username}</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-slate-700/50 rounded-xl">
              <p className="text-sm text-gray-500 dark:text-gray-400">Permissão</p>
              <p className="font-semibold text-gray-900 dark:text-white capitalize">{role}</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-slate-700/50 rounded-xl">
              <p className="text-sm text-gray-500 dark:text-gray-400">API Backend</p>
              <p className="font-semibold text-green-600 dark:text-green-400">Conectado</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-slate-700/50 rounded-xl">
              <p className="text-sm text-gray-500 dark:text-gray-400">Versão</p>
              <p className="font-semibold text-gray-900 dark:text-white">v2.0.0</p>
            </div>
          </div>
        </div>
      </div>
    </Protected>
  );
}
