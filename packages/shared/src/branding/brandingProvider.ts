/**
 * React Provider for tenant branding
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import {
  BrandingContext,
  applyBrandingToDocument,
  removeBrandingFromDocument,
  getTenantFromUrl,
} from './brandingContext'
import type { TenantBranding, BrandingContextType } from './types'
import { DEFAULT_BRANDING } from './types'

export interface BrandingProviderProps {
  children: React.ReactNode
  /** Initial branding to use */
  initialBranding?: TenantBranding
  /** Function to fetch branding for a tenant */
  fetchBranding?: (tenantId: string) => Promise<TenantBranding>
  /** Tenant ID (if not auto-detected from URL) */
  tenantId?: string
  /** Whether to auto-apply branding to document */
  autoApply?: boolean
  /** Whether dark mode is enabled */
  isDarkMode?: boolean
  /** Storage key for persisting branding */
  storageKey?: string
}

const STORAGE_KEY = 'tenant-branding'

/**
 * Load branding from localStorage
 */
function loadBrandingFromStorage(key: string): TenantBranding | null {
  if (typeof window === 'undefined') return null

  try {
    const stored = localStorage.getItem(key)
    if (stored) {
      return JSON.parse(stored) as TenantBranding
    }
  } catch {
    // Ignore parse errors
  }
  return null
}

/**
 * Save branding to localStorage
 */
function saveBrandingToStorage(key: string, branding: TenantBranding): void {
  if (typeof window === 'undefined') return

  try {
    localStorage.setItem(key, JSON.stringify(branding))
  } catch {
    // Ignore storage errors
  }
}

/**
 * Branding Provider Component
 */
export function BrandingProvider({
  children,
  initialBranding,
  fetchBranding,
  tenantId: propTenantId,
  autoApply = true,
  isDarkMode = false,
  storageKey = STORAGE_KEY,
}: BrandingProviderProps): React.ReactElement {
  const [branding, setBranding] = useState<TenantBranding>(
    initialBranding || loadBrandingFromStorage(storageKey) || DEFAULT_BRANDING
  )
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  // Determine tenant ID
  const tenantId = propTenantId || getTenantFromUrl() || 'default'

  // Fetch branding on mount or when tenant changes
  useEffect(() => {
    if (!fetchBranding || tenantId === 'default') return

    let cancelled = false

    const loadBranding = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const fetchedBranding = await fetchBranding(tenantId)
        if (!cancelled) {
          setBranding(fetchedBranding)
          saveBrandingToStorage(storageKey, fetchedBranding)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Failed to fetch branding'))
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadBranding()

    return () => {
      cancelled = true
    }
  }, [tenantId, fetchBranding, storageKey])

  // Apply branding to document when it changes
  useEffect(() => {
    if (autoApply) {
      applyBrandingToDocument(branding, isDarkMode)
    }

    return () => {
      if (autoApply) {
        removeBrandingFromDocument()
      }
    }
  }, [branding, isDarkMode, autoApply])

  // Update branding
  const updateBranding = useCallback(
    async (updates: Partial<TenantBranding>) => {
      const newBranding = { ...branding, ...updates, updatedAt: new Date().toISOString() }
      setBranding(newBranding)
      saveBrandingToStorage(storageKey, newBranding)
    },
    [branding, storageKey]
  )

  // Reset to default branding
  const resetBranding = useCallback(() => {
    setBranding(DEFAULT_BRANDING)
    localStorage.removeItem(storageKey)
  }, [storageKey])

  // Manually apply branding
  const applyBranding = useCallback(() => {
    applyBrandingToDocument(branding, isDarkMode)
  }, [branding, isDarkMode])

  // Context value
  const contextValue: BrandingContextType = useMemo(
    () => ({
      branding,
      isLoading,
      error,
      updateBranding,
      resetBranding,
      applyBranding,
    }),
    [branding, isLoading, error, updateBranding, resetBranding, applyBranding]
  )

  return React.createElement(BrandingContext.Provider, { value: contextValue }, children)
}

/**
 * HOC to wrap a component with branding provider
 */
export function withBranding<P extends object>(
  Component: React.ComponentType<P>,
  providerProps?: Omit<BrandingProviderProps, 'children'>
): React.FC<P> {
  const WrappedComponent: React.FC<P> = props => {
    const fullProviderProps: BrandingProviderProps = {
      ...providerProps,
      children: React.createElement(Component, props),
    }
    return React.createElement(BrandingProvider, fullProviderProps)
  }

  WrappedComponent.displayName = `withBranding(${Component.displayName || Component.name || 'Component'})`

  return WrappedComponent
}
