import { type HTMLAttributes, type ReactNode } from 'react'
import clsx from 'clsx'
import './EmptyState.css'

export interface EmptyStateProps extends HTMLAttributes<HTMLDivElement> {
  title: string
  description?: ReactNode
  icon?: ReactNode
  actions?: ReactNode
}

export function EmptyState({
  title,
  description,
  icon,
  actions,
  className,
  children,
  ...props
}: EmptyStateProps) {
  return (
    <div className={clsx('ds-empty-state', className)} {...props}>
      {icon && <div className="ds-empty-state__icon">{icon}</div>}
      <h3 className="ds-empty-state__title">{title}</h3>
      {description && <p className="ds-empty-state__description">{description}</p>}
      {children && <div className="ds-empty-state__body">{children}</div>}
      {actions && <div className="ds-empty-state__actions">{actions}</div>}
    </div>
  )
}

export default EmptyState
