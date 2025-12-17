"use client";
import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Protected from "../../../../components/Protected";
import Link from "next/link";
import api from "../../../../lib/api";

interface AgentStats {
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  success_rate: number;
  total_tokens_input: number;
  total_tokens_output: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
}

interface DailyStats {
  date: string;
  executions: number;
  tokens: number;
  cost: number;
  avg_latency: number;
}

interface ModelStats {
  model_id: string;
  executions: number;
  avg_latency_ms: number;
  success_rate: number;
}

const Icons = {
  back: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>),
  refresh: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>),
};

function StatCard({ title, value, subtitle, icon, color = "blue" }: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: string;
  color?: string;
}) {
  const colorClasses = {
    blue: "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400",
    green: "bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400",
    red: "bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400",
    purple: "bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400",
    orange: "bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400",
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-gray-100 dark:border-slate-700">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl ${colorClasses[color as keyof typeof colorClasses]}`}>
          <span className="text-xl">{icon}</span>
        </div>
      </div>
    </div>
  );
}

function LatencyChart({ p50, p95, p99, avg }: { p50: number; p95: number; p99: number; avg: number }) {
  const maxLatency = Math.max(p50, p95, p99, avg, 1);
  
  const bars = [
    { label: "P50", value: p50, color: "bg-green-500" },
    { label: "Média", value: avg, color: "bg-blue-500" },
    { label: "P95", value: p95, color: "bg-yellow-500" },
    { label: "P99", value: p99, color: "bg-red-500" },
  ];

  return (
    <div className="space-y-3">
      {bars.map(bar => (
        <div key={bar.label} className="flex items-center gap-3">
          <span className="w-12 text-xs text-gray-500 dark:text-gray-400">{bar.label}</span>
          <div className="flex-1 h-6 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden">
            <div 
              className={`h-full ${bar.color} rounded-full transition-all duration-500`}
              style={{ width: `${(bar.value / maxLatency) * 100}%` }}
            />
          </div>
          <span className="w-20 text-xs text-right text-gray-700 dark:text-gray-300">
            {bar.value.toFixed(0)}ms
          </span>
        </div>
      ))}
    </div>
  );
}

function UsageChart({ data }: { data: DailyStats[] }) {
  if (!data.length) return <p className="text-gray-500 text-sm">Sem dados disponíveis</p>;
  
  const maxExecutions = Math.max(...data.map(d => d.executions), 1);
  
  return (
    <div className="flex items-end gap-1 h-32">
      {data.slice(-14).map((day, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-1">
          <div 
            className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
            style={{ height: `${(day.executions / maxExecutions) * 100}%`, minHeight: day.executions > 0 ? '4px' : '0' }}
            title={`${day.date}: ${day.executions} execuções`}
          />
          <span className="text-xs text-gray-400 rotate-45 origin-left whitespace-nowrap">
            {new Date(day.date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function AgentAnalyticsPage() {
  const params = useParams();
  const agentName = (params?.name as string) || "";
  
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<AgentStats | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [modelStats, setModelStats] = useState<ModelStats[]>([]);
  const [period, setPeriod] = useState<"7d" | "30d" | "90d">("30d");

  useEffect(() => {
    loadStats();
  }, [agentName, period]);

  const loadStats = async () => {
    setLoading(true);
    try {
      // Simular dados (substituir por chamada real à API)
      await new Promise(r => setTimeout(r, 500));
      
      // Mock data
      setStats({
        total_executions: 1247,
        successful_executions: 1198,
        failed_executions: 49,
        success_rate: 0.961,
        total_tokens_input: 523000,
        total_tokens_output: 187000,
        total_cost_usd: 12.47,
        avg_latency_ms: 847,
        p50_latency_ms: 650,
        p95_latency_ms: 1890,
        p99_latency_ms: 3200,
      });

      // Mock daily data
      const days = period === "7d" ? 7 : period === "30d" ? 30 : 90;
      setDailyStats(
        Array.from({ length: days }, (_, i) => ({
          date: new Date(Date.now() - (days - i - 1) * 86400000).toISOString().split('T')[0],
          executions: Math.floor(Math.random() * 100) + 10,
          tokens: Math.floor(Math.random() * 10000) + 1000,
          cost: Math.random() * 0.5,
          avg_latency: Math.floor(Math.random() * 500) + 500,
        }))
      );

      setModelStats([
        { model_id: "gpt-5.1", executions: 823, avg_latency_ms: 780, success_rate: 0.97 },
        { model_id: "claude-sonnet-4.5", executions: 312, avg_latency_ms: 920, success_rate: 0.95 },
        { model_id: "gemini-2.5-flash", executions: 112, avg_latency_ms: 420, success_rate: 0.98 },
      ]);
    } catch (e) {
      console.error("Erro ao carregar stats:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Protected>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href={`/agents/${agentName}`} className="p-2 text-gray-500 hover:text-blue-600 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Voltar">
              {Icons.back}
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analytics: {decodeURIComponent(agentName)}</h1>
              <p className="text-gray-500 dark:text-gray-400 text-sm">Métricas de performance e uso</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Period Selector */}
            <div className="flex bg-gray-100 dark:bg-slate-700 rounded-lg p-1">
              {(["7d", "30d", "90d"] as const).map(p => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    period === p 
                      ? "bg-white dark:bg-slate-600 text-gray-900 dark:text-white shadow-sm" 
                      : "text-gray-500 dark:text-gray-400"
                  }`}
                >
                  {p === "7d" ? "7 dias" : p === "30d" ? "30 dias" : "90 dias"}
                </button>
              ))}
            </div>
            
            <button 
              onClick={loadStats} 
              disabled={loading}
              className="p-2 text-gray-500 hover:text-blue-600 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
              title="Atualizar"
            >
              {Icons.refresh}
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
          </div>
        ) : stats ? (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard 
                title="Execuções" 
                value={stats.total_executions.toLocaleString()} 
                subtitle={`${stats.successful_executions} sucesso / ${stats.failed_executions} falhas`}
                icon="🚀" 
                color="blue" 
              />
              <StatCard 
                title="Taxa de Sucesso" 
                value={`${(stats.success_rate * 100).toFixed(1)}%`} 
                icon="✅" 
                color={stats.success_rate > 0.95 ? "green" : stats.success_rate > 0.9 ? "orange" : "red"} 
              />
              <StatCard 
                title="Tokens Consumidos" 
                value={((stats.total_tokens_input + stats.total_tokens_output) / 1000).toFixed(0) + "K"} 
                subtitle={`${(stats.total_tokens_input/1000).toFixed(0)}K in / ${(stats.total_tokens_output/1000).toFixed(0)}K out`}
                icon="📊" 
                color="purple" 
              />
              <StatCard 
                title="Custo Total" 
                value={`$${stats.total_cost_usd.toFixed(2)}`} 
                subtitle={`$${(stats.total_cost_usd / stats.total_executions).toFixed(4)}/exec`}
                icon="💰" 
                color="green" 
              />
            </div>

            {/* Charts Row */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Usage Over Time */}
              <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Execuções por Dia</h3>
                <UsageChart data={dailyStats} />
              </div>

              {/* Latency Distribution */}
              <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Distribuição de Latência</h3>
                <LatencyChart 
                  p50={stats.p50_latency_ms}
                  p95={stats.p95_latency_ms}
                  p99={stats.p99_latency_ms}
                  avg={stats.avg_latency_ms}
                />
              </div>
            </div>

            {/* Model Breakdown */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Performance por Modelo</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-slate-700">
                      <th className="pb-3 font-medium">Modelo</th>
                      <th className="pb-3 font-medium text-right">Execuções</th>
                      <th className="pb-3 font-medium text-right">Latência Média</th>
                      <th className="pb-3 font-medium text-right">Taxa de Sucesso</th>
                    </tr>
                  </thead>
                  <tbody>
                    {modelStats.map(model => (
                      <tr key={model.model_id} className="border-b border-gray-50 dark:border-slate-700/50">
                        <td className="py-3">
                          <span className="font-medium text-gray-900 dark:text-white">{model.model_id}</span>
                        </td>
                        <td className="py-3 text-right text-gray-600 dark:text-gray-300">
                          {model.executions.toLocaleString()}
                        </td>
                        <td className="py-3 text-right text-gray-600 dark:text-gray-300">
                          {model.avg_latency_ms.toFixed(0)}ms
                        </td>
                        <td className="py-3 text-right">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            model.success_rate > 0.95 
                              ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                              : model.success_rate > 0.9
                              ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                              : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                          }`}>
                            {(model.success_rate * 100).toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-20 text-gray-500">
            Nenhum dado disponível
          </div>
        )}
      </div>
    </Protected>
  );
}
