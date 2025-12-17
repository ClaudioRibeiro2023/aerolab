"use client";
import React, { useState, useMemo } from "react";
import Protected from "../../../components/Protected";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { workflowTemplates, workflowCategories, searchTemplates } from "../../../lib/workflowTemplates";
import { WorkflowTemplate, STEP_TYPE_META, ORCHESTRATION_PATTERN_META } from "../../../lib/workflowTypes";
import { Bot, GitBranch, GitFork, Repeat, Users, Zap, Play, Square, Clock, Database, PenTool, Headphones, BarChart2, Calendar, Webhook, MessageCircle, FileText, CheckCircle, Layers, Heart, Link2, ArrowLeft, Star, Eye, Plus, Sparkles, Search, Grid } from "lucide-react";

const Icons: Record<string, React.ReactNode> = {
  Database: <Database className="w-5 h-5" />,
  PenTool: <PenTool className="w-5 h-5" />,
  Headphones: <Headphones className="w-5 h-5" />,
  BarChart2: <BarChart2 className="w-5 h-5" />,
  Zap: <Zap className="w-5 h-5" />,
  Link: <Link2 className="w-5 h-5" />,
  Grid: <Grid className="w-5 h-5" />,
  FileText: <FileText className="w-5 h-5" />,
  CheckCircle: <CheckCircle className="w-5 h-5" />,
  Layers: <Layers className="w-5 h-5" />,
  Heart: <Heart className="w-5 h-5" />,
  Calendar: <Calendar className="w-5 h-5" />,
  Webhook: <Webhook className="w-5 h-5" />,
  MessageCircle: <MessageCircle className="w-5 h-5" />,
  Users: <Users className="w-5 h-5" />,
  Bot: <Bot className="w-5 h-5" />,
};

const getDifficultyColor = (difficulty: string) => {
  switch (difficulty) {
    case 'beginner': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
    case 'intermediate': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
    case 'advanced': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
    default: return 'bg-gray-100 text-gray-700';
  }
};

const getDifficultyLabel = (difficulty: string) => {
  switch (difficulty) {
    case 'beginner': return 'Iniciante';
    case 'intermediate': return 'Intermediário';
    case 'advanced': return 'Avançado';
    default: return difficulty;
  }
};

export default function TemplatesPage() {
  const router = useRouter();
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredTemplates = useMemo(() => {
    return searchTemplates(searchQuery, selectedCategory === "all" ? undefined : selectedCategory);
  }, [searchQuery, selectedCategory]);

  const featuredTemplates = workflowTemplates.filter(t => 
    t.tags.includes('multi-agent') || t.difficulty === 'advanced'
  ).slice(0, 3);

  const useTemplate = (template: WorkflowTemplate) => {
    toast.success(`Template "${template.name}" selecionado!`);
    router.push(`/workflows/builder?template=${template.id}`);
  };

  return (
    <Protected>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/workflows" className="p-2 text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Voltar">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Templates de Workflows</h1>
              <p className="text-gray-500 dark:text-gray-400 mt-1">Comece rapidamente com templates pré-configurados</p>
            </div>
          </div>
          <Link href="/workflows/builder" className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors">
            <Plus className="w-4 h-4" />
            Criar do Zero
          </Link>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-modern pl-10 w-full"
            />
          </div>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {workflowCategories.map(cat => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
                  selectedCategory === cat.id
                    ? "bg-blue-500 text-white"
                    : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600"
                }`}
              >
                {Icons[cat.icon] || <Grid className="w-4 h-4" />}
                {cat.name}
              </button>
            ))}
          </div>
        </div>

        {/* Featured Templates */}
        {selectedCategory === "all" && !searchQuery && (
          <div className="mb-2">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-yellow-500" /> Destaques
            </h2>
            <div className="grid md:grid-cols-3 gap-4">
              {featuredTemplates.map(template => (
                <div key={template.id} className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl p-6 text-white relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
                  <div className="relative z-10">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center mb-4">
                      {Icons[template.icon] || <Bot className="w-6 h-6" />}
                    </div>
                    <h3 className="font-semibold text-lg">{template.name}</h3>
                    <p className="text-blue-100 text-sm mt-1 line-clamp-2">{template.description}</p>
                    <div className="flex items-center justify-between mt-4">
                      <div className="flex items-center gap-2">
                        <span className="text-xs bg-white/20 px-2 py-1 rounded-full">{template.definition.steps?.length || 0} passos</span>
                        <span className={`text-xs px-2 py-1 rounded-full ${getDifficultyColor(template.difficulty)}`}>
                          {getDifficultyLabel(template.difficulty)}
                        </span>
                      </div>
                      <button onClick={() => useTemplate(template)} className="px-3 py-1.5 bg-white text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-50 transition-colors">
                        Usar
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All Templates */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {selectedCategory === "all" ? "Todos os Templates" : workflowCategories.find(c => c.id === selectedCategory)?.name} ({filteredTemplates.length})
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTemplates.map(template => (
              <div key={template.id} className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 hover:shadow-lg hover:border-blue-200 dark:hover:border-blue-800 transition-all group">
                <div className="flex items-start justify-between">
                  <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center text-blue-600 dark:text-blue-400">
                    {Icons[template.icon] || <Bot className="w-5 h-5" />}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${getDifficultyColor(template.difficulty)}`}>
                      {getDifficultyLabel(template.difficulty)}
                    </span>
                  </div>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mt-3">{template.name}</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm mt-1 line-clamp-2">{template.description}</p>
                <div className="flex flex-wrap gap-1 mt-3">
                  {template.tags.slice(0, 3).map(tag => (
                    <span key={tag} className="text-xs bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-gray-400 px-2 py-0.5 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100 dark:border-slate-700">
                  <span className="text-xs text-gray-500">{template.definition.steps?.length || 0} passos</span>
                  <div className="flex gap-2">
                    <button className="p-2 text-gray-400 hover:text-blue-600 transition-colors opacity-0 group-hover:opacity-100" title="Visualizar">
                      <Eye className="w-4 h-4" />
                    </button>
                    <button onClick={() => useTemplate(template)} className="flex items-center gap-1 px-3 py-1.5 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors">
                      <Plus className="w-4 h-4" /> Usar
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {filteredTemplates.length === 0 && (
          <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-100 dark:bg-slate-700 flex items-center justify-center text-gray-400">
              <Grid className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Nenhum template encontrado</h3>
            <p className="text-gray-500 dark:text-gray-400">Tente ajustar os filtros de busca</p>
          </div>
        )}
      </div>
    </Protected>
  );
}
