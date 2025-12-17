/**
 * React Context for tenant branding
 */

import { createContext } from 'react'
import type { BrandingContextType, TenantBranding } from './types'
import { DEFAULT_BRANDING } from './types'

/**
 * Default context value
 */
const defaultContextValue: BrandingContextType = {
  branding: DEFAULT_BRANDING,
  isLoading: false,
  error: null,
  updateBranding: async () => {
    console.warn('BrandingProvider not found. Wrap your app with <BrandingProvider>.')
  },
  resetBranding: () => {
    console.warn('BrandingProvider not found.')
  },
  applyBranding: () => {
    console.warn('BrandingProvider not found.')
  },
}

/**
 * Branding Context
 */
export const BrandingContext = createContext<BrandingContextType>(defaultContextValue)

/**
 * Generate CSS variables from branding colors
 */
export function generateCssVariables(branding: TenantBranding, isDark = false): string {
  const colors =
    isDark && branding.darkColors ? { ...branding.colors, ...branding.darkColors } : branding.colors

  return `
    :root {
      --brand-primary: ${colors.primary};
      --brand-primary-hover: ${colors.primaryHover};
      --brand-primary-foreground: ${colors.primaryForeground};
      --brand-secondary: ${colors.secondary};
      --brand-secondary-hover: ${colors.secondaryHover};
      --brand-secondary-foreground: ${colors.secondaryForeground};
      --brand-accent: ${colors.accent};
      --brand-background: ${colors.background};
      --brand-foreground: ${colors.foreground};
      --brand-muted: ${colors.muted};
      --brand-muted-foreground: ${colors.mutedForeground};
      --brand-border: ${colors.border};
      --brand-success: ${colors.success};
      --brand-warning: ${colors.warning};
      --brand-error: ${colors.error};
      --brand-info: ${colors.info};
      --brand-font-family: ${branding.typography.fontFamily};
      --brand-heading-font-family: ${branding.typography.headingFontFamily || branding.typography.fontFamily};
      --brand-mono-font-family: ${branding.typography.monoFontFamily};
    }
  `.trim()
}

/**
 * Apply branding to document
 */
export function applyBrandingToDocument(branding: TenantBranding, isDark = false): void {
  // Create or update style element
  let styleEl = document.getElementById('tenant-branding-styles')
  if (!styleEl) {
    styleEl = document.createElement('style')
    styleEl.id = 'tenant-branding-styles'
    document.head.appendChild(styleEl)
  }

  // Generate and apply CSS variables
  const cssVariables = generateCssVariables(branding, isDark)
  styleEl.textContent = cssVariables + (branding.customCss || '')

  // Update document title
  document.title = branding.metadata.name

  // Update meta description
  let metaDesc = document.querySelector('meta[name="description"]')
  if (!metaDesc) {
    metaDesc = document.createElement('meta')
    metaDesc.setAttribute('name', 'description')
    document.head.appendChild(metaDesc)
  }
  metaDesc.setAttribute('content', branding.metadata.description)

  // Update favicon if custom
  if (branding.features.favicon) {
    let favicon = document.querySelector('link[rel="icon"]') as HTMLLinkElement
    if (!favicon) {
      favicon = document.createElement('link')
      favicon.rel = 'icon'
      document.head.appendChild(favicon)
    }
    favicon.href = branding.features.favicon
  }
}

/**
 * Remove branding from document
 */
export function removeBrandingFromDocument(): void {
  const styleEl = document.getElementById('tenant-branding-styles')
  if (styleEl) {
    styleEl.remove()
  }
}

/**
 * Get tenant ID from current URL
 */
export function getTenantFromUrl(): string | null {
  if (typeof window === 'undefined') return null

  const hostname = window.location.hostname

  // Check for subdomain pattern: {tenant}.example.com
  const parts = hostname.split('.')
  if (parts.length >= 3) {
    const subdomain = parts[0]
    // Exclude common non-tenant subdomains
    if (!['www', 'app', 'api', 'docs', 'admin'].includes(subdomain)) {
      return subdomain
    }
  }

  // Check for query parameter: ?tenant=xxx
  const urlParams = new URLSearchParams(window.location.search)
  const tenantParam = urlParams.get('tenant')
  if (tenantParam) {
    return tenantParam
  }

  return null
}
