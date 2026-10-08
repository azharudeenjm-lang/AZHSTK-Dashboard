"""Small helper for NSE's website data service (www.nseindia.com/api/...).

NSE wants browser-like headers and the cookies its home page sets. The
session is warmed up once, re-warmed after a refusal, and every call is
best-effort: on failure it returns None and the caller uses its cache.
"""
import time

import requests

HEAD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"}
BASE = "https://www.nseindia.com"


class NSE:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(HEAD)
        self.ok = None          # None = not tried, False = NSE refused this server
        self.fails = 0
        self._warm()

    def _warm(self):
        for path in ("/", "/market-data/live-equity-market"):
            try:
                self.s.get(BASE + path, timeout=15)
            except Exception:
                pass

    def get(self, path, params=None, referer=None, tries=2):
        if self.fails >= 8:                     # NSE is blocking us: stop wasting time
            return None
        for k in range(tries):
            try:
                h = {"Referer": BASE + referer} if referer else None
                r = self.s.get(BASE + path, params=params, headers=h, timeout=25)
                if r.status_code == 200 and r.content[:1] in (b"{", b"["):
                    self.fails, self.ok = 0, True
                    return r.json()
                if r.status_code in (401, 403):
                    self._warm()
            except Exception:
                pass
            time.sleep(1.5 * (k + 1))
        self.fails += 1
        if self.ok is None and self.fails >= 3:
            self.ok = False
        return None


def walk(o, key="symbol"):
    """Every dict inside a JSON answer that has `key` (NSE nests lists differently per API)."""
    out = []
    if isinstance(o, dict):
        if key in o:
            out.append(o)
        for v in o.values():
            if isinstance(v, (dict, list)):
                out += walk(v, key)
    elif isinstance(o, list):
        for v in o:
            out += walk(v, key)
    return out


def num(x):
    try:
        if isinstance(x, str):
            x = x.replace(",", "").strip()
            if x in ("", "-", "NA", "nil", "Nil"):
                return None
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None
