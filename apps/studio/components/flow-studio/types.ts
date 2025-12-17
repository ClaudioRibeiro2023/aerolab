/**
 * Agno Flow Studio v3.0 - Types
 * 
 * Core type definitions for the visual workflow builder
 */

import { Node, Edge, XYPosition } from '@xyflow/react';

// ============================================================
// Node Categories & Types
// ============================================================

export type NodeCategory = 
  | 'agents'
  | 'logic'
  | 'data'
  | 'memory'
  | 'integrations'
  | 'governance'
  | 'input'
  | 'output';

export type AgentNodeType = 
  | 'agent' | 'team' | 'supervisor' | 'critic' | 'planner'
  | 'tool-user' | 'researcher' | 'coder' | 'analyst'
  | 'multi-modal' | 'streaming' | 'memory-agent';

export type LogicNodeType = 
  | 'condition' | 'switch' | 'loop' | 'parallel' | 'join'
  | 'gate' | 'delay' | 'retry' | 'circuit-breaker' | 'rate-limiter';

export type DataNodeType = 
  | 'transform' | 'map' | 'filter' | 'reduce' | 'sort'
  | 'merge' | 'split' | 'aggregate' | 'cache' | 'schema-validator';

export type MemoryNodeType = 
  | 'memory-read' | 'memory-write' | 'long-term' | 'short-term'
  | 'rag-search' | 'rag-ingest' | 'vector-store' | 'reranker';

export type IntegrationNodeType = 
  | 'http' | 'graphql' | 'websocket' | 'grpc'
  | 'database' | 'queue' | 'storage' | 'email'
  | 'slack' | 'discord' | 'webhook' | 'mcp-tool';

export type GovernanceNodeType = 
  | 'human-approval' | 'checkpoint' | 'audit-log'
  | 'secret-fetch' | 'cost-guard' | 'time-guard'
  | 'compliance-check' | 'pii-detector';

export type FlowNodeType = 
  | AgentNodeType 
  | LogicNodeType 
  | DataNodeType 
  | MemoryNodeType 
  | IntegrationNodeType 
  | GovernanceNodeType
  | 'input' | 'output';

// ============================================================
// Port Types
// ============================================================

export type PortDataType = 
  | 'any' | 'string' | 'number' | 'boolean' | 'object' | 'array'
  | 'message' | 'context' | 'file' | 'image' | 'audio' | 'video';

export interface Port {
  id: string;
  name: string;
  type: 'input' | 'output';
  dataType: PortDataType;
  required?: boolean;
  multiple?: boolean;
  defaultValue?: unknown;
  description?: string;
}

// ============================================================
// Node Data
// ============================================================

export interface FlowNodeData extends Record<string, unknown> {
  label: string;
  description?: string;
  nodeType: FlowNodeType;
  category: NodeCategory;
  icon: string;
  color: string;
  
  // Ports
  inputs: Port[];
  outputs: Port[];
  
  // Configuration
  config: Record<string, unknown>;
  
  // State
  status?: 'idle' | 'running' | 'success' | 'error' | 'skipped' | 'waiting';
  error?: string;
  output?: unknown;
  
  // Execution metrics
  executionTime?: number;
  tokenUsage?: number;
  cost?: number;
  
  // UI state
  collapsed?: boolean;
  selected?: boolean;
  highlighted?: boolean;
  
  // Validation
  isValid?: boolean;
  validationErrors?: string[];
}

export type FlowNode = Node<FlowNodeData>;

// ============================================================
// Edge Data
// ============================================================

export interface FlowEdgeData {
  label?: string;
  condition?: string;
  animated?: boolean;
  pathType?: 'default' | 'success' | 'error' | 'conditional';
  dataPreview?: unknown;
}

// Note: Edge type is more permissive - we cast where needed
export type FlowEdge = Edge;

// ============================================================
// Workflow
// ============================================================

export type WorkflowStatus = 
  | 'draft' | 'published' | 'running' | 'paused' 
  | 'completed' | 'failed' | 'archived';

export interface WorkflowVariable {
  name: string;
  type: PortDataType;
  value: unknown;
  secret?: boolean;
}

export interface WorkflowTrigger {
  id: string;
  type: 'manual' | 'schedule' | 'webhook' | 'event';
  config: Record<string, unknown>;
  enabled: boolean;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  version: string;
  status: WorkflowStatus;
  
  // Graph
  nodes: FlowNode[];
  edges: FlowEdge[];
  
  // Viewport
  viewport: {
    x: number;
    y: number;
    zoom: number;
  };
  
  // Configuration
  variables: WorkflowVariable[];
  triggers: WorkflowTrigger[];
  settings: WorkflowSettings;
  
  // Metadata
  tags: string[];
  folder?: string;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  
  // Stats
  stats?: {
    executions: number;
    successRate: number;
    avgDuration: number;
    totalCost: number;
  };
}

export interface WorkflowSettings {
  timeout: number;
  retryPolicy: {
    maxRetries: number;
    backoffMultiplier: number;
  };
  errorHandling: 'stop' | 'continue' | 'fallback';
  logging: 'none' | 'minimal' | 'full';
  costLimit?: number;
}

// ============================================================
// Execution
// ============================================================

export type ExecutionStatus = 
  | 'pending' | 'running' | 'success' | 'failed' | 'cancelled';

export interface ExecutionStep {
  nodeId: string;
  nodeName: string;
  status: ExecutionStatus;
  startedAt?: string;
  completedAt?: string;
  duration?: number;
  input?: unknown;
  output?: unknown;
  error?: string;
  tokenUsage?: number;
  cost?: number;
}

export interface Execution {
  id: string;
  workflowId: string;
  status: ExecutionStatus;
  triggeredBy: 'manual' | 'schedule' | 'webhook' | 'api';
  
  // Timing
  startedAt: string;
  completedAt?: string;
  duration?: number;
  
  // Data
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
  
  // Steps
  steps: ExecutionStep[];
  currentStep?: string;
  
  // Metrics
  totalTokens?: number;
  totalCost?: number;
  
  // Error
  error?: string;
}

// ============================================================
// UI State
// ============================================================

export interface CanvasSettings {
  snapToGrid: boolean;
  gridSize: number;
  showMinimap: boolean;
  showGrid: boolean;
  connectionMode: 'strict' | 'loose';
  panOnDrag: boolean;
  zoomOnScroll: boolean;
  fitViewOnInit: boolean;
}

export interface UIState {
  theme: 'light' | 'dark' | 'system';
  sidebarOpen: boolean;
  sidebarTab: 'nodes' | 'properties' | 'execution' | 'history';
  inspectorOpen: boolean;
  minimapVisible: boolean;
  
  // Selection
  selectedNodes: string[];
  selectedEdges: string[];
  
  // Modes
  isEditing: boolean;
  isExecuting: boolean;
  isDebugging: boolean;
  
  // Debug
  breakpoints: string[];
  currentDebugStep?: string;
}

// ============================================================
// Node Definition (for Node Library)
// ============================================================

export interface NodeDefinition {
  type: FlowNodeType;
  category: NodeCategory;
  name: string;
  description: string;
  icon: string;
  color: string;
  
  // Ports
  defaultInputs: Omit<Port, 'id'>[];
  defaultOutputs: Omit<Port, 'id'>[];
  
  // Config schema
  configSchema: Record<string, {
    type: 'string' | 'number' | 'boolean' | 'select' | 'code' | 'json';
    label: string;
    default?: unknown;
    options?: { value: string; label: string }[];
    required?: boolean;
    placeholder?: string;
  }>;
  
  // Documentation
  docs?: string;
  examples?: string[];
}

// ============================================================
// History (for Undo/Redo)
// ============================================================

export interface HistoryEntry {
  id: string;
  timestamp: number;
  action: string;
  description: string;
  nodes: FlowNode[];
  edges: FlowEdge[];
}
