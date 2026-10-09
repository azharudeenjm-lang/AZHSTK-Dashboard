"""Forward test: paper-trades the Buy criteria rule from the day it is switched on.

Two portfolios, each starting with ₹10,00,000:
  "all" - every Buy criteria signal (liquid stocks)
  "ab"  - only stocks graded Quality A or B at the time of the signal
Rules (same as the Buy criteria tab):
  * Decisions only on completed weekly closes (the Friday evening run).
  * Exits first: sell when the weekly close is below the trailing stop
    (higher of the breakout-week low and the 10-week average).
  * Then entries: new signals, strongest relative strength first, up to 10
    stocks, each about 10% of the portfolio value, whole shares only.
  * Costs 0.15% on every buy and sell. Prices are the weekly close (in real
    life you would buy on Monday, so expect some difference).
  * Every run (also the intraday ones) values the open positions at the
    latest price, so the curve moves daily.
State is kept in data/cache/forward.json and published as docs/forward.json;
if the cache is ever lost, the published copy is read back, so the test
never restarts by accident.
"""
import json
import os

import numpy as np
import pandas as pd

from .config import CACHE, DOCS

CAPITAL = 1_000_000
SLOTS = 10
COST = 0.0015
PATH = CACHE / "forward.json"
BOOKS = {"all": "All Buy criteria signals", "ab": "Quality A or B only"}


def _load():
    try:
        return json.loads(PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:                     # cache lost: read back the last published copy
        try:
            import requests
            r = requests.get(f"https://raw.githubusercontent.com/{repo}/gh-pages/forward.json", timeout=20)
            if r.ok and r.text.startswith("{"):
                print("  forward test: restored from the published copy")
                return r.json()
        except Exception:
            pass
    return None


def _new(today, last_week):
    return {"start": today, "capital": CAPITAL, "last_week": last_week, "hist": [],
            "books": {k: {"cash": float(CAPITAL), "pos": {}, "closed": []} for k in BOOKS}}


def _val(book, price):
    return book["cash"] + sum(p["q"] * (price.get(s) or p["last"]) for s, p in book["pos"].items())


def _step(st, fu, c, l, sma, sig, rs, w, w_done, price, when, week_id):
    """One check: exits first (price below the trailing stop), then new buys.
    w: weekly bar (index label) whose signals and low are used (the week in progress during the week);
    w_done: last COMPLETED week, whose 10-week average sets the trailing stop; price: {sym: price now}."""
    sig_now = [t for t in sig.columns[sig.loc[w].fillna(False).values.astype(bool)]]
    sig_now.sort(key=lambda t: -(rs.at[w, t] if np.isfinite(rs.at[w, t]) else 0))
    srow = sma.loc[w_done] if w_done is not None else None
    acted = 0
    for key, book in st["books"].items():
        for s in list(book["pos"]):
            p = book["pos"][s]
            px_ = price.get(s)
            if px_ is None:
                continue
            sm = srow.get(s + ".NS") if srow is not None else None
            trail = max(p["sl"], sm if sm is not None and np.isfinite(sm) else -1)
            p["trail"] = round(float(trail), 2)
            p["best"] = max(p.get("best", p["ep"]), px_)
            p["last"] = px_
            if px_ < trail:
                proceeds = p["q"] * px_ * (1 - COST)
                book["cash"] += proceeds
                cost_in = p["q"] * p["ep"] * (1 + COST)
                book["closed"].append({"sym": s, "ed": p["ed"], "ep": p["ep"], "q": p["q"], "xd": when, "xp": round(px_, 2),
                                       "why": "Stop-loss" if trail == p["sl"] else "Trailing stop",
                                       "pnl": round(proceeds - cost_in, 0), "pct": round((proceeds / cost_in - 1) * 100, 1),
                                       "weeks": int((pd.Timestamp(when[:10]) - pd.Timestamp(p["ed"][:10])).days // 7), "wk": week_id})
                del book["pos"][s]
                acted += 1
        value = book["cash"] + sum(p["q"] * price.get(s, p["last"]) for s, p in book["pos"].items())
        sold_this_week = {x["sym"] for x in book["closed"] if x.get("wk") == week_id}
        for t in sig_now:
            s = t[:-3]
            if len(book["pos"]) >= SLOTS:
                break
            if s in book["pos"] or s in sold_this_week:      # no re-buying a stock sold the same week
                continue
            if key == "ab" and (fu.get(s) or {}).get("qg") not in ("A", "B"):
                continue
            px_ = price.get(s)
            sl = float(l.at[w, t])
            if px_ is None or not np.isfinite(sl) or px_ <= sl:
                continue
            amt = min(value / SLOTS, book["cash"])
            q = int(amt // (px_ * (1 + COST)))
            if q < 1:
                continue
            book["cash"] -= q * px_ * (1 + COST)
            book["pos"][s] = {"ed": when, "ep": round(px_, 2), "q": q, "sl": round(sl, 2), "trail": round(sl, 2),
                              "best": px_, "last": px_, "rs": round(float(rs.at[w, t]) * 100) if np.isfinite(rs.at[w, t]) else None,
                              "grade": (fu.get(s) or {}).get("qg")}
            acted += 1
    return acted


def update(frames, px, stocks, fu, benchmark, today, full_run=True, demo=False):
    """Called on every run (also the 30-minute market-hours ones). frames: weekly frames from buy.build.
    fu: {sym: fundamentals incl. 'qg'}. Returns the page payload."""
    c, l, sma, sig, rs = frames["c"], frames["l"], frames["sma"], frames["sig"], frames["rs"]
    done = [d for d in c.index if d.strftime("%Y-%m-%d") <= today]       # completed weekly bars
    w_done = done[-1] if done else None
    w = c.index[-1]                                                        # this week (in progress or just completed)
    info = {s["sym"]: s for s in stocks}
    latest = px["Close"].ffill().iloc[-1]
    price = {t[:-3]: float(v) for t, v in latest.items() if t.endswith(".NS") and np.isfinite(v)}
    now = pd.Timestamp.now(tz="Asia/Kolkata")
    when = f"{today} {now:%H:%M}"
    st = None if demo else _load()
    if demo:                     # demo: replay the last 30 weeks, one check per week, so the page has trades to show
        st = _new(done[-31].strftime("%Y-%m-%d"), None)
        st["hist"] = []
        for k in range(len(done) - 30, len(done)):
            wk = done[k]
            pr = c.loc[wk]
            pmap = {t[:-3]: float(v) for t, v in pr.items() if np.isfinite(v)}
            _step(st, fu, c, l, sma, sig, rs, wk, done[k - 1], pmap, wk.strftime("%Y-%m-%d") + " 15:30", wk.strftime("%Y-%m-%d"))
            st["hist"].append([wk.strftime("%Y-%m-%d")] + [round(_val(b, pmap), 0) for b in st["books"].values()] +
                              [round(float(px["Close"][benchmark].asof(wk)), 2) if benchmark in px["Close"] else None])
    if not st:
        st = _new(today, None)
        print(f"  forward test: started {today} with ₹{CAPITAL:,} per portfolio")
    if not demo:
        # if a completed week is used for signals (Friday evening / weekend), the trailing stop uses that week's average too
        w_ref = w_done if w_done is not None and w_done == w else (done[-1] if done else None)
        acted = _step(st, fu, c, l, sma, sig, rs, w, w_ref, price, when, w.strftime("%Y-%m-%d"))
        st["last_week"] = when
        print(f"  forward test: checked at {when}, {acted} trade(s)")

    # ---------- daily valuation ----------
    for book in st["books"].values():
        for s, p in book["pos"].items():
            if s in price:
                p["last"] = price[s]
    bpx = latest.get(benchmark)
    point = [today] + [round(_val(b, price), 0) for b in st["books"].values()] + [round(float(bpx), 2) if bpx is not None and np.isfinite(bpx) else None]
    if not demo:
        st["hist"] = [h for h in st["hist"] if h[0] != today] + [point]
    st["hist"] = st["hist"][-800:]
    try:
        if demo:
            raise RuntimeError("demo: not saved")
        CACHE.mkdir(parents=True, exist_ok=True)
        PATH.write_text(json.dumps(st), encoding="utf-8")
        DOCS.mkdir(parents=True, exist_ok=True)
        (DOCS / "forward.json").write_text(json.dumps(st), encoding="utf-8")
    except Exception:
        pass

    # ---------- page payload ----------
    out = {"start": st["start"], "capital": CAPITAL, "last_week": st["last_week"], "hist": st["hist"], "books": {}}
    pending = []
    if len(c.index):
        d = c.index[-1]
        pending = [{"sym": t[:-3], "name": (info.get(t[:-3]) or {}).get("name"), "price": round(float(c.at[d, t]), 2),
                    "sl": round(float(l.at[d, t]), 2), "grade": (fu.get(t[:-3]) or {}).get("qg")}
                   for t in sig.columns[sig.loc[d].fillna(False).values.astype(bool)]]
    for key, book in st["books"].items():
        val = _val(book, price)
        pos = []
        for s, p in book["pos"].items():
            last = p.get("last", p["ep"])
            pos.append({"sym": s, "name": (info.get(s) or {}).get("name"), **p, "last": round(last, 2),
                        "inv": round(p["q"] * p["ep"], 0), "now": round(p["q"] * last, 0),
                        "pct": round((last / p["ep"] - 1) * 100, 1), "room": round((last / p["trail"] - 1) * 100, 1) if p.get("trail") else None})
        cl = book["closed"]
        wins = [x for x in cl if x["pnl"] > 0]
        out["books"][key] = {"name": BOOKS[key], "value": round(val, 0), "cash": round(book["cash"], 0),
                             "ret": round((val / CAPITAL - 1) * 100, 2), "pos": sorted(pos, key=lambda x: x["ed"]),
                             "closed": list(reversed(cl[-200:])), "n_closed": len(cl),
                             "win": round(len(wins) / len(cl) * 100, 0) if cl else None,
                             "realised": round(sum(x["pnl"] for x in cl), 0)}
    out["pending"] = pending
    return out
