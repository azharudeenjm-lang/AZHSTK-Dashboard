"""Support/resistance levels, trendlines and breakout signals for every stock.

How it works, per stock and timeframe:
  1. Swing points: a swing high is higher than `pivot` bars on each side
     (a swing low is the mirror image).
  2. Horizontal levels: swing highs and lows within a tolerance (1.5% daily,
     2.5% weekly, or half an ATR if larger) are merged into one level. A level
     needs 2+ touches.
  3. Trendlines: a falling line through two lower swing highs, or a rising
     line through two higher swing lows. A line is only valid if no close
     broke it in between; more touches = stronger. The best line is kept.
  4. Signals (a stock can have several):
       Breakout              close 1%+ above a tested resistance in the last few bars
       Trendline breakout    close above a valid falling trendline
       Retest                broke out a little earlier, now back near that level
       At trendline support  just above a valid rising trendline
       Near support          within a few % above a support level
       Near resistance       within a few % below a resistance level
       Breakdown             close below a tested support
       Trendline breakdown   close below a valid rising trendline
"""
import numpy as np
import pandas as pd

from .config import LEVEL_PARAMS, WEEKLY_LIVE

BULLISH = ["Breakout", "Trendline breakout", "Retest", "At trendline support", "Near support"]
BEARISH = ["Breakdown", "Trendline breakdown", "Near resistance"]
ORDER = BULLISH + BEARISH


def weekly(close, high, low, volume, today=None):
    c = close.resample("W-FRI").last()
    h = high.resample("W-FRI").max()
    l = low.resample("W-FRI").min()
    v = volume.resample("W-FRI").sum(min_count=1)
    today = pd.Timestamp(today or pd.Timestamp.now(tz="Asia/Kolkata").date())
    done = (c.index <= today) | WEEKLY_LIVE   # live: keep the week in progress
    keep = c[done].notna().any(axis=1)
    return [x[done][keep] for x in (c, h, l, v)]


def _pivots(a, k, high=True):
    n, out = len(a), []
    for i in range(k, n - k):
        win = a[i - k:i + k + 1]
        if (a[i] >= win.max()) if high else (a[i] <= win.min()):
            if not out or i - out[-1] > k:      # skip flat duplicates
                out.append(i)
    return out


def _cluster(points, tol):
    """points: list of (price, index). Returns [(level, touches, last_index)]."""
    levels, cur = [], []
    for price, i in sorted(points):
        if cur and price > np.mean([p for p, _ in cur]) * (1 + tol):
            levels.append(cur)
            cur = []
        cur.append((price, i))
    if cur:
        levels.append(cur)
    return [(float(np.mean([p for p, _ in g])), len(g), max(i for _, i in g))
            for g in levels if len(g) >= 2]


def _best_line(piv, vals, c, n, tol, recent, falling):
    """Best valid trendline through swing points. Returns dict or None."""
    piv = [i for i in piv if i < n - 1][-8:]
    best = None
    for x in range(len(piv)):
        for y in range(x + 1, len(piv)):
            a, b = piv[x], piv[y]
            va, vb = vals[a], vals[b]
            if falling and not vb < va * (1 - tol):
                continue
            if not falling and not vb > va * (1 + tol):
                continue
            m = (vb - va) / (b - a)
            line = va + m * (np.arange(n) - a)
            if line[-1] <= 0:
                continue
            seg = slice(a + 1, max(a + 1, n - recent))
            if falling and np.any(c[seg] > line[seg] * (1 + tol / 2)):
                continue
            if not falling and np.any(c[seg] < line[seg] * (1 - tol / 2)):
                continue
            touches = sum(1 for i in piv if i >= a and abs(vals[i] - line[i]) <= line[i] * tol)
            score = (touches, b)
            if best is None or score > best["score"]:
                best = {"a": a, "b": b, "m": m, "va": va, "line": line,
                        "touches": touches, "score": score}
    return best


def analyze(c, h, l, v, p):
    """Arrays for one stock (oldest first, no NaN). Returns dict or None."""
    n = len(c)
    if n < max(60, 4 * p["pivot"] + 20):
        return None
    price = c[-1]
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    atr = tr[-14:].mean()
    tol = max(p["tol_min"], 0.5 * atr / price)
    k, R, brk = p["pivot"], p["recent"], p["brk"]

    ph, pl = _pivots(h, k, True), _pivots(l, k, False)
    levels = _cluster([(h[i], i) for i in ph] + [(l[i], i) for i in pl], tol)
    avgv = lambda j: np.nanmean(v[max(0, j - 20):j]) if j > 0 else np.nan
    volx = lambda j: float(v[j] / avgv(j)) if avgv(j) and not np.isnan(avgv(j)) and avgv(j) > 0 else None

    out = {"sig": [], "tol": round(tol * 100, 1)}
    above = [L for L in levels if L[0] > price]
    below = [L for L in levels if L[0] < price]
    if above:
        r = min(above, key=lambda L: L[0])
        out["res"] = {"p": r[0], "d": (r[0] / price - 1) * 100, "t": r[1]}
    if below:
        s = max(below, key=lambda L: L[0])
        out["sup"] = {"p": s[0], "d": (price / s[0] - 1) * 100, "t": s[1]}

    # horizontal breakout / retest / breakdown
    W = p["retest"]
    for lev, t, last in sorted(below, key=lambda L: -L[0]):
        for j in range(max(1, n - W), n):
            if c[j] > lev * (1 + brk) and c[j - 1] <= lev * (1 + brk) and last < j \
                    and np.nanmax(c[max(0, j - 30):j]) <= lev * (1 + tol):
                ago = n - 1 - j
                info = {"p": lev, "t": t, "ago": ago, "vx": volx(j), "j": j}
                if ago < R:
                    out["sig"].append("Breakout"); out["brk"] = info
                elif l[-R:].min() <= lev * (1 + 2 * tol) and price > lev:
                    out["sig"].append("Retest"); out["brk"] = info
                break
        if "brk" in out:
            break
    for lev, t, last in sorted(above, key=lambda L: L[0]):
        hit = False
        for j in range(max(1, n - R), n):
            if c[j] < lev * (1 - brk) and c[j - 1] >= lev * (1 - brk) and last < j \
                    and np.nanmin(c[max(0, j - 30):j]) >= lev * (1 - tol):
                out["sig"].append("Breakdown")
                out["bdn"] = {"p": lev, "t": t, "ago": n - 1 - j, "vx": volx(j), "j": j}
                hit = True
                break
        if hit:
            break

    # trendlines
    fall = _best_line(ph, h, c, n, tol, R, falling=True)
    if fall:
        line = fall["line"]
        lv = line[-1]
        broke = [j for j in range(n - R, n) if c[j] > line[j] * (1 + brk)]
        out["tlr"] = {"v": lv, "d": (lv / price - 1) * 100, "t": fall["touches"],
                      "a": fall["a"], "va": fall["va"]}
        if broke and price > lv:
            out["sig"].append("Trendline breakout")
            out["tlr"]["vx"] = volx(broke[0]); out["tlr"]["j"] = broke[0]
    rise = _best_line(pl, l, c, n, tol, R, falling=False)
    if rise:
        line = rise["line"]
        lv = line[-1]
        out["tls"] = {"v": lv, "d": (price / lv - 1) * 100, "t": rise["touches"],
                      "a": rise["a"], "va": rise["va"]}
        broke = [j for j in range(n - R, n) if c[j] < line[j] * (1 - brk)]
        if broke and price < lv:
            out["sig"].append("Trendline breakdown"); out["tls"]["j"] = broke[0]
        elif lv <= price <= lv * (1 + p["near_tl"]):
            out["sig"].append("At trendline support")

    if "sup" in out and out["sup"]["d"] <= p["near"] * 100 and "Breakdown" not in out["sig"] \
            and "Retest" not in out["sig"] and "Breakout" not in out["sig"]:
        out["sig"].append("Near support")  # skip when that support is the level just broken
    if "res" in out and out["res"]["d"] <= p["near"] * 100:
        out["sig"].append("Near resistance")

    out["sig"] = [s for s in ORDER if s in out["sig"]]
    return out


def _chart(c, res, n, p):
    """Compact chart payload: closes plus the lines/levels found."""
    m = min(p["chart"], n)
    s = n - m
    sig = lambda x: float(f"{x:.4g}")
    ch = {"c": [sig(x) for x in c[-m:]]}
    lv = {}
    for key in ("sup", "res"):
        if key in res:
            lv[key] = sig(res[key]["p"])
    for key in ("brk", "bdn"):
        if key in res:
            lv[key] = sig(res[key]["p"]); ch[key + "_x"] = res[key]["j"] - s
    if lv:
        ch["lv"] = lv
    for key in ("tlr", "tls"):
        if key in res:
            t = res[key]
            slope = (t["v"] - t["va"]) / ((n - 1) - t["a"]) if n - 1 > t["a"] else 0
            x0 = max(t["a"], s)
            ch[key] = [x0 - s, sig(t["va"] + slope * (x0 - t["a"])), m - 1, sig(t["v"])]
    return ch


def build_levels(close, high, low, volume, tickers, tf="d"):
    p = LEVEL_PARAMS[tf]
    cols = [t for t in tickers if t in close.columns]
    c, h, l, v = close[cols], high[cols], low[cols], volume[cols]
    if tf == "w":
        c, h, l, v = weekly(c, h, l, v)
    c, h, l, v = (x.tail(p["lookback"]) for x in (c, h, l, v))
    out = {}
    for t in cols:
        cc = c[t].to_numpy(float)
        ok = ~np.isnan(cc)
        if ok.sum() < 60:
            continue
        first = np.argmax(ok)
        cc, hh, ll, vv = (x[t].to_numpy(float)[first:] for x in (c, h, l, v))
        # fill odd gaps so maths doesn't break
        cc = pd.Series(cc).ffill().to_numpy()
        hh = pd.Series(hh).fillna(pd.Series(cc)).to_numpy()
        ll = pd.Series(ll).fillna(pd.Series(cc)).to_numpy()
        try:
            res = analyze(cc, hh, ll, vv, p)
        except Exception:
            res = None
        if not res:
            continue
        row = {"sig": res["sig"]}
        for key in ("sup", "res"):
            if key in res:
                row[key] = {"p": round(res[key]["p"], 2), "d": round(res[key]["d"], 1), "t": res[key]["t"]}
        for key in ("tlr", "tls"):
            if key in res:
                row[key] = {"v": round(res[key]["v"], 2), "d": round(res[key]["d"], 1), "t": res[key]["t"]}
        for key in ("brk", "bdn"):
            if key in res:
                b = res[key]
                row[key] = {"p": round(b["p"], 2), "t": b["t"], "ago": b["ago"],
                            "vx": round(b["vx"], 1) if b["vx"] else None}
        if "tlr" in res and res["tlr"].get("vx"):
            row["tlr"]["vx"] = round(res["tlr"]["vx"], 1)
        if res["sig"]:
            row["ch"] = _chart(cc, res, len(cc), p)
        out[t] = row
    return out
