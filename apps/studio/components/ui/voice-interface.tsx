"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Volume2, Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================
// TYPES
// ============================================================

interface VoiceCommand {
  transcript: string;
  confidence: number;
  timestamp: Date;
}

interface VoiceInterfaceState {
  isListening: boolean;
  isProcessing: boolean;
  transcript: string;
  error: string | null;
  isSupported: boolean;
}

// ============================================================
// VOICE RECOGNITION HOOK
// ============================================================

export function useVoiceRecognition() {
  const [state, setState] = useState<VoiceInterfaceState>({
    isListening: false,
    isProcessing: false,
    transcript: "",
    error: null,
    isSupported: false,
  });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check for browser support
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognitionAPI) {
      setState((prev) => ({ ...prev, isSupported: true }));
      
      const recognition = new SpeechRecognitionAPI();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = "pt-BR";

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          .map((result: any) => result[0].transcript)
          .join("");
        
        setState((prev) => ({ ...prev, transcript }));
      };

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onerror = (event: any) => {
        setState((prev) => ({
          ...prev,
          error: event.error,
          isListening: false,
        }));
      };

      recognition.onend = () => {
        setState((prev) => ({ ...prev, isListening: false }));
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  const startListening = useCallback(() => {
    if (recognitionRef.current && state.isSupported) {
      setState((prev) => ({ ...prev, isListening: true, error: null, transcript: "" }));
      recognitionRef.current.start();
    }
  }, [state.isSupported]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setState((prev) => ({ ...prev, isListening: false }));
    }
  }, []);

  const resetTranscript = useCallback(() => {
    setState((prev) => ({ ...prev, transcript: "" }));
  }, []);

  return {
    ...state,
    startListening,
    stopListening,
    resetTranscript,
  };
}

// ============================================================
// VOICE COMMAND PROCESSOR
// ============================================================

interface VoiceCommandMapping {
  patterns: RegExp[];
  action: string;
  params?: Record<string, string>;
}

const VOICE_COMMANDS: VoiceCommandMapping[] = [
  {
    patterns: [/abrir dashboard/i, /ir para dashboard/i, /mostrar dashboard/i],
    action: "navigate",
    params: { path: "/dashboard" },
  },
  {
    patterns: [/criar agente/i, /novo agente/i],
    action: "navigate",
    params: { path: "/agents/new" },
  },
  {
    patterns: [/criar time/i, /novo time/i, /criar equipe/i],
    action: "navigate",
    params: { path: "/teams/new" },
  },
  {
    patterns: [/abrir chat/i, /ir para chat/i],
    action: "navigate",
    params: { path: "/chat" },
  },
  {
    patterns: [/abrir domínios/i, /ir para domínios/i],
    action: "navigate",
    params: { path: "/domains" },
  },
  {
    patterns: [/abrir configurações/i, /ir para configurações/i],
    action: "navigate",
    params: { path: "/settings" },
  },
  {
    patterns: [/modo escuro/i, /tema escuro/i, /dark mode/i],
    action: "theme",
    params: { theme: "dark" },
  },
  {
    patterns: [/modo claro/i, /tema claro/i, /light mode/i],
    action: "theme",
    params: { theme: "light" },
  },
  {
    patterns: [/ajuda/i, /help/i, /comandos/i],
    action: "help",
  },
];

export function processVoiceCommand(transcript: string): {
  action: string;
  params?: Record<string, string>;
  matched: boolean;
} {
  for (const command of VOICE_COMMANDS) {
    for (const pattern of command.patterns) {
      if (pattern.test(transcript)) {
        return {
          action: command.action,
          params: command.params,
          matched: true,
        };
      }
    }
  }

  return { action: "unknown", matched: false };
}

// ============================================================
// VOICE BUTTON COMPONENT
// ============================================================

interface VoiceButtonProps {
  onCommand?: (command: { action: string; params?: Record<string, string> }) => void;
  className?: string;
  size?: "sm" | "md" | "lg";
}

const buttonSizes = {
  sm: "w-10 h-10",
  md: "w-12 h-12",
  lg: "w-16 h-16",
};

export function VoiceButton({ onCommand, className, size = "md" }: VoiceButtonProps) {
  const {
    isListening,
    isSupported,
    transcript,
    error,
    startListening,
    stopListening,
  } = useVoiceRecognition();

  const [showFeedback, setShowFeedback] = useState(false);
  const [lastCommand, setLastCommand] = useState<string>("");

  useEffect(() => {
    if (transcript && !isListening) {
      const result = processVoiceCommand(transcript);
      setLastCommand(transcript);
      setShowFeedback(true);
      
      if (result.matched && onCommand) {
        onCommand({ action: result.action, params: result.params });
      }
      
      // Hide feedback after 3 seconds
      const timeout = setTimeout(() => setShowFeedback(false), 3000);
      return () => clearTimeout(timeout);
    }
  }, [transcript, isListening, onCommand]);

  if (!isSupported) {
    return (
      <button
        className={cn(
          "rounded-full bg-slate-800 text-slate-500 flex items-center justify-center cursor-not-allowed",
          buttonSizes[size],
          className
        )}
        disabled
        title="Reconhecimento de voz não suportado"
      >
        <MicOff className="w-5 h-5" />
      </button>
    );
  }

  return (
    <div className="relative">
      <motion.button
        className={cn(
          "rounded-full flex items-center justify-center transition-all",
          isListening
            ? "bg-red-500 text-white shadow-lg shadow-red-500/30"
            : "bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white",
          buttonSizes[size],
          className
        )}
        whileTap={{ scale: 0.95 }}
        onClick={() => (isListening ? stopListening() : startListening())}
      >
        {isListening ? (
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ repeat: Infinity, duration: 1 }}
          >
            <Mic className="w-5 h-5" />
          </motion.div>
        ) : (
          <Mic className="w-5 h-5" />
        )}
      </motion.button>

      {/* Listening indicator */}
      <AnimatePresence>
        {isListening && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute -top-2 -right-2"
          >
            <span className="flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-4 w-4 bg-red-500" />
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Feedback popup */}
      <AnimatePresence>
        {showFeedback && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.9 }}
            className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 px-4 py-2 bg-slate-800 rounded-lg shadow-xl text-sm whitespace-nowrap"
          >
            <div className="text-slate-400 text-xs mb-1">Você disse:</div>
            <div className="text-white">{lastCommand}</div>
            {error && <div className="text-red-400 text-xs mt-1">{error}</div>}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================
// VOICE COMMANDS PANEL
// ============================================================

interface VoiceCommandsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function VoiceCommandsPanel({ isOpen, onClose }: VoiceCommandsPanelProps) {
  const commands = [
    { category: "Navegação", items: ["Abrir dashboard", "Ir para agentes", "Abrir chat", "Ir para domínios"] },
    { category: "Ações", items: ["Criar agente", "Novo time", "Criar workflow"] },
    { category: "Tema", items: ["Modo escuro", "Modo claro"] },
    { category: "Sistema", items: ["Ajuda", "Configurações"] },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            className="bg-slate-900 rounded-2xl p-6 max-w-lg w-full mx-4 shadow-2xl border border-slate-800"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <Volume2 className="w-5 h-5 text-blue-400" />
                </div>
                <h2 className="text-xl font-semibold text-white">Comandos de Voz</h2>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
                aria-label="Fechar comandos de voz"
                title="Fechar"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {commands.map((category) => (
                <div key={category.category}>
                  <h3 className="text-sm font-medium text-slate-400 mb-2">
                    {category.category}
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {category.items.map((item) => (
                      <span
                        key={item}
                        className="px-3 py-1.5 bg-slate-800 rounded-full text-sm text-slate-300"
                      >
                        "{item}"
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 p-4 bg-slate-800/50 rounded-xl">
              <p className="text-sm text-slate-400">
                Dica: Clique no botão de microfone e fale um comando. 
                O reconhecimento funciona melhor em português brasileiro.
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default {
  useVoiceRecognition,
  processVoiceCommand,
  VoiceButton,
  VoiceCommandsPanel,
};
