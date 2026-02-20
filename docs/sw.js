// ===============================
// 1. Nazwy cache
// ===============================
const STATIC_CACHE = "static-v1";
const DYNAMIC_CACHE = "dynamic-v1";

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
// 3. TTL dla danych (5 minut)
// ===============================
const TTL = 5 * 60 * 1000; // 5 min

// ===============================
// 4. Instalacja SW
// ===============================
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// ===============================
// 5. Aktywacja SW
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
// 6. Fetch handler
// ===============================
self.addEventListener("fetch", event => {
  const request = event.request;

  // Ignorujemy chrome-extension
  if (request.url.startsWith("chrome-extension")) return;

  // ===============================
  // A. API: data.json → Network-first + TTL
  // ===============================
  if (request.url.includes("data.json")) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // ===============================
  // B. HTML → Network-first
  // ===============================
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

  // ===============================
  // C. Assety → Cache-first
  // ===============================
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

// ===============================
// 7. Funkcja obsługi API z TTL
// ===============================
async function handleApiRequest(request) {
  const cache = await caches.open(DYNAMIC_CACHE);

  // Odczytaj metadane (timestamp)
  const meta = await cache.match(request.url + ":meta");

  if (meta) {
    const { timestamp } = await meta.json();
    const age = Date.now() - timestamp;

    // Jeśli dane są świeże → użyj cache
    if (age < TTL) {
      const cached = await cache.match(request);
      if (cached) return cached;
    }
  }

  // Network-first
  try {
    const networkResponse = await fetch(request);

    // Zapisz dane
    cache.put(request, networkResponse.clone());
    cache.put(
      request.url + ":meta",
      new Response(JSON.stringify({ timestamp: Date.now() }))
    );

    return networkResponse;
  } catch (err) {
    // Offline → fallback do cache
    const cached = await cache.match(request);
    if (cached) return cached;

    return new Response("{}", { status: 200 });
  }
}
