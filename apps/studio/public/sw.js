/**
 * AGNO Platform Service Worker v5.0 ULTIMATE
 * 
 * Provides offline functionality and caching for PWA support.
 */

const CACHE_NAME = 'agno-v5.0.0';
const OFFLINE_URL = '/offline.html';

// Assets to cache immediately on install
const PRECACHE_ASSETS = [
  '/',
  '/dashboard',
  '/manifest.json',
  '/favicon.svg',
  '/icon-192.png',
  '/icon-512.png',
];

// Cache strategies
const CACHE_STRATEGIES = {
  // Cache first, then network (for static assets)
  cacheFirst: async (request) => {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    try {
      const networkResponse = await fetch(request);
      if (networkResponse.ok) {
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    } catch (error) {
      console.error('Cache first failed:', error);
      throw error;
    }
  },

  // Network first, then cache (for dynamic content)
  networkFirst: async (request) => {
    try {
      const networkResponse = await fetch(request);
      if (networkResponse.ok) {
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    } catch (error) {
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        return cachedResponse;
      }
      throw error;
    }
  },

  // Stale while revalidate (for frequently updated content)
  staleWhileRevalidate: async (request) => {
    const cachedResponse = await caches.match(request);
    const fetchPromise = fetch(request).then((networkResponse) => {
      if (networkResponse.ok) {
        const cache = caches.open(CACHE_NAME);
        cache.then((c) => c.put(request, networkResponse.clone()));
      }
      return networkResponse;
    });

    return cachedResponse || fetchPromise;
  },
};

// Install event - precache assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing AGNO Service Worker v5.0...');
  
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Precaching assets...');
      return cache.addAll(PRECACHE_ASSETS);
    })
  );
  
  // Activate immediately
  self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating AGNO Service Worker v5.0...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    })
  );
  
  // Claim all clients
  self.clients.claim();
});

// Fetch event - handle requests
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip API requests (let them go to network)
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // Skip external requests
  if (url.origin !== self.location.origin) {
    return;
  }

  // Determine caching strategy based on request type
  let strategy;
  
  if (url.pathname.match(/\.(js|css|woff2?|ttf|eot)$/)) {
    // Static assets - cache first
    strategy = CACHE_STRATEGIES.cacheFirst;
  } else if (url.pathname.match(/\.(png|jpg|jpeg|gif|svg|ico|webp)$/)) {
    // Images - cache first
    strategy = CACHE_STRATEGIES.cacheFirst;
  } else if (url.pathname.startsWith('/_next/')) {
    // Next.js assets - cache first
    strategy = CACHE_STRATEGIES.cacheFirst;
  } else {
    // HTML pages - network first (for fresh content)
    strategy = CACHE_STRATEGIES.networkFirst;
  }

  event.respondWith(
    strategy(request).catch(() => {
      // Return offline page for navigation requests
      if (request.mode === 'navigate') {
        return caches.match(OFFLINE_URL);
      }
      throw new Error('Network error');
    })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'sync-pending-actions') {
    event.waitUntil(syncPendingActions());
  }
});

async function syncPendingActions() {
  // Get pending actions from IndexedDB
  // Sync with server when online
  console.log('[SW] Syncing pending actions...');
}

// Push notifications
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/dashboard',
    },
    actions: [
      { action: 'open', title: 'Abrir' },
      { action: 'close', title: 'Fechar' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'AGNO Platform', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'open' || !event.action) {
    const url = event.notification.data?.url || '/dashboard';
    event.waitUntil(
      self.clients.matchAll({ type: 'window' }).then((clients) => {
        // Focus existing window or open new
        for (const client of clients) {
          if (client.url === url && 'focus' in client) {
            return client.focus();
          }
        }
        if (self.clients.openWindow) {
          return self.clients.openWindow(url);
        }
      })
    );
  }
});

console.log('[SW] AGNO Service Worker v5.0 loaded');
