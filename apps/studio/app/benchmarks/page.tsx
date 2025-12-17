"use client";
import React, { useState, useEffect } from "react";
import Protected from "../../components/Protected";
import Link from "next/link";
import { toast } from "sonner";

interface Benchmark {
  id: string;
  name: string;
  description: string;
  category: string;
  taskCount: number;
  icon: string;
}

interface BenchmarkResult {
  benchmark_id: string;
  agent_id: string;
  model_id: string;
  overall_score: number;
  accuracy: number;
  relevance: number;
  coherence: number;
  avg_latency_ms: number;
  total_cost_usd: number;
  completed_tasks: number;
  total_tasks: number;
  timestamp: string;
}

const Icons = {
  play: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /></svg>),
  chart: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>),
  trophy: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>),
};

const mockBenchmarks: Benchmark[] = [
  { id: "general_v1", name: "General Intelligence", description: "Avalia capacidades gerais", category: "general", taskCount: 5, icon: "🧠" },
  { id: "coding_v1", name: "Coding Proficiency", description: "Avalia capacidades de programação", category: "coding", taskCount: 5, icon: "💻" },
  { id: "reasoning_v1", name: "Reasoning & Logic", description: "Avalia raciocínio lógico", category: "reasoning", taskCount: 5, icon: "🔬" },
];

const mockLeaderboard: BenchmarkResult[] = [
  { benchmark_id: "general_v1", agent_id: "researcher-pro", model_id: "gpt-5.1", overall_score: 0.92, accuracy: 0.95, relevance: 0.90, coherence: 0.88, avg_latency_ms: 720, total_cost_usd: 0.015, completed_tasks: 5, total_tasks: 5, timestamp: "2024-12-07T10:00:00Z" },
  { benchmark_id: "general_v1", agent_id: "assistant-v2", model_id: "claude-sonnet-4.5", overall_score: 0.88, accuracy: 0.90, relevance: 0.87, coherence: 0.85, avg_latency_ms: 890, total_cost_usd: 0.012, completed_tasks: 5, total_tasks: 5, timestamp: "2024-12-07T09:30:00Z" },
  { benchmark_id: "general_v1", agent_id: "fast-helper", model_id: "gemini-2.5-flash", overall_score: 0.82, accuracy: 0.85, relevance: 0.80, coherence: 0.78, avg_latency_ms: 320, total_cost_usd: 0.003, completed_tasks: 5, total_tasks: 5, timestamp: "2024-12-07T09:00:00Z" },
];

function ScoreBar({ score, label, color = "blue" }: { score: number; label: string; color?: string }) {
  const colorClasses = {
    blue: "bg-blue-500",
    green: "bg-green-500",
    purple: "bg-purple-500",
    orange: "bg-orange-500",
  };

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-gray-500">{label}</span>
        <span className="font-medium text-gray-700 dark:text-gray-300">{(score * 100).toFixed(0)}%</span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${colorClasses[color as keyof typeof colorClasses]} rounded-full transition-all duration-500`}
          style={{ width: `${score * 100}%` }}
        />
      </div>
    </div>
  );
}

export default function BenchmarksPage() {
  const [selectedBenchmark, setSelectedBenchmark] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<BenchmarkResult[]>(mockLeaderboard);

  const handleRunBenchmark = async (benchmarkId: string) => {
    setRunning(true);
    try {
      // Simular execução
      await new Promise(r => setTimeout(r, 3000));
      
      const newResult: BenchmarkResult = {
        benchmark_id: benchmarkId,
        agent_id: "my-agent",
        model_id: "gpt-5.1",
        overall_score: 0.85 + Math.random() * 0.1,
        accuracy: 0.88 + Math.random() * 0.1,
        relevance: 0.85 + Math.random() * 0.1,
        coherence: 0.82 + Math.random() * 0.1,
        avg_latency_ms: 500 + Math.random() * 500,
        total_cost_usd: 0.01 + Math.random() * 0.01,
        completed_tasks: 5,
        total_tasks: 5,
        timestamp: new Date().toISOString()
      };
      
      setResults([newResult, ...results]);
      toast.success("Benchmark concluído!");
    } catch (e) {
      toast.error("Erro ao executar benchmark");
    } finally {
      setRunning(false);
    }
  };

  const getLeaderboard = (benchmarkId: string) => {
    return results
      .filter(r => r.benchmark_id === benchmarkId)
      .sort((a, b) => b.overall_score - a.overall_score);
  };

  return (
    <Protected>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Benchmarks de Agentes</h1>
            <p className="text-gray-500 dark:text-gray-400">Avalie e compare a performance dos seus agentes</p>
          </div>
        </div>

        {/* Benchmarks Grid */}
        <div className="grid md:grid-cols-3 gap-4">
          {mockBenchmarks.map(benchmark => (
            <div 
              key={benchmark.id}
              className={`bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 transition-all cursor-pointer ${
                selectedBenchmark === benchmark.id
                  ? "border-blue-500 ring-2 ring-blue-200 dark:ring-blue-900"
                  : "border-gray-100 dark:border-slate-700 hover:border-gray-200"
              }`}
              onClick={() => setSelectedBenchmark(benchmark.id)}
            >
              <div className="flex items-start gap-3 mb-3">
                <span className="text-3xl">{benchmark.icon}</span>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">{benchmark.name}</h3>
                  <p className="text-sm text-gray-500">{benchmark.description}</p>
                </div>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">{benchmark.taskCount} tarefas</span>
                <button
                  onClick={(e) => { e.stopPropagation(); handleRunBenchmark(benchmark.id); }}
                  disabled={running}
                  className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-1"
                >
                  {running ? (
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : Icons.play}
                  Executar
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Leaderboard */}
        {selectedBenchmark && (
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 overflow-hidden">
            <div className="p-5 border-b border-gray-100 dark:border-slate-700">
              <div className="flex items-center gap-2">
                {Icons.trophy}
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Leaderboard: {mockBenchmarks.find(b => b.id === selectedBenchmark)?.name}
                </h2>
              </div>
            </div>
            
            <div className="divide-y divide-gray-100 dark:divide-slate-700">
              {getLeaderboard(selectedBenchmark).map((result, index) => (
                <div key={`${result.agent_id}-${result.timestamp}`} className="p-5">
                  <div className="flex items-start gap-4">
                    {/* Rank */}
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                      index === 0 ? "bg-yellow-100 text-yellow-700" :
                      index === 1 ? "bg-gray-100 text-gray-700" :
                      index === 2 ? "bg-orange-100 text-orange-700" :
                      "bg-gray-50 text-gray-500"
                    }`}>
                      {index + 1}
                    </div>
                    
                    {/* Agent Info */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-semibold text-gray-900 dark:text-white">{result.agent_id}</span>
                        <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-slate-700 rounded-full text-gray-600 dark:text-gray-300">
                          {result.model_id}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <ScoreBar score={result.accuracy} label="Accuracy" color="green" />
                        <ScoreBar score={result.relevance} label="Relevance" color="blue" />
                        <ScoreBar score={result.coherence} label="Coherence" color="purple" />
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-500">Latência</span>
                            <span className="font-medium text-gray-700 dark:text-gray-300">{result.avg_latency_ms.toFixed(0)}ms</span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-500">Custo</span>
                            <span className="font-medium text-gray-700 dark:text-gray-300">${result.total_cost_usd.toFixed(4)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Overall Score */}
                    <div className="text-center">
                      <div className={`text-3xl font-bold ${
                        result.overall_score >= 0.9 ? "text-green-600" :
                        result.overall_score >= 0.8 ? "text-blue-600" :
                        result.overall_score >= 0.7 ? "text-yellow-600" :
                        "text-red-600"
                      }`}>
                        {(result.overall_score * 100).toFixed(0)}
                      </div>
                      <div className="text-xs text-gray-500">Score</div>
                    </div>
                  </div>
                </div>
              ))}
              
              {getLeaderboard(selectedBenchmark).length === 0 && (
                <div className="p-10 text-center text-gray-500">
                  <span className="text-4xl block mb-2">🏆</span>
                  Nenhum resultado ainda. Execute o benchmark para começar!
                </div>
              )}
            </div>
          </div>
        )}

        {/* Info Cards */}
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-5 text-white">
            <h3 className="font-semibold mb-2">📊 Avalie Performance</h3>
            <p className="text-sm text-blue-100">Execute benchmarks padronizados para medir accuracy, relevância e coerência.</p>
          </div>
          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-5 text-white">
            <h3 className="font-semibold mb-2">🏆 Compare Agentes</h3>
            <p className="text-sm text-purple-100">Veja como seus agentes se comparam no leaderboard global.</p>
          </div>
          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl p-5 text-white">
            <h3 className="font-semibold mb-2">⚡ Otimize Custo</h3>
            <p className="text-sm text-green-100">Encontre o melhor balanço entre qualidade, velocidade e custo.</p>
          </div>
        </div>
      </div>
    </Protected>
  );
}
