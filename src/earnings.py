"""Upcoming results dates from NSE's event calendar (best effort).

NSE sometimes blocks cloud servers. When that happens the last good list
(kept in the cache) is used, and if there is none, earnings warnings are
simply left out rather than guessed.
"""
import json
from datetime import datetime, timedelta

import requests

from .config import CACHE

URLS = ["https://www.nseindia.com/api/event-calendar"]
HEAD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar"}
PATH = CACHE / "earnings.json"


def _parse(rows):
    out = {}
    today = datetime.now().date()
    for r in rows or []:
        sym = (r.get("symbol") or "").strip()
        purpose = f"{r.get('purpose', '')} {r.get('bm_desc', '')}".lower()
        if not sym or not any(k in purpose for k in ("result", "financial")):
            continue
        try:
            d = datetime.strptime(r.get("date", ""), "%d-%b-%Y").date()
        except ValueError:
            continue
        if d >= today - timedelta(days=1) and (sym not in out or d.isoformat() < out[sym]):
            out[sym] = d.isoformat()
    return out


def fetch():
    """Returns {symbol: 'YYYY-MM-DD'} of the next results date, or {}."""
    try:
        s = requests.Session()
        s.headers.update(HEAD)
        s.get("https://www.nseindia.com/", timeout=20)
        for url in URLS:
            r = s.get(url, timeout=30)
            if r.ok and r.text.strip().startswith("["):
                data = _parse(r.json())
                if data:
                    CACHE.mkdir(parents=True, exist_ok=True)
                    PATH.write_text(json.dumps({"fetched": datetime.now().isoformat(), "dates": data}))
                    print(f"  earnings: {len(data)} upcoming results dates")
                    return data
        print(f"  earnings: NSE answered {r.status_code}; using cache if any")
    except Exception as e:
        print(f"  earnings: {str(e)[:80]}; using cache if any")
    if PATH.exists():
        cached = json.loads(PATH.read_text())
        today = datetime.now().date().isoformat()
        return {k: v for k, v in cached.get("dates", {}).items() if v >= today}
    return {}
