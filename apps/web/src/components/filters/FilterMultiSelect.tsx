/**
 * FilterMultiSelect
 * 
 * Componente de filtro com seleção múltipla via checkboxes.
 */

import { useState, useRef, useEffect } from 'react'
import { ChevronDown, X, Check } from 'lucide-react'
import clsx from 'clsx'
import type { FilterValue } from '@/hooks/useFilters'
import type { FilterOption } from '@/config/navigation-schema'

interface FilterMultiSelectProps {
  id: string
  label: string
  placeholder?: string
  options: FilterOption[]
  value: FilterValue
  onChange: (value: FilterValue) => void
  onClear: () => void
  disabled?: boolean
  className?: string
}

export function FilterMultiSelect({
  id,
  label,
  placeholder = 'Selecione...',
  options,
  value,
  onChange,
  onClear,
  disabled = false,
  className,
}: FilterMultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  
  const selectedValues = Array.isArray(value) ? (value as string[]) : []
  const hasValue = selectedValues.length > 0

  // Fechar ao clicar fora
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const toggleOption = (optValue: string) => {
    if (selectedValues.includes(optValue)) {
      onChange(selectedValues.filter(v => v !== optValue))
    } else {
      onChange([...selectedValues, optValue])
    }
  }

  const getDisplayText = () => {
    if (selectedValues.length === 0) return placeholder
    if (selectedValues.length === 1) {
      return options.find(o => o.value === selectedValues[0])?.label || selectedValues[0]
    }
    return `${selectedValues.length} selecionados`
  }

  return (
    <div 
      ref={containerRef}
      className={clsx('filter-item', 'filter-multiselect', isOpen && 'is-open', className)}
    >
      <label htmlFor={id} className="filter-item__label">
        {label}
      </label>
      
      <div className="filter-item__control">
        <button
          type="button"
          id={id}
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          className="filter-multiselect__trigger"
          aria-expanded={isOpen ? 'true' : 'false'}
          aria-haspopup="listbox"
          aria-label={`${label}: ${getDisplayText()}`}
        >
          <span className={clsx('filter-multiselect__text', !hasValue && 'placeholder')}>
            {getDisplayText()}
          </span>
          <ChevronDown size={14} className={clsx('filter-multiselect__chevron', isOpen && 'rotated')} />
        </button>
        
        {hasValue && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onClear()
            }}
            className="filter-item__clear"
            title="Limpar"
          >
            <X size={12} />
          </button>
        )}
        
        {isOpen && (
          <div 
            className="filter-multiselect__dropdown" 
            role="group"
            aria-label={`Opções de ${label}`}
          >
            {options.map(opt => (
              <label
                key={opt.value}
                className={clsx(
                  'filter-multiselect__option',
                  selectedValues.includes(opt.value) && 'is-selected'
                )}
              >
                <input
                  type="checkbox"
                  checked={selectedValues.includes(opt.value)}
                  onChange={() => toggleOption(opt.value)}
                  className="sr-only"
                  aria-label={opt.label}
                />
                <span className="filter-multiselect__checkbox">
                  {selectedValues.includes(opt.value) && <Check size={12} />}
                </span>
                <span className="filter-multiselect__label">{opt.label}</span>
              </label>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default FilterMultiSelect
