/**
 * Image Optimization Hook
 *
 * Provides lazy loading, WebP support detection, and responsive image utilities.
 */

import { useState, useEffect, useRef, useCallback } from 'react'

// ============================================================================
// Types
// ============================================================================

export interface ImageSource {
  src: string
  srcSet?: string
  sizes?: string
  type?: string
}

export interface OptimizedImageProps {
  src: string
  alt: string
  width?: number
  height?: number
  loading?: 'lazy' | 'eager'
  placeholder?: string
  onLoad?: () => void
  onError?: () => void
}

export interface UseImageOptimizationOptions {
  enableLazyLoading?: boolean
  enableWebP?: boolean
  rootMargin?: string
  threshold?: number
}

// ============================================================================
// WebP Support Detection
// ============================================================================

let webpSupportCache: boolean | null = null

export function checkWebPSupport(): Promise<boolean> {
  if (webpSupportCache !== null) {
    return Promise.resolve(webpSupportCache)
  }

  return new Promise(resolve => {
    const img = new Image()
    img.onload = () => {
      webpSupportCache = img.width > 0 && img.height > 0
      resolve(webpSupportCache)
    }
    img.onerror = () => {
      webpSupportCache = false
      resolve(false)
    }
    // Tiny WebP image
    img.src = 'data:image/webp;base64,UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA=='
  })
}

export function useWebPSupport(): boolean {
  const [supported, setSupported] = useState(webpSupportCache ?? false)

  useEffect(() => {
    checkWebPSupport().then(setSupported)
  }, [])

  return supported
}

// ============================================================================
// Lazy Loading Hook
// ============================================================================

export function useLazyLoad(options: UseImageOptimizationOptions = {}): {
  ref: React.RefObject<HTMLImageElement>
  isLoaded: boolean
  isInView: boolean
} {
  const { enableLazyLoading = true, rootMargin = '200px', threshold = 0.1 } = options

  const ref = useRef<HTMLImageElement>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const [isInView, setIsInView] = useState(!enableLazyLoading)

  useEffect(() => {
    if (!enableLazyLoading) {
      setIsInView(true)
      return
    }

    const element = ref.current
    if (!element) return

    // Use native lazy loading if available
    if ('loading' in HTMLImageElement.prototype) {
      element.loading = 'lazy'
      setIsInView(true)
      return
    }

    // Fallback to IntersectionObserver
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            setIsInView(true)
            observer.unobserve(entry.target)
          }
        })
      },
      { rootMargin, threshold }
    )

    observer.observe(element)

    return () => {
      observer.disconnect()
    }
  }, [enableLazyLoading, rootMargin, threshold])

  const handleLoad = useCallback(() => {
    setIsLoaded(true)
  }, [])

  useEffect(() => {
    const element = ref.current
    if (element && isInView) {
      element.addEventListener('load', handleLoad)
      return () => element.removeEventListener('load', handleLoad)
    }
  }, [isInView, handleLoad])

  return { ref, isLoaded, isInView }
}

// ============================================================================
// Responsive Image Utilities
// ============================================================================

export interface ResponsiveBreakpoint {
  width: number
  suffix?: string
}

const DEFAULT_BREAKPOINTS: ResponsiveBreakpoint[] = [
  { width: 320, suffix: '-sm' },
  { width: 640, suffix: '-md' },
  { width: 1024, suffix: '-lg' },
  { width: 1920, suffix: '-xl' },
]

export function generateSrcSet(
  baseSrc: string,
  breakpoints: ResponsiveBreakpoint[] = DEFAULT_BREAKPOINTS
): string {
  const extension = baseSrc.split('.').pop() || ''
  const basePath = baseSrc.replace(`.${extension}`, '')

  return breakpoints
    .map(({ width, suffix }) => {
      const src = suffix ? `${basePath}${suffix}.${extension}` : baseSrc
      return `${src} ${width}w`
    })
    .join(', ')
}

export function generateSizes(breakpoints: ResponsiveBreakpoint[] = DEFAULT_BREAKPOINTS): string {
  const sizes = breakpoints.slice(0, -1).map(({ width }) => `(max-width: ${width}px) ${width}px`)

  sizes.push(`${breakpoints[breakpoints.length - 1].width}px`)

  return sizes.join(', ')
}

// ============================================================================
// Image Optimization Hook
// ============================================================================

export interface UseOptimizedImageResult {
  src: string
  srcSet?: string
  sizes?: string
  isLoaded: boolean
  isInView: boolean
  ref: React.RefObject<HTMLImageElement>
  webpSupported: boolean
}

export function useOptimizedImage(
  originalSrc: string,
  options: UseImageOptimizationOptions = {}
): UseOptimizedImageResult {
  const { enableWebP = true, ...lazyOptions } = options

  const webpSupported = useWebPSupport()
  const { ref, isLoaded, isInView } = useLazyLoad(lazyOptions)

  // Convert to WebP if supported and enabled
  const src =
    enableWebP && webpSupported ? originalSrc.replace(/\.(jpg|jpeg|png)$/i, '.webp') : originalSrc

  // Generate responsive srcSet
  const srcSet = generateSrcSet(src)
  const sizes = generateSizes()

  return {
    src,
    srcSet,
    sizes,
    isLoaded,
    isInView,
    ref,
    webpSupported,
  }
}

// ============================================================================
// Placeholder Generation
// ============================================================================

export function generatePlaceholder(
  width: number,
  height: number,
  color: string = '#e5e7eb'
): string {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
      <rect width="100%" height="100%" fill="${color}"/>
    </svg>
  `
  return `data:image/svg+xml,${encodeURIComponent(svg.trim())}`
}

export function generateBlurPlaceholder(width: number = 10, height: number = 10): string {
  // Low-resolution placeholder
  return generatePlaceholder(width, height, '#f3f4f6')
}

// ============================================================================
// Preload Images
// ============================================================================

export function preloadImage(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve()
    img.onerror = reject
    img.src = src
  })
}

export function preloadImages(sources: string[]): Promise<void[]> {
  return Promise.all(sources.map(preloadImage))
}

// ============================================================================
// Default Export
// ============================================================================

export default useOptimizedImage
