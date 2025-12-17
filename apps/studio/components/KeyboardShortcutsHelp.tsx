"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Shortcut {
  keys: string[];
  description: string;
  category: string;
}

const shortcuts: Shortcut[] = [
  // Global
  { keys: ["Ctrl", "K"], description: "Abrir Command Palette", category: "Global" },
  { keys: ["Ctrl", "Shift", "P"], description: "Toggle Performance Monitor", category: "Global" },
  { keys: ["?"], description: "Mostrar atalhos de teclado", category: "Global" },
  
  // Chat
  { keys: ["Ctrl", "F"], description: "Buscar mensagens", category: "Chat" },
  { keys: ["Ctrl", "L"], description: "Limpar conversa", category: "Chat" },
  { keys: ["Ctrl", "/"], description: "Focar input", category: "Chat" },
  { keys: ["Esc"], description: "Cancelar streaming / Limpar input", category: "Chat" },
  { keys: ["Enter"], description: "Enviar mensagem", category: "Chat" },
  { keys: ["Shift", "Enter"], description: "Nova linha", category: "Chat" },
  
  // Navigation
  { keys: ["G", "D"], description: "Ir para Dashboard", category: "Navegação" },
  { keys: ["G", "C"], description: "Ir para Chat", category: "Navegação" },
  { keys: ["G", "A"], description: "Ir para Agentes", category: "Navegação" },
  { keys: ["G", "H"], description: "Ir para Health", category: "Navegação" },
];

export default function KeyboardShortcutsHelp() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // ? key to toggle help
      if (e.key === "?" && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const activeElement = document.activeElement;
        const isInput = activeElement?.tagName === "INPUT" || 
                       activeElement?.tagName === "TEXTAREA" ||
                       (activeElement as HTMLElement)?.isContentEditable;
        if (!isInput) {
          e.preventDefault();
          setIsOpen(prev => !prev);
        }
      }
      // Escape to close
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  const categories = [...new Set(shortcuts.map(s => s.category))];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
                <div>
                  <h2 className="text-xl font-semibold text-white">Atalhos de Teclado</h2>
                  <p className="text-sm text-slate-400">Pressione ? para abrir/fechar</p>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Content */}
              <div className="p-6 overflow-y-auto max-h-[60vh] space-y-6">
                {categories.map(category => (
                  <div key={category}>
                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
                      {category}
                    </h3>
                    <div className="space-y-2">
                      {shortcuts
                        .filter(s => s.category === category)
                        .map((shortcut, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-slate-700/50 transition-colors"
                          >
                            <span className="text-slate-300">{shortcut.description}</span>
                            <div className="flex items-center gap-1">
                              {shortcut.keys.map((key, i) => (
                                <span key={i}>
                                  <kbd className="px-2 py-1 bg-slate-900 border border-slate-600 rounded text-xs font-mono text-slate-300">
                                    {key}
                                  </kbd>
                                  {i < shortcut.keys.length - 1 && (
                                    <span className="text-slate-500 mx-1">+</span>
                                  )}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-slate-700 bg-slate-800/50">
                <p className="text-xs text-slate-500 text-center">
                  Dica: Use <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-400">Ctrl+K</kbd> para abrir a Command Palette
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
