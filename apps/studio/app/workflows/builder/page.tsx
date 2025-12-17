"use client";

import React, { useState, useCallback, useRef } from "react";
import Protected from "../../../components/Protected";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useAuth } from "../../../store/auth";
import { PageHeader } from "../../../components/PageHeader";

// Types
interface WorkflowNode {
  id: string;
  type: "start" | "agent" | "condition" | "action" | "end";
  label: string;
  x: number;
  y: number;
  config?: Record<string, any>;
}

interface WorkflowEdge {
  id: string;
  from: string;
  to: string;
  label?: string;
}

// Icons
const Icons = {
  play: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" strokeWidth={2} /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 8l6 4-6 4V8z" /></svg>),
  agent: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>),
  condition: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  action: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>),
  stop: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" strokeWidth={2} /><rect x="9" y="9" width="6" height="6" strokeWidth={2} /></svg>),
  trash: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>),
  save: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>),
  back: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>),
  plus: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>),
  zoom: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" /></svg>),
};

const nodeTypes = [
  { type: "start", label: "Início", icon: Icons.play, color: "bg-green-500" },
  { type: "agent", label: "Agente", icon: Icons.agent, color: "bg-blue-500" },
  { type: "condition", label: "Condição", icon: Icons.condition, color: "bg-yellow-500" },
  { type: "action", label: "Ação", icon: Icons.action, color: "bg-purple-500" },
  { type: "end", label: "Fim", icon: Icons.stop, color: "bg-red-500" },
];

// Node Component
function WorkflowNodeComponent({ 
  node, 
  selected, 
  onSelect, 
  onDrag, 
  onDelete,
  onConnect
}: { 
  node: WorkflowNode; 
  selected: boolean;
  onSelect: () => void;
  onDrag: (x: number, y: number) => void;
  onDelete: () => void;
  onConnect: () => void;
}) {
  const nodeType = nodeTypes.find(t => t.type === node.type);
  const [dragging, setDragging] = useState(false);
  const startPos = useRef({ x: 0, y: 0, nodeX: 0, nodeY: 0 });

  const handleMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect();
    setDragging(true);
    startPos.current = { x: e.clientX, y: e.clientY, nodeX: node.x, nodeY: node.y };
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!dragging) return;
    const dx = e.clientX - startPos.current.x;
    const dy = e.clientY - startPos.current.y;
    onDrag(startPos.current.nodeX + dx, startPos.current.nodeY + dy);
  }, [dragging, onDrag]);

  const handleMouseUp = useCallback(() => {
    setDragging(false);
  }, []);

  React.useEffect(() => {
    if (dragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
      return () => {
        window.removeEventListener("mousemove", handleMouseMove);
        window.removeEventListener("mouseup", handleMouseUp);
      };
    }
  }, [dragging, handleMouseMove, handleMouseUp]);

  return (
    <div
      className={`absolute flex flex-col items-center cursor-move select-none transition-shadow ${selected ? "z-10" : ""}`}
      style={{ left: node.x, top: node.y }}
      onMouseDown={handleMouseDown}
    >
      <div className={`relative p-4 rounded-2xl shadow-lg border-2 transition-all ${selected ? "border-blue-500 shadow-blue-500/25" : "border-transparent"} bg-white dark:bg-slate-800`}>
        <div className={`absolute -top-2 -right-2 w-6 h-6 rounded-full ${nodeType?.color} flex items-center justify-center text-white text-xs`}>
          {nodeType?.icon}
        </div>
        <span className="text-sm font-medium text-gray-900 dark:text-white">{node.label}</span>
        
        {/* Connection points */}
        <div 
          className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-blue-500 rounded-full border-2 border-white dark:border-slate-800 cursor-crosshair hover:scale-125 transition-transform"
          onClick={(e) => { e.stopPropagation(); onConnect(); }}
          title="Conectar"
        />
        
        {selected && node.type !== "start" && (
          <button 
            className="absolute -top-2 -left-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white hover:bg-red-600 transition-colors"
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            title="Remover"
          >
            {Icons.trash}
          </button>
        )}
      </div>
    </div>
  );
}

export default function WorkflowBuilderPage() {
  const { role } = useAuth();
  const router = useRouter();
  
  React.useEffect(() => {
    if (role && role !== "admin") {
      toast.error("Apenas administradores podem acessar o construtor de workflows");
      router.replace("/workflows");
    }
  }, [role, router]);

  const [nodes, setNodes] = useState<WorkflowNode[]>([
    { id: "start", type: "start", label: "Início", x: 100, y: 100 },
  ]);
  const [edges, setEdges] = useState<WorkflowEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [connectingFrom, setConnectingFrom] = useState<string | null>(null);
  const [workflowName, setWorkflowName] = useState("Novo Workflow");
  const [zoom, setZoom] = useState(1);
  const canvasRef = useRef<HTMLDivElement>(null);

  const addNode = (type: WorkflowNode["type"]) => {
    const id = `node-${Date.now()}`;
    const label = nodeTypes.find(t => t.type === type)?.label || type;
    setNodes([...nodes, { id, type, label, x: 200 + Math.random() * 200, y: 150 + Math.random() * 150 }]);
  };

  const updateNodePosition = (id: string, x: number, y: number) => {
    setNodes(nodes.map(n => n.id === id ? { ...n, x: Math.max(0, x), y: Math.max(0, y) } : n));
  };

  const deleteNode = (id: string) => {
    setNodes(nodes.filter(n => n.id !== id));
    setEdges(edges.filter(e => e.from !== id && e.to !== id));
    setSelectedNode(null);
  };

  const handleConnect = (nodeId: string) => {
    if (!connectingFrom) {
      setConnectingFrom(nodeId);
    } else if (connectingFrom !== nodeId) {
      const edgeExists = edges.some(e => e.from === connectingFrom && e.to === nodeId);
      if (!edgeExists) {
        setEdges([...edges, { id: `edge-${Date.now()}`, from: connectingFrom, to: nodeId }]);
      }
      setConnectingFrom(null);
    } else {
      setConnectingFrom(null);
    }
  };

  const deleteEdge = (id: string) => {
    setEdges(edges.filter(e => e.id !== id));
  };

  const getNodeCenter = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return { x: 0, y: 0 };
    return { x: node.x + 50, y: node.y + 30 };
  };

  return (
    <Protected>
      <div className="h-[calc(100vh-8rem)] flex flex-col">
        <PageHeader
          title="Workflow Builder"
          subtitle="Construa e visualize fluxos de múltiplos agentes."
          leadingAction={
            <Link
              href="/workflows"
              className="p-2 text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
              title="Voltar"
            >
              {Icons.back}
            </Link>
          }
        />

        {/* Toolbar */}
        <div className="flex items-center justify-between gap-4 mb-4 p-4 bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <input 
              type="text" 
              value={workflowName} 
              onChange={(e) => setWorkflowName(e.target.value)}
              className="text-lg font-semibold bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1 text-gray-900 dark:text-white"
              placeholder="Nome do workflow"
            />
          </div>
          
          <div className="flex items-center gap-2">
            {/* Node palette */}
            {nodeTypes.filter(t => t.type !== "start").map(nodeType => (
              <button
                key={nodeType.type}
                onClick={() => addNode(nodeType.type as WorkflowNode["type"])}
                className={`flex items-center gap-2 px-3 py-2 ${nodeType.color} text-white rounded-xl text-sm font-medium hover:opacity-90 transition-opacity`}
                title={`Adicionar ${nodeType.label}`}
              >
                {nodeType.icon}
                <span className="hidden md:inline">{nodeType.label}</span>
              </button>
            ))}
            <div className="w-px h-8 bg-gray-200 dark:bg-slate-700 mx-2" />
            <button className="btn-primary flex items-center gap-2" title="Salvar">
              {Icons.save} <span className="hidden md:inline">Salvar</span>
            </button>
          </div>
        </div>

        {/* Canvas */}
        <div 
          ref={canvasRef}
          className="flex-1 relative bg-gray-50 dark:bg-slate-900 rounded-2xl border border-gray-200 dark:border-slate-700 overflow-hidden workflow-grid-bg"
          onClick={() => { setSelectedNode(null); setConnectingFrom(null); }}
        >
          {/* Zoom controls */}
          <div className="absolute top-4 right-4 flex items-center gap-2 bg-white dark:bg-slate-800 rounded-xl p-2 shadow-lg z-20">
            <button onClick={() => setZoom(Math.max(0.5, zoom - 0.1))} className="p-1 hover:bg-gray-100 dark:hover:bg-slate-700 rounded" title="Diminuir zoom">−</button>
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400 min-w-[3rem] text-center">{Math.round(zoom * 100)}%</span>
            <button onClick={() => setZoom(Math.min(2, zoom + 0.1))} className="p-1 hover:bg-gray-100 dark:hover:bg-slate-700 rounded" title="Aumentar zoom">+</button>
          </div>

          {/* Connection hint */}
          {connectingFrom && (
            <div className="absolute top-4 left-4 px-4 py-2 bg-blue-500 text-white rounded-xl text-sm shadow-lg z-20">
              Clique em outro nó para conectar
            </div>
          )}

          {/* SVG for edges */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ transform: `scale(${zoom})`, transformOrigin: "0 0" }}>
            <defs>
              <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#6366f1" />
              </marker>
            </defs>
            {edges.map(edge => {
              const from = getNodeCenter(edge.from);
              const to = getNodeCenter(edge.to);
              return (
                <g key={edge.id} className="pointer-events-auto cursor-pointer" onClick={() => deleteEdge(edge.id)}>
                  <line x1={from.x} y1={from.y + 15} x2={to.x} y2={to.y - 15} stroke="#6366f1" strokeWidth="2" markerEnd="url(#arrowhead)" />
                  <line x1={from.x} y1={from.y + 15} x2={to.x} y2={to.y - 15} stroke="transparent" strokeWidth="20" />
                </g>
              );
            })}
          </svg>

          {/* Nodes */}
          <div style={{ transform: `scale(${zoom})`, transformOrigin: "0 0" }}>
            {nodes.map(node => (
              <WorkflowNodeComponent
                key={node.id}
                node={node}
                selected={selectedNode === node.id}
                onSelect={() => setSelectedNode(node.id)}
                onDrag={(x, y) => updateNodePosition(node.id, x, y)}
                onDelete={() => deleteNode(node.id)}
                onConnect={() => handleConnect(node.id)}
              />
            ))}
          </div>
        </div>

        {/* Properties Panel */}
        {selectedNode && (
          <div className="absolute right-8 top-32 w-72 bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-xl p-4 z-30">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Propriedades</h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-500 dark:text-gray-400">Label</label>
                <input 
                  type="text" 
                  value={nodes.find(n => n.id === selectedNode)?.label || ""}
                  onChange={(e) => setNodes(nodes.map(n => n.id === selectedNode ? { ...n, label: e.target.value } : n))}
                  className="input-modern mt-1"
                  placeholder="Nome do nó"
                />
              </div>
              <div>
                <label className="text-sm text-gray-500 dark:text-gray-400">Tipo</label>
                <p className="text-sm font-medium text-gray-900 dark:text-white capitalize mt-1">
                  {nodes.find(n => n.id === selectedNode)?.type}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </Protected>
  );
}
