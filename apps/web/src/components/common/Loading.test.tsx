import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Loading, PageLoading } from './Loading'

describe('Loading', () => {
  it('renders spinner with default size', () => {
    render(<Loading />)
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
    expect(spinner).toHaveClass('w-8', 'h-8')
  })

  it('renders small spinner', () => {
    render(<Loading size="sm" />)
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toHaveClass('w-4', 'h-4')
  })

  it('renders large spinner', () => {
    render(<Loading size="lg" />)
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toHaveClass('w-12', 'h-12')
  })

  it('renders with text', () => {
    render(<Loading text="Carregando dados..." />)
    expect(screen.getByText('Carregando dados...')).toBeInTheDocument()
  })

  it('renders fullscreen variant', () => {
    render(<Loading fullScreen />)
    const overlay = document.querySelector('.fixed.inset-0')
    expect(overlay).toBeInTheDocument()
    expect(overlay).toHaveClass('bg-surface-base/80')
  })

  it('uses design system tokens for spinner', () => {
    render(<Loading />)
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toHaveClass('border-brand-primary')
  })
})

describe('PageLoading', () => {
  it('renders centered loading state', () => {
    render(<PageLoading />)
    const container = document.querySelector('.min-h-\\[50vh\\]')
    expect(container).toBeInTheDocument()
  })

  it('displays default loading text', () => {
    render(<PageLoading />)
    expect(screen.getByText('Carregando...')).toBeInTheDocument()
  })

  it('uses design system text color', () => {
    render(<PageLoading />)
    const text = screen.getByText('Carregando...')
    expect(text).toHaveClass('text-text-secondary')
  })
})
