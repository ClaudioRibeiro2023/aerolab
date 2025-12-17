"use client";
import React, { useState, useEffect } from "react";
import {
  analyzeAgentFeedbacks,
  getRatingTrend,
  applyImprovements,
  generateSampleFeedbacks,
  type AgentInsights as InsightsType,
  type InstructionImprovement,
} from "../lib/feedbackLoop";

interface AgentInsightsProps {
  agentName: string;
  currentInstructions: string[];
  onApplyImprovements?: (newInstructions: string[]) => void;
}

export default function AgentInsights({ 
  agentName,
  currentInstructions,
  onApplyImprovements,
}: AgentInsightsProps) {
  const [insights, setInsights] = useState<InsightsType | null>(null);
  const [trend, setTrend] = useState<ReturnType<typeof getRatingTrend> | null>(null);
  const [selectedImprovement, setSelectedImprovement] = useState<InstructionImprovement | null>(null);

  useEffect(() => {
    loadInsights();
  }, [agentName]);

  const loadInsights = () => {
    const data = analyzeAgentFeedbacks(agentName);
    setInsights(data);
    setTrend(getRatingTrend(agentName));
  };

  const handleGenerateSample = () => {
    generateSampleFeedbacks(agentName);
    loadInsights();
  };

  const handleApplyAll = () => {
    if (!insights || insights.suggestedImprovements.length === 0) return;
    
    const newInstructions = applyImprovements(
      currentInstructions,
      insights.suggestedImprovements
    );
    
    if (onApplyImprovements) {
      onApplyImprovements(newInstructions);
    }
    
    alert("Melhorias aplicadas! Revise as instruções atualizadas.");
  };

  if (!insights) {
    return <div className="text-center py-12">Carregando insights...</div>;
  }

  if (insights.totalFeedbacks === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-12 border border-gray-100 dark:border-slate-700 text-center">
        <div className="text-6xl mb-4">📊</div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Sem Feedbacks Ainda
        </h3>
        <p className="text-gray-500 dark:text-gray-400 mb-4">
          Colete feedbacks dos usuários para obter insights e sugestões de melhorias
        </p>
        <button
          onClick={handleGenerateSample}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          Gerar Feedbacks de Exemplo
        </button>
      </div>
    );
  }

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case "improving": return "text-green-600 dark:text-green-400";
      case "declining": return "text-red-600 dark:text-red-400";
      default: return "text-gray-600 dark:text-gray-400";
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "improving": return "📈";
      case "declining": return "📉";
      default: return "➡️";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-br from-indigo-600 to-purple-600 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">Insights do Agente</h2>
            <p className="text-indigo-100 mt-1">{agentName}</p>
          </div>
          <div className="text-5xl">📊</div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-indigo-200 text-sm">Total Feedbacks</p>
            <p className="text-2xl font-bold">{insights.totalFeedbacks}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-indigo-200 text-sm">Rating Médio</p>
            <p className="text-2xl font-bold">{insights.avgRating.toFixed(1)} ⭐</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-indigo-200 text-sm">Melhorias Sugeridas</p>
            <p className="text-2xl font-bold">{insights.suggestedImprovements.length}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-indigo-200 text-sm">Tendência</p>
            <p className={`text-2xl font-bold ${getTrendColor(trend?.trend || "stable")}`}>
              {getTrendIcon(trend?.trend || "stable")}
            </p>
          </div>
        </div>
      </div>

      {/* Strength Areas */}
      {insights.strengthAreas.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl">💪</span>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Pontos Fortes</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {insights.strengthAreas.map((strength, idx) => (
              <div
                key={idx}
                className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
              >
                <p className="text-sm text-green-700 dark:text-green-400">✓ {strength}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Improvement Areas */}
      {insights.improvementAreas.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl">🎯</span>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Áreas de Melhoria</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {insights.improvementAreas.map((area, idx) => (
              <div
                key={idx}
                className="p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg"
              >
                <p className="text-sm text-orange-700 dark:text-orange-400">⚠️ {area}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Common Issues */}
      {insights.commonIssues.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Issues Mais Reportados
          </h3>
          <div className="space-y-2">
            {insights.commonIssues.slice(0, 5).map(({ issue, count }) => (
              <div
                key={issue}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg"
              >
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {issue.replace(/_/g, " ")}
                </span>
                <span className="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full text-xs font-medium">
                  {count} {count === 1 ? "relato" : "relatos"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suggested Improvements */}
      {insights.suggestedImprovements.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-2xl">🔄</span>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Melhorias Sugeridas nas Instruções
              </h3>
            </div>
            {onApplyImprovements && (
              <button
                onClick={handleApplyAll}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium"
              >
                ✨ Aplicar Todas
              </button>
            )}
          </div>

          <div className="space-y-4">
            {insights.suggestedImprovements.map((improvement, idx) => (
              <div
                key={idx}
                className="border border-gray-200 dark:border-slate-600 rounded-xl overflow-hidden"
              >
                <div
                  className="p-4 bg-gray-50 dark:bg-slate-700/50 cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
                  onClick={() => setSelectedImprovement(
                    selectedImprovement?.suggested === improvement.suggested ? null : improvement
                  )}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          improvement.confidence >= 0.7
                            ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                            : improvement.confidence >= 0.5
                            ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                            : "bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400"
                        }`}>
                          {(improvement.confidence * 100).toFixed(0)}% confiança
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {improvement.supportingFeedback} feedbacks
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{improvement.reason}</p>
                    </div>
                    <svg
                      className={`w-5 h-5 text-gray-400 transition-transform ${
                        selectedImprovement?.suggested === improvement.suggested ? "rotate-180" : ""
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>

                {selectedImprovement?.suggested === improvement.suggested && (
                  <div className="p-4 bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-600">
                    <div className="space-y-4">
                      <div>
                        <p className="text-xs font-medium text-red-600 dark:text-red-400 mb-2">
                          ❌ Instrução Atual (ou similar):
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                          {improvement.original}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-green-600 dark:text-green-400 mb-2">
                          ✅ Instrução Sugerida:
                        </p>
                        <p className="text-sm text-gray-900 dark:text-white font-medium">
                          {improvement.suggested}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rating Trend Chart */}
      {trend && trend.ratings.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Evolução do Rating
          </h3>
          <div className="flex items-end gap-1 h-40">
            {trend.ratings.map((rating, idx) => {
              const height = (rating / 5) * 100;
              const color = rating >= 4 ? "bg-green-500" : rating >= 3 ? "bg-yellow-500" : "bg-red-500";
              
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                  <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-t relative" style={{ height: `${height}%`, minHeight: "20px" }}>
                    <div className={`absolute inset-0 ${color} rounded-t transition-all`} />
                    <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white">
                      {rating.toFixed(1)}
                    </span>
                  </div>
                  <span className="text-xs text-gray-400">{trend.dates[idx].slice(-5)}</span>
                </div>
              );
            })}
          </div>
          <div className="mt-4 p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
            <p className="text-sm text-center">
              <span className={`font-medium ${getTrendColor(trend.trend)}`}>
                {trend.trend === "improving" && "✓ Rating melhorando ao longo do tempo"}
                {trend.trend === "declining" && "⚠ Rating declinando - atenção necessária"}
                {trend.trend === "stable" && "→ Rating estável"}
              </span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
