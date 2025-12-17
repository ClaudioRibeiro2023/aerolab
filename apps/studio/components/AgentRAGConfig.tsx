"use client";
import React, { useState } from "react";

export interface RAGConfig {
  enabled: boolean;
  collection: string;
  strategy: "semantic" | "keyword" | "hybrid";
  topK: number;
  minScore: number;
  chunkSize: number;
  chunkOverlap: number;
  sources: RAGSource[];
}

export interface RAGSource {
  id: string;
  type: "file" | "url" | "database" | "api";
  name: string;
  status: "active" | "indexing" | "error";
}

interface Props {
  config: RAGConfig;
  onChange: (config: RAGConfig) => void;
}

const defaultSources: RAGSource[] = [
  { id: "docs", type: "file", name: "Documentação Interna", status: "active" },
  { id: "kb", type: "database", name: "Base de Conhecimento", status: "active" },
];

export const defaultRAGConfig: RAGConfig = {
  enabled: false,
  collection: "",
  strategy: "semantic",
  topK: 5,
  minScore: 0.7,
  chunkSize: 500,
  chunkOverlap: 50,
  sources: [],
};

export default function AgentRAGConfig({ config, onChange }: Props) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const updateConfig = (updates: Partial<RAGConfig>) => {
    onChange({ ...config, ...updates });
  };

  const toggleSource = (source: RAGSource) => {
    const exists = config.sources.find(s => s.id === source.id);
    if (exists) {
      updateConfig({ sources: config.sources.filter(s => s.id !== source.id) });
    } else {
      updateConfig({ sources: [...config.sources, source] });
    }
  };

  return (
    <div className="space-y-4">
      {/* Toggle Principal */}
      <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
        <div>
          <p className="font-medium text-gray-900 dark:text-white">Base de Conhecimento (RAG)</p>
          <p className="text-xs text-gray-500">Permite ao agente consultar documentos e dados específicos</p>
        </div>
        <button 
          onClick={() => updateConfig({ enabled: !config.enabled })}
          className={`w-12 h-6 rounded-full transition-colors ${config.enabled ? "bg-blue-500" : "bg-gray-300 dark:bg-slate-600"}`}
        >
          <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${config.enabled ? "translate-x-6" : "translate-x-0.5"}`} />
        </button>
      </div>

      {config.enabled && (
        <>
          {/* Collection Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Nome da Coleção
            </label>
            <input
              type="text"
              value={config.collection}
              onChange={e => updateConfig({ collection: e.target.value })}
              placeholder="Ex: docs_vendas, faq_suporte"
              className="input-modern"
            />
            <p className="text-xs text-gray-500 mt-1">Identificador único para a base de conhecimento</p>
          </div>

          {/* Strategy */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Estratégia de Busca
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: "semantic", name: "Semântica", desc: "Busca por significado" },
                { id: "keyword", name: "Palavras-chave", desc: "Busca exata" },
                { id: "hybrid", name: "Híbrida", desc: "Combina ambas" },
              ].map(s => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => updateConfig({ strategy: s.id as RAGConfig["strategy"] })}
                  className={`p-3 rounded-xl border-2 text-left transition-all ${
                    config.strategy === s.id
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                      : "border-gray-200 dark:border-slate-600"
                  }`}
                >
                  <span className="font-medium text-sm text-gray-900 dark:text-white">{s.name}</span>
                  <span className="block text-xs text-gray-500 mt-0.5">{s.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Sources */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Fontes de Dados
            </label>
            <div className="space-y-2">
              {defaultSources.map(source => {
                const isSelected = config.sources.some(s => s.id === source.id);
                return (
                  <button
                    key={source.id}
                    type="button"
                    onClick={() => toggleSource(source)}
                    className={`w-full p-3 rounded-xl border-2 text-left flex items-center gap-3 transition-all ${
                      isSelected
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                        : "border-gray-200 dark:border-slate-600"
                    }`}
                  >
                    <span className="text-xl">
                      {source.type === "file" ? "📄" : source.type === "database" ? "🗄️" : source.type === "url" ? "🌐" : "🔌"}
                    </span>
                    <div className="flex-1">
                      <span className="font-medium text-gray-900 dark:text-white">{source.name}</span>
                      <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
                        source.status === "active" ? "bg-green-100 text-green-700" :
                        source.status === "indexing" ? "bg-yellow-100 text-yellow-700" :
                        "bg-red-100 text-red-700"
                      }`}>
                        {source.status === "active" ? "Ativo" : source.status === "indexing" ? "Indexando" : "Erro"}
                      </span>
                    </div>
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                      isSelected ? "bg-blue-500 border-blue-500" : "border-gray-300"
                    }`}>
                      {isSelected && (
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Advanced Toggle */}
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
          >
            <svg className={`w-4 h-4 transition-transform ${showAdvanced ? "rotate-90" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            Configurações Avançadas
          </button>

          {showAdvanced && (
            <div className="space-y-4 p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Top K (resultados)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={config.topK}
                    onChange={e => updateConfig({ topK: parseInt(e.target.value) || 5 })}
                    className="input-modern"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Score Mínimo
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={1}
                    step={0.1}
                    value={config.minScore}
                    onChange={e => updateConfig({ minScore: parseFloat(e.target.value) || 0.7 })}
                    className="input-modern"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Chunk Size
                  </label>
                  <input
                    type="number"
                    min={100}
                    max={2000}
                    step={100}
                    value={config.chunkSize}
                    onChange={e => updateConfig({ chunkSize: parseInt(e.target.value) || 500 })}
                    className="input-modern"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Chunk Overlap
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={500}
                    step={10}
                    value={config.chunkOverlap}
                    onChange={e => updateConfig({ chunkOverlap: parseInt(e.target.value) || 50 })}
                    className="input-modern"
                  />
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
