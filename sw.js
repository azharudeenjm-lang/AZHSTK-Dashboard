// Network first; fall back to the last copy when offline.
const CACHE = "azh-v3";
self.addEventListener("install", e => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  // "no-cache" makes the browser check with the server for a newer copy every time
  e.respondWith(fetch(req, {cache: "no-cache"}).then(res => {
    // keep an offline copy of pages and small files only; the big screener data files and
    // zoom-out price files are skipped so the phone isn't rewriting megabytes every visit
    const big = /screener_ser_|\/px\/|levels_charts|screener\.json|trade_log/.test(req.url);
    if (res.ok && !big) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return res;
  }).catch(() => caches.match(req)));
});
