"use client";

import { useState } from "react";
import { Scale, FileText, Search, BookOpen } from "lucide-react";
import { PageHeader } from "../../../components/PageHeader";
import { PageSection } from "../../../components/PageSection";

export default function LegalDashboard() {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="space-y-6">
      <PageHeader
        title="Jurídico"
        subtitle="Contratos, compliance e legislação"
        leadingAction={
          <div className="bg-red-500 p-3 rounded-xl text-white shadow-lg">
            <Scale className="w-6 h-6" />
          </div>
        }
        breadcrumbs={[
          { label: "Domínios", href: "/domains" },
          { label: "Jurídico" },
        ]}
      />

      <PageSection title="Pesquisa Jurídica">
        <div className="flex gap-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar legislação, jurisprudência..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
          />
          <button className="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600" title="Buscar" aria-label="Buscar">
            <Search className="w-5 h-5" />
          </button>
        </div>
      </PageSection>

      <PageSection title="Acessos rápidos">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <FileText className="w-5 h-5 text-red-500" />
            <h3 className="font-semibold">Análise de Contratos</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Upload de contratos para análise automática de cláusulas e riscos.
          </p>
          <button className="w-full py-2 border border-red-500 text-red-500 rounded-lg hover:bg-red-50">
            Analisar Contrato
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <BookOpen className="w-5 h-5 text-red-500" />
            <h3 className="font-semibold">Legislação</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Acesso a leis, decretos e normas atualizadas.
          </p>
          <button className="w-full py-2 border border-red-500 text-red-500 rounded-lg hover:bg-red-50">
            Consultar
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Scale className="w-5 h-5 text-red-500" />
            <h3 className="font-semibold">Jurisprudência</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Busca em decisões de tribunais superiores.
          </p>
          <button className="w-full py-2 border border-red-500 text-red-500 rounded-lg hover:bg-red-50">
            Pesquisar
          </button>
        </div>
        </div>
      </PageSection>
    </div>
  );
}
