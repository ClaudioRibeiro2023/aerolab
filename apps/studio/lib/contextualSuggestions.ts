"use client";

/**
 * Sistema de sugestões contextuais baseadas em histórico
 * 
 * Analisa o histórico de interações para sugerir prompts relevantes
 */

const STORAGE_KEY = "agno_prompt_history";
const MAX_HISTORY = 100;
const MAX_SUGGESTIONS = 5;

interface PromptEntry {
  prompt: string;
  agentName: string;
  timestamp: number;
  successful: boolean;
  tags?: string[];
}

interface Suggestion {
  text: string;
  source: "history" | "template" | "popular";
  confidence: number;
  agentName?: string;
}

// Templates de prompts comuns por categoria
const PROMPT_TEMPLATES: Record<string, string[]> = {
  general: [
    "Resuma o seguinte texto:",
    "Explique de forma simples:",
    "Quais são os principais pontos de:",
    "Compare e contraste:",
    "Liste os prós e contras de:",
  ],
  analysis: [
    "Analise os dados a seguir:",
    "Identifique padrões em:",
    "Faça uma análise SWOT de:",
    "Avalie os riscos de:",
    "Projete tendências para:",
  ],
  writing: [
    "Escreva um email profissional sobre:",
    "Crie um resumo executivo de:",
    "Redija um relatório sobre:",
    "Elabore uma proposta para:",
    "Revise e melhore o texto:",
  ],
  code: [
    "Revise este código:",
    "Otimize a função:",
    "Adicione tratamento de erros em:",
    "Escreva testes para:",
    "Documente a função:",
  ],
  research: [
    "Pesquise sobre:",
    "Encontre informações sobre:",
    "Quais são as últimas novidades em:",
    "Compare as opções de:",
    "Faça um levantamento de:",
  ],
};

/**
 * Salva um prompt no histórico
 */
export function savePromptToHistory(entry: Omit<PromptEntry, "timestamp">): void {
  if (typeof window === "undefined") return;
  
  const history = getPromptHistory();
  
  // Evitar duplicatas recentes
  const isDuplicate = history.some(
    h => h.prompt === entry.prompt && Date.now() - h.timestamp < 60000
  );
  
  if (isDuplicate) return;
  
  history.unshift({
    ...entry,
    timestamp: Date.now(),
  });
  
  // Limitar tamanho
  const trimmed = history.slice(0, MAX_HISTORY);
  
  localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
}

/**
 * Obtém o histórico de prompts
 */
export function getPromptHistory(): PromptEntry[] {
  if (typeof window === "undefined") return [];
  
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

/**
 * Gera sugestões baseadas no contexto
 */
export function getSuggestions(
  agentName?: string,
  currentInput?: string
): Suggestion[] {
  const history = getPromptHistory();
  const suggestions: Suggestion[] = [];
  
  // 1. Sugestões do histórico
  const relevantHistory = history
    .filter(h => {
      // Filtrar por agente se especificado
      if (agentName && h.agentName !== agentName) return false;
      // Filtrar por sucesso
      if (!h.successful) return false;
      // Filtrar por texto parcial
      if (currentInput && !h.prompt.toLowerCase().includes(currentInput.toLowerCase())) {
        return false;
      }
      return true;
    })
    .slice(0, 3);
  
  for (const h of relevantHistory) {
    suggestions.push({
      text: h.prompt,
      source: "history",
      confidence: 0.9,
      agentName: h.agentName,
    });
  }
  
  // 2. Sugestões de templates
  if (currentInput && currentInput.length > 2) {
    const input = currentInput.toLowerCase();
    
    for (const [, templates] of Object.entries(PROMPT_TEMPLATES)) {
      for (const template of templates) {
        if (template.toLowerCase().includes(input)) {
          suggestions.push({
            text: template,
            source: "template",
            confidence: 0.7,
          });
        }
      }
    }
  }
  
  // 3. Templates populares se não houver input
  if (!currentInput && suggestions.length < MAX_SUGGESTIONS) {
    const popular = [
      ...PROMPT_TEMPLATES.general.slice(0, 2),
      ...PROMPT_TEMPLATES.analysis.slice(0, 1),
    ];
    
    for (const p of popular) {
      if (!suggestions.some(s => s.text === p)) {
        suggestions.push({
          text: p,
          source: "popular",
          confidence: 0.5,
        });
      }
    }
  }
  
  // Ordenar por confiança e limitar
  return suggestions
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, MAX_SUGGESTIONS);
}

/**
 * Obtém prompts recentes por agente
 */
export function getRecentPromptsByAgent(agentName: string, limit = 5): string[] {
  const history = getPromptHistory();
  
  return history
    .filter(h => h.agentName === agentName && h.successful)
    .slice(0, limit)
    .map(h => h.prompt);
}

/**
 * Detecta categoria do prompt
 */
export function detectPromptCategory(prompt: string): string {
  const lowerPrompt = prompt.toLowerCase();
  
  if (lowerPrompt.includes("código") || lowerPrompt.includes("função") || lowerPrompt.includes("bug")) {
    return "code";
  }
  if (lowerPrompt.includes("analise") || lowerPrompt.includes("dados") || lowerPrompt.includes("swot")) {
    return "analysis";
  }
  if (lowerPrompt.includes("escreva") || lowerPrompt.includes("email") || lowerPrompt.includes("relatório")) {
    return "writing";
  }
  if (lowerPrompt.includes("pesquise") || lowerPrompt.includes("encontre") || lowerPrompt.includes("busque")) {
    return "research";
  }
  
  return "general";
}

/**
 * Limpa o histórico
 */
export function clearPromptHistory(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}

/**
 * Estatísticas do histórico
 */
export function getHistoryStats(): {
  total: number;
  successful: number;
  byAgent: Record<string, number>;
} {
  const history = getPromptHistory();
  
  const byAgent: Record<string, number> = {};
  let successful = 0;
  
  for (const entry of history) {
    if (entry.successful) successful++;
    byAgent[entry.agentName] = (byAgent[entry.agentName] || 0) + 1;
  }
  
  return {
    total: history.length,
    successful,
    byAgent,
  };
}
