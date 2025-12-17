"use client";

import React, { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { useAuth } from "../store/auth";
import { useTheme } from "../providers/ThemeProvider";
import Sidebar from "./Sidebar";
import NotificationCenter from "./NotificationCenter";
import { CommandPalette, useCommandPalette } from "./ui/command-palette";

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { token, hydrate, isHydrated } = useAuth();
  const pathname = usePathname();
  const { resolvedTheme, toggleTheme } = useTheme();
  const { open: commandPaletteOpen, setOpen: setCommandPaletteOpen } = useCommandPalette();
  const [mounted, setMounted] = useState(false);

  // Hydrate auth state on mount to avoid SSR mismatch
  useEffect(() => {
    hydrate();
    setMounted(true);
  }, [hydrate]);

  // Páginas públicas (sem sidebar)
  const isPublicPage = pathname === "/" || pathname === "/login";

  // Prevent hydration mismatch - show nothing until mounted
  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="animate-pulse text-slate-500">Carregando...</div>
      </div>
    );
  }

  // Se não estiver logado ou for página pública, mostra layout simples
  if (!token || isPublicPage) {
    return <>{children}</>;
  }

  // Layout com sidebar para usuários autenticados
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 transition-colors">
      <Sidebar />
      <main className="pl-64">
        {/* Header */}
        <header className="h-16 bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700 flex items-center justify-between px-8 sticky top-0 z-30 transition-colors">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {getPageTitle(pathname)}
            </h2>
          </div>
          <div className="flex items-center gap-3">
            {/* Theme Toggle */}
            <button 
              onClick={toggleTheme}
              className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" 
              title={resolvedTheme === "dark" ? "Modo claro" : "Modo escuro"} 
              aria-label="Alternar tema"
            >
              {resolvedTheme === "dark" ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
            {/* Command Palette Trigger */}
            <button 
              onClick={() => document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }))}
              className="flex items-center gap-2 px-3 py-1.5 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 rounded-lg transition-colors text-sm" 
              title="Buscar (⌘K)" 
              aria-label="Abrir busca"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <span className="hidden md:inline">Buscar...</span>
              <kbd className="hidden md:inline px-1.5 py-0.5 text-xs font-medium bg-white dark:bg-slate-800 rounded">⌘K</kbd>
            </button>
            {/* Notifications */}
            <NotificationCenter />
          </div>
        </header>

        {/* Content */}
        <div className="p-8 animate-fade-in">
          {children}
        </div>
      </main>

      {/* Command Palette */}
      <CommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />
    </div>
  );
}

function getPageTitle(pathname: string | null): string {
  if (!pathname) return "Dashboard";
  
  const titles: Record<string, string> = {
    "/dashboard": "Dashboard",
    "/chat": "Chat com Agentes",
    "/agents": "Agentes",
    "/teams": "Times",
    "/workflows": "Workflows",
    "/domains": "Domínios",
    "/domains/geo": "Domínio Geo",
    "/domains/finance": "Domínio Finance",
    "/domains/data": "Domínio Data",
    "/domains/devops": "Domínio DevOps",
    "/domains/legal": "Domínio Legal",
    "/domains/corporate": "Domínio Corporate",
    "/editor": "Editor",
    "/rag/query": "RAG Query",
    "/rag/ingest": "RAG Ingest",
    "/rag/collections": "Coleções RAG",
    "/hitl": "Human-in-the-Loop",
  };

  return titles[pathname] || "Agno Platform";
}
