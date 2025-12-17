/**
 * React hook for accessing tenant branding
 */

import { useContext, useMemo } from 'react'
import { BrandingContext } from './brandingContext'
import type { TenantBranding, BrandingColors } from './types'

/**
 * Hook to access branding context
 */
export function useBranding() {
  const context = useContext(BrandingContext)
  return context
}

/**
 * Hook to get specific branding colors
 */
export function useBrandingColors(): BrandingColors {
  const { branding } = useBranding()
  return branding.colors
}

/**
 * Hook to get branding metadata
 */
export function useBrandingMetadata() {
  const { branding } = useBranding()
  return branding.metadata
}

/**
 * Hook to get branding logo
 */
export function useBrandingLogo() {
  const { branding } = useBranding()
  return branding.logo
}

/**
 * Hook to get branding features
 */
export function useBrandingFeatures() {
  const { branding } = useBranding()
  return branding.features
}

/**
 * Hook to generate inline styles from branding
 */
export function useBrandingStyles() {
  const { branding } = useBranding()

  return useMemo(
    () => ({
      primaryButton: {
        backgroundColor: branding.colors.primary,
        color: branding.colors.primaryForeground,
      },
      secondaryButton: {
        backgroundColor: branding.colors.secondary,
        color: branding.colors.secondaryForeground,
      },
      card: {
        backgroundColor: branding.colors.background,
        borderColor: branding.colors.border,
      },
      heading: {
        fontFamily: branding.typography.headingFontFamily || branding.typography.fontFamily,
        color: branding.colors.foreground,
      },
      text: {
        fontFamily: branding.typography.fontFamily,
        color: branding.colors.foreground,
      },
      mutedText: {
        fontFamily: branding.typography.fontFamily,
        color: branding.colors.mutedForeground,
      },
      link: {
        color: branding.colors.primary,
      },
    }),
    [branding]
  )
}

/**
 * Hook to check if a feature is enabled
 */
export function useBrandingFeature(feature: keyof TenantBranding['features']): boolean {
  const features = useBrandingFeatures()
  const value = features[feature]
  return typeof value === 'boolean' ? value : !!value
}
