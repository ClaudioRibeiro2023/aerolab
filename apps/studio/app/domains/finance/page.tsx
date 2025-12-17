"use client";

import { useState } from "react";
import { DollarSign, TrendingUp, BarChart3, AlertTriangle } from "lucide-react";
import { PageHeader } from "../../../components/PageHeader";
import { PageSection } from "../../../components/PageSection";

export default function FinanceDashboard() {
  const [symbol, setSymbol] = useState('PETR4.SA');
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleGetQuote = async () => {
    setLoading(true);
    try {
      // Aqui conectaria com a API do backend
      await new Promise(resolve => setTimeout(resolve, 1000));
      setQuote({
        symbol: symbol,
        name: 'PETROBRAS PN',
        price: 35.50,
        change: 0.45,
        changePercent: 1.28,
        volume: 45000000,
        marketCap: '450B',
      });
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Financeiro"
        subtitle="Mercado, análise e risco"
        leadingAction={
          <div className="bg-yellow-500 p-3 rounded-xl text-white shadow-lg">
            <DollarSign className="w-6 h-6" />
          </div>
        }
        breadcrumbs={[
          { label: "Domínios", href: "/domains" },
          { label: "Financeiro" },
        ]}
      />

      <PageSection title="Indicadores rápidos">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-600 mb-2">
            <TrendingUp className="w-4 h-4" />
            <span className="text-sm">IBOV</span>
          </div>
          <p className="text-2xl font-bold">125,430</p>
          <p className="text-sm text-green-500">+1.2%</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-600 mb-2">
            <BarChart3 className="w-4 h-4" />
            <span className="text-sm">Dólar</span>
          </div>
          <p className="text-2xl font-bold">R$ 5.89</p>
          <p className="text-sm text-red-500">-0.3%</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-600 mb-2">
            <DollarSign className="w-4 h-4" />
            <span className="text-sm">Selic</span>
          </div>
          <p className="text-2xl font-bold">11.25%</p>
          <p className="text-sm text-gray-500">a.a.</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-600 mb-2">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-sm">VIX</span>
          </div>
          <p className="text-2xl font-bold">15.2</p>
          <p className="text-sm text-green-500">Baixa vol.</p>
          </div>
        </div>
      </PageSection>

      <PageSection title="Cotação de Ações">
        <div className="flex gap-4 mb-6">
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="Ex: PETR4.SA"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
          />
          <button
            onClick={handleGetQuote}
            disabled={loading}
            className="px-6 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50"
          >
            {loading ? "Buscando..." : "Buscar"}
          </button>
        </div>

        {quote && (
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="text-xl font-bold">{quote.symbol}</h4>
                <p className="text-gray-600">{quote.name}</p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold">R$ {quote.price.toFixed(2)}</p>
                <p className={`text-sm ${quote.change >= 0 ? "text-green-500" : "text-red-500"}`}>
                  {quote.change >= 0 ? "+" : ""}{quote.change.toFixed(2)} ({quote.changePercent.toFixed(2)}%)
                </p>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Volume:</span>
                <span className="ml-2 font-medium">{(quote.volume / 1000000).toFixed(1)}M</span>
              </div>
              <div>
                <span className="text-gray-600">Market Cap:</span>
                <span className="ml-2 font-medium">{quote.marketCap}</span>
              </div>
            </div>
          </div>
        )}
      </PageSection>
    </div>
  );
}
