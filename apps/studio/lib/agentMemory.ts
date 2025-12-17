// Sistema de memória de longo prazo para agentes
// Armazena contexto, preferências e aprendizados de cada agente

export interface MemoryEntry {
  id: string;
  agentName: string;
  type: "context" | "preference" | "fact" | "interaction";
  content: string;
  timestamp: Date;
  importance: 1 | 2 | 3 | 4 | 5; // 5 = mais importante
  tags: string[];
  metadata?: Record<string, any>;
}

export interface AgentMemory {
  agentName: string;
  entries: MemoryEntry[];
  lastUpdated: Date;
  totalEntries: number;
}

const MEMORY_KEY = "agno_agent_memory";
const MAX_ENTRIES_PER_AGENT = 500; // Limite para performance

// Obter memória de um agente
export function getAgentMemory(agentName: string): AgentMemory | null {
  if (typeof window === "undefined") return null;
  
  const stored = localStorage.getItem(MEMORY_KEY);
  if (!stored) return null;
  
  const allMemories: Record<string, AgentMemory> = JSON.parse(stored);
  const memory = allMemories[agentName];
  
  if (!memory) return null;
  
  // Converter timestamps
  return {
    ...memory,
    lastUpdated: new Date(memory.lastUpdated),
    entries: memory.entries.map(e => ({
      ...e,
      timestamp: new Date(e.timestamp),
    })),
  };
}

// Adicionar entrada na memória
export function addMemoryEntry(
  agentName: string,
  type: MemoryEntry["type"],
  content: string,
  importance: MemoryEntry["importance"] = 3,
  tags: string[] = [],
  metadata?: Record<string, any>
): void {
  if (typeof window === "undefined") return;
  
  const stored = localStorage.getItem(MEMORY_KEY);
  const allMemories: Record<string, AgentMemory> = stored ? JSON.parse(stored) : {};
  
  if (!allMemories[agentName]) {
    allMemories[agentName] = {
      agentName,
      entries: [],
      lastUpdated: new Date(),
      totalEntries: 0,
    };
  }
  
  const memory = allMemories[agentName];
  
  // Criar nova entrada
  const entry: MemoryEntry = {
    id: `mem_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    agentName,
    type,
    content,
    timestamp: new Date(),
    importance,
    tags,
    metadata,
  };
  
  // Adicionar entrada
  memory.entries.unshift(entry);
  memory.totalEntries++;
  memory.lastUpdated = new Date();
  
  // Limpar entradas antigas se exceder limite (mantém as mais importantes)
  if (memory.entries.length > MAX_ENTRIES_PER_AGENT) {
    // Ordenar por importância e timestamp
    memory.entries.sort((a, b) => {
      if (a.importance !== b.importance) {
        return b.importance - a.importance;
      }
      return b.timestamp.getTime() - a.timestamp.getTime();
    });
    
    // Manter apenas MAX_ENTRIES_PER_AGENT
    memory.entries = memory.entries.slice(0, MAX_ENTRIES_PER_AGENT);
  }
  
  allMemories[agentName] = memory;
  localStorage.setItem(MEMORY_KEY, JSON.stringify(allMemories));
}

// Buscar memórias por tipo
export function getMemoriesByType(
  agentName: string,
  type: MemoryEntry["type"]
): MemoryEntry[] {
  const memory = getAgentMemory(agentName);
  if (!memory) return [];
  
  return memory.entries.filter(e => e.type === type);
}

// Buscar memórias por tags
export function getMemoriesByTags(
  agentName: string,
  tags: string[]
): MemoryEntry[] {
  const memory = getAgentMemory(agentName);
  if (!memory) return [];
  
  return memory.entries.filter(e => 
    tags.some(tag => e.tags.includes(tag))
  );
}

// Buscar memórias por texto
export function searchMemories(
  agentName: string,
  query: string
): MemoryEntry[] {
  const memory = getAgentMemory(agentName);
  if (!memory) return [];
  
  const lowerQuery = query.toLowerCase();
  return memory.entries.filter(e =>
    e.content.toLowerCase().includes(lowerQuery) ||
    e.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
  );
}

// Obter memórias recentes
export function getRecentMemories(
  agentName: string,
  limit: number = 10
): MemoryEntry[] {
  const memory = getAgentMemory(agentName);
  if (!memory) return [];
  
  return memory.entries
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    .slice(0, limit);
}

// Obter memórias importantes
export function getImportantMemories(
  agentName: string,
  minImportance: number = 4
): MemoryEntry[] {
  const memory = getAgentMemory(agentName);
  if (!memory) return [];
  
  return memory.entries.filter(e => e.importance >= minImportance);
}

// Atualizar importância de uma memória
export function updateMemoryImportance(
  agentName: string,
  entryId: string,
  newImportance: MemoryEntry["importance"]
): boolean {
  if (typeof window === "undefined") return false;
  
  const stored = localStorage.getItem(MEMORY_KEY);
  if (!stored) return false;
  
  const allMemories: Record<string, AgentMemory> = JSON.parse(stored);
  const memory = allMemories[agentName];
  
  if (!memory) return false;
  
  const entry = memory.entries.find(e => e.id === entryId);
  if (!entry) return false;
  
  entry.importance = newImportance;
  memory.lastUpdated = new Date();
  
  localStorage.setItem(MEMORY_KEY, JSON.stringify(allMemories));
  return true;
}

// Deletar uma memória
export function deleteMemory(agentName: string, entryId: string): boolean {
  if (typeof window === "undefined") return false;
  
  const stored = localStorage.getItem(MEMORY_KEY);
  if (!stored) return false;
  
  const allMemories: Record<string, AgentMemory> = JSON.parse(stored);
  const memory = allMemories[agentName];
  
  if (!memory) return false;
  
  const index = memory.entries.findIndex(e => e.id === entryId);
  if (index === -1) return false;
  
  memory.entries.splice(index, 1);
  memory.lastUpdated = new Date();
  
  localStorage.setItem(MEMORY_KEY, JSON.stringify(allMemories));
  return true;
}

// Limpar memória de um agente
export function clearAgentMemory(agentName: string): void {
  if (typeof window === "undefined") return;
  
  const stored = localStorage.getItem(MEMORY_KEY);
  if (!stored) return;
  
  const allMemories: Record<string, AgentMemory> = JSON.parse(stored);
  delete allMemories[agentName];
  
  localStorage.setItem(MEMORY_KEY, JSON.stringify(allMemories));
}

// Obter resumo da memória
export function getMemorySummary(agentName: string): {
  total: number;
  byType: Record<string, number>;
  byImportance: Record<number, number>;
  topTags: { tag: string; count: number }[];
} | null {
  const memory = getAgentMemory(agentName);
  if (!memory) return null;
  
  const byType: Record<string, number> = {};
  const byImportance: Record<number, number> = {};
  const tagCounts: Record<string, number> = {};
  
  memory.entries.forEach(entry => {
    // Por tipo
    byType[entry.type] = (byType[entry.type] || 0) + 1;
    
    // Por importância
    byImportance[entry.importance] = (byImportance[entry.importance] || 0) + 1;
    
    // Contar tags
    entry.tags.forEach(tag => {
      tagCounts[tag] = (tagCounts[tag] || 0) + 1;
    });
  });
  
  // Top tags
  const topTags = Object.entries(tagCounts)
    .map(([tag, count]) => ({ tag, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);
  
  return {
    total: memory.entries.length,
    byType,
    byImportance,
    topTags,
  };
}

// Criar contexto para prompt (últimas N memórias relevantes)
export function buildContextForPrompt(
  agentName: string,
  maxEntries: number = 5
): string {
  const memory = getAgentMemory(agentName);
  if (!memory || memory.entries.length === 0) {
    return "";
  }
  
  // Pegar memórias importantes e recentes
  const important = memory.entries
    .filter(e => e.importance >= 4)
    .slice(0, maxEntries);
  
  const recent = memory.entries
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    .slice(0, maxEntries);
  
  // Combinar e remover duplicatas
  const combined = [...important];
  recent.forEach(r => {
    if (!combined.find(c => c.id === r.id)) {
      combined.push(r);
    }
  });
  
  if (combined.length === 0) return "";
  
  // Construir contexto
  let context = "\n\n=== Contexto da Memória ===\n";
  combined.slice(0, maxEntries).forEach((entry, idx) => {
    context += `${idx + 1}. [${entry.type}] ${entry.content}\n`;
  });
  context += "=== Fim do Contexto ===\n\n";
  
  return context;
}

// Exportar memória de um agente (para backup)
export function exportAgentMemory(agentName: string): string | null {
  const memory = getAgentMemory(agentName);
  if (!memory) return null;
  
  return JSON.stringify(memory, null, 2);
}

// Importar memória de um agente (de backup)
export function importAgentMemory(jsonData: string): boolean {
  if (typeof window === "undefined") return false;
  
  try {
    const memory: AgentMemory = JSON.parse(jsonData);
    
    // Validar estrutura
    if (!memory.agentName || !Array.isArray(memory.entries)) {
      return false;
    }
    
    const stored = localStorage.getItem(MEMORY_KEY);
    const allMemories: Record<string, AgentMemory> = stored ? JSON.parse(stored) : {};
    
    allMemories[memory.agentName] = memory;
    localStorage.setItem(MEMORY_KEY, JSON.stringify(allMemories));
    
    return true;
  } catch {
    return false;
  }
}

// Gerar dados de exemplo
export function generateSampleMemory(agentName: string): void {
  const sampleEntries = [
    { type: "preference" as const, content: "Usuário prefere respostas concisas e diretas", importance: 5, tags: ["comunicacao", "estilo"] },
    { type: "fact" as const, content: "Empresa do usuário: Tech Solutions Inc.", importance: 4, tags: ["empresa", "contexto"] },
    { type: "context" as const, content: "Último projeto: Migração de sistema legado para cloud", importance: 4, tags: ["projeto", "tech"] },
    { type: "interaction" as const, content: "Usuário perguntou sobre melhores práticas de segurança", importance: 3, tags: ["seguranca", "consulta"] },
    { type: "preference" as const, content: "Horário preferido: 9h-18h", importance: 3, tags: ["horario", "disponibilidade"] },
    { type: "fact" as const, content: "Tech stack principal: React, Node.js, PostgreSQL", importance: 4, tags: ["tech", "stack"] },
    { type: "context" as const, content: "Time de 5 desenvolvedores", importance: 3, tags: ["time", "recursos"] },
    { type: "interaction" as const, content: "Solicitou análise de performance", importance: 3, tags: ["performance", "analise"] },
  ];
  
  sampleEntries.forEach(entry => {
    addMemoryEntry(
      agentName,
      entry.type,
      entry.content,
      entry.importance as MemoryEntry["importance"],
      entry.tags
    );
  });
}
