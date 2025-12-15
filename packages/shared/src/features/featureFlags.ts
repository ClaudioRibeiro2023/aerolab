/**
 * Feature Flags System
 *
 * Provides feature flag management with environment-based configuration.
 * Supports dev/staging/prod environments with different flag values.
 */

// ============================================================================
// Types
// ============================================================================

export type Environment = 'development' | 'staging' | 'production'

export interface FeatureFlagConfig {
  /** Flag identifier */
  id: string
  /** Human-readable name */
  name: string
  /** Description of what the flag controls */
  description: string
  /** Default value if not configured */
  defaultValue: boolean
  /** Environment-specific overrides */
  environments?: Partial<Record<Environment, boolean>>
  /** Optional metadata */
  metadata?: Record<string, unknown>
}

export interface FeatureFlagsState {
  flags: Record<string, boolean>
  environment: Environment
  initialized: boolean
}

// ============================================================================
// Environment Detection
// ============================================================================

export function detectEnvironment(): Environment {
  // Check for explicit environment variable
  let envVar: string | undefined

  if (typeof window !== 'undefined') {
    // Browser environment
    envVar = (window as unknown as { __ENV__?: string }).__ENV__
  } else if (typeof globalThis !== 'undefined' && 'process' in globalThis) {
    // Node.js environment
    envVar = (globalThis as unknown as { process: { env: { NODE_ENV?: string } } }).process.env
      .NODE_ENV
  }

  if (envVar === 'production') return 'production'
  if (envVar === 'staging') return 'staging'

  // Check for common staging indicators
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname
    if (hostname.includes('staging') || hostname.includes('stg')) {
      return 'staging'
    }
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'development'
    }
  }

  return 'development'
}

// ============================================================================
// Default Feature Flags Configuration
// ============================================================================

export const DEFAULT_FEATURE_FLAGS: FeatureFlagConfig[] = [
  {
    id: 'dark_mode',
    name: 'Dark Mode',
    description: 'Enable dark mode theme toggle',
    defaultValue: true,
  },
  {
    id: 'new_dashboard',
    name: 'New Dashboard',
    description: 'Enable redesigned dashboard layout',
    defaultValue: false,
    environments: {
      development: true,
      staging: true,
      production: false,
    },
  },
  {
    id: 'experimental_features',
    name: 'Experimental Features',
    description: 'Enable experimental/beta features',
    defaultValue: false,
    environments: {
      development: true,
      staging: false,
      production: false,
    },
  },
  {
    id: 'analytics',
    name: 'Analytics',
    description: 'Enable analytics and tracking',
    defaultValue: true,
    environments: {
      development: false,
      staging: true,
      production: true,
    },
  },
  {
    id: 'maintenance_mode',
    name: 'Maintenance Mode',
    description: 'Show maintenance page to users',
    defaultValue: false,
  },
]

// ============================================================================
// Feature Flags Manager
// ============================================================================

class FeatureFlagsManager {
  private flags: Map<string, boolean> = new Map()
  private configs: Map<string, FeatureFlagConfig> = new Map()
  private environment: Environment
  private initialized = false
  private listeners: Set<() => void> = new Set()

  constructor() {
    this.environment = detectEnvironment()
  }

  /**
   * Initialize feature flags with configuration
   */
  initialize(configs: FeatureFlagConfig[] = DEFAULT_FEATURE_FLAGS): void {
    this.configs.clear()
    this.flags.clear()

    for (const config of configs) {
      this.configs.set(config.id, config)

      // Determine flag value based on environment
      const envValue = config.environments?.[this.environment]
      const value = envValue !== undefined ? envValue : config.defaultValue

      this.flags.set(config.id, value)
    }

    this.initialized = true
    this.notifyListeners()
  }

  /**
   * Check if a feature flag is enabled
   */
  isEnabled(flagId: string): boolean {
    if (!this.initialized) {
      console.warn(`[FeatureFlags] Not initialized. Call initialize() first.`)
      return false
    }

    const value = this.flags.get(flagId)
    if (value === undefined) {
      console.warn(`[FeatureFlags] Unknown flag: ${flagId}`)
      return false
    }

    return value
  }

  /**
   * Override a flag value (useful for testing or admin overrides)
   */
  setFlag(flagId: string, value: boolean): void {
    if (!this.configs.has(flagId)) {
      console.warn(`[FeatureFlags] Cannot set unknown flag: ${flagId}`)
      return
    }

    this.flags.set(flagId, value)
    this.notifyListeners()
  }

  /**
   * Reset a flag to its default value
   */
  resetFlag(flagId: string): void {
    const config = this.configs.get(flagId)
    if (!config) {
      console.warn(`[FeatureFlags] Cannot reset unknown flag: ${flagId}`)
      return
    }

    const envValue = config.environments?.[this.environment]
    const value = envValue !== undefined ? envValue : config.defaultValue
    this.flags.set(flagId, value)
    this.notifyListeners()
  }

  /**
   * Get all flags and their current values
   */
  getAllFlags(): Record<string, boolean> {
    return Object.fromEntries(this.flags)
  }

  /**
   * Get all flag configurations
   */
  getAllConfigs(): FeatureFlagConfig[] {
    return Array.from(this.configs.values())
  }

  /**
   * Get current environment
   */
  getEnvironment(): Environment {
    return this.environment
  }

  /**
   * Set environment (useful for testing)
   */
  setEnvironment(env: Environment): void {
    this.environment = env
    // Re-initialize with new environment
    if (this.initialized) {
      this.initialize(Array.from(this.configs.values()))
    }
  }

  /**
   * Subscribe to flag changes
   */
  subscribe(listener: () => void): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener())
  }
}

// Singleton instance
export const featureFlags = new FeatureFlagsManager()

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if a feature is enabled (shorthand)
 */
export function isFeatureEnabled(flagId: string): boolean {
  return featureFlags.isEnabled(flagId)
}

/**
 * Initialize feature flags (call at app startup)
 */
export function initializeFeatureFlags(configs?: FeatureFlagConfig[]): void {
  featureFlags.initialize(configs)
}

// ============================================================================
// React Hook
// ============================================================================

import { useState, useEffect, useCallback } from 'react'

/**
 * React hook to check if a feature flag is enabled
 * Automatically re-renders when the flag value changes
 */
export function useFeatureFlag(flagId: string): boolean {
  const [enabled, setEnabled] = useState(() => featureFlags.isEnabled(flagId))

  useEffect(() => {
    // Update state when flags change
    const unsubscribe = featureFlags.subscribe(() => {
      setEnabled(featureFlags.isEnabled(flagId))
    })

    // Ensure we have the latest value
    setEnabled(featureFlags.isEnabled(flagId))

    return unsubscribe
  }, [flagId])

  return enabled
}

/**
 * React hook to get all feature flags
 */
export function useFeatureFlags(): {
  flags: Record<string, boolean>
  isEnabled: (flagId: string) => boolean
  setFlag: (flagId: string, value: boolean) => void
  resetFlag: (flagId: string) => void
  environment: Environment
} {
  const [, forceUpdate] = useState({})

  useEffect(() => {
    const unsubscribe = featureFlags.subscribe(() => {
      forceUpdate({})
    })
    return unsubscribe
  }, [])

  const isEnabled = useCallback((flagId: string) => {
    return featureFlags.isEnabled(flagId)
  }, [])

  const setFlag = useCallback((flagId: string, value: boolean) => {
    featureFlags.setFlag(flagId, value)
  }, [])

  const resetFlag = useCallback((flagId: string) => {
    featureFlags.resetFlag(flagId)
  }, [])

  return {
    flags: featureFlags.getAllFlags(),
    isEnabled,
    setFlag,
    resetFlag,
    environment: featureFlags.getEnvironment(),
  }
}

// Auto-initialize with defaults
if (typeof window !== 'undefined') {
  featureFlags.initialize()
}
