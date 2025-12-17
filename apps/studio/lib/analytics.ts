// Analytics and metrics tracking for agents
// Simula tracking (em produção, integraria com backend real)

export interface AgentMetrics {
  agentName: string;
  executions: number;
  successRate: number;
  avgResponseTime: number; // segundos
  totalTokens: number;
  totalCost: number; // USD
  lastExecution?: Date;
  trending: "up" | "down" | "stable";
}

export interface ExecutionMetrics {
  id: string;
  agentName: string;
  timestamp: Date;
  duration: number; // segundos
  tokens: number;
  cost: number;
  success: boolean;
  userRating?: number; // 1-5
  feedback?: string;
}

export interface SystemMetrics {
  totalExecutions: number;
  totalAgents: number;
  totalUsers: number;
  avgSuccessRate: number;
  totalCost: number;
  costTrend: number; // % mudança
  executionTrend: number; // % mudança
}

// Storage keys
const METRICS_KEY = "agno_agent_metrics";
const EXECUTIONS_KEY = "agno_executions";
const SYSTEM_KEY = "agno_system_metrics";

// Obter métricas de um agente
export function getAgentMetrics(agentName: string): AgentMetrics | null {
  if (typeof window === "undefined") return null;
  
  const stored = localStorage.getItem(METRICS_KEY);
  if (!stored) return null;
  
  const metrics: Record<string, AgentMetrics> = JSON.parse(stored);
  return metrics[agentName] || null;
}

// Obter métricas de todos os agentes
export function getAllAgentMetrics(): AgentMetrics[] {
  if (typeof window === "undefined") return [];
  
  const stored = localStorage.getItem(METRICS_KEY);
  if (!stored) return [];
  
  const metrics: Record<string, AgentMetrics> = JSON.parse(stored);
  return Object.values(metrics);
}

// Registrar execução
export function trackExecution(execution: Omit<ExecutionMetrics, "id" | "timestamp">): void {
  if (typeof window === "undefined") return;
  
  const id = `exec_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
  const newExecution: ExecutionMetrics = {
    ...execution,
    id,
    timestamp: new Date(),
  };
  
  // Salvar execução
  const executions = getExecutions();
  executions.push(newExecution);
  localStorage.setItem(EXECUTIONS_KEY, JSON.stringify(executions));
  
  // Atualizar métricas do agente
  updateAgentMetrics(execution.agentName, newExecution);
  
  // Atualizar métricas do sistema
  updateSystemMetrics(newExecution);
}

// Atualizar métricas do agente
function updateAgentMetrics(agentName: string, execution: ExecutionMetrics): void {
  const stored = localStorage.getItem(METRICS_KEY);
  const metrics: Record<string, AgentMetrics> = stored ? JSON.parse(stored) : {};
  
  if (!metrics[agentName]) {
    metrics[agentName] = {
      agentName,
      executions: 0,
      successRate: 0,
      avgResponseTime: 0,
      totalTokens: 0,
      totalCost: 0,
      trending: "stable",
    };
  }
  
  const current = metrics[agentName];
  const prevExecutions = current.executions;
  const newExecutions = prevExecutions + 1;
  
  // Atualizar métricas
  metrics[agentName] = {
    ...current,
    executions: newExecutions,
    successRate: ((current.successRate * prevExecutions) + (execution.success ? 1 : 0)) / newExecutions,
    avgResponseTime: ((current.avgResponseTime * prevExecutions) + execution.duration) / newExecutions,
    totalTokens: current.totalTokens + execution.tokens,
    totalCost: current.totalCost + execution.cost,
    lastExecution: execution.timestamp,
    trending: calculateTrend(agentName, newExecutions),
  };
  
  localStorage.setItem(METRICS_KEY, JSON.stringify(metrics));
}

// Calcular tendência
function calculateTrend(agentName: string, currentExecutions: number): "up" | "down" | "stable" {
  const executions = getExecutions().filter(e => e.agentName === agentName);
  if (executions.length < 2) return "stable";
  
  const last7Days = executions.filter(e => {
    const daysDiff = (Date.now() - new Date(e.timestamp).getTime()) / (1000 * 60 * 60 * 24);
    return daysDiff <= 7;
  }).length;
  
  const prev7Days = executions.filter(e => {
    const daysDiff = (Date.now() - new Date(e.timestamp).getTime()) / (1000 * 60 * 60 * 24);
    return daysDiff > 7 && daysDiff <= 14;
  }).length;
  
  if (last7Days > prev7Days * 1.1) return "up";
  if (last7Days < prev7Days * 0.9) return "down";
  return "stable";
}

// Obter execuções
export function getExecutions(): ExecutionMetrics[] {
  if (typeof window === "undefined") return [];
  
  const stored = localStorage.getItem(EXECUTIONS_KEY);
  if (!stored) return [];
  
  return JSON.parse(stored).map((e: any) => ({
    ...e,
    timestamp: new Date(e.timestamp),
  }));
}

// Obter execuções por agente
export function getAgentExecutions(agentName: string, limit?: number): ExecutionMetrics[] {
  const executions = getExecutions()
    .filter(e => e.agentName === agentName)
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  
  return limit ? executions.slice(0, limit) : executions;
}

// Atualizar métricas do sistema
function updateSystemMetrics(execution: ExecutionMetrics): void {
  const stored = localStorage.getItem(SYSTEM_KEY);
  const current: SystemMetrics = stored ? JSON.parse(stored) : {
    totalExecutions: 0,
    totalAgents: 0,
    totalUsers: 1,
    avgSuccessRate: 0,
    totalCost: 0,
    costTrend: 0,
    executionTrend: 0,
  };
  
  const prevExecutions = current.totalExecutions;
  const newExecutions = prevExecutions + 1;
  
  const updated: SystemMetrics = {
    ...current,
    totalExecutions: newExecutions,
    totalAgents: getAllAgentMetrics().length,
    avgSuccessRate: ((current.avgSuccessRate * prevExecutions) + (execution.success ? 1 : 0)) / newExecutions,
    totalCost: current.totalCost + execution.cost,
  };
  
  localStorage.setItem(SYSTEM_KEY, JSON.stringify(updated));
}

// Obter métricas do sistema
export function getSystemMetrics(): SystemMetrics {
  if (typeof window === "undefined") {
    return {
      totalExecutions: 0,
      totalAgents: 0,
      totalUsers: 0,
      avgSuccessRate: 0,
      totalCost: 0,
      costTrend: 0,
      executionTrend: 0,
    };
  }
  
  const stored = localStorage.getItem(SYSTEM_KEY);
  if (!stored) {
    return {
      totalExecutions: 0,
      totalAgents: 0,
      totalUsers: 1,
      avgSuccessRate: 0,
      totalCost: 0,
      costTrend: 0,
      executionTrend: 0,
    };
  }
  
  return JSON.parse(stored);
}

// Obter top agentes por métrica
export function getTopAgents(metric: keyof AgentMetrics, limit: number = 5): AgentMetrics[] {
  const allMetrics = getAllAgentMetrics();
  
  return allMetrics
    .sort((a, b) => {
      const aVal = a[metric];
      const bVal = b[metric];
      if (typeof aVal === "number" && typeof bVal === "number") {
        return bVal - aVal;
      }
      return 0;
    })
    .slice(0, limit);
}

// Calcular custo estimado de execução
export function estimateExecutionCost(tokens: number, provider: string, model: string): number {
  // Preços aproximados por 1M tokens (input + output média)
  const pricing: Record<string, Record<string, number>> = {
    openai: {
      "gpt-4.1": 15.0,
      "gpt-4o": 7.5,
      "gpt-4o-mini": 0.60,
    },
    anthropic: {
      "claude-3-5-sonnet-20241022": 6.0,
      "claude-3-opus-20240229": 45.0,
    },
    groq: {
      "llama-3.3-70b-versatile": 0.80,
      "mixtral-8x7b-32768": 0.70,
    },
  };
  
  const pricePerMillion = pricing[provider]?.[model] || 1.0;
  return (tokens / 1_000_000) * pricePerMillion;
}

// Gerar dados de exemplo para desenvolvimento/demo
export function generateSampleData(): void {
  if (typeof window === "undefined") return;
  
  const agents = ["Email Manager", "Market Researcher", "Content Writer", "Data Analyst", "Support Bot"];
  const providers = ["openai", "anthropic", "groq"];
  const models = ["gpt-4o", "claude-3-5-sonnet-20241022", "llama-3.3-70b-versatile"];
  
  // Gerar 50 execuções de exemplo
  for (let i = 0; i < 50; i++) {
    const agentName = agents[Math.floor(Math.random() * agents.length)];
    const provider = providers[Math.floor(Math.random() * providers.length)];
    const model = models[Math.floor(Math.random() * models.length)];
    const tokens = Math.floor(Math.random() * 5000) + 500;
    const duration = Math.random() * 10 + 1;
    const success = Math.random() > 0.1; // 90% success rate
    
    trackExecution({
      agentName,
      duration,
      tokens,
      cost: estimateExecutionCost(tokens, provider, model),
      success,
      userRating: success ? (Math.random() > 0.3 ? 5 : 4) : undefined,
    });
  }
}

// Limpar dados de analytics
export function clearAnalytics(): void {
  if (typeof window === "undefined") return;
  
  localStorage.removeItem(METRICS_KEY);
  localStorage.removeItem(EXECUTIONS_KEY);
  localStorage.removeItem(SYSTEM_KEY);
}
