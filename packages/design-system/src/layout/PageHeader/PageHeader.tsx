import { type HTMLAttributes, type ReactNode } from 'react'
import clsx from 'clsx'
import './PageHeader.css'

export interface PageHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title: string
  description?: ReactNode
  icon?: ReactNode
  actions?: ReactNode
}

export function PageHeader({
  title,
  description,
  icon,
  actions,
  className,
  children,
  ...props
}: PageHeaderProps) {
  return (
    <div className={clsx('ds-page-header', className)} {...props}>
      <div className="ds-page-header__main">
        {icon && <div className="ds-page-header__icon">{icon}</div>}
        <div className="ds-page-header__text">
          <h1 className="ds-page-header__title">{title}</h1>
          {description && <p className="ds-page-header__description">{description}</p>}
          {children}
        </div>
      </div>
      {actions && <div className="ds-page-header__actions">{actions}</div>}
    </div>
  )
}

export default PageHeader
