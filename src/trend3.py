"""Three-touch falling trendline breakouts (weekly), like E2E Networks in May 2026.

The pattern:
  1. A major top (the highest weekly high from that point on).
  2. A falling line from that top through later swing highs, touched at least 3 times
     (top included) within 3.5%, spanning at least 26 weeks.
  3. No weekly close above the line until the breakout.
  4. Breakout: a weekly close more than 2% above the line.
Stronger version (better in testing): breakout week up 8% or more and relative strength
(6-month return) in the top 40% of stocks.

Tested on this dashboard's 5 years of weekly prices (about 2,660 breakouts, liquid stocks,
exit on a weekly close below the 10-week average or the breakout-week low):
  all breakouts      39% won, avg win +27%, avg loss -7%, about +6.6% per trade, 18% reached +50%
  stronger version   47% won, avg win +36%, avg loss -9%, about +12% per trade, 23% reached +50%
Results swing by year (very strong 2023, close to flat 2025).
"""
import numpy as np
import pandas as pd

from .config import SCREENER_EVENT_BARS as NB
from .zones import weekly_bars

META = [
    ("t3_brk", "Broke a falling trendline touched 3+ times (weekly, 6+ months long)", "e"),
    ("t3_strong", "3-touch trendline breakout, strong: week up 8%+ and RS in the top 40%", "e"),
    ("t3_near", "Within 5% below a falling trendline touched 3+ times (watch)", "s"),
]
K, TOL, MIN_SPAN, LOOK, BUF = 3, 0.035, 26, 130, 0.02


def _pivots(a, k):
    out = []
    for i in range(k, len(a) - k):
        w = a[i - k:i + k + 1]
        if np.isfinite(a[i]) and a[i] >= np.nanmax(w) and (not out or i - out[-1] > k):
            out.append(i)
    return out


def detect(h, c):
    """Best falling line from a major top with 3+ touches. Returns dict or None."""
    n = len(c)
    lo = max(0, n - LOOK)
    ph = [i for i in _pivots(h, K) if i >= lo]
    best = None
    for ai, A in enumerate(ph):
        if A > n - 1 - MIN_SPAN:
            break
        if h[A] < np.nanmax(h[A:A + MIN_SPAN]) * 0.999:      # quick check: a real top
            continue
        for B in ph[ai + 1:]:
            if B - A < 6:
                continue
            m = (h[B] - h[A]) / (B - A)
            if m >= 0:
                continue
            line = lambda i: h[A] + m * (i - A)
            touches = [P for P in ph if P >= A and line(P) > 0 and abs(h[P] / line(P) - 1) <= TOL]
            if len(touches) < 3:
                continue
            last_t = max(touches)
            brk = None
            for i in range(last_t + 1, n):
                if line(i) <= 0:
                    break
                if c[i] > line(i) * (1 + BUF):
                    brk = i
                    break
            end = brk if brk is not None else n
            if h[A] < np.nanmax(h[A:max(A + 1, end)]) * 0.999:   # the top stays the highest point until the breakout
                continue
            if any(line(i) > 0 and c[i] > line(i) * (1 + BUF) for i in range(A + 1, end)):
                continue
            span = touches[-1] - A
            if span < MIN_SPAN * 0.6:
                continue
            key = (len(touches), span)
            if best is None or key > best[0]:
                best = (key, {"A": A, "m": m, "touches": touches, "brk": brk, "span": span})
    return best[1] if best else None


def build(px, stocks, rs_frame=None, today=None):
    """Returns (page rows dict, {ticker: screener conditions}, {ticker: chart geometry})."""
    info = {s["sym"]: s for s in stocks}
    cols = [s["sym"] + ".NS" for s in stocks if s.get("liquid") and s["sym"] + ".NS" in px["Close"].columns]
    c, h, l = weekly_bars(px["Close"][cols], px["High"][cols], px["Low"][cols])
    n = len(c.index)
    today = pd.Timestamp(today or pd.Timestamp.now(tz="Asia/Kolkata").date())
    forming = bool(n) and c.index[-1] > today
    sma10 = c.rolling(10, min_periods=10).mean()
    rs_last = rs_frame.iloc[-1] if rs_frame is not None and len(rs_frame) else pd.Series(dtype=float)
    ds = [d.strftime("%Y-%m-%d") for d in c.index]
    brks, near, sc, geo = [], [], {}, {}
    for t in cols:
        cc = c[t].to_numpy(float)
        ok = np.isfinite(cc)
        if ok.sum() < 60:
            continue
        f0 = int(np.argmax(ok))
        cc, hh, ll = cc[f0:], h[t].to_numpy(float)[f0:], l[t].to_numpy(float)[f0:]
        hh = np.where(np.isfinite(hh), hh, cc)
        ll = np.where(np.isfinite(ll), ll, cc)
        if np.isnan(cc).any():
            cc = pd.Series(cc).ffill().to_numpy()
        try:
            r = detect(hh, cc)
        except Exception:
            continue
        if not r:
            continue
        m_, A = r["m"], r["A"]
        line = lambda i: hh[A] + m_ * (i - A)
        nn = len(cc)
        sym = t[:-3]
        rsv = rs_last.get(t)
        rsv = float(rsv) if rsv is not None and np.isfinite(rsv) else None
        touch_dates = [ds[f0 + p] for p in r["touches"]]
        g = {"k": "pt_t3", "name": f"Trendline ({len(r['touches'])} touches)",
             "lines": [[int(nn - 1 - A), float(f"{hh[A]:.4g}"), 0, float(f"{max(line(nn - 1), 0.01):.4g}")]]}
        if r["brk"] is not None:
            b = r["brk"]
            ago = nn - 1 - b
            if ago >= 26:
                continue
            wk = cc[b] / cc[b - 1] - 1 if b > 0 else np.nan
            sl = ll[b]
            sm = sma10[t].to_numpy(float)[f0:][-1]
            trail = max(sl, sm if np.isfinite(sm) else -1)
            strong = bool(np.isfinite(wk) and wk >= 0.08 and rsv is not None and rsv >= 0.6)
            alive = cc[-1] >= trail
            row = {"sym": sym, "name": info[sym]["name"], "sector": info[sym].get("sector"), "bd": ds[f0 + b], "ago": int(ago),
                   "lvl": round(float(line(b)), 2), "entry": round(float(cc[b]), 2), "touches": len(r["touches"]),
                   "tdates": touch_dates, "span": int(r["span"]), "wk": round(float(wk) * 100, 1) if np.isfinite(wk) else None,
                   "rs": round(rsv * 100) if rsv is not None else None, "strong": strong, "sl": round(float(sl), 2),
                   "trail": round(float(trail), 2), "price": round(float(cc[-1]), 2), "gain": round((cc[-1] / cc[b] - 1) * 100, 1),
                   "mx": round(float((np.nanmax(cc[b:]) / cc[b] - 1) * 100), 1),
                   "alive": bool(alive), "forming": bool(forming and ago == 0),
                   "top": round(float(hh[A]), 2), "top_d": ds[f0 + A]}
            brks.append(row)
            if ago < NB:
                sc.setdefault(t, {})["t3_brk"] = int(ago)
                if strong:
                    sc[t]["t3_strong"] = int(ago)
            geo[t] = g
        else:
            lv = line(nn - 1)
            if lv > 0 and lv * 0.95 <= cc[-1] <= lv * (1 + BUF):
                near.append({"sym": sym, "name": info[sym]["name"], "sector": info[sym].get("sector"), "price": round(float(cc[-1]), 2),
                             "lvl": round(float(lv), 2), "trig": round(float(lv * (1 + BUF)), 2), "dist": round((lv * (1 + BUF) / cc[-1] - 1) * 100, 1),
                             "touches": len(r["touches"]), "tdates": touch_dates, "span": int(r["span"]),
                             "rs": round(rsv * 100) if rsv is not None else None, "top": round(float(hh[A]), 2), "top_d": ds[f0 + A]})
                sc.setdefault(t, {})["t3_near"] = 1
                geo[t] = g
    # ---------- 2-year walk-forward: every breakout as it would have been seen at the time ----------
    stats, exits, log = _history(c, h, l, sma10, rs_frame, cols, ds)
    for r in brks:
        x = exits.get((r["sym"], r["bd"]))
        if x:
            r["xd"], r["xp"], r["xg"], r["why"], r["mx"] = x
    brks.sort(key=lambda x: (x["ago"], not x["strong"], -(x["rs"] or 0)))
    near.sort(key=lambda x: x["dist"])
    return {"brk": brks, "near": near[:80], "forming": forming, "stats": stats, "log": log}, sc, geo


def _history(c, h, l, sma10, rs_frame, cols, ds, weeks=104):
    """Replays the detector week by week over the last 2 years. Returns (stats, {(sym, breakout date): exit info})."""
    n = len(c.index)
    start = max(60, n - weeks)
    res = {"all": [], "strong": []}
    opened = {"all": 0, "strong": 0}
    exits, log = {}, []
    rs_a = rs_frame.reindex(index=c.index, columns=cols).to_numpy(float) if rs_frame is not None else None
    for j, t in enumerate(cols):
        cc, hh, ll, sm = c[t].to_numpy(float), h[t].to_numpy(float), l[t].to_numpy(float), sma10[t].to_numpy(float)
        if np.isfinite(cc).sum() < 60:
            continue
        hh = np.where(np.isfinite(hh), hh, cc)
        ll = np.where(np.isfinite(ll), ll, cc)
        busy_until = -1
        for i in range(start, n):
            if i <= busy_until or not np.isfinite(cc[i]) or not np.isfinite(cc[i - 1]):
                continue
            if not (cc[i] > np.nanmax(cc[max(0, i - 4):i]) and cc[i] > cc[i - 1]):
                continue
            try:
                r = detect(hh[:i + 1], cc[:i + 1])
            except Exception:
                continue
            if not r or r["brk"] != i:
                continue
            wk = cc[i] / cc[i - 1] - 1
            rsv = rs_a[i, j] if rs_a is not None else np.nan
            strong = bool(wk >= 0.08 and np.isfinite(rsv) and rsv >= 0.6)
            ex, why = None, None
            for k in range(i + 1, n):
                trail = max(ll[i], sm[k] if np.isfinite(sm[k]) else -1)
                if np.isfinite(cc[k]) and cc[k] < trail:
                    ex, why = k, ("Stop-loss" if trail == ll[i] else "Trailing stop")
                    break
            busy_until = ex if ex is not None else n
            k_ = ex if ex is not None else n - 1
            while k_ > i and not np.isfinite(cc[k_]):
                k_ -= 1
            xg = (cc[k_] / cc[i] - 1) * 100
            # trade log: sym, entry week, entry, exit week, exit (or price now), gain, max gain, reason, weeks held, strong
            log.append([t[:-3], ds[i], round(float(cc[i]), 2), ds[ex] if ex is not None else None, round(float(cc[k_]), 2), round(float(xg), 1),
                        round(float((np.nanmax(cc[i:k_ + 1]) / cc[i] - 1) * 100), 1), why, int(k_ - i), strong])
            if ex is not None:
                g = (cc[ex] / cc[i] - 1) * 100
                exits[(t[:-3], ds[i])] = (ds[ex], round(float(cc[ex]), 2), round(float(g), 1), why,
                                         round(float((np.nanmax(cc[i:ex + 1]) / cc[i] - 1) * 100), 1))
                res["all"].append((g, why))
                if strong:
                    res["strong"].append((g, why))
            else:
                opened["all"] += 1
                if strong:
                    opened["strong"] += 1
    stats = {}
    for k, v in res.items():
        g = np.array([x[0] for x in v]) if v else np.array([0.0])
        stats[k] = {"n": len(v) + opened[k], "closed": len(v), "open": opened[k],
                    "win": round(float(np.mean(g > 0)) * 100) if v else None,
                    "avg_win": round(float(g[g > 0].mean()), 1) if v and (g > 0).any() else None,
                    "avg_loss": round(float(g[g <= 0].mean()), 1) if v and (g <= 0).any() else None,
                    "avg": round(float(g.mean()), 1) if v else None,
                    "sl_hit": round(float(np.mean([x[1] == "Stop-loss" for x in v])) * 100) if v else None,
                    "from": ds[start] if start < n else None}
    return stats, exits, log
