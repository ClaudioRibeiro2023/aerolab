"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import api from "@/lib/api";

interface Persona {
  id: string;
  name: string;
  description?: string;
  system_prompt: string;
  avatar_emoji: string;
  is_public: boolean;
  is_default: boolean;
  default_model?: string;
  temperature: number;
  tags: string[];
}

interface PersonaSelectorProps {
  selectedPersonaId: string | null;
  onSelectPersona: (persona: Persona | null) => void;
  compact?: boolean;
}

export default function PersonaSelector({
  selectedPersonaId,
  onSelectPersona,
  compact = false,
}: PersonaSelectorProps) {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadPersonas();
  }, []);

  const loadPersonas = async () => {
    try {
      const { data } = await api.get("/api/v2/personas");
      setPersonas(data);
    } catch (err) {
      console.error("Error loading personas:", err);
      // Fallback to empty
      setPersonas([]);
    } finally {
      setLoading(false);
    }
  };

  const selectedPersona = personas.find((p) => p.id === selectedPersonaId);

  const filteredPersonas = personas.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleSelect = (persona: Persona) => {
    onSelectPersona(persona);
    setIsOpen(false);
  };

  const handleClear = () => {
    onSelectPersona(null);
    setIsOpen(false);
  };

  if (compact) {
    return (
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 transition-colors"
          title="Selecionar Persona"
        >
          <span className="text-lg">{selectedPersona?.avatar_emoji || "🎭"}</span>
          <span className="text-sm text-slate-300 hidden sm:inline">
            {selectedPersona?.name || "Persona"}
          </span>
          <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute right-0 mt-2 w-80 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-30 overflow-hidden"
            >
              <div className="p-3 border-b border-slate-700">
                <input
                  type="text"
                  placeholder="Buscar personas..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="max-h-80 overflow-y-auto p-2">
                {selectedPersonaId && (
                  <button
                    onClick={handleClear}
                    className="w-full px-3 py-2 text-left text-sm text-slate-400 hover:bg-slate-700 rounded-lg mb-1"
                  >
                    ✕ Remover persona
                  </button>
                )}

                {loading ? (
                  <div className="p-4 text-center text-slate-500">Carregando...</div>
                ) : filteredPersonas.length === 0 ? (
                  <div className="p-4 text-center text-slate-500">Nenhuma persona encontrada</div>
                ) : (
                  filteredPersonas.map((persona) => (
                    <button
                      key={persona.id}
                      onClick={() => handleSelect(persona)}
                      className={`w-full px-3 py-2.5 text-left rounded-lg transition-colors flex items-start gap-3 ${
                        selectedPersonaId === persona.id
                          ? "bg-blue-600/20 border border-blue-500/30"
                          : "hover:bg-slate-700"
                      }`}
                    >
                      <span className="text-2xl flex-shrink-0">{persona.avatar_emoji}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-white text-sm">{persona.name}</span>
                          {persona.is_default && (
                            <span className="px-1.5 py-0.5 bg-blue-600/20 text-blue-400 text-xs rounded">
                              Padrão
                            </span>
                          )}
                        </div>
                        {persona.description && (
                          <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">
                            {persona.description}
                          </p>
                        )}
                        {persona.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {persona.tags.slice(0, 3).map((tag) => (
                              <span
                                key={tag}
                                className="px-1.5 py-0.5 bg-slate-700 text-slate-400 text-xs rounded"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      {selectedPersonaId === persona.id && (
                        <svg className="w-5 h-5 text-blue-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  ))
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // Full view
  return (
    <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-4">
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
        <span>🎭</span>
        Persona
      </h3>

      {selectedPersona ? (
        <div className="flex items-start gap-3 p-3 bg-slate-800 rounded-lg">
          <span className="text-3xl">{selectedPersona.avatar_emoji}</span>
          <div className="flex-1 min-w-0">
            <div className="font-medium text-white">{selectedPersona.name}</div>
            {selectedPersona.description && (
              <p className="text-sm text-slate-400 mt-1">{selectedPersona.description}</p>
            )}
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={() => setIsOpen(true)}
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                Alterar
              </button>
              <button
                onClick={handleClear}
                className="text-xs text-slate-500 hover:text-slate-400"
              >
                Remover
              </button>
            </div>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className="w-full p-4 border-2 border-dashed border-slate-700 rounded-lg text-center hover:border-slate-600 transition-colors"
        >
          <span className="text-3xl mb-2 block">🎭</span>
          <span className="text-sm text-slate-400">Selecionar uma persona</span>
        </button>
      )}

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden"
            >
              <div className="p-4 border-b border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-lg font-semibold text-white">Escolher Persona</h2>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <input
                  type="text"
                  placeholder="Buscar por nome ou tag..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="max-h-96 overflow-y-auto p-4 space-y-2">
                {loading ? (
                  <div className="p-8 text-center text-slate-500">Carregando personas...</div>
                ) : filteredPersonas.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    Nenhuma persona encontrada
                  </div>
                ) : (
                  filteredPersonas.map((persona) => (
                    <button
                      key={persona.id}
                      onClick={() => handleSelect(persona)}
                      className={`w-full p-4 text-left rounded-xl transition-colors flex items-start gap-4 ${
                        selectedPersonaId === persona.id
                          ? "bg-blue-600/20 border-2 border-blue-500/50"
                          : "bg-slate-800 border-2 border-transparent hover:border-slate-700"
                      }`}
                    >
                      <span className="text-4xl">{persona.avatar_emoji}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-white">{persona.name}</span>
                          {persona.is_default && (
                            <span className="px-2 py-0.5 bg-blue-600/20 text-blue-400 text-xs rounded-full">
                              Padrão
                            </span>
                          )}
                        </div>
                        {persona.description && (
                          <p className="text-sm text-slate-400 mb-2">{persona.description}</p>
                        )}
                        <div className="flex flex-wrap gap-1">
                          {persona.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-0.5 bg-slate-700 text-slate-400 text-xs rounded-full"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                      {selectedPersonaId === persona.id && (
                        <svg className="w-6 h-6 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  ))
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
