// Sistema de cache inteligente para respostas de agentes
// Reduz custos ao reutilizar respostas similares

export interface CacheEntry {
  id: string;
  agentName: string;
  prompt: string;
  response: string;
  timestamp: Date;
  hits: number; // Quantas vezes foi reutilizado
  tokensInput: number;
  tokensOutput: number;
  costSaved: number; // USD economizado por reutilização
  metadata?: Record<string, any>;
}

export interface CacheStats {
  totalEntries: number;
  totalHits: number;
  totalCostSaved: number;
  hitRate: number; // %
  avgTokensSaved: number;
}

const CACHE_KEY = "agno_intelligent_cache";
const MAX_CACHE_SIZE = 1000; // Limite de entradas
const SIMILARITY_THRESHOLD = 0.85; // Threshold para considerar similar (0-1)
const CACHE_TTL_DAYS = 30; // Tempo de vida do cache em dias

// Calcular similaridade entre dois textos (Jaccard similarity)
function calculateSimilarity(text1: string, text2: string): number {
  const tokens1 = new Set(text1.toLowerCase().split(/\s+/));
  const tokens2 = new Set(text2.toLowerCase().split(/\s+/));
  
  const intersection = new Set([...tokens1].filter(x => tokens2.has(x)));
  const union = new Set([...tokens1, ...tokens2]);
  
  return intersection.size / union.size;
}

// Normalizar prompt para melhor matching
function normalizePrompt(prompt: string): string {
  return prompt
    .toLowerCase()
    .trim()
    .replace(/\s+/g, " ")
    .replace(/[^\w\s]/g, "");
}

// Obter cache completo
function getCache(): Record<string, CacheEntry[]> {
  if (typeof window === "undefined") return {};
  
  const stored = localStorage.getItem(CACHE_KEY);
  if (!stored) return {};
  
  const cache: Record<string, CacheEntry[]> = JSON.parse(stored);
  
  // Converter timestamps
  Object.keys(cache).forEach(agentName => {
    cache[agentName] = cache[agentName].map(entry => ({
      ...entry,
      timestamp: new Date(entry.timestamp),
    }));
  });
  
  return cache;
}

// Salvar cache
function saveCache(cache: Record<string, CacheEntry[]>): void {
  if (typeof window === "undefined") return;
  
  localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
}

// Limpar entradas expiradas
function cleanExpiredEntries(entries: CacheEntry[]): CacheEntry[] {
  const now = Date.now();
  const ttlMs = CACHE_TTL_DAYS * 24 * 60 * 60 * 1000;
  
  return entries.filter(entry => {
    const age = now - new Date(entry.timestamp).getTime();
    return age < ttlMs;
  });
}

// Buscar no cache
export function searchCache(
  agentName: string,
  prompt: string
): CacheEntry | null {
  const cache = getCache();
  const agentCache = cache[agentName];
  
  if (!agentCache || agentCache.length === 0) return null;
  
  const normalizedPrompt = normalizePrompt(prompt);
  let bestMatch: CacheEntry | null = null;
  let bestSimilarity = 0;
  
  // Buscar melhor match
  for (const entry of agentCache) {
    const normalizedCached = normalizePrompt(entry.prompt);
    
    // Exact match (mais rápido)
    if (normalizedCached === normalizedPrompt) {
      return entry;
    }
    
    // Similarity match
    const similarity = calculateSimilarity(normalizedPrompt, normalizedCached);
    
    if (similarity >= SIMILARITY_THRESHOLD && similarity > bestSimilarity) {
      bestMatch = entry;
      bestSimilarity = similarity;
    }
  }
  
  return bestMatch;
}

// Adicionar ao cache
export function addToCache(
  agentName: string,
  prompt: string,
  response: string,
  tokensInput: number,
  tokensOutput: number,
  metadata?: Record<string, any>
): void {
  if (typeof window === "undefined") return;
  
  const cache = getCache();
  
  if (!cache[agentName]) {
    cache[agentName] = [];
  }
  
  // Limpar expirados
  cache[agentName] = cleanExpiredEntries(cache[agentName]);
  
  // Verificar se já existe
  const existing = searchCache(agentName, prompt);
  if (existing) {
    // Já existe, não adicionar duplicata
    return;
  }
  
  // Criar nova entrada
  const entry: CacheEntry = {
    id: `cache_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    agentName,
    prompt,
    response,
    timestamp: new Date(),
    hits: 0,
    tokensInput,
    tokensOutput,
    costSaved: 0,
    metadata,
  };
  
  cache[agentName].push(entry);
  
  // Limitar tamanho (remover mais antigos)
  if (cache[agentName].length > MAX_CACHE_SIZE) {
    cache[agentName].sort((a, b) => {
      // Priorizar por hits e recência
      const scoreA = a.hits * 0.7 + (Date.now() - a.timestamp.getTime()) * 0.3;
      const scoreB = b.hits * 0.7 + (Date.now() - b.timestamp.getTime()) * 0.3;
      return scoreB - scoreA;
    });
    
    cache[agentName] = cache[agentName].slice(0, MAX_CACHE_SIZE);
  }
  
  saveCache(cache);
}

// Registrar hit no cache
export function recordCacheHit(
  agentName: string,
  entryId: string,
  costSaved: number
): void {
  if (typeof window === "undefined") return;
  
  const cache = getCache();
  const agentCache = cache[agentName];
  
  if (!agentCache) return;
  
  const entry = agentCache.find(e => e.id === entryId);
  if (!entry) return;
  
  entry.hits++;
  entry.costSaved += costSaved;
  
  saveCache(cache);
}

// Obter estatísticas do cache
export function getCacheStats(agentName?: string): CacheStats {
  const cache = getCache();
  
  let entries: CacheEntry[] = [];
  if (agentName) {
    entries = cache[agentName] || [];
  } else {
    entries = Object.values(cache).flat();
  }
  
  const totalEntries = entries.length;
  const totalHits = entries.reduce((sum, e) => sum + e.hits, 0);
  const totalCostSaved = entries.reduce((sum, e) => sum + e.costSaved, 0);
  const totalRequests = totalEntries + totalHits;
  const hitRate = totalRequests > 0 ? (totalHits / totalRequests) * 100 : 0;
  
  const totalTokensSaved = entries.reduce(
    (sum, e) => sum + (e.tokensInput + e.tokensOutput) * e.hits,
    0
  );
  const avgTokensSaved = totalHits > 0 ? totalTokensSaved / totalHits : 0;
  
  return {
    totalEntries,
    totalHits,
    totalCostSaved,
    hitRate,
    avgTokensSaved,
  };
}

// Obter entradas populares
export function getPopularEntries(
  agentName: string,
  limit: number = 10
): CacheEntry[] {
  const cache = getCache();
  const agentCache = cache[agentName] || [];
  
  return agentCache
    .sort((a, b) => b.hits - a.hits)
    .slice(0, limit);
}

// Limpar cache de um agente
export function clearAgentCache(agentName: string): void {
  if (typeof window === "undefined") return;
  
  const cache = getCache();
  delete cache[agentName];
  saveCache(cache);
}

// Limpar todo o cache
export function clearAllCache(): void {
  if (typeof window === "undefined") return;
  
  localStorage.removeItem(CACHE_KEY);
}

// Obter tamanho do cache
export function getCacheSize(): {
  entries: number;
  sizeKB: number;
  agents: number;
} {
  if (typeof window === "undefined") {
    return { entries: 0, sizeKB: 0, agents: 0 };
  }
  
  const cache = getCache();
  const entries = Object.values(cache).flat().length;
  const agents = Object.keys(cache).length;
  
  const stored = localStorage.getItem(CACHE_KEY);
  const sizeKB = stored ? new Blob([stored]).size / 1024 : 0;
  
  return { entries, sizeKB, agents };
}

// Exportar cache
export function exportCache(): string {
  const cache = getCache();
  return JSON.stringify(cache, null, 2);
}

// Importar cache
export function importCache(jsonData: string): boolean {
  if (typeof window === "undefined") return false;
  
  try {
    const cache = JSON.parse(jsonData);
    
    // Validar estrutura básica
    if (typeof cache !== "object") return false;
    
    localStorage.setItem(CACHE_KEY, jsonData);
    return true;
  } catch {
    return false;
  }
}

// Otimizar cache (remover menos úteis)
export function optimizeCache(): {
  removedEntries: number;
  savedSpaceKB: number;
} {
  if (typeof window === "undefined") {
    return { removedEntries: 0, savedSpaceKB: 0 };
  }
  
  const sizeBefore = getCacheSize();
  const cache = getCache();
  
  let totalRemoved = 0;
  
  Object.keys(cache).forEach(agentName => {
    const entries = cache[agentName];
    
    // Remover entradas expiradas
    const cleaned = cleanExpiredEntries(entries);
    
    // Remover entradas com 0 hits e antigas (>7 dias)
    const now = Date.now();
    const filtered = cleaned.filter(entry => {
      const age = now - new Date(entry.timestamp).getTime();
      const daysDiff = age / (1000 * 60 * 60 * 24);
      
      if (entry.hits === 0 && daysDiff > 7) {
        totalRemoved++;
        return false;
      }
      return true;
    });
    
    cache[agentName] = filtered;
  });
  
  saveCache(cache);
  
  const sizeAfter = getCacheSize();
  const savedSpaceKB = sizeBefore.sizeKB - sizeAfter.sizeKB;
  
  return {
    removedEntries: totalRemoved,
    savedSpaceKB: Math.max(0, savedSpaceKB),
  };
}

// Gerar dados de exemplo
export function generateSampleCache(agentName: string): void {
  const samples = [
    {
      prompt: "Como melhorar a performance de um banco de dados PostgreSQL?",
      response: "Para melhorar a performance do PostgreSQL, você pode: 1) Criar índices adequados nas colunas mais consultadas, 2) Usar EXPLAIN ANALYZE para identificar queries lentas, 3) Configurar shared_buffers e work_mem apropriadamente, 4) Implementar particionamento de tabelas grandes, 5) Usar connection pooling (ex: PgBouncer).",
      tokensInput: 120,
      tokensOutput: 450,
    },
    {
      prompt: "Qual a diferença entre REST e GraphQL?",
      response: "As principais diferenças são: REST usa endpoints fixos (/users, /posts), enquanto GraphQL usa um único endpoint. REST pode retornar dados desnecessários (overfetching), GraphQL permite selecionar exatamente os campos necessários. REST é mais simples para APIs básicas, GraphQL é melhor para dados relacionados complexos.",
      tokensInput: 100,
      tokensOutput: 380,
    },
    {
      prompt: "Como implementar autenticação JWT em Node.js?",
      response: "Para implementar JWT: 1) Instale 'jsonwebtoken': npm install jsonwebtoken, 2) Crie um secret seguro, 3) No login, gere o token: jwt.sign({userId}, secret, {expiresIn: '24h'}), 4) Crie middleware de verificação: jwt.verify(token, secret), 5) Proteja rotas com o middleware. Armazene o token no cliente (localStorage ou httpOnly cookie).",
      tokensInput: 110,
      tokensOutput: 420,
    },
  ];
  
  samples.forEach(sample => {
    addToCache(
      agentName,
      sample.prompt,
      sample.response,
      sample.tokensInput,
      sample.tokensOutput
    );
    
    // Simular alguns hits
    const cache = getCache();
    const entry = cache[agentName]?.find(e => e.prompt === sample.prompt);
    if (entry) {
      entry.hits = Math.floor(Math.random() * 10) + 1;
      entry.costSaved = entry.hits * 0.002; // ~$0.002 por hit
      saveCache(cache);
    }
  });
}
