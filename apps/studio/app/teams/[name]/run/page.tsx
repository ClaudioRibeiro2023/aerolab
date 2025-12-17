"use client";
import React, { useState, useEffect, useRef } from "react";
import Protected from "../../../../components/Protected";
import Link from "next/link";
import { useParams } from "next/navigation";
import api from "../../../../lib/api";
import { toast } from "sonner";
import { addToHistory, getHistoryByFilter, ExecutionRecord } from "../../../../lib/executionHistory";
import { trackExecution, estimateExecutionCost } from "../../../../lib/analytics";

const Icons = {
  back: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>),
  play: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  spinner: (<svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>),
  user: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>),
  arrow: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>),
};

interface TeamData {
  name: string;
  members: string[];
  description?: string;
}

interface ExecutionStep {
  agent: string;
  status: "pending" | "running" | "done" | "error";
  output?: string;
}

export default function TeamRunPage() {
  const params = useParams();
  const teamName = decodeURIComponent((params?.name as string) || "");

  const [team, setTeam] = useState<TeamData | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [steps, setSteps] = useState<ExecutionStep[]>([]);
  const [finalResult, setFinalResult] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadTeam();
  }, [teamName]);

  const loadTeam = async () => {
    if (!teamName) return;
    setLoading(true);
    try {
      const { data } = await api.get(`/teams/${encodeURIComponent(teamName)}`);
      setTeam(data);
      // Initialize steps
      if (data?.members) {
        setSteps(data.members.map((m: string) => ({ agent: m, status: "pending" as const })));
      }
    } catch (e) {
      toast.error("Erro ao carregar time");
    } finally {
      setLoading(false);
    }
  };

  const runTeam = async () => {
    if (!prompt.trim() || !team) return;
    
    setRunning(true);
    setFinalResult(null);
    setSteps(team.members.map(m => ({ agent: m, status: "pending" })));

    const startTime = Date.now();

    try {
      // Simulate sequential execution with visual feedback
      for (let i = 0; i < team.members.length; i++) {
        setSteps(prev => prev.map((s, idx) => 
          idx === i ? { ...s, status: "running" } : s
        ));
        
        // Small delay for visual effect
        await new Promise(r => setTimeout(r, 500));
      }

      // Actually run the team
      const { data } = await api.post(`/teams/${encodeURIComponent(teamName)}/run`, {
        prompt: prompt.trim(),
      });

      const result = data.result || data.output || JSON.stringify(data, null, 2);
      const duration = (Date.now() - startTime) / 1000;

      // Mark all as done
      setSteps(prev => prev.map(s => ({ ...s, status: "done" })));
      setFinalResult(result);
      
      // Salvar no histórico
      addToHistory({
        type: "team",
        name: teamName,
        prompt: prompt.trim(),
        result: result.substring(0, 500), // Limitar tamanho
        timestamp: new Date().toISOString(),
        duration,
        status: "success",
      });

      // Rastrear execução para analytics
      const tokens = Math.ceil((prompt.length + result.length) / 4);
      trackExecution({
        agentName: `Team: ${teamName}`,
        duration,
        tokens,
        cost: estimateExecutionCost(tokens, "groq", "llama-3.3-70b-versatile") * team.members.length,
        success: true,
      });
      
      toast.success("Time executado com sucesso!");
      
      // Scroll to result
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    } catch (e: any) {
      const duration = (Date.now() - startTime) / 1000;
      
      setSteps(prev => prev.map((s, i) => 
        i === prev.length - 1 ? { ...s, status: "error" } : s
      ));
      
      // Salvar erro no histórico
      addToHistory({
        type: "team",
        name: teamName,
        prompt: prompt.trim(),
        result: e?.response?.data?.detail || "Erro ao executar time",
        timestamp: new Date().toISOString(),
        duration,
        status: "error",
      });

      // Rastrear execução com erro para analytics
      trackExecution({
        agentName: `Team: ${teamName}`,
        duration,
        tokens: Math.ceil(prompt.length / 4),
        cost: 0,
        success: false,
      });
      
      toast.error(e?.response?.data?.detail || "Erro ao executar time");
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <Protected>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            {Icons.spinner}
            <p className="mt-2 text-gray-500">Carregando...</p>
          </div>
        </div>
      </Protected>
    );
  }

  if (!team) {
    return (
      <Protected>
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Time não encontrado</h2>
          <Link href="/teams" className="text-blue-600 mt-2 inline-block">← Voltar</Link>
        </div>
      </Protected>
    );
  }

  return (
    <Protected>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Link href="/teams" className="p-2 text-gray-500 hover:text-blue-600 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Voltar">{Icons.back}</Link>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Executar {team.name}</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm">{team.description || `${team.members.length} agentes em sequência`}</p>
          </div>
        </div>

        {/* Pipeline Visualization */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Pipeline de Execução</h3>
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {steps.map((step, i) => (
              <React.Fragment key={i}>
                <div className={`flex items-center gap-2 px-4 py-3 rounded-xl min-w-fit transition-all ${
                  step.status === "running" ? "bg-blue-100 dark:bg-blue-900/30 ring-2 ring-blue-500" :
                  step.status === "done" ? "bg-green-100 dark:bg-green-900/30" :
                  step.status === "error" ? "bg-red-100 dark:bg-red-900/30" :
                  "bg-gray-100 dark:bg-slate-700"
                }`}>
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    step.status === "running" ? "bg-blue-500 text-white" :
                    step.status === "done" ? "bg-green-500 text-white" :
                    step.status === "error" ? "bg-red-500 text-white" :
                    "bg-gray-300 dark:bg-slate-600 text-gray-600 dark:text-gray-300"
                  }`}>
                    {step.status === "running" ? Icons.spinner : Icons.user}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{step.agent}</p>
                    <p className="text-xs text-gray-500 capitalize">{
                      step.status === "pending" ? "Aguardando" :
                      step.status === "running" ? "Executando..." :
                      step.status === "done" ? "Concluído" : "Erro"
                    }</p>
                  </div>
                </div>
                {i < steps.length - 1 && (
                  <div className="text-gray-400 dark:text-gray-500">{Icons.arrow}</div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Prompt Input */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Prompt de Entrada</h3>
          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="Digite o prompt inicial para o time processar..."
            className="w-full h-32 px-4 py-3 bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-600 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800 dark:text-gray-200"
            disabled={running}
          />
          <div className="flex justify-end mt-4">
            <button
              onClick={runTeam}
              disabled={!prompt.trim() || running}
              className="btn-primary flex items-center gap-2"
            >
              {running ? Icons.spinner : Icons.play}
              {running ? "Executando..." : "Executar Time"}
            </button>
          </div>
        </div>

        {/* Result */}
        {finalResult && (
          <div ref={resultRef} className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Resultado Final</h3>
            <div className="bg-gray-50 dark:bg-slate-900 rounded-xl p-4 max-h-96 overflow-y-auto">
              <pre className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap font-mono">{finalResult}</pre>
            </div>
          </div>
        )}

        {/* Quick Prompts */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Sugestões de Prompts</h3>
          <div className="flex flex-wrap gap-2">
            {[
              "Escreva um artigo sobre inteligência artificial",
              "Analise tendências do mercado de tecnologia",
              "Crie um resumo executivo sobre sustentabilidade",
              "Desenvolva um plano de marketing digital",
            ].map((p, i) => (
              <button
                key={i}
                onClick={() => setPrompt(p)}
                disabled={running}
                className="px-3 py-2 text-sm bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:text-blue-700 dark:hover:text-blue-400 transition-colors"
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>
    </Protected>
  );
}
