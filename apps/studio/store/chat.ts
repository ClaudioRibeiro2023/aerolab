"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// ============================================
// TYPES
// ============================================

export interface Attachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url?: string;
  preview?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  agent?: string;
  model?: string;
  provider?: string;
  attachments?: Attachment[];
  isStreaming?: boolean;
  tokens?: {
    input: number;
    output: number;
  };
}

export interface Conversation {
  id: string;
  title: string;
  agentId?: string;
  agentName?: string;
  model?: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  pinned: boolean;
  archived: boolean;
}

export interface ChatState {
  // Conversations
  conversations: Record<string, Conversation>;
  activeConversationId: string | null;
  
  // UI State
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  
  // Actions - Conversations
  createConversation: (agentName?: string, model?: string) => string;
  setActiveConversation: (id: string | null) => void;
  deleteConversation: (id: string) => void;
  updateConversationTitle: (id: string, title: string) => void;
  togglePin: (id: string) => void;
  archiveConversation: (id: string) => void;
  
  // Actions - Messages
  addMessage: (conversationId: string, message: Omit<Message, "id" | "timestamp">) => Message;
  updateMessage: (conversationId: string, messageId: string, updates: Partial<Message>) => void;
  clearMessages: (conversationId: string) => void;
  
  // Actions - State
  setLoading: (loading: boolean) => void;
  setStreaming: (streaming: boolean) => void;
  setError: (error: string | null) => void;
  
  // Getters
  getConversation: (id: string) => Conversation | undefined;
  getActiveConversation: () => Conversation | undefined;
  getMessages: (conversationId: string) => Message[];
  getRecentConversations: (limit?: number) => Conversation[];
  getPinnedConversations: () => Conversation[];
  
  // Hydration
  isHydrated: boolean;
  setHydrated: (hydrated: boolean) => void;
}

// ============================================
// HELPERS
// ============================================

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function generateTitle(agentName?: string): string {
  const date = new Date().toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
  return agentName ? `Chat com ${agentName} - ${date}` : `Nova conversa - ${date}`;
}

// ============================================
// STORE
// ============================================

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      // Initial State
      conversations: {},
      activeConversationId: null,
      isLoading: false,
      isStreaming: false,
      error: null,
      isHydrated: false,

      // ==================== Conversations ====================

      createConversation: (agentName?: string, model?: string) => {
        const id = generateId();
        const now = new Date().toISOString();
        
        const conversation: Conversation = {
          id,
          title: generateTitle(agentName),
          agentName,
          model,
          messages: [],
          createdAt: now,
          updatedAt: now,
          pinned: false,
          archived: false,
        };

        set((state) => ({
          conversations: {
            ...state.conversations,
            [id]: conversation,
          },
          activeConversationId: id,
        }));

        return id;
      },

      setActiveConversation: (id) => {
        set({ activeConversationId: id });
      },

      deleteConversation: (id) => {
        set((state) => {
          const { [id]: deleted, ...rest } = state.conversations;
          return {
            conversations: rest,
            activeConversationId:
              state.activeConversationId === id ? null : state.activeConversationId,
          };
        });
      },

      updateConversationTitle: (id, title) => {
        set((state) => {
          const conv = state.conversations[id];
          if (!conv) return state;
          
          return {
            conversations: {
              ...state.conversations,
              [id]: {
                ...conv,
                title,
                updatedAt: new Date().toISOString(),
              },
            },
          };
        });
      },

      togglePin: (id) => {
        set((state) => {
          const conv = state.conversations[id];
          if (!conv) return state;
          
          return {
            conversations: {
              ...state.conversations,
              [id]: {
                ...conv,
                pinned: !conv.pinned,
                updatedAt: new Date().toISOString(),
              },
            },
          };
        });
      },

      archiveConversation: (id) => {
        set((state) => {
          const conv = state.conversations[id];
          if (!conv) return state;
          
          return {
            conversations: {
              ...state.conversations,
              [id]: {
                ...conv,
                archived: true,
                updatedAt: new Date().toISOString(),
              },
            },
          };
        });
      },

      // ==================== Messages ====================

      addMessage: (conversationId, messageData) => {
        const message: Message = {
          ...messageData,
          id: generateId(),
          timestamp: new Date().toISOString(),
        };

        set((state) => {
          const conv = state.conversations[conversationId];
          if (!conv) {
            // Auto-create conversation if doesn't exist
            const newConv: Conversation = {
              id: conversationId,
              title: generateTitle(messageData.agent),
              agentName: messageData.agent,
              model: messageData.model,
              messages: [message],
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              pinned: false,
              archived: false,
            };
            return {
              conversations: {
                ...state.conversations,
                [conversationId]: newConv,
              },
              activeConversationId: conversationId,
            };
          }

          // Auto-generate title from first user message
          let newTitle = conv.title;
          if (conv.messages.length === 0 && messageData.role === "user") {
            const content = messageData.content.trim();
            newTitle = content.length > 50 ? content.substring(0, 50) + "..." : content;
          }

          return {
            conversations: {
              ...state.conversations,
              [conversationId]: {
                ...conv,
                title: newTitle,
                messages: [...conv.messages, message],
                updatedAt: new Date().toISOString(),
              },
            },
          };
        });

        return message;
      },

      updateMessage: (conversationId, messageId, updates) => {
        set((state) => {
          const conv = state.conversations[conversationId];
          if (!conv) return state;

          return {
            conversations: {
              ...state.conversations,
              [conversationId]: {
                ...conv,
                messages: conv.messages.map((msg) =>
                  msg.id === messageId ? { ...msg, ...updates } : msg
                ),
                updatedAt: new Date().toISOString(),
              },
            },
          };
        });
      },

      clearMessages: (conversationId) => {
        set((state) => {
          const conv = state.conversations[conversationId];
          if (!conv) return state;

          return {
            conversations: {
              ...state.conversations,
              [conversationId]: {
                ...conv,
                messages: [],
                updatedAt: new Date().toISOString(),
              },
            },
          };
        });
      },

      // ==================== State ====================

      setLoading: (loading) => set({ isLoading: loading }),
      setStreaming: (streaming) => set({ isStreaming: streaming }),
      setError: (error) => set({ error }),
      setHydrated: (hydrated) => set({ isHydrated: hydrated }),

      // ==================== Getters ====================

      getConversation: (id) => get().conversations[id],

      getActiveConversation: () => {
        const { activeConversationId, conversations } = get();
        return activeConversationId ? conversations[activeConversationId] : undefined;
      },

      getMessages: (conversationId) => {
        const conv = get().conversations[conversationId];
        return conv?.messages || [];
      },

      getRecentConversations: (limit = 20) => {
        const { conversations } = get();
        return Object.values(conversations)
          .filter((c) => !c.archived)
          .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
          .slice(0, limit);
      },

      getPinnedConversations: () => {
        const { conversations } = get();
        return Object.values(conversations)
          .filter((c) => c.pinned && !c.archived)
          .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
      },
    }),
    {
      name: "aerolab-chat-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        conversations: state.conversations,
        activeConversationId: state.activeConversationId,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated(true);
      },
    }
  )
);

// ============================================
// HOOKS HELPERS
// ============================================

export function useActiveConversation() {
  const activeConversationId = useChatStore((s) => s.activeConversationId);
  const conversations = useChatStore((s) => s.conversations);
  return activeConversationId ? conversations[activeConversationId] : undefined;
}

export function useConversationMessages(conversationId: string | null) {
  const conversations = useChatStore((s) => s.conversations);
  if (!conversationId) return [];
  return conversations[conversationId]?.messages || [];
}
