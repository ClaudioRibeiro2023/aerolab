import { useAuth } from '@template/shared'
import { Card } from '@template/design-system'
import { ArrowRight, Database, Activity, FileText, Shield } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const quickLinks = [
  { title: 'ETL & Dados', description: 'Importar, tratar e catalogar dados', icon: Database, path: '/admin/etl' },
  { title: 'Observabilidade', description: 'Métricas, logs e saúde do sistema', icon: Activity, path: '/admin/observability' },
  { title: 'Documentação', description: 'Guias, API e changelog', icon: FileText, path: '/docs' },
  { title: 'LGPD & Privacidade', description: 'Política, consentimento e meus dados', icon: Shield, path: '/lgpd' },
]

export function HomePage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="welcome-banner mb-8">
        <h1 className="text-3xl font-bold mb-2">
          Bem-vindo, {user?.name?.split(' ')[0] || 'Usuário'}! 👋
        </h1>
        <p className="text-white/80 text-lg">
          Este é o seu painel de controle. Use o menu lateral para navegar.
        </p>
      </div>

      {/* Quick Links */}
      <h2 className="text-xl font-semibold text-text-primary mb-4">Acesso Rápido</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {quickLinks.map((item) => (
          <Card 
            key={item.path} 
            variant="outlined" 
            interactive 
            className="group"
            onClick={() => navigate(item.path)}
          >
            <div className="p-6">
              <div className="w-12 h-12 rounded-lg bg-brand-primary/10 flex items-center justify-center mb-4 group-hover:bg-brand-primary/20 transition-colors">
                <item.icon size={24} className="text-brand-primary" />
              </div>
              <h3 className="font-semibold text-text-primary mb-1">{item.title}</h3>
              <p className="text-sm text-text-secondary mb-3">{item.description}</p>
              <span className="flex items-center gap-1 text-brand-primary text-sm font-medium group-hover:gap-2 transition-all">
                Acessar <ArrowRight size={16} />
              </span>
            </div>
          </Card>
        ))}
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card variant="elevated">
          <div className="p-6">
            <h3 className="font-semibold text-text-primary mb-2">🚀 Começando</h3>
            <p className="text-text-secondary text-sm">
              Este é um template pronto para uso. Adicione seus módulos em <code className="bg-surface-muted px-1 rounded">src/modules/</code>
            </p>
          </div>
        </Card>
        <Card variant="elevated">
          <div className="p-6">
            <h3 className="font-semibold text-text-primary mb-2">📚 Documentação</h3>
            <p className="text-text-secondary text-sm">
              Consulte a documentação em <code className="bg-surface-muted px-1 rounded">docs/</code> para mais informações.
            </p>
          </div>
        </Card>
        <Card variant="elevated">
          <div className="p-6">
            <h3 className="font-semibold text-text-primary mb-2">🔐 Autenticação</h3>
            <p className="text-text-secondary text-sm">
              Sistema de auth via Keycloak já configurado. Gerencie roles e permissões facilmente.
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}
