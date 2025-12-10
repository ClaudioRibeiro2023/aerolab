import { useState } from 'react'
import { Settings, Sliders, Palette, Bell, Plug, Save, RotateCcw } from 'lucide-react'
import { Button, Card } from '@template/design-system'

type ConfigTab = 'geral' | 'aparencia' | 'notificacoes' | 'integracoes'

const tabs = [
  { id: 'geral' as const, name: 'Geral', icon: Sliders },
  { id: 'aparencia' as const, name: 'Aparência', icon: Palette },
  { id: 'notificacoes' as const, name: 'Notificações', icon: Bell },
  { id: 'integracoes' as const, name: 'Integrações', icon: Plug },
]

export function ConfigPage() {
  const [activeTab, setActiveTab] = useState<ConfigTab>('geral')

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-brand-primary/10 rounded-lg">
          <Settings className="w-6 h-6 text-brand-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Configurações</h1>
          <p className="text-text-secondary">Parâmetros e preferências do sistema</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-surface-muted rounded-lg mb-6 w-fit">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-surface-elevated text-brand-primary shadow-sm'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.name}
          </button>
        ))}
      </div>

      {/* Content */}
      <Card variant="outlined">
        {activeTab === 'geral' && <ConfigGeral />}
        {activeTab === 'aparencia' && <ConfigAparencia />}
        {activeTab === 'notificacoes' && <ConfigNotificacoes />}
        {activeTab === 'integracoes' && <ConfigIntegracoes />}
      </Card>
    </div>
  )
}

function ConfigGeral() {
  return (
    <div className="p-6 space-y-6">
      <h2 className="text-lg font-semibold text-text-primary">Configurações Gerais</h2>
      
      <div className="grid gap-6">
        <div>
          <label htmlFor="app-name" className="form-label">
            Nome da Aplicação
          </label>
          <input
            id="app-name"
            type="text"
            defaultValue="Template Platform"
            className="form-input"
          />
        </div>

        <div>
          <label htmlFor="default-language" className="form-label">
            Idioma Padrão
          </label>
          <select id="default-language" className="form-select">
            <option value="pt-BR">Português (Brasil)</option>
            <option value="en-US">English (US)</option>
            <option value="es">Español</option>
          </select>
        </div>

        <div>
          <label htmlFor="timezone" className="form-label">
            Fuso Horário
          </label>
          <select id="timezone" className="form-select">
            <option value="America/Sao_Paulo">America/Sao_Paulo (GMT-3)</option>
            <option value="America/Cuiaba">America/Cuiaba (GMT-4)</option>
            <option value="UTC">UTC</option>
          </select>
        </div>

        <div className="flex items-center justify-between p-4 bg-surface-muted rounded-lg">
          <div>
            <h3 className="font-medium text-text-primary">Modo de Manutenção</h3>
            <p className="text-sm text-text-secondary">Desabilita acesso para usuários não-admin</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" className="sr-only peer" aria-label="Modo de manutenção" />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-teal-300 dark:peer-focus:ring-teal-800 rounded-full peer dark:bg-gray-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-500 peer-checked:bg-teal-600"></div>
          </label>
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-border-default">
        <Button variant="ghost" leftIcon={<RotateCcw size={16} />}>
          Restaurar Padrões
        </Button>
        <Button variant="primary" leftIcon={<Save size={16} />}>
          Salvar Alterações
        </Button>
      </div>
    </div>
  )
}

function ConfigAparencia() {
  return (
    <div className="p-6 space-y-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Aparência</h2>
      
      <div className="grid gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Tema
          </label>
          <div className="grid grid-cols-3 gap-3">
            {['light', 'dark', 'system'].map(theme => (
              <button
                key={theme}
                className="p-4 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:border-teal-500 transition-colors text-center"
              >
                <span className="block text-sm font-medium text-gray-900 dark:text-white capitalize">{theme === 'system' ? 'Sistema' : theme === 'light' ? 'Claro' : 'Escuro'}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Cor Principal
          </label>
          <div className="flex gap-3">
            {['teal', 'blue', 'purple', 'green', 'orange'].map(color => (
              <button
                key={color}
                aria-label={`Selecionar cor ${color}`}
                title={`Cor ${color}`}
                className={`w-10 h-10 rounded-full bg-${color}-500 hover:ring-2 hover:ring-offset-2 hover:ring-${color}-500 transition-all`}
                style={{ backgroundColor: color === 'teal' ? '#14b8a6' : color === 'blue' ? '#3b82f6' : color === 'purple' ? '#8b5cf6' : color === 'green' ? '#22c55e' : '#f97316' }}
              />
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="ui-density" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Densidade da Interface
          </label>
          <select id="ui-density" aria-label="Densidade da interface" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            <option value="comfortable">Confortável</option>
            <option value="compact">Compacto</option>
            <option value="spacious">Espaçoso</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-border-default">
        <Button variant="primary" leftIcon={<Save size={16} />}>
          Salvar Alterações
        </Button>
      </div>
    </div>
  )
}

function ConfigNotificacoes() {
  return (
    <div className="p-6 space-y-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Notificações</h2>
      
      <div className="space-y-4">
        {[
          { id: 'email', title: 'Notificações por Email', desc: 'Receber alertas importantes por email' },
          { id: 'push', title: 'Notificações Push', desc: 'Notificações no navegador' },
          { id: 'alerts', title: 'Alertas do Sistema', desc: 'Alertas críticos e avisos' },
          { id: 'reports', title: 'Relatórios Automáticos', desc: 'Receber relatórios semanais' },
        ].map(item => (
          <div key={item.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">{item.title}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">{item.desc}</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" aria-label={item.title} />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-teal-300 dark:peer-focus:ring-teal-800 rounded-full peer dark:bg-gray-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-500 peer-checked:bg-teal-600"></div>
            </label>
          </div>
        ))}
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-border-default">
        <Button variant="primary" leftIcon={<Save size={16} />}>
          Salvar Alterações
        </Button>
      </div>
    </div>
  )
}

function ConfigIntegracoes() {
  return (
    <div className="p-6 space-y-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Integrações</h2>
      
      <div className="space-y-4">
        {[
          { id: 'keycloak', name: 'Keycloak', status: 'connected', desc: 'Autenticação OIDC' },
          { id: 'api', name: 'API Backend', status: 'connected', desc: 'REST API principal' },
          { id: 'storage', name: 'Storage (S3/MinIO)', status: 'disconnected', desc: 'Armazenamento de arquivos' },
          { id: 'email', name: 'Servidor de Email', status: 'disconnected', desc: 'SMTP para notificações' },
        ].map(item => (
          <div key={item.id} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <div className="flex items-center gap-4">
              <div className={`w-3 h-3 rounded-full ${item.status === 'connected' ? 'bg-green-500' : 'bg-gray-400'}`} />
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white">{item.name}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">{item.desc}</p>
              </div>
            </div>
            <button className="px-3 py-1.5 text-sm font-medium text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/20 rounded-lg transition-colors">
              Configurar
            </button>
          </div>
        ))}
      </div>

      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <h3 className="font-medium text-blue-900 dark:text-blue-300">API Keys</h3>
        <p className="text-sm text-blue-700 dark:text-blue-400 mt-1">
          Gerencie suas chaves de API para integrações externas.
        </p>
        <button className="mt-3 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors">
          Gerenciar API Keys
        </button>
      </div>
    </div>
  )
}

export default ConfigPage
