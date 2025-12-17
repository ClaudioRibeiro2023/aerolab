"use client";

import React, { useEffect, useState } from "react";
import Protected from "../../components/Protected";
import api from "../../lib/api";
import { toast } from "sonner";
import { useAuth } from "../../store/auth";

import Link from "next/link";
import { PageHeader } from "../../components/PageHeader";
import { PageSection } from "../../components/PageSection";
import { CardListSkeleton } from "../../components/CardListSkeleton";
import EmptyState from "../../components/EmptyState";

const Icons = {
  workflow: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 0h6v6h-6v-6z"
      />
    </svg>
  ),
  plus: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
  ),
  trash: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
      />
    </svg>
  ),
  play: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
      />
    </svg>
  ),
  x: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  arrow: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13 7l5 5m0 0l-5 5m5-5H6"
      />
    </svg>
  ),
  spinner: (
    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  ),
  builder: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z"
      />
    </svg>
  ),
};

type WorkflowStep = { type: string; name: string; input_template: string; output_var?: string };

export default function WorkflowsPage() {
  const { role } = useAuth();
  const [agents, setAgents] = useState<Array<{ name: string }>>([]);
  const [workflows, setWorkflows] = useState<Array<{ name: string; steps: WorkflowStep[] }>>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [running, setRunning] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const [wfName, setWfName] = useState("");
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [newStepAgent, setNewStepAgent] = useState("");
  const [newStepTemplate, setNewStepTemplate] = useState("");

  const [selRunWf, setSelRunWf] = useState("");
  const [runInputsText, setRunInputsText] = useState('{"topic": "Exemplo"}');
  const [runOutput, setRunOutput] = useState<any>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ag, wf] = await Promise.all([api.get("/agents"), api.get("/workflows/registry")]);
      setAgents(Array.isArray(ag.data) ? ag.data : []);
      setWorkflows(Array.isArray(wf.data) ? wf.data : []);
      if (!selRunWf && wf.data?.length) setSelRunWf(wf.data[0].name);
      if (!newStepAgent && ag.data?.length) setNewStepAgent(ag.data[0].name);
    } catch (e: any) { toast.error("Erro ao carregar"); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  const addStep = () => {
    if (!newStepAgent || !newStepTemplate) return;
    setSteps(p => [...p, { type: "agent", name: newStepAgent, input_template: newStepTemplate }]);
    setNewStepTemplate("");
  };

  const onCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wfName || !steps.length) { toast.error("Preencha nome e passos"); return; }
    if (role !== "admin") { toast.error("Apenas administradores podem criar workflows"); return; }
    
    setCreating(true);
    try {
      await api.post("/workflows/registry/", { name: wfName, steps });
      setWfName(""); setSteps([]); setShowCreateModal(false);
      await loadData();
      toast.success("Workflow criado!");
    } catch (e: any) {
      const status = e?.response?.status;
      if (status === 403) toast.error("Sem permissão para criar workflow");
      else if (status === 409) toast.error("Já existe um workflow com este nome");
      else toast.error("Erro ao criar workflow");
    } finally { setCreating(false); }
  };

  const onDeleteWorkflow = async (name: string) => {
    if (!confirm(`Excluir "${name}"?`)) return;
    try { 
      await api.delete(`/workflows/registry/${encodeURIComponent(name)}`); 
      await loadData(); 
      toast.success("Excluído"); 
    } catch (e: any) { 
      const status = e?.response?.status;
      if (status === 403) toast.error("Sem permissão para excluir");
      else toast.error("Erro ao excluir"); 
    }
  };

  const onRunWorkflow = async () => {
    setRunning(true); setRunOutput(null);
    try {
      const inputs = runInputsText ? JSON.parse(runInputsText) : {};
      const res = await api.post(`/workflows/registry/${encodeURIComponent(selRunWf)}/run`, { inputs });
      setRunOutput(res.data); toast.success("Concluído");
    } catch (e: any) {
      toast.error("Erro na execução: " + (e?.response?.data?.detail || e.message));
    } finally { setRunning(false); }
  };

  return (
    <Protected>
      <div className="space-y-6">
        <PageHeader
          title="Workflows"
          subtitle="Automatize processos com sequências de agentes"
          rightActions={
            <div className="flex items-center gap-3">
              <Link href="/workflows/builder" className="btn-secondary flex items-center gap-2">
                {Icons.builder} Visual Builder
              </Link>
              {role === "admin" && (
                <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
                  {Icons.plus} Novo Workflow
                </button>
              )}
            </div>
          }
        />

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {loading ? (
            <CardListSkeleton count={3} />
          ) : workflows.length === 0 ? (
            <div className="md:col-span-3">
              <EmptyState
                icon="🧩"
                title="Nenhum workflow ainda"
                description="Crie seu primeiro workflow para automatizar processos com agentes em sequência."
                action={
                  role === "admin"
                    ? { label: "Criar Workflow", onClick: () => setShowCreateModal(true) }
                    : undefined
                }
              />
            </div>
          ) : workflows.map((wf) => (
            <div key={wf.name} className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 hover:shadow-lg transition-all group">
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white shadow-lg">{Icons.workflow}</div>
                    <div><h3 className="font-semibold text-gray-900 dark:text-white">{wf.name}</h3><p className="text-sm text-gray-500 dark:text-gray-400">{wf.steps?.length || 0} passos</p></div>
                  </div>
                  {role === "admin" && <button onClick={() => onDeleteWorkflow(wf.name)} className="p-2 text-gray-400 hover:text-red-500 rounded-lg opacity-0 group-hover:opacity-100 transition-all" title="Excluir" aria-label="Excluir">{Icons.trash}</button>}
                </div>
                {wf.steps?.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-100 dark:border-slate-700">
                    <div className="flex flex-wrap items-center gap-2">
                      {wf.steps.slice(0,3).map((s,i) => (<span key={i} className="flex items-center gap-1"><span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded text-xs">{s.name}</span>{i < Math.min(wf.steps.length,3)-1 && <span className="text-gray-300">{Icons.arrow}</span>}</span>))}
                      {wf.steps.length > 3 && <span className="text-xs text-gray-400">+{wf.steps.length-3}</span>}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {workflows.length > 0 && (
          <PageSection title="Executar Workflow">
            <div className="grid gap-4 md:grid-cols-4">
              <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Workflow</label><select value={selRunWf} onChange={(e) => setSelRunWf(e.target.value)} className="input-modern" title="Selecionar">{workflows.map(w => <option key={w.name} value={w.name}>{w.name}</option>)}</select></div>
              <div className="md:col-span-2"><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Inputs (JSON)</label><textarea value={runInputsText} onChange={(e) => setRunInputsText(e.target.value)} className="input-modern font-mono text-sm min-h-[80px]" /></div>
              <div className="flex items-end"><button onClick={onRunWorkflow} disabled={running || !selRunWf} className="btn-primary w-full flex items-center justify-center gap-2">{running ? Icons.spinner : Icons.play} {running ? "Executando..." : "Executar"}</button></div>
            </div>
            {runOutput && <div className="mt-4 p-4 bg-gray-50 dark:bg-slate-900 rounded-xl"><pre className="text-sm whitespace-pre-wrap text-gray-800 dark:text-gray-200">{JSON.stringify(runOutput, null, 2)}</pre></div>}
          </PageSection>
        )}

        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 w-full max-w-lg shadow-2xl animate-scale-in">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Criar Workflow</h2>
              <form onSubmit={onCreateWorkflow} className="space-y-4">
                <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nome</label><input type="text" value={wfName} onChange={(e) => setWfName(e.target.value)} className="input-modern" required autoFocus /></div>
                <div className="p-4 bg-gray-50 dark:bg-slate-900 rounded-xl space-y-3">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Adicionar Passo</p>
                  <div className="grid gap-2 md:grid-cols-3">
                    <select value={newStepAgent} onChange={(e) => setNewStepAgent(e.target.value)} className="input-modern text-sm" title="Agente">{agents.map(a => <option key={a.name} value={a.name}>{a.name}</option>)}</select>
                    <input type="text" value={newStepTemplate} onChange={(e) => setNewStepTemplate(e.target.value)} placeholder="Template: {{topic}}" className="input-modern text-sm" />
                    <button type="button" onClick={addStep} disabled={!newStepAgent || !newStepTemplate} className="btn-secondary text-sm">+ Passo</button>
                  </div>
                  {steps.length > 0 && <div className="space-y-2 mt-3">{steps.map((s, i) => (<div key={i} className="flex items-center justify-between p-2 bg-white dark:bg-slate-800 rounded-lg"><span className="text-sm"><strong>{s.name}</strong>: {s.input_template}</span><button type="button" onClick={() => setSteps(p => p.filter((_,j) => j !== i))} className="text-gray-400 hover:text-red-500">{Icons.x}</button></div>))}</div>}
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setShowCreateModal(false)} className="btn-secondary flex-1">Cancelar</button>
                  <button type="submit" disabled={creating} className="btn-primary flex-1 flex items-center justify-center gap-2">{creating && Icons.spinner} {creating ? "Criando..." : "Criar"}</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Protected>
  );
}
