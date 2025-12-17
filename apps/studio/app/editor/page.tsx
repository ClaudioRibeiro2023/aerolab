 "use client";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Protected from "../../components/Protected";
import api from "../../lib/api";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Label } from "../../components/ui/label";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import { PageHeader } from "../../components/PageHeader";
import { toast } from "sonner";

import ReactFlow, {
  addEdge,
  Background,
  Controls,
  MiniMap,
  Connection,
  Edge,
  MarkerType,
  Node,
  OnConnect,
  ReactFlowInstance,
  useEdgesState,
  useNodesState,
  NodeProps,
  Handle,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import ELK from "elkjs/lib/elk.bundled.js";

const STORAGE_KEY = "editor-graph-v1";

const kindStyles: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  agent: { bg: "bg-blue-50", border: "border-blue-300", text: "text-blue-900", badge: "bg-blue-600 text-white" },
  transform: { bg: "bg-amber-50", border: "border-amber-300", text: "text-amber-900", badge: "bg-amber-600 text-white" },
  decision: { bg: "bg-emerald-50", border: "border-emerald-300", text: "text-emerald-900", badge: "bg-emerald-600 text-white" },
};

function CustomNode({ data }: NodeProps<{ label: string; kind?: "agent" | "transform" | "decision"; __errors?: string[] }>) {
  const kind = data?.kind || "agent";
  const s = kindStyles[kind] || kindStyles.agent;
  const errs = data.__errors;
  const title = errs && errs.length ? errs.join("\n") : undefined;
  return (
    <div className={`rounded-md border ${s.border} ${s.bg} px-3 py-2 shadow-sm min-w-[160px]`} title={title}>
      <div className="flex items-center justify-between">
        <div className={`text-xs px-2 py-0.5 rounded ${s.badge}`} aria-label="tipo-do-no">{kind}</div>
      </div>
      <div className={`mt-1 text-sm font-medium ${s.text}`}>{String(data?.label || "Node")}</div>
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

type AgentItem = { name: string; role?: string };

type NodeData = {
  label: string;
  input_template?: string;
  output_var?: string;
  kind?: "agent" | "transform" | "decision";
};

type SerializableNode = {
  id: string;
  position: { x: number; y: number };
  data: NodeData;
};

type SerializableEdge = {
  id: string;
  source: string;
  target: string;
  label?: string;
};

export default function EditorPage() {
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [nodes, setNodes, onNodesChange] = useNodesState<NodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>("");
  const [filter, setFilter] = useState("");
  const rfRef = useRef<ReactFlowInstance | null>(null);
  const selectedNode = useMemo(() => nodes.find((n) => n.selected) || null, [nodes]);
  const selectedEdge = useMemo(() => edges.find((e) => e.selected) || null, [edges]);
  const selectedEdgeSourceKind = useMemo(() => {
    if (!selectedEdge) return null;
    const src = nodes.find((n) => n.id === selectedEdge.source);
    return (src?.data.kind || null) as null | string;
  }, [selectedEdge, nodes]);

  // Workflows integration
  const [workflows, setWorkflows] = useState<Array<{ name: string; steps: Array<{ name: string; input_template: string; type: string; output_var?: string }> }>>([]);
  const [wfName, setWfName] = useState("");
  const [selWf, setSelWf] = useState("");
  const [runInputsText, setRunInputsText] = useState("{\n  \"topic\": \"Exemplo\"\n}");
  const [runOutput, setRunOutput] = useState<unknown>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [invalidNodeIds, setInvalidNodeIds] = useState<string[]>([]);
  const [invalidEdgeIds, setInvalidEdgeIds] = useState<string[]>([]);
  const [decisionLabelPreset, setDecisionLabelPreset] = useState<"yesno" | "truefalse" | "successfail">("yesno");
  const [nodeErrors, setNodeErrors] = useState<Record<string, string[]>>({});
  const [edgeErrors, setEdgeErrors] = useState<Record<string, string[]>>({});
  const [showHighlights, setShowHighlights] = useState(true);

  const enableConditional = process.env.NEXT_PUBLIC_FEATURE_CONDITIONAL_WORKFLOW === "true";

  const [conditionalSchema, setConditionalSchema] = useState<"transitions" | "conditions">("transitions");

  const sendConditionalWorkflow = async () => {
    try {
      const steps = nodes.map((n) => {
        const { label, kind, input_template, output_var } = n.data;
        const outs = edges
          .filter((e) => e.source === n.id)
          .map((e) => {
            const targetNode = nodes.find((x) => x.id === e.target);
            const targetLabel = targetNode?.data.label || e.target;
            const edgeLabel = typeof e.label === "string" ? e.label : "";
            return {
              label: edgeLabel,
              to: targetLabel,
            };
          });
        const step: {
          name: string;
          type: string;
          input_template: string;
          output_var?: string;
          conditions?: Record<string, string>;
          transitions?: Array<{ label: string; to: string }>;
        } = {
          name: label || n.id,
          type: kind || "agent",
          input_template: input_template || "{{input}}",
        };
        if (output_var) step.output_var = output_var;
        if (outs.length) {
          if (conditionalSchema === "conditions") {
            const conds: Record<string, string> = {};
            for (const o of outs) if (o.label) conds[o.label] = o.to;
            step.conditions = conds;
          } else {
            step.transitions = outs;
          }
        }
        return step;
      });
      const payload = { name: wfName?.trim() || "workflow", steps };
      await api.post("/workflows/registry/", payload);
      toast.success("Workflow condicional enviado");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Falha ao enviar workflow. Verifique suporte no backend.");
    }
  };

  const presetLabels = useMemo(() => (
    decisionLabelPreset === "yesno" ? ["yes", "no"] : decisionLabelPreset === "truefalse" ? ["true", "false"] : ["success", "fail"]
  ), [decisionLabelPreset]);

  const displayNodes = useMemo(
    () =>
      nodes.map((n) => {
        const errs = nodeErrors[n.id] || [];
        const base = showHighlights && errs.length ? { ...n, data: { ...(n.data as any), __errors: errs } } : n;
        return showHighlights && invalidNodeIds.includes(n.id)
          ? { ...base, style: { ...(n.style || {}), border: "2px solid #ef4444", boxShadow: "0 0 0 2px rgba(239,68,68,0.2)" } }
          : base;
      }),
    [nodes, invalidNodeIds, nodeErrors, showHighlights]
  );

  const displayEdges = useMemo(
    () =>
      edges.map((e) => {
        if (!showHighlights) return e;
        const invalid = invalidEdgeIds.includes(e.id);
        const lbl = typeof e.label === "string" ? e.label : "";
        const shown = invalid ? `${lbl} ${lbl ? "" : ""}⚠` : lbl;
        return invalid
          ? {
              ...e,
              label: shown,
              style: { ...(e.style || {}), stroke: "#ef4444" },
              labelStyle: { ...(e.labelStyle || {}), fill: "#ef4444", fontWeight: 700 },
            }
          : { ...e, label: shown };
      }),
    [edges, invalidEdgeIds, showHighlights]
  );

  const focusNode = (id: string) => {
    setNodes((nds) => nds.map((n) => ({ ...n, selected: n.id === id })));
    setEdges((eds) => eds.map((e) => ({ ...e, selected: false })));
  };

  const focusEdge = (id: string) => {
    setEdges((eds) => eds.map((e) => ({ ...e, selected: e.id === id })));
  };

  const filteredAgents = useMemo(() => {
    if (!filter) return agents;
    const f = filter.toLowerCase();
    return agents.filter((a) => a.name.toLowerCase().includes(f));
  }, [agents, filter]);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get("/agents");
        const list: AgentItem[] = res.data || [];
        setAgents(list);
        if (list.length > 0) setSelectedAgent(list[0].name);
        // workflows
        try {
          const wf = await api.get("/workflows/registry");
          setWorkflows(wf.data || []);
          if ((wf.data || []).length > 0 && !selWf) setSelWf((wf.data || [])[0].name);
        } catch {}
      } catch (e: any) {
        toast.error(e?.response?.data?.detail || "Erro ao carregar agents");
      }
    };
    // preset from localStorage
    try {
      const p = localStorage.getItem("editor-decision-preset");
      if (p === "yesno" || p === "truefalse" || p === "successfail") setDecisionLabelPreset(p);
    } catch {}
    // conditional schema from localStorage
    try {
      const cs = localStorage.getItem("editor-conditional-schema");
      if (cs === "transitions" || cs === "conditions") setConditionalSchema(cs);
    } catch {}
    load();
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem("editor-decision-preset", decisionLabelPreset);
    } catch {}
  }, [decisionLabelPreset]);

  useEffect(() => {
    try {
      localStorage.setItem("editor-conditional-schema", conditionalSchema);
    } catch {}
  }, [conditionalSchema]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as { nodes: SerializableNode[]; edges: SerializableEdge[] };
        setNodes(
          (parsed.nodes || []).map((n) => ({ id: n.id, position: n.position, data: { label: (n as any).data?.label || n.id, input_template: (n as any).data?.input_template, output_var: (n as any).data?.output_var, kind: (n as any).data?.kind || "agent" }, type: "custom" }))
        );
        setEdges(
          (parsed.edges || []).map((e) => ({ id: e.id, source: e.source, target: e.target, label: (e as any).label, markerEnd: { type: MarkerType.ArrowClosed } }))
        );
      }
    } catch {
      // ignore
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Delete" || e.key === "Backspace") {
        setNodes((nds) => nds.filter((n) => !n.selected));
        setEdges((eds) => {
          const selectedEdgeIds = new Set(eds.filter((ed) => ed.selected).map((ed) => ed.id));
          const currentNodes = rfRef.current?.getNodes?.() || [];
          const remainingNodeIds = new Set(
            (currentNodes.length ? currentNodes : rfRef.current?.getNodes?.() || [])
              .filter((n) => !n.selected)
              .map((n) => n.id)
          );
          return eds.filter(
            (ed) => !selectedEdgeIds.has(ed.id) && remainingNodeIds.has(ed.source) && remainingNodeIds.has(ed.target)
          );
        });
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [setNodes, setEdges]);

  const onConnect: OnConnect = useCallback((connection: Connection) => {
    setEdges((eds) =>
      addEdge(
        {
          ...connection,
          id: `${connection.source}-${connection.target}-${Date.now()}`,
          markerEnd: { type: MarkerType.ArrowClosed },
        },
        eds
      )
    );
  }, [setEdges]);

  const addAgentNode = () => {
    if (!selectedAgent) return;
    const baseId = selectedAgent;
    let id = baseId;
    let i = 1;
    const existingIds = new Set(nodes.map((n) => n.id));
    while (existingIds.has(id)) {
      id = `${baseId}-${i++}`;
    }
    const newNode: Node<NodeData> = {
      id,
      position: { x: Math.random() * 400, y: Math.random() * 300 },
      data: { label: id, input_template: "{{input}}", output_var: "", kind: "agent" },
      type: "custom",
    };
    setNodes((nds) => [...nds, newNode]);
    toast.success(`Nó adicionado: ${id}`);
  };

  const clearGraph = () => {
    setNodes([]);
    setEdges([]);
    toast.success("Canvas limpo");
  };

  const saveGraph = () => {
    try {
      const toSave = {
        nodes: nodes.map((n) => ({ id: n.id, position: n.position, data: { ...n.data } })),
        edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target, label: typeof e.label === "string" ? e.label : undefined })),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
      toast.success("Grafo salvo");
    } catch {
      toast.error("Falha ao salvar grafo");
    }
  };

  const loadGraph = () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        toast.error("Nenhum grafo salvo");
        return;
      }
      const parsed = JSON.parse(raw) as { nodes: SerializableNode[]; edges: SerializableEdge[] };
      setNodes(
        (parsed.nodes || []).map((n) => ({
          id: n.id,
          position: n.position,
          data: {
            label: n.data.label || n.id,
            input_template: n.data.input_template,
            output_var: n.data.output_var,
            kind: n.data.kind || "agent",
          },
          type: "custom",
        }))
      );
      setEdges(
        (parsed.edges || []).map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.label,
          markerEnd: { type: MarkerType.ArrowClosed },
        }))
      );
      toast.success("Grafo carregado");
    } catch {
      toast.error("Falha ao carregar grafo");
    }
  };

  const fitView = () => {
    try {
      rfRef.current?.fitView();
    } catch {}
  };

  const autoLayout = async () => {
    const elk = new ELK();
    try {
      // Default size for nodes if not set
      const DEFAULT_W = 180;
      const DEFAULT_H = 60;
      const graph = {
        id: "root",
        layoutOptions: {
          "elk.algorithm": "layered",
          "elk.direction": "RIGHT",
          "elk.layered.spacing.nodeNodeBetweenLayers": "50",
          "elk.spacing.nodeNode": "40",
        },
        children: nodes.map((n) => ({
          id: n.id,
          width: DEFAULT_W,
          height: DEFAULT_H,
        })),
        edges: edges.map((e) => ({ id: e.id, sources: [e.source], targets: [e.target] })),
      } as any;

      const laidOut = await elk.layout(graph);
      const positions: Record<string, { x: number; y: number }> = {};
      for (const c of laidOut.children || []) {
        positions[c.id] = { x: c.x || 0, y: c.y || 0 };
      }
      setNodes((nds) => nds.map((n) => ({ ...n, position: positions[n.id] || n.position })));
      toast.success("Auto-layout aplicado");
      setTimeout(() => fitView(), 50);
    } catch (e: any) {
      toast.error("Falha no auto-layout");
    }
  };

  const validateGraph = () => {
    const idSet = new Set(nodes.map((n) => n.id));
    const indeg = new Map<string, number>();
    const outdeg = new Map<string, number>();
    for (const id of idSet) { indeg.set(id, 0); outdeg.set(id, 0); }
    for (const e of edges) {
      if (!idSet.has(e.source) || !idSet.has(e.target)) continue;
      indeg.set(e.target, (indeg.get(e.target) || 0) + 1);
      outdeg.set(e.source, (outdeg.get(e.source) || 0) + 1);
    }
    const orfaos = [...idSet].filter((id) => (indeg.get(id)! + outdeg.get(id)!) === 0);
    const roots = [...idSet].filter((id) => indeg.get(id)! === 0);
    const sinks = [...idSet].filter((id) => outdeg.get(id)! === 0);

    // Reachability from roots
    const adj = new Map<string, string[]>();
    for (const id of idSet) adj.set(id, []);
    for (const e of edges) {
      if (adj.has(e.source) && idSet.has(e.target)) adj.get(e.source)!.push(e.target);
    }
    const reachable = new Set<string>();
    const queue: string[] = [];
    for (const r of roots) queue.push(r), reachable.add(r);
    while (queue.length) {
      const u = queue.shift()!;
      for (const v of (adj.get(u) || [])) if (!reachable.has(v)) { reachable.add(v); queue.push(v); }
    }
    const unreachable = [...idSet].filter((id) => !reachable.has(id));

    // Decision rules: exactly 2 outgoing with non-empty distinct labels
    const invalidDecisionNodes: string[] = [];
    const invalidDecisionEdges: string[] = [];
    const nodeErrs: Record<string, string[]> = {};
    const edgeErrs: Record<string, string[]> = {};
    for (const n of nodes) {
      if ((n.data as any)?.kind !== "decision") continue;
      const outs = edges.filter((e) => e.source === n.id);
      const labels = outs.map((e) => String(((e as any).label || "")).trim());
      const nonEmpty = labels.filter((l) => l.length > 0);
      const distinct = new Set(nonEmpty);
      if (outs.length !== 2 || nonEmpty.length !== 2 || distinct.size !== 2) {
        invalidDecisionNodes.push(n.id);
        for (let i = 0; i < outs.length; i++) {
          const lbl = labels[i] || "";
          if (!lbl) {
            invalidDecisionEdges.push(outs[i].id);
            edgeErrs[outs[i].id] = [...(edgeErrs[outs[i].id] || []), "label vazio (decision)"];
          }
        }
        nodeErrs[n.id] = [...(nodeErrs[n.id] || []), "decision inválido: precisa de 2 saídas com labels distintos"];
      }
      // preset mismatch check (only if exactly 2 non-empty distinct)
      if (outs.length === 2 && nonEmpty.length === 2 && distinct.size === 2) {
        const preset = decisionLabelPreset;
        const expected = preset === "yesno" ? ["yes", "no"] : preset === "truefalse" ? ["true", "false"] : ["success", "fail"];
        const setLabels = new Set(nonEmpty.map((s) => s.toLowerCase()));
        const ok = expected.every((x) => setLabels.has(x));
        if (!ok) {
          invalidDecisionNodes.push(n.id);
          nodeErrs[n.id] = [...(nodeErrs[n.id] || []), `decision: labels devem ser ${expected.join("/")}`];
        }
      }
    }

    // Duplicate output_var across nodes
    const ovMap = new Map<string, string[]>();
    for (const n of nodes) {
      const v = String(((n.data as any)?.output_var || "")).trim();
      if (v) {
        const arr = ovMap.get(v) || [];
        arr.push(n.id);
        ovMap.set(v, arr);
      }
    }
    const duplicatedOutVars = [...ovMap.entries()].filter(([_, ids]) => ids.length > 1);
    const duplicateOutputNodes = duplicatedOutVars.flatMap(([, ids]) => ids);

    // Cycles
    const order = topoSort(nodes.map((n) => n.id), edges.map((e) => ({ id: e.id, source: e.source, target: e.target })) as SerializableEdge[]);
    const hasCycle = !order;

    const invalidNodes: string[] = [];
    const invalidEdges: string[] = [...invalidDecisionEdges];
    invalidNodes.push(...orfaos);
    if (roots.length > 1) {
      invalidNodes.push(...roots);
      for (const id of roots) nodeErrs[id] = [...(nodeErrs[id] || []), "múltiplas roots"];
    }
    if (sinks.length > 1) {
      invalidNodes.push(...sinks);
      for (const id of sinks) nodeErrs[id] = [...(nodeErrs[id] || []), "múltiplos sinks"];
    }
    invalidNodes.push(...unreachable);
    for (const id of unreachable) nodeErrs[id] = [...(nodeErrs[id] || []), "inalcançável"];
    invalidNodes.push(...invalidDecisionNodes);
    invalidNodes.push(...duplicateOutputNodes);
    for (const id of orfaos) nodeErrs[id] = [...(nodeErrs[id] || []), "órfão"];
    for (const id of duplicateOutputNodes) nodeErrs[id] = [...(nodeErrs[id] || []), "output_var duplicado"];

    setInvalidNodeIds(Array.from(new Set(invalidNodes)));
    setInvalidEdgeIds(Array.from(new Set(invalidEdges)));
    setNodeErrors(nodeErrs);
    setEdgeErrors(edgeErrs);

    if (orfaos.length) toast.warning(`Nós órfãos: ${orfaos.join(", ")}`);
    if (roots.length > 1) toast.warning(`Múltiplas roots (${roots.length})`);
    if (sinks.length > 1) toast.warning(`Múltiplos sinks (${sinks.length})`);
    if (unreachable.length) toast.warning(`Nós inalcançáveis: ${unreachable.join(", ")}`);
    if (invalidDecisionNodes.length) toast.warning(`Decision inválido: ${invalidDecisionNodes.join(", ")}`);
    if (duplicatedOutVars.length) toast.warning(`output_var duplicados: ${duplicatedOutVars.map(([k]) => k).join(", ")}`);
    if (hasCycle) {
      toast.error("Grafo inválido: ciclo detectado");
      return false;
    }
    toast.success("Validação concluída");
    return true;
  };

  const clearHighlights = () => {
    setInvalidNodeIds([]);
    setInvalidEdgeIds([]);
    toast.success("Realces limpos");
  };

  // Graph -> Workflow helpers
  function topoSort(nodeIds: string[], es: SerializableEdge[]): string[] | null {
    const adj = new Map<string, Set<string>>();
    const indeg = new Map<string, number>();
    for (const id of nodeIds) {
      adj.set(id, new Set());
      indeg.set(id, 0);
    }
    for (const e of es) {
      if (!adj.has(e.source) || !adj.has(e.target)) continue;
      if (!adj.get(e.source)!.has(e.target)) {
        adj.get(e.source)!.add(e.target);
        indeg.set(e.target, (indeg.get(e.target) || 0) + 1);
      }
    }
    const q: string[] = [];
    for (const [id, d] of indeg) if ((d || 0) === 0) q.push(id);
    const out: string[] = [];
    while (q.length) {
      const u = q.shift()!;
      out.push(u);
      for (const v of adj.get(u) || []) {
        indeg.set(v, (indeg.get(v) || 0) - 1);
        if ((indeg.get(v) || 0) === 0) q.push(v);
      }
    }
    return out.length === nodeIds.length ? out : null;
  }

  function toWorkflowSteps(): Array<{ type: string; name: string; input_template: string; output_var?: string }> | null {
    const es: SerializableEdge[] = edges.map((e) => ({ id: e.id, source: e.source, target: e.target } as SerializableEdge));
    const ids = nodes.map((n) => n.id);
    const order = topoSort(ids, es);
    if (!order) return null; // ciclo
    return order.map((id) => {
      const n = nodes.find((x) => x.id === id)!;
      const name = n.data.label || n.id;
      const input_template = n.data.input_template || "{{input}}";
      const output_var = n.data.output_var || undefined;
      const type = n.data.kind || "agent";
      const step: { type: string; name: string; input_template: string; output_var?: string } = {
        type,
        name,
        input_template,
      };
      if (output_var) step.output_var = output_var;
      return step;
    });
  }

  const saveAsWorkflow = async () => {
    if (!wfName.trim()) {
      toast.error("Informe um nome de workflow");
      return;
    }
    const steps = toWorkflowSteps();
    if (!steps) {
      toast.error("Grafo inválido: detectado ciclo. Remova ciclos e tente novamente.");
      return;
    }
    try {
      await api.post("/workflows/registry/", { name: wfName.trim(), steps });
      toast.success("Workflow salvo");
      setWfName("");
      const wf = await api.get("/workflows/registry");
      setWorkflows(wf.data || []);
      if ((wf.data || []).length > 0) setSelWf((wf.data || [])[0].name);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Falha ao salvar workflow");
    }
  };

  const loadWorkflowToCanvas = async () => {
    if (!selWf) return;
    try {
      const wf = (workflows || []).find((w) => w.name === selWf);
      if (!wf) {
        toast.error("Workflow não encontrado");
        return;
      }
      const seq = wf.steps || [];
      const baseX = 50;
      const baseY = 80;
      const gapX = 220;
      const newNodes: Node<NodeData>[] = seq.map((s, idx) => ({
        id: `${s.name}-${idx}`,
        position: { x: baseX + idx * gapX, y: baseY },
        data: { label: s.name, kind: (s.type as NodeData["kind"]) || "agent" },
        type: "custom",
      }));
      const newEdges: Edge[] = [];
      for (let i = 0; i < newNodes.length - 1; i++) {
        newEdges.push({
          id: `e-${i}`,
          source: newNodes[i].id,
          target: newNodes[i + 1].id,
          label: "",
          markerEnd: { type: MarkerType.ArrowClosed },
        });
      }
      setNodes(newNodes);
      setEdges(newEdges);
      toast.success("Workflow carregado no editor");
      setTimeout(() => fitView(), 50);
    } catch {
      toast.error("Falha ao carregar workflow");
    }
  };

  const runWorkflow = async () => {
    if (!selWf) {
      toast.error("Selecione um workflow");
      return;
    }
    setRunOutput(null);
    try {
      let inputs: Record<string, unknown> = {};
      if (runInputsText?.trim()) inputs = JSON.parse(runInputsText) as Record<string, unknown>;
      const res = await api.post(`/workflows/registry/${encodeURIComponent(selWf)}/run`, { inputs });
      setRunOutput(res.data);
      toast.success("Execução concluída");
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || "Falha na execução");
    }
  };

  const exportJSON = () => {
    try {
      const toSave = {
        nodes: nodes.map((n) => ({ id: n.id, position: n.position, data: { ...n.data } })),
        edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target, label: typeof e.label === "string" ? e.label : undefined })),
      };
      const blob = new Blob([JSON.stringify(toSave, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "graph.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Falha ao exportar JSON");
    }
  };

  const exportConditionalWorkflow = () => {
    try {
      const steps = nodes.map((n) => {
        const name = String((n.data as any)?.label || n.id);
        const type = String((n.data as any)?.kind || "agent");
        const input_template = String((n.data as any)?.input_template || "{{input}}");
        const output_var = (n.data as any)?.output_var || undefined;
        const outs = edges
          .filter((e) => e.source === n.id)
          .map((e) => ({
            label: String(((e as any).label || "")),
            to: String((((nodes.find((x) => x.id === e.target)?.data as any)?.label) || e.target)),
          }));
        const step: any = { name, type, input_template };
        if (output_var) step.output_var = output_var;
        if (outs.length) {
          if (conditionalSchema === "conditions") {
            const conds: Record<string, string> = {};
            for (const o of outs) if (o.label) conds[o.label] = o.to;
            step.conditions = conds;
          } else {
            step.transitions = outs;
          }
        }
        return step;
      });
      const payload = { name: wfName?.trim() || "workflow", steps };
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "workflow-conditional.json";
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Workflow condicional exportado");
    } catch {
      toast.error("Falha ao exportar workflow");
    }
  };

  const importJSON = async (file?: File | null) => {
    const f = file || fileInputRef.current?.files?.[0];
    if (!f) return;
    try {
      const text = await f.text();
      const parsed = JSON.parse(text) as { nodes: SerializableNode[]; edges: SerializableEdge[] };
      setNodes((parsed.nodes || []).map((n) => ({ id: n.id, position: n.position, data: { label: (n as any).data?.label || n.id, input_template: (n as any).data?.input_template, output_var: (n as any).data?.output_var, kind: (n as any).data?.kind || "agent" }, type: "custom" })));
      setEdges((parsed.edges || []).map((e) => ({ id: e.id, source: e.source, target: e.target, label: (e as any).label, markerEnd: { type: MarkerType.ArrowClosed } })));
      toast.success("JSON importado");
      setTimeout(() => fitView(), 50);
    } catch {
      toast.error("Falha ao importar JSON");
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <Protected>
      <div className="space-y-4">
        <PageHeader
          title="Editor de Workflows"
          subtitle="Visualize e edite grafos de agentes para gerar workflows executáveis."
          breadcrumbs={[
            { label: "Workflows", href: "/workflows" },
            { label: "Editor" },
          ]}
        />

        <div className="grid gap-4 md:grid-cols-4">
        <div className="md:col-span-1 space-y-3">
          <Card>
            <CardHeader>
              <CardTitle>Editor</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="filter">Filtrar agents</Label>
                <Input id="filter" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filtrar por nome" />
              </div>
              <div className="space-y-1">
                <Label htmlFor="agent">Adicionar nó (agent)</Label>
                <select
                  id="agent"
                  className="h-9 w-full rounded-md border border-gray-300 bg-white px-3 text-sm"
                  title="Selecionar agent"
                  value={selectedAgent}
                  onChange={(e) => setSelectedAgent(e.target.value)}
                >
                  {filteredAgents.map((a) => (
                    <option key={a.name} value={a.name}>{a.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2">
                <Button onClick={addAgentNode}>Adicionar</Button>
                <Button variant="outline" onClick={autoLayout}>Auto-Layout</Button>
                <Button variant="outline" onClick={validateGraph}>Validar</Button>
                <Button variant="outline" onClick={clearHighlights}>Limpar realces</Button>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={saveGraph}>Salvar</Button>
                <Button variant="outline" onClick={loadGraph}>Carregar</Button>
                <Button variant="outline" onClick={clearGraph}>Limpar</Button>
              </div>
              <p className="text-xs text-gray-600">Arraste para criar conexões. Clique em Auto-Layout para organizar.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Resumo de Validação</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-sm">Realces: {showHighlights ? "Ativos" : "Desativados"}</div>
                <Button variant="outline" onClick={() => setShowHighlights((v) => !v)}>
                  {showHighlights ? "Ocultar" : "Mostrar"}
                </Button>
              </div>
              {Object.keys(nodeErrors).length === 0 && Object.keys(edgeErrors).length === 0 ? (
                <p className="text-sm text-gray-600">Sem erros. Clique em Validar para analisar o grafo.</p>
              ) : (
                <>
                  <div>
                    <div className="text-xs font-medium text-gray-700 mb-1">Nós com erros</div>
                    <div className="space-y-1">
                      {Object.entries(nodeErrors).map(([id, errs]) => (
                        <button
                          key={id}
                          className="w-full text-left text-xs px-2 py-1 rounded border hover:bg-gray-50"
                          onClick={() => focusNode(id)}
                        >
                          <span className="font-medium">{id}</span>: {errs.join("; ")}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-medium text-gray-700 mb-1">Arestas com erros</div>
                    <div className="space-y-1">
                      {Object.entries(edgeErrors).map(([id, errs]) => (
                        <button
                          key={id}
                          className="w-full text-left text-xs px-2 py-1 rounded border hover:bg-gray-50"
                          onClick={() => focusEdge(id)}
                        >
                          <span className="font-medium">{id}</span>: {errs.join("; ")}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Nó Selecionado</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {!selectedNode ? (
                <p className="text-sm text-gray-600">Selecione um nó para editar suas propriedades.</p>
              ) : (
                <>
                  <div className="space-y-1">
                    <Label htmlFor="node-label">Label</Label>
                    <Input
                      id="node-label"
                      value={String(((selectedNode.data as any)?.label) || selectedNode.id)}
                      onChange={(e) =>
                        setNodes((nds) => nds.map((n) => (n.id === selectedNode.id ? { ...n, data: { ...(n.data as any), label: e.target.value } } : n)))
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="node-kind">Tipo</Label>
                    <select
                      id="node-kind"
                      className="h-9 w-full rounded-md border border-gray-300 bg-white px-3 text-sm"
                      title="Tipo do nó"
                      value={String(((selectedNode.data as any)?.kind) || "agent")}
                      onChange={(e) =>
                        setNodes((nds) => nds.map((n) => (n.id === selectedNode.id ? { ...n, data: { ...(n.data as any), kind: e.target.value as any } } : n)))
                      }
                    >
                      <option value="agent">Agent</option>
                      <option value="transform">Transform</option>
                      <option value="decision">Decision</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="node-input-template">Input Template</Label>
                    <Textarea
                      id="node-input-template"
                      placeholder="Ex: Pesquise sobre {{topic}}"
                      value={String(((selectedNode.data as any)?.input_template) || "")}
                      onChange={(e) =>
                        setNodes((nds) => nds.map((n) => (n.id === selectedNode.id ? { ...n, data: { ...(n.data as any), input_template: e.target.value } } : n)))
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="node-output-var">Output var (opcional)</Label>
                    <Input
                      id="node-output-var"
                      value={String(((selectedNode.data as any)?.output_var) || "")}
                      onChange={(e) =>
                        setNodes((nds) => nds.map((n) => (n.id === selectedNode.id ? { ...n, data: { ...(n.data as any), output_var: e.target.value } } : n)))
                      }
                    />
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Aresta Selecionada</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {!selectedEdge ? (
                <p className="text-sm text-gray-600">Selecione uma aresta para editar seu label.</p>
              ) : (
                <>
                  <div className="text-xs text-gray-600">{selectedEdge.source} → {selectedEdge.target}</div>
                  <div className="space-y-1">
                    <Label htmlFor="edge-label">Label</Label>
                    <Input
                      id="edge-label"
                      value={String(((selectedEdge as any).label) || "")}
                      onChange={(e) =>
                        setEdges((eds) => eds.map((ed) => ed.id === selectedEdge.id ? ({ ...ed, label: e.target.value } as Edge) : ed))
                      }
                    />
                  </div>
                  {selectedEdgeSourceKind === "decision" && (
                    <>
                      <div className="space-y-1">
                        <Label htmlFor="decision-preset">Preset de decisão</Label>
                        <select
                          id="decision-preset"
                          className="h-9 w-full rounded-md border border-gray-300 bg-white px-3 text-sm"
                          title="Preset de decisão"
                          value={decisionLabelPreset}
                          onChange={(e) => setDecisionLabelPreset(e.target.value as any)}
                        >
                          <option value="yesno">yes/no</option>
                          <option value="truefalse">true/false</option>
                          <option value="successfail">success/fail</option>
                        </select>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-600">Sugestões:</span>
                        {presetLabels.map((pl) => (
                          <Button key={pl} size="sm" variant="outline" onClick={() => setEdges((eds) => eds.map((ed) => ed.id === selectedEdge.id ? ({ ...ed, label: pl } as Edge) : ed))}>{pl}</Button>
                        ))}
                      </div>
                    </>
                  )}
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Workflow</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="wf-name">Salvar como Workflow</Label>
                <div className="flex gap-2">
                  <Input id="wf-name" placeholder="Nome do workflow" value={wfName} onChange={(e) => setWfName(e.target.value)} />
                  <Button onClick={saveAsWorkflow} disabled={!wfName.trim()}>Salvar</Button>
                </div>
              </div>
              <div className="space-y-1">
                <Label htmlFor="wf-select">Carregar / Executar</Label>
                <select
                  id="wf-select"
                  className="h-9 w-full rounded-md border border-gray-300 bg-white px-3 text-sm"
                  title="Selecionar workflow"
                  value={selWf}
                  onChange={(e) => setSelWf(e.target.value)}
                >
                  {(workflows || []).map((w) => (
                    <option key={w.name} value={w.name}>{w.name}</option>
                  ))}
                </select>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={loadWorkflowToCanvas} disabled={!selWf}>Carregar no Editor</Button>
                  <Button variant="outline" onClick={runWorkflow} disabled={!selWf}>Executar</Button>
                </div>
              </div>
              <div className="space-y-1">
                <Label htmlFor="run-inputs">Inputs (JSON)</Label>
                <textarea
                  id="run-inputs"
                  className="w-full min-h-[90px] rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-mono"
                  placeholder="Ex: JSON de inputs"
                  value={runInputsText}
                  onChange={(e) => setRunInputsText(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="conditional-schema">Esquema condicional</Label>
                <select
                  id="conditional-schema"
                  className="h-9 w-full rounded-md border border-gray-300 bg-white px-3 text-sm"
                  title="Esquema condicional no payload do workflow"
                  value={conditionalSchema}
                  onChange={(e) => setConditionalSchema(e.target.value as any)}
                >
                  <option value="transitions">transitions (array)</option>
                  <option value="conditions">conditions (record)</option>
                </select>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={exportConditionalWorkflow} title="Exporta um JSON com transições por aresta (para nós decision)">Exportar Workflow Condicional</Button>
                <Button
                  variant="outline"
                  onClick={sendConditionalWorkflow}
                  disabled={!enableConditional}
                  title={enableConditional ? "Envia o workflow condicional para o backend" : "Requer suporte no backend (NEXT_PUBLIC_FEATURE_CONDITIONAL_WORKFLOW=true)"}
                >
                  Enviar Workflow Condicional
                </Button>
              </div>
              {runOutput !== null && (
                <pre className="text-xs whitespace-pre-wrap bg-gray-50 p-2 border rounded">{typeof runOutput === 'string' ? runOutput : JSON.stringify(runOutput, null, 2)}</pre>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Importar / Exportar</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex gap-2">
                <Button variant="outline" onClick={exportJSON}>Exportar JSON</Button>
                <Button variant="outline" onClick={() => fileInputRef.current?.click()}>Importar JSON</Button>
              </div>
              <input ref={fileInputRef} type="file" accept="application/json" className="hidden" aria-label="Importar JSON" title="Importar JSON" onChange={(e) => importJSON(e.target.files?.[0] || null)} />
            </CardContent>
          </Card>
        </div>
        <div className="md:col-span-3 h-[70vh] border rounded bg-white">
          <ReactFlow
            nodes={displayNodes}
            edges={displayEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={(inst) => { rfRef.current = inst; setTimeout(() => inst.fitView(), 50); }}
            snapToGrid
            snapGrid={[15, 15]}
            nodeTypes={{ custom: CustomNode }}
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
      </div>
    </div>
    </Protected>
  );
}
