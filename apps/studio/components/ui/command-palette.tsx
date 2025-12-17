"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Search,
  Bot,
  Users,
  Workflow,
  Database,
  Settings,
  HelpCircle,
  Plus,
  LayoutDashboard,
  MessageSquare,
  Code,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface CommandItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  shortcut?: string;
  action: () => void;
  category: string;
}

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const router = useRouter();

  const commands: CommandItem[] = [
    // Quick Actions
    {
      id: "new-agent",
      label: "Novo Agente",
      icon: <Plus className="w-4 h-4" />,
      shortcut: "⌘N",
      action: () => router.push("/agents/new"),
      category: "Ações Rápidas",
    },
    {
      id: "new-team",
      label: "Novo Time",
      icon: <Users className="w-4 h-4" />,
      shortcut: "⌘T",
      action: () => router.push("/teams/new"),
      category: "Ações Rápidas",
    },
    {
      id: "new-workflow",
      label: "Novo Workflow",
      icon: <Workflow className="w-4 h-4" />,
      shortcut: "⌘⇧N",
      action: () => router.push("/workflows/builder"),
      category: "Ações Rápidas",
    },
    // Navigation
    {
      id: "dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard className="w-4 h-4" />,
      shortcut: "⌘1",
      action: () => router.push("/dashboard"),
      category: "Navegação",
    },
    {
      id: "agents",
      label: "Agentes",
      icon: <Bot className="w-4 h-4" />,
      shortcut: "⌘2",
      action: () => router.push("/agents"),
      category: "Navegação",
    },
    {
      id: "teams",
      label: "Times",
      icon: <Users className="w-4 h-4" />,
      shortcut: "⌘3",
      action: () => router.push("/teams"),
      category: "Navegação",
    },
    {
      id: "workflows",
      label: "Workflows",
      icon: <Workflow className="w-4 h-4" />,
      shortcut: "⌘4",
      action: () => router.push("/workflows"),
      category: "Navegação",
    },
    {
      id: "domains",
      label: "Domínios",
      icon: <Database className="w-4 h-4" />,
      shortcut: "⌘5",
      action: () => router.push("/domains"),
      category: "Navegação",
    },
    {
      id: "chat",
      label: "Chat",
      icon: <MessageSquare className="w-4 h-4" />,
      action: () => router.push("/chat"),
      category: "Navegação",
    },
    {
      id: "flow-studio",
      label: "Flow Studio",
      icon: <Sparkles className="w-4 h-4" />,
      action: () => router.push("/flow-studio"),
      category: "Navegação",
    },
    {
      id: "editor",
      label: "Editor de Código",
      icon: <Code className="w-4 h-4" />,
      action: () => router.push("/editor"),
      category: "Navegação",
    },
    // Settings
    {
      id: "settings",
      label: "Configurações",
      icon: <Settings className="w-4 h-4" />,
      shortcut: "⌘,",
      action: () => router.push("/settings"),
      category: "Sistema",
    },
    {
      id: "help",
      label: "Ajuda",
      icon: <HelpCircle className="w-4 h-4" />,
      shortcut: "?",
      action: () => router.push("/help"),
      category: "Sistema",
    },
  ];

  const filteredCommands = query
    ? commands.filter((cmd) =>
        cmd.label.toLowerCase().includes(query.toLowerCase())
      )
    : commands;

  const groupedCommands = filteredCommands.reduce((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = [];
    acc[cmd.category].push(cmd);
    return acc;
  }, {} as Record<string, CommandItem[]>);

  const flatCommands = Object.values(groupedCommands).flat();

  const executeCommand = useCallback((cmd: CommandItem) => {
    cmd.action();
    onOpenChange(false);
    setQuery("");
    setSelectedIndex(0);
  }, [onOpenChange]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!open) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((i) => Math.min(i + 1, flatCommands.length - 1));
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((i) => Math.max(i - 1, 0));
          break;
        case "Enter":
          e.preventDefault();
          if (flatCommands[selectedIndex]) {
            executeCommand(flatCommands[selectedIndex]);
          }
          break;
        case "Escape":
          e.preventDefault();
          onOpenChange(false);
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, selectedIndex, flatCommands, executeCommand, onOpenChange]);

  // Reset on open
  useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIndex(0);
    }
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => onOpenChange(false)}
          />

          {/* Palette */}
          <motion.div
            className="relative w-full max-w-2xl mx-4 bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-2xl shadow-2xl overflow-hidden"
            initial={{ scale: 0.95, y: -20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.95, y: -20 }}
            transition={{ duration: 0.15 }}
          >
            {/* Search Input */}
            <div className="flex items-center gap-3 px-4 border-b border-slate-800">
              <Search className="w-5 h-5 text-slate-400" />
              <input
                className="flex-1 py-4 bg-transparent text-white placeholder-slate-400 focus:outline-none text-base"
                placeholder="Buscar comandos, páginas, ações..."
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setSelectedIndex(0);
                }}
                autoFocus
              />
              <kbd className="px-2 py-1 text-xs text-slate-400 bg-slate-800 rounded border border-slate-700">
                ESC
              </kbd>
            </div>

            {/* Results */}
            <div className="max-h-[400px] overflow-y-auto p-2">
              {Object.entries(groupedCommands).map(([category, items]) => (
                <div key={category} className="mb-4 last:mb-0">
                  <p className="px-3 py-2 text-xs font-medium text-slate-500 uppercase tracking-wider">
                    {category}
                  </p>
                  <div className="space-y-1">
                    {items.map((item) => {
                      const isSelected = flatCommands[selectedIndex]?.id === item.id;
                      return (
                        <button
                          key={item.id}
                          className={cn(
                            "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors",
                            isSelected
                              ? "bg-blue-600 text-white"
                              : "text-slate-300 hover:bg-slate-800"
                          )}
                          onClick={() => executeCommand(item)}
                          onMouseEnter={() =>
                            setSelectedIndex(flatCommands.indexOf(item))
                          }
                        >
                          <span
                            className={cn(
                              "p-1.5 rounded-md",
                              isSelected ? "bg-blue-500" : "bg-slate-800"
                            )}
                          >
                            {item.icon}
                          </span>
                          <span className="flex-1 font-medium">{item.label}</span>
                          {item.shortcut && (
                            <kbd
                              className={cn(
                                "px-2 py-0.5 text-xs rounded",
                                isSelected
                                  ? "bg-blue-500 text-white"
                                  : "bg-slate-800 text-slate-400"
                              )}
                            >
                              {item.shortcut}
                            </kbd>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              {filteredCommands.length === 0 && (
                <div className="py-12 text-center text-slate-400">
                  <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Nenhum resultado para &quot;{query}&quot;</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800 text-xs text-slate-500">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-slate-800 rounded">↑↓</kbd>
                  navegar
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-slate-800 rounded">↵</kbd>
                  selecionar
                </span>
              </div>
              <span>AGNO Command Palette</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Hook para abrir o command palette com Cmd+K
export function useCommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return { open, setOpen };
}

export default CommandPalette;
