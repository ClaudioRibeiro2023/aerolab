/**
 * CDN Integration Utilities
 *
 * Provides utilities for CDN asset management, cache control, and URL generation.
 */

// ============================================================================
// Configuration
// ============================================================================

const CDN_CONFIG = {
  enabled: import.meta.env.VITE_CDN_ENABLED === 'true',
  baseUrl: import.meta.env.VITE_CDN_URL || '',
  cacheVersion: import.meta.env.VITE_CDN_CACHE_VERSION || 'v1',
  defaultTTL: 31536000, // 1 year in seconds
}

// ============================================================================
// Types
// ============================================================================

export interface CDNAsset {
  path: string
  url: string
  cacheControl: string
}

export interface CacheConfig {
  maxAge?: number
  sMaxAge?: number
  staleWhileRevalidate?: number
  immutable?: boolean
  public?: boolean
}

// ============================================================================
// URL Generation
// ============================================================================

/**
 * Get the CDN URL for an asset.
 * Falls back to local path if CDN is disabled.
 */
export function getCDNUrl(path: string): string {
  if (!CDN_CONFIG.enabled || !CDN_CONFIG.baseUrl) {
    return path
  }

  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`

  // Add cache version for cache busting
  const separator = normalizedPath.includes('?') ? '&' : '?'
  const versionedPath = `${normalizedPath}${separator}v=${CDN_CONFIG.cacheVersion}`

  return `${CDN_CONFIG.baseUrl}${versionedPath}`
}

/**
 * Get CDN URL for an image with optional transformations.
 */
export function getCDNImageUrl(
  path: string,
  options?: {
    width?: number
    height?: number
    quality?: number
    format?: 'auto' | 'webp' | 'avif' | 'jpg' | 'png'
  }
): string {
  const baseUrl = getCDNUrl(path)

  if (!options || !CDN_CONFIG.enabled) {
    return baseUrl
  }

  // Build transformation params (compatible with Cloudflare/CloudFront)
  const params = new URLSearchParams()

  if (options.width) params.set('w', options.width.toString())
  if (options.height) params.set('h', options.height.toString())
  if (options.quality) params.set('q', options.quality.toString())
  if (options.format) params.set('f', options.format)

  const separator = baseUrl.includes('?') ? '&' : '?'
  return `${baseUrl}${separator}${params.toString()}`
}

// ============================================================================
// Cache Control
// ============================================================================

/**
 * Generate cache control header value.
 */
export function generateCacheControl(config: CacheConfig): string {
  const directives: string[] = []

  if (config.public !== false) {
    directives.push('public')
  }

  if (config.maxAge !== undefined) {
    directives.push(`max-age=${config.maxAge}`)
  }

  if (config.sMaxAge !== undefined) {
    directives.push(`s-maxage=${config.sMaxAge}`)
  }

  if (config.staleWhileRevalidate !== undefined) {
    directives.push(`stale-while-revalidate=${config.staleWhileRevalidate}`)
  }

  if (config.immutable) {
    directives.push('immutable')
  }

  return directives.join(', ')
}

/**
 * Predefined cache configurations for common asset types.
 */
export const CACHE_PRESETS = {
  // Static assets (JS, CSS) - long cache with immutable
  static: generateCacheControl({
    maxAge: 31536000, // 1 year
    sMaxAge: 31536000,
    immutable: true,
  }),

  // Images - long cache
  images: generateCacheControl({
    maxAge: 2592000, // 30 days
    sMaxAge: 31536000, // 1 year on CDN
    staleWhileRevalidate: 86400, // 1 day
  }),

  // HTML pages - short cache with revalidation
  html: generateCacheControl({
    maxAge: 0,
    sMaxAge: 3600, // 1 hour on CDN
    staleWhileRevalidate: 86400, // 1 day
  }),

  // API responses - no cache by default
  api: 'no-cache, no-store, must-revalidate',

  // Dynamic content - short cache
  dynamic: generateCacheControl({
    maxAge: 60, // 1 minute
    sMaxAge: 300, // 5 minutes on CDN
    staleWhileRevalidate: 3600, // 1 hour
  }),
}

// ============================================================================
// Preload / Prefetch
// ============================================================================

/**
 * Preload critical assets.
 */
export function preloadAsset(
  url: string,
  as: 'script' | 'style' | 'image' | 'font' | 'fetch',
  crossOrigin?: 'anonymous' | 'use-credentials'
): void {
  const link = document.createElement('link')
  link.rel = 'preload'
  link.href = getCDNUrl(url)
  link.as = as

  if (crossOrigin) {
    link.crossOrigin = crossOrigin
  }

  // Font preloading requires crossorigin
  if (as === 'font' && !crossOrigin) {
    link.crossOrigin = 'anonymous'
  }

  document.head.appendChild(link)
}

/**
 * Prefetch assets for future navigation.
 */
export function prefetchAsset(url: string): void {
  const link = document.createElement('link')
  link.rel = 'prefetch'
  link.href = getCDNUrl(url)
  document.head.appendChild(link)
}

/**
 * Preconnect to CDN origin.
 */
export function preconnectToCDN(): void {
  if (!CDN_CONFIG.enabled || !CDN_CONFIG.baseUrl) {
    return
  }

  const link = document.createElement('link')
  link.rel = 'preconnect'
  link.href = new URL(CDN_CONFIG.baseUrl).origin
  link.crossOrigin = 'anonymous'
  document.head.appendChild(link)
}

// ============================================================================
// Service Worker Cache Integration
// ============================================================================

/**
 * Cache strategy hints for service worker.
 */
export const CACHE_STRATEGIES = {
  // Cache first, then network
  cacheFirst: ['fonts', 'images/icons'],

  // Network first, cache fallback
  networkFirst: ['api', 'data'],

  // Stale while revalidate
  staleWhileRevalidate: ['images', 'scripts', 'styles'],

  // Network only
  networkOnly: ['auth', 'analytics'],
}

/**
 * Get cache strategy for a URL.
 */
export function getCacheStrategy(url: string): keyof typeof CACHE_STRATEGIES | null {
  for (const [strategy, patterns] of Object.entries(CACHE_STRATEGIES)) {
    if (patterns.some(pattern => url.includes(pattern))) {
      return strategy as keyof typeof CACHE_STRATEGIES
    }
  }
  return null
}

// ============================================================================
// Exports
// ============================================================================

export const cdn = {
  getUrl: getCDNUrl,
  getImageUrl: getCDNImageUrl,
  preload: preloadAsset,
  prefetch: prefetchAsset,
  preconnect: preconnectToCDN,
  cacheControl: generateCacheControl,
  presets: CACHE_PRESETS,
  config: CDN_CONFIG,
}

export default cdn
