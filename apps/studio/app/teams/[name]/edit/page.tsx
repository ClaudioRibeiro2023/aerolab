"use client";
import React, { useState, useEffect } from "react";
import Protected from "../../../../components/Protected";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import api from "../../../../lib/api";
import { toast } from "sonner";

const Icons = {
  back: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>),
  save: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>),
  user: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>),
  x: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>),
  plus: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>),
  spinner: (<svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>),
  grip: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" /></svg>),
};

interface TeamData {
  name: string;
  members: string[];
  description?: string;
}

interface Agent {
  name: string;
  role?: string;
}

export default function TeamEditPage() {
  const params = useParams();
  const router = useRouter();
  const teamName = decodeURIComponent((params?.name as string) || "");

  const [team, setTeam] = useState<TeamData | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [members, setMembers] = useState<string[]>([]);

  useEffect(() => {
    loadData();
  }, [teamName]);

  const loadData = async () => {
    if (!teamName) return;
    setLoading(true);
    try {
      const [teamRes, agentsRes] = await Promise.all([
        api.get(`/teams/${encodeURIComponent(teamName)}`),
        api.get("/agents"),
      ]);
      
      const teamData = teamRes.data;
      setTeam(teamData);
      setName(teamData.name);
      setDescription(teamData.description || "");
      setMembers(teamData.members || []);
      setAgents(agentsRes.data || []);
    } catch (e) {
      toast.error("Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Nome é obrigatório");
      return;
    }

    setSaving(true);
    try {
      await api.put(`/teams/${encodeURIComponent(teamName)}`, {
        name: name.trim(),
        description: description.trim() || undefined,
        members,
      });
      toast.success("Time atualizado com sucesso!");
      router.push(`/teams/${encodeURIComponent(name.trim())}`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Erro ao atualizar time");
    } finally {
      setSaving(false);
    }
  };

  const addMember = (agentName: string) => {
    if (!members.includes(agentName)) {
      setMembers([...members, agentName]);
    }
  };

  const removeMember = (agentName: string) => {
    setMembers(members.filter(m => m !== agentName));
  };

  const moveMember = (index: number, direction: "up" | "down") => {
    const newMembers = [...members];
    const newIndex = direction === "up" ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= members.length) return;
    [newMembers[index], newMembers[newIndex]] = [newMembers[newIndex], newMembers[index]];
    setMembers(newMembers);
  };

  const availableAgents = agents.filter(a => !members.includes(a.name));

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
      <div className="max-w-3xl mx-auto">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link href={`/teams/${encodeURIComponent(teamName)}`} className="p-2 text-gray-500 hover:text-purple-600 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Voltar">{Icons.back}</Link>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Editar Time</h1>
                <p className="text-gray-500 dark:text-gray-400 text-sm">{teamName}</p>
              </div>
            </div>
            <button
              type="submit"
              disabled={saving}
              className="btn-primary flex items-center gap-2"
            >
              {saving ? Icons.spinner : Icons.save}
              {saving ? "Salvando..." : "Salvar"}
            </button>
          </div>

          {/* Basic Info */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Informações Básicas</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Nome do Time *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Ex: Time de Análise"
                  className="input-modern"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Descrição
                </label>
                <textarea
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Descreva o propósito do time..."
                  className="input-modern min-h-[80px] resize-none"
                  rows={3}
                />
              </div>
            </div>
          </div>

          {/* Members */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900 dark:text-white">Membros do Time</h3>
              <span className="text-sm text-gray-500">{members.length} membro(s)</span>
            </div>

            {/* Current Members */}
            <div className="space-y-2 mb-4">
              {members.length === 0 ? (
                <p className="text-gray-500 text-center py-4">Nenhum membro adicionado</p>
              ) : (
                members.map((member, index) => (
                  <div key={member} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-slate-700/50 rounded-xl">
                    <div className="flex flex-col gap-1">
                      <button
                        type="button"
                        onClick={() => moveMember(index, "up")}
                        disabled={index === 0}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                        title="Mover para cima"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" /></svg>
                      </button>
                      <button
                        type="button"
                        onClick={() => moveMember(index, "down")}
                        disabled={index === members.length - 1}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                        title="Mover para baixo"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                      </button>
                    </div>
                    <div className="w-8 h-8 rounded-lg bg-purple-500 text-white flex items-center justify-center text-sm font-bold">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white">{member}</p>
                      <p className="text-xs text-gray-500">Agente</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeMember(member)}
                      className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all"
                      title="Remover membro"
                    >
                      {Icons.x}
                    </button>
                  </div>
                ))
              )}
            </div>

            {/* Add Member */}
            {availableAgents.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Adicionar Membro
                </label>
                <div className="flex gap-2">
                  <select
                    className="input-modern flex-1"
                    onChange={e => {
                      if (e.target.value) {
                        addMember(e.target.value);
                        e.target.value = "";
                      }
                    }}
                    defaultValue=""
                    title="Selecionar agente"
                  >
                    <option value="" disabled>Selecione um agente...</option>
                    {availableAgents.map(a => (
                      <option key={a.name} value={a.name}>{a.name} {a.role ? `(${a.role})` : ""}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {availableAgents.length === 0 && members.length > 0 && (
              <p className="text-sm text-gray-500 text-center">Todos os agentes já estão no time</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <Link
              href={`/teams/${encodeURIComponent(teamName)}`}
              className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              Cancelar
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="btn-primary flex items-center gap-2"
            >
              {saving ? Icons.spinner : Icons.save}
              {saving ? "Salvando..." : "Salvar Alterações"}
            </button>
          </div>
        </form>
      </div>
    </Protected>
  );
}
