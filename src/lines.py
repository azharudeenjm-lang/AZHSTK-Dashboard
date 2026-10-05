"""Trend-line, support/resistance and DeMark TD-line conditions for the Screener.

Everything is checked on each of the last N bars (N = SCREENER_EVENT_BARS), so
the screener can ask "within the last 3 bars". Events are returned as
"bars ago" (0 = latest bar); states as 1.

Trend lines
  Four candidate lines per stock, each through two swing points and only kept
  if no close broke it before the recent window:
    falling resistance (lower highs)   rising resistance (higher highs)
    rising support (higher lows)       falling support (lower lows)
  "Rising" conditions use the rising lines, "falling" the falling lines,
  plain "trendline" any of the four.
  crossed above / below  close moved from one side of the line to the other
  touched above          low came within the touch zone, close stayed above
  touched below          high came within the touch zone, close stayed below
  bounced up / down      a touch followed by a higher / lower close

Support and resistance
  Horizontal levels from clustered swing highs and lows (2+ touches). A level
  is "resistance" if most of its touches were swing highs, otherwise
  "support", so a broken resistance is still called resistance when price
  comes back to test it from above. 2x / 3x touched = touched on 2 or 3
  separate bars within the window. Bull trap = crossed above resistance and
  closed back below within 5 bars; bear trap = the mirror image.

DeMark TD lines (levels 1-3)
  A TD point high is a high with that many lower highs on each side. The TD
  supply line joins the latest TD point high to the most recent earlier TD
  point high that is higher; the TD demand line does the same with lows.
  Upward breakout = close crosses above the supply line. Qualifiers:
    1  the bar before the breakout closed down
    2  the breakout bar opened above the line
    3  the close beat the prior close by more than the prior bar's
       distance from close to true low (demand-side pressure)
  Downward breakouts mirror these.
"""
import numpy as np
import pandas as pd

from .config import LEVEL_PARAMS, SCREENER_EVENT_BARS as NB
from .levels import _cluster, _pivots

TL_META = [
    ("tl_ab_rise", "Above rising trendline", "s"),
    ("tl_x_rise", "Price crossed above rising trendline", "e"),
    ("tl_x_any", "Price crossed above trendline", "e"),
    ("tl_x_fall", "Price crossed above falling trendline", "e"),
    ("tl_ta_rise", "Price touched rising trendline (from above)", "e"),
    ("tl_ta_any", "Price touched above trendline", "e"),
    ("tl_ta_fall", "Price touched falling trendline (from above)", "e"),
    ("tl_bu_rise", "Price bounced up from rising trendline", "e"),
    ("tl_bu_any", "Price bounced up from trendline", "e"),
    ("tl_bu_fall", "Price bounced up from falling trendline", "e"),
    ("tl_xd_fall", "Price crossed below falling trendline", "e"),
    ("tl_xd_any", "Price crossed below trendline", "e"),
    ("tl_xd_rise", "Price crossed below rising trendline", "e"),
    ("tl_tb_fall", "Price touched falling trendline (from below)", "e"),
    ("tl_tb_any", "Price touched below trendline", "e"),
    ("tl_tb_rise", "Price touched rising trendline (from below)", "e"),
    ("tl_bd_fall", "Price bounced down from falling trendline", "e"),
    ("tl_bd_rise", "Price bounced down from rising trendline", "e"),
    ("tl_bl_fall", "Below falling trendline", "s"),
]
SR_META = [
    ("sr_xa_res", "Price crossed above resistance", "e"),
    ("sr_xa_sup", "Price crossed above support", "e"),
    ("sr_tb_res", "Price touched below resistance", "e"),
    ("sr_tb_sup", "Price touched below support", "e"),
    ("sr_bd_res", "Price bounced down from resistance", "e"),
    ("sr_bd_sup", "Price bounced down from support", "e"),
    ("sr_xb_res", "Price crossed below resistance", "e"),
    ("sr_xb_sup", "Price crossed below support", "e"),
    ("sr_bu_res", "Price bounced up from resistance", "e"),
    ("sr_bu_sup", "Price bounced up from support", "e"),
    ("sr_ta_res", "Price touched above resistance", "e"),
    ("sr_ta_sup", "Price touched above support", "e"),
    ("sr_2ta_res", "Price 2x touched above resistance", "e"),
    ("sr_2ta_sup", "Price 2x touched above support", "e"),
    ("sr_2tb_res", "Price 2x touched below resistance", "e"),
    ("sr_2tb_sup", "Price 2x touched below support", "e"),
    ("sr_3ta_res", "Price 3x touched above resistance", "e"),
    ("sr_3ta_sup", "Price 3x touched above support", "e"),
    ("sr_3tb_res", "Price 3x touched below resistance", "e"),
    ("sr_3tb_sup", "Price 3x touched below support", "e"),
    ("bull_trap", "Bull trap (breakout failed within 5 bars)", "e"),
    ("bear_trap", "Bear trap (breakdown failed within 5 bars)", "e"),
]
TD_META = []
for _dir, _word in (("u", "Upward"), ("d", "Downward")):
    for _lv in (1, 2, 3):
        TD_META.append((f"td{_dir}{_lv}", f"TD-line level {_lv} {_word.lower()} breakout", "e"))
        for _q in (1, 2, 3):
            TD_META.append((f"td{_dir}{_lv}q{_q}", f"TD-line level {_lv} {_word.lower()} breakout, qualifier {_q} met", "e"))


def _line_through(piv, vals, c, n, tol, side, slope):
    """Best valid line through two swing points (most touches, then newest)."""
    piv = [i for i in piv if i < n - 1][-8:]
    best, end = None, max(0, n - NB)
    for x in range(len(piv)):
        for y in range(x + 1, len(piv)):
            a, b = piv[x], piv[y]
            va, vb = vals[a], vals[b]
            if slope == "up" and not vb > va * (1 + tol):
                continue
            if slope == "down" and not vb < va * (1 - tol):
                continue
            line = va + (vb - va) / (b - a) * (np.arange(n) - a)
            if line[-1] <= 0:
                continue
            seg = slice(a + 1, max(a + 1, end))
            if side == "res" and np.any(c[seg] > line[seg] * (1 + tol / 2)):
                continue
            if side == "sup" and np.any(c[seg] < line[seg] * (1 - tol / 2)):
                continue
            touches = sum(1 for i in piv if i >= a and abs(vals[i] - line[i]) <= line[i] * tol)
            if best is None or (touches, b) > best[0]:
                best = ((touches, b), line, a)
    return (best[1], best[2]) if best else None


def _events(c, h, l, L, tt, start):
    """Event arrays (bool) for one line over all bars from `start`."""
    n = len(c)
    e = {k: np.zeros(n, bool) for k in ("xu", "xd", "ta", "tb", "bu", "bd")}
    for t in range(max(start + 1, 1), n):
        e["xu"][t] = c[t] > L[t] and c[t - 1] <= L[t - 1]
        e["xd"][t] = c[t] < L[t] and c[t - 1] >= L[t - 1]
        e["ta"][t] = l[t] <= L[t] * (1 + tt) and c[t] > L[t]
        e["tb"][t] = h[t] >= L[t] * (1 - tt) and c[t] < L[t]
        e["bu"][t] = e["ta"][t - 1] and c[t] > c[t - 1] and c[t] > L[t]
        e["bd"][t] = e["tb"][t - 1] and c[t] < c[t - 1] and c[t] < L[t]
    return e


def _ago(arr):
    n = len(arr)
    for back in range(min(NB, n)):
        if arr[n - 1 - back]:
            return back
    return None


def _td(o, h, l, c, out):
    n = len(c)
    first = n - NB
    for lv in (1, 2, 3):
        hi_pts = [i for i in range(lv, n - lv) if all(h[i] > h[i - k] and h[i] > h[i + k] for k in range(1, lv + 1))]
        lo_pts = [i for i in range(lv, n - lv) if all(l[i] < l[i - k] and l[i] < l[i + k] for k in range(1, lv + 1))]
        for direction, pts, vals in (("u", hi_pts, h), ("d", lo_pts, l)):
            for t in range(max(first, 2), n):
                known = [p for p in pts if p + lv <= t - 1]       # confirmed before the breakout bar
                if len(known) < 2:
                    continue
                p2 = known[-1]
                p1 = next((p for p in reversed(known[:-1]) if (vals[p] > vals[p2] if direction == "u" else vals[p] < vals[p2])), None)
                if p1 is None:
                    continue
                m = (vals[p2] - vals[p1]) / (p2 - p1)
                line = lambda i: vals[p1] + m * (i - p1)
                if direction == "u":
                    hit = c[t] > line(t) and c[t - 1] <= line(t - 1)
                    q1 = c[t - 1] < c[t - 2]
                    q2 = o[t] > line(t)
                    q3 = c[t] > c[t - 1] + (c[t - 1] - min(l[t - 1], c[t - 2]))
                else:
                    hit = c[t] < line(t) and c[t - 1] >= line(t - 1)
                    q1 = c[t - 1] > c[t - 2]
                    q2 = o[t] < line(t)
                    q3 = c[t] < c[t - 1] - (max(h[t - 1], c[t - 2]) - c[t - 1])
                if hit:
                    ago = n - 1 - t
                    key = f"td{direction}{lv}"
                    out[key] = min(out.get(key, 99), ago)
                    for q, ok in ((1, q1), (2, q2), (3, q3)):
                        if ok:
                            out[f"{key}q{q}"] = min(out.get(f"{key}q{q}", 99), ago)


def analyze(o, h, l, c, p):
    """All trend-line, S/R and TD conditions for one stock (arrays, oldest first)."""
    n = len(c)
    out = {}
    if n < 40:
        return out
    price = c[-1]
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    tol = max(p["tol_min"], 0.5 * tr[-14:].mean() / price)
    tt = tol / 2                                 # touch zone: half the level tolerance
    k = p["pivot"]
    ph, pl = _pivots(h, k, True), _pivots(l, k, False)
    start = n - NB - 1

    # ---- trend lines ----
    lines = {}
    for name, piv, vals, side, slope in (("res_dn", ph, h, "res", "down"), ("res_up", ph, h, "res", "up"),
                                          ("sup_up", pl, l, "sup", "up"), ("sup_dn", pl, l, "sup", "down")):
        r = _line_through(piv, vals, c, n, tol, side, slope)
        if r:
            lines[name] = _events(c, h, l, r[0], tt, start), r[0]
    groups = {"rise": ("res_up", "sup_up"), "fall": ("res_dn", "sup_dn"), "any": ("res_up", "sup_up", "res_dn", "sup_dn")}
    for g, names in groups.items():
        for ev, key in (("xu", "x"), ("xd", "xd"), ("ta", "ta"), ("tb", "tb"), ("bu", "bu"), ("bd", "bd")):
            agos = [_ago(lines[nm][0][ev]) for nm in names if nm in lines]
            agos = [a for a in agos if a is not None]
            if agos:
                out[f"tl_{key}_{g}"] = min(agos)
    if "sup_up" in lines and price > lines["sup_up"][1][-1]:
        out["tl_ab_rise"] = 1
    if "res_dn" in lines and price < lines["res_dn"][1][-1]:
        out["tl_bl_fall"] = 1
    out.pop("tl_bd_any", None)                   # not in the list (bounced down from any line)

    # ---- support / resistance ----
    hi_set = set(ph)
    pts = [(h[i], i) for i in ph] + [(l[i], i) for i in pl]
    for lev, touches, last in _cluster(pts, tol):
        if not (0.85 * price <= lev <= 1.15 * price):
            continue
        members = [i for v, i in pts if abs(v / lev - 1) <= tol]
        kind = "res" if sum(1 for i in members if i in hi_set) * 2 >= len(members) else "sup"
        L = np.full(n, lev)
        e = _events(c, h, l, L, tt, start)
        for ev, key in (("xu", "xa"), ("xd", "xb"), ("ta", "ta"), ("tb", "tb"), ("bu", "bu"), ("bd", "bd")):
            a = _ago(e[ev])
            if a is not None:
                kk = f"sr_{key}_{kind}"
                out[kk] = min(out.get(kk, 99), a)
        for ev, key in (("ta", "ta"), ("tb", "tb")):
            hits = [t for t in range(n - NB, n) if e[ev][t]]
            sep = [t for i, t in enumerate(hits) if i == 0 or t - hits[i - 1] >= 2]
            for times in (2, 3):
                if len(sep) >= times:
                    kk = f"sr_{times}{key}_{kind}"
                    out[kk] = min(out.get(kk, 99), n - 1 - sep[-1])
        # traps
        for t in range(max(start + 1, 1), n):
            if kind == "res" and e["xu"][t]:
                back = next((u for u in range(t + 1, min(n, t + 6)) if c[u] < lev), None)
                if back is not None:
                    out["bull_trap"] = min(out.get("bull_trap", 99), n - 1 - back)
            if kind == "sup" and e["xd"][t]:
                back = next((u for u in range(t + 1, min(n, t + 6)) if c[u] > lev), None)
                if back is not None:
                    out["bear_trap"] = min(out.get("bear_trap", 99), n - 1 - back)

    # ---- DeMark TD lines ----
    _td(o, h, l, c, out)
    return {kk: v for kk, v in out.items() if v != 99}


def build_tf(o, h, l, c, tf):
    """o,h,l,c: wide frames (bars x tickers). Returns {ticker: {cond: value}}."""
    p = LEVEL_PARAMS[tf]
    o, h, l, c = (x.tail(p["lookback"]) for x in (o, h, l, c))
    res = {}
    for t in c.columns:
        cc = c[t].to_numpy(float)
        ok = ~np.isnan(cc)
        if ok.sum() < 40:
            continue
        f0 = int(np.argmax(ok))
        cc = pd.Series(cc[f0:]).ffill().to_numpy()
        hh = pd.Series(h[t].to_numpy(float)[f0:]).fillna(pd.Series(cc)).to_numpy()
        ll = pd.Series(l[t].to_numpy(float)[f0:]).fillna(pd.Series(cc)).to_numpy()
        oo = pd.Series(o[t].to_numpy(float)[f0:]).fillna(pd.Series(cc)).to_numpy()
        try:
            r = analyze(oo, hh, ll, cc, p)
        except Exception:
            r = {}
        if r:
            res[t] = r
    return res
