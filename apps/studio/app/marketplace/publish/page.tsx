"use client";
import React, { useState } from "react";
import Protected from "../../../components/Protected";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

const Icons = {
  back: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>),
  upload: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>),
};

const categories = [
  { id: "productivity", name: "Produtividade", icon: "📊" },
  { id: "business", name: "Negócios", icon: "💼" },
  { id: "content", name: "Conteúdo", icon: "✍️" },
  { id: "support", name: "Suporte", icon: "💬" },
  { id: "development", name: "Desenvolvimento", icon: "💻" },
  { id: "data", name: "Dados", icon: "📈" },
];

const iconOptions = ["🤖", "🔬", "🧙", "🎨", "💼", "📊", "💻", "🔍", "✍️", "🤝", "💰", "📈", "🔄", "⚡", "🎯"];

export default function PublishAgentPage() {
  const router = useRouter();
  const [publishing, setPublishing] = useState(false);
  
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    category: "productivity",
    icon: "🤖",
    price: "free" as "free" | "premium",
    tags: "",
    agentId: "", // Agent existente para publicar
    readme: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error("Nome é obrigatório");
      return;
    }
    if (!formData.description.trim()) {
      toast.error("Descrição é obrigatória");
      return;
    }

    setPublishing(true);
    try {
      // Simular publicação
      await new Promise(r => setTimeout(r, 1500));
      toast.success("Agente publicado no Marketplace!");
      router.push("/marketplace");
    } catch (e) {
      toast.error("Erro ao publicar agente");
    } finally {
      setPublishing(false);
    }
  };

  return (
    <Protected>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Link href="/marketplace" className="p-2 text-gray-500 hover:text-blue-600 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors" title="Voltar">
            {Icons.back}
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Publicar no Marketplace</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm">Compartilhe seu agente com a comunidade</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Informações Básicas</h2>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nome do Agente *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ex: Super Researcher Pro"
                  className="input-modern"
                  required
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Descrição *</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Descreva o que seu agente faz, seus diferenciais e casos de uso..."
                  rows={3}
                  className="input-modern"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Categoria</label>
                <select
                  value={formData.category}
                  onChange={e => setFormData({ ...formData, category: e.target.value })}
                  className="input-modern"
                >
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Preço</label>
                <select
                  value={formData.price}
                  onChange={e => setFormData({ ...formData, price: e.target.value as any })}
                  className="input-modern"
                >
                  <option value="free">Grátis</option>
                  <option value="premium">Premium</option>
                </select>
              </div>
            </div>
          </div>

          {/* Icon Selection */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Ícone</h2>
            <div className="flex flex-wrap gap-2">
              {iconOptions.map(icon => (
                <button
                  key={icon}
                  type="button"
                  onClick={() => setFormData({ ...formData, icon })}
                  className={`w-12 h-12 text-2xl rounded-xl border-2 transition-all ${
                    formData.icon === icon
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                      : "border-gray-200 dark:border-slate-600 hover:border-gray-300"
                  }`}
                >
                  {icon}
                </button>
              ))}
            </div>
          </div>

          {/* Tags */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Tags</h2>
            <input
              type="text"
              value={formData.tags}
              onChange={e => setFormData({ ...formData, tags: e.target.value })}
              placeholder="Ex: research, AI, automation (separadas por vírgula)"
              className="input-modern"
            />
            <p className="text-xs text-gray-500">Adicione tags para ajudar na descoberta do seu agente</p>
          </div>

          {/* README */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">README / Documentação</h2>
            <textarea
              value={formData.readme}
              onChange={e => setFormData({ ...formData, readme: e.target.value })}
              placeholder="# Meu Agente&#10;&#10;## Descrição&#10;...&#10;&#10;## Como usar&#10;...&#10;&#10;## Exemplos&#10;..."
              rows={10}
              className="input-modern font-mono text-sm"
            />
            <p className="text-xs text-gray-500">Suporta Markdown. Inclua instruções de uso, exemplos e limitações.</p>
          </div>

          {/* Submit */}
          <div className="flex gap-3">
            <Link href="/marketplace" className="btn-secondary flex-1 text-center">Cancelar</Link>
            <button 
              type="submit" 
              disabled={publishing}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {publishing ? (
                <>
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Publicando...
                </>
              ) : (
                <>
                  {Icons.upload} Publicar Agente
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </Protected>
  );
}
