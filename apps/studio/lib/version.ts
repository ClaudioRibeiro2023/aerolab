/**
 * AGNO Platform - Version Management System
 * 
 * Tracks all module versions and changelog
 */

export interface ModuleVersion {
  name: string;
  version: string;
  lastUpdate: string;
  features: string[];
  status: 'stable' | 'beta' | 'alpha';
}

export interface ChangelogEntry {
  version: string;
  date: string;
  type: 'feature' | 'fix' | 'improvement' | 'breaking';
  module: string;
  description: string;
}

// Platform version
export const PLATFORM_VERSION = "5.1.0";
export const PLATFORM_BUILD = "2024.12.08.3";
export const LAST_UPDATE = "2024-12-08T10:00:00-03:00";

// Module versions
export const MODULE_VERSIONS: ModuleVersion[] = [
  {
    name: "Design System",
    version: "5.1.0",
    lastUpdate: "2024-12-08T10:00:00-03:00",
    features: [
      "25+ Premium Components",
      "Gradient Mesh Backgrounds",
      "Animated Charts (6 tipos)",
      "AI Assistant Widget",
      "Interactive Tutorials",
      "Gamification System",
      "Theme Studio",
      "Activity Feed Real-time",
      "Bottom Navigation Mobile",
      "Toast Premium Notifications"
    ],
    status: 'stable'
  },
  {
    name: "Domain Studio",
    version: "3.5.0",
    lastUpdate: "2024-12-08T08:20:00-03:00",
    features: [
      "15 Domínios Especializados",
      "Agentic RAG Engine",
      "GraphRAG + Neo4j",
      "Compliance Engine (30+ regs)",
      "MultiModal Processing",
      "Workflow Engine",
      "Analytics Engine",
      "MCP + A2A Protocols"
    ],
    status: 'stable'
  },
  {
    name: "Flow Studio",
    version: "2.0.0",
    lastUpdate: "2024-12-01T10:00:00-03:00",
    features: [
      "60+ Node Types",
      "Visual Workflow Builder",
      "NL to Workflow",
      "AI Optimization",
      "Real-time Execution"
    ],
    status: 'stable'
  },
  {
    name: "Team Orchestrator",
    version: "2.0.0",
    lastUpdate: "2024-12-05T14:30:00-03:00",
    features: [
      "15+ Orchestration Modes",
      "20+ Agent Personas",
      "NL Team Builder",
      "Agent Learning",
      "Conflict Resolution"
    ],
    status: 'stable'
  },
  {
    name: "Dashboard",
    version: "1.5.0",
    lastUpdate: "2024-11-28T09:00:00-03:00",
    features: [
      "Real-time Metrics",
      "Agent Monitoring",
      "Cost Tracking",
      "Performance Analytics"
    ],
    status: 'stable'
  },
  {
    name: "RAG System",
    version: "2.0.0",
    lastUpdate: "2024-12-08T08:20:00-03:00",
    features: [
      "Multi-format Ingestion",
      "Hybrid Search",
      "Collections Management",
      "Agentic RAG"
    ],
    status: 'stable'
  },
  {
    name: "Agents API",
    version: "1.8.0",
    lastUpdate: "2024-11-25T16:00:00-03:00",
    features: [
      "Agent CRUD",
      "Tool Integration",
      "Memory Management",
      "Multi-provider"
    ],
    status: 'stable'
  },
  {
    name: "Chat System",
    version: "1.6.0",
    lastUpdate: "2024-11-20T11:00:00-03:00",
    features: [
      "Conversational AI",
      "Memory Persistence",
      "Multi-agent Chat",
      "Streaming"
    ],
    status: 'stable'
  }
];

// Changelog
export const CHANGELOG: ChangelogEntry[] = [
  {
    version: "5.1.0",
    date: "2024-12-08",
    type: "feature",
    module: "Design System",
    description: "Sprint Longo: Gamification completo, Theme Studio, Real-time Activity Feed"
  },
  {
    version: "5.1.0",
    date: "2024-12-08",
    type: "feature",
    module: "Design System",
    description: "Sprint Médio: AI Assistant Widget, Interactive Tutorials, Bottom Navigation Mobile"
  },
  {
    version: "5.1.0",
    date: "2024-12-08",
    type: "feature",
    module: "Design System",
    description: "Sprint Curto: Gradient Mesh Backgrounds, Toast Premium, Animated Charts (6 tipos)"
  },
  {
    version: "5.0.0",
    date: "2024-12-08",
    type: "feature",
    module: "Design System",
    description: "Design System v5.0 ULTIMATE - GlassCard, GradientButton, BentoGrid, Command Palette"
  },
  {
    version: "5.0.0",
    date: "2024-12-08",
    type: "feature",
    module: "Design System",
    description: "Animated Background components: Particles, Spotlight, BorderBeam, GradientOrb"
  },
  {
    version: "5.0.0",
    date: "2024-12-08",
    type: "feature",
    module: "Design System",
    description: "Command Palette com Cmd+K - navegação e ações rápidas"
  },
  {
    version: "3.5.0",
    date: "2024-12-08",
    type: "feature",
    module: "Domain Studio",
    description: "Domain Studio v3.5 ULTIMATE - 15 domínios, Agentic RAG, GraphRAG, Compliance, MultiModal"
  },
  {
    version: "3.5.0",
    date: "2024-12-08",
    type: "feature",
    module: "Domain Studio",
    description: "Legal Domain com 6 agentes especializados e 3 workflows"
  },
  {
    version: "3.5.0",
    date: "2024-12-08",
    type: "feature",
    module: "Domain Studio",
    description: "Compliance Engine com 30+ regulamentações (LGPD, CVM, OAB, ANVISA, GDPR, HIPAA)"
  },
  {
    version: "3.5.0",
    date: "2024-12-08",
    type: "feature",
    module: "Domain Studio",
    description: "MCP Protocol e A2A Protocol para comunicação entre agentes"
  },
  {
    version: "2.0.0",
    date: "2024-12-05",
    type: "feature",
    module: "Team Orchestrator",
    description: "Team Orchestrator v2.0 com 15+ modos de orquestração"
  },
  {
    version: "2.0.0",
    date: "2024-12-01",
    type: "feature",
    module: "Flow Studio",
    description: "Flow Studio v2.0 com 60+ tipos de nós e NL to Workflow"
  },
  {
    version: "1.5.0",
    date: "2024-11-28",
    type: "improvement",
    module: "Dashboard",
    description: "Dashboard com métricas em tempo real e monitoramento de agentes"
  }
];

// Helper functions
export function formatDate(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function getLatestUpdate(): string {
  return formatDate(LAST_UPDATE);
}

export function getModuleByName(name: string): ModuleVersion | undefined {
  return MODULE_VERSIONS.find(m => m.name.toLowerCase().includes(name.toLowerCase()));
}

export function getRecentChanges(limit: number = 5): ChangelogEntry[] {
  return CHANGELOG.slice(0, limit);
}
