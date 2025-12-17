"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface Step {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  action?: { label: string; href: string };
}

const Icons = {
  wave: (<svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11" /></svg>),
  agent: (<svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>),
  team: (<svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>),
  workflow: (<svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" /></svg>),
  chat: (<svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>),
  check: (<svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  x: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>),
  arrow: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>),
};

const steps: Step[] = [
  {
    id: "welcome",
    title: "Bem-vindo ao AeroLab! 👋",
    description: "A plataforma multi-agente de IA que vai transformar a forma como você trabalha. Vamos configurar tudo em poucos passos.",
    icon: Icons.wave,
  },
  {
    id: "agents",
    title: "Conheça os Agentes",
    description: "Agentes são assistentes de IA especializados. Você pode usar os pré-configurados ou criar os seus próprios com instruções personalizadas.",
    icon: Icons.agent,
    action: { label: "Ver Agentes", href: "/agents" },
  },
  {
    id: "teams",
    title: "Monte seu Time",
    description: "Combine múltiplos agentes em times para resolver tarefas complexas. Cada agente contribui com sua especialidade.",
    icon: Icons.team,
    action: { label: "Criar Time", href: "/teams" },
  },
  {
    id: "workflows",
    title: "Automatize com Workflows",
    description: "Crie fluxos de trabalho automatizados conectando agentes em sequência. Use o Visual Builder para desenhar seus processos.",
    icon: Icons.workflow,
    action: { label: "Visual Builder", href: "/workflows/builder" },
  },
  {
    id: "chat",
    title: "Converse com seus Agentes",
    description: "Use a interface de chat para interagir diretamente com qualquer agente. Faça perguntas, peça análises ou gere conteúdo.",
    icon: Icons.chat,
    action: { label: "Abrir Chat", href: "/chat" },
  },
  {
    id: "done",
    title: "Tudo Pronto! 🎉",
    description: "Você está pronto para começar. Use ⌘K (ou Ctrl+K) para navegar rapidamente. Explore os Domínios especializados para funcionalidades avançadas.",
    icon: Icons.check,
  },
];

export default function OnboardingWizard() {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const router = useRouter();

  useEffect(() => {
    const hasSeenOnboarding = localStorage.getItem("aerolab_onboarding_completed");
    if (!hasSeenOnboarding) {
      const timer = setTimeout(() => setIsOpen(true), 500);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    localStorage.setItem("agno_onboarding_completed", "true");
    setIsOpen(false);
  };

  const handleSkip = () => {
    localStorage.setItem("agno_onboarding_completed", "true");
    setIsOpen(false);
  };

  const handleAction = (href: string) => {
    localStorage.setItem("agno_onboarding_completed", "true");
    setIsOpen(false);
    router.push(href);
  };

  if (!isOpen) return null;

  const step = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={handleSkip} />

      {/* Modal */}
      <div className="relative w-full max-w-lg bg-white dark:bg-slate-800 rounded-3xl shadow-2xl overflow-hidden animate-scale-in">
        {/* Progress bar */}
        <div className="h-1 bg-gray-200 dark:bg-slate-700">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Close button */}
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          title="Pular introdução"
        >
          {Icons.x}
        </button>

        {/* Content */}
        <div className="p-8 text-center">
          {/* Step indicator */}
          <div className="flex justify-center gap-2 mb-6">
            {steps.map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full transition-all ${
                  i === currentStep
                    ? "w-6 bg-blue-500"
                    : i < currentStep
                    ? "bg-blue-500"
                    : "bg-gray-300 dark:bg-slate-600"
                }`}
              />
            ))}
          </div>

          {/* Icon */}
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-lg">
            {step.icon}
          </div>

          {/* Title */}
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
            {step.title}
          </h2>

          {/* Description */}
          <p className="text-gray-600 dark:text-gray-400 mb-8 leading-relaxed">
            {step.description}
          </p>

          {/* Action button */}
          {step.action && (
            <button
              onClick={() => handleAction(step.action!.href)}
              className="mb-4 px-6 py-2.5 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-xl font-medium hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
            >
              {step.action.label} →
            </button>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between gap-4">
            <button
              onClick={handlePrev}
              disabled={currentStep === 0}
              className={`px-6 py-2.5 rounded-xl font-medium transition-colors ${
                currentStep === 0
                  ? "text-gray-400 cursor-not-allowed"
                  : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-700"
              }`}
            >
              ← Anterior
            </button>

            <button
              onClick={handleNext}
              className="flex-1 px-6 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
            >
              {currentStep === steps.length - 1 ? "Começar" : "Próximo"}
              {Icons.arrow}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
