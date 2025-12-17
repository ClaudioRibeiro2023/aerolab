"use client";
import React from "react";

export interface AgentTool {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: "research" | "devops" | "database" | "communication" | "finance" | "productivity";
  requires_api_key?: string;
  recommended_for?: string[];
}

export const availableTools: AgentTool[] = [
  // Research
  {
    id: "tavily",
    name: "Tavily Search",
    description: "Busca web otimizada para AI com resultados estruturados",
    icon: "🔍",
    category: "research",
    requires_api_key: "TAVILY_API_KEY",
    recommended_for: ["market-researcher", "competitor-monitor", "blog-writer"]
  },
  {
    id: "web_scraper",
    name: "Web Scraper",
    description: "Extrai dados de páginas web",
    icon: "🕷️",
    category: "research",
    recommended_for: ["market-researcher", "competitor-monitor"]
  },
  // DevOps
  {
    id: "github",
    name: "GitHub",
    description: "Gerencia repositórios, issues e pull requests",
    icon: "🐙",
    category: "devops",
    requires_api_key: "GITHUB_TOKEN",
    recommended_for: ["code-reviewer", "documentation-generator"]
  },
  {
    id: "netlify",
    name: "Netlify",
    description: "Deploy e gerenciamento de sites",
    icon: "🚀",
    category: "devops",
    requires_api_key: "NETLIFY_TOKEN"
  },
  {
    id: "supabase",
    name: "Supabase",
    description: "Banco de dados PostgreSQL e autenticação",
    icon: "⚡",
    category: "database",
    requires_api_key: "SUPABASE_URL"
  },
  // Communication
  {
    id: "gmail",
    name: "Gmail",
    description: "Lê e envia emails via Gmail API",
    icon: "📧",
    category: "communication",
    requires_api_key: "GOOGLE_CREDENTIALS",
    recommended_for: ["email-manager"]
  },
  {
    id: "slack",
    name: "Slack",
    description: "Envia mensagens e gerencia canais",
    icon: "💬",
    category: "communication",
    requires_api_key: "SLACK_TOKEN"
  },
  {
    id: "notion",
    name: "Notion",
    description: "Gerencia páginas e databases do Notion",
    icon: "📝",
    category: "productivity",
    requires_api_key: "NOTION_TOKEN"
  },
  {
    id: "google_calendar",
    name: "Google Calendar",
    description: "Agenda e gerencia eventos",
    icon: "📅",
    category: "productivity",
    requires_api_key: "GOOGLE_CREDENTIALS",
    recommended_for: ["meeting-scheduler"]
  },
  {
    id: "zapier",
    name: "Zapier",
    description: "Conecta com 5000+ apps via webhooks",
    icon: "🔗",
    category: "productivity",
    requires_api_key: "ZAPIER_WEBHOOK_URL",
    recommended_for: ["task-automator"]
  },
  // Finance
  {
    id: "calculator",
    name: "Calculadora",
    description: "Cálculos matemáticos e financeiros",
    icon: "🧮",
    category: "finance",
    recommended_for: ["financial-analyst", "data-analyst"]
  },
  {
    id: "data_viz",
    name: "Visualizador de Dados",
    description: "Gera gráficos e visualizações",
    icon: "📊",
    category: "finance",
    recommended_for: ["data-analyst", "financial-analyst"]
  }
];

const categoryLabels: Record<string, { label: string; color: string }> = {
  research: { label: "Pesquisa", color: "blue" },
  devops: { label: "DevOps", color: "green" },
  database: { label: "Database", color: "purple" },
  communication: { label: "Comunicação", color: "orange" },
  finance: { label: "Finanças", color: "emerald" },
  productivity: { label: "Produtividade", color: "indigo" },
};

interface Props {
  selected: string[];
  onToggle: (toolId: string) => void;
  recommendedFor?: string; // template ID to highlight recommended tools
}

export default function AgentToolsSelector({ selected, onToggle, recommendedFor }: Props) {
  const groupedTools = availableTools.reduce((acc, tool) => {
    if (!acc[tool.category]) acc[tool.category] = [];
    acc[tool.category].push(tool);
    return acc;
  }, {} as Record<string, AgentTool[]>);

  return (
    <div className="space-y-6">
      {Object.entries(groupedTools).map(([category, tools]) => {
        const catInfo = categoryLabels[category];
        
        return (
          <div key={category}>
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full bg-${catInfo.color}-500`} />
              {catInfo.label}
            </h3>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
              {tools.map((tool) => {
                const isSelected = selected.includes(tool.id);
                const isRecommended = recommendedFor && tool.recommended_for?.includes(recommendedFor);
                
                return (
                  <button
                    key={tool.id}
                    type="button"
                    onClick={() => onToggle(tool.id)}
                    className={`p-3 rounded-xl border-2 text-left transition-all relative ${
                      isSelected
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                        : "border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500"
                    }`}
                  >
                    {/* Recommended badge */}
                    {isRecommended && !isSelected && (
                      <span className="absolute -top-2 -right-2 text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-400">
                        Recomendado
                      </span>
                    )}
                    
                    <div className="flex items-start gap-3">
                      <span className="text-xl">{tool.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className={`font-medium ${isSelected ? "text-blue-700 dark:text-blue-300" : "text-gray-900 dark:text-white"}`}>
                            {tool.name}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">
                          {tool.description}
                        </p>
                        
                        {tool.requires_api_key && (
                          <div className="flex items-center gap-1 mt-2 text-xs text-amber-600 dark:text-amber-400">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                            </svg>
                            Requer API Key
                          </div>
                        )}
                      </div>
                      
                      {/* Checkbox */}
                      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                        isSelected 
                          ? "bg-blue-500 border-blue-500" 
                          : "border-gray-300 dark:border-slate-500"
                      }`}>
                        {isSelected && (
                          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
      
      {selected.length > 0 && (
        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            <strong>{selected.length}</strong> ferramenta{selected.length > 1 ? "s" : ""} selecionada{selected.length > 1 ? "s" : ""}
          </p>
        </div>
      )}
    </div>
  );
}
