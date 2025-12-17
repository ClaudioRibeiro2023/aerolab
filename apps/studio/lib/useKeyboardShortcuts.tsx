"use client";

import { useEffect, useCallback } from "react";

interface ShortcutAction {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description: string;
}

interface UseKeyboardShortcutsOptions {
  enabled?: boolean;
}

/**
 * Hook para gerenciar atalhos de teclado
 */
export function useKeyboardShortcuts(
  shortcuts: ShortcutAction[],
  options: UseKeyboardShortcutsOptions = {}
) {
  const { enabled = true } = options;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      const target = event.target as HTMLElement;
      const isInput = target.tagName === "INPUT" || target.tagName === "TEXTAREA";
      
      for (const shortcut of shortcuts) {
        const ctrlMatch = shortcut.ctrl ? (event.ctrlKey || event.metaKey) : !event.ctrlKey && !event.metaKey;
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const altMatch = shortcut.alt ? event.altKey : !event.altKey;
        const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase();

        if (ctrlMatch && shiftMatch && altMatch && keyMatch) {
          if (isInput && !(shortcut.ctrl && shortcut.key === "Enter")) {
            if (!(shortcut.ctrl && shortcut.key === "k")) {
              continue;
            }
          }
          
          event.preventDefault();
          shortcut.action();
          return;
        }
      }
    },
    [shortcuts, enabled]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}

// Atalhos padrão do chat
export const defaultChatShortcuts = {
  send: { key: "Enter", ctrl: true, description: "Enviar mensagem" },
  search: { key: "k", ctrl: true, description: "Buscar agente" },
  clear: { key: "l", ctrl: true, description: "Limpar chat" },
  newChat: { key: "n", ctrl: true, description: "Nova conversa" },
  escape: { key: "Escape", description: "Fechar modal" },
  help: { key: "/", ctrl: true, description: "Mostrar atalhos" },
};

// Componente de ajuda de atalhos
export function ShortcutHelpContent() {
  const shortcuts = [
    { keys: "Ctrl + Enter", description: "Enviar mensagem" },
    { keys: "Ctrl + K", description: "Buscar/trocar agente" },
    { keys: "Ctrl + L", description: "Limpar histórico do chat" },
    { keys: "Ctrl + N", description: "Nova conversa" },
    { keys: "Ctrl + /", description: "Mostrar esta ajuda" },
    { keys: "Escape", description: "Fechar modal/menu" },
  ];

  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
        Atalhos de Teclado
      </h3>
      <div className="grid gap-2">
        {shortcuts.map((s, i) => (
          <div key={i} className="flex items-center justify-between py-1">
            <span className="text-sm text-gray-600 dark:text-gray-300">
              {s.description}
            </span>
            <kbd className="px-2 py-1 text-xs font-mono bg-gray-100 dark:bg-slate-700 rounded border border-gray-200 dark:border-slate-600">
              {s.keys}
            </kbd>
          </div>
        ))}
      </div>
    </div>
  );
}
