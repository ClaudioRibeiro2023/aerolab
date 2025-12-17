"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "../../components/PageHeader";

interface ServiceStatus {
  name: string;
  status: "online" | "offline" | "degraded" | "checking";
  latency?: number;
  lastCheck: Date;
  details?: string;
}

interface HealthData {
  status: string;
  service: string;
  version: string;
  modules: Record<string, string>;
}

export default function HealthDashboard() {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: "Backend API", status: "checking", lastCheck: new Date() },
    { name: "Frontend", status: "checking", lastCheck: new Date() },
    { name: "Database", status: "checking", lastCheck: new Date() },
  ]);
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const checkHealth = async () => {
    const startTime = Date.now();
    
    // Check Backend
    try {
      const res = await fetch("http://localhost:8000/health");
      const latency = Date.now() - startTime;
      if (res.ok) {
        const data = await res.json();
        setHealthData(data);
        setServices(prev => prev.map(s => 
          s.name === "Backend API" 
            ? { ...s, status: "online", latency, lastCheck: new Date(), details: `v${data.version}` }
            : s
        ));
      } else {
        setServices(prev => prev.map(s => 
          s.name === "Backend API" 
            ? { ...s, status: "degraded", latency, lastCheck: new Date(), details: `HTTP ${res.status}` }
            : s
        ));
      }
    } catch {
      setServices(prev => prev.map(s => 
        s.name === "Backend API" 
          ? { ...s, status: "offline", lastCheck: new Date(), details: "Não alcançável" }
          : s
      ));
    }

    // Frontend is always online if this page loads
    setServices(prev => prev.map(s => 
      s.name === "Frontend" 
        ? { ...s, status: "online", latency: Date.now() - startTime, lastCheck: new Date(), details: "Next.js 15" }
        : s
    ));

    // Check Database via agents endpoint (requires DB)
    try {
      const dbStart = Date.now();
      const res = await fetch("http://localhost:8000/agents");
      const latency = Date.now() - dbStart;
      setServices(prev => prev.map(s => 
        s.name === "Database" 
          ? { ...s, status: res.ok ? "online" : "degraded", latency, lastCheck: new Date() }
          : s
      ));
    } catch {
      setServices(prev => prev.map(s => 
        s.name === "Database" 
          ? { ...s, status: "offline", lastCheck: new Date() }
          : s
      ));
    }
  };

  useEffect(() => {
    checkHealth();
    if (autoRefresh) {
      const interval = setInterval(checkHealth, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusColor = (status: ServiceStatus["status"]) => {
    switch (status) {
      case "online": return "bg-emerald-500";
      case "offline": return "bg-red-500";
      case "degraded": return "bg-amber-500";
      default: return "bg-slate-500 animate-pulse";
    }
  };

  const getStatusBg = (status: ServiceStatus["status"]) => {
    switch (status) {
      case "online": return "bg-emerald-500/10 border-emerald-500/30";
      case "offline": return "bg-red-500/10 border-red-500/30";
      case "degraded": return "bg-amber-500/10 border-amber-500/30";
      default: return "bg-slate-500/10 border-slate-500/30";
    }
  };

  const allOnline = services.every(s => s.status === "online");
  const anyOffline = services.some(s => s.status === "offline");

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Health Dashboard"
        subtitle="Status dos serviços em tempo real"
        rightActions={
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-400">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
              />
              Auto-refresh
            </label>
            <button
              onClick={checkHealth}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Verificar agora
            </button>
          </div>
        }
      />

      {/* Overall Status */}
      <div className={`p-6 rounded-2xl border ${allOnline ? "bg-emerald-500/10 border-emerald-500/30" : anyOffline ? "bg-red-500/10 border-red-500/30" : "bg-amber-500/10 border-amber-500/30"}`}>
        <div className="flex items-center gap-4">
          <div className={`w-4 h-4 rounded-full ${allOnline ? "bg-emerald-500" : anyOffline ? "bg-red-500" : "bg-amber-500"}`} />
          <div>
            <h2 className="text-xl font-semibold text-white">
              {allOnline ? "Todos os serviços operacionais" : anyOffline ? "Alguns serviços offline" : "Serviços degradados"}
            </h2>
            <p className="text-slate-400 text-sm">
              Última verificação: {services[0]?.lastCheck.toLocaleTimeString("pt-BR")}
            </p>
          </div>
        </div>
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {services.map((service) => (
          <div
            key={service.name}
            className={`p-5 rounded-xl border ${getStatusBg(service.status)}`}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-white">{service.name}</h3>
              <div className={`w-3 h-3 rounded-full ${getStatusColor(service.status)}`} />
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Status:</span>
                <span className={service.status === "online" ? "text-emerald-400" : service.status === "offline" ? "text-red-400" : "text-amber-400"}>
                  {service.status === "checking" ? "Verificando..." : service.status}
                </span>
              </div>
              {service.latency !== undefined && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Latência:</span>
                  <span className={service.latency < 200 ? "text-emerald-400" : service.latency < 500 ? "text-amber-400" : "text-red-400"}>
                    {service.latency}ms
                  </span>
                </div>
              )}
              {service.details && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Detalhes:</span>
                  <span className="text-slate-300">{service.details}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Modules Status */}
      {healthData?.modules && (
        <div className="bg-slate-800/50 rounded-2xl border border-slate-700 p-6">
          <h3 className="font-semibold text-white mb-4">Módulos do Backend</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {Object.entries(healthData.modules).map(([name, status]) => (
              <div
                key={name}
                className={`px-4 py-3 rounded-lg text-center ${status === "active" ? "bg-emerald-500/10 border border-emerald-500/30" : "bg-red-500/10 border border-red-500/30"}`}
              >
                <div className="text-sm font-medium text-white capitalize">
                  {name.replace(/_/g, " ")}
                </div>
                <div className={`text-xs ${status === "active" ? "text-emerald-400" : "text-red-400"}`}>
                  {status}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Links */}
      <div className="bg-slate-800/50 rounded-2xl border border-slate-700 p-6">
        <h3 className="font-semibold text-white mb-4">Links Rápidos</h3>
        <div className="flex flex-wrap gap-3">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors"
          >
            📚 API Docs (Swagger)
          </a>
          <a
            href="http://localhost:8000/redoc"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors"
          >
            📖 ReDoc
          </a>
          <a
            href="http://localhost:8000/metrics"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors"
          >
            📊 Metrics
          </a>
        </div>
      </div>
    </div>
  );
}
