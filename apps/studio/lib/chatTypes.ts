/**
 * Chat Types - Sistema de tipos TypeScript para Chat v2
 */

// ==================== Enums ====================

export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';
export type MessageType = 'text' | 'markdown' | 'code' | 'image' | 'audio' | 'video' | 'file' | 'artifact' | 'tool_call' | 'tool_result';
export type MessageStatus = 'pending' | 'sending' | 'streaming' | 'done' | 'error' | 'cancelled';
export type ConversationStatus = 'active' | 'archived' | 'deleted';
export type ReasoningMode = 'off' | 'basic' | 'extended';

// ==================== Stream Events ====================

export type StreamEventType = 
  | 'message_start'
  | 'message_delta'
  | 'message_done'
  | 'message_error'
  | 'thinking_start'
  | 'thinking_delta'
  | 'thinking_done'
  | 'tool_call_start'
  | 'tool_call_args'
  | 'tool_call_done'
  | 'tool_result'
  | 'artifact_start'
  | 'artifact_delta'
  | 'artifact_done'
  | 'citation_added'
  | 'typing'
  | 'processing'
  | 'done'
  | 'error'
  | 'user_typing';

export interface StreamEvent {
  type: StreamEventType;
  timestamp: string;
  messageId?: string;
  conversationId?: string;
  content?: string;
  delta?: string;
  finishReason?: string;
  toolCallId?: string;
  toolName?: string;
  arguments?: Record<string, unknown>;
  result?: string;
  artifactId?: string;
  artifactType?: string;
  citation?: Citation;
  error?: string;
  errorCode?: string;
  data?: Record<string, unknown>;
}

// ==================== Attachments ====================

export interface Attachment {
  id: string;
  name: string;
  mimeType: string;
  sizeBytes: number;
  url?: string;
  thumbnailUrl?: string;
  metadata?: Record<string, unknown>;
}

// ==================== Citations ====================

export interface Citation {
  id: string;
  title: string;
  url?: string;
  snippet: string;
  sourceType: 'web' | 'document' | 'rag';
  relevanceScore: number;
}

// ==================== Tool Calls ====================

export interface ToolCall {
  id: string;
  toolName: string;
  arguments: Record<string, unknown>;
  result?: string;
  status: 'pending' | 'running' | 'success' | 'error';
  durationMs: number;
}

// ==================== Reasoning ====================

export interface ReasoningStep {
  stepNumber: number;
  content: string;
  stepType: 'thinking' | 'planning' | 'evaluating' | 'concluding';
  durationMs: number;
}

// ==================== Reactions ====================

export interface Reaction {
  userId: string;
  emoji: string;
  createdAt: string;
}

// ==================== Messages ====================

export interface Message {
  id: string;
  conversationId: string;
  branchId: string;
  parentId?: string;
  
  // Author
  role: MessageRole;
  agentId?: string;
  userId?: string;
  
  // Content
  content: string;
  contentType: MessageType;
  
  // Rich content
  attachments: Attachment[];
  citations: Citation[];
  toolCalls: ToolCall[];
  reasoningSteps: ReasoningStep[];
  artifactIds: string[];
  
  // Metadata
  model?: string;
  tokensPrompt: number;
  tokensCompletion: number;
  latencyMs: number;
  
  // Status
  status: MessageStatus;
  error?: string;
  
  // Interactions
  reactions: Reaction[];
  feedback?: 'good' | 'bad';
  regeneratedFrom?: string;
  
  // Timestamps
  createdAt: string;
  updatedAt: string;
  editedAt?: string;
}

// ==================== Branches ====================

export interface Branch {
  id: string;
  name: string;
  parentId?: string;
  parentMessageId?: string;
  createdAt: string;
}

// ==================== Collaborators ====================

export interface Collaborator {
  userId: string;
  role: 'owner' | 'editor' | 'viewer';
  joinedAt: string;
  isOnline: boolean;
  cursorPosition?: number;
}

// ==================== Settings ====================

export interface ConversationSettings {
  model: string;
  temperature: number;
  maxTokens: number;
  customInstructions?: string;
  systemPrompt?: string;
  reasoningMode: ReasoningMode;
  webSearchEnabled: boolean;
  codeExecutionEnabled: boolean;
  voiceModeEnabled: boolean;
  maxContextMessages: number;
  includeSystemPrompt: boolean;
}

// ==================== Conversation ====================

export interface Conversation {
  id: string;
  projectId?: string;
  title: string;
  autoTitle: boolean;
  userId: string;
  organizationId?: string;
  status: ConversationStatus;
  pinned: boolean;
  
  // Branches
  branches: Branch[];
  activeBranchId: string;
  
  // Messages (loaded on demand)
  messageCount: number;
  
  // Agents
  agentIds: string[];
  primaryAgentId?: string;
  
  // Collaborators
  collaborators: Collaborator[];
  
  // Settings
  settings: ConversationSettings;
  
  // Metrics
  totalTokens: number;
  estimatedCostUsd: number;
  
  // Timestamps
  createdAt: string;
  updatedAt: string;
  lastMessageAt?: string;
  archivedAt?: string;
  
  // Metadata
  tags: string[];
}

// ==================== List Items ====================

export interface ConversationListItem {
  id: string;
  title: string;
  status: ConversationStatus;
  pinned: boolean;
  messageCount: number;
  primaryAgentId?: string;
  lastMessageAt?: string;
  createdAt: string;
}

// ==================== Session ====================

export interface Session {
  id: string;
  userId: string;
  activeConversationId?: string;
  activeAgentId?: string;
  isTyping: boolean;
  isProcessing: boolean;
  createdAt: string;
  lastActivity: string;
  expiresAt?: string;
}

// ==================== API Types ====================

export interface CreateConversationRequest {
  userId: string;
  agentId?: string;
  title?: string;
  projectId?: string;
  settings?: Partial<ConversationSettings>;
}

export interface SendMessageRequest {
  conversationId: string;
  content: string;
  userId: string;
  agentId?: string;
  attachments?: File[];
}

export interface UpdateConversationRequest {
  title?: string;
  pinned?: boolean;
  settings?: Partial<ConversationSettings>;
}

// ==================== UI State ====================

export interface ChatUIState {
  // Current view
  activeConversationId: string | null;
  activeBranchId: string | null;
  
  // Loading states
  isLoadingConversations: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;
  isStreaming: boolean;
  
  // Streaming state
  streamingMessageId: string | null;
  streamingContent: string;
  streamingThinking: string;
  
  // UI state
  showSidebar: boolean;
  showSettings: boolean;
  showBranches: boolean;
  
  // Error
  error: string | null;
}

// ==================== Defaults ====================

export const DEFAULT_SETTINGS: ConversationSettings = {
  model: 'gpt-4o',
  temperature: 0.7,
  maxTokens: 4096,
  reasoningMode: 'off',
  webSearchEnabled: false,
  codeExecutionEnabled: false,
  voiceModeEnabled: false,
  maxContextMessages: 50,
  includeSystemPrompt: true,
};

export const AVAILABLE_MODELS = [
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai' },
  { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', provider: 'openai' },
  { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', provider: 'anthropic' },
  { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus', provider: 'anthropic' },
  { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', provider: 'google' },
  { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B', provider: 'groq' },
];

// ==================== Helper Functions ====================

export function createEmptyMessage(conversationId: string, role: MessageRole = 'user'): Message {
  return {
    id: crypto.randomUUID(),
    conversationId,
    branchId: 'main',
    role,
    content: '',
    contentType: 'text',
    attachments: [],
    citations: [],
    toolCalls: [],
    reasoningSteps: [],
    artifactIds: [],
    tokensPrompt: 0,
    tokensCompletion: 0,
    latencyMs: 0,
    status: 'pending',
    reactions: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

export function formatMessageTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

export function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffMins < 1) return 'agora';
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}d`;
  return date.toLocaleDateString('pt-BR');
}

export function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4);
}

export function formatTokens(tokens: number): string {
  if (tokens < 1000) return tokens.toString();
  return `${(tokens / 1000).toFixed(1)}k`;
}
