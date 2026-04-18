const SW_VERSION = "v4.2.1";
const CACHE_NAME = `static-${SW_VERSION}`;

const STATIC_ASSETS = [
  "./",
  "./index.html",
  "./style.css",
  "./script.js",
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./data_offline.json"
];

/* ============================================================
   INSTALL — pobranie plików + natychmiastowe przejście dalej
   ============================================================ */
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );

  // iOS ignoruje to czasem, ale musi tu być
  self.skipWaiting();
});

/* ============================================================
   ACTIVATE — czyszczenie starych cache + przejęcie kontroli
   ============================================================ */
self.addEventListener("activate", event => {
  event.waitUntil(
    (async () => {
      // usuń wszystkie stare cache
      const keys = await caches.keys();
      await Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );

      // przejmij kontrolę nad wszystkimi klientami
      await self.clients.claim();

      // powiadom frontend o nowej wersji
      const clients = await self.clients.matchAll({ type: "window" });
      for (const client of clients) {
        client.postMessage({
          type: "NEW_VERSION_AVAILABLE",
          version: SW_VERSION
        });
      }
    })()
  );
});

/* ============================================================
   FETCH — network-first dla CSS/JS (iOS fix)
   ============================================================ */
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);

  // nie przechwytujemy zewnętrznych domen
  if (url.origin !== location.origin) return;

  const isCSS = event.request.destination === "style";
  const isJS = event.request.destination === "script";

  // iOS fix: CSS/JS zawsze z sieci (fallback do cache)
  if (isCSS || isJS) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // reszta: cache-first
  event.respondWith(
    caches.match(event.request).then(cached => {
      return cached || fetch(event.request);
    })
  );
});

/* ============================================================
   MESSAGE — obsługa SKIP_WAITING i force reload
   ============================================================ */
self.addEventListener("message", event => {
  // wymuszenie aktywacji nowego SW
  if (event.data?.type === "SKIP_WAITING") {
    self.skipWaiting();
  }

  // wymuszenie reloadu wszystkich klientów
  if (event.data === "force-reload") {
    self.clients.matchAll().then(clients => {
      clients.forEach(client => client.navigate(client.url));
    });
  }
});
