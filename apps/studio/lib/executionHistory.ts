/**
 * Utilitário para gerenciar histórico de execuções de agentes e teams.
 * Persiste no localStorage.
 */

export interface ExecutionRecord {
  id: string;
  type: "agent" | "team";
  name: string;
  prompt: string;
  result: string;
  timestamp: string;
  duration: number;
  status: "success" | "error";
}

const STORAGE_KEY = "agno_execution_history";
const MAX_RECORDS = 100;

/**
 * Gera um ID único para o registro
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Obtém todo o histórico de execuções
 */
export function getHistory(): ExecutionRecord[] {
  if (typeof window === "undefined") return [];
  
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    return JSON.parse(stored);
  } catch {
    return [];
  }
}

/**
 * Obtém histórico filtrado por tipo e/ou nome
 */
export function getHistoryByFilter(filter: {
  type?: "agent" | "team";
  name?: string;
}): ExecutionRecord[] {
  const history = getHistory();
  
  return history.filter(record => {
    if (filter.type && record.type !== filter.type) return false;
    if (filter.name && record.name !== filter.name) return false;
    return true;
  });
}

/**
 * Adiciona um novo registro ao histórico
 */
export function addToHistory(record: Omit<ExecutionRecord, "id">): ExecutionRecord {
  const history = getHistory();
  
  const newRecord: ExecutionRecord = {
    ...record,
    id: generateId(),
  };
  
  // Adicionar no início (mais recentes primeiro)
  history.unshift(newRecord);
  
  // Limitar tamanho
  if (history.length > MAX_RECORDS) {
    history.splice(MAX_RECORDS);
  }
  
  // Salvar
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  } catch {
    // Ignorar erros de storage
  }
  
  return newRecord;
}

/**
 * Remove um registro do histórico
 */
export function removeFromHistory(id: string): boolean {
  const history = getHistory();
  const index = history.findIndex(r => r.id === id);
  
  if (index === -1) return false;
  
  history.splice(index, 1);
  
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  } catch {
    // Ignorar erros de storage
  }
  
  return true;
}

/**
 * Limpa todo o histórico
 */
export function clearHistory(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignorar erros de storage
  }
}

/**
 * Limpa histórico por tipo e/ou nome
 */
export function clearHistoryByFilter(filter: {
  type?: "agent" | "team";
  name?: string;
}): void {
  const history = getHistory();
  
  const filtered = history.filter(record => {
    if (filter.type && record.type === filter.type) {
      if (!filter.name || record.name === filter.name) {
        return false; // Remove este
      }
    }
    return true;
  });
  
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
  } catch {
    // Ignorar erros de storage
  }
}

/**
 * Obtém estatísticas do histórico
 */
export function getHistoryStats(filter?: {
  type?: "agent" | "team";
  name?: string;
}): {
  total: number;
  success: number;
  error: number;
  successRate: number;
  avgDuration: number;
} {
  const history = filter ? getHistoryByFilter(filter) : getHistory();
  
  if (history.length === 0) {
    return { total: 0, success: 0, error: 0, successRate: 0, avgDuration: 0 };
  }
  
  const success = history.filter(r => r.status === "success").length;
  const error = history.filter(r => r.status === "error").length;
  const totalDuration = history.reduce((acc, r) => acc + r.duration, 0);
  
  return {
    total: history.length,
    success,
    error,
    successRate: Math.round((success / history.length) * 100),
    avgDuration: Number((totalDuration / history.length).toFixed(1)),
  };
}
