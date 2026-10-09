"""Themes tab: structural investment themes, their stock baskets, performance and news history.

For every theme:
  * an equal-weight index of its stocks (daily, from the dashboard's 5 years of prices)
  * returns (1 week to 3 years), breadth (share of stocks above their 50-day average,
    share within 5% of a 52-week high)
  * rotation against NIFTY 50, like the sector chart:
        Leading    stronger than NIFTY and gaining
        Weakening  stronger than NIFTY but losing pace
        Lagging    weaker than NIFTY and losing
        Improving  weaker than NIFTY but gaining (the early-turn signal)
  * news: Google News results collected year by year from the theme's start
    (a few years per run until the history is complete) and then kept up to date daily.
"""
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

import numpy as np
import pandas as pd

from .config import CACHE, DOCS
from .themes_list import META, THEMES

IST = timezone(timedelta(hours=5, minutes=30))
NEWS_PATH = CACHE / "theme_news.json"
BACKFILL_PER_RUN = 40          # year-by-year history queries per run (gentle on Google News)


def load_themes(root=None):
    """themes.json in the repository root replaces the built-in list when present."""
    from pathlib import Path
    p = Path(root or ".") / "themes.json"
    try:
        if p.exists():
            t = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(t, list) and t:
                print(f"  themes: using themes.json ({len(t)} themes)")
                return t
    except Exception as e:
        print(f"  ! themes.json not used: {str(e)[:80]}")
    return THEMES


def _r(x, n=1):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


# ---------------------------------------------------------------- news
def _gn(query):
    from .news import _parse
    url = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
    return _parse(url, 100, query)


def update_news(themes, demo=False):
    """Returns {theme id: [items newest first]}; fills history a few years per run."""
    if demo:
        return _demo_news(themes)
    try:
        store = json.loads(NEWS_PATH.read_text(encoding="utf-8"))
    except Exception:
        store = {}
    now = datetime.now(IST)
    budget = BACKFILL_PER_RUN
    added = 0
    for th in themes:
        st = store.setdefault(th["id"], {"done": [], "items": []})
        seen = {x["t"].lower()[:90] for x in st["items"]}

        def add(items):
            nonlocal added
            for it in items:
                k = it["t"].lower()[:90]
                if it["t"] and k not in seen:
                    seen.add(k)
                    st["items"].append({"d": it["iso"], "t": it["t"], "u": it["u"], "s": it["s"]})
                    added += 1
        # history: one query per year from the start year, oldest first
        st["done"] = [k for k in st["done"] if not k.startswith("cy:") or k == f"cy:{now:%Y-%m-%d}"]
        for y in range(int(th.get("start", now.year)), now.year + 1):
            for qi, q in enumerate(th.get("q", [])[:2]):
                # past years once each; the current year once a day
                key = f"{y}:{qi}" if y < now.year else f"cy:{now:%Y-%m-%d}"
                if key in st["done"] or budget <= 0 or (y == now.year and qi > 0):
                    continue
                add(_gn(f"{q} after:{y}-01-01 before:{y + 1}-01-01"))
                st["done"].append(key)
                budget -= 1
                time.sleep(1)
        # latest week
        if th.get("q"):
            add(_gn(th["q"][0] + " when:7d"))
            time.sleep(1)
        st["items"] = sorted(st["items"], key=lambda x: x["d"], reverse=True)[:500]
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        NEWS_PATH.write_text(json.dumps(store), encoding="utf-8")
    except Exception:
        pass
    left = sum(1 for th in themes for y in range(int(th.get("start", now.year)), now.year)
               for qi in range(min(2, len(th.get("q", [])))) if f"{y}:{qi}" not in store.get(th["id"], {}).get("done", []))
    print(f"  theme news: {added} new headlines; {left} history searches still to do")
    return {k: v["items"] for k, v in store.items()}


def load_news():
    try:
        return {k: v["items"] for k, v in json.loads(NEWS_PATH.read_text(encoding="utf-8")).items()}
    except Exception:
        return {}


def _demo_news(themes):
    import random
    rnd = random.Random(2)
    out = {}
    for th in themes:
        items = []
        for y in range(int(th.get("start", 2020)), 2027):
            for k in range(rnd.randint(2, 5)):
                d = f"{y}-{rnd.randint(1, 12):02d}-{rnd.randint(1, 28):02d}"
                items.append({"d": d, "t": f"Demo headline about {th['name'].lower()} ({y})", "u": "https://news.google.com/", "s": "Demo"})
        out[th["id"]] = sorted(items, key=lambda x: x["d"], reverse=True)
    return out


# ---------------------------------------------------------------- build
def build(px, stocks, benchmark, themes=None, zones=None, buy_rec=None, tam_rows=None, news=None):
    """Returns (page payload, {sym: [theme chips]}, {ticker: screener conditions})."""
    themes = themes or THEMES
    info = {s["sym"]: s for s in stocks}
    C = px["Close"]
    H = px["High"]
    bench = C[benchmark].dropna() if benchmark in C.columns else None
    zones = zones or {}
    buy_rec = buy_rec or {}
    tam_syms = {r["sym"]: r for r in (tam_rows or [])}
    out, chips, sc = [], {}, {}
    for th in themes:
        syms = [s for s in dict.fromkeys(th.get("stocks", [])) if s in info and s + ".NS" in C.columns]
        if len(syms) < 2:
            continue
        cols = [s + ".NS" for s in syms]
        rets = C[cols].pct_change(fill_method=None).clip(-0.2, 0.2)
        ew = rets.mean(axis=1, skipna=True).fillna(0)
        idx = (1 + ew).cumprod() * 100
        first_valid = C[cols].notna().any(axis=1)
        idx = idx[first_valid.idxmax():] if first_valid.any() else idx

        def ret(days):
            if len(idx) <= days:
                return None
            return _r((idx.iloc[-1] / idx.iloc[-1 - days] - 1) * 100)
        state, rsv, mom = None, None, None
        curve, bcurve = [], []
        if bench is not None:
            b = bench.reindex(idx.index).ffill()
            ratio = idx / b
            rs = ratio / ratio.rolling(130, min_periods=60).mean()
            mo = rs / rs.shift(20)
            rsv, mom = rs.iloc[-1], mo.iloc[-1]
            if np.isfinite(rsv) and np.isfinite(mom):
                state = ("Leading" if mom > 1 else "Weakening") if rsv > 1 else ("Improving" if mom > 1 else "Lagging")
            wk = idx.resample("W-FRI").last().dropna()
            bw = b.resample("W-FRI").last().reindex(wk.index).ffill()
            base_b = bw.iloc[0] if len(bw) else 1
            curve = [[d.strftime("%Y-%m-%d"), _r(v, 2)] for d, v in wk.items()]
            bcurve = [[d.strftime("%Y-%m-%d"), _r(v / base_b * 100, 2)] for d, v in bw.items()]
            # rotation trail: last 8 weeks of (strength, momentum)
            rsw, mow = rs.resample("W-FRI").last(), mo.resample("W-FRI").last()
            trail = [[_r(a * 100, 2), _r(m * 100, 2)] for a, m in zip(rsw.iloc[-8:], mow.iloc[-8:]) if np.isfinite(a) and np.isfinite(m)]
        else:
            trail = []
        last = C[cols].ffill().iloc[-1]
        sma50 = C[cols].rolling(50, min_periods=40).mean().iloc[-1]
        hi52 = H[cols].rolling(250, min_periods=120).max().iloc[-1]
        above = float(np.nanmean((last > sma50).astype(float))) * 100
        near = float(np.nanmean((last >= hi52 * 0.95).astype(float))) * 100
        rows = []
        for s, t in zip(syms, cols):
            cs = C[t].dropna()
            if len(cs) < 2:
                continue
            g = lambda n: _r((cs.iloc[-1] / cs.iloc[-1 - n] - 1) * 100) if len(cs) > n else None
            zd, zw = (zones.get("d") or {}).get(t) or {}, (zones.get("w") or {}).get(t) or {}
            br = buy_rec.get(s) or {}
            rows.append({"sym": s, "name": info[s].get("name"), "px": _r(cs.iloc[-1], 2), "r1m": g(21), "r3m": g(63), "r1y": g(250),
                         "r3y": g(750), "hi": _r((cs.iloc[-1] / hi52[t] - 1) * 100) if np.isfinite(hi52[t]) else None,
                         "a50": bool(last[t] > sma50[t]) if np.isfinite(sma50[t]) else None,
                         "zw": zw.get("zone"), "zd": zd.get("zone"),
                         "buy": {"new": "new signal", "open": "open trade", "watch": "watch"}.get(br.get("st")),
                         "tam": bool(s in tam_syms)})
        rows.sort(key=lambda r: -(r["r3m"] if r["r3m"] is not None else -999))
        th_out = {"id": th["id"], "name": th["name"], "thesis": th.get("thesis"), "start": th.get("start"),
                  "timeline": th.get("timeline", []), "n": len(rows), "state": state,
                  "rs": _r(rsv * 100, 1) if rsv is not None and np.isfinite(rsv) else None,
                  "mom": _r(mom * 100, 1) if mom is not None and np.isfinite(mom) else None,
                  "r1w": ret(5), "r1m": ret(21), "r3m": ret(63), "r6m": ret(126), "r1y": ret(250), "r3y": ret(750),
                  "since": _r((idx.iloc[-1] / idx.iloc[0] - 1) * 100), "since_d": idx.index[0].strftime("%Y-%m-%d"),
                  "a50": _r(above, 0), "near": _r(near, 0), "trail": trail,
                  "buys": sum(1 for r in rows if r["buy"] in ("new signal", "open trade")), "tams": sum(1 for r in rows if r["tam"]),
                  "stocks": rows, "curve": curve, "bcurve": bcurve,
                  "news_n": len((news or {}).get(th["id"], []))}
        out.append(th_out)
        for s in syms:
            chips.setdefault(s, []).append({"id": th["id"], "name": th["name"], "state": state})
            if state in ("Leading", "Improving"):
                key = "th_lead" if state == "Leading" else "th_imp"
                sc.setdefault(s + ".NS", {})[key] = 1
    order = {"Leading": 0, "Improving": 1, "Weakening": 2, "Lagging": 3, None: 4}
    out.sort(key=lambda t: (order.get(t["state"], 4), -(t["r3m"] or -999)))
    ist = datetime.now(IST)
    page = {"generated": ist.strftime("%d %b %Y, %I:%M %p IST"), "themes": out}
    # news history goes in its own file, loaded only when a theme is opened
    if news is not None:
        try:
            DOCS.mkdir(parents=True, exist_ok=True)
            (DOCS / "themes_news.json").write_text(json.dumps(news, separators=(",", ":")), encoding="utf-8")
        except Exception:
            pass
    return page, chips, sc
