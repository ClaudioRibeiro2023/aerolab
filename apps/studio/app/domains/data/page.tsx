"use client";

import { useState } from "react";
import { Database, Play, Download, Table } from "lucide-react";
import { PageHeader } from "../../../components/PageHeader";
import { PageSection } from "../../../components/PageSection";

export default function DataDashboard() {
  const [query, setQuery] = useState('SELECT * FROM users LIMIT 10');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleExecute = async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setResult({
        columns: ['id', 'name', 'email', 'created_at'],
        rows: [
          [1, 'João Silva', 'joao@example.com', '2024-01-15'],
          [2, 'Maria Santos', 'maria@example.com', '2024-01-16'],
          [3, 'Pedro Oliveira', 'pedro@example.com', '2024-01-17'],
        ],
        count: 3,
        executionTime: '0.023s',
      });
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dados & Analytics"
        subtitle="SQL, analytics e visualização"
        leadingAction={
          <div className="bg-blue-500 p-3 rounded-xl text-white shadow-lg">
            <Database className="w-6 h-6" />
          </div>
        }
        breadcrumbs={[
          { label: "Domínios", href: "/domains" },
          { label: "Dados & Analytics" },
        ]}
      />

      <PageSection title="SQL Editor">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Editor de SQL</h3>
          <div className="flex gap-2">
            <button
              onClick={handleExecute}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              {loading ? "Executando..." : "Executar"}
            </button>
            <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
              <Download className="w-4 h-4" />
              Exportar
            </button>
          </div>
        </div>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full h-32 px-4 py-3 font-mono text-sm bg-gray-900 text-green-400 rounded-lg focus:ring-2 focus:ring-blue-500"
          placeholder="Digite sua query SQL..."
        />
      </PageSection>

      {result && (
        <PageSection title="Resultados">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Table className="w-5 h-5" />
              Resultados
            </h3>
            <span className="text-sm text-gray-500">
              {result.count} linhas • {result.executionTime}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  {result.columns.map((col: string) => (
                    <th key={col} className="px-4 py-2 text-left font-medium text-gray-700 border-b">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.rows.map((row: any[], i: number) => (
                  <tr key={i} className="hover:bg-gray-50">
                    {row.map((cell, j) => (
                      <td key={j} className="px-4 py-2 border-b border-gray-100">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </PageSection>
      )}
    </div>
  );
}
