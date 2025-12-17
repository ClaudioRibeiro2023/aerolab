"use client";
import React, { useState, useEffect } from "react";
import Protected from "../../../components/Protected";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "../../../lib/api";
import { toast } from "sonner";

const teamTemplates = [
  { id: "blank", name: "Em Branco", desc: "Configure do zero", icon: "📝" },
  { id: "content", name: "Criação de Conteúdo", desc: "Pesquisador + Escritor", icon: "✍️", members: ["Researcher", "Writer"] },
  { id: "review", name: "Revisão", desc: "Pesquisador + Escritor + Revisor", icon: "📝", members: ["Researcher", "Writer", "Reviewer"] },
  { id: "analysis", name: "Análise de Dados", desc: "Analista + Escritor", icon: "📊", members: ["Analyst", "Writer"] },
  { id: "development", name: "Desenvolvimento", desc: "Arquiteto + Programador + Revisor", icon: "💻", members: ["Architect", "Coder", "Reviewer"] },
  { id: "research", name: "Pesquisa", desc: "Múltiplos Pesquisadores", icon: "🔍", members: ["Researcher", "Researcher"] },
];

const Icons = {
  back: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>),
  check: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>),
  plus: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>),
  trash: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>),
  spinner: (<svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>),
  user: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>),
};

interface Agent { name: string; role?: string; }

export default function NewTeamPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [creating, setCreating] = useState(false);
  const [agents, setAgents] = useState<Agent[]>([]);

  // Form state
  const [template, setTemplate] = useState("blank");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [members, setMembers] = useState<string[]>([]);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const { data } = await api.get("/agents");
      setAgents(data || []);
    } catch (e) {
      console.error("Erro ao carregar agentes:", e);
    }
  };

  const selectTemplate = (id: string) => {
    const t = teamTemplates.find(x => x.id === id);
    setTemplate(id);
    if (t && t.members) {
      // Filtrar apenas membros que existem
      const existingMembers = t.members.filter(m => agents.some(a => a.name === m));
      setMembers(existingMembers);
    }
    setStep(2);
  };

  const addMember = (agentName: string) => {
    if (!members.includes(agentName)) {
      setMembers([...members, agentName]);
    }
  };

  const removeMember = (index: number) => {
    setMembers(members.filter((_, i) => i !== index));
  };

  const handleCreate = async () => {
    if (!name.trim()) { toast.error("Nome é obrigatório"); return; }
    if (members.length === 0) { toast.error("Adicione pelo menos um membro"); return; }
    
    setCreating(true);
    try {
      await api.post("/teams", {
        name: name.trim(),
        members,
        description: description.trim() || undefined,
      });
      toast.success("Time criado com sucesso!");
      router.push("/teams");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Erro ao criar time");
    } finally {
      setCreating(false);
    }
  };

  const progress = (step / 3) * 100;

  return (
    <Protected>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Link href="/teams" className="p-2 text-gray-500 hover:text-blue-600 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Voltar">{Icons.back}</Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Criar Novo Time</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm">Etapa {step} de 3</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-300" style={{ width: `${progress}%` }} />
        </div>

        {/* Step 1: Template */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Escolha um template</h2>
            <div className="grid md:grid-cols-3 gap-4">
              {teamTemplates.map(t => (
                <button key={t.id} onClick={() => selectTemplate(t.id)} className="p-6 bg-white dark:bg-slate-800 rounded-2xl border-2 border-gray-100 dark:border-slate-700 hover:border-purple-500 text-left transition-all">
                  <div className="text-4xl mb-3">{t.icon}</div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">{t.name}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t.desc}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Info Básica */}
        {step === 2 && (
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Informações do Time</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nome do Time *</label>
                <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Ex: Time de Conteúdo" className="input-modern" autoFocus />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Descrição</label>
                <input type="text" value={description} onChange={e => setDescription(e.target.value)} placeholder="Ex: Cria artigos de blog" className="input-modern" />
              </div>
            </div>
            <div className="flex gap-3 pt-4">
              <button onClick={() => setStep(1)} className="btn-secondary">Voltar</button>
              <button onClick={() => setStep(3)} disabled={!name.trim()} className="btn-primary flex-1">Próximo</button>
            </div>
          </div>
        )}

        {/* Step 3: Membros */}
        {step === 3 && (
          <div className="space-y-6">
            {/* Membros Selecionados */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Membros do Time ({members.length})</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">Agentes executarão em sequência na ordem listada</p>
              
              <div className="space-y-2">
                {members.map((member, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-slate-900 rounded-lg">
                    <span className="w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600 flex items-center justify-center text-xs font-bold">{i + 1}</span>
                    <span className="text-sm text-gray-800 dark:text-gray-200 flex-1">{member}</span>
                    <button onClick={() => removeMember(i)} className="p-1 text-gray-400 hover:text-red-500" title="Remover">{Icons.trash}</button>
                  </div>
                ))}
                {members.length === 0 && (
                  <p className="text-sm text-gray-400 italic text-center py-4">Nenhum membro adicionado</p>
                )}
              </div>
            </div>

            {/* Agentes Disponíveis */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Agentes Disponíveis</h2>
              
              {agents.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500 dark:text-gray-400 mb-4">Nenhum agente disponível</p>
                  <Link href="/agents/new" className="text-blue-600 hover:underline">Criar um agente primeiro</Link>
                </div>
              ) : (
                <div className="grid md:grid-cols-2 gap-2">
                  {agents.map(agent => (
                    <button
                      key={agent.name}
                      onClick={() => addMember(agent.name)}
                      className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-slate-900 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors text-left"
                    >
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs">
                        {Icons.user}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 dark:text-white text-sm truncate">{agent.name}</p>
                        <p className="text-xs text-gray-500 truncate">{agent.role || "Agente"}</p>
                      </div>
                      <span className="text-purple-500">{Icons.plus}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button onClick={() => setStep(2)} className="btn-secondary">Voltar</button>
              <button onClick={handleCreate} disabled={creating || members.length === 0} className="btn-primary flex-1 flex items-center justify-center gap-2">
                {creating ? Icons.spinner : Icons.check} {creating ? "Criando..." : "Criar Time"}
              </button>
            </div>
          </div>
        )}
      </div>
    </Protected>
  );
}
