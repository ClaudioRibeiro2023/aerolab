"use client";
import React, { useState } from "react";
import { agentTemplates, categories, type AgentTemplate } from "../lib/agentTemplates";
import { Badge } from "./Badge";

interface AgentTemplateSelectorProps {
  onSelect: (template: AgentTemplate) => void;
}

export default function AgentTemplateSelector({ onSelect }: AgentTemplateSelectorProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredTemplates = agentTemplates.filter(template => {
    const matchesCategory = !selectedCategory || template.category === selectedCategory;
    const matchesSearch = !searchQuery || 
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.useCases.some(uc => uc.toLowerCase().includes(searchQuery.toLowerCase()));
    
    return matchesCategory && matchesSearch;
  });

  const getDifficultyVariant = (difficulty: string) => {
    switch (difficulty) {
      case "easy":
        return "success" as const;
      case "medium":
        return "warning" as const;
      case "advanced":
        return "error" as const;
      default:
        return "neutral" as const;
    }
  };

  const getDifficultyLabel = (difficulty: string) => {
    switch (difficulty) {
      case "easy":
        return "Fácil";
      case "medium":
        return "Médio";
      case "advanced":
        return "Avançado";
      default:
        return difficulty;
    }
  };

  const getCategoryColor = (categoryId: string) => {
    const cat = categories.find(c => c.id === categoryId);
    const colors: Record<string, string> = {
      blue: "from-blue-500 to-blue-600",
      purple: "from-purple-500 to-purple-600",
      green: "from-green-500 to-green-600",
      orange: "from-orange-500 to-orange-600",
      red: "from-red-500 to-red-600",
      indigo: "from-indigo-500 to-indigo-600",
    };
    return colors[cat?.color || "blue"];
  };

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="relative">
        <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Buscar templates por nome, descrição ou caso de uso..."
          className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
        />
      </div>

      {/* Category Filters */}
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`px-4 py-2 rounded-xl font-medium whitespace-nowrap transition-all ${
            !selectedCategory
              ? "bg-blue-500 text-white shadow-lg shadow-blue-500/25"
              : "bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-700"
          }`}
        >
          Todos
        </button>
        {categories.map((category) => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.id)}
            className={`px-4 py-2 rounded-xl font-medium whitespace-nowrap transition-all flex items-center gap-2 ${
              selectedCategory === category.id
                ? "bg-blue-500 text-white shadow-lg shadow-blue-500/25"
                : "bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-700"
            }`}
          >
            <span>{category.icon}</span>
            <span>{category.name}</span>
          </button>
        ))}
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-500 dark:text-gray-400">
        {filteredTemplates.length} template{filteredTemplates.length !== 1 ? "s" : ""} encontrado{filteredTemplates.length !== 1 ? "s" : ""}
      </div>

      {/* Templates Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTemplates.map((template) => (
          <button
            key={template.id}
            onClick={() => onSelect(template)}
            className="group relative p-6 bg-white dark:bg-slate-800 rounded-2xl border-2 border-gray-100 dark:border-slate-700 hover:border-blue-500 dark:hover:border-blue-500 text-left transition-all hover:shadow-xl hover:-translate-y-1"
          >
            {/* Icon */}
            <div className={`absolute top-4 right-4 w-14 h-14 rounded-xl bg-gradient-to-br ${getCategoryColor(template.category)} flex items-center justify-center text-3xl shadow-lg opacity-90 group-hover:opacity-100 transition-opacity`}>
              {template.icon}
            </div>

            {/* Header */}
            <div className="mb-4 pr-16">
              <h3 className="font-semibold text-gray-900 dark:text-white text-lg group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {template.name}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                {template.description}
              </p>
            </div>

            {/* Badges */}
            <div className="flex flex-wrap gap-2 mb-4">
              <Badge variant={getDifficultyVariant(template.difficulty)}>
                {getDifficultyLabel(template.difficulty)}
              </Badge>
              <Badge variant="neutral">
                ⏱️ {template.estimatedTime}
              </Badge>
              {template.useRAG && (
                <Badge variant="info" className="flex items-center gap-1">
                  📚 RAG
                </Badge>
              )}
              {template.useHITL && (
                <Badge variant="warning" className="flex items-center gap-1">
                  👤 HITL
                </Badge>
              )}
            </div>

            {/* Use Cases */}
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Casos de uso:</p>
              <div className="flex flex-wrap gap-1">
                {template.useCases.slice(0, 2).map((useCase, idx) => (
                  <span key={idx} className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-slate-900 px-2 py-0.5 rounded">
                    {useCase}
                  </span>
                ))}
                {template.useCases.length > 2 && (
                  <span className="text-xs text-gray-400">
                    +{template.useCases.length - 2}
                  </span>
                )}
              </div>
            </div>

            {/* Hover Effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
          </button>
        ))}
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center text-4xl">
            🔍
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Nenhum template encontrado
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Tente ajustar os filtros ou termo de busca
          </p>
          <button
            onClick={() => {
              setSearchQuery("");
              setSelectedCategory(null);
            }}
            className="btn-secondary"
          >
            Limpar Filtros
          </button>
        </div>
      )}
    </div>
  );
}
