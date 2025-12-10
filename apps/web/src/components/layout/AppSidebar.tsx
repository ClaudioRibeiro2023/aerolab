import { NavLink, Link } from 'react-router-dom'
import { useAuth } from '@template/shared'
import { 
  Home, 
  User, 
  Settings, 
  LogOut,
  ChevronRight,
  LayoutGrid,
  BarChart3,
  Database,
  Users,
  Shield,
  FileText,
  Activity,
  PanelLeftClose,
  PanelLeftOpen,
  type LucideIcon
} from 'lucide-react'
import clsx from 'clsx'
import { useNavigationConfig } from '@/hooks/useNavigationConfig'

// Mapa de ícones dinâmicos
const ICON_MAP: Record<string, LucideIcon> = {
  Home,
  User,
  Settings,
  LayoutGrid,
  BarChart3,
  Database,
  Users,
  Shield,
  FileText,
  Activity,
}

// Função helper para obter ícone
function getIcon(iconName?: string, FallbackIcon: LucideIcon = LayoutGrid): React.ReactNode {
  if (!iconName) return <FallbackIcon size={20} />
  const Icon = ICON_MAP[iconName] || FallbackIcon
  return <Icon size={20} />
}

const APP_NAME = 'Template'
const APP_VERSION = '0.1.0'

interface AppSidebarProps {
  collapsed?: boolean
  onToggle?: () => void
}

export function AppSidebar({ collapsed = false, onToggle }: AppSidebarProps) {
  const { user, logout } = useAuth()
  
  // Usar hook de configuração dinâmica
  const { authorizedModules } = useNavigationConfig()

  // Converter módulos para itens de navegação
  const navItems = authorizedModules
    .filter(m => m.showInSidebar !== false && m.enabled)
    .map(module => ({
      label: module.name,
      path: module.path,
      icon: getIcon(module.icon),
      group: module.group || 'Módulos',
    }))

  return (
    <aside 
      className={clsx(
        'fixed left-0 top-0 h-screen flex flex-col sidebar-gradient transition-all duration-300 z-40',
        collapsed ? 'w-[var(--sidebar-collapsed-width,72px)]' : 'w-[var(--sidebar-width)]'
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-white/10">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-8 h-8 min-w-[32px] rounded-lg bg-brand-primary flex items-center justify-center">
            <span className="text-white font-bold text-sm">T</span>
          </div>
          {!collapsed && <span className="text-white font-semibold text-lg whitespace-nowrap">Template</span>}
        </div>
        {onToggle && (
          <button
            onClick={onToggle}
            className="p-1.5 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-colors"
            title={collapsed ? 'Expandir menu' : 'Recolher menu'}
          >
            {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 overflow-y-auto">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) => clsx(
                  'flex items-center gap-3 rounded-lg transition-all duration-200',
                  'text-white/70 hover:text-white hover:bg-white/10',
                  collapsed ? 'px-3 py-2.5 justify-center' : 'px-3 py-2.5',
                  isActive && 'bg-brand-primary text-white shadow-lg'
                )}
              >
                <span className="min-w-[20px]">{item.icon}</span>
                {!collapsed && (
                  <>
                    <span className="font-medium flex-1">{item.label}</span>
                    <ChevronRight size={16} className="opacity-50" />
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Serviços Técnicos */}
      <div className={clsx('py-3 border-t border-white/10', collapsed ? 'px-2' : 'px-4')}>
        {!collapsed && (
          <p className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-2">
            Serviços Técnicos
          </p>
        )}
        <div className={clsx('flex items-center', collapsed ? 'flex-col gap-1' : 'gap-2')}>
          <Link
            to="/admin/etl"
            className="p-2 rounded-lg hover:bg-white/10 text-white/50 hover:text-white transition-colors"
            title="ETL & Dados"
          >
            <Database size={18} />
          </Link>
          <Link
            to="/admin/config"
            className="p-2 rounded-lg hover:bg-white/10 text-white/50 hover:text-white transition-colors"
            title="Configurações"
          >
            <Settings size={18} />
          </Link>
          <Link
            to="/admin/observability"
            className="p-2 rounded-lg hover:bg-white/10 text-white/50 hover:text-white transition-colors"
            title="Observabilidade"
          >
            <Activity size={18} />
          </Link>
        </div>
      </div>

      {/* App Info */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-white/10">
          <p className="text-white font-semibold">{APP_NAME}</p>
          <p className="text-white/40 text-xs">v{APP_VERSION} · © {new Date().getFullYear()}</p>
          <p className="text-white/40 text-xs">Todos os direitos reservados</p>
          <div className="flex items-center gap-2 mt-2">
            <Link
              to="/docs"
              className="inline-flex items-center gap-1 px-2 py-1 text-xs text-white/60 hover:text-white bg-white/5 hover:bg-white/10 rounded transition-colors"
            >
              <FileText size={12} />
              Documentação
            </Link>
            <Link
              to="/lgpd"
              className="inline-flex items-center gap-1 px-2 py-1 text-xs text-white/60 hover:text-white bg-white/5 hover:bg-white/10 rounded transition-colors"
            >
              <Shield size={12} />
              LGPD
            </Link>
          </div>
        </div>
      )}

      {/* User section */}
      <div className={clsx('border-t border-white/10', collapsed ? 'p-2' : 'p-4')}>
        {collapsed ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-brand-primary/20 flex items-center justify-center">
              <User size={20} className="text-brand-accent" />
            </div>
            <button
              onClick={logout}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors"
              title="Sair"
            >
              <LogOut size={18} />
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-brand-primary/20 flex items-center justify-center">
                <User size={20} className="text-brand-accent" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">{user?.name || 'Usuário'}</p>
                <p className="text-white/50 text-sm truncate">{user?.email || ''}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-colors"
            >
              <LogOut size={18} />
              <span>Sair</span>
            </button>
          </>
        )}
      </div>
    </aside>
  )
}
