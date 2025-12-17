"use client";

import React, { useState, useEffect } from "react";
import Protected from "../../../components/Protected";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "../../../lib/api";
import { toast } from "sonner";
import { useAuth } from "../../../store/auth";
import AgentTemplateSelector from "../../../components/AgentTemplateSelector";
import AgentPreview from "../../../components/AgentPreview";
import AgentProfileSelector, { agentProfiles, type AgentProfile } from "../../../components/AgentProfileSelector";
import AgentToolsSelector, { availableTools } from "../../../components/AgentToolsSelector";
import { type AgentTemplate } from "../../../lib/agentTemplates";
import { PageHeader } from "../../../components/PageHeader";
import { PageSection } from "../../../components/PageSection";
import { ToggleCard } from "../../../components/ToggleCard";

// Modelos atualizados conforme catálogo llm_catalog.json
const modelOptions = [
  { 
    provider: "openai", 
    label: "OpenAI",
    models: [
      { id: "gpt-5.1", name: "GPT-5.1", desc: "Frontier geral, vision, tools", badge: "Recomendado" },
      { id: "gpt-5.1-codex-max", name: "GPT-5.1 Codex Max", desc: "Coding frontier", badge: "Coding" },
      { id: "gpt-5.1-codex-mini", name: "GPT-5.1 Codex Mini", desc: "Coding alto volume" },
      { id: "o3-pro", name: "O3 Pro", desc: "Deep reasoning", badge: "Reasoning" },
    ] 
  },
  { 
    provider: "anthropic", 
    label: "Anthropic",
    models: [
      { id: "claude-sonnet-4.5", name: "Claude Sonnet 4.5", desc: "Frontier geral", badge: "Recomendado" },
      { id: "claude-opus-4.5", name: "Claude Opus 4.5", desc: "Deep reasoning", badge: "Reasoning" },
      { id: "claude-haiku-4.5", name: "Claude Haiku 4.5", desc: "Rápido e econômico", badge: "Fast" },
    ] 
  },
  { 
    provider: "google_gemini", 
    label: "Google Gemini",
    models: [
      { id: "gemini-2.5-pro", name: "Gemini 2.5 Pro", desc: "Multimodal frontier", badge: "Recomendado" },
      { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", desc: "Rápido, 1M contexto", badge: "Fast" },
      { id: "gemini-2.5-flash-lite", name: "Gemini 2.5 Flash Lite", desc: "Ultra rápido" },
      { id: "gemini-3-pro", name: "Gemini 3 Pro", desc: "Research reasoning", badge: "Novo" },
    ] 
  },
  { 
    provider: "mistral", 
    label: "Mistral",
    models: [
      { id: "mistral-large-3", name: "Mistral Large 3", desc: "Open-weight frontier", badge: "Recomendado" },
      { id: "mistral-medium-3.1", name: "Mistral Medium 3.1", desc: "Uso geral" },
      { id: "mistral-small-3.1", name: "Mistral Small 3.1", desc: "Rápido e econômico", badge: "Fast" },
    ] 
  },
];

const Icons = {
  back: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>),
  check: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>),
  plus: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>),
  trash: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>),
  spinner: (<svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>),
  play: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /></svg>),
};

export default function NewAgentPage() {
  const router = useRouter();
  const { role: userRole, isHydrated } = useAuth();
  const [step, setStep] = useState(1);
  const [creating, setCreating] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testOutput, setTestOutput] = useState<string | null>(null);

  // Verificar permissão (só após hidratação completa)
  useEffect(() => {
    // Só verifica após hidratação E se role foi carregado
    if (isHydrated && userRole !== null && userRole !== "admin") {
      toast.error("Apenas administradores podem criar agentes");
      router.replace("/agents");
    }
  }, [userRole, router, isHydrated]);

  // Form state
  const [template, setTemplate] = useState("blank");
  const [name, setName] = useState("");
  const [agentRole, setAgentRole] = useState("");
  const [agentProfile, setAgentProfile] = useState("balanced");
  const [provider, setProvider] = useState("openai");
  const [modelId, setModelId] = useState("gpt-5.1");
  const [instructions, setInstructions] = useState<string[]>([]);
  const [newInstruction, setNewInstruction] = useState("");
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const [useDatabase, setUseDatabase] = useState(false);
  const [addHistory, setAddHistory] = useState(true);
  const [markdown, setMarkdown] = useState(true);
  const [debugMode, setDebugMode] = useState(false);
  const [testPrompt, setTestPrompt] = useState("");

  const handleProfileSelect = (profile: AgentProfile) => {
    setAgentProfile(profile.id);
    if (profile.id !== "custom") {
      setProvider(profile.recommended_provider);
      setModelId(profile.recommended_model);
    }
  };

  const toggleTool = (toolId: string) => {
    setSelectedTools(prev => 
      prev.includes(toolId) 
        ? prev.filter(t => t !== toolId)
        : [...prev, toolId]
    );
  };

  const selectTemplate = (template: AgentTemplate) => {
    setTemplate(template.id);
    setName(template.name);
    setAgentRole(template.description);
    setProvider(template.recommendedModel.provider);
    setModelId(template.recommendedModel.modelId);
    if (template.instructions.length > 0) setInstructions([...template.instructions]);
    if (template.config) {
      setUseDatabase(template.config.useDatabase || false);
      setAddHistory(template.config.addHistory !== false);
      setMarkdown(template.config.markdown !== false);
    }
    setStep(2);
  };

  const addInstruction = () => {
    if (!newInstruction.trim()) return;
    setInstructions([...instructions, newInstruction.trim()]);
    setNewInstruction("");
  };

  const removeInstruction = (index: number) => {
    setInstructions(instructions.filter((_, i) => i !== index));
  };

  const handleCreate = async () => {
    if (!name.trim()) { toast.error("Nome é obrigatório"); return; }
    setCreating(true);
    try {
      await api.post("/agents", {
        name: name.trim(),
        role: agentRole.trim() || undefined,
        model_provider: provider,
        model_id: modelId,
        instructions: instructions.length > 0 ? instructions : undefined,
        use_database: useDatabase,
        add_history_to_context: addHistory,
        markdown,
        debug_mode: debugMode,
      });
      toast.success("Agente criado com sucesso!");
      router.push("/agents");
    } catch (e: any) {
      const status = e?.response?.status;
      const detail = e?.response?.data?.detail;
      
      if (status === 401) {
        toast.error("Sessão expirada. Faça login novamente.");
      } else if (status === 403) {
        toast.error("Sem permissão. Apenas administradores podem criar agentes.");
      } else if (status === 409) {
        toast.error("Já existe um agente com este nome.");
      } else {
        toast.error(detail || "Erro ao criar agente. Verifique sua conexão.");
      }
    } finally {
      setCreating(false);
    }
  };

  const handleTest = async () => {
    if (!testPrompt.trim()) return;
    setTesting(true);
    setTestOutput(null);
    try {
      // Criar agente temporário para teste
      const tempName = `_test_${Date.now()}`;
      await api.post("/agents", { name: tempName, role: agentRole, model_provider: provider, model_id: modelId, instructions });
      const res = await api.post(`/agents/${tempName}/run`, { prompt: testPrompt });
      setTestOutput(res.data?.output || "Sem resposta");
      await api.delete(`/agents/${tempName}`);
    } catch (e: any) {
      toast.error("Erro no teste: " + (e?.response?.data?.detail || e.message));
    } finally {
      setTesting(false);
    }
  };

  const totalSteps = 5;
  const progress = (step / totalSteps) * 100;
  const stepNames = ["Template", "Perfil", "Instruções", "Ferramentas", "Configurar"];

  return (
    <Protected>
      <div className="max-w-4xl mx-auto space-y-6">
        <PageHeader
          title="Criar Novo Agente"
          subtitle={`Etapa ${step} de ${totalSteps}: ${stepNames[step - 1]}`}
          leadingAction={
            <Link
              href="/agents"
              className="p-2 text-gray-500 hover:bg-gray-100 hover:text-blue-600 rounded-lg transition-colors dark:hover:bg-slate-700"
              title="Voltar"
            >
              {Icons.back}
            </Link>
          }
        />

        {/* Progress Bar */}
        <div className="h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300" style={{ width: `${progress}%` }} />
        </div>

        {/* Step 1: Template Selector */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Escolha um Template</h2>
              <p className="text-gray-500 dark:text-gray-400">Comece com um template pronto ou crie do zero</p>
            </div>
            <AgentTemplateSelector onSelect={selectTemplate} />
          </div>
        )}

        {/* Step 2: Perfil e Modelo */}
        {step === 2 && (
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* Informações Básicas */}
              <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Informações Básicas</h2>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nome do Agente *</label>
                    <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Ex: Assistente de Vendas" className="input-modern" autoFocus />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Descrição/Role</label>
                    <input type="text" value={agentRole} onChange={e => setAgentRole(e.target.value)} placeholder="Ex: Especialista em atendimento" className="input-modern" />
                  </div>
                </div>
              </div>

              {/* Profile Selector */}
              <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Perfil do Agente</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">Escolha um perfil que define automaticamente o modelo ideal para seu caso de uso</p>
                <AgentProfileSelector selected={agentProfile} onSelect={handleProfileSelect} />
              </div>

              {/* Model Selection (colapsável para perfil custom) */}
              {agentProfile === "custom" && (
                <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Modelo Personalizado</h2>
                  {/* Provedor Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Provedor de IA</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {modelOptions.map(m => (
                  <button
                    key={m.provider}
                    type="button"
                    onClick={() => { setProvider(m.provider); setModelId(m.models[0]?.id || ""); }}
                    className={`p-3 rounded-xl border-2 transition-all text-left ${
                      provider === m.provider 
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" 
                        : "border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500"
                    }`}
                  >
                    <span className="font-medium text-gray-900 dark:text-white">{m.label}</span>
                    <span className="block text-xs text-gray-500 dark:text-gray-400 mt-0.5">{m.models.length} modelos</span>
                  </button>
                ))}
              </div>
            </div>

                  {/* Model Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Modelo</label>
                    <div className="grid gap-2">
                      {modelOptions.find(m => m.provider === provider)?.models.map(m => (
                        <button
                          key={m.id}
                          type="button"
                          onClick={() => setModelId(m.id)}
                          className={`p-3 rounded-xl border-2 transition-all text-left flex items-center justify-between ${
                            modelId === m.id 
                              ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" 
                              : "border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500"
                          }`}
                        >
                          <div>
                            <span className="font-medium text-gray-900 dark:text-white">{m.name}</span>
                            <span className="block text-xs text-gray-500 dark:text-gray-400 mt-0.5">{m.desc}</span>
                          </div>
                          {m.badge && (
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              m.badge === "Recomendado" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" :
                              m.badge === "Novo" ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" :
                              m.badge === "Grátis" ? "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400" :
                              "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                            }`}>
                              {m.badge}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="flex gap-3 pt-4">
                <button onClick={() => setStep(1)} className="btn-secondary">Voltar</button>
                <button onClick={() => setStep(3)} disabled={!name.trim()} className="btn-primary flex-1">Próximo</button>
              </div>
            </div>
            {/* Preview */}
            <div className="lg:col-span-1">
              <AgentPreview
                name={name}
                role={agentRole}
                provider={provider}
                modelId={modelId}
                instructions={instructions}
                markdown={markdown}
              />
            </div>
          </div>
        )}

        {/* Step 3: Instruções */}
        {step === 3 && (
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Instruções do Agente</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">Defina como o agente deve se comportar</p>
            
            <div className="space-y-2">
              {instructions.map((inst, i) => (
                <div key={i} className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-slate-900 rounded-lg">
                  <span className="text-sm text-gray-800 dark:text-gray-200 flex-1">{inst}</span>
                  <button onClick={() => removeInstruction(i)} className="p-1 text-gray-400 hover:text-red-500" title="Remover">{Icons.trash}</button>
                </div>
              ))}
            </div>
            
            <div className="flex gap-2">
              <input type="text" value={newInstruction} onChange={e => setNewInstruction(e.target.value)} onKeyDown={e => e.key === "Enter" && addInstruction()} placeholder="Adicionar nova instrução..." className="input-modern flex-1" />
              <button onClick={addInstruction} className="btn-secondary">{Icons.plus}</button>
            </div>
            
              <div className="flex gap-3 pt-4">
                <button onClick={() => setStep(2)} className="btn-secondary">Voltar</button>
                <button onClick={() => setStep(4)} className="btn-primary flex-1">Próximo</button>
              </div>
            </div>
            {/* Preview */}
            <div className="lg:col-span-1">
              <AgentPreview
                name={name}
                role={agentRole}
                provider={provider}
                modelId={modelId}
                instructions={instructions}
                markdown={markdown}
              />
            </div>
          </div>
        )}

        {/* Step 4: Ferramentas */}
        {step === 4 && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Ferramentas do Agente</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Selecione as ferramentas que o agente poderá usar. Ferramentas permitem que o agente interaja com sistemas externos.
              </p>
              <AgentToolsSelector 
                selected={selectedTools} 
                onToggle={toggleTool}
                recommendedFor={template}
              />
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(3)} className="btn-secondary">Voltar</button>
              <button onClick={() => setStep(5)} className="btn-primary flex-1">Próximo</button>
            </div>
          </div>
        )}

        {/* Step 5: Configurações e Teste */}
        {step === 5 && (
          <div className="space-y-6">
            {/* Configurações */}
            <PageSection title="Configurações Avançadas">
              <div className="grid gap-4 md:grid-cols-2">
                {[
                  { key: "db", label: "Usar Database", desc: "Persistir dados do agente", val: useDatabase, set: setUseDatabase },
                  { key: "hist", label: "Histórico no Contexto", desc: "Lembrar conversas anteriores", val: addHistory, set: setAddHistory },
                  { key: "md", label: "Markdown", desc: "Formatar respostas em Markdown", val: markdown, set: setMarkdown },
                  { key: "debug", label: "Modo Debug", desc: "Logs detalhados", val: debugMode, set: setDebugMode },
                ].map((opt) => (
                  <ToggleCard
                    key={opt.key}
                    label={opt.label}
                    description={opt.desc}
                    enabled={opt.val}
                    onToggle={opt.set}
                  />
                ))}
              </div>
            </PageSection>

            {/* Teste */}
            <PageSection title="Testar Agente">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={testPrompt}
                  onChange={(e) => setTestPrompt(e.target.value)}
                  placeholder="Digite uma mensagem de teste..."
                  className="input-modern flex-1"
                />
                <button
                  onClick={handleTest}
                  disabled={testing || !testPrompt.trim()}
                  className="btn-secondary flex items-center gap-2"
                >
                  {testing ? Icons.spinner : Icons.play} Testar
                </button>
              </div>
              {testOutput && (
                <div className="mt-4 rounded-xl bg-gray-50 p-4 dark:bg-slate-900">
                  <p className="mb-2 text-xs text-gray-500">Resposta:</p>
                  <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200">{testOutput}</pre>
                </div>
              )}
            </PageSection>

            {/* Actions */}
            <div className="flex gap-3">
              <button onClick={() => setStep(4)} className="btn-secondary">Voltar</button>
              <button onClick={handleCreate} disabled={creating} className="btn-primary flex-1 flex items-center justify-center gap-2">
                {creating ? Icons.spinner : Icons.check} {creating ? "Criando..." : "Criar Agente"}
              </button>
            </div>
          </div>
        )}
      </div>
    </Protected>
  );
}
