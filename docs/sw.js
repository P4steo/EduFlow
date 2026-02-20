// ===============================
// 1. Nazwy cache
// ===============================
const STATIC_CACHE = "static-v2";
const DYNAMIC_CACHE = "dynamic-v2";

// ===============================
// 2. Pliki statyczne (offline)
// ===============================
const STATIC_ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./offline.html",
  "./icons/icon-192.png",
  "./icons/icon-512.png"
];

// ===============================
// 3. Instalacja SW
// ===============================
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// ===============================
// 4. Aktywacja SW
// ===============================
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
          .map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// ===============================
// 5. Fetch handler
// ===============================
self.addEventListener("fetch", event => {
  const request = event.request;

  if (request.url.startsWith("chrome-extension")) return;

  // HTML → network-first
  if (request.headers.get("accept")?.includes("text/html")) {
    event.respondWith(
      fetch(request)
        .then(response => {
          const cloned = response.clone();
          caches.open(DYNAMIC_CACHE).then(cache => cache.put(request, cloned));
          return response;
        })
        .catch(() =>
          caches.match(request).then(res => res || caches.match("./offline.html"))
        )
    );
    return;
  }

  // Assety → cache-first
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
          if (request.destination === "image") {
            return caches.match("./icons/icon-192.png");
          }
        });
    })
  );
});
