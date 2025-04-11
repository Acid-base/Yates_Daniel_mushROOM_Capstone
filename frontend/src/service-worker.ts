// Service Worker for mushROOM PWA

// Cache names
const CACHE_NAME = 'mushroom-app-v1';
const DATA_CACHE_NAME = 'mushroom-data-v1';

// Resources to pre-cache
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/src/main.tsx',
  '/src/App.tsx',
  '/src/App.css',
  '/src/index.css',
  '/src/theme.ts',
  '/src/queryClient.ts',
  '/public/vite.svg',
  // Add other static assets here
];

// Install event - cache static assets
self.addEventListener('install', (event: any) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  // @ts-ignore
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event: any) => {
  const cacheWhitelist = [CACHE_NAME, DATA_CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (!cacheWhitelist.includes(cacheName)) {
            return caches.delete(cacheName);
          }
          return null;
        })
      );
    })
  );
  // @ts-ignore
  self.clients.claim();
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event: any) => {
  // API calls - network first, then cache
  if (event.request.url.includes('/api/') || event.request.url.includes('data.mongodb-api.com')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.status === 200) {
            const responseToCache = response.clone();
            caches.open(DATA_CACHE_NAME).then((cache) => {
              cache.put(event.request, responseToCache);
            });
          }
          return response;
        })
        .catch(() => {
          return caches.match(event.request);
        })
    );
    return;
  }

  // Static assets - cache first, then network
  event.respondWith(
    caches.match(event.request).then((response) => {
      return (
        response ||
        fetch(event.request)
          .then(async (fetchResponse) => {
            const cache = await caches.open(CACHE_NAME);
            cache.put(event.request, fetchResponse.clone());
            return fetchResponse;
          })
          .catch((error) => {
            console.error('Fetch error:', error);
            // You could return a custom offline page here
          })
      );
    })
  );
});

// Handle background sync for offline operations
self.addEventListener('sync', (event: any) => {
  if (event.tag === 'sync-mushroom-data') {
    event.waitUntil(syncMushroomData());
  }
});

// Function to sync data when online
async function syncMushroomData() {
  // Implement data synchronization logic here
  // This will depend on your specific requirements
}
