import type { ExampleItem } from '../types'
import { StatusBadge } from '@template/design-system'

interface ExampleCardProps {
  item: ExampleItem
  onClick?: (item: ExampleItem) => void
}

export function ExampleCard({ item, onClick }: ExampleCardProps) {
  const variantByStatus: Record<ExampleItem['status'], 'success' | 'warning' | 'info' | 'pending'> =
    {
      active: 'success',
      inactive: 'pending',
      pending: 'warning',
    }

  return (
    <div
      className="bg-surface-elevated rounded-xl p-6 border border-border-default hover:border-brand-primary transition-colors cursor-pointer hover-lift"
      onClick={() => onClick?.(item)}
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-semibold text-text-primary">{item.title}</h3>
        <StatusBadge variant={variantByStatus[item.status]} size="sm">
          {item.status}
        </StatusBadge>
      </div>
      <p className="text-text-secondary text-sm mb-3">{item.description}</p>
      <p className="text-text-muted text-xs">
        Criado em: {new Date(item.createdAt).toLocaleDateString('pt-BR')}
      </p>
    </div>
  )
}
