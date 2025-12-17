"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import Protected from "../../components/Protected";
import api from "../../lib/api";
import { PageHeader } from "../../components/PageHeader";
import {
  Search,
  FileText,
  AlertTriangle,
  TrendingUp,
  Calendar,
  MapPin,
  DollarSign,
  Clock,
  RefreshCw,
  Filter,
  ChevronRight,
  Building2,
  Target,
  Loader2,
} from "lucide-react";

interface LicitacaoItem {
  external_id: string;
  source: string;
  objeto: string;
  orgao: string;
  uf: string;
  valor_estimado: number | null;
  data_abertura: string | null;
  modalidade: string;
  situacao: string;
}

interface TriageScore {
  licitacao_id: string;
  score: number;
  prioridade: string;
  motivos: string[];
}

interface DigestData {
  date: string;
  total_items: number;
  p0_count: number;
  p1_count: number;
  items: LicitacaoItem[];
  scores: TriageScore[];
}

function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    P0: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
    P1: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
    P2: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
    P3: "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300",
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${colors[priority] || colors.P3}`}>
      {priority}
    </span>
  );
}

function StatCard({
  title,
  value,
  icon,
  color = "blue",
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
}) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
    red: "bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400",
    orange: "bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400",
    green: "bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400",
  };
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-slate-700">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colors[color]}`}>{icon}</div>
        <div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
        </div>
      </div>
    </div>
  );
}

function LicitacaoCard({
  item,
  score,
}: {
  item: LicitacaoItem;
  score?: TriageScore;
}) {
  const formatCurrency = (value: number | null) => {
    if (!value) return "Não informado";
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Não informado";
    return new Date(dateStr).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-slate-700 hover:shadow-md transition-all">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            {score && <PriorityBadge priority={score.prioridade} />}
            <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">
              {item.modalidade}
            </span>
          </div>
          <h3 className="font-medium text-gray-900 dark:text-white line-clamp-2 mb-2">
            {item.objeto}
          </h3>
          <div className="flex flex-wrap gap-3 text-sm text-gray-500 dark:text-gray-400">
            <span className="flex items-center gap-1">
              <Building2 className="w-4 h-4" />
              {item.orgao}
            </span>
            <span className="flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              {item.uf}
            </span>
            <span className="flex items-center gap-1">
              <DollarSign className="w-4 h-4" />
              {formatCurrency(item.valor_estimado)}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              {formatDate(item.data_abertura)}
            </span>
          </div>
          {score && score.motivos.length > 0 && (
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              <span className="font-medium">Motivos:</span> {score.motivos.slice(0, 2).join(", ")}
            </div>
          )}
        </div>
        <Link
          href={`/licitacoes/${item.external_id}`}
          className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline text-sm whitespace-nowrap"
        >
          Ver detalhes
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
}

export default function LicitacoesPage() {
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [digest, setDigest] = useState<DigestData | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<LicitacaoItem[]>([]);
  const [filterUF, setFilterUF] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const loadDigest = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const today = new Date().toISOString().split("T")[0];
      const response = await api.get(`/api/v1/licitacoes/digest/${today}`);
      setDigest(response.data);
    } catch (err: any) {
      console.error("Failed to load digest:", err);
      setError("Falha ao carregar digest. Verifique se o backend está rodando.");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim() || searchQuery.length < 3) return;

    setSearching(true);
    setError(null);
    try {
      const params = new URLSearchParams({ q: searchQuery });
      if (filterUF) params.append("uf", filterUF);

      const response = await api.get(`/api/v1/licitacoes/search?${params}`);
      setSearchResults(response.data.items || []);
    } catch (err: any) {
      console.error("Search failed:", err);
      setError("Falha na busca. Tente novamente.");
    } finally {
      setSearching(false);
    }
  }, [searchQuery, filterUF]);

  const handleAnalyze = useCallback(async () => {
    const licitacaoId = prompt("Digite o ID da licitação para análise:");
    if (!licitacaoId) return;

    try {
      const response = await api.post("/api/v1/licitacoes/analyze", {
        licitacao_id: licitacaoId,
      });
      alert(`Análise iniciada!\nRun ID: ${response.data.run_id}\nStatus: ${response.data.result.status}`);
    } catch (err: any) {
      alert(`Erro na análise: ${err.message}`);
    }
  }, []);

  useEffect(() => {
    loadDigest();
  }, [loadDigest]);

  const displayItems = searchResults.length > 0 ? searchResults : (digest?.items || []);
  const scoreMap = new Map(digest?.scores?.map((s) => [s.licitacao_id, s]) || []);

  return (
    <Protected>
      <div className="min-h-screen bg-gray-50 dark:bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <PageHeader
            title="Licitações"
            description="Monitoramento de licitações públicas - Techdengue"
            icon={<FileText className="w-8 h-8" />}
          />

          {/* Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <StatCard
              title="Total Monitoradas"
              value={digest?.total_items || 0}
              icon={<FileText className="w-5 h-5" />}
              color="blue"
            />
            <StatCard
              title="Prioridade P0"
              value={digest?.p0_count || 0}
              icon={<AlertTriangle className="w-5 h-5" />}
              color="red"
            />
            <StatCard
              title="Prioridade P1"
              value={digest?.p1_count || 0}
              icon={<Target className="w-5 h-5" />}
              color="orange"
            />
            <StatCard
              title="Data do Digest"
              value={digest?.date || "-"}
              icon={<Calendar className="w-5 h-5" />}
              color="green"
            />
          </div>

          {/* Search and Actions */}
          <div className="mt-6 bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-slate-700">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar licitações (min. 3 caracteres)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-200 dark:border-slate-600 bg-gray-50 dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <select
                value={filterUF}
                onChange={(e) => setFilterUF(e.target.value)}
                className="px-4 py-2 rounded-lg border border-gray-200 dark:border-slate-600 bg-gray-50 dark:bg-slate-700 text-gray-900 dark:text-white"
              >
                <option value="">Todas UFs</option>
                <option value="SP">São Paulo</option>
                <option value="RJ">Rio de Janeiro</option>
                <option value="MG">Minas Gerais</option>
                <option value="PR">Paraná</option>
                <option value="SC">Santa Catarina</option>
                <option value="RS">Rio Grande do Sul</option>
                <option value="BA">Bahia</option>
                <option value="PE">Pernambuco</option>
                <option value="CE">Ceará</option>
                <option value="GO">Goiás</option>
                <option value="DF">Distrito Federal</option>
              </select>
              <button
                onClick={handleSearch}
                disabled={searching || searchQuery.length < 3}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Buscar
              </button>
              <button
                onClick={loadDigest}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                Atualizar
              </button>
              <button
                onClick={handleAnalyze}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                <TrendingUp className="w-4 h-4" />
                Analisar
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400">
              {error}
            </div>
          )}

          {/* Results */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {searchResults.length > 0
                  ? `Resultados da busca (${searchResults.length})`
                  : `Licitações do dia (${displayItems.length})`}
              </h2>
              {searchResults.length > 0 && (
                <button
                  onClick={() => setSearchResults([])}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Limpar busca
                </button>
              )}
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              </div>
            ) : displayItems.length === 0 ? (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Nenhuma licitação encontrada</p>
                <p className="text-sm mt-2">Tente ajustar os filtros ou executar o monitoramento</p>
              </div>
            ) : (
              <div className="space-y-4">
                {displayItems.map((item) => (
                  <LicitacaoCard
                    key={item.external_id}
                    item={item}
                    score={scoreMap.get(item.external_id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Protected>
  );
}
