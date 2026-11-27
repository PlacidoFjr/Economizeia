const CACHE = 'economizeia-offline-v1'
const OFFLINE = '/offline.html'
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll([OFFLINE, '/icons/app-192.png'])).then(() => self.skipWaiting()))
})
self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith('economizeia-offline-') && key !== CACHE).map(key => caches.delete(key))
  )).then(() => self.clients.claim()))
})
self.addEventListener('fetch', (event) => {
  const request = event.request
  const url = new URL(request.url)
  if (url.origin === self.location.origin && url.pathname === '/icons/app-192.png' && request.method === 'GET') {
    event.respondWith(caches.match(request).then(response => response || fetch(request)))
    return
  }
  if (request.method !== 'GET' || request.mode !== 'navigate' ||
      url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return
  event.respondWith(fetch(request).catch(async () => {
    const response = await caches.match(OFFLINE)
    return response || new Response('Sem conexão. Reconecte e tente novamente.', {
      status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    })
  }))
})

