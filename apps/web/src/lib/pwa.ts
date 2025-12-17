/**
 * Progressive Web App (PWA) Configuration
 * 
 * Para habilitar PWA completo:
 * 1. Instalar: pnpm --filter @template/web add -D vite-plugin-pwa
 * 2. Configurar em vite.config.ts
 * 3. Criar manifest.json e icons
 */
/* eslint-disable no-console */

/**
 * Configuração do manifest.json para PWA
 */
export const pwaManifest = {
  name: 'AeroLab',
  short_name: 'AeroLab',
  description: 'AeroLab - Plataforma Corporativa',
  theme_color: '#3b82f6',
  background_color: '#ffffff',
  display: 'standalone' as const,
  scope: '/',
  start_url: '/',
  orientation: 'portrait' as const,
  icons: [
    {
      src: '/icons/icon-72x72.png',
      sizes: '72x72',
      type: 'image/png',
      purpose: 'maskable any',
    },
    {
      src: '/icons/icon-96x96.png',
      sizes: '96x96',
      type: 'image/png',
      purpose: 'maskable any',
    },
    {
      src: '/icons/icon-128x128.png',
      sizes: '128x128',
      type: 'image/png',
      purpose: 'maskable any',
    },
    {
      src: '/icons/icon-144x144.png',
      sizes: '144x144',
      type: 'image/png',
      purpose: 'maskable any',
    },
    {
      src: '/icons/icon-152x152.png',
      sizes: '152x152',
      type: 'image/png',
      purpose: 'maskable any',
    },
    {
      src: '/icons/icon-192x192.png',
      sizes: '192x192',
      type: 'image/png',
      purpose: 'maskable any',
    },
    {
      src: '/icons/icon-384x384.png',
      sizes: '384x384',
      type: 'image/png',
      purpose: 'maskable any',
    },
    {
      src: '/icons/icon-512x512.png',
      sizes: '512x512',
      type: 'image/png',
      purpose: 'maskable any',
    },
  ],
  categories: ['business', 'productivity'],
  shortcuts: [
    {
      name: 'Perfil',
      short_name: 'Perfil',
      description: 'Acessar meu perfil',
      url: '/profile',
      icons: [{ src: '/icons/profile-96x96.png', sizes: '96x96' }],
    },
    {
      name: 'Configurações',
      short_name: 'Config',
      description: 'Configurações do sistema',
      url: '/admin/config',
      icons: [{ src: '/icons/settings-96x96.png', sizes: '96x96' }],
    },
  ],
}

/**
 * Configuração do Vite PWA Plugin
 * 
 * Adicionar em vite.config.ts:
 * ```ts
 * import { VitePWA } from 'vite-plugin-pwa'
 * import { vitePwaConfig } from './src/lib/pwa'
 * 
 * export default defineConfig({
 *   plugins: [react(), VitePWA(vitePwaConfig)],
 * })
 * ```
 */
export const vitePwaConfig = {
  registerType: 'autoUpdate' as const,
  includeAssets: ['favicon.ico', 'robots.txt', 'icons/*.png'],
  manifest: pwaManifest,
  workbox: {
    // Cache de assets estáticos
    globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
    
    // Cache de API responses
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/api\..*/i,
        handler: 'NetworkFirst' as const,
        options: {
          cacheName: 'api-cache',
          expiration: {
            maxEntries: 100,
            maxAgeSeconds: 60 * 60 * 24, // 24 horas
          },
          cacheableResponse: {
            statuses: [0, 200],
          },
        },
      },
      {
        urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
        handler: 'CacheFirst' as const,
        options: {
          cacheName: 'google-fonts-cache',
          expiration: {
            maxEntries: 10,
            maxAgeSeconds: 60 * 60 * 24 * 365, // 1 ano
          },
          cacheableResponse: {
            statuses: [0, 200],
          },
        },
      },
    ],
  },
  devOptions: {
    enabled: true,
    type: 'module',
  },
}

/**
 * Verifica se o app está rodando como PWA
 */
export function isPWA(): boolean {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    // @ts-expect-error - Safari specific
    window.navigator.standalone === true
  )
}

/**
 * Verifica se PWA pode ser instalado
 */
export function canInstallPWA(): boolean {
  return 'BeforeInstallPromptEvent' in window
}

/**
 * Hook state para controlar instalação PWA
 */
export interface PWAInstallState {
  canInstall: boolean
  isInstalled: boolean
  prompt: (() => Promise<void>) | null
}

/**
 * Registra service worker manualmente (se não usar vite-plugin-pwa)
 */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      })
      
      console.info('[PWA] Service Worker registrado:', registration.scope)
      return registration
    } catch (error) {
      console.error('[PWA] Erro ao registrar Service Worker:', error)
      return null
    }
  }
  
  console.warn('[PWA] Service Workers não suportados')
  return null
}

/**
 * Verifica se há atualização disponível
 */
export async function checkForUpdates(): Promise<boolean> {
  if ('serviceWorker' in navigator) {
    const registration = await navigator.serviceWorker.ready
    await registration.update()
    return registration.waiting !== null
  }
  return false
}

/**
 * Força atualização do Service Worker
 */
export async function forceUpdate(): Promise<void> {
  if ('serviceWorker' in navigator) {
    const registration = await navigator.serviceWorker.ready
    
    if (registration.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' })
      window.location.reload()
    }
  }
}
