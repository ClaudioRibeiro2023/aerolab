import { useAuth } from '@template/shared'
import { User, Mail, Shield } from 'lucide-react'

export function ProfilePage() {
  const { user } = useAuth()

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-text-primary mb-6">Meu Perfil</h1>

      <div className="bg-surface-elevated rounded-xl border border-border-default overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-brand-primary to-brand-secondary p-8">
          <div className="flex items-center gap-6">
            <div className="w-20 h-20 rounded-full bg-white/20 flex items-center justify-center">
              <User size={40} className="text-white" />
            </div>
            <div className="text-white">
              <h2 className="text-2xl font-bold">{user?.name || 'Usuário'}</h2>
              <p className="text-white/80">{user?.email || 'email@example.com'}</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-3 p-4 bg-surface-muted rounded-lg">
              <Mail className="text-brand-primary" size={20} />
              <div>
                <p className="text-sm text-text-secondary">Email</p>
                <p className="font-medium text-text-primary">{user?.email || 'Não informado'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-surface-muted rounded-lg">
              <Shield className="text-brand-primary" size={20} />
              <div>
                <p className="text-sm text-text-secondary">Perfis</p>
                <p className="font-medium text-text-primary">{user?.roles?.join(', ') || 'Nenhum'}</p>
              </div>
            </div>
          </div>

          {/* Roles badges */}
          <div>
            <h3 className="text-sm font-medium text-text-secondary mb-3">Permissões</h3>
            <div className="flex flex-wrap gap-2">
              {user?.roles?.map((role) => (
                <span 
                  key={role}
                  className="px-3 py-1 bg-brand-primary/10 text-brand-primary rounded-full text-sm font-medium"
                >
                  {role}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
