"use client";
import React, { useEffect, useState } from "react";
import {
  getSystemMetrics,
  getAllAgentMetrics,
  getTopAgents,
  generateSampleData,
  type AgentMetrics,
  type SystemMetrics,
} from "../lib/analytics";

export default function AnalyticsDashboard() {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [topAgents, setTopAgents] = useState<AgentMetrics[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<"7d" | "30d" | "90d">("30d");
  
  useEffect(() => {
    // Carregar métricas
    loadMetrics();
  }, []);

  const loadMetrics = () => {
    setSystemMetrics(getSystemMetrics());
    setTopAgents(getTopAgents("executions", 5));
  };

  const handleGenerateSampleData = () => {
    generateSampleData();
    loadMetrics();
  };

  if (!systemMetrics) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
        <p className="text-gray-500">Carregando analytics...</p>
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Analytics</h2>
          <p className="text-gray-500 dark:text-gray-400">Métricas e performance dos seus agentes</p>
        </div>
        <div className="flex gap-2">
          {/* Period Selector */}
          <div className="flex bg-gray-100 dark:bg-slate-800 rounded-lg p-1">
            {(["7d", "30d", "90d"] as const).map((period) => (
              <button
                key={period}
                onClick={() => setSelectedPeriod(period)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedPeriod === period
                    ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                }`}
              >
                {period === "7d" ? "7 dias" : period === "30d" ? "30 dias" : "90 dias"}
              </button>
            ))}
          </div>
          {/* Demo Data Button */}
          {systemMetrics.totalExecutions === 0 && (
            <button
              onClick={handleGenerateSampleData}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
            >
              ✨ Gerar Dados de Exemplo
            </button>
          )}
        </div>
      </div>

      {/* System Metrics Cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Executions */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Execuções</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                {systemMetrics.totalExecutions.toLocaleString()}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className={`flex items-center gap-1 ${systemMetrics.executionTrend >= 0 ? "text-green-600" : "text-red-600"}`}>
              {systemMetrics.executionTrend >= 0 ? "↑" : "↓"}
              {Math.abs(systemMetrics.executionTrend).toFixed(1)}%
            </span>
            <span className="text-gray-500">vs período anterior</span>
          </div>
        </div>

        {/* Success Rate */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Taxa de Sucesso</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                {formatPercent(systemMetrics.avgSuccessRate)}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center text-green-600 dark:text-green-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-500"
              style={{ width: formatPercent(systemMetrics.avgSuccessRate) }}
            />
          </div>
        </div>

        {/* Total Cost */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Custo Total</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                {formatCurrency(systemMetrics.totalCost)}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className={`flex items-center gap-1 ${systemMetrics.costTrend >= 0 ? "text-red-600" : "text-green-600"}`}>
              {systemMetrics.costTrend >= 0 ? "↑" : "↓"}
              {Math.abs(systemMetrics.costTrend).toFixed(1)}%
            </span>
            <span className="text-gray-500">vs período anterior</span>
          </div>
        </div>

        {/* Active Agents */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Agentes Ativos</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                {systemMetrics.totalAgents}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center text-orange-600 dark:text-orange-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <p className="text-sm text-gray-500">
            {systemMetrics.totalUsers} usuário{systemMetrics.totalUsers !== 1 ? "s" : ""}
          </p>
        </div>
      </div>

      {/* Top Agents Table */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Top Agentes por Performance</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Agentes com maior número de execuções</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-slate-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Agente</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Execuções</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Taxa de Sucesso</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tempo Médio</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Custo Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tendência</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-700">
              {topAgents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="text-gray-400 dark:text-gray-500">
                      <svg className="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                      </svg>
                      <p className="font-medium">Nenhum dado disponível</p>
                      <p className="text-sm mt-1">Execute alguns agentes para ver analytics</p>
                    </div>
                  </td>
                </tr>
              ) : (
                topAgents.map((agent, idx) => (
                  <tr key={agent.agentName} className="hover:bg-gray-50 dark:hover:bg-slate-900 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                          #{idx + 1}
                        </div>
                        <span className="font-medium text-gray-900 dark:text-white">{agent.agentName}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900 dark:text-white">
                      {agent.executions.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-lg ${
                        agent.successRate >= 0.95 ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" :
                        agent.successRate >= 0.80 ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" :
                        "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                      }`}>
                        {formatPercent(agent.successRate)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900 dark:text-white">
                      {agent.avgResponseTime.toFixed(1)}s
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-900 dark:text-white">
                      {formatCurrency(agent.totalCost)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {agent.trending === "up" && <span className="text-green-600">↑ Alta</span>}
                      {agent.trending === "down" && <span className="text-red-600">↓ Baixa</span>}
                      {agent.trending === "stable" && <span className="text-gray-500">→ Estável</span>}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
