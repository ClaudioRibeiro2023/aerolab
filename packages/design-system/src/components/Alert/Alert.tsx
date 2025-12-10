import { forwardRef, type HTMLAttributes, type ReactNode } from 'react'
import clsx from 'clsx'
import './Alert.css'

export type AlertVariant = 'info' | 'success' | 'warning' | 'error'

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  /** Variante visual do alerta */
  variant?: AlertVariant
  /** Título do alerta */
  title?: string
  /** Descrição principal */
  description?: ReactNode
  /** Ícone opcional à esquerda */
  icon?: ReactNode
  /** Ações à direita (botões, links) */
  actions?: ReactNode
}

export const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ variant = 'info', title, description, icon, actions, className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx('ds-alert', `ds-alert--${variant}`, className)}
        role="alert"
        {...props}
      >
        {icon && <div className="ds-alert__icon">{icon}</div>}

        <div className="ds-alert__content">
          {title && <h3 className="ds-alert__title">{title}</h3>}
          {description && <p className="ds-alert__description">{description}</p>}
          {children && <div className="ds-alert__body">{children}</div>}
        </div>

        {actions && <div className="ds-alert__actions">{actions}</div>}
      </div>
    )
  }
)

Alert.displayName = 'Alert'

export default Alert
