// ===============================
// 1. Nazwy cache
// ===============================
const STATIC_CACHE = "static-v1";
const DYNAMIC_CACHE = "dynamic-v1";

// ===============================
// 2. Pliki do pre-cache (działają offline)
// ===============================
const STATIC_ASSETS = [
  "./",
  "./index.html",
  "./style.css",
  "./manifest.json",
  "./offline.html",
  "./icons/icon-192.png",
  "./icons/icon-512.png"
];

// ===============================
// 3. Instalacja SW → pre-cache
// ===============================
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// ===============================
// 4. Aktywacja SW → czyszczenie starych cache
// ===============================
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys
          .filter(key => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
          .map(key => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// ===============================
// 5. Fetch → strategie cache
// ===============================
self.addEventListener("fetch", event => {
  const request = event.request;

  // Nie cache'ujemy zapytań do chrome-extension itp.
  if (request.url.startsWith("chrome-extension")) return;

  // Strategia: Network First dla HTML
  if (request.headers.get("accept")?.includes("text/html")) {
    event.respondWith(
      fetch(request)
        .then(response => {
          const cloned = response.clone();
          caches.open(DYNAMIC_CACHE).then(cache => cache.put(request, cloned));
          return response;
        })
        .catch(() => {
          return caches.match(request).then(res => res || caches.match("./offline.html"));
        })
    );
    return;
  }

  // Strategia: Cache First dla reszty (CSS, JS, IMG)
  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached;

      return fetch(request)
        .then(response => {
          const cloned = response.clone();
          caches.open(DYNAMIC_CACHE).then(cache => cache.put(request, cloned));
          return response;
        })
        .catch(() => {
          // fallback dla obrazków
          if (request.destination === "image") {
            return caches.match("./icons/icon-192.png");
          }
        });
    })
  );
});
