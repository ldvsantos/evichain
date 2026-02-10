/* EviChain Service Worker (cache básico para PWA)
   - Cacheia assets estáticos (HTML/CSS/JS/manifest/icon)
   - Network-first para navegação (sempre tenta atualizar)
*/

const CACHE_VERSION = 'evichain-v2';

const CORE_ASSETS = [
  './',
  './index.html',
  './dashboard.html',
  './investigador.html',
  './nova-denuncia.html',
  './styles.css',
  './home.css',
  './dashboard.css',
  './script.js',
  './home.js',
  './dashboard.js',
  './manifest.json',
  './icon.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(CORE_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

function isSameOrigin(requestUrl) {
  try {
    const url = new URL(requestUrl);
    return url.origin === self.location.origin;
  } catch {
    return false;
  }
}

self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Só cacheia GET do mesmo host
  if (request.method !== 'GET' || !isSameOrigin(request.url)) {
    return;
  }

  const url = new URL(request.url);

  // Não cachear chamadas API (deixa sempre na rede)
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  const isNavigation = request.mode === 'navigate';

  if (isNavigation) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(async () => {
          const cache = await caches.open(CACHE_VERSION);
          return (
            (await cache.match(request)) ||
            (await cache.match('/index.html')) ||
            (await cache.match('/'))
          );
        })
    );
    return;
  }

  // Assets: cache-first com fallback para rede
  event.respondWith(
    caches.match(request).then((cached) =>
      cached ||
      fetch(request).then((response) => {
        const copy = response.clone();
        caches.open(CACHE_VERSION).then((cache) => cache.put(request, copy));
        return response;
      })
    )
  );
});
