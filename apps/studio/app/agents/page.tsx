"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import Protected from "../../components/Protected";
import api from "../../lib/api";
import { toast } from "sonner";
import { useAuth } from "../../store/auth";
import { getFavoriteAgents, toggleFavoriteAgent } from "../../lib/favorites";
import { getAgentTags, addAgentTag, removeAgentTag, getAvailableTags, getTagColor } from "../../lib/tags";
import { successWithAction } from "../../lib/toastActions";
import EmptyState from "../../components/EmptyState";
import { CardListSkeleton } from "../../components/CardListSkeleton";
import { trackExecution, estimateExecutionCost } from "../../lib/analytics";
import { PageHeader } from "../../components/PageHeader";
import { PageSection } from "../../components/PageSection";

// Icons
const Icons = {
  robot: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
  plus: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
  ),
  trash: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
  ),
  edit: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  ),
  chat: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  ),
  clone: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  ),
  play: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0110 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  spinner: (
    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  ),
  star: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
    </svg>
  ),
  starFilled: (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
      <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
    </svg>
  ),
  sort: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
    </svg>
  ),
  tag: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
    </svg>
  ),
  x: (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
};

export default function AgentsPage() {
  const { role } = useAuth();
  const [agents, setAgents] = useState<Array<{ id?: string; name: string; role?: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [search, setSearch] = useState("");
  const [favorites, setFavorites] = useState<string[]>([]);
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [sortBy, setSortBy] = useState<"name" | "role">("name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(9);
  const [filterTag, setFilterTag] = useState<string | null>(null);
  const [agentTags, setAgentTags] = useState<Record<string, string[]>>({});
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [showTagMenu, setShowTagMenu] = useState<string | null>(null);
  const [selectedAgents, setSelectedAgents] = useState<Set<string>>(new Set());
  const [bulkMode, setBulkMode] = useState(false);

  const [runName, setRunName] = useState("");
  const [runPrompt, setRunPrompt] = useState("");
  const [runOutput, setRunOutput] = useState<string | null>(null);

  // Filtrar e ordenar agentes
  const filteredAgents = agents
    .filter(a => 
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      (a.role || "").toLowerCase().includes(search.toLowerCase())
    )
    .filter(a => !showFavoritesOnly || favorites.includes(a.name))
    .filter(a => !filterTag || (agentTags[a.name] || []).includes(filterTag))
    .sort((a, b) => {
      // Favoritos primeiro
      const aFav = favorites.includes(a.name);
      const bFav = favorites.includes(b.name);
      if (aFav && !bFav) return -1;
      if (!aFav && bFav) return 1;
      
      // Ordenação selecionada
      let cmp = 0;
      if (sortBy === "name") {
        cmp = a.name.localeCompare(b.name);
      } else if (sortBy === "role") {
        cmp = (a.role || "").localeCompare(b.role || "");
      }
      return sortOrder === "asc" ? cmp : -cmp;
    });

  // Paginação
  const totalPages = Math.ceil(filteredAgents.length / itemsPerPage);
  const paginatedAgents = filteredAgents.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Reset página ao mudar filtros
  useEffect(() => {
    setCurrentPage(1);
  }, [search, showFavoritesOnly, sortBy, sortOrder, filterTag]);

  // Limpar seleção ao mudar de página ou sair do bulk mode
  useEffect(() => {
    setSelectedAgents(new Set());
  }, [currentPage]);

  const handleToggleFavorite = (name: string) => {
    toggleFavoriteAgent(name);
    setFavorites(getFavoriteAgents());
  };

  const loadTags = () => {
    const tags: Record<string, string[]> = {};
    agents.forEach(a => {
      tags[a.name] = getAgentTags(a.name);
    });
    setAgentTags(tags);
    setAvailableTags(getAvailableTags());
  };

  const handleAddTag = (agentName: string, tag: string) => {
    addAgentTag(agentName, tag);
    setAgentTags(prev => ({
      ...prev,
      [agentName]: [...(prev[agentName] || []), tag]
    }));
    setShowTagMenu(null);
  };

  const handleRemoveTag = (agentName: string, tag: string) => {
    removeAgentTag(agentName, tag);
    setAgentTags(prev => ({
      ...prev,
      [agentName]: (prev[agentName] || []).filter(t => t !== tag)
    }));
  };

  interface ApiAgentListItem {
    id?: string;
    name?: string;
    role?: string;
  }

  const loadAgents = async () => {
    setLoading(true);
    try {
      const res = await api.get("/agents");
      const data = (res.data || []) as ApiAgentListItem[];
      const normalized = data.map((a) => ({
        id: a.id || a.name,
        name: a.name || a.id || "",
        role: a.role,
      }));
      setAgents(normalized);
      if (!runName && normalized.length > 0) {
        // Usar name para execução (API é case-sensitive)
        setRunName(normalized[0].name);
      }
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || "Erro ao listar agents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
    setFavorites(getFavoriteAgents());
    setAvailableTags(getAvailableTags());
  }, []);

  useEffect(() => {
    if (agents.length > 0) loadTags();
  }, [agents]);

  const onDelete = async (id: string, displayName: string) => {
    if (!confirm(`Excluir agent "${displayName}"?`)) return;
    try {
      await api.delete(`/agents/${encodeURIComponent(id)}`);
      await loadAgents();
      toast.success("Agent excluído");
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || "Erro ao deletar agent");
    }
  };

  // Bulk Actions
  const toggleSelect = (name: string) => {
    setSelectedAgents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(name)) {
        newSet.delete(name);
      } else {
        newSet.add(name);
      }
      return newSet;
    });
  };

  const selectAll = () => {
    if (selectedAgents.size === paginatedAgents.length) {
      setSelectedAgents(new Set());
    } else {
      setSelectedAgents(new Set(paginatedAgents.map(a => a.name)));
    }
  };

  const bulkDelete = async () => {
    if (selectedAgents.size === 0) return;
    if (!confirm(`Excluir ${selectedAgents.size} agente(s) selecionado(s)?`)) return;
    
    let deleted = 0;
    for (const name of selectedAgents) {
      try {
        const agent = agents.find(a => a.name === name || a.id === name);
        const id = agent?.id || name;
        await api.delete(`/agents/${encodeURIComponent(id)}`);
        deleted++;
      } catch {}
    }
    
    await loadAgents();
    setSelectedAgents(new Set());
    setBulkMode(false);
    toast.success(`${deleted} agente(s) excluído(s)`);
  };

  const bulkAddTag = (tag: string) => {
    const agentsUpdated = Array.from(selectedAgents);
    
    agentsUpdated.forEach(name => {
      addAgentTag(name, tag);
    });
    loadTags();
    
    successWithAction({
      message: `Tag "${tag}" adicionada a ${agentsUpdated.length} agente(s)`,
      actionLabel: "Desfazer",
      onAction: () => {
        agentsUpdated.forEach(name => removeAgentTag(name, tag));
        loadTags();
        toast.info("Ação desfeita");
      },
    });
  };

  const bulkAddToFavorites = () => {
    const added: string[] = [];
    
    selectedAgents.forEach(name => {
      if (!favorites.includes(name)) {
        toggleFavoriteAgent(name);
        added.push(name);
      }
    });
    
    setFavorites(getFavoriteAgents());
    
    successWithAction({
      message: `${added.length} agente(s) adicionado(s) aos favoritos`,
      actionLabel: "Desfazer",
      onAction: () => {
        added.forEach(name => toggleFavoriteAgent(name));
        setFavorites(getFavoriteAgents());
        toast.info("Ação desfeita");
      },
    });
  };

  const onClone = async (id: string, displayName: string) => {
    const newName = prompt(`Nome para o clone de "${displayName}":`, `${displayName} (cópia)`);
    if (!newName || !newName.trim()) return;
    
    try {
      // Buscar dados do agente original
      const original = await api.get(`/agents/${encodeURIComponent(id)}`);
      const data = original.data as {
        role?: string;
        model_provider?: string;
        model_id?: string;
        instructions?: string;
        use_database?: boolean;
        add_history_to_context?: boolean;
        markdown?: string;
        debug_mode?: boolean;
      };

      // Criar clone
      await api.post("/agents", {
        name: newName.trim(),
        role: data.role,
        model_provider: data.model_provider,
        model_id: data.model_id,
        instructions: data.instructions,
        use_database: data.use_database,
        add_history_to_context: data.add_history_to_context,
        markdown: data.markdown,
        debug_mode: data.debug_mode,
      });

      await loadAgents();
      toast.success(`Agente "${newName}" criado com sucesso!`);
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || "Erro ao clonar agente");
    }
  };

  const onRun = async () => {
    if (!runName || !runPrompt) return;
    setRunning(true);
    setRunOutput(null);
    const startTime = Date.now();
    try {
      const res = await api.post(`/agents/${encodeURIComponent(runName)}/run`, { prompt: runPrompt });
      const output = (res.data?.output as string | undefined) ?? "";
      const duration = (Date.now() - startTime) / 1000;
      setRunOutput(output);
      toast.success("Execução concluída");

      // Rastrear execução para analytics
      const tokens = Math.ceil((runPrompt.length + output.length) / 4);
      trackExecution({
        agentName: runName,
        duration,
        tokens,
        cost: estimateExecutionCost(tokens, "groq", "llama-3.3-70b-versatile"),
        success: true,
      });
    } catch (e) {
      const duration = (Date.now() - startTime) / 1000;
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || "Erro ao executar agent");
      
      // Rastrear execução com erro
      trackExecution({
        agentName: runName,
        duration,
        tokens: Math.ceil(runPrompt.length / 4),
        cost: 0,
        success: false,
      });
    } finally {
      setRunning(false);
    }
  };

  return (
    <Protected>
      <div className="space-y-6">
        <PageHeader
          title="Agentes"
          subtitle={
            loading
              ? "Carregando..."
              : `${filteredAgents.length} de ${agents.length} agente${agents.length !== 1 ? "s" : ""}`
          }
          rightActions={
            <div className="flex items-center gap-3">
              {/* Ordenação */}
              <div className="flex items-center gap-1 bg-gray-100 dark:bg-slate-800 rounded-lg p-1">
                <select
                  value={sortBy}
                  onChange={e => setSortBy(e.target.value as "name" | "role")}
                  className="bg-transparent text-sm text-gray-600 dark:text-gray-300 border-none focus:outline-none cursor-pointer"
                  title="Ordenar por"
                >
                  <option value="name">Nome</option>
                  <option value="role">Role</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
                  className="p-1 text-gray-500 hover:text-blue-500 transition-colors"
                  title={sortOrder === "asc" ? "Ordem crescente" : "Ordem decrescente"}
                >
                  <svg className={`w-4 h-4 transition-transform ${sortOrder === "desc" ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                </button>
              </div>
              {/* Filtro Favoritos */}
              <button
                onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
                className={`p-2 rounded-lg transition-all ${
                  showFavoritesOnly 
                    ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600" 
                    : "bg-gray-100 dark:bg-slate-800 text-gray-400 hover:text-yellow-500"
                }`}
                title={showFavoritesOnly ? "Mostrar todos" : "Mostrar favoritos"}
              >
                {showFavoritesOnly ? Icons.starFilled : Icons.star}
              </button>
              {/* Filtro por Tag */}
              <select
                value={filterTag || ""}
                onChange={e => setFilterTag(e.target.value || null)}
                className={`px-3 py-2 rounded-lg text-sm border-none cursor-pointer ${
                  filterTag
                    ? "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400"
                    : "bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-gray-400"
                }`}
                title="Filtrar por tag"
              >
                <option value="">Todas as tags</option>
                {availableTags.map(tag => (
                  <option key={tag} value={tag}>{tag}</option>
                ))}
              </select>
              {/* Search */}
              <div className="relative">
                <input
                  type="text"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Buscar agentes..."
                  className="pl-9 pr-4 py-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-48"
                />
                <svg className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              {role === "admin" && (
                <>
                  <button
                    onClick={() => { setBulkMode(!bulkMode); setSelectedAgents(new Set()); }}
                    className={`p-2 rounded-lg transition-all ${
                      bulkMode 
                        ? "bg-blue-100 dark:bg-blue-900/30 text-blue-600" 
                        : "bg-gray-100 dark:bg-slate-800 text-gray-400 hover:text-blue-500"
                    }`}
                    title={bulkMode ? "Sair do modo seleção" : "Modo seleção múltipla"}
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                    </svg>
                  </button>
                  <Link
                    href="/agents/new"
                    className="btn-primary flex items-center gap-2"
                  >
                    {Icons.plus}
                    Novo Agente
                  </Link>
                </>
              )}
            </div>
          }
        />

        <PageSection
          title="Lista de agentes"
          subtitle={
            loading
              ? "Carregando..."
              : `${filteredAgents.length} de ${agents.length} agente${agents.length !== 1 ? "s" : ""}`
          }
          className="space-y-4"
        >
          {/* Bulk Actions Bar */}
          {bulkMode && (
            <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 border border-blue-200 dark:border-blue-800">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedAgents.size === paginatedAgents.length && paginatedAgents.length > 0}
                    onChange={selectAll}
                    className="rounded border-blue-300"
                    title="Selecionar todos"
                  />
                  {selectedAgents.size === paginatedAgents.length ? "Desmarcar todos" : "Selecionar todos"}
                </label>
                <span className="text-sm text-blue-600 dark:text-blue-400">
                  {selectedAgents.size} selecionado(s)
                </span>
              </div>
              {selectedAgents.size > 0 && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={bulkAddToFavorites}
                    className="px-3 py-1.5 bg-yellow-100 text-yellow-700 rounded-lg text-sm hover:bg-yellow-200 transition-colors"
                  >
                    ⭐ Favoritar
                  </button>
                  <select
                    onChange={e => { if (e.target.value) { bulkAddTag(e.target.value); e.target.value = ""; }}}
                    className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded-lg text-sm border-none cursor-pointer"
                    defaultValue=""
                    title="Adicionar tag"
                  >
                    <option value="" disabled>🏷️ Adicionar tag</option>
                    {availableTags.map(tag => (
                      <option key={tag} value={tag}>{tag}</option>
                    ))}
                  </select>
                  <button
                    onClick={bulkDelete}
                    className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg text-sm hover:bg-red-200 transition-colors"
                  >
                    🗑️ Excluir
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Agents Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {loading ? (
              <CardListSkeleton count={3} />
            ) : paginatedAgents.length === 0 ? (
              // Empty state
              <div className="md:col-span-2 lg:col-span-3">
                <EmptyState
                  icon="🤖"
                  title={search ? "Nenhum resultado" : "Nenhum agente ainda"}
                  description={search ? `Nenhum agente encontrado para "${search}"` : "Crie seu primeiro agente em menos de 5 minutos usando nossos templates prontos!"}
                  action={role === "admin" ? {
                    label: "✨ Criar Primeiro Agente",
                    href: "/agents/new"
                  } : undefined}
                  secondaryAction={search ? {
                    label: "Limpar Busca",
                    onClick: () => setSearch("")
                  } : {
                    label: "📚 Ver Tutorial",
                    href: "/help"
                  }}
                  suggestions={[
                    "Use um template pronto para começar rápido",
                    "Explore os 15 templates especializados por categoria",
                    "Configure instruções personalizadas para seu caso de uso"
                  ]}
                />
              </div>
            ) : (
              // Agent cards
              paginatedAgents.map((agent) => (
                <div
                  key={agent.name}
                  className={`bg-white dark:bg-slate-800 rounded-2xl p-6 border hover:shadow-lg transition-all duration-200 group ${
                    selectedAgents.has(agent.name) 
                      ? "border-blue-400 dark:border-blue-600 ring-2 ring-blue-200 dark:ring-blue-800" 
                      : "border-gray-100 dark:border-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      {bulkMode && (
                        <label className="flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selectedAgents.has(agent.name)}
                            onChange={() => toggleSelect(agent.name)}
                            className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            title={`Selecionar ${agent.name}`}
                          />
                        </label>
                      )}
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-lg">
                        {Icons.robot}
                      </div>
                      <div>
                        <a href={`/agents/${encodeURIComponent(agent.id || agent.name)}`} className="font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                          {agent.name}
                        </a>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          {agent.role || "Agente genérico"}
                        </p>
                        {/* Tags */}
                        <div className="flex flex-wrap gap-1 mt-2">
                          {(agentTags[agent.name] || []).map(tag => (
                            <span
                              key={tag}
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${getTagColor(tag)}`}
                            >
                              {tag}
                              <button
                                onClick={() => handleRemoveTag(agent.name, tag)}
                                className="hover:bg-black/10 rounded-full"
                                title="Remover tag"
                              >
                                {Icons.x}
                              </button>
                            </span>
                          ))}
                          <div className="relative">
                            <button
                              onClick={() => setShowTagMenu(showTagMenu === agent.name ? null : agent.name)}
                              className="p-1 text-gray-400 hover:text-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded transition-all"
                              title="Adicionar tag"
                            >
                              {Icons.tag}
                            </button>
                            {showTagMenu === agent.name && (
                              <div className="absolute left-0 top-full mt-1 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700 py-1 z-10 min-w-[120px]">
                                {availableTags
                                  .filter(t => !(agentTags[agent.name] || []).includes(t))
                                  .map(tag => (
                                    <button
                                      key={tag}
                                      onClick={() => handleAddTag(agent.name, tag)}
                                      className="w-full text-left px-3 py-1.5 text-sm hover:bg-gray-100 dark:hover:bg-slate-700"
                                    >
                                      {tag}
                                    </button>
                                  ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                    {role === "admin" && (
                      <button
                        onClick={() => onDelete(agent.id || agent.name, agent.name)}
                        className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                        title="Excluir agente"
                        aria-label="Excluir agente"
                      >
                        {Icons.trash}
                      </button>
                    )}
                  </div>
                  <div className="mt-4 pt-4 border-t border-gray-100 dark:border-slate-700 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggleFavorite(agent.name)}
                        className={`p-1.5 rounded-lg transition-all ${
                          favorites.includes(agent.name)
                            ? "text-yellow-500"
                            : "text-gray-300 hover:text-yellow-500"
                        }`}
                        title={favorites.includes(agent.name) ? "Remover favorito" : "Adicionar favorito"}
                      >
                        {favorites.includes(agent.name) ? Icons.starFilled : Icons.star}
                      </button>
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                        Ativo
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <a
                        href={`/agents/${encodeURIComponent(agent.id || agent.name)}/edit`}
                        className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded-lg transition-all"
                        title="Editar"
                      >
                        {Icons.edit}
                      </a>
                      <button
                        onClick={() => onClone(agent.id || agent.name, agent.name)}
                        className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-lg transition-all"
                        title="Clonar agente"
                      >
                        {Icons.clone}
                      </button>
                      <a
                        href={`/chat?agent=${encodeURIComponent(agent.name)}`}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-all"
                        title="Conversar"
                      >
                        {Icons.chat}
                      </a>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Paginação */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-100 dark:border-slate-700">
              <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                <span>Mostrando {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, filteredAgents.length)} de {filteredAgents.length}</span>
                <select
                  value={itemsPerPage}
                  onChange={e => { setItemsPerPage(Number(e.target.value)); setCurrentPage(1); }}
                  className="bg-gray-100 dark:bg-slate-700 rounded px-2 py-1 text-sm border-none"
                  title="Itens por página"
                >
                  <option value={6}>6</option>
                  <option value={9}>9</option>
                  <option value={12}>12</option>
                  <option value={24}>24</option>
                </select>
                <span>por página</span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Primeira página"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" /></svg>
                </button>
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Página anterior"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
                </button>
                <span className="px-3 py-1 text-sm font-medium">{currentPage} / {totalPages}</span>
                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Próxima página"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                </button>
                <button
                  onClick={() => setCurrentPage(totalPages)}
                  disabled={currentPage === totalPages}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Última página"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" /></svg>
                </button>
              </div>
            </div>
          )}
        </PageSection>

        {/* Run Agent Section */}
        {agents.length > 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              {Icons.play}
              Executar Agente
            </h2>
            <div className="grid gap-4 md:grid-cols-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Agente
                </label>
                <select
                  value={runName}
                  onChange={(e) => setRunName(e.target.value)}
                  className="input-modern"
                  title="Selecionar agente"
                >
                  {agents.map((a) => (
                    <option key={a.id || a.name} value={a.name}>{a.name}</option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Prompt
                </label>
                <input
                  type="text"
                  value={runPrompt}
                  onChange={(e) => setRunPrompt(e.target.value)}
                  placeholder="Digite sua mensagem..."
                  className="input-modern"
                  onKeyDown={(e) => e.key === "Enter" && onRun()}
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={onRun}
                  disabled={running || !runName || !runPrompt}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  {running ? Icons.spinner : Icons.play}
                  {running ? "Executando..." : "Executar"}
                </button>
              </div>
            </div>
            {runOutput !== null && (
              <div className="mt-4 p-4 bg-gray-50 dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-700">
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Resposta:</p>
                <pre className="text-sm whitespace-pre-wrap text-gray-800 dark:text-gray-200">{runOutput}</pre>
              </div>
            )}
          </div>
        )}

      </div>
    </Protected>
  );
}
