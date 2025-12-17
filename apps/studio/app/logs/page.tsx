"use client";

import { useEffect, useState } from "react";
import api from "../../lib/api";

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
}

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchLogs() {
      try {
        const { data } = await api.get("/logs");
        setLogs(data.logs || []);
      } catch (error) {
        console.error("Error fetching logs:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchLogs();
  }, []);

  const getLevelColor = (level: string) => {
    switch (level.toUpperCase()) {
      case "ERROR":
        return "text-red-500 bg-red-500/10";
      case "WARN":
      case "WARNING":
        return "text-yellow-500 bg-yellow-500/10";
      case "INFO":
        return "text-blue-500 bg-blue-500/10";
      case "DEBUG":
        return "text-gray-500 bg-gray-500/10";
      default:
        return "text-gray-400 bg-gray-400/10";
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Logs do Sistema
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Visualize os logs e eventos da plataforma
        </p>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700">
        <div className="p-4 border-b border-gray-200 dark:border-slate-700 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900 dark:text-white">
            Eventos Recentes
          </h2>
          <button
            onClick={() => window.location.reload()}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Atualizar
          </button>
        </div>

        <div className="divide-y divide-gray-100 dark:divide-slate-700">
          {loading ? (
            <div className="p-8 text-center text-gray-500">
              Carregando logs...
            </div>
          ) : logs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Nenhum log disponível
            </div>
          ) : (
            logs.map((log, index) => (
              <div
                key={index}
                className="p-4 hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <span
                    className={`px-2 py-0.5 text-xs font-medium rounded ${getLevelColor(
                      log.level
                    )}`}
                  >
                    {log.level}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 dark:text-white">
                      {log.message}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(log.timestamp).toLocaleString("pt-BR")}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
