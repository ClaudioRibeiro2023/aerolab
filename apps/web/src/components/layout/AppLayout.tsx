import { useState, useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { AppSidebar } from './AppSidebar'
import { Header } from './Header'
import { ModuleFunctionsPanel } from '@/components/navigation'
import { GlobalSearch, useGlobalSearch } from '@/components/search'
import { NAVIGATION } from '@/navigation/map'
import clsx from 'clsx'

const SIDEBAR_COLLAPSED_KEY = 'sidebar-collapsed'

// Hook para detectar mobile
function useIsMobile(breakpoint = 768) {
  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' ? window.innerWidth < breakpoint : false
  )

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < breakpoint)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [breakpoint])

  return isMobile
}

export function AppLayout() {
  const location = useLocation()
  const isMobile = useIsMobile()
  const globalSearch = useGlobalSearch()
  const [isPanelOpen, setIsPanelOpen] = useState(true)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem(SIDEBAR_COLLAPSED_KEY)
    return saved === 'true'
  })

  // Fechar menu mobile ao mudar de página
  useEffect(() => {
    setIsMobileMenuOpen(false)
  }, [location.pathname])

  // Persistir estado da sidebar
  useEffect(() => {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(isSidebarCollapsed))
  }, [isSidebarCollapsed])

  // Verificar se o módulo atual tem funções para mostrar o painel
  const hasModuleFunctions = NAVIGATION.modules.some(module => {
    const isModuleActive = location.pathname === module.path || 
                          location.pathname.startsWith(module.path + '/')
    
    // Verificar também pelas funções
    const isFunctionActive = module.functions?.some(
      func => location.pathname === func.path || location.pathname.startsWith(func.path + '/')
    )
    
    return (isModuleActive || isFunctionActive) && module.functions && module.functions.length > 0
  })

  // Calcular margem do conteúdo principal
  const getContentMargin = () => {
    if (isMobile) return '0'
    if (hasModuleFunctions && isPanelOpen) {
      return `calc(${isSidebarCollapsed ? '72px' : 'var(--sidebar-width)'} + var(--functions-panel-width, 280px))`
    }
    return isSidebarCollapsed ? '72px' : 'var(--sidebar-width)'
  }

  return (
    <div className="flex min-h-screen bg-surface-base">
      {/* Mobile overlay */}
      {isMobile && (
        <div 
          className={clsx('sidebar-overlay', isMobileMenuOpen && 'visible')}
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={clsx(
        isMobile && 'sidebar-mobile',
        isMobile && isMobileMenuOpen && 'open'
      )}>
        <AppSidebar 
          collapsed={isMobile ? false : isSidebarCollapsed}
          onToggle={isMobile ? undefined : () => setIsSidebarCollapsed(prev => !prev)}
        />
      </div>
      
      {/* Functions Panel - hidden on mobile */}
      {hasModuleFunctions && !isMobile && (
        <>
          <ModuleFunctionsPanel 
            isOpen={isPanelOpen} 
            onClose={() => setIsPanelOpen(false)}
          />
          {/* Toggle button when panel is closed */}
          {!isPanelOpen && (
            <button
              onClick={() => setIsPanelOpen(true)}
              className={clsx(
                'functions-panel-toggle',
                isSidebarCollapsed && 'sidebar-collapsed'
              )}
              title="Abrir painel de funções"
              aria-label="Abrir painel de funções"
            >
              <ChevronRight size={16} />
            </button>
          )}
        </>
      )}
      
      {/* Main content */}
      <div 
        className={clsx(
          'flex-1 flex flex-col transition-all duration-300',
          isMobile && 'main-content-mobile'
        )}
        style={{ marginLeft: getContentMargin() }}
      >
        <Header 
          showPanelToggle={false}
          isPanelOpen={isPanelOpen}
          onTogglePanel={() => setIsPanelOpen(prev => !prev)}
          onMobileMenuToggle={() => setIsMobileMenuOpen(prev => !prev)}
        />
        <main className="flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>

      {/* Global Search (Ctrl+K) */}
      <GlobalSearch 
        isOpen={globalSearch.isOpen} 
        onClose={globalSearch.close} 
      />
    </div>
  )
}
