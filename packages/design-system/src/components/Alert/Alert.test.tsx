import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Alert } from './Alert'
import { Info } from 'lucide-react'

describe('Alert', () => {
  it('renders title and description', () => {
    render(
      <Alert
        title="Test Title"
        description="Test description"
      />
    )
    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByText('Test description')).toBeInTheDocument()
  })

  it('renders with info variant by default', () => {
    render(<Alert title="Info Alert" />)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('ds-alert--info')
  })

  it('applies success variant styles', () => {
    render(<Alert variant="success" title="Success" />)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('ds-alert--success')
  })

  it('applies warning variant styles', () => {
    render(<Alert variant="warning" title="Warning" />)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('ds-alert--warning')
  })

  it('applies error variant styles', () => {
    render(<Alert variant="error" title="Error" />)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('ds-alert--error')
  })

  it('renders with icon', () => {
    render(
      <Alert
        title="With Icon"
        icon={<Info data-testid="alert-icon" size={20} />}
      />
    )
    expect(screen.getByTestId('alert-icon')).toBeInTheDocument()
  })

  it('renders without title when only description is provided', () => {
    render(<Alert description="Only description" />)
    expect(screen.getByText('Only description')).toBeInTheDocument()
  })

  it('has alert role for accessibility', () => {
    render(<Alert title="Accessible Alert" />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<Alert title="Custom" className="custom-alert" />)
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('custom-alert')
  })
})
