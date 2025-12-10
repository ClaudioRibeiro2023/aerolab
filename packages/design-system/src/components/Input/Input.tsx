/**
 * Input Component
 * 
 * Componente de input reutilizável com suporte a labels, erros e ícones.
 */

import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react'
import clsx from 'clsx'
import './Input.css'

export type InputSize = 'sm' | 'md' | 'lg'

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** Label do input */
  label?: string
  /** Texto de ajuda */
  helperText?: string
  /** Mensagem de erro */
  error?: string
  /** Tamanho do input */
  size?: InputSize
  /** Ícone à esquerda */
  leftIcon?: ReactNode
  /** Ícone à direita */
  rightIcon?: ReactNode
  /** Ocupar largura total */
  fullWidth?: boolean
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      error,
      size = 'md',
      leftIcon,
      rightIcon,
      fullWidth = true,
      className,
      id,
      disabled,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`
    const hasError = !!error

    return (
      <div className={clsx('ds-input-wrapper', fullWidth && 'ds-input-wrapper--full', className)}>
        {label && (
          <label htmlFor={inputId} className="ds-input__label">
            {label}
          </label>
        )}
        
        <div className={clsx(
          'ds-input__container',
          `ds-input__container--${size}`,
          hasError && 'ds-input__container--error',
          disabled && 'ds-input__container--disabled'
        )}>
          {leftIcon && (
            <span className="ds-input__icon ds-input__icon--left">{leftIcon}</span>
          )}
          
          <input
            ref={ref}
            id={inputId}
            className="ds-input"
            disabled={disabled}
            aria-invalid={hasError ? 'true' : undefined}
            aria-describedby={
              error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
            }
            {...props}
          />
          
          {rightIcon && (
            <span className="ds-input__icon ds-input__icon--right">{rightIcon}</span>
          )}
        </div>
        
        {error && (
          <span id={`${inputId}-error`} className="ds-input__error" role="alert">
            {error}
          </span>
        )}
        
        {helperText && !error && (
          <span id={`${inputId}-helper`} className="ds-input__helper">
            {helperText}
          </span>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input
