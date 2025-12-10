/**
 * FilterToggle
 * 
 * Componente de filtro tipo toggle (on/off).
 */

import clsx from 'clsx'
import type { FilterValue } from '@/hooks/useFilters'

interface FilterToggleProps {
  id: string
  label: string
  placeholder?: string
  value: FilterValue
  onChange: (value: FilterValue) => void
  onClear: () => void
  disabled?: boolean
  className?: string
}

export function FilterToggle({
  id,
  label,
  value,
  onChange,
  disabled = false,
  className,
}: FilterToggleProps) {
  const isChecked = value === true

  const handleChange = () => {
    onChange(!isChecked)
  }

  return (
    <div className={clsx('filter-item', 'filter-toggle', className)}>
      <label htmlFor={id} className="filter-toggle__wrapper">
        <span className="filter-item__label">{label}</span>
        
        <button
          type="button"
          id={id}
          role="switch"
          aria-checked={isChecked ? 'true' : 'false'}
          aria-label={`${label}: ${isChecked ? 'Ativado' : 'Desativado'}`}
          onClick={handleChange}
          disabled={disabled}
          className={clsx('filter-toggle__switch', isChecked && 'is-on')}
        >
          <span className="filter-toggle__track" />
          <span className="filter-toggle__thumb" />
        </button>
      </label>
    </div>
  )
}

export default FilterToggle
