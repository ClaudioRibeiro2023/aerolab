"use client";
import React from "react";

export interface AgentProfile {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  recommended_provider: string;
  recommended_model: string;
  use_cases: string[];
  characteristics: {
    speed: number; // 1-5
    quality: number; // 1-5
    cost: number; // 1-5 (1=cheap, 5=expensive)
  };
}

export const agentProfiles: AgentProfile[] = [
  {
    id: "fast",
    name: "Rápido & Econômico",
    description: "Respostas rápidas com custo otimizado. Ideal para alto volume.",
    icon: "⚡",
    color: "green",
    recommended_provider: "google_gemini",
    recommended_model: "gemini-2.5-flash",
    use_cases: ["Chatbots", "Triagem", "Tarefas simples"],
    characteristics: { speed: 5, quality: 3, cost: 1 }
  },
  {
    id: "balanced",
    name: "Equilibrado",
    description: "Melhor custo-benefício para uso geral.",
    icon: "⚖️",
    color: "blue",
    recommended_provider: "openai",
    recommended_model: "gpt-5.1",
    use_cases: ["Assistentes", "Atendimento", "Automação"],
    characteristics: { speed: 4, quality: 4, cost: 3 }
  },
  {
    id: "powerful",
    name: "Máxima Qualidade",
    description: "Modelos frontier para tarefas complexas e críticas.",
    icon: "🧠",
    color: "purple",
    recommended_provider: "anthropic",
    recommended_model: "claude-opus-4.5",
    use_cases: ["Análise profunda", "Decisões críticas", "Research"],
    characteristics: { speed: 2, quality: 5, cost: 5 }
  },
  {
    id: "coding",
    name: "Especialista em Código",
    description: "Otimizado para desenvolvimento, review e documentação.",
    icon: "💻",
    color: "orange",
    recommended_provider: "openai",
    recommended_model: "gpt-5.1-codex-max",
    use_cases: ["Code review", "Geração de código", "Debugging"],
    characteristics: { speed: 3, quality: 5, cost: 4 }
  },
  {
    id: "reasoning",
    name: "Raciocínio Profundo",
    description: "Para problemas que exigem análise step-by-step.",
    icon: "🔬",
    color: "indigo",
    recommended_provider: "openai",
    recommended_model: "o3-pro",
    use_cases: ["Matemática", "Lógica", "Planejamento"],
    characteristics: { speed: 1, quality: 5, cost: 5 }
  },
  {
    id: "custom",
    name: "Personalizado",
    description: "Configure manualmente todos os parâmetros.",
    icon: "🎛️",
    color: "gray",
    recommended_provider: "openai",
    recommended_model: "gpt-5.1",
    use_cases: ["Configuração avançada"],
    characteristics: { speed: 3, quality: 3, cost: 3 }
  }
];

interface Props {
  selected: string;
  onSelect: (profile: AgentProfile) => void;
}

const colorClasses: Record<string, { border: string; bg: string; text: string }> = {
  green: { 
    border: "border-green-500", 
    bg: "bg-green-50 dark:bg-green-900/20", 
    text: "text-green-600 dark:text-green-400" 
  },
  blue: { 
    border: "border-blue-500", 
    bg: "bg-blue-50 dark:bg-blue-900/20", 
    text: "text-blue-600 dark:text-blue-400" 
  },
  purple: { 
    border: "border-purple-500", 
    bg: "bg-purple-50 dark:bg-purple-900/20", 
    text: "text-purple-600 dark:text-purple-400" 
  },
  orange: { 
    border: "border-orange-500", 
    bg: "bg-orange-50 dark:bg-orange-900/20", 
    text: "text-orange-600 dark:text-orange-400" 
  },
  indigo: { 
    border: "border-indigo-500", 
    bg: "bg-indigo-50 dark:bg-indigo-900/20", 
    text: "text-indigo-600 dark:text-indigo-400" 
  },
  gray: { 
    border: "border-gray-500", 
    bg: "bg-gray-50 dark:bg-gray-900/20", 
    text: "text-gray-600 dark:text-gray-400" 
  },
};

function MetricBar({ value, label, color }: { value: number; label: string; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 text-gray-500 dark:text-gray-400">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-200 dark:bg-slate-600 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all ${
            color === "green" ? "bg-green-500" :
            color === "blue" ? "bg-blue-500" :
            color === "purple" ? "bg-purple-500" :
            color === "orange" ? "bg-orange-500" :
            color === "indigo" ? "bg-indigo-500" :
            "bg-gray-500"
          }`}
          style={{ width: `${value * 20}%` }}
        />
      </div>
    </div>
  );
}

export default function AgentProfileSelector({ selected, onSelect }: Props) {
  return (
    <div className="space-y-4">
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agentProfiles.map((profile) => {
          const isSelected = selected === profile.id;
          const colors = colorClasses[profile.color] || colorClasses.gray;
          
          return (
            <button
              key={profile.id}
              type="button"
              onClick={() => onSelect(profile)}
              className={`p-4 rounded-2xl border-2 text-left transition-all hover:shadow-md ${
                isSelected
                  ? `${colors.border} ${colors.bg}`
                  : "border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500"
              }`}
            >
              {/* Header */}
              <div className="flex items-start gap-3 mb-3">
                <span className="text-2xl">{profile.icon}</span>
                <div className="flex-1">
                  <h3 className={`font-semibold ${isSelected ? colors.text : "text-gray-900 dark:text-white"}`}>
                    {profile.name}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {profile.description}
                  </p>
                </div>
              </div>

              {/* Use Cases Tags */}
              <div className="flex flex-wrap gap-1 mb-3">
                {profile.use_cases.slice(0, 3).map((uc, i) => (
                  <span 
                    key={i}
                    className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300"
                  >
                    {uc}
                  </span>
                ))}
              </div>

              {/* Metrics */}
              {profile.id !== "custom" && (
                <div className="space-y-1.5 pt-2 border-t border-gray-100 dark:border-slate-700">
                  <MetricBar value={profile.characteristics.speed} label="Velocidade" color={profile.color} />
                  <MetricBar value={profile.characteristics.quality} label="Qualidade" color={profile.color} />
                  <MetricBar value={6 - profile.characteristics.cost} label="Economia" color={profile.color} />
                </div>
              )}

              {/* Selected indicator */}
              {isSelected && (
                <div className={`mt-3 text-xs ${colors.text} font-medium flex items-center gap-1`}>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Selecionado
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
