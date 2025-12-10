import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from './StatusBadge'
import { Check } from 'lucide-react'

describe('StatusBadge', () => {
  it('renders children correctly', () => {
    render(<StatusBadge>Test Badge</StatusBadge>)
    expect(screen.getByText('Test Badge')).toBeInTheDocument()
  })

  it('applies success variant styles', () => {
    render(<StatusBadge variant="success">Success</StatusBadge>)
    const badge = screen.getByText('Success').closest('.ds-status-badge')
    expect(badge).toHaveClass('ds-status-badge--success')
  })

  it('applies warning variant styles', () => {
    render(<StatusBadge variant="warning">Warning</StatusBadge>)
    const badge = screen.getByText('Warning').closest('.ds-status-badge')
    expect(badge).toHaveClass('ds-status-badge--warning')
  })

  it('applies error variant styles', () => {
    render(<StatusBadge variant="error">Error</StatusBadge>)
    const badge = screen.getByText('Error').closest('.ds-status-badge')
    expect(badge).toHaveClass('ds-status-badge--error')
  })

  it('applies info variant styles', () => {
    render(<StatusBadge variant="info">Info</StatusBadge>)
    const badge = screen.getByText('Info').closest('.ds-status-badge')
    expect(badge).toHaveClass('ds-status-badge--info')
  })

  it('applies pending variant styles', () => {
    render(<StatusBadge variant="pending">Pending</StatusBadge>)
    const badge = screen.getByText('Pending').closest('.ds-status-badge')
    expect(badge).toHaveClass('ds-status-badge--pending')
  })

  it('renders with small size', () => {
    render(<StatusBadge size="sm">Small</StatusBadge>)
    const badge = screen.getByText('Small').closest('.ds-status-badge')
    expect(badge).toHaveClass('ds-status-badge--sm')
  })

  it('renders with medium size by default', () => {
    render(<StatusBadge>Default</StatusBadge>)
    const badge = screen.getByText('Default').closest('.ds-status-badge')
    expect(badge).toHaveClass('ds-status-badge--md')
  })

  it('renders with icon', () => {
    render(
      <StatusBadge icon={<Check data-testid="icon" size={12} />}>
        With Icon
      </StatusBadge>
    )
    expect(screen.getByTestId('icon')).toBeInTheDocument()
    expect(screen.getByText('With Icon')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<StatusBadge className="custom-class">Custom</StatusBadge>)
    const badge = screen.getByText('Custom').closest('.ds-status-badge')
    expect(badge).toHaveClass('custom-class')
  })
})
