"use client";

import React, { useState, useEffect, useRef, Suspense, useCallback, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import Protected from "../../components/Protected";
import api from "@/lib/api";
import { toast } from "sonner";
import { addToHistory } from "../../lib/executionHistory";
import { trackExecution, estimateExecutionCost } from "../../lib/analytics";
import { motion, AnimatePresence } from "framer-motion";
import { PageHeader } from "../../components/PageHeader";
import EmptyState from "../../components/EmptyState";
import { useChatStore, type Message as StoreMessage, type Attachment as StoreAttachment } from "../../store/chat";
import { useStreamChat } from "../../hooks/useStreamChat";
import ConversationSidebar from "../../components/chat/ConversationSidebar";
import PersonaSelector from "../../components/chat/PersonaSelector";

interface Agent {
  id?: string;
  name: string;
  description?: string;
  model?: string;
}

interface ApiAgent {
  id?: string;
  name?: string;
  description?: string;
  system_message?: { summary?: string };
  model_id?: string;
  model?: { model?: string };
}

interface Attachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url?: string;
  preview?: string;
}

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  agent?: string;
  model?: string;
  attachments?: Attachment[];
  isStreaming?: boolean;
}

// ============================================================
// AVAILABLE MODELS
// ============================================================

const AVAILABLE_MODELS = [
  { id: "llama-3.3-70b-versatile", name: "Llama 3.3 70B", provider: "Groq", icon: "🦙" },
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI", icon: "🤖" },
  { id: "gpt-4o-mini", name: "GPT-4o Mini", provider: "OpenAI", icon: "⚡" },
  { id: "claude-3-5-sonnet-20241022", name: "Claude 3.5 Sonnet", provider: "Anthropic", icon: "🎭" },
  { id: "claude-3-5-haiku-20241022", name: "Claude 3.5 Haiku", provider: "Anthropic", icon: "📝" },
  { id: "gemini-2.0-flash-exp", name: "Gemini 2.0 Flash", provider: "Google", icon: "💎" },
  { id: "mixtral-8x7b-32768", name: "Mixtral 8x7B", provider: "Groq", icon: "🌀" },
];

// ============================================================
// MARKDOWN RENDERER
// ============================================================

function parseMarkdown(text: string): React.ReactNode {
  if (!text) return null;

  // Split into lines for processing
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeContent = "";
  let codeLanguage = "";
  let listItems: string[] = [];
  let listType: "ul" | "ol" | null = null;

  const flushList = () => {
    if (listItems.length > 0) {
      const ListTag = listType === "ol" ? "ol" : "ul";
      elements.push(
        <ListTag key={`list-${elements.length}`} className={listType === "ol" ? "list-decimal ml-4 my-2 space-y-1" : "list-disc ml-4 my-2 space-y-1"}>
          {listItems.map((item, idx) => (
            <li key={idx} className="text-slate-300">{parseInlineMarkdown(item)}</li>
          ))}
        </ListTag>
      );
      listItems = [];
      listType = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block start/end
    if (line.startsWith("```")) {
      if (!inCodeBlock) {
        flushList();
        inCodeBlock = true;
        codeLanguage = line.slice(3).trim();
        codeContent = "";
      } else {
        elements.push(
          <div key={`code-${elements.length}`} className="my-3 rounded-lg overflow-hidden">
            {codeLanguage && (
              <div className="bg-slate-900 px-3 py-1.5 text-xs text-slate-400 border-b border-slate-700 flex items-center justify-between">
                <span>{codeLanguage}</span>
                <button
                  onClick={() => navigator.clipboard.writeText(codeContent)}
                  className="text-slate-500 hover:text-white transition-colors"
                >
                  Copiar
                </button>
              </div>
            )}
            <pre className="bg-slate-900 p-3 overflow-x-auto">
              <code className="text-sm text-emerald-400 font-mono">{codeContent}</code>
            </pre>
          </div>
        );
        inCodeBlock = false;
        codeContent = "";
        codeLanguage = "";
      }
      continue;
    }

    if (inCodeBlock) {
      codeContent += (codeContent ? "\n" : "") + line;
      continue;
    }

    // Unordered list
    if (line.match(/^[\-\*]\s+/)) {
      if (listType !== "ul") flushList();
      listType = "ul";
      listItems.push(line.replace(/^[\-\*]\s+/, ""));
      continue;
    }

    // Ordered list
    if (line.match(/^\d+\.\s+/)) {
      if (listType !== "ol") flushList();
      listType = "ol";
      listItems.push(line.replace(/^\d+\.\s+/, ""));
      continue;
    }

    // Flush list if we hit a non-list line
    flushList();

    // Headers
    if (line.startsWith("### ")) {
      elements.push(<h3 key={`h3-${i}`} className="text-lg font-semibold text-white mt-4 mb-2">{parseInlineMarkdown(line.slice(4))}</h3>);
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(<h2 key={`h2-${i}`} className="text-xl font-semibold text-white mt-4 mb-2">{parseInlineMarkdown(line.slice(3))}</h2>);
      continue;
    }
    if (line.startsWith("# ")) {
      elements.push(<h1 key={`h1-${i}`} className="text-2xl font-bold text-white mt-4 mb-2">{parseInlineMarkdown(line.slice(2))}</h1>);
      continue;
    }

    // Horizontal rule
    if (line.match(/^[\-\*\_]{3,}$/)) {
      elements.push(<hr key={`hr-${i}`} className="border-slate-700 my-4" />);
      continue;
    }

    // Empty line
    if (!line.trim()) {
      elements.push(<div key={`br-${i}`} className="h-2" />);
      continue;
    }

    // Regular paragraph
    elements.push(<p key={`p-${i}`} className="text-slate-300 my-1">{parseInlineMarkdown(line)}</p>);
  }

  flushList();

  return <div className="prose prose-invert max-w-none">{elements}</div>;
}

function parseInlineMarkdown(text: string): React.ReactNode {
  // Split by patterns and process
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // Bold **text**
    const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
    if (boldMatch && boldMatch.index !== undefined) {
      if (boldMatch.index > 0) {
        parts.push(<span key={key++}>{remaining.slice(0, boldMatch.index)}</span>);
      }
      parts.push(<strong key={key++} className="font-semibold text-white">{boldMatch[1]}</strong>);
      remaining = remaining.slice(boldMatch.index + boldMatch[0].length);
      continue;
    }

    // Inline code `code`
    const codeMatch = remaining.match(/`([^`]+)`/);
    if (codeMatch && codeMatch.index !== undefined) {
      if (codeMatch.index > 0) {
        parts.push(<span key={key++}>{remaining.slice(0, codeMatch.index)}</span>);
      }
      parts.push(
        <code key={key++} className="px-1.5 py-0.5 bg-slate-800 rounded text-emerald-400 text-sm font-mono">
          {codeMatch[1]}
        </code>
      );
      remaining = remaining.slice(codeMatch.index + codeMatch[0].length);
      continue;
    }

    // Italic *text* or _text_
    const italicMatch = remaining.match(/(?:\*|_)([^*_]+)(?:\*|_)/);
    if (italicMatch && italicMatch.index !== undefined) {
      if (italicMatch.index > 0) {
        parts.push(<span key={key++}>{remaining.slice(0, italicMatch.index)}</span>);
      }
      parts.push(<em key={key++} className="italic text-slate-200">{italicMatch[1]}</em>);
      remaining = remaining.slice(italicMatch.index + italicMatch[0].length);
      continue;
    }

    // No more matches, add remaining text
    parts.push(<span key={key++}>{remaining}</span>);
    break;
  }

  return <>{parts}</>;
}

// ============================================================
// PARSE API RESPONSE
// ============================================================

function parseApiResponse(response: string | object): string {
  if (typeof response === "object") {
    // Handle {"agent": "...", "output": "..."} format
    if ("output" in response && typeof (response as {output: unknown}).output === "string") {
      return (response as {output: string}).output;
    }
    if ("result" in response && typeof (response as {result: unknown}).result === "string") {
      return (response as {result: string}).result;
    }
    if ("response" in response && typeof (response as {response: unknown}).response === "string") {
      return (response as {response: string}).response;
    }
    if ("content" in response && typeof (response as {content: unknown}).content === "string") {
      return (response as {content: string}).content;
    }
    return JSON.stringify(response, null, 2);
  }
  
  // Try to parse JSON string
  if (typeof response === "string") {
    try {
      const parsed = JSON.parse(response);
      return parseApiResponse(parsed);
    } catch {
      // Not JSON, return as is
      return response;
    }
  }
  
  return String(response);
}

function ChatContent() {
  const searchParams = useSearchParams();
  const agentFromUrl = searchParams?.get("agent") || null;
  
  // Chat Store (persistent)
  const {
    conversations,
    activeConversationId,
    createConversation,
    setActiveConversation,
    addMessage: addStoreMessage,
    clearMessages: clearStoreMessages,
    getMessages: getStoreMessages,
    isHydrated,
  } = useChatStore();

  // Local UI State
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState(AVAILABLE_MODELS[0].id);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showAgentList, setShowAgentList] = useState(false);
  const [showModelList, setShowModelList] = useState(false);
  const [initialAgentSet, setInitialAgentSet] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(false);
  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(null);
  const [useStreaming, setUseStreaming] = useState(true);

  // Streaming hook
  const {
    sendMessage: sendStreamMessage,
    cancelStream,
    isStreaming,
    currentMessage: streamingMessage,
  } = useStreamChat({
    onToken: () => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    },
    onComplete: (msg) => {
      if (conversationId && msg.content) {
        addStoreMessage(conversationId, {
          role: "assistant",
          content: msg.content,
          agent: selectedAgent,
          model: selectedModel,
          provider: msg.provider,
        });
      }
    },
    onError: (err) => {
      toast.error(err);
    },
  });

  // Get messages from store
  const messages = useMemo(() => {
    if (!conversationId) return [];
    const storeMessages = getStoreMessages(conversationId);
    return storeMessages.map(m => ({
      ...m,
      timestamp: new Date(m.timestamp),
    })) as Message[];
  }, [conversationId, conversations, getStoreMessages]);

  // Estimated tokens calculation
  const estimatedTokens = useMemo(() => {
    const totalChars = messages.reduce((acc, m) => acc + (m.content?.length || 0), 0);
    return Math.ceil(totalChars / 4); // ~4 chars per token
  }, [messages]);
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load agents on mount
  useEffect(() => {
    loadAgents();
  }, []);

  // Initialize or restore conversation
  useEffect(() => {
    if (!isHydrated) return;
    
    // If there's an active conversation, use it
    if (activeConversationId && conversations[activeConversationId]) {
      setConversationId(activeConversationId);
      const conv = conversations[activeConversationId];
      if (conv.agentName) setSelectedAgent(conv.agentName);
      if (conv.model) setSelectedModel(conv.model);
    } else {
      // Create new conversation when agent is selected
      if (selectedAgent && !conversationId) {
        const newId = createConversation(selectedAgent, selectedModel);
        setConversationId(newId);
      }
    }
  }, [isHydrated, activeConversationId, selectedAgent]);

  // Set agent from URL param after agents load
  useEffect(() => {
    if (!initialAgentSet && agents.length > 0) {
      if (agentFromUrl) {
        const match = agents.find(
          a => a.name === agentFromUrl || a.id === agentFromUrl
        );
        if (match) {
          setSelectedAgent(match.name);
          toast.success(`Agente "${match.name}" selecionado`);
        } else if (!selectedAgent && agents.length > 0) {
          setSelectedAgent(agents[0].name);
        }
      } else if (!selectedAgent && agents.length > 0) {
        setSelectedAgent(agents[0].name);
      }
      setInitialAgentSet(true);
    }
  }, [agents, agentFromUrl, initialAgentSet, selectedAgent]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadAgents = async () => {
    try {
      const { data } = await api.get("/agents");
      const list = (data || []) as ApiAgent[];
      const normalized = list.map((a) => ({
        id: a.id || a.name,
        name: a.name || a.id || "",
        description: a.description || a.system_message?.summary,
        model: a.model_id || a.model?.model,
      }));
      setAgents(normalized);
    } catch (err) {
      console.error("Erro ao carregar agentes:", err);
    }
  };

  // Handle file selection
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newAttachments: Attachment[] = [];
    
    Array.from(files).forEach((file) => {
      const attachment: Attachment = {
        id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        name: file.name,
        type: file.type,
        size: file.size,
      };

      // Create preview for images
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => {
          attachment.preview = e.target?.result as string;
          setAttachments(prev => [...prev.filter(a => a.id !== attachment.id), attachment]);
        };
        reader.readAsDataURL(file);
      }

      newAttachments.push(attachment);
    });

    setAttachments(prev => [...prev, ...newAttachments]);
    e.target.value = ""; // Reset input
  }, []);

  const removeAttachment = useCallback((id: string) => {
    setAttachments(prev => prev.filter(a => a.id !== id));
  }, []);

  const sendMessage = async () => {
    if ((!input.trim() && attachments.length === 0) || !selectedAgent || loading || isStreaming) return;

    // Ensure we have a conversation
    let currentConvId = conversationId;
    if (!currentConvId) {
      currentConvId = createConversation(selectedAgent, selectedModel);
      setConversationId(currentConvId);
    }

    const userMessageData = {
      role: "user" as const,
      content: input.trim(),
      agent: selectedAgent,
      model: selectedModel,
      attachments: attachments.length > 0 ? attachments.map(a => ({
        id: a.id,
        name: a.name,
        type: a.type,
        size: a.size,
        url: a.url,
        preview: a.preview,
      })) : undefined,
    };

    const userMessage = addStoreMessage(currentConvId, userMessageData);
    const messageContent = input.trim();
    setInput("");
    setAttachments([]);

    const startTime = Date.now();

    // Build prompt with attachment info
    let fullPrompt = messageContent;
    if (userMessage.attachments && userMessage.attachments.length > 0) {
      const attachmentInfo = userMessage.attachments.map(a => `[Anexo: ${a.name} (${a.type})]`).join("\n");
      fullPrompt = `${attachmentInfo}\n\n${fullPrompt}`;
    }

    // Use streaming
    if (useStreaming) {
      const result = await sendStreamMessage({
        message: fullPrompt,
        model: selectedModel,
        conversationId: currentConvId,
        personaId: selectedPersonaId || undefined,
      });

      if (result) {
        const duration = (Date.now() - startTime) / 1000;
        
        // Save to history
        addToHistory({
          type: "agent",
          name: currentAgent?.name || selectedAgent,
          prompt: messageContent,
          result: result.content.substring(0, 500),
          timestamp: new Date().toISOString(),
          duration,
          status: "success",
        });

        // Track execution
        const tokens = result.usage?.total_tokens || Math.ceil((messageContent.length + result.content.length) / 4);
        trackExecution({
          agentName: currentAgent?.name || selectedAgent,
          duration,
          tokens,
          cost: estimateExecutionCost(tokens, result.provider || "groq", selectedModel),
          success: true,
        });
      }
      return;
    }

    // Fallback: non-streaming mode
    setLoading(true);
    try {
      const { data } = await api.post(`/agents/${encodeURIComponent(selectedAgent)}/run`, {
        prompt: fullPrompt,
        model: selectedModel,
      });

      const rawResult = data.result || data.response || data;
      const result = parseApiResponse(rawResult);
      const duration = (Date.now() - startTime) / 1000;

      addStoreMessage(currentConvId!, {
        role: "assistant",
        content: result,
        agent: currentAgent?.name || selectedAgent,
        model: selectedModel,
        provider: data.provider,
      });

      addToHistory({
        type: "agent",
        name: currentAgent?.name || selectedAgent,
        prompt: messageContent,
        result: result.substring(0, 500),
        timestamp: new Date().toISOString(),
        duration,
        status: "success",
      });

      const tokens = Math.ceil((messageContent.length + result.length) / 4);
      trackExecution({
        agentName: currentAgent?.name || selectedAgent,
        duration,
        tokens,
        cost: estimateExecutionCost(tokens, "groq", selectedModel),
        success: true,
      });
    } catch (e) {
      const duration = (Date.now() - startTime) / 1000;
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || "Erro ao enviar mensagem");
      
      addStoreMessage(currentConvId!, {
        role: "system",
        content: "Erro ao processar sua mensagem. Tente novamente.",
      });

      addToHistory({
        type: "agent",
        name: selectedAgent,
        prompt: messageContent,
        result: err.response?.data?.detail || "Erro ao processar mensagem",
        timestamp: new Date().toISOString(),
        duration,
        status: "error",
      });

      trackExecution({
        agentName: selectedAgent,
        duration,
        tokens: Math.ceil(messageContent.length / 4),
        cost: 0,
        success: false,
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const clearChat = () => {
    if (conversationId) {
      clearStoreMessages(conversationId);
    }
    // Create new conversation
    const newId = createConversation(selectedAgent, selectedModel);
    setConversationId(newId);
  };

  const copyMessage = useCallback((content: string) => {
    navigator.clipboard.writeText(content);
    toast.success("Mensagem copiada!");
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const currentAgent = agents.find(a => a.name === selectedAgent);
  const currentModel = AVAILABLE_MODELS.find(m => m.id === selectedModel);

  // Handle new conversation
  const handleNewConversation = () => {
    const newId = createConversation(selectedAgent, selectedModel);
    setConversationId(newId);
    setActiveConversation(newId);
    setShowSidebar(false);
  };

  // Handle select conversation from sidebar
  const handleSelectConversation = (id: string) => {
    setConversationId(id);
    setActiveConversation(id);
    const conv = conversations[id];
    if (conv?.agentName) setSelectedAgent(conv.agentName);
    if (conv?.model) setSelectedModel(conv.model);
    setShowSidebar(false);
  };

  return (
    <Protected>
      {/* Conversation Sidebar */}
      <ConversationSidebar
        isOpen={showSidebar}
        onClose={() => setShowSidebar(false)}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />

      <div className="h-[calc(100vh-8rem)] flex flex-col">
        <PageHeader
          title="Chat com Agentes"
          subtitle="Converse com seus agentes de IA"
          rightActions={
            <div className="flex items-center gap-3">
              {/* Sidebar Toggle */}
              <button
                onClick={() => setShowSidebar(true)}
                className="flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl hover:bg-slate-700 transition-colors"
                title="Histórico de Conversas"
              >
                <svg className="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                </svg>
                <span className="text-sm text-slate-300 hidden sm:inline">Histórico</span>
              </button>

              {/* Persona Selector */}
              <PersonaSelector
                selectedPersonaId={selectedPersonaId}
                onSelectPersona={(persona) => setSelectedPersonaId(persona?.id || null)}
                compact
              />

              {/* Streaming Toggle */}
              <button
                onClick={() => setUseStreaming(!useStreaming)}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl border transition-colors ${
                  useStreaming
                    ? "bg-emerald-600/20 border-emerald-500/50 text-emerald-400"
                    : "bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-700"
                }`}
                title={useStreaming ? "Streaming ativo - clique para desativar" : "Streaming inativo - clique para ativar"}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {useStreaming ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  )}
                </svg>
                <span className="text-xs hidden sm:inline">{useStreaming ? "Stream" : "Sync"}</span>
              </button>

              {/* Model Selector */}
              <div className="relative">
              <button
                onClick={() => setShowModelList(!showModelList)}
                className="flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl hover:bg-slate-700 transition-colors"
                title="Selecionar Modelo"
              >
                <span className="text-lg">{currentModel?.icon || "🤖"}</span>
                <span className="text-sm font-medium text-slate-300 hidden sm:inline">
                  {currentModel?.name || "Modelo"}
                </span>
                <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              <AnimatePresence>
                {showModelList && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute right-0 mt-2 w-72 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-20 overflow-hidden"
                  >
                    <div className="p-2 border-b border-slate-700">
                      <p className="text-xs text-slate-400 px-2">Selecione o modelo de IA</p>
                    </div>
                    <div className="max-h-80 overflow-y-auto p-1">
                      {AVAILABLE_MODELS.map(model => (
                        <button
                          key={model.id}
                          onClick={() => {
                            setSelectedModel(model.id);
                            setShowModelList(false);
                            toast.success(`Modelo ${model.name} selecionado`);
                          }}
                          className={`w-full px-3 py-2.5 text-left rounded-lg transition-colors flex items-center gap-3 ${
                            selectedModel === model.id 
                              ? "bg-blue-600/20 border border-blue-500/30" 
                              : "hover:bg-slate-700"
                          }`}
                        >
                          <span className="text-xl">{model.icon}</span>
                          <div className="flex-1">
                            <div className="font-medium text-white text-sm">{model.name}</div>
                            <div className="text-xs text-slate-400">{model.provider}</div>
                          </div>
                          {selectedModel === model.id && (
                            <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </button>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              </div>

              {/* Agent Selector */}
              <div className="relative">
              <button
                onClick={() => setShowAgentList(!showAgentList)}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl hover:bg-slate-700 transition-colors"
              >
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <span className="text-sm font-medium text-slate-200">
                  {currentAgent?.name || selectedAgent || "Selecionar Agente"}
                </span>
                <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              <AnimatePresence>
                {showAgentList && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute right-0 mt-2 w-72 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-20 overflow-hidden"
                  >
                    {agents.length === 0 ? (
                      <div className="p-4 text-center text-slate-400 text-sm">
                        Nenhum agente disponível
                      </div>
                    ) : (
                      <div className="max-h-60 overflow-y-auto p-1">
                        {agents.map(agent => (
                          <button
                            key={agent.name}
                            onClick={() => {
                              setSelectedAgent(agent.name);
                              setShowAgentList(false);
                            }}
                            className={`w-full px-3 py-2.5 text-left rounded-lg transition-colors ${
                              selectedAgent === agent.name ? "bg-blue-600/20 border border-blue-500/30" : "hover:bg-slate-700"
                            }`}
                          >
                            <div className="font-medium text-white text-sm">{agent.name}</div>
                            {agent.description && (
                              <div className="text-xs text-slate-400 mt-0.5 truncate">
                                {agent.description}
                              </div>
                            )}
                          </button>
                        ))}
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
              </div>

              {/* Clear Chat */}
              {messages.length > 0 && (
                <button
                  onClick={clearChat}
                  className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                  title="Limpar conversa"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              )}
            </div>
          }
        />

        {/* Chat Container */}
        <div className="flex-1 bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-slate-800 flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <EmptyState
                  icon="💬"
                  title="Comece uma conversa"
                  description="Selecione um agente e modelo, depois envie uma mensagem para começar."
                  action={
                    selectedAgent || agents.length === 0
                      ? undefined
                      : {
                          label: "Selecionar agente",
                          onClick: () => setShowAgentList(true),
                        }
                  }
                  secondaryAction={{
                    label: "Ver agentes disponíveis",
                    href: "/agents",
                  }}
                  suggestions={[
                    currentAgent
                      ? `Conversando com ${currentAgent.name}.`
                      : "Escolha um agente no topo para começar.",
                    currentModel
                      ? `${currentModel.icon} ${currentModel.name} está selecionado como modelo.`
                      : "Selecione um modelo no topo para ajustar qualidade e custo.",
                    "Envie uma mensagem descrevendo seu contexto ou tarefa.",
                  ]}
                />
              </div>
            ) : (
              <>
                {messages.map(message => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex gap-4 ${message.role === "user" ? "flex-row-reverse" : ""}`}
                  >
                    {/* Avatar */}
                    <div className={`w-10 h-10 rounded-xl flex-shrink-0 flex items-center justify-center ${
                      message.role === "user" 
                        ? "bg-gradient-to-br from-emerald-500 to-teal-600" 
                        : message.role === "assistant"
                        ? "bg-gradient-to-br from-blue-500 to-purple-600"
                        : "bg-red-500/20"
                    }`}>
                      {message.role === "user" ? (
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                      )}
                    </div>
                    
                    {/* Message Content */}
                    <div className={`flex-1 max-w-[80%] ${message.role === "user" ? "text-right" : ""}`}>
                      {/* Attachments */}
                      {message.attachments && message.attachments.length > 0 && (
                        <div className={`flex flex-wrap gap-2 mb-2 ${message.role === "user" ? "justify-end" : ""}`}>
                          {message.attachments.map(att => (
                            <div key={att.id} className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 rounded-lg">
                              {att.preview ? (
                                <img src={att.preview} alt={att.name} className="w-8 h-8 rounded object-cover" />
                              ) : (
                                <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                                </svg>
                              )}
                              <span className="text-xs text-slate-300 truncate max-w-[100px]">{att.name}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Message Bubble */}
                      <div
                        className={`inline-block px-4 py-3 rounded-2xl ${
                          message.role === "user"
                            ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-br-md"
                            : message.role === "assistant"
                            ? "bg-slate-800 text-slate-100 rounded-bl-md"
                            : "bg-red-500/20 text-red-300 border border-red-500/30"
                        }`}
                      >
                        {message.role === "assistant" ? (
                          parseMarkdown(message.content)
                        ) : (
                          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        )}
                      </div>

                      {/* Meta info */}
                      <div className={`flex items-center gap-3 mt-2 text-xs text-slate-500 ${message.role === "user" ? "justify-end" : ""}`}>
                        <span>{message.timestamp.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</span>
                        {message.agent && <span>• {message.agent}</span>}
                        {message.model && (
                          <span className="text-slate-600">
                            • {AVAILABLE_MODELS.find(m => m.id === message.model)?.name || message.model}
                          </span>
                        )}
                        {message.role === "assistant" && (
                          <button
                            onClick={() => copyMessage(message.content)}
                            className="text-slate-500 hover:text-white transition-colors"
                            title="Copiar mensagem"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
                
                {/* Streaming message */}
                {isStreaming && streamingMessage && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex gap-4"
                  >
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div className="flex-1 max-w-[80%]">
                      <div className="inline-block px-4 py-3 bg-slate-800 text-slate-100 rounded-2xl rounded-bl-md">
                        {parseMarkdown(streamingMessage.content)}
                        <span className="inline-block w-2 h-4 ml-1 bg-blue-400 animate-pulse rounded-sm" />
                      </div>
                      <div className="flex items-center gap-3 mt-2">
                        <button
                          onClick={cancelStream}
                          className="flex items-center gap-1 px-2 py-1 text-xs text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 rounded-lg transition-colors"
                          title="Cancelar streaming"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                          Cancelar
                        </button>
                        <span className="text-xs text-slate-500">Gerando resposta...</span>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* Loading indicator (non-streaming) */}
                {loading && !isStreaming && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex gap-4"
                  >
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                      <svg className="w-5 h-5 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div className="px-4 py-3 bg-slate-800 rounded-2xl rounded-bl-md">
                      <div className="flex items-center gap-2">
                        <div className="flex gap-1">
                          <motion.div animate={{ y: [0, -5, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: 0 }} className="w-2 h-2 bg-blue-400 rounded-full" />
                          <motion.div animate={{ y: [0, -5, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: 0.15 }} className="w-2 h-2 bg-blue-400 rounded-full" />
                          <motion.div animate={{ y: [0, -5, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: 0.3 }} className="w-2 h-2 bg-blue-400 rounded-full" />
                        </div>
                        <span className="text-sm text-slate-400 ml-2">Pensando...</span>
                      </div>
                    </div>
                  </motion.div>
                )}
                
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Attachments Preview */}
          <AnimatePresence>
            {attachments.length > 0 && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="px-4 py-2 border-t border-slate-800 bg-slate-800/50"
              >
                <div className="flex flex-wrap gap-2">
                  {attachments.map(att => (
                    <div key={att.id} className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 rounded-lg group">
                      {att.preview ? (
                        <img src={att.preview} alt={att.name} className="w-8 h-8 rounded object-cover" />
                      ) : (
                        <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      )}
                      <span className="text-xs text-slate-300 truncate max-w-[150px]">{att.name}</span>
                      <button
                        onClick={() => removeAttachment(att.id)}
                        className="text-slate-500 hover:text-red-400 transition-colors"
                        title="Remover anexo"
                        aria-label={`Remover ${att.name}`}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input */}
          <div className="p-4 border-t border-slate-800 bg-slate-900/80">
            <div className="flex items-end gap-3">
              {/* File Upload */}
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*,.pdf,.doc,.docx,.txt,.csv,.json"
                onChange={handleFileSelect}
                className="hidden"
                title="Selecionar arquivos"
                aria-label="Selecionar arquivos para anexar"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-3 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
                title="Anexar arquivo"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </button>

              {/* Text Input */}
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => {
                    setInput(e.target.value);
                    // Auto resize
                    e.target.style.height = "auto";
                    e.target.style.height = Math.min(e.target.scrollHeight, 150) + "px";
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder={selectedAgent ? `Mensagem para ${selectedAgent}...` : "Selecione um agente primeiro"}
                  disabled={!selectedAgent || loading}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-slate-500 disabled:opacity-50 min-h-[48px] max-h-[150px]"
                  rows={1}
                />
              </div>

              {/* Send Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={sendMessage}
                disabled={(!input.trim() && attachments.length === 0) || !selectedAgent || loading}
                className="p-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 disabled:from-slate-700 disabled:to-slate-700 text-white rounded-xl transition-all disabled:cursor-not-allowed shadow-lg shadow-blue-500/20 disabled:shadow-none"
                title="Enviar mensagem"
              >
                {loading ? (
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </motion.button>
            </div>
            <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
              <p>Enter para enviar • Shift+Enter para nova linha</p>
              <div className="flex items-center gap-3">
                {estimatedTokens > 0 && (
                  <span className="flex items-center gap-1" title="Tokens estimados na conversa">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                    <span className={estimatedTokens > 3000 ? "text-amber-400" : estimatedTokens > 6000 ? "text-red-400" : ""}>
                      {estimatedTokens.toLocaleString()} tokens
                    </span>
                  </span>
                )}
                <span>{messages.length} msgs</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Protected>
  );
}

// Wrapper com Suspense para useSearchParams
export default function ChatPage() {
  return (
    <Suspense fallback={
      <Protected>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <svg className="w-8 h-8 animate-spin mx-auto text-blue-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="mt-2 text-gray-500">Carregando chat...</p>
          </div>
        </div>
      </Protected>
    }>
      <ChatContent />
    </Suspense>
  );
}
