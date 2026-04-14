const CACHE_NAME = "mundialenvivo-v2";
const ASSETS = [
  "./index.html",
  "./manifest.json",
  "https://cdn.jsdelivr.net/npm/hls.js@latest",
  "https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js",
  "https://www.gstatic.com/firebasejs/8.10.0/firebase-database.js",
];

// Instalar — cachear assets principales
self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
      .catch(() => {}) // No fallar si algún asset externo no carga
  );
  self.skipWaiting();
});

// Activar — limpiar caches viejos
self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// Fetch — cache first para assets propios, network first para el resto
self.addEventListener("fetch", e => {
  const url = e.request.url;

  // No interceptar streams, Firebase, YouTube
  if (
    url.includes("firebasedatabase") ||
    url.includes("firebaseio.com") ||
    url.includes(".m3u8") ||
    url.includes(".ts") ||
    url.includes("youtube") ||
    url.includes("nocookie") ||
    url.includes("googleapis")
  ) {
    return;
  }

  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request)
        .then(response => {
          // Cachear respuestas exitosas de assets propiosjjjj
          if (response.ok && url.includes(self.location.origin)) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
          }
          return response;
        })        
        .catch(() => caches.match("./index.html"));
    })
  );
});