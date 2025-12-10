import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EmptyState } from './EmptyState'
import { FileX } from 'lucide-react'

describe('EmptyState', () => {
  it('renders title correctly', () => {
    render(<EmptyState title="No items found" />)
    expect(screen.getByText('No items found')).toBeInTheDocument()
  })

  it('renders title and description', () => {
    render(
      <EmptyState
        title="Empty List"
        description="There are no items to display"
      />
    )
    expect(screen.getByText('Empty List')).toBeInTheDocument()
    expect(screen.getByText('There are no items to display')).toBeInTheDocument()
  })

  it('renders with icon', () => {
    render(
      <EmptyState
        title="With Icon"
        icon={<FileX data-testid="empty-icon" size={24} />}
      />
    )
    expect(screen.getByTestId('empty-icon')).toBeInTheDocument()
  })

  it('renders actions', () => {
    render(
      <EmptyState
        title="With Actions"
        actions={<button data-testid="add-btn">Add Item</button>}
      />
    )
    expect(screen.getByTestId('add-btn')).toBeInTheDocument()
  })

  it('renders children content', () => {
    render(
      <EmptyState title="With Children">
        <div data-testid="custom-content">Custom content</div>
      </EmptyState>
    )
    expect(screen.getByTestId('custom-content')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<EmptyState title="Custom" className="custom-empty" />)
    const container = screen.getByText('Custom').closest('.ds-empty-state')
    expect(container).toHaveClass('custom-empty')
  })

  it('renders title as heading', () => {
    render(<EmptyState title="Heading Test" />)
    expect(screen.getByText('Heading Test')).toBeInTheDocument()
  })
})
