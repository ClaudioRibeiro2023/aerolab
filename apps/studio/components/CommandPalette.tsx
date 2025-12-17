"use client";
import React, { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";

interface Command {
  id: string;
  name: string;
  description?: string;
  icon: React.ReactNode;
  action: () => void;
  keywords?: string[];
  shortcut?: string;
}

const Icons = {
  search: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>),
  dashboard: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6z" /></svg>),
  chat: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>),
  agents: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>),
  teams: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>),
  workflows: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5z" /></svg>),
  domains: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>),
  rag: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" /></svg>),
  sun: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>),
  moon: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>),
  code: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>),
  builder: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" /></svg>),
  hitl: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>),
  logs: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>),
  settings: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>),
  help: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  template: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" /></svg>),
  logout: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>),
};

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const commands: Command[] = [
    { id: "dashboard", name: "Dashboard", description: "Ir para o painel principal", icon: Icons.dashboard, action: () => router.push("/dashboard"), keywords: ["home", "inicio", "painel"] },
    { id: "chat", name: "Chat", description: "Conversar com agentes", icon: Icons.chat, action: () => router.push("/chat"), keywords: ["conversar", "mensagem", "ia"] },
    { id: "agents", name: "Agentes", description: "Gerenciar agentes de IA", icon: Icons.agents, action: () => router.push("/agents"), keywords: ["bot", "ia", "criar"] },
    { id: "teams", name: "Times", description: "Gerenciar times de agentes", icon: Icons.teams, action: () => router.push("/teams"), keywords: ["grupo", "equipe"] },
    { id: "workflows", name: "Workflows", description: "Automações e fluxos", icon: Icons.workflows, action: () => router.push("/workflows"), keywords: ["automacao", "fluxo", "processo"] },
    { id: "builder", name: "Visual Builder", description: "Criar workflow visual", icon: Icons.builder, action: () => router.push("/workflows/builder"), keywords: ["drag", "drop", "visual", "editor"] },
    { id: "hitl", name: "HITL", description: "Human-in-the-Loop", icon: Icons.hitl, action: () => router.push("/hitl"), keywords: ["revisao", "humano", "aprovacao"] },
    { id: "domains", name: "Domínios", description: "Domínios especializados", icon: Icons.domains, action: () => router.push("/domains"), keywords: ["geo", "data", "devops", "finance", "legal"] },
    { id: "rag-query", name: "RAG Query", description: "Busca semântica em documentos", icon: Icons.rag, action: () => router.push("/rag/query"), keywords: ["busca", "search", "documentos"] },
    { id: "rag-ingest", name: "RAG Ingest", description: "Adicionar documentos", icon: Icons.rag, action: () => router.push("/rag/ingest"), keywords: ["upload", "adicionar", "importar"] },
    { id: "editor", name: "Editor de Código", description: "Editor Monaco integrado", icon: Icons.code, action: () => router.push("/editor"), keywords: ["codigo", "programar", "monaco"] },
    { id: "templates", name: "Templates", description: "Templates de workflows prontos", icon: Icons.template, action: () => router.push("/workflows/templates"), keywords: ["pronto", "modelo", "exemplo"] },
    { id: "logs", name: "Logs", description: "Histórico de execuções", icon: Icons.logs, action: () => router.push("/logs"), keywords: ["historico", "execucoes", "erro"] },
    { id: "settings", name: "Configurações", description: "Preferências e conta", icon: Icons.settings, action: () => router.push("/settings"), keywords: ["config", "perfil", "conta", "preferencias"] },
    { id: "help", name: "Ajuda", description: "Central de ajuda e FAQ", icon: Icons.help, action: () => router.push("/help"), keywords: ["faq", "suporte", "duvidas"] },
    { id: "theme-toggle", name: "Alternar Tema", description: "Claro / Escuro", icon: Icons.sun, action: () => { document.documentElement.classList.toggle("dark"); localStorage.setItem("theme", document.documentElement.classList.contains("dark") ? "dark" : "light"); }, keywords: ["dark", "light", "escuro", "claro"] },
    { id: "logout", name: "Sair", description: "Encerrar sessão", icon: Icons.logout, action: () => { localStorage.clear(); window.location.href = "/"; }, keywords: ["logout", "desconectar", "sair"] },
  ];

  const filteredCommands = query
    ? commands.filter(cmd => {
        const q = query.toLowerCase();
        return cmd.name.toLowerCase().includes(q) ||
               cmd.description?.toLowerCase().includes(q) ||
               cmd.keywords?.some(k => k.includes(q));
      })
    : commands;

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Cmd+K ou Ctrl+K para abrir
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      setIsOpen(prev => !prev);
      setQuery("");
      setSelectedIndex(0);
    }
    // Escape para fechar
    if (e.key === "Escape" && isOpen) {
      setIsOpen(false);
    }
  }, [isOpen]);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const executeCommand = (cmd: Command) => {
    cmd.action();
    setIsOpen(false);
    setQuery("");
  };

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, filteredCommands.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === "Enter" && filteredCommands[selectedIndex]) {
      e.preventDefault();
      executeCommand(filteredCommands[selectedIndex]);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={() => setIsOpen(false)}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-start justify-center p-4 pt-[15vh]">
        <div className="relative w-full max-w-xl bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-slate-700 overflow-hidden animate-scale-in">
          {/* Search Input */}
          <div className="flex items-center gap-3 px-4 border-b border-gray-100 dark:border-slate-700">
            <span className="text-gray-400">{Icons.search}</span>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleInputKeyDown}
              placeholder="Digite um comando ou busque..."
              className="flex-1 py-4 bg-transparent outline-none text-gray-800 dark:text-gray-200 placeholder-gray-400"
            />
            <kbd className="hidden sm:inline-flex px-2 py-1 text-xs font-medium text-gray-400 bg-gray-100 dark:bg-slate-700 rounded">
              ESC
            </kbd>
          </div>

          {/* Commands List */}
          <div className="max-h-[300px] overflow-y-auto p-2">
            {filteredCommands.length === 0 ? (
              <div className="py-8 text-center text-gray-500 dark:text-gray-400">
                Nenhum comando encontrado
              </div>
            ) : (
              <div className="space-y-1">
                {filteredCommands.map((cmd, index) => (
                  <button
                    key={cmd.id}
                    onClick={() => executeCommand(cmd)}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-colors ${
                      selectedIndex === index
                        ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700"
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      selectedIndex === index
                        ? "bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400"
                        : "bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-gray-400"
                    }`}>
                      {cmd.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{cmd.name}</div>
                      {cmd.description && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {cmd.description}
                        </div>
                      )}
                    </div>
                    {cmd.shortcut && (
                      <kbd className="px-2 py-1 text-xs font-medium text-gray-400 bg-gray-100 dark:bg-slate-700 rounded">
                        {cmd.shortcut}
                      </kbd>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-3 border-t border-gray-100 dark:border-slate-700 flex items-center justify-between text-xs text-gray-400">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-slate-700 rounded">↑</kbd>
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-slate-700 rounded">↓</kbd>
                <span className="ml-1">Navegar</span>
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-slate-700 rounded">↵</kbd>
                <span className="ml-1">Selecionar</span>
              </span>
            </div>
            <span className="hidden sm:inline">
              <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-slate-700 rounded">⌘</kbd>
              <span className="mx-1">+</span>
              <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-slate-700 rounded">K</kbd>
              <span className="ml-1">para abrir</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
