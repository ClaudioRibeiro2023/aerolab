/**
 * GlobalSearch (Command Palette)
 * 
 * Componente de busca global acionado por Ctrl+K.
 * Permite buscar em módulos, funções, páginas e ações rápidas.
 */

import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Search, 
  ArrowRight, 
  FileText, 
  Settings, 
  Database,
  Activity,
  Shield,
  Book,
  X,
  CornerDownLeft
} from 'lucide-react'
import clsx from 'clsx'
import { useNavigationConfig } from '@/hooks/useNavigationConfig'

// Tipos
interface SearchResult {
  id: string
  title: string
  subtitle?: string
  path: string
  icon: typeof Search
  category: 'module' | 'function' | 'page' | 'action'
}

interface GlobalSearchProps {
  isOpen: boolean
  onClose: () => void
}

// Ícones por categoria
const CATEGORY_ICONS: Record<string, typeof Search> = {
  etl: Database,
  observabilidade: Activity,
  lgpd: Shield,
  documentacao: Book,
  configuracoes: Settings,
  default: FileText,
}

// Ações rápidas
const QUICK_ACTIONS: SearchResult[] = [
  { id: 'action-home', title: 'Ir para Início', path: '/', icon: ArrowRight, category: 'action' },
  { id: 'action-config', title: 'Configurações', path: '/admin/config', icon: Settings, category: 'action' },
  { id: 'action-docs', title: 'Documentação', path: '/docs', icon: Book, category: 'action' },
]

export function GlobalSearch({ isOpen, onClose }: GlobalSearchProps) {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const { authorizedModules, getModuleFunctions } = useNavigationConfig()
  
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)

  // Construir lista de resultados pesquisáveis
  const allResults = useMemo(() => {
    const results: SearchResult[] = []

    // Adicionar módulos
    authorizedModules.forEach(module => {
      const iconKey = module.id.toLowerCase()
      results.push({
        id: `module-${module.id}`,
        title: module.name,
        subtitle: module.description,
        path: module.path,
        icon: CATEGORY_ICONS[iconKey] || CATEGORY_ICONS.default,
        category: 'module',
      })

      // Adicionar funções do módulo
      const functions = getModuleFunctions(module.id)
      functions.forEach(func => {
        results.push({
          id: `func-${func.id}`,
          title: func.name,
          subtitle: `${module.name} › ${func.subtitle || ''}`,
          path: func.path,
          icon: CATEGORY_ICONS[iconKey] || CATEGORY_ICONS.default,
          category: 'function',
        })
      })
    })

    // Adicionar ações rápidas
    results.push(...QUICK_ACTIONS)

    return results
  }, [authorizedModules, getModuleFunctions])

  // Filtrar resultados por query
  const filteredResults = useMemo(() => {
    if (!query.trim()) {
      // Mostrar ações rápidas e módulos principais quando não há busca
      return allResults.slice(0, 8)
    }

    const lowerQuery = query.toLowerCase()
    return allResults
      .filter(result => 
        result.title.toLowerCase().includes(lowerQuery) ||
        result.subtitle?.toLowerCase().includes(lowerQuery)
      )
      .slice(0, 10)
  }, [allResults, query])

  // Reset ao abrir
  useEffect(() => {
    if (isOpen) {
      setQuery('')
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen])

  // Keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev < filteredResults.length - 1 ? prev + 1 : 0
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : filteredResults.length - 1
        )
        break
      case 'Enter':
        e.preventDefault()
        if (filteredResults[selectedIndex]) {
          navigate(filteredResults[selectedIndex].path)
          onClose()
        }
        break
      case 'Escape':
        e.preventDefault()
        onClose()
        break
    }
  }, [filteredResults, selectedIndex, navigate, onClose])

  // Scroll item selecionado para view
  useEffect(() => {
    const list = listRef.current
    if (!list) return

    const selected = list.querySelector(`[data-index="${selectedIndex}"]`)
    if (selected) {
      selected.scrollIntoView({ block: 'nearest' })
    }
  }, [selectedIndex])

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div 
        className="global-search__backdrop"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="global-search">
        {/* Header com input */}
        <div className="global-search__header">
          <Search size={20} className="global-search__icon" />
          <input
            ref={inputRef}
            type="text"
            className="global-search__input"
            placeholder="Buscar módulos, funções, páginas..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setSelectedIndex(0)
            }}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={onClose}
            className="global-search__close"
            title="Fechar (Esc)"
          >
            <X size={18} />
          </button>
        </div>

        {/* Resultados */}
        <div ref={listRef} className="global-search__results">
          {filteredResults.length === 0 ? (
            <div className="global-search__empty">
              <Search size={32} className="global-search__empty-icon" />
              <p>Nenhum resultado encontrado</p>
              <span>Tente outro termo de busca</span>
            </div>
          ) : (
            filteredResults.map((result, index) => {
              const Icon = result.icon
              return (
                <button
                  key={result.id}
                  data-index={index}
                  className={clsx(
                    'global-search__item',
                    index === selectedIndex && 'is-selected'
                  )}
                  onClick={() => {
                    navigate(result.path)
                    onClose()
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <div className="global-search__item-icon">
                    <Icon size={18} />
                  </div>
                  <div className="global-search__item-content">
                    <span className="global-search__item-title">{result.title}</span>
                    {result.subtitle && (
                      <span className="global-search__item-subtitle">{result.subtitle}</span>
                    )}
                  </div>
                  <div className="global-search__item-badge">
                    {result.category === 'module' && 'Módulo'}
                    {result.category === 'function' && 'Função'}
                    {result.category === 'page' && 'Página'}
                    {result.category === 'action' && 'Ação'}
                  </div>
                </button>
              )
            })
          )}
        </div>

        {/* Footer com atalhos */}
        <div className="global-search__footer">
          <div className="global-search__shortcut">
            <kbd>↑</kbd><kbd>↓</kbd>
            <span>Navegar</span>
          </div>
          <div className="global-search__shortcut">
            <kbd><CornerDownLeft size={12} /></kbd>
            <span>Abrir</span>
          </div>
          <div className="global-search__shortcut">
            <kbd>Esc</kbd>
            <span>Fechar</span>
          </div>
        </div>
      </div>
    </>
  )
}

// Hook para usar o GlobalSearch
export function useGlobalSearch() {
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+K ou Cmd+K
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen(prev => !prev)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return {
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    toggle: () => setIsOpen(prev => !prev),
  }
}

export default GlobalSearch
