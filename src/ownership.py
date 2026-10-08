"""Ownership alerts and trading facts from NSE (once per evening run).

  Insider trades (SEBI PIT disclosures): promoter / promoter-group buying and
     selling, pledges created, released or invoked, directors and key staff
     selling or buying.                       api/corporates-pit
  Promoter holding and pledged share %      api/corporate-pledgedata
     (quarter by quarter; the change from the previous quarter is tracked)
  Bulk and block deals (who bought or sold big blocks)
                                            api/snapshot-capital-market-largedeal
  Surveillance lists (ASM / GSM)            api/reportASM, api/reportGSM
  Delivery % per stock (last ~25 sessions)  archives: sec_bhavdata_full_DDMMYYYY.csv

Everything is cached in data/cache/own_*.json so a refused call on one day
still shows the last good data. Intraday runs only read the cache.
"""
import io
import json
import re
from datetime import datetime, timedelta, timezone

import pandas as pd

from .config import CACHE, SCREENER_EVENT_BARS as NB
from .nse_api import NSE, num, walk

IST = timezone(timedelta(hours=5, minutes=30))
F = {k: CACHE / f"own_{k}.json" for k in ("pit", "pledge", "deals", "surv", "dlv")}
KEEP_PIT, KEEP_DEALS = 120, 60

META = [
    ("al_psell", "Promoter group sold shares (insider filing)", "e"),
    ("al_pbuy", "Promoter group bought shares (insider filing)", "e"),
    ("al_plg", "Promoter pledged shares (new pledge)", "e"),
    ("al_rel", "Promoter pledge released", "e"),
    ("al_inv", "Pledged shares invoked by lender (forced sale)", "e"),
    ("al_dsell", "Director or key staff sold shares", "e"),
    ("al_dbuy", "Director or key staff bought shares", "e"),
    ("al_bb", "Bulk / block deal: big buyer", "e"),
    ("al_bs", "Bulk / block deal: big seller", "e"),
    ("al_dlv", "High delivery: at least 1.5x its 20-day average and 50%+", "e"),
    ("al_pdn", "Promoter holding fell in the latest quarter", "s"),
    ("al_pup", "Promoter holding rose in the latest quarter", "s"),
    ("al_plg_hi", "More than 25% of promoter shares pledged", "s"),
    ("al_asm", "Under NSE surveillance (ASM / GSM)", "s"),
]


def _now():
    return datetime.now(IST)


def _load(k, default):
    try:
        return json.loads(F[k].read_text(encoding="utf-8"))
    except Exception:
        return default


def _save(k, obj):
    try:
        F[k].parent.mkdir(parents=True, exist_ok=True)
        F[k].write_text(json.dumps(obj), encoding="utf-8")
    except Exception:
        pass


def _date(x):
    s = str(x or "").strip()
    for fmt, n in (("%d-%b-%Y", 11), ("%d-%m-%Y", 10), ("%Y-%m-%d", 10), ("%d/%m/%Y", 10)):
        try:
            return datetime.strptime(s[:n], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _cr(v):
    return f"₹{v / 1e7:,.1f} cr" if v and v >= 1e6 else (f"₹{v / 1e5:,.1f} lakh" if v else "")


def _qty(q):
    if not q:
        return ""
    return f"{q / 1e7:,.2f} cr shares" if q >= 1e7 else f"{q / 1e5:,.2f} lakh shares" if q >= 1e5 else f"{q:,.0f} shares"


# ---------------------------------------------------------------- fetchers
def _fetch_pit(api, first):
    days = 45 if first else 10
    to, fr = _now(), _now() - timedelta(days=days)
    j = api.get("/api/corporates-pit", {"index": "equities", "from_date": f"{fr:%d-%m-%Y}", "to_date": f"{to:%d-%m-%Y}"},
                referer="/companies-listing/corporate-filings-insider-trading")
    if j is None:
        return None
    out = []
    for x in walk(j, "symbol"):
        cat = str(x.get("personCategory") or "")
        typ = f"{x.get('tdpTransactionType') or ''} {x.get('acqMode') or ''}".lower()
        if "revok" in typ or "release" in typ:
            kind = "rel"
        elif "invoc" in typ:
            kind = "inv"
        elif "pledge" in typ:
            kind = "plg"
        elif any(w in typ for w in ("sell", "sale", "dispos")):
            kind = "sell"
        elif any(w in typ for w in ("buy", "purchase", "acqui", "allot")):
            kind = "buy"
        else:
            continue
        who = "p" if "promoter" in cat.lower() else ("d" if re.search(r"director|key managerial|kmp|designated|employee", cat, re.I) else None)
        if not who:
            continue
        d = _date(x.get("date")) or _date(x.get("intimDt")) or _date(x.get("acqtoDt"))
        if not d:
            continue
        out.append({"s": str(x["symbol"]).strip(), "d": d, "w": who, "k": kind, "n": str(x.get("acqName") or "")[:60],
                    "q": num(x.get("secAcq")), "v": num(x.get("secVal")), "a": num(x.get("afterAcqSharesPer")),
                    "b": num(x.get("befAcqSharesPer")), "c": cat[:40]})
    return out


def _fetch_pledge(api, names):
    j = api.get("/api/corporate-pledgedata", {"index": "equities"}, referer="/companies-listing/corporate-filings-pledged-data")
    if j is None:
        return None
    rows = walk(j, "comName") or walk(j, "symbol")
    out = {}
    for x in rows:
        sym = str(x.get("symbol") or "").strip()
        if not sym:
            sym = names.get(_norm(x.get("comName")))
        if not sym:
            continue
        out[sym] = {"shp": _date(x.get("shp")) or str(x.get("shp") or ""), "prom": num(x.get("percPromoterHolding")),
                    "plg": num(x.get("percPromoterShares")), "sh": num(x.get("totIssuedShares"))}
    return out


def _fetch_deals(api):
    j = api.get("/api/snapshot-capital-market-largedeal", referer="/market-data/large-deals")
    if j is None:
        return None
    out = []
    for key, typ in (("BULK_DEALS_DATA", "bulk"), ("BLOCK_DEALS_DATA", "block")):
        for x in (j.get(key) or []) if isinstance(j, dict) else []:
            d = _date(x.get("date"))
            side = str(x.get("buySell") or "").upper()
            if not d or side not in ("BUY", "SELL"):
                continue
            out.append({"s": str(x.get("symbol") or "").strip(), "d": d, "t": typ, "side": side,
                        "n": str(x.get("clientName") or "")[:60], "q": num(x.get("qty")), "p": num(x.get("watp"))})
    return out


def _fetch_surv(api):
    out = {}
    for path, ref, label in (("/api/reportASM", "/reports/asm", "ASM"), ("/api/reportGSM", "/reports/gsm", "GSM")):
        j = api.get(path, referer=ref)
        if j is None:
            continue
        for x in walk(j, "symbol"):
            stage = next((str(v) for k, v in x.items() if re.search(r"stage|indicator|survcode", k, re.I) and v), "")
            out[str(x["symbol"]).strip()] = (label + (" " + stage if stage else "")).strip()
    return out or None


def _fetch_delivery(days=25):
    """{date: {symbol: delivery %}} for recent sessions (archive files work where the API may not)."""
    from . import nse_eod
    import requests
    have = _load("dlv", {})
    s = requests.Session()
    s.headers.update(nse_eod.HEAD)
    got = 0
    d = _now().date() if _now().hour >= 19 else _now().date() - timedelta(days=1)
    tried = 0
    while tried < days + 12 and len([k for k in have if k >= (d - timedelta(days=40)).isoformat()]) < days + 2:
        iso = d.isoformat()
        if d.weekday() < 5 and iso not in have:
            raw = nse_eod._get(s, f"/products/content/sec_bhavdata_full_{d:%d%m%Y}.csv")
            if raw:
                try:
                    df = pd.read_csv(io.BytesIO(raw))
                    df.columns = [c.strip() for c in df.columns]
                    df = df[df["SERIES"].astype(str).str.strip().isin(["EQ", "BE", "BZ"])]
                    dp = pd.to_numeric(df["DELIV_PER"].astype(str).str.strip(), errors="coerce")
                    have[iso] = {str(a).strip(): round(float(b), 1) for a, b in zip(df["SYMBOL"], dp) if pd.notna(b)}
                    got += 1
                except Exception as e:
                    print(f"  ! delivery file {iso}: {str(e)[:60]}")
            tried += 1
        d -= timedelta(days=1)
        if d < _now().date() - timedelta(days=60):
            break
    keep = sorted(have)[-30:]
    have = {k: have[k] for k in keep}
    _save("dlv", have)
    print(f"  delivery %: {got} new day(s), {len(have)} days cached")
    return have


# ---------------------------------------------------------------- build
def _norm(x):
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\b(limited|ltd)\b", "", str(x or "").lower()))


def build(stocks, dates_d, dates_w, prices=None, fetch=True, demo=False):
    """stocks: [(symbol, name)]. prices: {symbol: last price}.
    Returns (alerts {sym: [items]}, events {tf: {ticker: {cond: value}}}, facts {sym: {...}})."""
    if demo:
        pit, pledge, deals, surv, dlv, hist = _demo(stocks)
    else:
        pit = _load("pit", [])
        pl_cache = _load("pledge", {"now": {}, "hist": {}})
        deals = _load("deals", [])
        surv = _load("surv", {})
        dlv = _load("dlv", {})
        if fetch:
            api = NSE()
            names = {_norm(n): s for s, n in stocks}
            new = _fetch_pit(api, first=not pit)
            if new is not None:
                key = lambda r: (r["s"], r["d"], r["n"], r["k"], r["q"])
                seen = {key(r) for r in pit}
                pit += [r for r in new if key(r) not in seen]
            pnow = _fetch_pledge(api, names)
            if pnow:
                for s, r in pnow.items():
                    h = pl_cache["hist"].setdefault(s, [])
                    if r["shp"] and (not h or h[-1][0] != r["shp"]):
                        h.append([r["shp"], r["prom"], r["plg"]])
                        h.sort()
                        del h[:-6]
                pl_cache["now"] = pnow
            nd = _fetch_deals(api)
            if nd is not None:
                key = lambda r: (r["s"], r["d"], r["n"], r["side"], r["q"])
                seen = {key(r) for r in deals}
                deals += [r for r in nd if key(r) not in seen]
            sv = _fetch_surv(api)
            if sv is not None:
                surv = sv
            try:
                dlv = _fetch_delivery()
            except Exception as e:
                print(f"  ! delivery % skipped: {str(e)[:80]}")
            cut = (_now() - timedelta(days=KEEP_PIT)).strftime("%Y-%m-%d")
            pit = [r for r in pit if r["d"] >= cut]
            cut = (_now() - timedelta(days=KEEP_DEALS)).strftime("%Y-%m-%d")
            deals = [r for r in deals if r["d"] >= cut]
            _save("pit", pit)
            _save("pledge", pl_cache)
            _save("deals", deals)
            _save("surv", surv)
            print(f"  NSE ownership data: insider trades {len(pit)}, pledge rows {len(pl_cache['now'])}, "
                  f"deals {len(deals)}, surveillance {len(surv)} (NSE {'reachable' if api.ok else 'refused - cached data used'})")
        pledge, hist = pl_cache["now"], pl_cache["hist"]

    known = {s for s, _ in stocks}
    alerts, facts = {}, {}
    prices = prices or {}

    def add(sym, d, text, kind, tone, ev=None):
        alerts.setdefault(sym, []).append({"d": d, "t": text, "k": kind, "m": tone, "e": ev})

    for r in pit:
        s = r["s"]
        if s not in known:
            continue
        who = "Promoter group" if r["w"] == "p" else "Director / key staff"
        amt = " · ".join(x for x in (_qty(r["q"]), _cr(r["v"])) if x)
        nm = f" ({r['n']})" if r["n"] else ""
        txt = {"sell": f"{who} sold {amt}{nm}", "buy": f"{who} bought {amt}{nm}",
               "plg": f"{who} pledged {amt}{nm}", "rel": f"{who} released pledge on {amt}{nm}",
               "inv": f"Lender invoked pledge: {amt} of {r['n'] or 'promoter'} shares"}[r["k"]]
        if r.get("b") is not None and r.get("a") is not None and r["k"] in ("sell", "buy"):
            txt += f"; holding {r['b']:.2f}% → {r['a']:.2f}%"
        tone = {"sell": -1, "buy": 1, "plg": -1, "rel": 1, "inv": -1}[r["k"]]
        ev = {"sell": "al_psell", "buy": "al_pbuy", "plg": "al_plg", "rel": "al_rel", "inv": "al_inv"}[r["k"]] if r["w"] == "p" \
            else {"sell": "al_dsell", "buy": "al_dbuy"}.get(r["k"])
        add(s, r["d"], txt, "ins", tone, ev)
    for r in deals:
        s = r["s"]
        if s not in known:
            continue
        val = (r["q"] or 0) * (r["p"] or 0)
        txt = f"{r['t'].title()} deal: {r['n'] or 'a large investor'} {'bought' if r['side'] == 'BUY' else 'sold'} " \
              f"{_qty(r['q'])} at ₹{(r['p'] or 0):,.2f}" + (f" ({_cr(val)})" if val else "")
        add(s, r["d"], txt, "deal", 1 if r["side"] == "BUY" else -1, "al_bb" if r["side"] == "BUY" else "al_bs")
    # delivery %
    ddays = sorted(dlv)
    for s in known:
        series_ = [(d, dlv[d].get(s)) for d in ddays if dlv[d].get(s) is not None]
        f = facts.setdefault(s, {})
        if series_:
            f["dlv"] = series_[-1][1]
            base = [v for _, v in series_[-21:-1]]
            if len(base) >= 8:
                avg = sum(base) / len(base)
                f["dlvx"] = round(series_[-1][1] / avg, 2) if avg > 0 else None
            # high-delivery days in the event window
            for i in range(max(0, len(series_) - NB), len(series_)):
                d, v = series_[i]
                prev = [x for _, x in series_[max(0, i - 20):i]]
                if len(prev) >= 8 and v >= 50 and v >= 1.5 * (sum(prev) / len(prev)):
                    add(s, d, f"High delivery: {v:.0f}% of volume taken for delivery (20-day average {sum(prev) / len(prev):.0f}%)",
                        "dlv", 1, "al_dlv")
        p = pledge.get(s)
        if p:
            f["prom"], f["plg"] = p.get("prom"), p.get("plg")
            if p.get("sh") and prices.get(s):
                f["mc"] = round(p["sh"] * prices[s] / 1e7, 0)
            h = hist.get(s) or []
            if len(h) >= 2 and h[-1][1] is not None and h[-2][1] is not None:
                f["pchg"] = round(h[-1][1] - h[-2][1], 2)
        if s in surv:
            f["asm"] = surv[s]
    for s, f in facts.items():
        for k in [k for k, v in f.items() if v is None]:
            del f[k]
    facts = {s: f for s, f in facts.items() if f}

    # screener events (bars ago) and states, per timeframe
    from bisect import bisect_left
    events = {"d": {}, "w": {}}
    for tf, dates in (("d", dates_d), ("w", dates_w)):
        if not dates:
            continue
        n = len(dates)
        for s, items in alerts.items():
            row = {}
            for it in items:
                if not it["e"]:
                    continue
                j = bisect_left(dates, it["d"])
                ago = max(0, n - 1 - j) if j < n else 0
                if ago < NB:
                    row[it["e"]] = min(row.get(it["e"], 99), ago)
            if row:
                events[tf][s + ".NS"] = row
        for s, f in facts.items():
            row = events[tf].setdefault(s + ".NS", {})
            if f.get("pchg") is not None and f["pchg"] <= -0.5:
                row["al_pdn"] = 1
            if f.get("pchg") is not None and f["pchg"] >= 0.5:
                row["al_pup"] = 1
            if (f.get("plg") or 0) > 25:
                row["al_plg_hi"] = 1
            if f.get("asm"):
                row["al_asm"] = 1
            if not row:
                del events[tf][s + ".NS"]
    # standing alerts (not dated events) for the pop-up
    today = _now().strftime("%Y-%m-%d")
    for s, f in facts.items():
        if f.get("asm"):
            add(s, today, f"Under NSE surveillance: {f['asm']} (higher margins, tighter limits)", "surv", -1)
        if (f.get("plg") or 0) > 0:
            add(s, today, f"{f['plg']:.1f}% of promoter shares are pledged", "plgst", -1 if f["plg"] > 25 else 0)
        if f.get("pchg"):
            add(s, today, f"Promoter holding {'fell' if f['pchg'] < 0 else 'rose'} {abs(f['pchg']):.2f} points last quarter "
                          f"(now {f.get('prom', 0):.2f}%)", "phold", -1 if f["pchg"] < 0 else 1)
    for s in alerts:
        alerts[s] = sorted(alerts[s], key=lambda x: x["d"], reverse=True)[:15]
    return alerts, events, facts


def _demo(stocks):
    import random
    rnd = random.Random(11)
    today = _now().date()
    pit, deals, surv, dlv, pledge, hist = [], [], {}, {}, {}, {}
    for i, (s, n) in enumerate(stocks):
        if i % 9 == 0:
            pit.append({"s": s, "d": (today - timedelta(days=rnd.randint(0, 14))).isoformat(), "w": rnd.choice("pd"),
                        "k": rnd.choice(["sell", "buy", "plg", "rel"]), "n": "Demo Holder", "q": rnd.randint(1, 50) * 1e4,
                        "v": rnd.randint(1, 90) * 1e6, "a": 51.2, "b": 52.0, "c": "Promoter Group"})
        if i % 13 == 0:
            deals.append({"s": s, "d": (today - timedelta(days=rnd.randint(0, 9))).isoformat(), "t": rnd.choice(["bulk", "block"]),
                          "side": rnd.choice(["BUY", "SELL"]), "n": "Demo Fund", "q": rnd.randint(1, 30) * 1e5, "p": 250.0})
        if i % 31 == 0:
            surv[s] = "ASM Stage I"
        pledge[s] = {"shp": "2026-09-30", "prom": round(rnd.uniform(30, 75), 2),
                     "plg": round(rnd.choice([0, 0, 0, rnd.uniform(1, 60)]), 2), "sh": rnd.randint(5, 300) * 1e6}
        hist[s] = [["2026-06-30", pledge[s]["prom"] + rnd.choice([-1.2, 0, 0, 0.8]), 0], ["2026-09-30", pledge[s]["prom"], 0]]
    for k in range(25):
        d = today - timedelta(days=k)
        if d.weekday() < 5:
            dlv[d.isoformat()] = {s: round(rnd.uniform(20, 70) if not (k == 0 and i % 7 == 0) else 85, 1)
                                  for i, (s, _) in enumerate(stocks)}
    return pit, pledge, deals, surv, dlv, hist
