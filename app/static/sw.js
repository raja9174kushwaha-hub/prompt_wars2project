/**
 * ElectionGuide AI – Service Worker
 * Cache-first for static assets, network-first for API calls.
 */

const CACHE_NAME  = 'electionguide-v1';
const STATIC_URLS = [
  '/',
  '/static/styles.css',
  '/static/app.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_URLS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Network-first for API
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => new Response(
        JSON.stringify({ error: 'Offline – please reconnect.' }),
        { headers: { 'Content-Type': 'application/json' }, status: 503 }
      ))
    );
    return;
  }

  // Cache-first for static assets
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
});
