const CACHE_NAME = 'atom-cache-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  'https://cdn.tailwindcss.com'
];

// Install Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

// Cache and return requests
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});