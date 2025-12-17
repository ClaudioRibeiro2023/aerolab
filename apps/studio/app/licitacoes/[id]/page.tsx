"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Protected from "../../../components/Protected";
import api from "../../../lib/api";
import { PageHeader } from "../../../components/PageHeader";
import {
  FileText,
  ArrowLeft,
  Building2,
  MapPin,
  DollarSign,
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ExternalLink,
  Download,
  Loader2,
  Target,
  Shield,
  FileSearch,
  List,
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
  sources: Array<{ source: string; url: string }>;
}

interface RiscoIdentificado {
  tipo: string;
  nivel: string;
  descricao: string;
  evidencia?: string;
}

interface ChecklistItem {
  item: string;
  status: string;
  observacao?: string;
}

interface AnalysisPack {
  licitacao_id: string;
  resumo_executivo: string;
  pontos_atencao: string[];
  riscos: RiscoIdentificado[];
  oportunidades: string[];
  checklist_tecnico: ChecklistItem[];
  checklist_juridico: ChecklistItem[];
  recomendacao: string;
  confianca: number;
  aviso_revisao: string;
}

interface AnalyzeResponse {
  run_id: string;
  licitacao: LicitacaoItem | null;
  analysis: AnalysisPack | null;
  result: {
    status: string;
    errors: string[];
  };
}

function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    P0: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
    P1: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
    P2: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
    P3: "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300",
  };
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${colors[priority] || colors.P3}`}>
      {priority}
    </span>
  );
}

function RiskBadge({ nivel }: { nivel: string }) {
  const colors: Record<string, string> = {
    baixo: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    medio: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
    alto: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
    critico: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[nivel] || colors.medio}`}>
      {nivel.toUpperCase()}
    </span>
  );
}

function ChecklistIcon({ status }: { status: string }) {
  if (status === "ok") return <CheckCircle className="w-4 h-4 text-green-500" />;
  if (status === "nok") return <XCircle className="w-4 h-4 text-red-500" />;
  return <Clock className="w-4 h-4 text-yellow-500" />;
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-slate-700">
      <div className="flex items-center gap-2 mb-4">
        <div className="text-blue-600 dark:text-blue-400">{icon}</div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h2>
      </div>
      {children}
    </div>
  );
}

export default function LicitacaoDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadDetail = useCallback(async () => {
    if (!id) return;

    setLoading(true);
    setError(null);
    try {
      const response = await api.post("/api/v1/licitacoes/analyze", {
        licitacao_id: id,
      });
      setData(response.data);
    } catch (err: any) {
      console.error("Failed to load detail:", err);
      setError("Falha ao carregar detalhes. Verifique o ID e tente novamente.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  const handleReanalyze = async () => {
    setAnalyzing(true);
    await loadDetail();
    setAnalyzing(false);
  };

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

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

  const licitacao = data?.licitacao;
  const analysis = data?.analysis;

  return (
    <Protected>
      <div className="min-h-screen bg-gray-50 dark:bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Back Button */}
          <Link
            href="/licitacoes"
            className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar para lista
          </Link>

          {loading ? (
            <div className="flex items-center justify-center py-24">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : error ? (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
              <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-red-500" />
              <p className="text-red-700 dark:text-red-400">{error}</p>
              <button
                onClick={() => router.push("/licitacoes")}
                className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Voltar
              </button>
            </div>
          ) : !licitacao ? (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-6 text-center">
              <FileSearch className="w-12 h-12 mx-auto mb-4 text-yellow-500" />
              <p className="text-yellow-700 dark:text-yellow-400">Licitação não encontrada</p>
            </div>
          ) : (
            <>
              <PageHeader
                title={`Licitação ${id}`}
                description={licitacao.objeto}
                icon={<FileText className="w-8 h-8" />}
              />

              {/* Main Info */}
              <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column - Basic Info */}
                <div className="lg:col-span-2 space-y-6">
                  <Section title="Informações Básicas" icon={<Building2 className="w-5 h-5" />}>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Órgão</p>
                        <p className="font-medium text-gray-900 dark:text-white">{licitacao.orgao}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">UF</p>
                        <p className="font-medium text-gray-900 dark:text-white">{licitacao.uf}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Modalidade</p>
                        <p className="font-medium text-gray-900 dark:text-white">{licitacao.modalidade}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Situação</p>
                        <p className="font-medium text-gray-900 dark:text-white">{licitacao.situacao}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Valor Estimado</p>
                        <p className="font-medium text-gray-900 dark:text-white">{formatCurrency(licitacao.valor_estimado)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Data de Abertura</p>
                        <p className="font-medium text-gray-900 dark:text-white">{formatDate(licitacao.data_abertura)}</p>
                      </div>
                    </div>
                    {licitacao.sources && licitacao.sources.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-gray-100 dark:border-slate-700">
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Fontes</p>
                        <div className="flex flex-wrap gap-2">
                          {licitacao.sources.map((src, i) => (
                            <a
                              key={i}
                              href={src.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg text-sm hover:bg-blue-100 dark:hover:bg-blue-900/50"
                            >
                              {src.source.toUpperCase()}
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </Section>

                  {analysis && (
                    <>
                      <Section title="Resumo Executivo" icon={<FileText className="w-5 h-5" />}>
                        <div className="prose dark:prose-invert max-w-none">
                          <p className="whitespace-pre-line text-gray-700 dark:text-gray-300">
                            {analysis.resumo_executivo}
                          </p>
                        </div>
                        <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg text-sm text-yellow-700 dark:text-yellow-400">
                          ⚠️ {analysis.aviso_revisao}
                        </div>
                      </Section>

                      {analysis.pontos_atencao.length > 0 && (
                        <Section title="Pontos de Atenção" icon={<AlertTriangle className="w-5 h-5" />}>
                          <ul className="space-y-2">
                            {analysis.pontos_atencao.map((ponto, i) => (
                              <li key={i} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                                <span className="text-yellow-500 mt-1">•</span>
                                {ponto}
                              </li>
                            ))}
                          </ul>
                        </Section>
                      )}

                      {analysis.oportunidades.length > 0 && (
                        <Section title="Oportunidades" icon={<Target className="w-5 h-5" />}>
                          <ul className="space-y-2">
                            {analysis.oportunidades.map((op, i) => (
                              <li key={i} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                                <span className="text-green-500 mt-1">✓</span>
                                {op}
                              </li>
                            ))}
                          </ul>
                        </Section>
                      )}
                    </>
                  )}
                </div>

                {/* Right Column - Analysis & Checklists */}
                <div className="space-y-6">
                  {analysis && (
                    <>
                      <Section title="Recomendação" icon={<CheckCircle className="w-5 h-5" />}>
                        <div className="text-center">
                          <p className={`text-2xl font-bold ${
                            analysis.recomendacao === "participar" ? "text-green-600" :
                            analysis.recomendacao === "descartar" ? "text-red-600" : "text-yellow-600"
                          }`}>
                            {analysis.recomendacao.toUpperCase()}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                            Confiança: {(analysis.confianca * 100).toFixed(0)}%
                          </p>
                        </div>
                      </Section>

                      {analysis.riscos.length > 0 && (
                        <Section title="Riscos Identificados" icon={<Shield className="w-5 h-5" />}>
                          <div className="space-y-3">
                            {analysis.riscos.map((risco, i) => (
                              <div key={i} className="p-3 bg-gray-50 dark:bg-slate-700 rounded-lg">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="font-medium text-gray-900 dark:text-white text-sm">
                                    {risco.tipo}
                                  </span>
                                  <RiskBadge nivel={risco.nivel} />
                                </div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">{risco.descricao}</p>
                              </div>
                            ))}
                          </div>
                        </Section>
                      )}

                      <Section title="Checklist Técnico" icon={<List className="w-5 h-5" />}>
                        <div className="space-y-2">
                          {analysis.checklist_tecnico.slice(0, 5).map((item, i) => (
                            <div key={i} className="flex items-center gap-2">
                              <ChecklistIcon status={item.status} />
                              <span className="text-sm text-gray-700 dark:text-gray-300">{item.item}</span>
                            </div>
                          ))}
                        </div>
                      </Section>
                    </>
                  )}

                  <div className="flex flex-col gap-2">
                    <button
                      onClick={handleReanalyze}
                      disabled={analyzing}
                      className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      {analyzing ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <FileSearch className="w-4 h-4" />
                      )}
                      Reanalisar
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </Protected>
  );
}
