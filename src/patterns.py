"""Channels, bands and chart patterns for the Screener.

Channels and bands (standard settings, in bars of the chosen timeframe)
  Bollinger 20, 2 SD     Keltner EMA 20 +/- 2 x ATR 10     Donchian 20 and 55
  STARC SMA 6 +/- 2 x ATR 15     TTM squeeze (Bollinger inside Keltner)
  Darvas box (top after a new 52-week high holds 3 bars, then a bottom holds 3 bars)
  NSE circuit limits (daily only, needs NSE's price-band list)

Chart patterns (found from swing points; every pattern's lines are also drawn
on the stock's candle chart so it can be checked by eye)
  Triangles (ascending / descending / symmetrical), wedges (rising / falling),
  price channels (rising / falling / sideways), bull and bear flags,
  double bottom / top, head and shoulders and inverse head and shoulders.
  Each has a "forming" state (price still inside) and breakout / breakdown
  events (close through the line, within the last N bars).
"""
import numpy as np
import pandas as pd

from .config import SCREENER_EVENT_BARS as NB

# ---------------------------------------------------------------- metadata
BAND_META = [
    ("bb_ab", "Close above the upper Bollinger band (20, 2)", "s"),
    ("bb_xa", "Crossed above the upper Bollinger band", "e"),
    ("bb_xb", "Crossed below the lower Bollinger band", "e"),
    ("bb_in", "Closed back inside, above the lower Bollinger band", "e"),
    ("kc_ab", "Close above the upper Keltner channel (20, 2 ATR)", "s"),
    ("kc_xa", "Crossed above the upper Keltner channel", "e"),
    ("kc_lo", "Touched the lower Keltner channel and closed above it", "e"),
    ("kc_bl", "Close below the lower Keltner channel", "s"),
    ("ttm_on", "TTM squeeze on (Bollinger bands inside Keltner)", "s"),
    ("ttm_up", "TTM squeeze fired upward", "e"),
    ("dc20_u", "Donchian 20 breakout (close above prior 20-bar high)", "e"),
    ("dc20_d", "Donchian 20 breakdown (close below prior 20-bar low)", "e"),
    ("dc55_u", "Donchian 55 breakout (close above prior 55-bar high)", "e"),
    ("dc55_d", "Donchian 55 breakdown (close below prior 55-bar low)", "e"),
    ("starc_hi", "Touched the upper STARC band (stretched)", "e"),
    ("starc_lo", "Touched the lower STARC band (stretched down)", "e"),
    ("darv_in", "Inside a Darvas box", "s"),
    ("darv_u", "Darvas box breakout", "e"),
    ("darv_d", "Darvas box breakdown", "e"),
    ("circ_up", "Hit the upper circuit limit", "e"),
    ("circ_dn", "Hit the lower circuit limit", "e"),
]
PAT_NAMES = {
    "at": "Ascending triangle", "dt": "Descending triangle", "st": "Symmetrical triangle",
    "rw": "Rising wedge", "fw": "Falling wedge",
    "ac": "Rising channel", "dc": "Falling channel", "hc": "Sideways channel (rectangle)",
}
PAT_META = []
for _k, _n in PAT_NAMES.items():
    PAT_META += [(f"pt_{_k}_f", f"{_n} forming", "s"),
                 (f"pt_{_k}_u", f"{_n}: breakout up", "e"),
                 (f"pt_{_k}_d", f"{_n}: breakdown", "e")]
PAT_META += [
    ("pt_bf_f", "Bull flag forming", "s"), ("pt_bf_u", "Bull flag breakout", "e"),
    ("pt_ef_f", "Bear flag forming", "s"), ("pt_ef_d", "Bear flag breakdown", "e"),
    ("pt_db_f", "Double bottom formed (below neckline)", "s"), ("pt_db_u", "Double bottom breakout", "e"),
    ("pt_dt2_f", "Double top formed (above neckline)", "s"), ("pt_dt2_d", "Double top breakdown", "e"),
    ("pt_hs_f", "Head and shoulders formed (above neckline)", "s"), ("pt_hs_d", "Head and shoulders breakdown", "e"),
    ("pt_ih_f", "Inverse head and shoulders formed (below neckline)", "s"), ("pt_ih_u", "Inverse head and shoulders breakout", "e"),
]

# per-timeframe settings
P = {
    "d": {"height": 0.06, "win": 100, "piv": 3, "span": 15, "flat": 0.06, "fit": 0.025, "buf": 0.01, "recent": 25, "pole": 0.15, "pole_len": 10,
          "flag": (3, 15), "dbl_gap": 10, "dbl_tol": 0.03, "dbl_peak": 0.08, "hs_sh": 0.05, "darv": 250},
    "w": {"height": 0.10, "win": 52, "piv": 2, "span": 8, "flat": 0.25, "fit": 0.045, "buf": 0.02, "recent": 10, "pole": 0.20, "pole_len": 6,
          "flag": (2, 8), "dbl_gap": 4, "dbl_tol": 0.04, "dbl_peak": 0.12, "hs_sh": 0.07, "darv": 52},
}


def _cross_up(a, b):
    return (a > b) & (a.shift() <= b.shift())


def _w(df, n):
    return df.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


# ------------------------------------------------------------ bands (all stocks at once)
def add_bands(S, E, o, h, l, c, tf, circuit=None):
    """Adds band/channel conditions to S (last-bar states) and E (event frames)."""
    pc = c.shift()
    tr = np.maximum(np.maximum(h - l, (h - pc).abs()), (l - pc).abs())
    m20, sd = c.rolling(20).mean(), c.rolling(20).std()
    bu, bl = m20 + 2 * sd, m20 - 2 * sd
    S["bb_ab"] = (c > bu).iloc[-1]
    E["bb_xa"] = _cross_up(c, bu)
    E["bb_xb"] = _cross_up(bl, c)
    E["bb_in"] = _cross_up(c, bl)
    e20, atr10 = c.ewm(span=20, adjust=False, min_periods=20).mean(), _w(tr, 10)
    ku, kl = e20 + 2 * atr10, e20 - 2 * atr10
    S["kc_ab"] = (c > ku).iloc[-1]
    E["kc_xa"] = _cross_up(c, ku)
    E["kc_lo"] = (l <= kl) & (c > kl) & (pc > kl.shift())
    S["kc_bl"] = (c < kl).iloc[-1]
    sq = (bu < ku) & (bl > kl)
    S["ttm_on"] = sq.iloc[-1]
    E["ttm_up"] = sq.shift().fillna(False).astype(bool) & ~sq & (c > m20)
    for n_ in (20, 55):
        hh, ll = h.rolling(n_, min_periods=n_).max().shift(), l.rolling(n_, min_periods=n_).min().shift()
        E[f"dc{n_}_u"] = (c > hh) & (pc <= hh.shift())
        E[f"dc{n_}_d"] = (c < ll) & (pc >= ll.shift())
    s6, atr15 = c.rolling(6).mean(), _w(tr, 15)
    E["starc_hi"] = h >= s6 + 2 * atr15
    E["starc_lo"] = l <= s6 - 2 * atr15
    if tf == "d" and circuit:
        band = pd.Series({t: circuit.get(t[:-3]) for t in c.columns}, dtype=float)
        chg = (c / pc - 1) * 100
        lim = band.reindex(c.columns)
        E["circ_up"] = (chg >= lim - 0.1) & (c >= h * 0.999)
        E["circ_dn"] = (chg <= -(lim - 0.1)) & (c <= l * 1.001)


def darvas(h, l, c, lookback):
    """Darvas box for one stock. Returns ({cond: value}, {key: level}) or ({}, {})."""
    n = len(c)
    if n < 40:
        return {}, {}
    nh = np.zeros(n, bool)
    for i in range(1, n):
        lo = max(0, i - lookback)
        if i - lo >= min(lookback, n) * 0.6 and h[i] >= np.nanmax(h[lo:i]):
            nh[i] = True
    top = bot = None
    state, top_i, cand_b = "none", None, None
    events = []
    for i in range(n):
        if state == "boxed" and (c[i] > top or c[i] < bot):
            events.append(("u" if c[i] > top else "d", i, top if c[i] > top else bot))
            state = "none"
            if c[i] <= top or not nh[i]:
                continue
        if state in ("none", "boxed") and nh[i]:
            state, top, top_i, bot, cand_b = "top", h[i], i, None, None
            continue
        if state == "top":
            if h[i] > top:
                top, top_i = h[i], i
            elif i - top_i >= 3:
                state, cand_b = "bottom", (np.nanmin(l[top_i:i + 1]), i)
            continue
        if state == "bottom":
            if h[i] > top:
                state, top, top_i = "top", h[i], i
                continue
            if l[i] < cand_b[0]:
                cand_b = (l[i], i)
            elif i - cand_b[1] >= 3:
                state, bot = "boxed", cand_b[0]
            continue
    out, lv = {}, {}
    for kind, i, level in events:
        ago = n - 1 - i
        if ago < NB:
            key = "darv_u" if kind == "u" else "darv_d"
            if ago < out.get(key, 99):
                out[key], lv[key] = ago, level
    if state == "boxed":
        out["darv_in"], lv["darv_in"] = 1, top
    return out, lv


# ------------------------------------------------------------ chart patterns (per stock)
def _pivots(a, k, high):
    n, out = len(a), []
    for i in range(k, n - k):
        w = a[i - k:i + k + 1]
        if np.isnan(a[i]):
            continue
        if (a[i] >= np.nanmax(w)) if high else (a[i] <= np.nanmin(w)):
            if not out or i - out[-1] > k:
                out.append(i)
    return out


def _fit(idx, vals):
    x, y = np.asarray(idx, float), np.asarray(vals, float)
    if len(x) == 2:
        m = (y[1] - y[0]) / (x[1] - x[0])
        return m, y[0] - m * x[0]
    m, b = np.polyfit(x, y, 1)
    return m, b


def _lines_pattern(h, l, c, p):
    """Triangles, wedges and channels. Returns (key, upper(m,b), lower(m,b), start) or None."""
    n = len(c)
    k, w = p["piv"], p["win"]
    lo0 = max(0, n - w)
    ph = [i for i in _pivots(h, k, True) if i >= lo0 and i < n - 1]
    pl = [i for i in _pivots(l, k, False) if i >= lo0 and i < n - 1]
    ph, pl = ph[-4:], pl[-4:]
    if len(ph) < 2 or len(pl) < 2:
        return None
    start = min(ph[0], pl[0])
    if (n - 1) - start < p["span"] or max(ph[-1], pl[-1]) - start < p["span"] * 0.6:
        return None
    mu, bu_ = _fit(ph, h[ph])
    ml, bl_ = _fit(pl, l[pl])
    U = lambda i: mu * i + bu_
    L = lambda i: ml * i + bl_
    price = c[-1]
    # each swing point must sit close to its line
    if max(abs(h[i] / U(i) - 1) for i in ph) > p["fit"] or max(abs(l[i] / L(i) - 1) for i in pl) > p["fit"]:
        return None
    if U(start) <= L(start) or U(n - 1) <= L(n - 1) * 1.005:     # lines have not met yet
        return None
    if len(ph) + len(pl) < 5:                                     # at least 3 touches on one line
        return None
    if (U(start) - L(start)) / price < p["height"]:               # pattern tall enough to matter
        return None
    # price stayed inside the lines (small tolerance) until the event window
    end = max(start + 1, n - NB)
    tol = p["fit"] / 2
    for i in range(start, end):
        if c[i] > U(i) * (1 + tol) or c[i] < L(i) * (1 - tol):
            return None
    su, sl = mu / price * 100, ml / price * 100        # % per bar
    f = p["flat"]
    flat_u, flat_l = abs(su) <= f, abs(sl) <= f
    w0, w1 = U(start) - L(start), U(n - 1) - L(n - 1)
    converging = w1 < w0 * 0.85
    key = None
    if flat_u and flat_l:
        key = "hc"
    elif flat_u and sl > f and converging:
        key = "at"
    elif flat_l and su < -f and converging:
        key = "dt"
    elif su < -f and sl > f and converging:
        key = "st"
    elif su > f and sl > f:
        if converging and sl > su:
            key = "rw"
        elif abs(su - sl) <= 0.35 * max(abs(su), abs(sl)):
            key = "ac"
    elif su < -f and sl < -f:
        if converging and su < sl:
            key = "fw"
        elif abs(su - sl) <= 0.35 * max(abs(su), abs(sl)):
            key = "dc"
    if not key:
        return None
    return key, (mu, bu_), (ml, bl_), start, h[ph[-1]], l[pl[-1]]


def _flag(h, l, c, p, bull=True):
    """Bull (or bear) flag: a sharp pole, then a tight drift against it."""
    n = len(c)
    fmin, fmax = p["flag"]
    best = None
    for top in range(n - 1 - fmin, max(p["pole_len"], n - 1 - fmax - NB), -1):
        seg = slice(max(0, top - p["pole_len"]), top + 1)
        if bull:
            base = np.nanmin(l[seg])
            pole = h[top] / base - 1
            if pole < p["pole"] or h[top] < np.nanmax(h[seg]):
                continue
        else:
            base = np.nanmax(h[seg])
            pole = 1 - l[top] / base
            if pole < p["pole"] or l[top] > np.nanmin(l[seg]):
                continue
        # flag = bars after the pole tip, before any breakout
        fl = top + 1
        brk = None
        hi_f = lo_f = None
        for i in range(fl, n):
            hi_f = np.nanmax(h[fl:i + 1]) if hi_f is None else max(hi_f, h[i])
            lo_f = np.nanmin(l[fl:i + 1]) if lo_f is None else min(lo_f, l[i])
            if i - fl + 1 >= fmin and brk is None:
                if bull and c[i] > np.nanmax(h[fl:i]) and i - fl >= fmin:
                    brk = i
                if not bull and c[i] < np.nanmin(l[fl:i]) and i - fl >= fmin:
                    brk = i
            if brk is not None:
                break
        stop = brk if brk is not None else n
        flen = stop - fl
        if flen < fmin or flen > fmax:
            continue
        fh, flo = np.nanmax(h[fl:stop]), np.nanmin(l[fl:stop])
        height = (h[top] - base) if bull else (base - l[top])
        if bull and (fh > h[top] * 1.005 or h[top] - flo > 0.5 * height):
            continue
        if not bull and (flo < l[top] * 0.995 or fh - l[top] > 0.5 * height):
            continue
        slope = np.polyfit(np.arange(flen), c[fl:stop], 1)[0] / c[top] * 100
        if (bull and slope > 0.15) or (not bull and slope < -0.15):
            continue
        best = (top, fl, stop, brk, fh, flo, base)
        break
    return best


def _double(h, l, c, p, bottom=True):
    n = len(c)
    k = p["piv"]
    piv = _pivots(l, k, False) if bottom else _pivots(h, k, True)
    piv = [i for i in piv if i >= n - p["win"]]
    if len(piv) < 2:
        return None
    a, b = piv[-2], piv[-1]
    if b - a < p["dbl_gap"] or (n - 1) - b > p["recent"]:
        return None
    va, vb = (l[a], l[b]) if bottom else (h[a], h[b])
    if abs(vb / va - 1) > p["dbl_tol"]:
        return None
    if bottom:
        neck = np.nanmax(h[a:b + 1])
        if neck < max(va, vb) * (1 + p["dbl_peak"]):
            return None
    else:
        neck = np.nanmin(l[a:b + 1])
        if neck > min(va, vb) * (1 - p["dbl_peak"]):
            return None
    return a, b, neck


def _hs(h, l, c, p, inverse=False):
    n = len(c)
    k = p["piv"]
    arr = l if inverse else h
    piv = [i for i in _pivots(arr, k, not inverse) if i >= n - p["win"]]
    if len(piv) < 3:
        return None
    A, B, C = piv[-3:]
    if (n - 1) - C > p["recent"] or B - A < p["piv"] * 2 or C - B < p["piv"] * 2:
        return None
    va, vb, vc = arr[A], arr[B], arr[C]
    if not inverse and not (vb > va * 1.03 and vb > vc * 1.03):
        return None
    if inverse and not (vb < va * 0.97 and vb < vc * 0.97):
        return None
    if abs(vc / va - 1) > p["hs_sh"]:
        return None
    if inverse:
        t1, t2 = A + int(np.nanargmax(h[A:B + 1])), B + int(np.nanargmax(h[B:C + 1]))
        n1, n2 = h[t1], h[t2]
    else:
        t1, t2 = A + int(np.nanargmin(l[A:B + 1])), B + int(np.nanargmin(l[B:C + 1]))
        n1, n2 = l[t1], l[t2]
    if t2 == t1:
        return None
    m = (n2 - n1) / (t2 - t1)
    return (A, B, C), (t1, n1, m)


def _seg(i0, v0, i1, v1, n):
    """A line segment as [bars-ago start, value, bars-ago end, value] for the chart."""
    return [int(n - 1 - i0), float(f"{v0:.4g}"), int(n - 1 - i1), float(f"{v1:.4g}")]


def chart_patterns(o, h, l, c, tf):
    """Returns ({cond: value}, {cond: level}, geometry or None) for one stock."""
    p = P[tf]
    n = len(c)
    out, lv, geo = {}, {}, []
    if n < 40:
        return out, lv, geo

    def ago_first(cond):
        for i in range(max(1, n - NB), n):
            if cond(i):
                return n - 1 - i
        return None

    # triangles, wedges, channels
    r = _lines_pattern(h, l, c, p)
    if r:
        key, (mu, bu_), (ml, bl_), start, last_hi, last_lo = r
        U = lambda i: mu * i + bu_
        L = lambda i: ml * i + bl_
        bf = p["buf"]
        # a breakout must clear the line AND the last swing point on that side
        # (near the apex the line alone is too close to price to mean much)
        UP = lambda i: max(U(i) * (1 + bf), last_hi)
        DN = lambda i: min(L(i) * (1 - bf), last_lo)
        up = ago_first(lambda i: c[i] > UP(i) and c[i - 1] <= UP(i - 1))
        dn = ago_first(lambda i: c[i] < DN(i) and c[i - 1] >= DN(i - 1))
        if up is not None:
            out[f"pt_{key}_u"], lv[f"pt_{key}_u"] = up, U(n - 1 - up)
        if dn is not None:
            out[f"pt_{key}_d"], lv[f"pt_{key}_d"] = dn, L(n - 1 - dn)
        if up is None and dn is None and DN(n - 1) <= c[-1] <= UP(n - 1):
            out[f"pt_{key}_f"], lv[f"pt_{key}_f"] = 1, U(n - 1)
        geo.append({"k": f"pt_{key}", "name": PAT_NAMES[key],
               "lines": [_seg(start, U(start), n - 1, U(n - 1), n), _seg(start, L(start), n - 1, L(n - 1), n)]})

    # flags
    for bull in (True, False):
        f = _flag(h, l, c, p, bull)
        if not f:
            continue
        top, fl, stop, brk, fh, flo, base = f
        k_ = "bf" if bull else "ef"
        if brk is not None:
            a = n - 1 - brk
            if a < NB:
                out[f"pt_{k_}_{'u' if bull else 'd'}"] = a
                lv[f"pt_{k_}_{'u' if bull else 'd'}"] = fh if bull else flo
        else:
            out[f"pt_{k_}_f"], lv[f"pt_{k_}_f"] = 1, (fh if bull else flo)
        if True:
            tip = h[top] if bull else l[top]
            pole_start = int(np.nanargmin(l[max(0, top - p["pole_len"]):top + 1]) if bull
                             else np.nanargmax(h[max(0, top - p["pole_len"]):top + 1])) + max(0, top - p["pole_len"])
            end = (brk if brk is not None else n - 1)
            geo.append({"k": f"pt_{k_}", "name": "Bull flag" if bull else "Bear flag",
                   "lines": [_seg(pole_start, base, top, tip, n),
                             _seg(fl, fh, end, fh, n), _seg(fl, flo, end, flo, n)]})

    # double bottom / top
    for bottom in (True, False):
        d = _double(h, l, c, p, bottom)
        if not d:
            continue
        a, b, neck = d
        k_ = "db" if bottom else "dt2"
        if bottom:
            ev = ago_first(lambda i: i > b and c[i] > neck and c[i - 1] <= neck)
            if ev is not None:
                out["pt_db_u"], lv["pt_db_u"] = ev, neck
            elif c[-1] < neck and c[-1] > min(l[a], l[b]) * 0.97 and c[-1] >= neck * 0.9:
                out["pt_db_f"], lv["pt_db_f"] = 1, neck
        else:
            ev = ago_first(lambda i: i > b and c[i] < neck and c[i - 1] >= neck)
            if ev is not None:
                out["pt_dt2_d"], lv["pt_dt2_d"] = ev, neck
            elif c[-1] > neck and c[-1] < max(h[a], h[b]) * 1.03 and c[-1] <= neck * 1.1:
                out["pt_dt2_f"], lv["pt_dt2_f"] = 1, neck
        if f"pt_{k_}_u" in out or f"pt_{k_}_d" in out or f"pt_{k_}_f" in out:
            va, vb = (l[a], l[b]) if bottom else (h[a], h[b])
            geo.append({"k": f"pt_{k_}", "name": "Double bottom" if bottom else "Double top",
                   "lines": [_seg(a, va, b, vb, n), _seg(a, neck, n - 1, neck, n)]})

    # head and shoulders / inverse
    for inverse in (False, True):
        s = _hs(h, l, c, p, inverse)
        if not s:
            continue
        (A, B, C), (t1, n1, m) = s
        N = lambda i: n1 + m * (i - t1)
        k_ = "ih" if inverse else "hs"
        if inverse:
            ev = ago_first(lambda i: i > C and c[i] > N(i) and c[i - 1] <= N(i - 1))
            if ev is not None:
                out["pt_ih_u"], lv["pt_ih_u"] = ev, N(n - 1 - ev)
            elif N(n - 1) * 0.94 <= c[-1] < N(n - 1):
                out["pt_ih_f"], lv["pt_ih_f"] = 1, N(n - 1)
        else:
            ev = ago_first(lambda i: i > C and c[i] < N(i) and c[i - 1] >= N(i - 1))
            if ev is not None:
                out["pt_hs_d"], lv["pt_hs_d"] = ev, N(n - 1 - ev)
            elif N(n - 1) < c[-1] <= N(n - 1) * 1.06:
                out["pt_hs_f"], lv["pt_hs_f"] = 1, N(n - 1)
        if any(x.startswith(f"pt_{k_}_") for x in out):
            arr = l if inverse else h
            geo.append({"k": f"pt_{k_}", "name": "Inverse head and shoulders" if inverse else "Head and shoulders",
                   "lines": [_seg(A, arr[A], B, arr[B], n), _seg(B, arr[B], C, arr[C], n),
                             _seg(A, N(A), n - 1, N(n - 1), n)]})
    geo = [g for g in geo if any(k_.startswith(g["k"] + "_") for k_ in out)]
    lv = {k_: float(f"{v:.4g}") for k_, v in lv.items() if k_ in out and np.isfinite(v)}
    return out, lv, geo


def build_tf(o, h, l, c, tf, lookback):
    """Darvas + chart patterns for every stock. Returns ({t: row}, {t: geometry})."""
    rows, geos = {}, {}
    p = P[tf]
    tail = max(p["darv"] + 40, p["win"] + 20)
    o, h, l, c = (x.tail(tail) for x in (o, h, l, c))
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
        row, lv = {}, {}
        try:
            d, dl = darvas(hh, ll, cc, p["darv"])
            row.update(d); lv.update(dl)
            # chart patterns use only the pattern window
            w = min(len(cc), p["win"] + 10)
            pr, plv, geo = chart_patterns(oo[-w:], hh[-w:], ll[-w:], cc[-w:], tf)
            row.update(pr); lv.update(plv)
            if geo:
                geos[t] = geo
        except Exception:
            continue
        if row:
            if lv:
                row["_v"] = {k_: float(f"{v:.4g}") for k_, v in lv.items() if np.isfinite(v)}
            rows[t] = row
    return rows, geos
