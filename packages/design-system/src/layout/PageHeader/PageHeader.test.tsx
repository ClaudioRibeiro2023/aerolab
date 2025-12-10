import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PageHeader } from './PageHeader'
import { Database } from 'lucide-react'

describe('PageHeader', () => {
  it('renders title correctly', () => {
    render(<PageHeader title="Test Page" />)
    expect(screen.getByText('Test Page')).toBeInTheDocument()
  })

  it('renders title and description', () => {
    render(
      <PageHeader
        title="Page Title"
        description="Page description text"
      />
    )
    expect(screen.getByText('Page Title')).toBeInTheDocument()
    expect(screen.getByText('Page description text')).toBeInTheDocument()
  })

  it('renders with icon', () => {
    render(
      <PageHeader
        title="With Icon"
        icon={<Database data-testid="header-icon" size={28} />}
      />
    )
    expect(screen.getByTestId('header-icon')).toBeInTheDocument()
  })

  it('renders actions', () => {
    render(
      <PageHeader
        title="With Actions"
        actions={<button data-testid="action-btn">Action</button>}
      />
    )
    expect(screen.getByTestId('action-btn')).toBeInTheDocument()
  })

  it('renders children content', () => {
    render(
      <PageHeader title="With Children">
        <div data-testid="child-content">Child content</div>
      </PageHeader>
    )
    expect(screen.getByTestId('child-content')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<PageHeader title="Custom" className="custom-header" />)
    const header = screen.getByText('Custom').closest('.ds-page-header')
    expect(header).toHaveClass('custom-header')
  })

  it('renders title as heading', () => {
    render(<PageHeader title="Heading Test" />)
    expect(screen.getByText('Heading Test')).toBeInTheDocument()
  })
})
