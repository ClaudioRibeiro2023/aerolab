/**
 * Types for tenant branding system
 */

export interface BrandingColors {
  /** Primary brand color (buttons, links, accents) */
  primary: string
  /** Primary hover state */
  primaryHover: string
  /** Primary foreground (text on primary background) */
  primaryForeground: string
  /** Secondary brand color */
  secondary: string
  /** Secondary hover state */
  secondaryHover: string
  /** Secondary foreground */
  secondaryForeground: string
  /** Accent color for highlights */
  accent: string
  /** Background color */
  background: string
  /** Foreground/text color */
  foreground: string
  /** Muted background */
  muted: string
  /** Muted foreground */
  mutedForeground: string
  /** Border color */
  border: string
  /** Success color */
  success: string
  /** Warning color */
  warning: string
  /** Error/danger color */
  error: string
  /** Info color */
  info: string
}

export interface BrandingTypography {
  /** Primary font family */
  fontFamily: string
  /** Heading font family (optional, defaults to fontFamily) */
  headingFontFamily?: string
  /** Monospace font family */
  monoFontFamily?: string
}

export interface BrandingLogo {
  /** Full logo URL (for header, login page) */
  full: string
  /** Icon/favicon URL (for small spaces) */
  icon: string
  /** Logo alt text */
  alt: string
  /** Logo width in pixels (optional) */
  width?: number
  /** Logo height in pixels (optional) */
  height?: number
}

export interface BrandingMetadata {
  /** Application/tenant name */
  name: string
  /** Short name (for mobile, tabs) */
  shortName: string
  /** Description for SEO */
  description: string
  /** Keywords for SEO */
  keywords?: string[]
  /** Copyright text */
  copyright?: string
  /** Support email */
  supportEmail?: string
  /** Support URL */
  supportUrl?: string
}

export interface BrandingDomain {
  /** Primary domain */
  primary: string
  /** Subdomains (e.g., ['app', 'api', 'docs']) */
  subdomains?: string[]
  /** Custom domains allowed */
  customDomains?: string[]
}

export interface BrandingFeatures {
  /** Show powered by footer */
  showPoweredBy: boolean
  /** Allow dark mode toggle */
  allowDarkMode: boolean
  /** Show language selector */
  showLanguageSelector: boolean
  /** Custom login background */
  customLoginBackground?: string
  /** Custom favicon */
  favicon?: string
}

export interface TenantBranding {
  /** Unique tenant identifier */
  tenantId: string
  /** Color scheme */
  colors: BrandingColors
  /** Dark mode colors (optional) */
  darkColors?: Partial<BrandingColors>
  /** Typography settings */
  typography: BrandingTypography
  /** Logo configuration */
  logo: BrandingLogo
  /** Metadata (name, description, etc.) */
  metadata: BrandingMetadata
  /** Domain configuration */
  domain?: BrandingDomain
  /** Feature flags for branding */
  features: BrandingFeatures
  /** Custom CSS to inject */
  customCss?: string
  /** Last updated timestamp */
  updatedAt?: string
}

export interface BrandingContextType {
  /** Current branding configuration */
  branding: TenantBranding
  /** Whether branding is loading */
  isLoading: boolean
  /** Error if branding failed to load */
  error: Error | null
  /** Update branding (for admin) */
  updateBranding: (updates: Partial<TenantBranding>) => Promise<void>
  /** Reset to default branding */
  resetBranding: () => void
  /** Apply branding to document */
  applyBranding: () => void
}

/** Default branding configuration */
export const DEFAULT_BRANDING: TenantBranding = {
  tenantId: 'default',
  colors: {
    primary: '#4F46E5',
    primaryHover: '#4338CA',
    primaryForeground: '#FFFFFF',
    secondary: '#6B7280',
    secondaryHover: '#4B5563',
    secondaryForeground: '#FFFFFF',
    accent: '#8B5CF6',
    background: '#FFFFFF',
    foreground: '#1F2937',
    muted: '#F3F4F6',
    mutedForeground: '#6B7280',
    border: '#E5E7EB',
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
  },
  typography: {
    fontFamily: 'Inter, system-ui, sans-serif',
    headingFontFamily: 'Inter, system-ui, sans-serif',
    monoFontFamily: 'JetBrains Mono, monospace',
  },
  logo: {
    full: '/logo.svg',
    icon: '/icon.svg',
    alt: 'Template Platform',
  },
  metadata: {
    name: 'Template Platform',
    shortName: 'Template',
    description: 'Enterprise-ready template platform',
    copyright: '© 2024 Template Platform. All rights reserved.',
  },
  features: {
    showPoweredBy: true,
    allowDarkMode: true,
    showLanguageSelector: false,
  },
}
