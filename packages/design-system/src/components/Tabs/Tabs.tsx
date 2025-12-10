/**
 * Tabs Component
 * 
 * Sistema de navegação por abas.
 */

import { createContext, useContext, useState, type ReactNode, type HTMLAttributes } from 'react'
import clsx from 'clsx'
import './Tabs.css'

export type TabsVariant = 'line' | 'pills' | 'enclosed'
export type TabsSize = 'sm' | 'md' | 'lg'

interface TabsContextValue {
  activeTab: string
  setActiveTab: (id: string) => void
  variant: TabsVariant
  size: TabsSize
}

const TabsContext = createContext<TabsContextValue | null>(null)

function useTabsContext() {
  const context = useContext(TabsContext)
  if (!context) {
    throw new Error('Tabs components must be used within a Tabs provider')
  }
  return context
}

// Main Tabs component
export interface TabsProps extends Omit<HTMLAttributes<HTMLDivElement>, 'onChange'> {
  /** ID da aba ativa inicial */
  defaultValue?: string
  /** ID da aba ativa (controlado) */
  value?: string
  /** Callback quando aba muda */
  onChange?: (value: string) => void
  /** Variante visual */
  variant?: TabsVariant
  /** Tamanho */
  size?: TabsSize
  children?: ReactNode
}

export function Tabs({
  defaultValue,
  value,
  onChange,
  variant = 'line',
  size = 'md',
  className,
  children,
  ...props
}: TabsProps) {
  const [internalValue, setInternalValue] = useState(defaultValue || '')
  const activeTab = value !== undefined ? value : internalValue

  const setActiveTab = (id: string) => {
    if (value === undefined) {
      setInternalValue(id)
    }
    onChange?.(id)
  }

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab, variant, size }}>
      <div className={clsx('ds-tabs', className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  )
}

// TabList component
export interface TabListProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode
}

export function TabList({ className, children, ...props }: TabListProps) {
  const { variant } = useTabsContext()

  return (
    <div 
      className={clsx('ds-tabs__list', `ds-tabs__list--${variant}`, className)} 
      role="tablist"
      {...props}
    >
      {children}
    </div>
  )
}

// Tab component
export interface TabProps extends HTMLAttributes<HTMLButtonElement> {
  /** ID único da aba */
  value: string
  /** Ícone opcional */
  icon?: ReactNode
  /** Desabilitado */
  disabled?: boolean
  children?: ReactNode
}

export function Tab({ value, icon, disabled = false, className, children, ...props }: TabProps) {
  const { activeTab, setActiveTab, variant, size } = useTabsContext()
  const isActive = activeTab === value

  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive ? 'true' : 'false'}
      aria-controls={`tabpanel-${value}`}
      id={`tab-${value}`}
      tabIndex={isActive ? 0 : -1}
      disabled={disabled}
      className={clsx(
        'ds-tabs__tab',
        `ds-tabs__tab--${variant}`,
        `ds-tabs__tab--${size}`,
        isActive && 'ds-tabs__tab--active',
        className
      )}
      onClick={() => setActiveTab(value)}
      {...props}
    >
      {icon && <span className="ds-tabs__tab-icon">{icon}</span>}
      <span className="ds-tabs__tab-text">{children}</span>
    </button>
  )
}

// TabPanels component
export interface TabPanelsProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode
}

export function TabPanels({ className, children, ...props }: TabPanelsProps) {
  return (
    <div className={clsx('ds-tabs__panels', className)} {...props}>
      {children}
    </div>
  )
}

// TabPanel component
export interface TabPanelProps extends HTMLAttributes<HTMLDivElement> {
  /** ID correspondente à aba */
  value: string
  children?: ReactNode
}

export function TabPanel({ value, className, children, ...props }: TabPanelProps) {
  const { activeTab } = useTabsContext()
  const isActive = activeTab === value

  if (!isActive) return null

  return (
    <div
      role="tabpanel"
      id={`tabpanel-${value}`}
      aria-labelledby={`tab-${value}`}
      tabIndex={0}
      className={clsx('ds-tabs__panel', className)}
      {...props}
    >
      {children}
    </div>
  )
}

export default Tabs
