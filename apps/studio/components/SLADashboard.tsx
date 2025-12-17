"use client";

import React, { useState, useEffect } from "react";

interface SLAMetric {
  name: string;
  current: number;
  target: number;
  unit: string;
  status: "healthy" | "warning" | "critical";
  trend: "up" | "down" | "stable";
}

interface IncidentSummary {
  total: number;
  resolved: number;
  open: number;
  avgResolutionTime: number;
}

interface UptimeData {
  date: string;
  uptime: number;
  incidents: number;
}

const defaultMetrics: SLAMetric[] = [
  { name: "Uptime", current: 99.95, target: 99.9, unit: "%", status: "healthy", trend: "stable" },
  { name: "Latência P95", current: 245, target: 300, unit: "ms", status: "healthy", trend: "down" },
  { name: "Taxa de Erro", current: 0.12, target: 0.5, unit: "%", status: "healthy", trend: "down" },
  { name: "Tempo de Resposta", current: 1.8, target: 2.0, unit: "s", status: "healthy", trend: "stable" },
];

const defaultIncidents: IncidentSummary = {
  total: 3,
  resolved: 2,
  open: 1,
  avgResolutionTime: 45,
};

export default function SLADashboard() {
  const [metrics, setMetrics] = useState<SLAMetric[]>(defaultMetrics);
  const [incidents, setIncidents] = useState<IncidentSummary>(defaultIncidents);
  const [period, setPeriod] = useState<"24h" | "7d" | "30d">("7d");
  const [uptimeHistory, setUptimeHistory] = useState<UptimeData[]>([]);

  useEffect(() => {
    // Gerar dados de histórico
    const days = period === "24h" ? 24 : period === "7d" ? 7 : 30;
    const history: UptimeData[] = [];
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      history.push({
        date: date.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }),
        uptime: 99.5 + Math.random() * 0.5,
        incidents: Math.random() > 0.8 ? 1 : 0,
      });
    }
    
    setUptimeHistory(history);
  }, [period]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy": return "text-green-500";
      case "warning": return "text-yellow-500";
      case "critical": return "text-red-500";
      default: return "text-gray-500";
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case "healthy": return "bg-green-100 dark:bg-green-900/30";
      case "warning": return "bg-yellow-100 dark:bg-yellow-900/30";
      case "critical": return "bg-red-100 dark:bg-red-900/30";
      default: return "bg-gray-100 dark:bg-gray-900/30";
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "up": return "↑";
      case "down": return "↓";
      default: return "→";
    }
  };

  const overallStatus = metrics.every(m => m.status === "healthy") 
    ? "healthy" 
    : metrics.some(m => m.status === "critical") 
      ? "critical" 
      : "warning";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            SLA Dashboard
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Monitoramento de Service Level Agreement
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Status Geral */}
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${getStatusBg(overallStatus)}`}>
            <span className={`w-3 h-3 rounded-full ${
              overallStatus === "healthy" ? "bg-green-500" :
              overallStatus === "warning" ? "bg-yellow-500" : "bg-red-500"
            }`} />
            <span className={`font-medium ${getStatusColor(overallStatus)}`}>
              {overallStatus === "healthy" ? "Todos os SLAs OK" :
               overallStatus === "warning" ? "Atenção" : "Crítico"}
            </span>
          </div>

          {/* Period Selector */}
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as "24h" | "7d" | "30d")}
            className="px-3 py-2 border rounded-lg bg-white dark:bg-slate-800 dark:border-slate-700"
            title="Período"
          >
            <option value="24h">Últimas 24h</option>
            <option value="7d">Últimos 7 dias</option>
            <option value="30d">Últimos 30 dias</option>
          </select>
        </div>
      </div>

      {/* Métricas Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <div
            key={index}
            className={`p-4 rounded-xl border ${getStatusBg(metric.status)} border-transparent`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                {metric.name}
              </span>
              <span className={`text-xs ${
                metric.trend === "up" ? "text-green-500" :
                metric.trend === "down" ? "text-blue-500" : "text-gray-500"
              }`}>
                {getTrendIcon(metric.trend)}
              </span>
            </div>
            
            <div className="flex items-baseline gap-1">
              <span className={`text-3xl font-bold ${getStatusColor(metric.status)}`}>
                {metric.current.toFixed(metric.unit === "%" ? 2 : 0)}
              </span>
              <span className="text-sm text-gray-500">{metric.unit}</span>
            </div>
            
            <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
              <span>Meta: {metric.target}{metric.unit}</span>
              <span className={metric.status === "healthy" ? "text-green-500" : "text-red-500"}>
                {metric.status === "healthy" ? "✓ Dentro" : "✗ Fora"}
              </span>
            </div>
            
            {/* Progress bar */}
            <div className="mt-2 h-1.5 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  metric.status === "healthy" ? "bg-green-500" :
                  metric.status === "warning" ? "bg-yellow-500" : "bg-red-500"
                }`}
                style={{ width: `${Math.min((metric.current / metric.target) * 100, 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Uptime Chart */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-gray-200 dark:border-slate-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Histórico de Uptime
        </h3>
        
        <div className="flex items-end gap-1 h-32">
          {uptimeHistory.map((day, index) => (
            <div
              key={index}
              className="flex-1 flex flex-col items-center group"
            >
              <div className="relative w-full">
                <div
                  className={`w-full rounded-t transition-all ${
                    day.uptime >= 99.9 ? "bg-green-500" :
                    day.uptime >= 99.5 ? "bg-yellow-500" : "bg-red-500"
                  }`}
                  style={{ height: `${(day.uptime - 99) * 100}px` }}
                />
                
                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  {day.date}: {day.uptime.toFixed(2)}%
                  {day.incidents > 0 && ` (${day.incidents} incidente)`}
                </div>
              </div>
              
              {index % Math.ceil(uptimeHistory.length / 7) === 0 && (
                <span className="text-xs text-gray-500 mt-1">{day.date}</span>
              )}
            </div>
          ))}
        </div>
        
        <div className="flex items-center justify-center gap-6 mt-4 text-xs">
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-green-500" />
            <span className="text-gray-600 dark:text-gray-400">&gt;99.9%</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-yellow-500" />
            <span className="text-gray-600 dark:text-gray-400">99.5-99.9%</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-red-500" />
            <span className="text-gray-600 dark:text-gray-400">&lt;99.5%</span>
          </div>
        </div>
      </div>

      {/* Incidentes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-gray-200 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Resumo de Incidentes
          </h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
              <div className="text-3xl font-bold text-gray-900 dark:text-white">
                {incidents.total}
              </div>
              <div className="text-sm text-gray-500">Total</div>
            </div>
            <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="text-3xl font-bold text-green-600">
                {incidents.resolved}
              </div>
              <div className="text-sm text-gray-500">Resolvidos</div>
            </div>
            <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div className="text-3xl font-bold text-red-600">
                {incidents.open}
              </div>
              <div className="text-sm text-gray-500">Em Aberto</div>
            </div>
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-3xl font-bold text-blue-600">
                {incidents.avgResolutionTime}m
              </div>
              <div className="text-sm text-gray-500">Tempo Médio</div>
            </div>
          </div>
        </div>

        {/* SLA Compliance */}
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-gray-200 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Compliance por Categoria
          </h3>
          
          <div className="space-y-4">
            {[
              { name: "Disponibilidade", value: 99.95, target: 99.9 },
              { name: "Performance", value: 98.5, target: 95 },
              { name: "Suporte", value: 97.2, target: 95 },
              { name: "Segurança", value: 100, target: 99 },
            ].map((item, index) => (
              <div key={index}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-600 dark:text-gray-300">
                    {item.name}
                  </span>
                  <span className={`text-sm font-medium ${
                    item.value >= item.target ? "text-green-500" : "text-red-500"
                  }`}>
                    {item.value}%
                  </span>
                </div>
                <div className="h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      item.value >= item.target ? "bg-green-500" : "bg-red-500"
                    }`}
                    style={{ width: `${item.value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
