import { forwardRef, type HTMLAttributes, type ReactNode } from 'react'
import clsx from 'clsx'
import './StatusBadge.css'

export type StatusBadgeVariant = 'success' | 'warning' | 'error' | 'info' | 'pending'
export type StatusBadgeSize = 'sm' | 'md'

export interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  /** Variante visual do badge */
  variant?: StatusBadgeVariant
  /** Tamanho do badge */
  size?: StatusBadgeSize
  /** Ícone opcional à esquerda */
  icon?: ReactNode
}

export const StatusBadge = forwardRef<HTMLSpanElement, StatusBadgeProps>(
  ({ variant = 'info', size = 'md', icon, className, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={clsx(
          'ds-status-badge',
          `ds-status-badge--${variant}`,
          `ds-status-badge--${size}`,
          className
        )}
        {...props}
      >
        {icon && (
          <span className="ds-status-badge__icon" aria-hidden="true">
            {icon}
          </span>
        )}
        <span className="ds-status-badge__label">{children}</span>
      </span>
    )
  }
)

StatusBadge.displayName = 'StatusBadge'

export default StatusBadge
