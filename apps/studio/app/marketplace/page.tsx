"use client";
import React, { useState, useEffect } from "react";
import Protected from "../../components/Protected";
import Link from "next/link";
import { toast } from "sonner";
import api from "../../lib/api";

interface MarketplaceAgent {
  id: string;
  name: string;
  description: string;
  author: string;
  category: string;
  icon: string;
  rating: number;
  reviews: number;
  downloads: number;
  price: "free" | "premium";
  tags: string[];
  verified: boolean;
  featured: boolean;
  createdAt: string;
  config: {
    model: string;
    tools: string[];
    skills: string[];
  };
}

const Icons = {
  search: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>),
  star: (<svg className="w-4 h-4 fill-current" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>),
  download: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>),
  check: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>),
  plus: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>),
  upload: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>),
};

const categories = [
  { id: "all", name: "Todos", icon: "🌐" },
  { id: "productivity", name: "Produtividade", icon: "📊" },
  { id: "business", name: "Negócios", icon: "💼" },
  { id: "content", name: "Conteúdo", icon: "✍️" },
  { id: "support", name: "Suporte", icon: "💬" },
  { id: "development", name: "Desenvolvimento", icon: "💻" },
  { id: "data", name: "Dados", icon: "📈" },
];

// Mock data
const mockAgents: MarketplaceAgent[] = [
  {
    id: "1",
    name: "Super Researcher Pro",
    description: "Agente de pesquisa avançado com acesso a múltiplas fontes e síntese automática de informações.",
    author: "AgnoLabs",
    category: "productivity",
    icon: "🔬",
    rating: 4.8,
    reviews: 127,
    downloads: 2340,
    price: "free",
    tags: ["research", "synthesis", "AI"],
    verified: true,
    featured: true,
    createdAt: "2024-01-15",
    config: { model: "gpt-5.1", tools: ["tavily", "web_scraper"], skills: ["summarize", "data_insights"] }
  },
  {
    id: "2",
    name: "Code Wizard",
    description: "Assistente de programação com geração, review e documentação automática de código.",
    author: "DevTools Inc",
    category: "development",
    icon: "🧙",
    rating: 4.9,
    reviews: 89,
    downloads: 1890,
    price: "premium",
    tags: ["coding", "review", "documentation"],
    verified: true,
    featured: true,
    createdAt: "2024-02-20",
    config: { model: "gpt-5.1-codex-max", tools: ["github", "code_analyzer"], skills: ["code_generation", "code_review"] }
  },
  {
    id: "3",
    name: "Customer Success Bot",
    description: "Agente de suporte com escalação inteligente e base de conhecimento integrada.",
    author: "SupportAI",
    category: "support",
    icon: "🤝",
    rating: 4.6,
    reviews: 203,
    downloads: 3120,
    price: "free",
    tags: ["support", "HITL", "RAG"],
    verified: true,
    featured: false,
    createdAt: "2024-03-10",
    config: { model: "gemini-2.5-flash", tools: ["knowledge_base", "ticketing"], skills: ["sentiment_analysis"] }
  },
  {
    id: "4",
    name: "Financial Analyst Pro",
    description: "Análise financeira automatizada com forecasts, métricas e recomendações.",
    author: "FinTech Solutions",
    category: "business",
    icon: "💰",
    rating: 4.7,
    reviews: 56,
    downloads: 890,
    price: "premium",
    tags: ["finance", "analysis", "forecasting"],
    verified: false,
    featured: false,
    createdAt: "2024-04-05",
    config: { model: "claude-sonnet-4.5", tools: ["calculator", "data_viz"], skills: ["data_insights", "step_by_step"] }
  },
  {
    id: "5",
    name: "Content Creator Suite",
    description: "Suite completa para criação de conteúdo: blog, social media, SEO.",
    author: "MarketingAI",
    category: "content",
    icon: "🎨",
    rating: 4.5,
    reviews: 178,
    downloads: 2670,
    price: "free",
    tags: ["content", "SEO", "social"],
    verified: true,
    featured: true,
    createdAt: "2024-01-28",
    config: { model: "gpt-5.1", tools: ["seo_analyzer", "image_gen"], skills: ["summarize"] }
  },
  {
    id: "6",
    name: "Data Pipeline Manager",
    description: "Orquestra pipelines de dados com monitoramento e alertas automáticos.",
    author: "DataOps Team",
    category: "data",
    icon: "🔄",
    rating: 4.4,
    reviews: 34,
    downloads: 456,
    price: "premium",
    tags: ["data", "pipeline", "monitoring"],
    verified: false,
    featured: false,
    createdAt: "2024-05-12",
    config: { model: "gpt-5.1", tools: ["supabase", "zapier"], skills: ["data_insights"] }
  },
];

function AgentCard({ agent, onInstall }: { agent: MarketplaceAgent; onInstall: () => void }) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 overflow-hidden hover:shadow-lg transition-shadow">
      {agent.featured && (
        <div className="bg-gradient-to-r from-blue-500 to-purple-500 text-white text-xs text-center py-1 font-medium">
          ⭐ Em Destaque
        </div>
      )}
      
      <div className="p-5">
        <div className="flex items-start gap-3 mb-3">
          <span className="text-3xl">{agent.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900 dark:text-white truncate">{agent.name}</h3>
              {agent.verified && (
                <span className="flex-shrink-0 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center" title="Verificado">
                  <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500">por {agent.author}</p>
          </div>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
            agent.price === "free" 
              ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
              : "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400"
          }`}>
            {agent.price === "free" ? "Grátis" : "Premium"}
          </span>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">{agent.description}</p>

        <div className="flex flex-wrap gap-1 mb-3">
          {agent.tags.slice(0, 3).map(tag => (
            <span key={tag} className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 rounded-full">
              {tag}
            </span>
          ))}
        </div>

        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 text-yellow-500">
              {Icons.star}
              <span className="text-gray-700 dark:text-gray-300">{agent.rating}</span>
              <span className="text-gray-400">({agent.reviews})</span>
            </span>
            <span className="flex items-center gap-1 text-gray-500">
              {Icons.download}
              {agent.downloads.toLocaleString()}
            </span>
          </div>
          
          <button 
            onClick={onInstall}
            className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-1"
          >
            {Icons.plus} Instalar
          </button>
        </div>
      </div>
    </div>
  );
}

export default function MarketplacePage() {
  const [agents, setAgents] = useState<MarketplaceAgent[]>(mockAgents);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [priceFilter, setPriceFilter] = useState<"all" | "free" | "premium">("all");
  const [sortBy, setSortBy] = useState<"popular" | "rating" | "recent">("popular");
  const [loading, setLoading] = useState(false);

  const filteredAgents = agents
    .filter(a => {
      if (category !== "all" && a.category !== category) return false;
      if (priceFilter !== "all" && a.price !== priceFilter) return false;
      if (search && !a.name.toLowerCase().includes(search.toLowerCase()) && 
          !a.description.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === "popular") return b.downloads - a.downloads;
      if (sortBy === "rating") return b.rating - a.rating;
      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
    });

  const handleInstall = async (agent: MarketplaceAgent) => {
    try {
      setLoading(true);
      // Simular instalação
      await new Promise(r => setTimeout(r, 1000));
      toast.success(`${agent.name} instalado com sucesso!`);
    } catch (e) {
      toast.error("Erro ao instalar agente");
    } finally {
      setLoading(false);
    }
  };

  const featuredAgents = agents.filter(a => a.featured);

  return (
    <Protected>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Marketplace de Agentes</h1>
            <p className="text-gray-500 dark:text-gray-400">Descubra e instale agentes prontos para uso</p>
          </div>
          
          <Link href="/marketplace/publish" className="btn-primary flex items-center gap-2 w-fit">
            {Icons.upload} Publicar Agente
          </Link>
        </div>

        {/* Search and Filters */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-gray-100 dark:border-slate-700">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">{Icons.search}</span>
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Buscar agentes..."
                className="input-modern pl-10"
              />
            </div>
            
            {/* Price Filter */}
            <select
              value={priceFilter}
              onChange={e => setPriceFilter(e.target.value as any)}
              className="input-modern w-40"
            >
              <option value="all">Todos os preços</option>
              <option value="free">Grátis</option>
              <option value="premium">Premium</option>
            </select>
            
            {/* Sort */}
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as any)}
              className="input-modern w-40"
            >
              <option value="popular">Mais populares</option>
              <option value="rating">Melhor avaliados</option>
              <option value="recent">Mais recentes</option>
            </select>
          </div>
        </div>

        {/* Categories */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setCategory(cat.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl whitespace-nowrap transition-colors ${
                category === cat.id
                  ? "bg-blue-500 text-white"
                  : "bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-slate-600 hover:border-blue-500"
              }`}
            >
              <span>{cat.icon}</span>
              <span className="font-medium">{cat.name}</span>
            </button>
          ))}
        </div>

        {/* Featured Section */}
        {category === "all" && featuredAgents.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">⭐ Em Destaque</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {featuredAgents.map(agent => (
                <AgentCard key={agent.id} agent={agent} onInstall={() => handleInstall(agent)} />
              ))}
            </div>
          </div>
        )}

        {/* All Agents */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {category === "all" ? "Todos os Agentes" : categories.find(c => c.id === category)?.name}
            <span className="ml-2 text-sm font-normal text-gray-500">({filteredAgents.length})</span>
          </h2>
          
          {filteredAgents.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <span className="text-4xl block mb-4">🔍</span>
              <p>Nenhum agente encontrado</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredAgents.filter(a => !a.featured || category !== "all").map(agent => (
                <AgentCard key={agent.id} agent={agent} onInstall={() => handleInstall(agent)} />
              ))}
            </div>
          )}
        </div>
      </div>
    </Protected>
  );
}
