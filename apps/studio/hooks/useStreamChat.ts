"use client";

import { useState, useCallback, useRef } from "react";

interface StreamMessage {
  id: string;
  content: string;
  isComplete: boolean;
  model?: string;
  provider?: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  duration_ms?: number;
  error?: string;
}

interface UseStreamChatOptions {
  apiUrl?: string;
  onToken?: (token: string) => void;
  onComplete?: (message: StreamMessage) => void;
  onError?: (error: string) => void;
}

interface StreamChatParams {
  message: string;
  model?: string;
  conversationId?: string;
  agentId?: string;
  personaId?: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
}

export function useStreamChat(options: UseStreamChatOptions = {}) {
  const {
    apiUrl = "/api/v2/chat/stream",
    onToken,
    onComplete,
    onError,
  } = options;

  const [isStreaming, setIsStreaming] = useState(false);
  const [currentMessage, setCurrentMessage] = useState<StreamMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (params: StreamChatParams): Promise<StreamMessage | null> => {
      const {
        message,
        model = "llama-3.1-8b-instant",
        conversationId,
        agentId,
        personaId,
        temperature = 0.7,
        maxTokens = 4096,
        systemPrompt,
      } = params;

      // Cancel any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();
      setIsStreaming(true);
      setError(null);

      const newMessage: StreamMessage = {
        id: `msg_${Date.now()}`,
        content: "",
        isComplete: false,
      };
      setCurrentMessage(newMessage);

      try {
        // Get base URL
        const baseUrl =
          typeof window !== "undefined"
            ? window.location.origin.includes("localhost")
              ? "http://localhost:8000"
              : ""
            : "";

        const response = await fetch(`${baseUrl}${apiUrl}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify({
            message,
            model,
            conversation_id: conversationId,
            agent_id: agentId,
            persona_id: personaId,
            temperature,
            max_tokens: maxTokens,
            system_prompt: systemPrompt,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("No response body");
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });

          // Parse SSE events
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let eventType = "";
          let eventData = "";

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              eventData = line.slice(6);

              if (eventType && eventData) {
                try {
                  const data = JSON.parse(eventData);

                  switch (eventType) {
                    case "message_start":
                      newMessage.id = data.id;
                      newMessage.model = data.model;
                      break;

                    case "message_delta":
                      newMessage.content += data.delta;
                      setCurrentMessage({ ...newMessage });
                      onToken?.(data.delta);
                      break;

                    case "message_done":
                      newMessage.isComplete = true;
                      newMessage.provider = data.provider;
                      newMessage.usage = data.usage;
                      newMessage.duration_ms = data.duration_ms;
                      setCurrentMessage({ ...newMessage });
                      onComplete?.(newMessage);
                      break;

                    case "error":
                      newMessage.error = data.message;
                      setError(data.message);
                      onError?.(data.message);
                      break;
                  }
                } catch {
                  console.warn("Failed to parse SSE data:", eventData);
                }

                eventType = "";
                eventData = "";
              }
            }
          }
        }

        setIsStreaming(false);
        return newMessage;
      } catch (err) {
        if ((err as Error).name === "AbortError") {
          // Cancelled by user
          setIsStreaming(false);
          return null;
        }

        const errorMessage = (err as Error).message || "Stream error";
        setError(errorMessage);
        onError?.(errorMessage);
        setIsStreaming(false);
        return null;
      }
    },
    [apiUrl, onToken, onComplete, onError]
  );

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const clearMessage = useCallback(() => {
    setCurrentMessage(null);
    setError(null);
  }, []);

  return {
    sendMessage,
    cancelStream,
    clearMessage,
    isStreaming,
    currentMessage,
    error,
  };
}

export type { StreamMessage, StreamChatParams };
