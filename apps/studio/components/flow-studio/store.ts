/**
 * Agno Flow Studio v3.0 - Store
 * 
 * Zustand store with Immer for state management with undo/redo
 */

import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { temporal } from 'zundo';
import {
  FlowNode,
  FlowEdge,
  FlowNodeData,
  Workflow,
  WorkflowSettings,
  Execution,
  UIState,
  CanvasSettings,
  HistoryEntry,
} from './types';
import {
  Connection,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  NodeChange,
  EdgeChange,
} from '@xyflow/react';

// ============================================================
// Store State Interface
// ============================================================

interface FlowStudioState {
  // Workflow
  workflow: Workflow | null;
  isDirty: boolean;
  
  // Nodes & Edges
  nodes: FlowNode[];
  edges: FlowEdge[];
  
  // Execution
  execution: Execution | null;
  isExecuting: boolean;
  
  // UI
  ui: UIState;
  canvasSettings: CanvasSettings;
  
  // History
  history: HistoryEntry[];
  historyIndex: number;
  
  // Actions - Workflow
  setWorkflow: (workflow: Workflow) => void;
  saveWorkflow: () => Promise<void>;
  loadWorkflow: (id: string) => Promise<void>;
  newWorkflow: () => void;
  
  // Actions - Nodes
  setNodes: (nodes: FlowNode[]) => void;
  addNode: (node: FlowNode) => void;
  updateNode: (id: string, data: Partial<FlowNodeData>) => void;
  removeNode: (id: string) => void;
  duplicateNode: (id: string) => void;
  onNodesChange: (changes: NodeChange<FlowNode>[]) => void;
  
  // Actions - Edges
  setEdges: (edges: FlowEdge[]) => void;
  addEdge: (edge: FlowEdge) => void;
  removeEdge: (id: string) => void;
  onEdgesChange: (changes: EdgeChange<FlowEdge>[]) => void;
  onConnect: (connection: Connection) => void;
  
  // Actions - Selection
  selectNode: (id: string, multi?: boolean) => void;
  selectEdge: (id: string, multi?: boolean) => void;
  selectAll: () => void;
  clearSelection: () => void;
  deleteSelected: () => void;
  
  // Actions - Execution
  startExecution: (input?: Record<string, unknown>) => Promise<void>;
  stopExecution: () => void;
  updateNodeStatus: (nodeId: string, status: FlowNodeData['status'], output?: unknown) => void;
  
  // Actions - UI
  setTheme: (theme: UIState['theme']) => void;
  toggleSidebar: () => void;
  setSidebarTab: (tab: UIState['sidebarTab']) => void;
  toggleInspector: () => void;
  toggleMinimap: () => void;
  setEditMode: (editing: boolean) => void;
  
  // Actions - Debug
  addBreakpoint: (nodeId: string) => void;
  removeBreakpoint: (nodeId: string) => void;
  clearBreakpoints: () => void;
  stepDebug: () => void;
  
  // Actions - Canvas
  updateCanvasSettings: (settings: Partial<CanvasSettings>) => void;
  fitView: () => void;
  zoomIn: () => void;
  zoomOut: () => void;
  resetZoom: () => void;
}

// ============================================================
// Default Values
// ============================================================

const defaultUIState: UIState = {
  theme: 'system',
  sidebarOpen: true,
  sidebarTab: 'nodes',
  inspectorOpen: true,
  minimapVisible: true,
  selectedNodes: [],
  selectedEdges: [],
  isEditing: true,
  isExecuting: false,
  isDebugging: false,
  breakpoints: [],
};

const defaultCanvasSettings: CanvasSettings = {
  snapToGrid: true,
  gridSize: 20,
  showMinimap: true,
  showGrid: true,
  connectionMode: 'strict',
  panOnDrag: true,
  zoomOnScroll: true,
  fitViewOnInit: true,
};

const defaultWorkflowSettings: WorkflowSettings = {
  timeout: 300000,
  retryPolicy: {
    maxRetries: 3,
    backoffMultiplier: 2,
  },
  errorHandling: 'stop',
  logging: 'full',
};

// ============================================================
// Store Creation
// ============================================================

export const useFlowStudioStore = create<FlowStudioState>()(
  temporal(
    immer((set, get) => ({
      // Initial State
      workflow: null,
      isDirty: false,
      nodes: [],
      edges: [],
      execution: null,
      isExecuting: false,
      ui: defaultUIState,
      canvasSettings: defaultCanvasSettings,
      history: [],
      historyIndex: -1,
      
      // Workflow Actions
      setWorkflow: (workflow) => set((state) => {
        state.workflow = workflow;
        state.nodes = workflow.nodes;
        state.edges = workflow.edges;
        state.isDirty = false;
      }),
      
      saveWorkflow: async () => {
        const { workflow, nodes, edges } = get();
        if (!workflow) return;
        
        const updatedWorkflow: Workflow = {
          ...workflow,
          nodes,
          edges,
          updatedAt: new Date().toISOString(),
        };
        
        // TODO: API call to save
        console.log('Saving workflow:', updatedWorkflow);
        
        set((state) => {
          state.workflow = updatedWorkflow;
          state.isDirty = false;
        });
      },
      
      loadWorkflow: async (id) => {
        // TODO: API call to load
        console.log('Loading workflow:', id);
      },
      
      newWorkflow: () => set((state) => {
        const newWorkflow: Workflow = {
          id: `wf_${Date.now()}`,
          name: 'New Workflow',
          description: '',
          version: '1.0.0',
          status: 'draft',
          nodes: [],
          edges: [],
          viewport: { x: 0, y: 0, zoom: 1 },
          variables: [],
          triggers: [],
          settings: defaultWorkflowSettings,
          tags: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        state.workflow = newWorkflow;
        state.nodes = [];
        state.edges = [];
        state.isDirty = false;
      }),
      
      // Node Actions
      setNodes: (nodes) => set((state) => {
        state.nodes = nodes;
        state.isDirty = true;
      }),
      
      addNode: (node) => set((state) => {
        state.nodes.push(node);
        state.isDirty = true;
      }),
      
      updateNode: (id, data) => set((state) => {
        const node = state.nodes.find(n => n.id === id);
        if (node) {
          node.data = { ...node.data, ...data };
          state.isDirty = true;
        }
      }),
      
      removeNode: (id) => set((state) => {
        state.nodes = state.nodes.filter(n => n.id !== id);
        state.edges = state.edges.filter(e => e.source !== id && e.target !== id);
        state.ui.selectedNodes = state.ui.selectedNodes.filter(nid => nid !== id);
        state.isDirty = true;
      }),
      
      duplicateNode: (id) => set((state) => {
        const node = state.nodes.find(n => n.id === id);
        if (node) {
          const newNode: FlowNode = {
            ...node,
            id: `node_${Date.now()}`,
            position: {
              x: node.position.x + 50,
              y: node.position.y + 50,
            },
            selected: false,
          };
          state.nodes.push(newNode);
          state.isDirty = true;
        }
      }),
      
      onNodesChange: (changes) => set((state) => {
        state.nodes = applyNodeChanges(changes, state.nodes) as FlowNode[];
        state.isDirty = true;
      }),
      
      // Edge Actions
      setEdges: (edges) => set((state) => {
        state.edges = edges;
        state.isDirty = true;
      }),
      
      addEdge: (edge) => set((state) => {
        state.edges.push(edge);
        state.isDirty = true;
      }),
      
      removeEdge: (id) => set((state) => {
        state.edges = state.edges.filter(e => e.id !== id);
        state.ui.selectedEdges = state.ui.selectedEdges.filter(eid => eid !== id);
        state.isDirty = true;
      }),
      
      onEdgesChange: (changes) => set((state) => {
        state.edges = applyEdgeChanges(changes, state.edges) as FlowEdge[];
        state.isDirty = true;
      }),
      
      onConnect: (connection) => set((state) => {
        const newEdge: FlowEdge = {
          id: `edge_${Date.now()}`,
          source: connection.source!,
          target: connection.target!,
          sourceHandle: connection.sourceHandle || undefined,
          targetHandle: connection.targetHandle || undefined,
          data: { animated: true },
        };
        state.edges = addEdge(newEdge, state.edges) as FlowEdge[];
        state.isDirty = true;
      }),
      
      // Selection Actions
      selectNode: (id, multi = false) => set((state) => {
        if (multi) {
          if (state.ui.selectedNodes.includes(id)) {
            state.ui.selectedNodes = state.ui.selectedNodes.filter(nid => nid !== id);
          } else {
            state.ui.selectedNodes.push(id);
          }
        } else {
          state.ui.selectedNodes = [id];
          state.ui.selectedEdges = [];
        }
      }),
      
      selectEdge: (id, multi = false) => set((state) => {
        if (multi) {
          if (state.ui.selectedEdges.includes(id)) {
            state.ui.selectedEdges = state.ui.selectedEdges.filter(eid => eid !== id);
          } else {
            state.ui.selectedEdges.push(id);
          }
        } else {
          state.ui.selectedEdges = [id];
          state.ui.selectedNodes = [];
        }
      }),
      
      selectAll: () => set((state) => {
        state.ui.selectedNodes = state.nodes.map(n => n.id);
        state.ui.selectedEdges = state.edges.map(e => e.id);
      }),
      
      clearSelection: () => set((state) => {
        state.ui.selectedNodes = [];
        state.ui.selectedEdges = [];
      }),
      
      deleteSelected: () => set((state) => {
        const { selectedNodes, selectedEdges } = state.ui;
        state.nodes = state.nodes.filter(n => !selectedNodes.includes(n.id));
        state.edges = state.edges.filter(e => 
          !selectedEdges.includes(e.id) &&
          !selectedNodes.includes(e.source) &&
          !selectedNodes.includes(e.target)
        );
        state.ui.selectedNodes = [];
        state.ui.selectedEdges = [];
        state.isDirty = true;
      }),
      
      // Execution Actions
      startExecution: async (input) => {
        const { workflow, nodes } = get();
        if (!workflow) return;
        
        const execution: Execution = {
          id: `exec_${Date.now()}`,
          workflowId: workflow.id,
          status: 'running',
          triggeredBy: 'manual',
          startedAt: new Date().toISOString(),
          input: input || {},
          steps: nodes.map(n => ({
            nodeId: n.id,
            nodeName: n.data.label,
            status: 'pending',
          })),
        };
        
        set((state) => {
          state.execution = execution;
          state.isExecuting = true;
          state.ui.isExecuting = true;
          // Reset all node statuses
          state.nodes.forEach(n => {
            n.data.status = 'idle';
            n.data.error = undefined;
            n.data.output = undefined;
          });
        });
        
        // TODO: Actual execution via API
      },
      
      stopExecution: () => set((state) => {
        if (state.execution) {
          state.execution.status = 'cancelled';
          state.execution.completedAt = new Date().toISOString();
        }
        state.isExecuting = false;
        state.ui.isExecuting = false;
      }),
      
      updateNodeStatus: (nodeId, status, output) => set((state) => {
        const node = state.nodes.find(n => n.id === nodeId);
        if (node) {
          node.data.status = status;
          if (output !== undefined) {
            node.data.output = output;
          }
        }
        if (state.execution) {
          const step = state.execution.steps.find(s => s.nodeId === nodeId);
          if (step) {
            step.status = status === 'success' ? 'success' : status === 'error' ? 'failed' : 'running';
          }
        }
      }),
      
      // UI Actions
      setTheme: (theme) => set((state) => {
        state.ui.theme = theme;
      }),
      
      toggleSidebar: () => set((state) => {
        state.ui.sidebarOpen = !state.ui.sidebarOpen;
      }),
      
      setSidebarTab: (tab) => set((state) => {
        state.ui.sidebarTab = tab;
      }),
      
      toggleInspector: () => set((state) => {
        state.ui.inspectorOpen = !state.ui.inspectorOpen;
      }),
      
      toggleMinimap: () => set((state) => {
        state.ui.minimapVisible = !state.ui.minimapVisible;
        state.canvasSettings.showMinimap = !state.canvasSettings.showMinimap;
      }),
      
      setEditMode: (editing) => set((state) => {
        state.ui.isEditing = editing;
      }),
      
      // Debug Actions
      addBreakpoint: (nodeId) => set((state) => {
        if (!state.ui.breakpoints.includes(nodeId)) {
          state.ui.breakpoints.push(nodeId);
        }
      }),
      
      removeBreakpoint: (nodeId) => set((state) => {
        state.ui.breakpoints = state.ui.breakpoints.filter(id => id !== nodeId);
      }),
      
      clearBreakpoints: () => set((state) => {
        state.ui.breakpoints = [];
      }),
      
      stepDebug: () => {
        // TODO: Step through execution
        console.log('Step debug');
      },
      
      // Canvas Actions
      updateCanvasSettings: (settings) => set((state) => {
        state.canvasSettings = { ...state.canvasSettings, ...settings };
      }),
      
      fitView: () => {
        // Handled by React Flow ref
        console.log('Fit view');
      },
      
      zoomIn: () => {
        console.log('Zoom in');
      },
      
      zoomOut: () => {
        console.log('Zoom out');
      },
      
      resetZoom: () => {
        console.log('Reset zoom');
      },
    })),
    {
      limit: 50, // Keep 50 history entries
      equality: (a, b) => JSON.stringify(a.nodes) === JSON.stringify(b.nodes) &&
                         JSON.stringify(a.edges) === JSON.stringify(b.edges),
    }
  )
);

// Selectors
export const useNodes = () => useFlowStudioStore(state => state.nodes);
export const useEdges = () => useFlowStudioStore(state => state.edges);
export const useWorkflow = () => useFlowStudioStore(state => state.workflow);
export const useUIState = () => useFlowStudioStore(state => state.ui);
export const useSelectedNodes = () => useFlowStudioStore(state => 
  state.nodes.filter(n => state.ui.selectedNodes.includes(n.id))
);
