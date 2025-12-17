"use client";
import React, { useState } from "react";
import Protected from "../../components/Protected";
import Link from "next/link";

interface HelpItem {
  id: string;
  question: string;
  answer: string;
  category: string;
}

const Icons = {
  help: (<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  search: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>),
  book: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>),
  video: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>),
  chat: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>),
  chevron: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>),
  external: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>),
};

const faqItems: HelpItem[] = [
  { id: "1", category: "Geral", question: "O que é o Agno Platform?", answer: "Agno é uma plataforma multi-agente de IA que permite criar, gerenciar e orquestrar agentes inteligentes para automatizar tarefas, processar documentos e muito mais." },
  { id: "2", category: "Geral", question: "Como acessar o atalho de navegação rápida?", answer: "Pressione ⌘K (Mac) ou Ctrl+K (Windows) para abrir o Command Palette e navegar rapidamente entre as funcionalidades." },
  { id: "3", category: "Agentes", question: "Como criar um novo agente?", answer: "Vá para a página 'Agentes' e clique em 'Novo Agente'. Defina nome, instruções e modelo, depois salve." },
  { id: "4", category: "Agentes", question: "Posso usar diferentes modelos de IA?", answer: "Sim! O Agno suporta GPT-4, Claude, Gemini e outros modelos. Configure as API Keys nas Configurações." },
  { id: "5", category: "Workflows", question: "O que são Workflows?", answer: "Workflows são sequências automatizadas de tarefas executadas por agentes. Você pode criar fluxos complexos combinando múltiplos agentes." },
  { id: "6", category: "Workflows", question: "Como usar o Visual Builder?", answer: "Acesse Workflows > Visual Builder. Arraste nós para o canvas, conecte-os e configure cada passo do seu fluxo." },
  { id: "7", category: "RAG", question: "O que é RAG?", answer: "RAG (Retrieval-Augmented Generation) permite que agentes busquem informações em seus documentos antes de responder, aumentando precisão." },
  { id: "8", category: "RAG", question: "Quais formatos de arquivo são suportados?", answer: "PDF, TXT, DOCX, MD e outros formatos de texto. Você também pode ingerir URLs diretamente." },
  { id: "9", category: "Times", question: "Como funcionam os Times?", answer: "Times são grupos de agentes que trabalham juntos. Defina um líder e membros, e eles colaborarão para resolver tarefas complexas." },
  { id: "10", category: "API", question: "Como obter minha API Key?", answer: "Vá para Configurações > API Keys. Sua chave será exibida lá. Use-a para autenticar chamadas à API." },
];

const categories = ["Todos", "Geral", "Agentes", "Workflows", "RAG", "Times", "API"];

const quickLinks = [
  { title: "Documentação", desc: "Guias completos e referência da API", icon: Icons.book, href: "https://docs.agno.com" },
  { title: "Tutoriais em Vídeo", desc: "Aprenda visualmente com nossos vídeos", icon: Icons.video, href: "#" },
  { title: "Comunidade", desc: "Tire dúvidas com outros usuários", icon: Icons.chat, href: "#" },
];

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("Todos");
  const [expandedFaq, setExpandedFaq] = useState<string | null>(null);

  const filteredFaq = faqItems.filter(item => {
    const matchesCategory = selectedCategory === "Todos" || item.category === selectedCategory;
    const matchesSearch = item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.answer.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <Protected>
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white">{Icons.help}</div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Central de Ajuda</h1>
          <p className="text-gray-500 dark:text-gray-400">Encontre respostas rápidas e aprenda a usar todas as funcionalidades</p>
        </div>

        {/* Search */}
        <div className="max-w-xl mx-auto relative">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">{Icons.search}</span>
          <input
            type="text"
            placeholder="Buscar na ajuda..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-modern pl-12 py-4 text-lg"
          />
        </div>

        {/* Quick Links */}
        <div className="grid md:grid-cols-3 gap-4">
          {quickLinks.map((link, i) => (
            <a key={i} href={link.href} target="_blank" rel="noopener noreferrer" className="flex items-center gap-4 p-5 bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 hover:shadow-lg transition-shadow group">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-xl text-blue-600 dark:text-blue-400">{link.icon}</div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 transition-colors flex items-center gap-2">
                  {link.title} {Icons.external}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">{link.desc}</p>
              </div>
            </a>
          ))}
        </div>

        {/* FAQ */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 overflow-hidden">
          <div className="p-6 border-b border-gray-100 dark:border-slate-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Perguntas Frequentes</h2>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
                    selectedCategory === cat
                      ? "bg-blue-500 text-white"
                      : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div className="divide-y divide-gray-100 dark:divide-slate-700">
            {filteredFaq.length === 0 ? (
              <div className="p-12 text-center text-gray-400">
                <p>Nenhuma pergunta encontrada</p>
              </div>
            ) : (
              filteredFaq.map(item => (
                <div key={item.id}>
                  <button
                    onClick={() => setExpandedFaq(expandedFaq === item.id ? null : item.id)}
                    className="w-full flex items-center justify-between p-5 text-left hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 rounded-full">{item.category}</span>
                      <span className="font-medium text-gray-900 dark:text-white">{item.question}</span>
                    </div>
                    <div className={`transition-transform ${expandedFaq === item.id ? "rotate-180" : ""}`}>{Icons.chevron}</div>
                  </button>
                  {expandedFaq === item.id && (
                    <div className="px-5 pb-5">
                      <p className="text-gray-600 dark:text-gray-400 pl-16">{item.answer}</p>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Contact */}
        <div className="text-center p-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl text-white">
          <h3 className="text-xl font-semibold mb-2">Ainda precisa de ajuda?</h3>
          <p className="text-blue-100 mb-4">Nossa equipe está pronta para ajudar você</p>
          <Link href="/chat" className="inline-flex items-center gap-2 px-6 py-3 bg-white text-blue-600 rounded-xl font-medium hover:bg-blue-50 transition-colors">
            {Icons.chat} Falar com Suporte
          </Link>
        </div>
      </div>
    </Protected>
  );
}
