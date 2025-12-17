"use client";
import React from "react";
import { Badge } from "./Badge";

interface AgentPreviewProps {
  name: string;
  role: string;
  provider: string;
  modelId: string;
  instructions: string[];
  useRAG?: boolean;
  useHITL?: boolean;
  markdown?: boolean;
}

export default function AgentPreview({
  name,
  role,
  provider,
  modelId,
  instructions,
  useRAG,
  useHITL,
  markdown
}: AgentPreviewProps) {
  const getProviderInfo = () => {
    const providers: Record<string, { name: string; speed: string; cost: string; color: string }> = {
      openai: { name: "OpenAI", speed: "Rápido", cost: "$$", color: "from-green-500 to-green-600" },
      anthropic: { name: "Anthropic", speed: "Médio", cost: "$$$", color: "from-orange-500 to-orange-600" },
      groq: { name: "Groq", speed: "Muito Rápido", cost: "$", color: "from-purple-500 to-purple-600" },
    };
    return providers[provider] || providers.openai;
  };

  const providerInfo = getProviderInfo();

  const getModelName = () => {
    const models: Record<string, string> = {
      "gpt-4.1": "GPT-4.1",
      "gpt-4o": "GPT-4o",
      "gpt-4o-mini": "GPT-4o Mini",
      "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet",
      "claude-3-opus-20240229": "Claude 3 Opus",
      "llama-3.3-70b-versatile": "Llama 3.3 70B",
      "mixtral-8x7b-32768": "Mixtral 8x7B",
    };
    return models[modelId] || modelId;
  };

  return (
    <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-slate-900 dark:to-slate-800 rounded-2xl p-6 border border-blue-100 dark:border-slate-700">
      {/* Header */}
      <div className="flex items-start gap-4 mb-6">
        <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/25">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
            {name || "Nome do Agente"}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
            {role || "Descrição do agente"}
          </p>
        </div>
        <Badge variant="success" className="self-start flex items-center gap-1">
          ✨ Preview
        </Badge>
      </div>

      {/* AI Model Info */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <div className="bg-white dark:bg-slate-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-3 h-3 rounded-full bg-gradient-to-br ${providerInfo.color}`} />
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Provedor</p>
          </div>
          <p className="font-semibold text-gray-900 dark:text-white">{providerInfo.name}</p>
          <p className="text-xs text-gray-500 mt-1">{providerInfo.speed} • {providerInfo.cost}</p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-3 h-3 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
            </svg>
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Modelo</p>
          </div>
          <p className="font-semibold text-gray-900 dark:text-white">{getModelName()}</p>
        </div>
      </div>

      {/* Features */}
      {(useRAG || useHITL || markdown) && (
        <div className="mb-6">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-3">Recursos Habilitados</p>
          <div className="flex flex-wrap gap-2">
            {useRAG && (
              <div className="flex items-center gap-2 px-3 py-2 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-lg text-sm">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <span className="font-medium">RAG</span>
                <span className="text-xs opacity-75">Consulta documentos</span>
              </div>
            )}
            {useHITL && (
              <div className="flex items-center gap-2 px-3 py-2 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded-lg text-sm">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span className="font-medium">HITL</span>
                <span className="text-xs opacity-75">Aprovação humana</span>
              </div>
            )}
            {markdown && (
              <div className="flex items-center gap-2 px-3 py-2 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-lg text-sm">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <span className="font-medium">Markdown</span>
                <span className="text-xs opacity-75">Formatação rica</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Instructions */}
      {instructions && instructions.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-3">
            Instruções ({instructions.length})
          </p>
          <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar">
            {instructions.map((instruction, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 bg-white dark:bg-slate-800 rounded-lg">
                <div className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center flex-shrink-0 text-xs font-medium">
                  {idx + 1}
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                  {instruction}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {(!instructions || instructions.length === 0) && (
        <div className="text-center py-8 bg-white dark:bg-slate-800 rounded-xl">
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 dark:bg-slate-700 flex items-center justify-center text-2xl">
            📝
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Nenhuma instrução configurada ainda
          </p>
        </div>
      )}

      {/* Info Footer */}
      <div className="mt-6 pt-6 border-t border-blue-100 dark:border-slate-700">
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>
            Este é um preview. Você poderá testar o agente após criá-lo.
          </span>
        </div>
      </div>
    </div>
  );
}
