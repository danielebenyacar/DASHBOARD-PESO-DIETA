// Incrementa CACHE a ogni modifica di index.html o degli asset, cosi' l'app si aggiorna.
const CACHE = "diario-peso-beta-v1.21";
// Il database dei prodotti (prodotti-it-*.txt) e' grande e cambia di rado: sta in una cache sua, che non si svuota a ogni versione.
const DBCACHE = "diario-peso-beta-prodotti";
const ASSETS = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith("diario-peso-beta-") && k !== CACHE && k !== DBCACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Network-first per le risorse dell'app (cosi' vedi subito gli aggiornamenti), cache come fallback offline.
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  // Database dei prodotti: prima la cache (il nome del file cambia a ogni aggiornamento), e tiene solo l'ultimo file.
  if (/\/prodotti-[^/]*\.txt$/.test(url.pathname)) {
    e.respondWith(
      caches.open(DBCACHE).then((c) =>
        c.match(req).then((hit) => hit || fetch(req).then((res) => {
          if (res.ok) {
            const copy = res.clone();
            c.keys().then((ks) => Promise.all(ks.filter((k) => k.url !== req.url).map((k) => c.delete(k)))).then(() => c.put(req, copy));
          }
          return res;
        }))
      )
    );
    return;
  }
  e.respondWith(
    fetch(req)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
        return res;
      })
      .catch(() => caches.match(req).then((r) => r || caches.match("./index.html")))
  );
});
