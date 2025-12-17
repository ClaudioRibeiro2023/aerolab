"use client";
import React, { useState, useRef } from "react";
import Protected from "../../components/Protected";
import { toast } from "sonner";
import { useAuth } from "../../store/auth";
import { useTheme } from "../../providers/ThemeProvider";
import api from "../../lib/api";
import { getHistory, clearHistory } from "../../lib/executionHistory";

const Icons = {
  settings: (<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>),
  user: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>),
  palette: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" /></svg>),
  bell: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>),
  key: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>),
  shield: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>),
  save: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>),
  download: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>),
  upload: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>),
};

const tabs = [
  { id: "profile", name: "Perfil", icon: Icons.user },
  { id: "appearance", name: "Aparência", icon: Icons.palette },
  { id: "notifications", name: "Notificações", icon: Icons.bell },
  { id: "api", name: "API Keys", icon: Icons.key },
  { id: "security", name: "Segurança", icon: Icons.shield },
  { id: "backup", name: "Backup", icon: Icons.download },
];

export default function SettingsPage() {
  const { username, role } = useAuth();
  const { theme, setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState("profile");
  const [settings, setSettings] = useState({
    displayName: username || "Usuário",
    email: "usuario@exemplo.com",
    language: "pt-BR",
    timezone: "America/Sao_Paulo",
    notifications: {
      email: true,
      push: true,
      workflow: true,
      system: false,
    },
    apiKey: "ak_••••••••••••••••",
    twoFactor: false,
  });

  const handleSave = () => {
    toast.success("Configurações salvas com sucesso!");
  };

  const resetOnboarding = () => {
    localStorage.removeItem("agno_onboarding_completed");
    toast.success("Onboarding resetado! Recarregue a página para ver.");
  };

  const fileInputRef = useRef<HTMLInputElement>(null);

  const exportConfig = async () => {
    try {
      const [agentsRes, teamsRes] = await Promise.allSettled([
        api.get("/agents"),
        api.get("/teams"),
      ]);
      
      const history = getHistory();
      
      const config = {
        version: "1.0",
        exportedAt: new Date().toISOString(),
        agents: agentsRes.status === "fulfilled" ? agentsRes.value.data : [],
        teams: teamsRes.status === "fulfilled" ? teamsRes.value.data : [],
        history,
        settings,
      };

      const blob = new Blob([JSON.stringify(config, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `agno-backup-${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast.success("Configurações exportadas com sucesso!");
    } catch (e) {
      toast.error("Erro ao exportar configurações");
    }
  };

  const importConfig = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const config = JSON.parse(event.target?.result as string);
        
        if (!config.version) {
          toast.error("Arquivo de backup inválido");
          return;
        }

        // Importar histórico
        if (config.history) {
          localStorage.setItem("agno_execution_history", JSON.stringify(config.history));
        }

        toast.success(`Backup importado! ${config.agents?.length || 0} agentes, ${config.teams?.length || 0} times`);
        
        // Limpar input
        if (fileInputRef.current) fileInputRef.current.value = "";
      } catch (err) {
        toast.error("Erro ao importar: arquivo inválido");
      }
    };
    reader.readAsText(file);
  };

  return (
    <Protected>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-gray-500 to-gray-700 flex items-center justify-center text-white">{Icons.settings}</div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Configurações</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm">Gerencie suas preferências e conta</p>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Tabs */}
          <div className="lg:w-56 flex lg:flex-col gap-2 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? "bg-blue-500 text-white"
                    : "bg-white dark:bg-slate-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700"
                }`}
              >
                {tab.icon} {tab.name}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700">
            {activeTab === "profile" && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Informações do Perfil</h2>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Nome de Exibição</label>
                    <input type="text" value={settings.displayName} onChange={(e) => setSettings({...settings, displayName: e.target.value})} className="input-modern" placeholder="Seu nome" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Email</label>
                    <input type="email" value={settings.email} onChange={(e) => setSettings({...settings, email: e.target.value})} className="input-modern" placeholder="email@exemplo.com" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Idioma</label>
                    <select aria-label="Idioma" value={settings.language} onChange={(e) => setSettings({...settings, language: e.target.value})} className="input-modern">
                      <option value="pt-BR">Português (Brasil)</option>
                      <option value="en-US">English (US)</option>
                      <option value="es">Español</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Fuso Horário</label>
                    <select aria-label="Fuso horário" value={settings.timezone} onChange={(e) => setSettings({...settings, timezone: e.target.value})} className="input-modern">
                      <option value="America/Sao_Paulo">Brasília (GMT-3)</option>
                      <option value="America/New_York">New York (GMT-5)</option>
                      <option value="Europe/London">London (GMT)</option>
                    </select>
                  </div>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Função: <span className="font-medium text-gray-900 dark:text-white capitalize">{role}</span></p>
                </div>
              </div>
            )}

            {activeTab === "appearance" && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Aparência</h2>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Tema</label>
                  <div className="grid grid-cols-3 gap-3">
                    {["light", "dark", "system"].map(t => (
                      <button
                        key={t}
                        onClick={() => setTheme(t as "light" | "dark" | "system")}
                        className={`p-4 rounded-xl border-2 transition-colors ${
                          theme === t ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" : "border-gray-200 dark:border-slate-700"
                        }`}
                      >
                        <div className={`w-8 h-8 mx-auto mb-2 rounded-lg ${t === "light" ? "bg-white border" : t === "dark" ? "bg-slate-800" : "bg-gradient-to-br from-white to-slate-800"}`} />
                        <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">{t === "system" ? "Sistema" : t === "light" ? "Claro" : "Escuro"}</p>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="pt-4 border-t border-gray-100 dark:border-slate-700">
                  <button onClick={resetOnboarding} className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
                    Resetar tutorial de onboarding
                  </button>
                </div>
              </div>
            )}

            {activeTab === "notifications" && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Preferências de Notificação</h2>
                <div className="space-y-4">
                  {[
                    { key: "email", label: "Notificações por Email", desc: "Receba atualizações importantes por email" },
                    { key: "push", label: "Notificações Push", desc: "Receba alertas em tempo real no navegador" },
                    { key: "workflow", label: "Execuções de Workflow", desc: "Alertas quando workflows são concluídos" },
                    { key: "system", label: "Atualizações do Sistema", desc: "Notificações sobre novidades e manutenções" },
                  ].map(item => (
                    <div key={item.key} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{item.label}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{item.desc}</p>
                      </div>
                      <button
                        onClick={() => setSettings({...settings, notifications: {...settings.notifications, [item.key]: !settings.notifications[item.key as keyof typeof settings.notifications]}})}
                        className={`w-12 h-6 rounded-full transition-colors ${settings.notifications[item.key as keyof typeof settings.notifications] ? "bg-blue-500" : "bg-gray-300 dark:bg-slate-600"}`}
                      >
                        <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${settings.notifications[item.key as keyof typeof settings.notifications] ? "translate-x-6" : "translate-x-0.5"}`} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === "api" && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Chaves de API</h2>
                <div className="p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Sua API Key</label>
                  <div className="flex gap-2">
                    <input type="text" value={settings.apiKey} readOnly className="input-modern flex-1 font-mono" />
                    <button className="btn-secondary" onClick={() => toast.success("API Key copiada!")}>Copiar</button>
                    <button className="btn-primary" onClick={() => toast.info("Nova API Key gerada")}>Regenerar</button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Use esta chave para autenticar chamadas à API</p>
                </div>
                <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-xl border border-orange-200 dark:border-orange-800">
                  <p className="text-sm text-orange-700 dark:text-orange-300">⚠️ Nunca compartilhe sua API Key. Regenere se suspeitar de vazamento.</p>
                </div>
              </div>
            )}

            {activeTab === "security" && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Segurança</h2>
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Autenticação de Dois Fatores</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Adicione uma camada extra de segurança</p>
                  </div>
                  <button
                    onClick={() => setSettings({...settings, twoFactor: !settings.twoFactor})}
                    className={`w-12 h-6 rounded-full transition-colors ${settings.twoFactor ? "bg-blue-500" : "bg-gray-300 dark:bg-slate-600"}`}
                    title="Toggle 2FA"
                  >
                    <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${settings.twoFactor ? "translate-x-6" : "translate-x-0.5"}`} />
                  </button>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
                  <p className="font-medium text-gray-900 dark:text-white mb-2">Alterar Senha</p>
                  <button className="btn-secondary">Alterar Senha</button>
                </div>
                <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-200 dark:border-red-800">
                  <p className="font-medium text-red-700 dark:text-red-300 mb-2">Zona de Perigo</p>
                  <button className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 transition-colors">Excluir Conta</button>
                </div>
              </div>
            )}

            {activeTab === "backup" && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Backup & Restauração</h2>
                
                {/* Exportar */}
                <div className="p-6 bg-gray-50 dark:bg-slate-900 rounded-xl">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg text-blue-600">{Icons.download}</div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">Exportar Configurações</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Baixe um arquivo JSON com todos os dados</p>
                    </div>
                  </div>
                  <button onClick={exportConfig} className="btn-primary flex items-center gap-2">
                    {Icons.download} Exportar Backup
                  </button>
                </div>

                {/* Importar */}
                <div className="p-6 bg-gray-50 dark:bg-slate-900 rounded-xl">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg text-green-600">{Icons.upload}</div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">Importar Configurações</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Restaure dados de um backup anterior</p>
                    </div>
                  </div>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={importConfig}
                    accept=".json"
                    className="hidden"
                    id="backup-import"
                  />
                  <label htmlFor="backup-import" className="btn-secondary flex items-center gap-2 cursor-pointer inline-flex">
                    {Icons.upload} Selecionar Arquivo
                  </label>
                </div>

                {/* Limpar dados */}
                <div className="p-6 bg-orange-50 dark:bg-orange-900/20 rounded-xl border border-orange-200 dark:border-orange-800">
                  <div className="flex items-center gap-3 mb-3">
                    <p className="font-medium text-orange-700 dark:text-orange-300">Limpar Histórico de Execuções</p>
                  </div>
                  <p className="text-sm text-orange-600 dark:text-orange-400 mb-3">Remove todo o histórico de execuções do localStorage</p>
                  <button onClick={() => { clearHistory(); toast.success("Histórico limpo!"); }} className="px-4 py-2 bg-orange-600 text-white rounded-lg text-sm hover:bg-orange-700 transition-colors">
                    Limpar Histórico
                  </button>
                </div>
              </div>
            )}

            {/* Save Button */}
            <div className="mt-6 pt-6 border-t border-gray-100 dark:border-slate-700 flex justify-end">
              <button onClick={handleSave} className="btn-primary flex items-center gap-2">
                {Icons.save} Salvar Alterações
              </button>
            </div>
          </div>
        </div>
      </div>
    </Protected>
  );
}
