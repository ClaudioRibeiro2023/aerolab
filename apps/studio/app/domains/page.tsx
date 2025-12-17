"use client";

import Link from "next/link";
import {
  MapPin,
  Database,
  GitBranch,
  DollarSign,
  Scale,
  Building2,
  ArrowRight,
} from "lucide-react";
import { PageHeader } from "../../components/PageHeader";
import { PageSection } from "../../components/PageSection";
import { Badge } from "../../components/Badge";

const domains = [
  {
    id: 'geo',
    name: 'Geolocalização',
    description: 'Análise espacial, mapas e rotas',
    icon: MapPin,
    gradient: 'from-green-500 to-emerald-600',
    features: ['Geocoding', 'Rotas', 'Isócronas', 'IBGE'],
  },
  {
    id: 'data',
    name: 'Dados & Analytics',
    description: 'SQL, analytics e visualização',
    icon: Database,
    gradient: 'from-blue-500 to-cyan-600',
    features: ['SQL Query', 'DuckDB', 'Agregações', 'Export'],
  },
  {
    id: 'devops',
    name: 'DevOps',
    description: 'GitHub, Netlify, Supabase',
    icon: GitBranch,
    gradient: 'from-purple-500 to-indigo-600',
    features: ['Repos', 'Issues', 'Deploy', 'Database'],
  },
  {
    id: 'finance',
    name: 'Financeiro',
    description: 'Mercado, análise e risco',
    icon: DollarSign,
    gradient: 'from-yellow-500 to-orange-600',
    features: ['Cotações', 'Histórico', 'DCF', 'Risco'],
  },
  {
    id: 'legal',
    name: 'Jurídico',
    description: 'Contratos e compliance',
    icon: Scale,
    gradient: 'from-red-500 to-rose-600',
    features: ['Legislação', 'Jurisprudência', 'Análise'],
  },
  {
    id: 'corporate',
    name: 'Corporativo',
    description: 'Estratégia e análise',
    icon: Building2,
    gradient: 'from-slate-500 to-gray-600',
    features: ['SWOT', 'Porter', 'PESTEL'],
  },
];

export default function DomainsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Domínios Especializados"
        subtitle="Selecione um domínio para acessar ferramentas e agentes especializados"
      />

      <PageSection title="Domínios">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {domains.map((domain) => {
            const Icon = domain.icon;
            return (
              <Link
                key={domain.id}
                href={`/domains/${domain.id}`}
                className="group bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
              >
                <div className="flex items-start gap-4">
                  <div className={`bg-gradient-to-br ${domain.gradient} p-3 rounded-xl text-white shadow-lg`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 flex items-center gap-2 transition-colors">
                      {domain.name}
                      <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-all transform group-hover:translate-x-1" />
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{domain.description}</p>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100 dark:border-slate-700 flex flex-wrap gap-2">
                  {domain.features.map((feature) => (
                    <Badge key={feature} variant="neutral" className="text-[11px]">
                      {feature}
                    </Badge>
                  ))}
                </div>
              </Link>
            );
          })}
        </div>
      </PageSection>
    </div>
  );
}
