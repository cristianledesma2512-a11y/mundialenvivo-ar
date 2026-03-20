const CACHE = "mundialenvivo-v1";
const ASSETS = [
  "./index.html",
  "./manifest.json",
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", e => {
  // Solo cachear assets propios, no streams ni Firebase
  if (e.request.url.includes("firebasedatabase") ||
      e.request.url.includes(".m3u8") ||
      e.request.url.includes(".ts")) {
    return;
  }
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
