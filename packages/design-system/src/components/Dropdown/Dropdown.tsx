/**
 * Dropdown Component
 * 
 * Menu dropdown com trigger e lista de itens.
 */

import { useState, useRef, useEffect, createContext, useContext, type ReactNode, type HTMLAttributes, type ButtonHTMLAttributes } from 'react'
import { ChevronDown } from 'lucide-react'
import clsx from 'clsx'
import './Dropdown.css'

export type DropdownAlign = 'start' | 'end' | 'center'

interface DropdownContextValue {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  close: () => void
}

const DropdownContext = createContext<DropdownContextValue | null>(null)

function useDropdownContext() {
  const context = useContext(DropdownContext)
  if (!context) {
    throw new Error('Dropdown components must be used within a Dropdown provider')
  }
  return context
}

// Main Dropdown Container
export interface DropdownProps extends HTMLAttributes<HTMLDivElement> {
  /** Alinhamento do menu */
  align?: DropdownAlign
  children?: ReactNode
}

export function Dropdown({ align = 'start', className, children, ...props }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const close = () => setIsOpen(false)

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  // Close on ESC
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false)
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEsc)
    }

    return () => document.removeEventListener('keydown', handleEsc)
  }, [isOpen])

  return (
    <DropdownContext.Provider value={{ isOpen, setIsOpen, close }}>
      <div
        ref={dropdownRef}
        className={clsx('ds-dropdown', `ds-dropdown--${align}`, className)}
        {...props}
      >
        {children}
      </div>
    </DropdownContext.Provider>
  )
}

// Dropdown Trigger
export interface DropdownTriggerProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Mostrar seta */
  showArrow?: boolean
  children?: ReactNode
}

export function DropdownTrigger({ showArrow = true, className, children, ...props }: DropdownTriggerProps) {
  const { isOpen, setIsOpen } = useDropdownContext()

  return (
    <button
      type="button"
      className={clsx('ds-dropdown__trigger', isOpen && 'ds-dropdown__trigger--open', className)}
      onClick={() => setIsOpen(!isOpen)}
      aria-expanded={isOpen ? 'true' : 'false'}
      aria-haspopup="menu"
      {...props}
    >
      {children}
      {showArrow && (
        <ChevronDown size={16} className={clsx('ds-dropdown__arrow', isOpen && 'ds-dropdown__arrow--open')} />
      )}
    </button>
  )
}

// Dropdown Menu
export interface DropdownMenuProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode
}

export function DropdownMenu({ className, children, ...props }: DropdownMenuProps) {
  const { isOpen } = useDropdownContext()

  if (!isOpen) return null

  return (
    <div className={clsx('ds-dropdown__menu', className)} role="menu" {...props}>
      {children}
    </div>
  )
}

// Dropdown Item
export interface DropdownItemProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Ícone opcional */
  icon?: ReactNode
  /** Item destrutivo (vermelho) */
  destructive?: boolean
  children?: ReactNode
}

export function DropdownItem({ icon, destructive = false, className, children, onClick, ...props }: DropdownItemProps) {
  const { close } = useDropdownContext()

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    onClick?.(e)
    close()
  }

  return (
    <button
      type="button"
      className={clsx('ds-dropdown__item', destructive && 'ds-dropdown__item--destructive', className)}
      role="menuitem"
      onClick={handleClick}
      {...props}
    >
      {icon && <span className="ds-dropdown__item-icon">{icon}</span>}
      <span className="ds-dropdown__item-text">{children}</span>
    </button>
  )
}

// Dropdown Separator
export function DropdownSeparator({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('ds-dropdown__separator', className)} role="separator" {...props} />
}

// Dropdown Label
export function DropdownLabel({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx('ds-dropdown__label', className)} {...props}>
      {children}
    </div>
  )
}

export default Dropdown
