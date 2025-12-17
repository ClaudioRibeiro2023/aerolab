"use client";

import { useState } from "react";
import { MapPin, Search, Route, Clock, Map } from "lucide-react";
import { PageHeader } from "../../../components/PageHeader";
import { PageSection } from "../../../components/PageSection";

export default function GeoDashboard() {
  const [activeTab, setActiveTab] = useState('geocode');
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const tabs = [
    { id: 'geocode', label: 'Geocoding', icon: Search },
    { id: 'ibge', label: 'IBGE', icon: Map },
    { id: 'route', label: 'Rotas', icon: Route },
    { id: 'isochrone', label: 'Isócronas', icon: Clock },
  ];

  const handleSearch = async () => {
    setLoading(true);
    try {
      // Simular chamada à API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (activeTab === 'ibge') {
        const res = await fetch('https://servicodados.ibge.gov.br/api/v1/localidades/estados');
        const data = await res.json();
        setResult({ type: 'estados', data: data.slice(0, 10) });
      } else {
        setResult({ 
          type: activeTab,
          message: `Resultado para: ${query}`,
          lat: -23.5505,
          lon: -46.6333,
        });
      }
    } catch (error) {
      setResult({ error: 'Erro na busca' });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Geolocalização"
        subtitle="Análise espacial, mapas e rotas"
        leadingAction={
          <div className="bg-green-500 p-3 rounded-xl text-white shadow-lg">
            <MapPin className="w-6 h-6" />
          </div>
        }
        breadcrumbs={[
          { label: "Domínios", href: "/domains" },
          { label: "Geolocalização" },
        ]}
      />

      <PageSection title="Ferramentas de geolocalização">
        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-gray-200">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? "border-green-500 text-green-600"
                    : "border-transparent text-gray-600 hover:text-gray-900"
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Search & Result */}
        <div className="space-y-4">
          <div className="flex gap-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={activeTab === "ibge" ? "Buscar estado ou município..." : "Digite um endereço..."}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
            >
              {loading ? "Buscando..." : "Buscar"}
            </button>
          </div>

          {result && (
            <div className="mt-2">
              <h3 className="text-lg font-semibold mb-4">Resultados</h3>
              <pre className="bg-gray-100 p-4 rounded-lg overflow-auto text-sm">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </PageSection>
    </div>
  );
}
