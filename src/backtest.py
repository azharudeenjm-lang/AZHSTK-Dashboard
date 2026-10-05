"""Weekly backtest of the zone rotation strategy.

Entry   the week a stock moves Accumulation -> Bullish (buy at that close)
Hold    while it stays in Bullish, Strong momentum or Extended
Exit    "cooling": the week it leaves Extended (any direction)
        "divergence": the week it enters the Divergence zone
        "failure": it drops to Neutral, Bearish, Oversold or Accumulation
                   before ever reaching Extended
Variant "ob_exit": also exit if Strong momentum slips back to Bullish
                   before Extended was reached

Runs for every Extended-zone RSI floor in BACKTEST["floors"]. Only one open
trade per stock at a time. Liquidity is checked at the entry week, using the
data available then, so today's liquid list does not leak into the past.
"""
import time
from copy import deepcopy

import numpy as np
import pandas as pd

from .config import BACKTEST, CACHE, ZONE_PARAMS
from .zones import classify, indicators

FAMILY = {"U", "B", "D"}
NAMES = {"U": "Bullish", "B": "Strong momentum", "D": "Extended", "V": "Divergence zone", "N": "Neutral",
         "R": "Bearish", "O": "Oversold", "A": "Accumulation", "-": "No data"}


def download_weekly(tickers, benchmark):
    """10 years of weekly OHLCV, completed weeks only."""
    import yfinance as yf
    allt = list(dict.fromkeys([benchmark] + list(tickers)))
    parts = {f: [] for f in ("Close", "High", "Low", "Volume")}
    for i in range(0, len(allt), 40):
        batch = allt[i:i + 40]
        for attempt in range(2):
            try:
                df = yf.download(batch, period=BACKTEST["history"], interval="1wk", auto_adjust=True,
                                 group_by="column", threads=4, timeout=30, progress=False)
                if df is not None and not df.empty:
                    if not isinstance(df.columns, pd.MultiIndex):
                        df.columns = pd.MultiIndex.from_product([df.columns, batch])
                    for f in parts:
                        parts[f].append(df[f])
                break
            except Exception as e:
                print(f"  ! weekly batch {i}: {str(e)[:80]}")
                time.sleep(10)
        if (i // 40) % 10 == 0:
            print(f"  weekly prices {min(i + 40, len(allt))}/{len(allt)}")
        time.sleep(2)
    out = {}
    for f, lst in parts.items():
        d = pd.concat(lst, axis=1).sort_index()
        d = d.loc[:, ~d.columns.duplicated()]
        d.index = pd.to_datetime(d.index).tz_localize(None)
        out[f] = d
    # Yahoo labels weeks by their Monday; keep only weeks whose Friday has passed
    today = pd.Timestamp(pd.Timestamp.now(tz="Asia/Kolkata").date())
    done = (out["Close"].index + pd.Timedelta(days=4)) <= today
    cols = out["Close"].columns
    for f in out:
        out[f] = out[f].reindex(columns=cols)[done]
    return out


def simulate(codes, close, liquid, bench, cost):
    """codes: DataFrame of zone letters (weeks x tickers). Returns trade list."""
    dates = codes.index
    bidx = bench.reindex(dates).ffill().to_numpy()
    trades = []
    for t in codes.columns:
        z = codes[t].to_numpy()
        c = close[t].to_numpy()
        liq = liquid[t].to_numpy()
        for variant in ("hold", "ob_exit"):
            pos = None
            for i in range(1, len(z)):
                if pos is None:
                    if z[i] == "U" and z[i - 1] == "A" and liq[i] and c[i] == c[i]:
                        pos = {"i": i, "peak": "U", "hiD": False, "hi": c[i]}
                    continue
                pos["hi"] = max(pos["hi"], c[i]) if c[i] == c[i] else pos["hi"]
                zi, reason = z[i], None
                if zi == "V":
                    reason = "Divergence"
                elif pos["hiD"] and zi != "D":
                    reason = "Cooled from Extended"
                elif zi not in FAMILY:
                    reason = "Left uptrend to " + NAMES.get(zi, zi)
                elif variant == "ob_exit" and pos["peak"] == "B" and zi == "U":
                    reason = "Momentum fell back"
                if zi == "D":
                    pos["hiD"] = True
                if zi in ("B", "D") and pos["peak"] != "D":
                    pos["peak"] = zi
                if reason and c[i] == c[i]:
                    trades.append(_trade(t, variant, pos, i, c, dates, bidx, cost, reason))
                    pos = None
            if pos is not None:  # still open at the end
                i = len(z) - 1
                while i > pos["i"] and c[i] != c[i]:
                    i -= 1
                tr = _trade(t, variant, pos, i, c, dates, bidx, cost, "Open")
                tr["open"] = True
                trades.append(tr)
    return trades


def _trade(t, variant, pos, j, c, dates, bidx, cost, reason):
    i = pos["i"]
    ret = (c[j] / c[i] - 1) * 100 - cost
    b = (bidx[j] / bidx[i] - 1) * 100 if bidx[i] and bidx[i] == bidx[i] and bidx[j] == bidx[j] else None
    return {"t": t, "v": variant, "in": dates[i].strftime("%Y-%m-%d"), "out": dates[j].strftime("%Y-%m-%d"),
            "pi": round(float(c[i]), 2), "po": round(float(c[j]), 2), "ret": round(float(ret), 2),
            "wk": int(j - i), "peak": NAMES[pos["peak"]], "why": reason,
            "best": round(float((pos["hi"] / c[i] - 1) * 100), 1),
            "nifty": round(float(b), 2) if b is not None else None, "open": False}


def summarise(tr):
    closed = [x for x in tr if not x["open"]]
    if not closed:
        return {"n": 0, "open": len(tr)}
    r = np.array([x["ret"] for x in closed])
    w, l = r[r > 0], r[r <= 0]
    edge = [x["ret"] - x["nifty"] for x in closed if x["nifty"] is not None]
    reasons = {}
    for x in closed:
        reasons[x["why"]] = reasons.get(x["why"], 0) + 1
    peaks = {}
    for p in ("Bullish", "Strong momentum", "Extended"):
        sub = np.array([x["ret"] for x in closed if x["peak"] == p])
        peaks[p] = {"n": int(len(sub)), "avg": round(float(sub.mean()), 2) if len(sub) else None,
                    "win": round(float((sub > 0).mean() * 100), 1) if len(sub) else None}
    return {
        "n": int(len(r)), "open": len(tr) - len(closed),
        "win": round(float((r > 0).mean() * 100), 1),
        "avg": round(float(r.mean()), 2), "med": round(float(np.median(r)), 2),
        "aw": round(float(w.mean()), 2) if len(w) else None, "al": round(float(l.mean()), 2) if len(l) else None,
        "pf": round(float(w.sum() / -l.sum()), 2) if len(l) and l.sum() < 0 else None,
        "wk": round(float(np.mean([x["wk"] for x in closed])), 1),
        "edge": round(float(np.mean(edge)), 2) if edge else None,
        "best": round(float(r.max()), 1), "worst": round(float(r.min()), 1),
        "danger": round(float(np.mean([x["peak"] == "Extended" for x in closed]) * 100), 1),
        "reasons": reasons, "peaks": peaks,
    }


def breakdown(tr, key):
    groups = {}
    for x in tr:
        if not x["open"]:
            groups.setdefault(key(x), []).append(x["ret"])
    out = []
    for k, v in groups.items():
        a = np.array(v)
        out.append({"k": k, "n": int(len(a)), "win": round(float((a > 0).mean() * 100), 1),
                    "avg": round(float(a.mean()), 2), "med": round(float(np.median(a)), 2)})
    return sorted(out, key=lambda d: str(d["k"]))


def hist(tr):
    edges = [-100, -20, -10, -5, 0, 5, 10, 20, 50, 100, 1e9]
    labels = ["< −20", "−20 to −10", "−10 to −5", "−5 to 0", "0 to 5", "5 to 10", "10 to 20", "20 to 50", "50 to 100", "> 100"]
    r = [x["ret"] for x in tr if not x["open"]]
    cnt = np.histogram(r, bins=edges)[0] if r else [0] * len(labels)
    return [{"k": k, "n": int(n)} for k, n in zip(labels, cnt)]


def run(wk, universe, benchmark):
    """wk: dict of weekly DataFrames. Returns payload for the backtest page."""
    sec = dict(zip(universe["ticker"], universe["sector"]))
    tick = [t for t in universe["ticker"] if t in wk["Close"].columns]
    c, h, l, v = (wk[f][tick] for f in ("Close", "High", "Low", "Volume"))
    ind = indicators(c, h, l)
    turnover = (c * v / 5).rolling(4, min_periods=2).mean() / 1e7   # avg daily value, Rs crore
    liquid = turnover >= BACKTEST["min_turnover_cr"]
    bench = wk["Close"][benchmark]

    variants, trades_all = [], {}
    for floor in BACKTEST["floors"]:
        p = deepcopy(ZONE_PARAMS["w"]); p["rsi_floor"] = floor
        codes = classify(c, ind, p)[0]
        tr = simulate(codes, c, liquid, bench, BACKTEST["cost_pct"])
        for x in tr:
            x["sym"] = x["t"][:-3]; x["sec"] = sec.get(x["t"]); x["fl"] = floor
            del x["t"]
        for variant in ("hold", "ob_exit"):
            sub = [x for x in tr if x["v"] == variant]
            key = f"{floor}-{variant}"
            trades_all[key] = sub
            variants.append({"key": key, "floor": floor, "v": variant, **summarise(sub),
                             "year": breakdown(sub, lambda x: x["in"][:4]),
                             "sector": breakdown(sub, lambda x: x["sec"] or "Unclassified"),
                             "hist": hist(sub)})
        print(f"  backtest floor {floor}: {len(tr)} trades")
    first = wk["Close"].index[0].strftime("%Y-%m-%d") if len(wk["Close"].index) else None
    last = wk["Close"].index[-1].strftime("%Y-%m-%d") if len(wk["Close"].index) else None
    return {"variants": variants, "trades": trades_all, "range": [first, last],
            "cfg": {**BACKTEST, "warmup": "about 80 weeks for the Ichimoku cloud and trend rules"}}
