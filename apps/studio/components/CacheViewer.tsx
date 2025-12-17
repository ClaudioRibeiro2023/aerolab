"use client";
import React, { useState, useEffect } from "react";
import {
  getCacheStats,
  getCacheSize,
  getPopularEntries,
  optimizeCache,
  clearAllCache,
  generateSampleCache,
  type CacheEntry,
} from "../lib/intelligentCache";

interface CacheViewerProps {
  agentName?: string;
}

export default function CacheViewer({ agentName }: CacheViewerProps) {
  const [stats, setStats] = useState(getCacheStats(agentName));
  const [size, setSize] = useState(getCacheSize());
  const [popularEntries, setPopularEntries] = useState<CacheEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<CacheEntry | null>(null);

  useEffect(() => {
    loadData();
  }, [agentName]);

  const loadData = () => {
    setStats(getCacheStats(agentName));
    setSize(getCacheSize());
    if (agentName) {
      setPopularEntries(getPopularEntries(agentName, 5));
    }
  };

  const handleOptimize = () => {
    const result = optimizeCache();
    alert(`Otimizado! ${result.removedEntries} entradas removidas, ${result.savedSpaceKB.toFixed(2)}KB economizados.`);
    loadData();
  };

  const handleClearAll = () => {
    if (confirm("Tem certeza que deseja limpar TODO o cache? Esta ação não pode ser desfeita.")) {
      clearAllCache();
      loadData();
    }
  };

  const handleGenerateSample = () => {
    if (!agentName) {
      alert("Selecione um agente específico para gerar dados de exemplo");
      return;
    }
    generateSampleCache(agentName);
    loadData();
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-br from-green-600 to-teal-600 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">Cache Inteligente</h2>
            <p className="text-green-100 mt-1">
              {agentName ? `Agente: ${agentName}` : "Todos os agentes"}
            </p>
          </div>
          <div className="text-5xl">⚡</div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-green-200 text-sm">Entradas</p>
            <p className="text-2xl font-bold">{stats.totalEntries}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-green-200 text-sm">Hits</p>
            <p className="text-2xl font-bold">{stats.totalHits}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-green-200 text-sm">Taxa de Hit</p>
            <p className="text-2xl font-bold">{stats.hitRate.toFixed(1)}%</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-green-200 text-sm">Economia</p>
            <p className="text-2xl font-bold">{formatCurrency(stats.totalCostSaved)}</p>
          </div>
        </div>
      </div>

      {/* Cache Info */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Informações do Cache</h3>
          <div className="flex gap-2">
            {agentName && stats.totalEntries === 0 && (
              <button
                onClick={handleGenerateSample}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
              >
                Gerar Exemplo
              </button>
            )}
            <button
              onClick={handleOptimize}
              className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-sm"
            >
              🔧 Otimizar
            </button>
            <button
              onClick={handleClearAll}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm"
            >
              🗑️ Limpar Tudo
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 dark:bg-slate-700/50 rounded-xl">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total de Agentes</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{size.agents}</p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-slate-700/50 rounded-xl">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Tamanho do Cache</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{size.sizeKB.toFixed(2)} KB</p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-slate-700/50 rounded-xl">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Tokens Economizados</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.avgTokensSaved.toFixed(0)}
            </p>
          </div>
        </div>
      </div>

      {/* Popular Entries */}
      {agentName && popularEntries.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Queries Mais Populares
          </h3>
          <div className="space-y-3">
            {popularEntries.map((entry) => (
              <div
                key={entry.id}
                onClick={() => setSelectedEntry(selectedEntry?.id === entry.id ? null : entry)}
                className="p-4 bg-gray-50 dark:bg-slate-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors cursor-pointer"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {entry.prompt}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                      <span>🔥 {entry.hits} hits</span>
                      <span>💰 {formatCurrency(entry.costSaved)} economizado</span>
                      <span>📅 {new Date(entry.timestamp).toLocaleDateString("pt-BR")}</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className="px-2 py-1 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded text-xs font-medium">
                      {entry.tokensInput + entry.tokensOutput} tokens
                    </span>
                  </div>
                </div>

                {/* Expanded Response */}
                {selectedEntry?.id === entry.id && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-slate-600">
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {entry.response}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Benefits */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Benefícios do Cache Inteligente
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg text-green-600 dark:text-green-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white">Resposta Instantânea</h4>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Queries similares são respondidas em {'<'}1ms
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg text-blue-600 dark:text-blue-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white">Redução de Custos</h4>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Economize 30-40% em custos de API
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg text-purple-600 dark:text-purple-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white">Consistência</h4>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Respostas consistentes para queries similares
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
