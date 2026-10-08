"""Automatic Elliott wave count for the Screener and the candle chart.

How the count is made (the same steps for every stock, on daily and weekly bars):
1. Swing points: a zigzag joins highs and lows; a new swing needs a reversal of
   at least X% (X follows the stock's own volatility: about 2.5 x its average
   daily range, 4-12% on daily bars, 7-20% on weekly bars). Three sizes are
   tried (smaller, normal, larger swings).
2. Wave labels: starting from a swing low (rise) or swing high (fall), the
   swings are labelled 1-2-3-4-5 and then A-B-C. The last label is the wave
   that is still in progress.
3. Elliott's rules must hold, otherwise that count is thrown away:
   - wave 2 never goes beyond the start of wave 1;
   - wave 3 goes past the end of wave 1 and is not the shortest of 1, 3 and 5;
   - wave 4 does not overlap wave 1's territory;
   - wave 5 goes past the end of wave 3 (no "truncated" fifths);
   - the A-B-C correction does not wipe out the whole 5-wave move.
4. Of all valid counts, the one with the most labelled waves wins (a larger
   swing size wins a tie). The latest bars are always part of the count.

Targets use the usual Fibonacci guides: wave 3 = 1.618 x wave 1 from the end of
wave 2; wave 5 = wave 1 from the end of wave 4; wave C = wave A from the end of B.
An automatic count is a guide, not a certainty: the chart shows the labels so
each count can be checked by eye, and the "invalid below/above" level says
where the count is proven wrong.
"""
import numpy as np

from .config import SCREENER_EVENT_BARS as NB

META = [
    ("ew_w2", "Rise: wave 2 pullback (wave 3 not yet confirmed)", "s"),
    ("ew_w3x", "Rise: wave 3 confirmed (closed above the wave 1 high)", "e"),
    ("ew_w3", "Rise: in wave 3 (usually the strongest leg)", "s"),
    ("ew_w4", "Rise: in wave 4 pullback (wave 5 still ahead)", "s"),
    ("ew_w5", "Rise: in wave 5 (late stage of the move)", "s"),
    ("ew_end", "Rise: 5 waves complete, A-B correction under way", "s"),
    ("ew_c", "Rise: in wave C of the correction (pullback may be ending)", "s"),
    ("ew_d3", "Fall: in falling wave 3", "s"),
    ("ew_d5", "Fall: in falling wave 5 (selling may be ending)", "s"),
    ("ew_dend", "Fall: 5 falling waves complete, rebound under way", "s"),
]
LABELS = ["0", "1", "2", "3", "4", "5", "A", "B", "C"]
# window = same number of bars the chart shows
P = {"d": {"win": 120, "k": 2.5, "lo": 0.04, "hi": 0.12},
     "w": {"win": 104, "k": 2.0, "lo": 0.07, "hi": 0.20}}


def zigzag(h, l, thr):
    """Swing points [(index, price, +1 high / -1 low)]; the last one is still forming."""
    n = len(h)
    piv = []
    trend = 0
    hi, hi_i, lo, lo_i = h[0], 0, l[0], 0
    cur = None
    for i in range(1, n):
        if trend == 0:
            if h[i] > hi:
                hi, hi_i = h[i], i
            if l[i] < lo:
                lo, lo_i = l[i], i
            if hi >= lo * (1 + thr):
                if lo_i < hi_i:
                    piv.append((lo_i, lo, -1))
                    trend, cur = 1, (hi_i, hi)
                else:
                    piv.append((hi_i, hi, 1))
                    trend, cur = -1, (lo_i, lo)
        elif trend == 1:
            if h[i] >= cur[1]:
                cur = (i, h[i])
            elif l[i] <= cur[1] * (1 - thr):
                piv.append((cur[0], cur[1], 1))
                trend, cur = -1, (i, l[i])
        else:
            if l[i] <= cur[1]:
                cur = (i, l[i])
            elif h[i] >= cur[1] * (1 + thr):
                piv.append((cur[0], cur[1], -1))
                trend, cur = 1, (i, h[i])
    if cur is not None:
        piv.append((cur[0], cur[1], trend))
    return piv


def _valid(v):
    """v: prices of points 0..k for a RISING count (a fall is passed in negated).
    The last point is the wave still in progress. Returns True if the rules hold."""
    k = len(v) - 1
    last = k
    L = lambda a, b: abs(v[b] - v[a])
    if k >= 2:
        if v[2] <= v[0] or v[1] <= v[0]:
            return False
    if k >= 3 and last > 3 and v[3] <= v[1]:          # completed wave 3 must pass wave 1
        return False
    if k >= 3 and last > 3 and L(2, 3) < 0.9 * L(0, 1):  # a completed wave 3 is not shorter than wave 1
        return False
    if k >= 4 and v[4] <= v[1]:                       # no overlap with wave 1
        return False
    if k >= 5 and last > 5:
        if v[5] <= v[3]:
            return False
        if L(2, 3) < L(0, 1) and L(2, 3) < L(4, 5):   # wave 3 never the shortest
            return False
    if k >= 6 and v[6] <= v[0] + 0.0 * v[0]:          # correction keeps the start of wave 1
        return False
    if k >= 7 and (v[7] >= v[5] or v[7] <= v[6]):
        return False
    if k >= 8 and v[8] <= v[0]:
        return False
    return True


def _count(piv, n, win):
    """Best count over these swing points. Returns (direction, start position) or None."""
    best = None
    first = n - win
    for s in range(len(piv)):
        m = len(piv) - s
        if m < 3 or m > 9 or piv[s][0] < first:
            continue
        typ = piv[s][2]
        if typ == 0:
            continue
        vals = [p[1] for p in piv[s:]]
        if typ == -1:
            ok, d = _valid(vals), "up"
        else:
            ok, d = _valid([-x for x in vals]), "down"
        if ok and (best is None or m > best[2]):
            best = (d, s, m)
    return best


def _first_cross(c, level, start, up=True):
    """Bars ago of the first close beyond `level` after index `start` (within the event window)."""
    n = len(c)
    for i in range(max(start + 1, 1), n):
        if (up and c[i] > level and c[i - 1] <= level) or (not up and c[i] < level and c[i - 1] >= level):
            ago = n - 1 - i
            return ago if ago < NB else None
    return None


def analyse(h, l, c, tf):
    """One stock. Returns (conditions {id: value}, levels {id: price}, geometry or None)."""
    p = P[tf]
    n = len(c)
    if n < 40:
        return {}, {}, None
    w = min(n, p["win"])
    h, l, c = h[-w:], l[-w:], c[-w:]
    n = w
    rng = np.nanmedian((h[-60:] - l[-60:]) / c[-60:])
    if not np.isfinite(rng) or rng <= 0:
        return {}, {}, None
    base = float(np.clip(p["k"] * rng, p["lo"], p["hi"]))
    best = None
    for thr in (base * 0.75, base, base * 1.35):
        piv = zigzag(h, l, thr)
        r = _count(piv, n, w)
        if r and (best is None or r[2] > best[2] or (r[2] == best[2])):
            best = (r[0], piv[r[1]:], r[2], thr)
    if not best:
        return {}, {}, None
    d, pts, m, thr = best
    up = d == "up"
    v = [x[1] for x in pts]
    ix = [x[0] for x in pts]
    lab = LABELS[m - 1]
    price = c[-1]
    sgn = 1 if up else -1
    ln = lambda a, b: abs(v[b] - v[a])
    out, lv = {}, {}
    tgt = inv = None

    def ext(base, length, ratios, rising=True):
        """First Fibonacci projection still ahead of the current price."""
        for r in ratios:
            t = base + r * length if rising else base - r * length
            if (rising and t > price) or (not rising and t < price):
                return t
        return base + ratios[-1] * length if rising else base - ratios[-1] * length
    state = ""
    if up:
        if lab == "2" or (lab == "3" and price <= v[1]):
            out["ew_w2"] = 1
            tgt, inv = ext(v[2], ln(0, 1), (1.618, 2.618)), v[0]
            state = "wave 2 pullback; wave 3 is confirmed above the wave 1 high ₹%s" % _f(v[1])
            lv["ew_w2"] = v[1]
        elif lab == "3":
            out["ew_w3"] = 1
            tgt, inv = ext(v[2], ln(0, 1), (1.618, 2.618, 4.236)), v[1]
            lv["ew_w3"] = tgt
            x = _first_cross(c, v[1], ix[2])
            if x is not None:
                out["ew_w3x"], lv["ew_w3x"] = x, v[1]
            state = "in wave 3"
        elif lab == "4":
            out["ew_w4"] = 1
            tgt, inv = ext(v[4], ln(0, 1), (1.0, 1.618)), v[1]
            lv["ew_w4"] = v[3] - 0.382 * ln(2, 3)
            state = "in wave 4 pullback; the usual zone is ₹%s (38.2%% of wave 3)" % _f(lv["ew_w4"])
        elif lab == "5":
            out["ew_w5"] = 1
            tgt, inv = ext(v[4], ln(0, 1), (1.0, 1.618, 2.618)), v[4]
            lv["ew_w5"] = tgt
            state = "in wave 5 (late stage)"
        elif lab in ("A", "B"):
            out["ew_end"] = 1
            tgt = (v[7] if lab == "B" else v[5]) - ln(5, 6)
            inv = v[5]
            lv["ew_end"] = tgt
            state = "5 waves up complete; correction wave %s" % lab
        elif lab == "C":
            out["ew_c"] = 1
            tgt, inv = v[7] - ln(5, 6), v[0]
            lv["ew_c"] = tgt
            state = "in wave C of the correction"
    else:
        if lab == "3" and price < v[1]:
            out["ew_d3"] = 1
            tgt, inv = ext(v[2], ln(0, 1), (1.618, 2.618, 4.236), False), v[1]
            lv["ew_d3"] = tgt
            state = "in falling wave 3"
        elif lab == "5":
            out["ew_d5"] = 1
            tgt, inv = ext(v[4], ln(0, 1), (1.0, 1.618, 2.618), False), v[4]
            lv["ew_d5"] = tgt
            state = "in falling wave 5"
        elif lab in ("A", "B"):
            out["ew_dend"] = 1
            tgt = (v[7] if lab == "B" else v[5]) + ln(5, 6)
            inv = v[5]
            lv["ew_dend"] = tgt
            state = "5 waves down complete; rebound wave %s" % lab
        elif lab == "2" or lab == "3":
            state = "falling wave %s" % ("2 bounce" if lab == "2" else "3, not yet below the wave 1 low")
            tgt, inv = v[2] - 1.618 * ln(0, 1), v[0]
        elif lab == "4":
            state = "falling wave 4 bounce"
            tgt, inv = price - ln(0, 1), v[1]
        elif lab == "C":
            state = "wave C of the rebound"
            tgt, inv = v[7] + ln(5, 6), v[0]
    geo = {"d": d, "s": state, "pts": [[int(n - 1 - i), float(f"{x:.4g}"), LABELS[j]] for j, (i, x) in enumerate(zip(ix, v))],
           "tg": float(f"{tgt:.4g}") if tgt is not None and np.isfinite(tgt) and tgt > 0 else None,
           "iv": float(f"{inv:.4g}") if inv is not None and np.isfinite(inv) else None}
    lv = {k: float(f"{x:.4g}") for k, x in lv.items() if k in out and np.isfinite(x)}
    return out, lv, geo


def _f(x):
    return f"{x:,.2f}" if x < 100 else f"{x:,.0f}"


def build_tf(h, l, c, tf):
    """All stocks for one timeframe. Returns ({t: row with _v}, {t: geometry})."""
    rows, geos = {}, {}
    w = P[tf]["win"]
    H, Lw, C = (x.tail(w) for x in (h, l, c))
    for t in C.columns:
        cc = C[t].to_numpy(float)
        ok = ~np.isnan(cc)
        if ok.sum() < 40:
            continue
        f0 = int(np.argmax(ok))
        cc = cc[f0:]
        hh = H[t].to_numpy(float)[f0:]
        ll = Lw[t].to_numpy(float)[f0:]
        hh = np.where(np.isnan(hh), cc, hh)
        ll = np.where(np.isnan(ll), cc, ll)
        if np.isnan(cc).any():
            continue
        try:
            o, lv, g = analyse(hh, ll, cc, tf)
        except Exception:
            continue
        if g:
            # chart bars count from the latest bar; stocks with a short history start later
            geos[t] = g
        if o:
            if lv:
                o["_v"] = lv
            rows[t] = o
    return rows, geos
