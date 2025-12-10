import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FilterSelect } from './FilterSelect'

const mockOptions = [
  { value: 'opt1', label: 'Option 1' },
  { value: 'opt2', label: 'Option 2' },
  { value: 'opt3', label: 'Option 3' },
]

describe('FilterSelect', () => {
  it('renders with label', () => {
    render(
      <FilterSelect
        id="test-select"
        label="Test Label"
        options={mockOptions}
        value={null}
        onChange={vi.fn()}
        onClear={vi.fn()}
      />
    )
    expect(screen.getByText('Test Label')).toBeInTheDocument()
  })

  it('renders all options', () => {
    render(
      <FilterSelect
        id="test-select"
        label="Test Label"
        options={mockOptions}
        value={null}
        onChange={vi.fn()}
        onClear={vi.fn()}
      />
    )
    const select = screen.getByRole('combobox')
    expect(select).toBeInTheDocument()

    // Check options count (3 + placeholder)
    expect(select.querySelectorAll('option')).toHaveLength(4)
  })

  it('shows placeholder when no value selected', () => {
    render(
      <FilterSelect
        id="test-select"
        label="Test Label"
        placeholder="Select an option..."
        options={mockOptions}
        value={null}
        onChange={vi.fn()}
        onClear={vi.fn()}
      />
    )
    expect(screen.getByText('Select an option...')).toBeInTheDocument()
  })

  it('calls onChange when selecting an option', () => {
    const handleChange = vi.fn()
    render(
      <FilterSelect
        id="test-select"
        label="Test Label"
        options={mockOptions}
        value={null}
        onChange={handleChange}
        onClear={vi.fn()}
      />
    )

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'opt1' } })

    expect(handleChange).toHaveBeenCalledWith('opt1')
  })

  it('shows clear button when value is selected', () => {
    render(
      <FilterSelect
        id="test-select"
        label="Test Label"
        options={mockOptions}
        value="opt1"
        onChange={vi.fn()}
        onClear={vi.fn()}
      />
    )

    const clearButton = screen.getByTitle('Limpar')
    expect(clearButton).toBeInTheDocument()
  })

  it('does not show clear button when no value selected', () => {
    render(
      <FilterSelect
        id="test-select"
        label="Test Label"
        options={mockOptions}
        value={null}
        onChange={vi.fn()}
        onClear={vi.fn()}
      />
    )

    expect(screen.queryByTitle('Limpar')).not.toBeInTheDocument()
  })

  it('calls onClear when clicking clear button', () => {
    const handleClear = vi.fn()
    render(
      <FilterSelect
        id="test-select"
        label="Test Label"
        options={mockOptions}
        value="opt1"
        onChange={vi.fn()}
        onClear={handleClear}
      />
    )

    const clearButton = screen.getByTitle('Limpar')
    fireEvent.click(clearButton)

    expect(handleClear).toHaveBeenCalled()
  })

  it('uses design system CSS classes', () => {
    const { container } = render(
      <FilterSelect
        id="test-select"
        label="Test Label"
        options={mockOptions}
        value={null}
        onChange={vi.fn()}
        onClear={vi.fn()}
      />
    )

    expect(container.querySelector('.filter-item')).toBeInTheDocument()
    expect(container.querySelector('.filter-select')).toBeInTheDocument()
    expect(container.querySelector('.filter-item__label')).toBeInTheDocument()
    expect(container.querySelector('.filter-select__input')).toBeInTheDocument()
  })
})
