const SW_VERSION = "v4.0.2";
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

// INSTALL — natychmiastowa aktywacja nowej wersji
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// ACTIVATE — czyszczenie starych cache + przejęcie kontroli
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    )
  );

  self.clients.claim();
});

// FETCH — cache-first dla plików lokalnych
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);

  // Nie przechwytujemy API ani zewnętrznych domen
  if (url.origin !== location.origin) return;

  event.respondWith(
    caches.match(event.request).then(cached => {
      return (
        cached ||
        fetch(event.request).then(response => {
          return response;
        })
      );
    })
  );
});

// ODBIERANIE KOMEND (np. wymuszenie reloadu)
self.addEventListener("message", event => {
  if (event.data === "force-reload") {
    self.clients.matchAll().then(clients => {
      clients.forEach(client => client.navigate(client.url));
    });
  }
});


