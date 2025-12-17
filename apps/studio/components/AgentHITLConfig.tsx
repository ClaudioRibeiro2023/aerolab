"use client";
import React, { useState } from "react";

export interface HITLConfig {
  enabled: boolean;
  triggers: HITLTrigger[];
  escalationChannel: "email" | "slack" | "webhook" | "dashboard";
  escalationTarget: string;
  timeout: number; // minutos
  fallbackAction: "wait" | "auto_approve" | "reject";
  notifyOnResolution: boolean;
}

export interface HITLTrigger {
  id: string;
  type: "low_confidence" | "keyword" | "user_request" | "sensitive_action" | "error";
  name: string;
  description: string;
  enabled: boolean;
  config?: Record<string, any>;
}

interface Props {
  config: HITLConfig;
  onChange: (config: HITLConfig) => void;
}

const defaultTriggers: HITLTrigger[] = [
  {
    id: "low_confidence",
    type: "low_confidence",
    name: "Confiança Baixa",
    description: "Escala quando o agente não tem certeza da resposta",
    enabled: true,
    config: { threshold: 0.6 }
  },
  {
    id: "keyword",
    type: "keyword",
    name: "Palavras-chave",
    description: "Escala quando detecta termos sensíveis",
    enabled: false,
    config: { keywords: ["cancelar", "reembolso", "reclamação", "jurídico"] }
  },
  {
    id: "user_request",
    type: "user_request",
    name: "Pedido do Usuário",
    description: "Escala quando o usuário pede para falar com humano",
    enabled: true
  },
  {
    id: "sensitive_action",
    type: "sensitive_action",
    name: "Ação Sensível",
    description: "Escala antes de executar ações irreversíveis",
    enabled: true,
    config: { actions: ["delete", "payment", "contract"] }
  },
  {
    id: "error",
    type: "error",
    name: "Erro Repetido",
    description: "Escala após múltiplos erros consecutivos",
    enabled: true,
    config: { errorCount: 3 }
  }
];

export const defaultHITLConfig: HITLConfig = {
  enabled: false,
  triggers: defaultTriggers,
  escalationChannel: "dashboard",
  escalationTarget: "",
  timeout: 30,
  fallbackAction: "wait",
  notifyOnResolution: true
};

export default function AgentHITLConfig({ config, onChange }: Props) {
  const updateConfig = (updates: Partial<HITLConfig>) => {
    onChange({ ...config, ...updates });
  };

  const toggleTrigger = (triggerId: string) => {
    const newTriggers = config.triggers.map(t =>
      t.id === triggerId ? { ...t, enabled: !t.enabled } : t
    );
    updateConfig({ triggers: newTriggers });
  };

  return (
    <div className="space-y-4">
      {/* Toggle Principal */}
      <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
        <div>
          <p className="font-medium text-gray-900 dark:text-white">Human-in-the-Loop (HITL)</p>
          <p className="text-xs text-gray-500">Escala automaticamente para humanos quando necessário</p>
        </div>
        <button 
          onClick={() => updateConfig({ enabled: !config.enabled })}
          className={`w-12 h-6 rounded-full transition-colors ${config.enabled ? "bg-blue-500" : "bg-gray-300 dark:bg-slate-600"}`}
        >
          <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${config.enabled ? "translate-x-6" : "translate-x-0.5"}`} />
        </button>
      </div>

      {config.enabled && (
        <>
          {/* Triggers */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Gatilhos de Escalação
            </label>
            <div className="space-y-2">
              {config.triggers.map(trigger => (
                <div
                  key={trigger.id}
                  className={`p-3 rounded-xl border-2 transition-all ${
                    trigger.enabled
                      ? "border-orange-500 bg-orange-50 dark:bg-orange-900/20"
                      : "border-gray-200 dark:border-slate-600"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-xl">
                        {trigger.type === "low_confidence" ? "🤔" :
                         trigger.type === "keyword" ? "🔑" :
                         trigger.type === "user_request" ? "👋" :
                         trigger.type === "sensitive_action" ? "⚠️" : "❌"}
                      </span>
                      <div>
                        <span className="font-medium text-gray-900 dark:text-white">{trigger.name}</span>
                        <span className="block text-xs text-gray-500">{trigger.description}</span>
                      </div>
                    </div>
                    <button 
                      onClick={() => toggleTrigger(trigger.id)}
                      className={`w-10 h-5 rounded-full transition-colors ${trigger.enabled ? "bg-orange-500" : "bg-gray-300 dark:bg-slate-600"}`}
                    >
                      <div className={`w-4 h-4 bg-white rounded-full shadow transition-transform ${trigger.enabled ? "translate-x-5" : "translate-x-0.5"}`} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Escalation Channel */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Canal de Escalação
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {[
                { id: "dashboard", name: "Dashboard", icon: "📊" },
                { id: "email", name: "Email", icon: "📧" },
                { id: "slack", name: "Slack", icon: "💬" },
                { id: "webhook", name: "Webhook", icon: "🔗" },
              ].map(channel => (
                <button
                  key={channel.id}
                  type="button"
                  onClick={() => updateConfig({ escalationChannel: channel.id as HITLConfig["escalationChannel"] })}
                  className={`p-3 rounded-xl border-2 text-center transition-all ${
                    config.escalationChannel === channel.id
                      ? "border-orange-500 bg-orange-50 dark:bg-orange-900/20"
                      : "border-gray-200 dark:border-slate-600"
                  }`}
                >
                  <span className="text-xl block mb-1">{channel.icon}</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{channel.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Target */}
          {config.escalationChannel !== "dashboard" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {config.escalationChannel === "email" ? "Email de Destino" :
                 config.escalationChannel === "slack" ? "Canal Slack" :
                 "URL do Webhook"}
              </label>
              <input
                type="text"
                value={config.escalationTarget}
                onChange={e => updateConfig({ escalationTarget: e.target.value })}
                placeholder={
                  config.escalationChannel === "email" ? "suporte@empresa.com" :
                  config.escalationChannel === "slack" ? "#suporte-escalado" :
                  "https://api.empresa.com/webhook/hitl"
                }
                className="input-modern"
              />
            </div>
          )}

          {/* Timeout and Fallback */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Timeout (minutos)
              </label>
              <input
                type="number"
                min={5}
                max={1440}
                value={config.timeout}
                onChange={e => updateConfig({ timeout: parseInt(e.target.value) || 30 })}
                className="input-modern"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Ação após Timeout
              </label>
              <select
                value={config.fallbackAction}
                onChange={e => updateConfig({ fallbackAction: e.target.value as HITLConfig["fallbackAction"] })}
                className="input-modern"
              >
                <option value="wait">Continuar aguardando</option>
                <option value="auto_approve">Aprovar automaticamente</option>
                <option value="reject">Rejeitar/Cancelar</option>
              </select>
            </div>
          </div>

          {/* Notify on Resolution */}
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-slate-900 rounded-xl">
            <div>
              <p className="font-medium text-gray-900 dark:text-white text-sm">Notificar ao resolver</p>
              <p className="text-xs text-gray-500">Enviar notificação quando a escalação for resolvida</p>
            </div>
            <button 
              onClick={() => updateConfig({ notifyOnResolution: !config.notifyOnResolution })}
              className={`w-10 h-5 rounded-full transition-colors ${config.notifyOnResolution ? "bg-blue-500" : "bg-gray-300 dark:bg-slate-600"}`}
            >
              <div className={`w-4 h-4 bg-white rounded-full shadow transition-transform ${config.notifyOnResolution ? "translate-x-5" : "translate-x-0.5"}`} />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
