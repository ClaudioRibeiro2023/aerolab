"use client";

import React, { useState, useEffect, useCallback, createContext, useContext } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ChevronRight, ChevronLeft, Check, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================
// TYPES
// ============================================================

interface TutorialStep {
  id: string;
  title: string;
  content: string;
  target?: string; // CSS selector for highlight
  position?: "top" | "bottom" | "left" | "right";
  action?: string; // Action description
  completed?: boolean;
}

interface Tutorial {
  id: string;
  name: string;
  description: string;
  steps: TutorialStep[];
}

interface TutorialContextValue {
  activeTutorial: Tutorial | null;
  currentStep: number;
  startTutorial: (tutorial: Tutorial) => void;
  nextStep: () => void;
  prevStep: () => void;
  endTutorial: () => void;
  skipTutorial: () => void;
  completedTutorials: string[];
}

// ============================================================
// CONTEXT
// ============================================================

const TutorialContext = createContext<TutorialContextValue | null>(null);

export function useTutorial() {
  const context = useContext(TutorialContext);
  if (!context) {
    throw new Error("useTutorial must be used within TutorialProvider");
  }
  return context;
}

// ============================================================
// PROVIDER
// ============================================================

interface TutorialProviderProps {
  children: React.ReactNode;
}

export function TutorialProvider({ children }: TutorialProviderProps) {
  const [activeTutorial, setActiveTutorial] = useState<Tutorial | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [completedTutorials, setCompletedTutorials] = useState<string[]>([]);

  // Load completed tutorials from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("agno-completed-tutorials");
    if (saved) {
      setCompletedTutorials(JSON.parse(saved));
    }
  }, []);

  const startTutorial = useCallback((tutorial: Tutorial) => {
    setActiveTutorial(tutorial);
    setCurrentStep(0);
  }, []);

  const nextStep = useCallback(() => {
    if (!activeTutorial) return;
    if (currentStep < activeTutorial.steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      // Complete tutorial
      const newCompleted = [...completedTutorials, activeTutorial.id];
      setCompletedTutorials(newCompleted);
      localStorage.setItem("agno-completed-tutorials", JSON.stringify(newCompleted));
      setActiveTutorial(null);
      setCurrentStep(0);
    }
  }, [activeTutorial, currentStep, completedTutorials]);

  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [currentStep]);

  const endTutorial = useCallback(() => {
    if (activeTutorial) {
      const newCompleted = [...completedTutorials, activeTutorial.id];
      setCompletedTutorials(newCompleted);
      localStorage.setItem("agno-completed-tutorials", JSON.stringify(newCompleted));
    }
    setActiveTutorial(null);
    setCurrentStep(0);
  }, [activeTutorial, completedTutorials]);

  const skipTutorial = useCallback(() => {
    setActiveTutorial(null);
    setCurrentStep(0);
  }, []);

  return (
    <TutorialContext.Provider
      value={{
        activeTutorial,
        currentStep,
        startTutorial,
        nextStep,
        prevStep,
        endTutorial,
        skipTutorial,
        completedTutorials,
      }}
    >
      {children}
      <TutorialOverlay />
    </TutorialContext.Provider>
  );
}

// ============================================================
// OVERLAY
// ============================================================

function TutorialOverlay() {
  const { activeTutorial, currentStep, nextStep, prevStep, skipTutorial } = useTutorial();
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  // Get target element position
  useEffect(() => {
    if (!activeTutorial) return;

    const step = activeTutorial.steps[currentStep];
    if (step.target) {
      const element = document.querySelector(step.target);
      if (element) {
        const rect = element.getBoundingClientRect();
        setTargetRect(rect);
        
        // Scroll element into view
        element.scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        setTargetRect(null);
      }
    } else {
      setTargetRect(null);
    }
  }, [activeTutorial, currentStep]);

  if (!activeTutorial) return null;

  const step = activeTutorial.steps[currentStep];
  const isLastStep = currentStep === activeTutorial.steps.length - 1;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[200]"
      >
        {/* Backdrop with cutout */}
        <div className="absolute inset-0">
          <svg className="w-full h-full">
            <defs>
              <mask id="tutorial-mask">
                <rect width="100%" height="100%" fill="white" />
                {targetRect && (
                  <rect
                    x={targetRect.left - 8}
                    y={targetRect.top - 8}
                    width={targetRect.width + 16}
                    height={targetRect.height + 16}
                    rx="8"
                    fill="black"
                  />
                )}
              </mask>
            </defs>
            <rect
              width="100%"
              height="100%"
              fill="rgba(0, 0, 0, 0.75)"
              mask="url(#tutorial-mask)"
            />
          </svg>
        </div>

        {/* Highlight ring around target */}
        {targetRect && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="absolute pointer-events-none"
            style={{
              left: targetRect.left - 8,
              top: targetRect.top - 8,
              width: targetRect.width + 16,
              height: targetRect.height + 16,
            }}
          >
            <div className="absolute inset-0 rounded-lg border-2 border-blue-500 animate-pulse" />
            <div className="absolute inset-0 rounded-lg bg-blue-500/10" />
          </motion.div>
        )}

        {/* Tooltip */}
        <TutorialTooltip
          step={step}
          currentStep={currentStep}
          totalSteps={activeTutorial.steps.length}
          targetRect={targetRect}
          onNext={nextStep}
          onPrev={prevStep}
          onSkip={skipTutorial}
          isLastStep={isLastStep}
        />
      </motion.div>
    </AnimatePresence>
  );
}

// ============================================================
// TOOLTIP
// ============================================================

interface TutorialTooltipProps {
  step: TutorialStep;
  currentStep: number;
  totalSteps: number;
  targetRect: DOMRect | null;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
  isLastStep: boolean;
}

function TutorialTooltip({
  step,
  currentStep,
  totalSteps,
  targetRect,
  onNext,
  onPrev,
  onSkip,
  isLastStep,
}: TutorialTooltipProps) {
  const position = step.position || "bottom";
  
  // Calculate tooltip position
  const getTooltipStyle = (): React.CSSProperties => {
    if (!targetRect) {
      return {
        left: "50%",
        top: "50%",
        transform: "translate(-50%, -50%)",
      };
    }

    const padding = 16;
    
    switch (position) {
      case "top":
        return {
          left: targetRect.left + targetRect.width / 2,
          top: targetRect.top - padding,
          transform: "translate(-50%, -100%)",
        };
      case "bottom":
        return {
          left: targetRect.left + targetRect.width / 2,
          top: targetRect.bottom + padding,
          transform: "translateX(-50%)",
        };
      case "left":
        return {
          left: targetRect.left - padding,
          top: targetRect.top + targetRect.height / 2,
          transform: "translate(-100%, -50%)",
        };
      case "right":
        return {
          left: targetRect.right + padding,
          top: targetRect.top + targetRect.height / 2,
          transform: "translateY(-50%)",
        };
      default:
        return {};
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="absolute w-80 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-4"
      style={getTooltipStyle()}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-blue-500/20 rounded-lg">
            <Sparkles className="w-4 h-4 text-blue-400" />
          </div>
          <span className="text-xs text-slate-400">
            Passo {currentStep + 1} de {totalSteps}
          </span>
        </div>
        <button
          onClick={onSkip}
          className="p-1 text-slate-400 hover:text-white"
          title="Pular tutorial"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <h3 className="text-lg font-semibold text-white mb-2">{step.title}</h3>
      <p className="text-sm text-slate-300 mb-4">{step.content}</p>

      {/* Action hint */}
      {step.action && (
        <div className="mb-4 p-2 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <p className="text-xs text-blue-400">💡 {step.action}</p>
        </div>
      )}

      {/* Progress dots */}
      <div className="flex items-center justify-center gap-1.5 mb-4">
        {Array.from({ length: totalSteps }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "w-1.5 h-1.5 rounded-full transition-colors",
              i === currentStep ? "bg-blue-500" : "bg-slate-600"
            )}
          />
        ))}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={onPrev}
          disabled={currentStep === 0}
          className={cn(
            "flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors",
            currentStep === 0
              ? "text-slate-600 cursor-not-allowed"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          )}
        >
          <ChevronLeft className="w-4 h-4" />
          Anterior
        </button>

        <button
          onClick={onNext}
          className="flex items-center gap-1 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          {isLastStep ? (
            <>
              Concluir
              <Check className="w-4 h-4" />
            </>
          ) : (
            <>
              Próximo
              <ChevronRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </motion.div>
  );
}

// ============================================================
// PREDEFINED TUTORIALS
// ============================================================

export const TUTORIALS = {
  gettingStarted: {
    id: "getting-started",
    name: "Primeiros Passos",
    description: "Aprenda os conceitos básicos da plataforma AGNO",
    steps: [
      {
        id: "welcome",
        title: "Bem-vindo ao AGNO!",
        content: "Esta é sua plataforma de agentes de IA. Vamos fazer um tour rápido pelos recursos principais.",
        position: "bottom" as const,
      },
      {
        id: "sidebar",
        title: "Menu de Navegação",
        content: "Use a barra lateral para navegar entre as diferentes seções da plataforma.",
        target: "[data-tutorial='sidebar']",
        position: "right" as const,
      },
      {
        id: "agents",
        title: "Agentes",
        content: "Crie e gerencie seus agentes de IA. Cada agente pode ter um propósito específico.",
        target: "[data-tutorial='agents']",
        position: "right" as const,
      },
      {
        id: "teams",
        title: "Times",
        content: "Agrupe agentes em times para trabalhos colaborativos complexos.",
        target: "[data-tutorial='teams']",
        position: "right" as const,
      },
      {
        id: "workflows",
        title: "Workflows",
        content: "Automatize tarefas criando fluxos de trabalho visuais.",
        target: "[data-tutorial='workflows']",
        position: "right" as const,
      },
      {
        id: "command-palette",
        title: "Atalho Rápido",
        content: "Pressione Cmd+K (ou Ctrl+K) para abrir a paleta de comandos a qualquer momento.",
        action: "Experimente: pressione Cmd+K agora!",
        position: "bottom" as const,
      },
    ],
  },

  createAgent: {
    id: "create-agent",
    name: "Criar Primeiro Agente",
    description: "Aprenda a criar seu primeiro agente de IA",
    steps: [
      {
        id: "intro",
        title: "Criando um Agente",
        content: "Agentes são assistentes de IA especializados. Vamos criar um!",
      },
      {
        id: "name",
        title: "Nome do Agente",
        content: "Escolha um nome descritivo para seu agente, como 'Assistente de Vendas'.",
        target: "[data-tutorial='agent-name']",
        position: "bottom" as const,
      },
      {
        id: "model",
        title: "Modelo de IA",
        content: "Selecione o modelo que irá alimentar seu agente. GPT-4 é recomendado para tarefas complexas.",
        target: "[data-tutorial='agent-model']",
        position: "bottom" as const,
      },
      {
        id: "instructions",
        title: "Instruções",
        content: "Defina a personalidade e comportamento do agente através das instruções do sistema.",
        target: "[data-tutorial='agent-instructions']",
        position: "bottom" as const,
      },
      {
        id: "done",
        title: "Pronto!",
        content: "Clique em Salvar para criar seu agente. Ele estará pronto para uso imediatamente.",
        action: "Clique em 'Criar Agente' para finalizar",
      },
    ],
  },
};

export default {
  TutorialProvider,
  useTutorial,
  TUTORIALS,
};
