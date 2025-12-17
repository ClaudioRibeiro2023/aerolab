"use client";
import React, { useState, useEffect } from "react";
import Protected from "../../../../components/Protected";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import api from "../../../../lib/api";
import { toast } from "sonner";
import { useAuth } from "../../../../store/auth";

// Modelos atualizados conforme catálogo llm_catalog.json
const modelOptions = [
  { 
    provider: "openai", 
    label: "OpenAI",
    models: [
      { id: "gpt-5.1", name: "GPT-5.1" },
      { id: "gpt-5.1-codex-max", name: "GPT-5.1 Codex Max" },
      { id: "gpt-5.1-codex-mini", name: "GPT-5.1 Codex Mini" },
      { id: "o3-pro", name: "O3 Pro" },
    ] 
  },
  { 
    provider: "anthropic", 
    label: "Anthropic",
    models: [
      { id: "claude-sonnet-4.5", name: "Claude Sonnet 4.5" },
      { id: "claude-opus-4.5", name: "Claude Opus 4.5" },
      { id: "claude-haiku-4.5", name: "Claude Haiku 4.5" },
    ] 
  },
  { 
    provider: "google_gemini", 
    label: "Google Gemini",
    models: [
      { id: "gemini-2.5-pro", name: "Gemini 2.5 Pro" },
      { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash" },
      { id: "gemini-2.5-flash-lite", name: "Gemini 2.5 Flash Lite" },
      { id: "gemini-3-pro", name: "Gemini 3 Pro" },
    ] 
  },
  { 
    provider: "mistral", 
    label: "Mistral",
    models: [
      { id: "mistral-large-3", name: "Mistral Large 3" },
      { id: "mistral-medium-3.1", name: "Mistral Medium 3.1" },
      { id: "mistral-small-3.1", name: "Mistral Small 3.1" },
    ] 
  },
];

const Icons = {
  back: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>),
  save: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>),
  plus: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>),
  trash: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>),
  spinner: (<svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>),
  play: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /></svg>),
};

interface AgentData {
  name: string;
  role?: string;
  model_provider?: string;
  model_id?: string;
  instructions?: string[];
  use_database?: boolean;
  add_history_to_context?: boolean;
  markdown?: boolean;
  debug_mode?: boolean;
}

export default function EditAgentPage() {
  const router = useRouter();
  const params = useParams();
  const { role: userRole, isHydrated } = useAuth();
  const agentName = decodeURIComponent((params?.name as string) || "");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testOutput, setTestOutput] = useState<string | null>(null);

  // Form state
  const [agentRole, setAgentRole] = useState("");
  const [provider, setProvider] = useState("openai");

  // Verificar permissão (só após hidratação completa)
  useEffect(() => {
    // Só verifica após hidratação E se role foi carregado
    if (isHydrated && userRole !== null && userRole !== "admin") {
      toast.error("Apenas administradores podem editar agentes");
      router.replace("/agents");
    }
  }, [userRole, router, isHydrated]);
  const [modelId, setModelId] = useState("gpt-5.1");
  const [instructions, setInstructions] = useState<string[]>([]);
  const [newInstruction, setNewInstruction] = useState("");
  const [useDatabase, setUseDatabase] = useState(false);
  const [addHistory, setAddHistory] = useState(true);
  const [markdown, setMarkdown] = useState(true);
  const [debugMode, setDebugMode] = useState(false);
  const [testPrompt, setTestPrompt] = useState("");

  useEffect(() => {
    loadAgent();
  }, [agentName]);

  const loadAgent = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/agents/${encodeURIComponent(agentName)}`);
      const data: AgentData = res.data;
      setAgentRole(data.role || "");
      setProvider(data.model_provider || "openai");
      setModelId(data.model_id || "gpt-4.1");
      setInstructions(data.instructions || []);
      setUseDatabase(data.use_database || false);
      setAddHistory(data.add_history_to_context !== false);
      setMarkdown(data.markdown !== false);
      setDebugMode(data.debug_mode || false);
    } catch (e: any) {
      toast.error("Erro ao carregar agente: " + (e?.response?.data?.detail || e.message));
      router.push("/agents");
    } finally {
      setLoading(false);
    }
  };

  const addInstruction = () => {
    if (!newInstruction.trim()) return;
    setInstructions([...instructions, newInstruction.trim()]);
    setNewInstruction("");
  };

  const removeInstruction = (index: number) => {
    setInstructions(instructions.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/agents/${encodeURIComponent(agentName)}`, {
        role: agentRole.trim() || undefined,
        model_provider: provider,
        model_id: modelId,
        instructions: instructions.length > 0 ? instructions : undefined,
        use_database: useDatabase,
        add_history_to_context: addHistory,
        markdown,
        debug_mode: debugMode,
      });
      toast.success("Agente atualizado com sucesso!");
      router.push("/agents");
    } catch (e: any) {
      const status = e?.response?.status;
      const detail = e?.response?.data?.detail;
      if (status === 403) toast.error("Apenas administradores podem editar agentes.");
      else toast.error(detail || "Erro ao atualizar agente");
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (!testPrompt.trim()) return;
    setTesting(true);
    setTestOutput(null);
    try {
      const res = await api.post(`/agents/${encodeURIComponent(agentName)}/run`, { prompt: testPrompt });
      setTestOutput(res.data?.output || "Sem resposta");
    } catch (e: any) {
      toast.error("Erro no teste: " + (e?.response?.data?.detail || e.message));
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <Protected>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            {Icons.spinner}
            <p className="mt-2 text-gray-500">Carregando agente...</p>
          </div>
        </div>
      </Protected>
    );
  }

  return (
    <Protected>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Link href="/agents" className="p-2 text-gray-500 hover:text-blue-600 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Voltar">{Icons.back}</Link>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Editar: {agentName}</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm">Modifique as configurações do agente</p>
          </div>
          <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
            {saving ? Icons.spinner : Icons.save}
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </div>

        {/* Info Básica */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Informações Básicas</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nome do Agente</label>
              <input type="text" value={agentName} disabled className="input-modern bg-gray-100 dark:bg-slate-900 cursor-not-allowed" />
              <p className="text-xs text-gray-500 mt-1">O nome não pode ser alterado</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Descrição/Role</label>
              <input type="text" value={agentRole} onChange={e => setAgentRole(e.target.value)} placeholder="Ex: Especialista em atendimento" className="input-modern" />
            </div>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Provedor</label>
              <select value={provider} onChange={e => { setProvider(e.target.value); setModelId(modelOptions.find(m => m.provider === e.target.value)?.models[0]?.id || ""); }} className="input-modern" title="Provedor de IA">
                {modelOptions.map(m => <option key={m.provider} value={m.provider}>{m.provider.charAt(0).toUpperCase() + m.provider.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Modelo</label>
              <select value={modelId} onChange={e => setModelId(e.target.value)} className="input-modern" title="Modelo de IA">
                {modelOptions.find(m => m.provider === provider)?.models.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Instruções */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Instruções do Agente</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">Defina como o agente deve se comportar</p>
          
          <div className="space-y-2">
            {instructions.map((inst, i) => (
              <div key={i} className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-slate-900 rounded-lg">
                <span className="text-sm text-gray-800 dark:text-gray-200 flex-1">{inst}</span>
                <button onClick={() => removeInstruction(i)} className="p-1 text-gray-400 hover:text-red-500" title="Remover">{Icons.trash}</button>
              </div>
            ))}
            {instructions.length === 0 && (
              <p className="text-sm text-gray-400 italic">Nenhuma instrução definida</p>
            )}
          </div>
          
          <div className="flex gap-2">
            <input type="text" value={newInstruction} onChange={e => setNewInstruction(e.target.value)} onKeyDown={e => e.key === "Enter" && addInstruction()} placeholder="Adicionar nova instrução..." className="input-modern flex-1" />
            <button onClick={addInstruction} className="btn-secondary" title="Adicionar">{Icons.plus}</button>
          </div>
        </div>

        {/* Configurações */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Configurações Avançadas</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {[
              { key: "db", label: "Usar Database", desc: "Persistir dados do agente", val: useDatabase, set: setUseDatabase },
              { key: "hist", label: "Histórico no Contexto", desc: "Lembrar conversas anteriores", val: addHistory, set: setAddHistory },
              { key: "md", label: "Markdown", desc: "Formatar respostas em Markdown", val: markdown, set: setMarkdown },
              { key: "debug", label: "Modo Debug", desc: "Logs detalhados", val: debugMode, set: setDebugMode },
            ].map(opt => (
              <div key={opt.key} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
                <div><p className="font-medium text-gray-900 dark:text-white">{opt.label}</p><p className="text-xs text-gray-500">{opt.desc}</p></div>
                <button onClick={() => opt.set(!opt.val)} className={`w-12 h-6 rounded-full transition-colors ${opt.val ? "bg-blue-500" : "bg-gray-300 dark:bg-slate-600"}`} title={opt.label}>
                  <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${opt.val ? "translate-x-6" : "translate-x-0.5"}`} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Teste */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Testar Agente</h2>
          <div className="flex gap-2">
            <input type="text" value={testPrompt} onChange={e => setTestPrompt(e.target.value)} placeholder="Digite uma mensagem de teste..." className="input-modern flex-1" />
            <button onClick={handleTest} disabled={testing || !testPrompt.trim()} className="btn-secondary flex items-center gap-2">
              {testing ? Icons.spinner : Icons.play} Testar
            </button>
          </div>
          {testOutput && (
            <div className="p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
              <p className="text-xs text-gray-500 mb-2">Resposta:</p>
              <pre className="text-sm whitespace-pre-wrap text-gray-800 dark:text-gray-200">{testOutput}</pre>
            </div>
          )}
        </div>
      </div>
    </Protected>
  );
}
