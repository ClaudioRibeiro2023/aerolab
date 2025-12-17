"use client";
import React, { useState, useCallback } from "react";
import Protected from "../../../components/Protected";
import Link from "next/link";
import { toast } from "sonner";

interface AgentNode {
  id: string;
  name: string;
  type: "agent" | "router" | "combiner";
  position: { x: number; y: number };
  config: {
    agentId?: string;
    strategy?: string;
    description?: string;
  };
}

interface Connection {
  id: string;
  from: string;
  to: string;
  label?: string;
}

type CombinationStrategy = "voting" | "weighted" | "chain" | "parallel" | "fallback" | "consensus";

const Icons = {
  back: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>),
  plus: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>),
  trash: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>),
  save: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>),
  play: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /></svg>),
};

const strategies: { id: CombinationStrategy; name: string; description: string; icon: string }[] = [
  { id: "chain", name: "Cadeia", description: "Executa agentes em sequência", icon: "🔗" },
  { id: "parallel", name: "Paralelo", description: "Executa agentes simultaneamente", icon: "⚡" },
  { id: "voting", name: "Votação", description: "Combina por maioria", icon: "🗳️" },
  { id: "weighted", name: "Ponderado", description: "Combina por pesos", icon: "⚖️" },
  { id: "fallback", name: "Fallback", description: "Usa próximo se falhar", icon: "🔄" },
  { id: "consensus", name: "Consenso", description: "Requer acordo entre agentes", icon: "🤝" },
];

const availableAgents = [
  { id: "researcher", name: "Pesquisador", icon: "🔍" },
  { id: "writer", name: "Escritor", icon: "✍️" },
  { id: "reviewer", name: "Revisor", icon: "📝" },
  { id: "analyst", name: "Analista", icon: "📊" },
  { id: "coder", name: "Programador", icon: "💻" },
];

function NodeCard({ node, isSelected, onSelect, onDelete }: {
  node: AgentNode;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  const bgColor = node.type === "agent" 
    ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
    : node.type === "router"
    ? "bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800"
    : "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800";

  return (
    <div 
      onClick={onSelect}
      className={`relative p-4 rounded-xl border-2 cursor-pointer transition-all ${bgColor} ${
        isSelected ? "ring-2 ring-blue-500 ring-offset-2" : ""
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">
            {node.type === "agent" ? "🤖" : node.type === "router" ? "🔀" : "🔄"}
          </span>
          <div>
            <p className="font-medium text-gray-900 dark:text-white">{node.name}</p>
            <p className="text-xs text-gray-500 capitalize">{node.type}</p>
          </div>
        </div>
        <button 
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          className="p-1 text-gray-400 hover:text-red-500 transition-colors"
          title="Remover"
        >
          {Icons.trash}
        </button>
      </div>
      {node.config.strategy && (
        <div className="mt-2 text-xs text-gray-500">
          Estratégia: {strategies.find(s => s.id === node.config.strategy)?.name}
        </div>
      )}
    </div>
  );
}

export default function MultiAgentBuilderPage() {
  const [teamName, setTeamName] = useState("Novo Time de Agentes");
  const [nodes, setNodes] = useState<AgentNode[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [strategy, setStrategy] = useState<CombinationStrategy>("chain");

  const addAgent = (agentId: string) => {
    const agent = availableAgents.find(a => a.id === agentId);
    if (!agent) return;

    const newNode: AgentNode = {
      id: `node_${Date.now()}`,
      name: agent.name,
      type: "agent",
      position: { x: nodes.length * 120, y: 100 },
      config: { agentId: agent.id }
    };
    setNodes([...nodes, newNode]);
  };

  const removeNode = (nodeId: string) => {
    setNodes(nodes.filter(n => n.id !== nodeId));
    setConnections(connections.filter(c => c.from !== nodeId && c.to !== nodeId));
    if (selectedNode === nodeId) setSelectedNode(null);
  };

  const connectNodes = (fromId: string, toId: string) => {
    if (fromId === toId) return;
    const exists = connections.some(c => c.from === fromId && c.to === toId);
    if (exists) return;

    setConnections([...connections, {
      id: `conn_${Date.now()}`,
      from: fromId,
      to: toId
    }]);
  };

  const handleSave = async () => {
    if (nodes.length < 2) {
      toast.error("Adicione pelo menos 2 agentes ao time");
      return;
    }

    try {
      // Salvar time (simular)
      await new Promise(r => setTimeout(r, 500));
      toast.success("Time salvo com sucesso!");
    } catch (e) {
      toast.error("Erro ao salvar time");
    }
  };

  const handleTest = async () => {
    if (nodes.length < 1) {
      toast.error("Adicione pelo menos 1 agente");
      return;
    }
    toast.info("Funcionalidade de teste em desenvolvimento");
  };

  return (
    <Protected>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/teams" className="p-2 text-gray-500 hover:text-blue-600 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Voltar">
              {Icons.back}
            </Link>
            <div>
              <input
                type="text"
                value={teamName}
                onChange={e => setTeamName(e.target.value)}
                className="text-2xl font-bold text-gray-900 dark:text-white bg-transparent border-none focus:outline-none focus:ring-0"
                placeholder="Nome do Time"
              />
              <p className="text-gray-500 dark:text-gray-400 text-sm">Multi-Agent Builder</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button onClick={handleTest} className="btn-secondary flex items-center gap-2">
              {Icons.play} Testar
            </button>
            <button onClick={handleSave} className="btn-primary flex items-center gap-2">
              {Icons.save} Salvar
            </button>
          </div>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar - Agent Palette */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-gray-100 dark:border-slate-700">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Agentes Disponíveis</h3>
              <div className="space-y-2">
                {availableAgents.map(agent => (
                  <button
                    key={agent.id}
                    onClick={() => addAgent(agent.id)}
                    className="w-full p-3 rounded-xl border border-gray-200 dark:border-slate-600 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all text-left flex items-center gap-2"
                  >
                    <span className="text-xl">{agent.icon}</span>
                    <span className="font-medium text-gray-900 dark:text-white">{agent.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Strategy Selector */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-gray-100 dark:border-slate-700">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Estratégia de Combinação</h3>
              <div className="space-y-2">
                {strategies.map(s => (
                  <button
                    key={s.id}
                    onClick={() => setStrategy(s.id)}
                    className={`w-full p-3 rounded-xl border-2 text-left transition-all ${
                      strategy === s.id
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                        : "border-gray-200 dark:border-slate-600"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{s.icon}</span>
                      <div>
                        <span className="font-medium text-gray-900 dark:text-white text-sm">{s.name}</span>
                        <p className="text-xs text-gray-500">{s.description}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Canvas */}
          <div className="lg:col-span-3">
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 min-h-[500px] p-6">
              {nodes.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-400">
                  <span className="text-4xl mb-4">🤖</span>
                  <p className="text-lg font-medium">Arraste agentes para cá</p>
                  <p className="text-sm">ou clique nos agentes disponíveis</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Flow Visualization */}
                  <div className="flex items-center justify-center gap-2 mb-6">
                    <span className="text-sm text-gray-500">Fluxo:</span>
                    <div className="flex items-center gap-2">
                      {nodes.map((node, i) => (
                        <React.Fragment key={node.id}>
                          <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm">
                            {node.name}
                          </span>
                          {i < nodes.length - 1 && (
                            <span className="text-gray-400">
                              {strategy === "parallel" ? "||" : "→"}
                            </span>
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>

                  {/* Nodes Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {nodes.map(node => (
                      <NodeCard
                        key={node.id}
                        node={node}
                        isSelected={selectedNode === node.id}
                        onSelect={() => setSelectedNode(node.id)}
                        onDelete={() => removeNode(node.id)}
                      />
                    ))}
                  </div>

                  {/* Summary */}
                  <div className="mt-6 p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-2">Configuração do Time</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Agentes:</span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-white">{nodes.length}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Estratégia:</span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-white">
                          {strategies.find(s => s.id === strategy)?.name}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Status:</span>
                        <span className="ml-2 px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs">
                          Rascunho
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Protected>
  );
}
