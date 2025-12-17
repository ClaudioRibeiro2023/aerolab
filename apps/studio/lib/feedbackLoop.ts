// Sistema de feedback loop automático
// Ajusta instruções dos agentes baseado no feedback dos usuários

export interface FeedbackRecord {
  id: string;
  agentName: string;
  timestamp: Date;
  rating: number; // 1-5
  issues: string[];
  suggestion?: string;
  prompt: string;
  response: string;
  currentInstructions: string[];
}

export interface InstructionImprovement {
  original: string;
  suggested: string;
  reason: string;
  confidence: number; // 0-1
  supportingFeedback: number; // Quantidade de feedbacks que suportam esta melhoria
}

export interface AgentInsights {
  agentName: string;
  totalFeedbacks: number;
  avgRating: number;
  commonIssues: { issue: string; count: number }[];
  suggestedImprovements: InstructionImprovement[];
  strengthAreas: string[]; // Áreas onde o agente vai bem
  improvementAreas: string[]; // Áreas que precisam melhorar
}

const FEEDBACK_KEY = "agno_feedback_records";
const MIN_FEEDBACKS_FOR_SUGGESTION = 3; // Mínimo de feedbacks para sugerir mudança

// Salvar feedback
export function saveFeedback(
  agentName: string,
  rating: number,
  issues: string[],
  prompt: string,
  response: string,
  currentInstructions: string[],
  suggestion?: string
): void {
  if (typeof window === "undefined") return;
  
  const stored = localStorage.getItem(FEEDBACK_KEY);
  const allFeedback: Record<string, FeedbackRecord[]> = stored ? JSON.parse(stored) : {};
  
  if (!allFeedback[agentName]) {
    allFeedback[agentName] = [];
  }
  
  const record: FeedbackRecord = {
    id: `fb_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    agentName,
    timestamp: new Date(),
    rating,
    issues,
    suggestion,
    prompt,
    response,
    currentInstructions,
  };
  
  allFeedback[agentName].push(record);
  localStorage.setItem(FEEDBACK_KEY, JSON.stringify(allFeedback));
}

// Obter feedbacks de um agente
export function getAgentFeedbacks(agentName: string): FeedbackRecord[] {
  if (typeof window === "undefined") return [];
  
  const stored = localStorage.getItem(FEEDBACK_KEY);
  if (!stored) return [];
  
  const allFeedback: Record<string, FeedbackRecord[]> = JSON.parse(stored);
  const feedbacks = allFeedback[agentName] || [];
  
  return feedbacks.map(f => ({
    ...f,
    timestamp: new Date(f.timestamp),
  }));
}

// Analisar feedbacks e gerar insights
export function analyzeAgentFeedbacks(agentName: string): AgentInsights {
  const feedbacks = getAgentFeedbacks(agentName);
  
  if (feedbacks.length === 0) {
    return {
      agentName,
      totalFeedbacks: 0,
      avgRating: 0,
      commonIssues: [],
      suggestedImprovements: [],
      strengthAreas: [],
      improvementAreas: [],
    };
  }
  
  // Calcular média de rating
  const avgRating = feedbacks.reduce((sum, f) => sum + f.rating, 0) / feedbacks.length;
  
  // Contar issues comuns
  const issueCount: Record<string, number> = {};
  feedbacks.forEach(f => {
    f.issues.forEach(issue => {
      issueCount[issue] = (issueCount[issue] || 0) + 1;
    });
  });
  
  const commonIssues = Object.entries(issueCount)
    .map(([issue, count]) => ({ issue, count }))
    .sort((a, b) => b.count - a.count);
  
  // Identificar áreas fortes (ratings altos)
  const highRatedFeedbacks = feedbacks.filter(f => f.rating >= 4);
  const strengthAreas = identifyStrengths(highRatedFeedbacks);
  
  // Identificar áreas de melhoria (ratings baixos)
  const lowRatedFeedbacks = feedbacks.filter(f => f.rating <= 2);
  const improvementAreas = identifyImprovements(lowRatedFeedbacks, commonIssues);
  
  // Gerar sugestões de melhorias nas instruções
  const suggestedImprovements = generateInstructionImprovements(
    feedbacks,
    commonIssues
  );
  
  return {
    agentName,
    totalFeedbacks: feedbacks.length,
    avgRating,
    commonIssues,
    suggestedImprovements,
    strengthAreas,
    improvementAreas,
  };
}

// Identificar pontos fortes
function identifyStrengths(highRatedFeedbacks: FeedbackRecord[]): string[] {
  if (highRatedFeedbacks.length < 3) return [];
  
  const strengths: string[] = [];
  
  // Analisar patterns em feedbacks positivos
  const hasConsistentTone = highRatedFeedbacks.every(f => 
    !f.issues.includes("inappropriate_tone")
  );
  if (hasConsistentTone) strengths.push("Tom de comunicação apropriado");
  
  const hasGoodClarity = highRatedFeedbacks.every(f => 
    !f.issues.includes("unclear_response")
  );
  if (hasGoodClarity) strengths.push("Respostas claras e objetivas");
  
  const hasAccuracy = highRatedFeedbacks.every(f => 
    !f.issues.includes("incorrect_info")
  );
  if (hasAccuracy) strengths.push("Informações precisas");
  
  return strengths;
}

// Identificar áreas de melhoria
function identifyImprovements(
  lowRatedFeedbacks: FeedbackRecord[],
  commonIssues: { issue: string; count: number }[]
): string[] {
  const improvements: string[] = [];
  
  const issueMapping: Record<string, string> = {
    incorrect_info: "Precisão das informações",
    inappropriate_tone: "Tom de comunicação",
    unclear_response: "Clareza das respostas",
    incomplete_response: "Completude das respostas",
    too_verbose: "Concisão",
    too_brief: "Detalhamento",
    slow_response: "Tempo de resposta",
  };
  
  commonIssues
    .filter(({ count }) => count >= MIN_FEEDBACKS_FOR_SUGGESTION)
    .forEach(({ issue }) => {
      const improvement = issueMapping[issue];
      if (improvement) {
        improvements.push(improvement);
      }
    });
  
  return improvements;
}

// Gerar sugestões de melhorias nas instruções
function generateInstructionImprovements(
  feedbacks: FeedbackRecord[],
  commonIssues: { issue: string; count: number }[]
): InstructionImprovement[] {
  const improvements: InstructionImprovement[] = [];
  
  // Mapear issues para sugestões de instruções
  commonIssues
    .filter(({ count }) => count >= MIN_FEEDBACKS_FOR_SUGGESTION)
    .forEach(({ issue, count }) => {
      let improvement: InstructionImprovement | null = null;
      
      switch (issue) {
        case "incorrect_info":
          improvement = {
            original: "Forneça informações úteis",
            suggested: "Forneça informações precisas e verificáveis. Cite fontes quando possível e admita se não tiver certeza sobre algo.",
            reason: `${count} usuários reportaram informações incorretas`,
            confidence: Math.min(count / 10, 0.9),
            supportingFeedback: count,
          };
          break;
          
        case "inappropriate_tone":
          improvement = {
            original: "Seja prestativo",
            suggested: "Mantenha um tom profissional, empático e respeitoso. Adapte a linguagem ao contexto e ao nível técnico do usuário.",
            reason: `${count} usuários reportaram tom inadequado`,
            confidence: Math.min(count / 10, 0.9),
            supportingFeedback: count,
          };
          break;
          
        case "unclear_response":
          improvement = {
            original: "Responda claramente",
            suggested: "Estruture respostas de forma clara: use tópicos, exemplos práticos e evite jargões desnecessários. Priorize objetividade.",
            reason: `${count} usuários reportaram falta de clareza`,
            confidence: Math.min(count / 10, 0.9),
            supportingFeedback: count,
          };
          break;
          
        case "incomplete_response":
          improvement = {
            original: "Responda completamente",
            suggested: "Forneça respostas abrangentes que cubram todos os aspectos da pergunta. Antecipe dúvidas relacionadas e ofereça contexto adicional quando relevante.",
            reason: `${count} usuários reportaram respostas incompletas`,
            confidence: Math.min(count / 10, 0.9),
            supportingFeedback: count,
          };
          break;
          
        case "too_verbose":
          improvement = {
            original: "Seja detalhado",
            suggested: "Seja conciso e direto ao ponto. Forneça detalhes apenas quando necessário. Use bullet points para melhor escaneabilidade.",
            reason: `${count} usuários reportaram respostas muito longas`,
            confidence: Math.min(count / 10, 0.9),
            supportingFeedback: count,
          };
          break;
          
        case "too_brief":
          improvement = {
            original: "Seja conciso",
            suggested: "Forneça explicações detalhadas com exemplos práticos. Balance brevidade com completude - inclua contexto e justificativas.",
            reason: `${count} usuários reportaram respostas muito curtas`,
            confidence: Math.min(count / 10, 0.9),
            supportingFeedback: count,
          };
          break;
      }
      
      if (improvement) {
        improvements.push(improvement);
      }
    });
  
  return improvements.sort((a, b) => b.confidence - a.confidence);
}

// Obter tendência de rating ao longo do tempo
export function getRatingTrend(agentName: string): {
  dates: string[];
  ratings: number[];
  trend: "improving" | "declining" | "stable";
} {
  const feedbacks = getAgentFeedbacks(agentName);
  
  if (feedbacks.length < 2) {
    return { dates: [], ratings: [], trend: "stable" };
  }
  
  // Agrupar por dia
  const byDate: Record<string, number[]> = {};
  feedbacks.forEach(f => {
    const date = f.timestamp.toISOString().split("T")[0];
    if (!byDate[date]) byDate[date] = [];
    byDate[date].push(f.rating);
  });
  
  const dates = Object.keys(byDate).sort();
  const ratings = dates.map(date => {
    const dayRatings = byDate[date];
    return dayRatings.reduce((sum, r) => sum + r, 0) / dayRatings.length;
  });
  
  // Calcular tendência (primeira metade vs segunda metade)
  if (ratings.length < 4) {
    return { dates, ratings, trend: "stable" };
  }
  
  const mid = Math.floor(ratings.length / 2);
  const firstHalf = ratings.slice(0, mid);
  const secondHalf = ratings.slice(mid);
  
  const firstAvg = firstHalf.reduce((sum, r) => sum + r, 0) / firstHalf.length;
  const secondAvg = secondHalf.reduce((sum, r) => sum + r, 0) / secondHalf.length;
  
  const diff = secondAvg - firstAvg;
  const trend = diff > 0.3 ? "improving" : diff < -0.3 ? "declining" : "stable";
  
  return { dates, ratings, trend };
}

// Aplicar melhorias sugeridas (retorna novas instruções)
export function applyImprovements(
  currentInstructions: string[],
  improvements: InstructionImprovement[]
): string[] {
  const newInstructions = [...currentInstructions];
  
  improvements.forEach(improvement => {
    // Tentar encontrar e substituir instrução similar
    const idx = newInstructions.findIndex(inst => 
      inst.toLowerCase().includes(improvement.original.toLowerCase().split(" ").slice(0, 2).join(" "))
    );
    
    if (idx !== -1) {
      // Substituir instrução existente
      newInstructions[idx] = improvement.suggested;
    } else {
      // Adicionar nova instrução
      newInstructions.push(improvement.suggested);
    }
  });
  
  return newInstructions;
}

// Gerar dados de exemplo
export function generateSampleFeedbacks(agentName: string): void {
  const samples = [
    { rating: 5, issues: [], prompt: "Como implementar auth JWT?", response: "Resposta detalhada..." },
    { rating: 4, issues: [], prompt: "Melhores práticas React?", response: "Resposta clara..." },
    { rating: 2, issues: ["unclear_response", "incomplete_response"], prompt: "Explicar GraphQL", response: "GraphQL é..." },
    { rating: 5, issues: [], prompt: "Performance PostgreSQL", response: "Para melhorar..." },
    { rating: 3, issues: ["too_verbose"], prompt: "Diferença REST vs GraphQL", response: "Resposta muito longa..." },
    { rating: 1, issues: ["incorrect_info", "inappropriate_tone"], prompt: "Como usar Docker", response: "Resposta incorreta..." },
    { rating: 4, issues: [], prompt: "Configurar TypeScript", response: "Resposta útil..." },
    { rating: 2, issues: ["unclear_response"], prompt: "O que é middleware", response: "Resposta confusa..." },
  ];
  
  samples.forEach(sample => {
    saveFeedback(
      agentName,
      sample.rating,
      sample.issues,
      sample.prompt,
      sample.response,
      ["Seja prestativo", "Responda claramente", "Forneça exemplos"]
    );
  });
}

// Limpar feedbacks de um agente
export function clearAgentFeedbacks(agentName: string): void {
  if (typeof window === "undefined") return;
  
  const stored = localStorage.getItem(FEEDBACK_KEY);
  if (!stored) return;
  
  const allFeedback: Record<string, FeedbackRecord[]> = JSON.parse(stored);
  delete allFeedback[agentName];
  
  localStorage.setItem(FEEDBACK_KEY, JSON.stringify(allFeedback));
}
