"""Fundamentals, cached between runs.

Two sources:
  NSE quarterly results (api/results-comparision, one call per stock):
     sales and profit growth vs the same quarter last year, trailing EPS -> P/E.
     A few hundred stocks are refreshed per evening run (stocks that just
     reported first, then never-fetched, then the oldest), so the whole list
     is covered within about a week without slowing any one run much.
  Yahoo (weekly, Saturday): ROE, debt/equity, margins, P/B, dividend yield,
     institutional holding. Yahoo often refuses GitHub's servers; then those
     fields simply stay empty.
"""
import time
from datetime import datetime, timedelta

import pandas as pd

from .config import CACHE, FUNDAMENTALS_MAX_AGE_DAYS, FUNDAMENTALS_SLEEP_SEC

PATH = CACHE / "fundamentals.parquet"
MAX_CONSECUTIVE_FAILS = 25  # give up early when Yahoo blocks the server
COLS = ["symbol", "fetched", "pe", "pb", "roe", "de", "mcap_cr",
        "margin", "rev_g", "eps_g", "y_sector", "y_industry", "dy", "inst", "qeg"]
NSE_PATH = CACHE / "fund_nse.json"
NSE_BUDGET = 400      # stocks per evening run


def load():
    if PATH.exists():
        df = pd.read_parquet(PATH)
        for c in COLS:
            if c not in df.columns:
                df[c] = None
        return df
    return pd.DataFrame(columns=COLS)


def _num(x, scale=1.0):
    try:
        return round(float(x) * scale, 2)
    except (TypeError, ValueError):
        return None


class Blocked(Exception):
    pass


def _fetch_one(symbol):
    import yfinance as yf
    try:
        info = yf.Ticker(symbol + ".NS").info or {}
    except Exception as e:
        raise Blocked(str(e)[:120])
    if len(info) < 5:  # Yahoo answered with nothing useful (401 / blocked)
        raise Blocked("empty response")
    de = _num(info.get("debtToEquity"))
    return {
        "symbol": symbol, "fetched": datetime.utcnow().strftime("%Y-%m-%d"),
        "pe": _num(info.get("trailingPE")),
        "pb": _num(info.get("priceToBook")),
        "roe": _num(info.get("returnOnEquity"), 100),
        "de": round(de / 100, 2) if de is not None else None,  # Yahoo gives %
        "mcap_cr": _num(info.get("marketCap"), 1e-7),
        "margin": _num(info.get("profitMargins"), 100),
        "rev_g": _num(info.get("revenueGrowth"), 100),
        "eps_g": _num(info.get("earningsGrowth"), 100),
        "y_sector": info.get("sector"), "y_industry": info.get("industry"),
        "dy": _num(info.get("trailingAnnualDividendYield"), 100) if info.get("trailingAnnualDividendYield") is not None
        else _num(info.get("dividendYield")),
        "inst": _num(info.get("heldPercentInstitutions"), 100),
        "qeg": _num(info.get("earningsQuarterlyGrowth"), 100),
    }


def refresh(symbols, max_calls=None, force=False):
    """Fetch fundamentals for stale/missing symbols. Returns full table."""
    df = load()
    cutoff = (datetime.utcnow() - timedelta(days=FUNDAMENTALS_MAX_AGE_DAYS)).strftime("%Y-%m-%d")
    fresh = set() if force else set(df.loc[df["fetched"] >= cutoff, "symbol"])
    todo = [s for s in symbols if s not in fresh]
    if max_calls:
        todo = todo[:max_calls]
    print(f"  fundamentals: {len(todo)} to fetch, {len(fresh)} fresh in cache")

    rows, fails = [], 0
    for i, sym in enumerate(todo, 1):
        try:
            rows.append(_fetch_one(sym))
            fails = 0
        except Blocked as e:
            fails += 1
            if fails == 1 or fails % 10 == 0:
                print(f"  ! {sym}: {e}")
            if fails >= MAX_CONSECUTIVE_FAILS:
                print(f"  Yahoo is refusing fundamentals requests ({fails} in a row). "
                      "Skipping fundamentals this run; prices, technicals and zones still update.")
                break
            time.sleep(3)
        time.sleep(FUNDAMENTALS_SLEEP_SEC)
        if i % 100 == 0 or i == len(todo):
            print(f"  fundamentals {i}/{len(todo)}")
            _save(df, rows)  # checkpoint so a crash keeps progress
    return _save(df, rows)


def _save(df, rows):
    if rows:
        new = pd.DataFrame(rows, columns=COLS)
        df = pd.concat([df[~df["symbol"].isin(new["symbol"])], new], ignore_index=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PATH, index=False)
    return df


# ---------------------------------------------------------------- NSE quarterly results
def _parse_results(j):
    """Quarter rows [(period end, sales, profit, eps)] newest first, from NSE's results comparison."""
    import re
    from .nse_api import num
    recs = []

    def scan(o):
        if isinstance(o, dict):
            if any(re.search(r"to_?dt|todate|period_?end", k, re.I) for k in o):
                recs.append(o)
            for v in o.values():
                scan(v)
        elif isinstance(o, list):
            for v in o:
                scan(v)
    scan(j)
    def pick(r, rx):
        for one in rx.split("|"):                 # patterns in priority order
            v = next((r[k] for k in r if re.search(one, k, re.I) and r[k] not in (None, "", "-")), None)
            if v is not None:
                return v
        return None
    # prefer consolidated figures when both are present
    cons = [r for r in recs if any(str(v).strip().lower() in ("consolidated", "c") for k, v in r.items() if re.search(r"con|type", k, re.I))]
    rows = {}
    for r in (cons or recs):
        end = None
        for k in r:
            if re.search(r"to_?dt|todate|period_?end", k, re.I):
                end = r[k]
                break
        d = None
        for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %b %Y"):
            try:
                d = datetime.strptime(str(end).strip()[:11], fmt)
                break
            except ValueError:
                continue
        if not d or d.strftime("%Y-%m-%d") in rows:
            continue
        sales = num(pick(r, r"net_?sale|income_?from_?op|revenue|total_?inc"))
        prof = num(pick(r, r"net_?profit|pro_?loss_?aft|profit_?after|_pat$|netpl"))
        eps = num(pick(r, r"basic_?eps|eps_?basic|eps"))
        rows[d.strftime("%Y-%m-%d")] = (d, sales, prof, eps)
    return sorted(rows.values(), key=lambda x: x[0], reverse=True)


def _metrics(q):
    """Growth vs same quarter last year and trailing-4-quarter EPS."""
    if not q:
        return {}
    L = q[0]
    out = {"res_end": L[0].strftime("%Y-%m-%d")}
    yo = next((r for r in q[1:] if 330 <= (L[0] - r[0]).days <= 400), None)
    if yo:
        if L[1] and yo[1] and yo[1] > 0:
            out["sg"] = round((L[1] / yo[1] - 1) * 100, 1)
        if L[2] is not None and yo[2] not in (None, 0):
            out["pg"] = round((L[2] - yo[2]) / abs(yo[2]) * 100, 1)
    last4 = q[:4]
    if len(last4) == 4 and all(r[3] is not None for r in last4) and (last4[0][0] - last4[3][0]).days <= 300:
        out["eps_ttm"] = round(sum(r[3] for r in last4), 2)
    if L[1] and L[2] is not None and L[1] > 0:
        out["npm_q"] = round(L[2] / L[1] * 100, 1)
    return out


def refresh_nse(symbols, priority=(), budget=NSE_BUDGET):
    """Fetch NSE quarterly results for up to `budget` stocks. Returns {symbol: metrics}."""
    import json
    from .nse_api import NSE
    try:
        store = json.loads(NSE_PATH.read_text(encoding="utf-8"))
    except Exception:
        store = {}
    order = [s for s in priority if s in symbols]
    order += [s for s in symbols if s not in store and s not in order]
    order += sorted([s for s in symbols if s in store and s not in order], key=lambda s: store[s].get("at", ""))
    todo = order[:budget]
    api = NSE()
    ok = 0
    t0 = time.time()
    for i, sym in enumerate(todo, 1):
        j = api.get("/api/results-comparision", {"symbol": sym}, referer=f"/get-quotes/equity?symbol={sym}", tries=1)
        if j is None:
            if api.fails >= 8:
                print("  NSE refused results requests; using cached figures")
                break
            continue
        m = _metrics(_parse_results(j))
        m["at"] = datetime.utcnow().strftime("%Y-%m-%d")
        store[sym] = m
        ok += 1 if len(m) > 1 else 0
        time.sleep(0.25)
        if time.time() - t0 > 900:          # never spend more than 15 minutes here
            break
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        NSE_PATH.write_text(json.dumps(store), encoding="utf-8")
    except Exception:
        pass
    print(f"  NSE results: {ok} of {len(todo)} stocks refreshed, {len(store)} in cache")
    try:
        from .nse_api import DIAG
        DIAG["results_parsed"] = {"with_figures": ok, "tried": len(todo), "cached": len(store),
                                  "example": next(({k: v} for k, v in store.items() if len(v) > 1), None)}
    except Exception:
        pass
    return store


def load_nse():
    import json
    try:
        return json.loads(NSE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


FIN_SECTORS = ("Financial Services",)


def combine(stocks, fund_df, nse, own_facts):
    """One small dict per stock for the Screener and pop-up (short keys).
    stocks: list of dicts with sym, sector, price."""
    yahoo = {} if fund_df is None or not len(fund_df) else fund_df.set_index("symbol").to_dict("index")
    out = {}
    for s in stocks:
        sym, px = s["sym"], s.get("price")
        y, n, o = yahoo.get(sym, {}), nse.get(sym, {}), own_facts.get(sym, {})
        g = lambda d, k: (None if d.get(k) is None or (isinstance(d.get(k), float) and d.get(k) != d.get(k)) else d.get(k))
        f = {}
        eps = g(n, "eps_ttm")
        f["pe"] = round(px / eps, 1) if px and eps and eps > 0 else g(y, "pe")
        f["pb"], f["roe"], f["de"] = g(y, "pb"), g(y, "roe"), g(y, "de")
        f["mc"] = o.get("mc") or g(y, "mcap_cr")
        f["npm"] = g(n, "npm_q") if g(n, "npm_q") is not None else g(y, "margin")
        f["sg"] = g(n, "sg") if g(n, "sg") is not None else g(y, "rev_g")
        f["pg"] = g(n, "pg") if g(n, "pg") is not None else (g(y, "qeg") if g(y, "qeg") is not None else g(y, "eps_g"))
        f["dy"], f["inst"] = g(y, "dy"), g(y, "inst")
        f["prom"], f["plg"], f["pchg"] = o.get("prom"), o.get("plg"), o.get("pchg")
        f["dlv"], f["dlvx"], f["asm"] = o.get("dlv"), o.get("dlvx"), o.get("asm")
        f["qe"] = g(n, "res_end")
        # quality grade from what is available
        fin = s.get("sector") in FIN_SECTORS
        checks = [("roe", lambda v: v >= 15), ("sg", lambda v: v >= 10), ("pg", lambda v: v >= 10), ("npm", lambda v: v >= 8)]
        if not fin:
            checks.append(("de", lambda v: v <= 1))
        res = [fn(f[k]) for k, fn in checks if f.get(k) is not None]
        if len(res) >= 2:
            frac = sum(res) / len(res)
            grade = 0 if frac >= 0.8 else 1 if frac >= 0.6 else 2 if frac >= 0.4 else 3
            if (f.get("plg") or 0) > 25 or f.get("asm"):
                grade = min(3, grade + 1)
            f["qg"] = "ABCD"[grade]
            f["qs"] = round(frac * 5, 1)
        out[sym] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in f.items() if v is not None}
    return out
