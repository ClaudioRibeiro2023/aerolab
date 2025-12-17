"use client";
import React, { useState, useEffect } from "react";
import {
  getAgentMemory,
  getMemorySummary,
  getRecentMemories,
  searchMemories,
  deleteMemory,
  updateMemoryImportance,
  generateSampleMemory,
  type MemoryEntry,
} from "../lib/agentMemory";

interface AgentMemoryViewerProps {
  agentName: string;
}

export default function AgentMemoryViewer({ agentName }: AgentMemoryViewerProps) {
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [summary, setSummary] = useState<ReturnType<typeof getMemorySummary>>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<"all" | MemoryEntry["type"]>("all");
  const [selectedMemory, setSelectedMemory] = useState<MemoryEntry | null>(null);

  useEffect(() => {
    loadMemories();
  }, [agentName, filterType, searchQuery]);

  const loadMemories = () => {
    let results: MemoryEntry[] = [];
    
    if (searchQuery.trim()) {
      results = searchMemories(agentName, searchQuery);
    } else {
      results = getRecentMemories(agentName, 50);
    }
    
    if (filterType !== "all") {
      results = results.filter(m => m.type === filterType);
    }
    
    setMemories(results);
    setSummary(getMemorySummary(agentName));
  };

  const handleDelete = (id: string) => {
    if (confirm("Tem certeza que deseja deletar esta memória?")) {
      deleteMemory(agentName, id);
      loadMemories();
    }
  };

  const handleImportanceChange = (id: string, newImportance: MemoryEntry["importance"]) => {
    updateMemoryImportance(agentName, id, newImportance);
    loadMemories();
  };

  const handleGenerateSample = () => {
    generateSampleMemory(agentName);
    loadMemories();
  };

  const typeColors = {
    context: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
    preference: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
    fact: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    interaction: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  };

  const typeIcons = {
    context: "📋",
    preference: "⚙️",
    fact: "💡",
    interaction: "💬",
  };

  if (!summary) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-12 border border-gray-100 dark:border-slate-700 text-center">
        <div className="text-6xl mb-4">🧠</div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Nenhuma Memória
        </h3>
        <p className="text-gray-500 dark:text-gray-400 mb-4">
          Este agente ainda não possui memórias armazenadas
        </p>
        <button
          onClick={handleGenerateSample}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          Gerar Memórias de Exemplo
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Stats */}
      <div className="bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">Memória do Agente</h2>
            <p className="text-purple-100 mt-1">{agentName}</p>
          </div>
          <div className="text-5xl">🧠</div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-purple-200 text-sm">Total</p>
            <p className="text-2xl font-bold">{summary.total}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-purple-200 text-sm">Contextos</p>
            <p className="text-2xl font-bold">{summary.byType.context || 0}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-purple-200 text-sm">Preferências</p>
            <p className="text-2xl font-bold">{summary.byType.preference || 0}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-purple-200 text-sm">Fatos</p>
            <p className="text-2xl font-bold">{summary.byType.fact || 0}</p>
          </div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar memórias..."
              className="w-full px-4 py-2 bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          {/* Type Filter */}
          <div className="flex gap-2">
            <button
              onClick={() => setFilterType("all")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filterType === "all"
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-600"
              }`}
            >
              Todos
            </button>
            {(["context", "preference", "fact", "interaction"] as const).map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filterType === type
                    ? "bg-blue-500 text-white"
                    : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-600"
                }`}
              >
                {typeIcons[type]} {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Memory List */}
      <div className="space-y-3">
        {memories.length === 0 ? (
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-12 border border-gray-100 dark:border-slate-700 text-center">
            <p className="text-gray-500 dark:text-gray-400">
              {searchQuery ? "Nenhuma memória encontrada" : "Nenhuma memória para exibir"}
            </p>
          </div>
        ) : (
          memories.map((memory) => (
            <div
              key={memory.id}
              className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  {/* Type Badge */}
                  <div className="flex items-center gap-2 mb-3">
                    <span className={`px-3 py-1 rounded-lg text-xs font-medium ${typeColors[memory.type]}`}>
                      {typeIcons[memory.type]} {memory.type}
                    </span>
                    <span className="text-xs text-gray-400">
                      {new Date(memory.timestamp).toLocaleDateString("pt-BR")}
                    </span>
                  </div>
                  
                  {/* Content */}
                  <p className="text-gray-900 dark:text-white mb-3">{memory.content}</p>
                  
                  {/* Tags */}
                  {memory.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {memory.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 rounded text-xs"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* Actions */}
                <div className="flex flex-col gap-2">
                  {/* Importance Stars */}
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((level) => (
                      <button
                        key={level}
                        onClick={() => handleImportanceChange(memory.id, level as MemoryEntry["importance"])}
                        className={`text-lg ${
                          level <= memory.importance
                            ? "text-yellow-400"
                            : "text-gray-300 dark:text-gray-600"
                        } hover:text-yellow-400 transition-colors`}
                        title={`Importância: ${level}`}
                      >
                        ⭐
                      </button>
                    ))}
                  </div>
                  
                  {/* Delete Button */}
                  <button
                    onClick={() => handleDelete(memory.id)}
                    className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                    title="Deletar memória"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Top Tags */}
      {summary.topTags.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Tags Mais Usadas</h3>
          <div className="flex flex-wrap gap-2">
            {summary.topTags.map(({ tag, count }) => (
              <button
                key={tag}
                onClick={() => setSearchQuery(tag)}
                className="px-3 py-2 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 rounded-lg text-sm transition-colors"
              >
                #{tag} <span className="text-gray-400 ml-1">({count})</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
