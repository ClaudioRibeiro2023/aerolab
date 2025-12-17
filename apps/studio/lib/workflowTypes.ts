/**
 * Tipos TypeScript para Workflows
 */

// Status de execução
export type ExecutionStatus = 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
export type WorkflowStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';

// Tipos de steps
export type StepType = 
  | 'agent'
  | 'condition' 
  | 'parallel'
  | 'loop'
  | 'multi_agent'
  | 'action'
  | 'wait'
  | 'start'
  | 'end';

// Padrões de orquestração multi-agente
export type OrchestrationPattern = 
  | 'sequential'
  | 'hierarchical'
  | 'collaborative'
  | 'debate'
  | 'router'
  | 'voting'
  | 'chain';

// Estratégias de join paralelo
export type JoinStrategy = 'all' | 'any' | 'first';

// Tipos de loop
export type LoopType = 'for_each' | 'while' | 'until' | 'map' | 'times';

// Tipos de trigger
export type TriggerType = 'manual' | 'webhook' | 'schedule' | 'event';

// Definição de step
export interface WorkflowStep {
  id: string;
  type: StepType;
  name: string;
  description?: string;
  config: StepConfig;
  next_step?: string;
  on_error?: string;
  retry_policy?: RetryPolicy;
  timeout_seconds?: number;
  position?: { x: number; y: number };
}

// Configuração de step (por tipo)
export interface StepConfig {
  // Agent
  agent_id?: string;
  prompt?: string;
  output_variable?: string;
  model_override?: string;
  temperature?: number;
  max_tokens?: number;
  tools?: string[];
  use_rag?: boolean;
  
  // Condition
  branches?: ConditionBranch[];
  default_step?: string;
  switch_variable?: string;
  cases?: Record<string, string>;
  
  // Parallel
  parallel_branches?: ParallelBranch[];
  join_strategy?: JoinStrategy;
  max_concurrent?: number;
  
  // Loop
  loop_type?: LoopType;
  items_variable?: string;
  item_variable?: string;
  condition?: string;
  times?: number;
  step_config?: StepConfig;
  
  // Multi-agent
  pattern?: OrchestrationPattern;
  agents?: AgentConfig[];
  manager_agent?: AgentConfig;
  task?: string;
  max_rounds?: number;
  
  // Action
  action_type?: 'http' | 'db' | 'email' | 'webhook';
  url?: string;
  method?: string;
  headers?: Record<string, string>;
  body?: string;
  
  // Genérico
  [key: string]: unknown;
}

// Branch condicional
export interface ConditionBranch {
  condition: string;
  next_step: string;
  label?: string;
}

// Branch paralelo
export interface ParallelBranch {
  id: string;
  step_type: StepType;
  config: StepConfig;
}

// Configuração de agente (para multi-agent)
export interface AgentConfig {
  id: string;
  agent_id: string;
  role?: string;
  goal?: string;
  prompt_template?: string;
  backstory?: string;
  tools?: string[];
  allow_delegation?: boolean;
}

// Política de retry
export interface RetryPolicy {
  max_retries: number;
  initial_delay_ms: number;
  max_delay_ms: number;
  backoff_multiplier: number;
}

// Definição de workflow
export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  version: string;
  steps: WorkflowStep[];
  start_step?: string;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  enabled: boolean;
  tags: string[];
}

// Configuração de trigger
export interface TriggerConfig {
  id: string;
  name: string;
  workflow_id: string;
  trigger_type: TriggerType;
  enabled: boolean;
  config: {
    // Webhook
    path?: string;
    methods?: string[];
    require_signature?: boolean;
    
    // Schedule
    cron?: string;
    timezone?: string;
    
    // Event
    event_types?: string[];
    data_conditions?: Record<string, unknown>;
  };
}

// Resultado de execução
export interface ExecutionResult {
  execution_id: string;
  workflow_id: string;
  status: ExecutionStatus;
  outputs: Record<string, unknown>;
  step_results: StepResult[];
  started_at?: string;
  completed_at?: string;
  duration_ms: number;
  error?: string;
}

// Resultado de step
export interface StepResult {
  step_id: string;
  status: ExecutionStatus;
  output?: unknown;
  error?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms: number;
  retry_count: number;
}

// Template de workflow
export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  tags: string[];
  definition: Partial<WorkflowDefinition>;
  preview_image?: string;
}

// Sugestão de step
export interface StepSuggestion {
  step_type: StepType;
  name: string;
  description: string;
  config: StepConfig;
  confidence: number;
  reason: string;
}

// Recomendação de otimização
export interface OptimizationRecommendation {
  id: string;
  type: 'performance' | 'cost' | 'reliability' | 'parallelization' | 'caching';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  impact: string;
  steps_affected: string[];
  estimated_improvement?: number;
  implementation_effort: 'low' | 'medium' | 'high';
}

// Versão de workflow
export interface WorkflowVersion {
  version: string;
  workflow_id: string;
  status: 'draft' | 'active' | 'deprecated' | 'archived';
  created_at: string;
  created_by: string;
  message: string;
  executions_count: number;
  success_rate: number;
}

// Conexão no builder visual
export interface WorkflowConnection {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
  type?: 'default' | 'success' | 'error';
}

// Node no builder visual
export interface WorkflowNode {
  id: string;
  type: StepType;
  position: { x: number; y: number };
  data: {
    step: WorkflowStep;
    onEdit?: (step: WorkflowStep) => void;
    onDelete?: (id: string) => void;
  };
}

// Presets de schedule
export const SCHEDULE_PRESETS: Record<string, string> = {
  every_minute: '* * * * *',
  every_5_minutes: '*/5 * * * *',
  every_15_minutes: '*/15 * * * *',
  every_30_minutes: '*/30 * * * *',
  hourly: '0 * * * *',
  daily_midnight: '0 0 * * *',
  daily_morning: '0 8 * * *',
  weekdays_morning: '0 8 * * 1-5',
  weekly_monday: '0 0 * * 1',
  monthly_first: '0 0 1 * *',
};

// Step type metadata
export const STEP_TYPE_META: Record<StepType, {
  label: string;
  description: string;
  icon: string;
  color: string;
}> = {
  start: {
    label: 'Start',
    description: 'Início do workflow',
    icon: 'Play',
    color: '#10b981'
  },
  end: {
    label: 'End',
    description: 'Fim do workflow',
    icon: 'Square',
    color: '#ef4444'
  },
  agent: {
    label: 'Agent',
    description: 'Executa um agente LLM',
    icon: 'Bot',
    color: '#3b82f6'
  },
  condition: {
    label: 'Condition',
    description: 'Branching condicional',
    icon: 'GitBranch',
    color: '#f59e0b'
  },
  parallel: {
    label: 'Parallel',
    description: 'Execução paralela',
    icon: 'GitFork',
    color: '#8b5cf6'
  },
  loop: {
    label: 'Loop',
    description: 'Iteração',
    icon: 'Repeat',
    color: '#06b6d4'
  },
  multi_agent: {
    label: 'Multi-Agent',
    description: 'Orquestra múltiplos agentes',
    icon: 'Users',
    color: '#ec4899'
  },
  action: {
    label: 'Action',
    description: 'Ação externa (HTTP, DB)',
    icon: 'Zap',
    color: '#84cc16'
  },
  wait: {
    label: 'Wait',
    description: 'Aguarda evento ou tempo',
    icon: 'Clock',
    color: '#6b7280'
  }
};

// Orchestration pattern metadata
export const ORCHESTRATION_PATTERN_META: Record<OrchestrationPattern, {
  label: string;
  description: string;
}> = {
  sequential: {
    label: 'Sequential (Crew)',
    description: 'Agentes executam em sequência, passando output'
  },
  hierarchical: {
    label: 'Hierarchical',
    description: 'Manager coordena workers'
  },
  collaborative: {
    label: 'Collaborative',
    description: 'Agentes colaboram em múltiplas rodadas'
  },
  debate: {
    label: 'Debate',
    description: 'Agentes debatem até consenso'
  },
  router: {
    label: 'Router',
    description: 'Roteia para o melhor agente'
  },
  voting: {
    label: 'Voting',
    description: 'Todos respondem, voto decide'
  },
  chain: {
    label: 'Chain',
    description: 'Output de um é input do próximo'
  }
};
