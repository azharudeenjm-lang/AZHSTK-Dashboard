"""Home-screen app files: manifest, icons and a small offline helper.

The service worker shows the latest loaded pages and data when there is no
signal, and always fetches fresh data first when online.
"""
import json

from .config import DOCS

MANIFEST = {
    "name": "AZH Stock Dashboard", "short_name": "AZH Stocks",
    "start_url": "setups.html", "scope": "./", "display": "standalone",
    "background_color": "#EEF2F6", "theme_color": "#16243A",
    "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
}

SW = r"""// Network first; fall back to the last copy when offline.
const CACHE = "azh-v2";
self.addEventListener("install", e => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  // "no-cache" makes the browser check with the server for a newer copy every time
  e.respondWith(fetch(req, {cache: "no-cache"}).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return res;
  }).catch(() => caches.match(req)));
});
"""


def _icon(size):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (size, size), "#16243A")
    d = ImageDraw.Draw(img)
    s = size / 512
    # three rising bars in the zone colours, plus a trend line
    for i, (col, h) in enumerate((("#2F62C8", 150), ("#1E8F5A", 230), ("#13857A", 320))):
        x0 = int((118 + i * 102) * s)
        d.rounded_rectangle([x0, int((400 - h) * s), x0 + int(70 * s), int(400 * s)], radius=int(10 * s), fill=col)
    d.line([(int(100 * s), int(330 * s)), (int(260 * s), int(230 * s)), (int(410 * s), int(110 * s))],
           fill="#FFFFFF", width=max(2, int(18 * s)), joint="curve")
    return img


def write():
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "manifest.webmanifest").write_text(json.dumps(MANIFEST, indent=1), encoding="utf-8")
    (DOCS / "sw.js").write_text(SW, encoding="utf-8")
    try:
        for n in (192, 512):
            _icon(n).save(DOCS / f"icon-{n}.png")
    except Exception as e:   # Pillow missing: the app still works, just without a custom icon
        print(f"  icons skipped: {e}")
