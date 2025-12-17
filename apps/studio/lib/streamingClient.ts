"use client";

/**
 * Cliente para streaming de respostas via SSE (Server-Sent Events)
 * com suporte a auto-retry e fallback de modelo
 */

interface StreamOptions {
  onChunk: (chunk: string) => void;
  onComplete?: (fullResponse: string) => void;
  onError?: (error: Error) => void;
  signal?: AbortSignal;
}

interface ModelConfig {
  provider: string;
  modelId: string;
  priority: number;
}

// Modelos ordenados por prioridade para fallback
const MODEL_FALLBACK_CHAIN: ModelConfig[] = [
  { provider: "groq", modelId: "llama-3.3-70b-versatile", priority: 1 },
  { provider: "openai", modelId: "gpt-4o-mini", priority: 2 },
  { provider: "openai", modelId: "gpt-4o", priority: 3 },
  { provider: "anthropic", modelId: "claude-3-5-sonnet-20241022", priority: 4 },
];

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

/**
 * Executa uma requisição com streaming SSE
 */
export async function streamRequest(
  url: string,
  body: Record<string, unknown>,
  options: StreamOptions
): Promise<void> {
  const { onChunk, onComplete, onError, signal } = options;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify(body),
      signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Response body is not readable");
    }

    const decoder = new TextDecoder();
    let fullResponse = "";

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      
      // Parse SSE format
      const lines = chunk.split("\n");
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") {
            onComplete?.(fullResponse);
            return;
          }
          try {
            const parsed = JSON.parse(data);
            const content = parsed.content || parsed.delta?.content || "";
            if (content) {
              fullResponse += content;
              onChunk(content);
            }
          } catch {
            // Se não for JSON válido, usar diretamente
            fullResponse += data;
            onChunk(data);
          }
        }
      }
    }

    onComplete?.(fullResponse);
  } catch (error) {
    onError?.(error instanceof Error ? error : new Error(String(error)));
    throw error;
  }
}

/**
 * Executa requisição com auto-retry e fallback de modelo
 */
export async function executeWithRetry<T>(
  fn: (modelConfig: ModelConfig) => Promise<T>,
  options: {
    maxRetries?: number;
    retryDelay?: number;
    onRetry?: (attempt: number, error: Error, nextModel?: ModelConfig) => void;
  } = {}
): Promise<T> {
  const { 
    maxRetries = MAX_RETRIES, 
    retryDelay = RETRY_DELAY_MS,
    onRetry 
  } = options;

  let lastError: Error | null = null;
  let modelIndex = 0;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    const currentModel = MODEL_FALLBACK_CHAIN[modelIndex];
    
    try {
      return await fn(currentModel);
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      // Verificar se deve tentar outro modelo
      const isModelError = isModelRelatedError(lastError);
      
      if (isModelError && modelIndex < MODEL_FALLBACK_CHAIN.length - 1) {
        modelIndex++;
        const nextModel = MODEL_FALLBACK_CHAIN[modelIndex];
        onRetry?.(attempt, lastError, nextModel);
        console.warn(`Fallback para modelo: ${nextModel.provider}/${nextModel.modelId}`);
      } else if (attempt < maxRetries) {
        onRetry?.(attempt, lastError);
        await delay(retryDelay * attempt); // Exponential backoff
      }
    }
  }

  throw lastError || new Error("Todas as tentativas falharam");
}

/**
 * Verifica se o erro está relacionado ao modelo
 */
function isModelRelatedError(error: Error): boolean {
  const modelErrors = [
    "rate limit",
    "quota exceeded",
    "model not found",
    "overloaded",
    "capacity",
    "timeout",
    "503",
    "529",
  ];
  
  const message = error.message.toLowerCase();
  return modelErrors.some(e => message.includes(e));
}

/**
 * Delay helper
 */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Hook de estado para streaming
 */
export interface StreamingState {
  isStreaming: boolean;
  chunks: string[];
  fullText: string;
  error: Error | null;
}

export const initialStreamingState: StreamingState = {
  isStreaming: false,
  chunks: [],
  fullText: "",
  error: null,
};
