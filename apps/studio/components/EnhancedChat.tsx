"use client";
import React, { useState, useRef, useEffect } from "react";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  status?: "sending" | "processing" | "done" | "error";
  progress?: {
    current: number;
    total: number;
    step: string;
    details?: string;
  };
  attachments?: Array<{
    name: string;
    size: number;
    type: string;
    url: string;
  }>;
}

interface EnhancedChatProps {
  agentName: string;
  agentIcon?: string;
  onSendMessage: (message: string, attachments?: File[]) => Promise<void>;
  messages: Message[];
  isProcessing?: boolean;
  currentProgress?: {
    current: number;
    total: number;
    step: string;
    details?: string;
  };
}

export default function EnhancedChat({
  agentName,
  agentIcon = "🤖",
  onSendMessage,
  messages,
  isProcessing = false,
  currentProgress,
}: EnhancedChatProps) {
  const [input, setInput] = useState("");
  const [attachments, setAttachments] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && attachments.length === 0) return;

    await onSendMessage(input, attachments);
    setInput("");
    setAttachments([]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachments(prev => [...prev, ...files]);
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const getProgressColor = (percent: number) => {
    if (percent < 33) return "bg-blue-500";
    if (percent < 66) return "bg-purple-500";
    return "bg-green-500";
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-slate-700 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-slate-900 dark:to-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/25">
              <span className="text-xl">{agentIcon}</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">{agentName}</h3>
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <div className={`w-2 h-2 rounded-full ${isProcessing ? "bg-blue-500 animate-pulse" : "bg-green-500"}`} />
                <span>{isProcessing ? "Processando..." : "Online"}</span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Histórico">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
            <button className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Configurações">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/25">
              <span className="text-4xl">{agentIcon}</span>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Olá! Sou o {agentName}
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              Como posso ajudar você hoje?
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              <button
                onClick={() => setInput("Resuma os últimos emails importantes")}
                className="px-4 py-2 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
              >
                📧 Resumir emails
              </button>
              <button
                onClick={() => setInput("Analise os dados do último relatório")}
                className="px-4 py-2 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
              >
                📊 Analisar dados
              </button>
              <button
                onClick={() => setInput("Ajude-me a escrever um artigo sobre IA")}
                className="px-4 py-2 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
              >
                ✍️ Escrever conteúdo
              </button>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}
            >
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                message.role === "user"
                  ? "bg-gradient-to-br from-gray-500 to-gray-600 text-white"
                  : "bg-gradient-to-br from-blue-500 to-purple-600 text-white"
              }`}>
                {message.role === "user" ? "👤" : agentIcon}
              </div>

              {/* Message Content */}
              <div className={`flex-1 max-w-[80%] ${message.role === "user" ? "items-end" : ""}`}>
                <div className={`rounded-2xl p-4 ${
                  message.role === "user"
                    ? "bg-blue-500 text-white ml-auto"
                    : "bg-gray-100 dark:bg-slate-700 text-gray-900 dark:text-white"
                }`}>
                  {/* Progress Indicator */}
                  {message.status === "processing" && message.progress && (
                    <div className="mb-3 p-3 bg-white/10 dark:bg-slate-800/50 rounded-xl">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">
                          {message.progress.step}
                        </span>
                        <span className="text-xs opacity-75">
                          {message.progress.current}/{message.progress.total}
                        </span>
                      </div>
                      <div className="h-2 bg-white/20 dark:bg-slate-900/50 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${getProgressColor((message.progress.current / message.progress.total) * 100)} transition-all duration-300`}
                          style={{ width: `${(message.progress.current / message.progress.total) * 100}%` }}
                        />
                      </div>
                      {message.progress.details && (
                        <p className="text-xs opacity-75 mt-2">{message.progress.details}</p>
                      )}
                    </div>
                  )}

                  {/* Text Content */}
                  <div className="whitespace-pre-wrap">{message.content}</div>

                  {/* Attachments */}
                  {message.attachments && message.attachments.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {message.attachments.map((file, idx) => (
                        <a
                          key={idx}
                          href={file.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 p-2 bg-white/10 dark:bg-slate-800/50 rounded-lg hover:bg-white/20 transition-colors"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                          </svg>
                          <span className="text-sm flex-1">{file.name}</span>
                          <span className="text-xs opacity-75">{formatFileSize(file.size)}</span>
                        </a>
                      ))}
                    </div>
                  )}
                </div>

                {/* Timestamp */}
                <div className={`flex items-center gap-2 mt-1 px-2 text-xs text-gray-500 dark:text-gray-400 ${
                  message.role === "user" ? "justify-end" : ""
                }`}>
                  <span>{new Date(message.timestamp).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</span>
                  {message.status === "error" && <span className="text-red-500">⚠️ Erro</span>}
                  {message.status === "done" && message.role === "assistant" && (
                    <button className="hover:text-blue-500 transition-colors" title="Gostei">
                      👍
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Current Processing Status */}
        {isProcessing && currentProgress && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white animate-pulse">
              {agentIcon}
            </div>
            <div className="flex-1 max-w-[80%]">
              <div className="bg-gray-100 dark:bg-slate-700 rounded-2xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <svg className="w-5 h-5 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span className="font-medium text-gray-900 dark:text-white">{currentProgress.step}</span>
                </div>
                <div className="h-2 bg-gray-200 dark:bg-slate-600 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getProgressColor((currentProgress.current / currentProgress.total) * 100)} transition-all duration-300`}
                    style={{ width: `${(currentProgress.current / currentProgress.total) * 100}%` }}
                  />
                </div>
                {currentProgress.details && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{currentProgress.details}</p>
                )}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="px-6 py-4 border-t border-gray-200 dark:border-slate-700">
        {/* Attachments Preview */}
        {attachments.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {attachments.map((file, idx) => (
              <div key={idx} className="flex items-center gap-2 px-3 py-2 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-lg text-sm">
                <span>📎 {file.name}</span>
                <span className="text-xs opacity-75">({formatFileSize(file.size)})</span>
                <button
                  onClick={() => removeAttachment(idx)}
                  className="ml-1 hover:text-red-500 transition-colors"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            multiple
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-3 text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-slate-700 rounded-xl transition-colors"
            title="Anexar arquivo"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite sua mensagem..."
            disabled={isProcessing}
            className="flex-1 px-4 py-3 bg-gray-100 dark:bg-slate-700 border-0 rounded-xl focus:ring-2 focus:ring-blue-500 transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isProcessing || (!input.trim() && attachments.length === 0)}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isProcessing ? (
              <>
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Processando...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                Enviar
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
