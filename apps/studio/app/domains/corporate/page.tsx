"use client";

import { useState } from "react";
import { Building2, Target, TrendingUp, Users } from "lucide-react";
import { PageHeader } from "../../../components/PageHeader";
import { PageSection } from "../../../components/PageSection";

type FrameworkId = "swot" | "porter" | "pestel";

export default function CorporateDashboard() {
  const [activeFramework, setActiveFramework] = useState<FrameworkId>("swot");

  const frameworks: { id: FrameworkId; name: string; description: string }[] = [
    { id: "swot", name: "SWOT", description: "Forças, Fraquezas, Oportunidades, Ameaças" },
    { id: "porter", name: "Porter", description: "Cinco Forças Competitivas" },
    { id: "pestel", name: "PESTEL", description: "Análise Macro Ambiental" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Corporativo"
        subtitle="Estratégia e análise empresarial"
        leadingAction={
          <div className="bg-gray-700 p-3 rounded-xl text-white shadow-lg">
            <Building2 className="w-6 h-6" />
          </div>
        }
        breadcrumbs={[
          { label: "Domínios", href: "/domains" },
          { label: "Corporativo" },
        ]}
      />

      <PageSection title="Indicadores">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-2 text-gray-600 mb-2">
              <Target className="w-4 h-4" />
              <span className="text-sm">Projetos Ativos</span>
            </div>
            <p className="text-2xl font-bold">12</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-2 text-gray-600 mb-2">
              <TrendingUp className="w-4 h-4" />
              <span className="text-sm">ROI Médio</span>
            </div>
            <p className="text-2xl font-bold">24.5%</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-2 text-gray-600 mb-2">
              <Users className="w-4 h-4" />
              <span className="text-sm">Equipes</span>
            </div>
            <p className="text-2xl font-bold">8</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-2 text-gray-600 mb-2">
              <Building2 className="w-4 h-4" />
              <span className="text-sm">Unidades</span>
            </div>
            <p className="text-2xl font-bold">3</p>
          </div>
        </div>
      </PageSection>

      <PageSection title="Frameworks Estratégicos">
        <div className="flex gap-2 mb-6">
          {frameworks.map((fw) => (
            <button
              key={fw.id}
              onClick={() => setActiveFramework(fw.id)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeFramework === fw.id
                  ? "bg-gray-700 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {fw.name}
            </button>
          ))}
        </div>

        {activeFramework === "swot" && (
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <h4 className="font-semibold text-green-700 mb-2">Forças</h4>
              <ul className="text-sm text-green-600 space-y-1">
                <li>• Equipe qualificada</li>
                <li>• Tecnologia proprietária</li>
                <li>• Marca reconhecida</li>
              </ul>
            </div>
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <h4 className="font-semibold text-red-700 mb-2">Fraquezas</h4>
              <ul className="text-sm text-red-600 space-y-1">
                <li>• Custos operacionais altos</li>
                <li>• Dependência de fornecedor</li>
              </ul>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-blue-700 mb-2">Oportunidades</h4>
              <ul className="text-sm text-blue-600 space-y-1">
                <li>• Expansão internacional</li>
                <li>• Novos mercados</li>
                <li>• Parcerias estratégicas</li>
              </ul>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <h4 className="font-semibold text-yellow-700 mb-2">Ameaças</h4>
              <ul className="text-sm text-yellow-600 space-y-1">
                <li>• Concorrência crescente</li>
                <li>• Regulamentações</li>
              </ul>
            </div>
          </div>
        )}

        {activeFramework === "porter" && (
          <div className="text-center py-8 text-gray-500">
            Clique para gerar análise das 5 Forças de Porter
          </div>
        )}

        {activeFramework === "pestel" && (
          <div className="text-center py-8 text-gray-500">
            Clique para gerar análise PESTEL
          </div>
        )}
      </PageSection>
    </div>
  );
}
