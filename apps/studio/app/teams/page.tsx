"use client";

import React, { useState, useEffect } from "react";
import Protected from "../../components/Protected";
import api from "../../lib/api";
import { toast } from "sonner";
import { useAuth } from "../../store/auth";
import { getFavoriteTeams, toggleFavoriteTeam } from "../../lib/favorites";
import { PageHeader } from "../../components/PageHeader";
import { CardListSkeleton } from "../../components/CardListSkeleton";
import EmptyState from "../../components/EmptyState";

// Icons
const Icons = {
  team: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
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
  user: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  ),
  x: (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  play: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
    </svg>
  ),
  clone: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
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
  spinner: (
    <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  ),
};

type AgentItem = { name: string; role?: string };
type TeamItem = { name: string; members: string[]; description?: string };

export default function TeamsPage() {
  const { role } = useAuth();
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [teams, setTeams] = useState<TeamItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [expandedTeam, setExpandedTeam] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [favorites, setFavorites] = useState<string[]>([]);
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [sortBy, setSortBy] = useState<"name" | "members">("name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(9);

  const [teamName, setTeamName] = useState("");
  const [teamDesc, setTeamDesc] = useState("");
  const [teamMembers, setTeamMembers] = useState<string[]>([]);

  // Filtrar e ordenar times
  const filteredTeams = teams
    .filter(t =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      (t.description || "").toLowerCase().includes(search.toLowerCase()) ||
      t.members.some(m => m.toLowerCase().includes(search.toLowerCase()))
    )
    .filter(t => !showFavoritesOnly || favorites.includes(t.name))
    .sort((a, b) => {
      const aFav = favorites.includes(a.name);
      const bFav = favorites.includes(b.name);
      if (aFav && !bFav) return -1;
      if (!aFav && bFav) return 1;
      
      let cmp = 0;
      if (sortBy === "name") {
        cmp = a.name.localeCompare(b.name);
      } else if (sortBy === "members") {
        cmp = a.members.length - b.members.length;
      }
      return sortOrder === "asc" ? cmp : -cmp;
    });

  // Paginação
  const totalPages = Math.ceil(filteredTeams.length / itemsPerPage);
  const paginatedTeams = filteredTeams.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Reset página ao mudar filtros
  useEffect(() => {
    setCurrentPage(1);
  }, [search, showFavoritesOnly, sortBy, sortOrder]);

  const handleToggleFavorite = (name: string) => {
    toggleFavoriteTeam(name);
    setFavorites(getFavoriteTeams());
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [ag, tm] = await Promise.all([api.get("/agents"), api.get("/teams")]);
      setAgents(Array.isArray(ag.data) ? ag.data : []);
      const teamsData = Array.isArray(tm.data) ? tm.data : [];
      // Garantir que members seja sempre um array
      setTeams(teamsData.map((t: TeamItem) => ({
        ...t,
        members: Array.isArray(t.members) ? t.members : []
      })));
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    setFavorites(getFavoriteTeams());
  }, []);

  const onCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post("/teams", {
        name: teamName,
        members: teamMembers,
        description: teamDesc || undefined,
      });
      setTeamName("");
      setTeamDesc("");
      setTeamMembers([]);
      setShowCreateModal(false);
      await loadData();
      toast.success("Time criado com sucesso!");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Erro ao criar time");
    } finally {
      setCreating(false);
    }
  };

  const onDeleteTeam = async (name: string) => {
    if (!confirm(`Excluir time "${name}"?`)) return;
    try {
      await api.delete(`/teams/${encodeURIComponent(name)}`);
      await loadData();
      toast.success("Time excluído");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Erro ao deletar time");
    }
  };

  const onAddMember = async (teamName: string, agentName: string) => {
    try {
      await api.post(`/teams/${encodeURIComponent(teamName)}/members`, { agent: agentName });
      await loadData();
      toast.success("Membro adicionado");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Erro ao adicionar membro");
    }
  };

  const onRemoveMember = async (team: string, agent: string) => {
    try {
      await api.delete(`/teams/${encodeURIComponent(team)}/members/${encodeURIComponent(agent)}`);
      await loadData();
      toast.success("Membro removido");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Erro ao remover membro");
    }
  };

  const onCloneTeam = async (team: TeamItem) => {
    const newName = prompt(`Nome do novo time (clone de "${team.name}"):`, `${team.name} - Cópia`);
    if (!newName?.trim()) return;

    try {
      await api.post("/teams", {
        name: newName.trim(),
        members: team.members,
        description: team.description ? `${team.description} (cópia)` : undefined,
      });
      await loadData();
      toast.success("Time clonado com sucesso!");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Erro ao clonar time");
    }
  };

  const toggleMember = (name: string) => {
    setTeamMembers((prev) => (prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]));
  };

  const getAvailableAgents = (team: TeamItem) => {
    return agents.filter((a) => !team.members.includes(a.name));
  };

  return (
    <Protected>
      <div className="space-y-6">
        <PageHeader
          title="Times"
          subtitle={
            loading
              ? "Carregando..."
              : `${filteredTeams.length} de ${teams.length} time${teams.length !== 1 ? "s" : ""}`
          }
          rightActions={
            <div className="flex items-center gap-3">
              {/* Ordenação */}
              <div className="flex items-center gap-1 bg-gray-100 dark:bg-slate-800 rounded-lg p-1">
                <select
                  value={sortBy}
                  onChange={e => setSortBy(e.target.value as "name" | "members")}
                  className="bg-transparent text-sm text-gray-600 dark:text-gray-300 border-none focus:outline-none cursor-pointer"
                  title="Ordenar por"
                >
                  <option value="name">Nome</option>
                  <option value="members">Membros</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
                  className="p-1 text-gray-500 hover:text-purple-500 transition-colors"
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
              {/* Search */}
              <div className="relative">
                <input
                  type="text"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Buscar times..."
                  className="pl-9 pr-4 py-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 w-48"
                />
                <svg className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              {role === "admin" && (
                <a
                  href="/teams/new"
                  className="btn-primary flex items-center gap-2"
                >
                  {Icons.plus}
                  Novo Time
                </a>
              )}
            </div>
          }
        />

        {/* Teams Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {loading ? (
            <CardListSkeleton count={3} />
          ) : filteredTeams.length === 0 ? (
            <div className="md:col-span-2 lg:col-span-3">
              <EmptyState
                icon={search ? "🔍" : "👥"}
                title={search ? "Nenhum time encontrado" : "Nenhum time ainda"}
                description={
                  search
                    ? `Nenhum time encontrado para "${search}". Tente ajustar o termo de busca.`
                    : "Crie seu primeiro time para organizar agentes."
                }
                action={
                  !search && role === "admin"
                    ? { label: "Criar Time", href: "/teams/new" }
                    : undefined
                }
                secondaryAction={
                  search
                    ? {
                        label: "Limpar busca",
                        onClick: () => setSearch(""),
                      }
                    : undefined
                }
              />
            </div>
          ) : (
            paginatedTeams.map((team) => (
              <div
                key={team.name}
                className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 hover:shadow-lg transition-all duration-200 overflow-hidden"
              >
                {/* Team Header */}
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white shadow-lg">
                        {Icons.team}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <a href={`/teams/${encodeURIComponent(team.name)}`} className="font-semibold text-gray-900 dark:text-white hover:text-purple-600 dark:hover:text-purple-400 transition-colors">
                            {team.name}
                          </a>
                          <button
                            onClick={() => handleToggleFavorite(team.name)}
                            className={`p-1 rounded transition-all ${
                              favorites.includes(team.name)
                                ? "text-yellow-500"
                                : "text-gray-300 hover:text-yellow-500"
                            }`}
                            title={favorites.includes(team.name) ? "Remover favorito" : "Adicionar favorito"}
                          >
                            {favorites.includes(team.name) ? Icons.starFilled : Icons.star}
                          </button>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          {team.members.length} membro{team.members.length !== 1 ? "s" : ""}
                        </p>
                      </div>
                    </div>
                    {role === "admin" && (
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => onCloneTeam(team)}
                          className="p-2 text-gray-400 hover:text-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded-lg transition-all"
                          title="Clonar time"
                          aria-label="Clonar time"
                        >
                          {Icons.clone}
                        </button>
                        <button
                          onClick={() => onDeleteTeam(team.name)}
                          className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-all"
                          title="Excluir time"
                          aria-label="Excluir time"
                        >
                          {Icons.trash}
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Members */}
                  <div className="mt-4 pt-4 border-t border-gray-100 dark:border-slate-700">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Membros:</p>
                    <div className="flex flex-wrap gap-2">
                      {team.members.length === 0 ? (
                        <span className="text-sm text-gray-400">Nenhum membro</span>
                      ) : (
                        team.members.map((member) => (
                          <span
                            key={member}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400"
                          >
                            {Icons.user}
                            {member}
                            {role === "admin" && (
                              <button
                                onClick={() => onRemoveMember(team.name, member)}
                                className="ml-1 hover:text-red-500"
                                title="Remover membro"
                                aria-label={`Remover ${member}`}
                              >
                                {Icons.x}
                              </button>
                            )}
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                {team.members.length > 0 && (
                  <div className="px-6 pb-4">
                    <a
                      href={`/teams/${encodeURIComponent(team.name)}/run`}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors text-sm font-medium"
                    >
                      {Icons.play} Executar Time
                    </a>
                  </div>
                )}

                {/* Add Member */}
                {role === "admin" && getAvailableAgents(team).length > 0 && (
                  <div className="px-6 pb-4">
                    <div className="flex gap-2">
                      <select
                        className="input-modern flex-1 text-sm"
                        onChange={(e) => {
                          if (e.target.value) {
                            onAddMember(team.name, e.target.value);
                            e.target.value = "";
                          }
                        }}
                        defaultValue=""
                        title="Adicionar membro"
                      >
                        <option value="" disabled>+ Adicionar membro</option>
                        {getAvailableAgents(team).map((a) => (
                          <option key={a.name} value={a.name}>{a.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Paginação */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-100 dark:border-slate-700">
            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
              <span>Mostrando {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, filteredTeams.length)} de {filteredTeams.length}</span>
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

        {/* Create Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl animate-scale-in">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Criar Novo Time</h2>
              <form onSubmit={onCreateTeam} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Nome do Time
                  </label>
                  <input
                    type="text"
                    value={teamName}
                    onChange={(e) => setTeamName(e.target.value)}
                    placeholder="Ex: Equipe de Análise"
                    className="input-modern"
                    required
                    autoFocus
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Descrição (opcional)
                  </label>
                  <input
                    type="text"
                    value={teamDesc}
                    onChange={(e) => setTeamDesc(e.target.value)}
                    placeholder="Ex: Time especializado em análise de dados"
                    className="input-modern"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Membros Iniciais
                  </label>
                  <div className="max-h-40 overflow-auto border border-gray-200 dark:border-slate-700 rounded-xl p-3 space-y-2">
                    {agents.length === 0 ? (
                      <p className="text-sm text-gray-400">Nenhum agente disponível</p>
                    ) : (
                      agents.map((a) => (
                        <label
                          key={a.name}
                          className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700 cursor-pointer transition-colors"
                        >
                          <input
                            type="checkbox"
                            checked={teamMembers.includes(a.name)}
                            onChange={() => toggleMember(a.name)}
                            className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm text-gray-700 dark:text-gray-300">{a.name}</span>
                          {a.role && (
                            <span className="text-xs text-gray-400">({a.role})</span>
                          )}
                        </label>
                      ))
                    )}
                  </div>
                  {teamMembers.length > 0 && (
                    <p className="mt-2 text-xs text-gray-500">{teamMembers.length} selecionado(s)</p>
                  )}
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="btn-secondary flex-1"
                  >
                    Cancelar
                  </button>
                  <button type="submit" disabled={creating} className="btn-primary flex-1 flex items-center justify-center gap-2">
                    {creating && Icons.spinner}
                    {creating ? "Criando..." : "Criar Time"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Protected>
  );
}
