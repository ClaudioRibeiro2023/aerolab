"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, X, Send, Minimize2, Maximize2, Sparkles, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================
// TYPES
// ============================================================

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface AIAssistantProps {
  className?: string;
  onSendMessage?: (message: string) => Promise<string>;
  welcomeMessage?: string;
  placeholder?: string;
}

// ============================================================
// AI AVATAR
// ============================================================

function AIAvatar({ isThinking = false }: { isThinking?: boolean }) {
  return (
    <div className="relative">
      <motion.div
        className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center"
        animate={isThinking ? { scale: [1, 1.1, 1] } : {}}
        transition={{ duration: 1, repeat: isThinking ? Infinity : 0 }}
      >
        <Bot className="w-5 h-5 text-white" />
      </motion.div>
      
      {/* Pulse ring when thinking */}
      {isThinking && (
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-blue-400"
          animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
      )}
    </div>
  );
}

// ============================================================
// TYPING INDICATOR
// ============================================================

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3 py-2">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-2 h-2 rounded-full bg-slate-400"
          animate={{ y: [0, -5, 0] }}
          transition={{ duration: 0.6, delay: i * 0.15, repeat: Infinity }}
        />
      ))}
    </div>
  );
}

// ============================================================
// CHAT BUBBLE
// ============================================================

interface ChatBubbleProps {
  message: Message;
}

function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex gap-2", isUser ? "flex-row-reverse" : "")}
    >
      {!isUser && <AIAvatar />}
      
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2",
          isUser
            ? "bg-blue-600 text-white rounded-br-sm"
            : "bg-slate-800 text-slate-200 rounded-bl-sm"
        )}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        <span className="text-[10px] opacity-60 mt-1 block">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </motion.div>
  );
}

// ============================================================
// MAIN COMPONENT
// ============================================================

export function AIAssistant({
  className,
  onSendMessage,
  welcomeMessage = "Olá! Sou o assistente AGNO. Como posso ajudar você hoje?",
  placeholder = "Digite sua mensagem...",
}: AIAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: welcomeMessage,
          timestamp: new Date(),
        },
      ]);
    }
  }, [welcomeMessage, messages.length]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      let response: string;
      
      if (onSendMessage) {
        response = await onSendMessage(userMessage.content);
      } else {
        // Default simulated response
        await new Promise((resolve) => setTimeout(resolve, 1500));
        response = getDefaultResponse(userMessage.content);
      }

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: "Desculpe, ocorreu um erro. Por favor, tente novamente.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Floating Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsOpen(true)}
            className={cn(
              "fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full",
              "bg-gradient-to-br from-blue-500 to-purple-600",
              "flex items-center justify-center shadow-lg shadow-blue-500/30",
              "hover:shadow-xl hover:shadow-blue-500/40 transition-shadow",
              className
            )}
          >
            <Sparkles className="w-6 h-6 text-white" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{
              opacity: 1,
              y: 0,
              scale: 1,
              height: isMinimized ? "auto" : 500,
            }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className={cn(
              "fixed bottom-6 right-6 z-50 w-96",
              "bg-slate-900/95 backdrop-blur-xl rounded-2xl",
              "border border-slate-700 shadow-2xl overflow-hidden",
              "flex flex-col"
            )}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <AIAvatar isThinking={isTyping} />
                <div>
                  <h3 className="font-semibold text-white">AGNO Assistant</h3>
                  <p className="text-xs text-slate-400">
                    {isTyping ? "Digitando..." : "Online"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
                  title={isMinimized ? "Expandir" : "Minimizar"}
                >
                  {isMinimized ? (
                    <Maximize2 className="w-4 h-4" />
                  ) : (
                    <Minimize2 className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
                  title="Fechar"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Messages */}
            {!isMinimized && (
              <>
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.map((message) => (
                    <ChatBubble key={message.id} message={message} />
                  ))}
                  {isTyping && (
                    <div className="flex gap-2">
                      <AIAvatar isThinking />
                      <div className="bg-slate-800 rounded-2xl rounded-bl-sm">
                        <TypingIndicator />
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-4 border-t border-slate-800">
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={placeholder}
                      className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
                    />
                    <button
                      onClick={handleSend}
                      disabled={!input.trim() || isTyping}
                      className={cn(
                        "p-2.5 rounded-xl transition-all",
                        input.trim() && !isTyping
                          ? "bg-blue-600 text-white hover:bg-blue-500"
                          : "bg-slate-800 text-slate-500"
                      )}
                    >
                      {isTyping ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <Send className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// Default response generator
function getDefaultResponse(input: string): string {
  const lower = input.toLowerCase();
  
  if (lower.includes("agente") || lower.includes("criar")) {
    return "Para criar um novo agente, vá para Agentes > Novo Agente. Você pode definir nome, modelo, instruções e ferramentas.";
  }
  if (lower.includes("workflow") || lower.includes("fluxo")) {
    return "Os workflows permitem automatizar tarefas complexas. Acesse Flow Studio para criar visualmente.";
  }
  if (lower.includes("time") || lower.includes("equipe")) {
    return "Times são grupos de agentes que trabalham juntos. Vá para Times > Novo Time para criar um.";
  }
  if (lower.includes("rag") || lower.includes("documento")) {
    return "O sistema RAG permite que agentes consultem seus documentos. Use RAG > Ingest para carregar arquivos.";
  }
  if (lower.includes("ajuda") || lower.includes("help")) {
    return "Posso ajudar com:\n• Criação de agentes\n• Configuração de workflows\n• Gestão de times\n• Sistema RAG\n• Domínios especializados";
  }
  
  return "Entendi! Posso ajudar você com agentes, workflows, times e muito mais. O que gostaria de fazer?";
}

export default AIAssistant;
