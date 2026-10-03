"""Fibonacci retracements and extension targets on the latest upswing.

Swing:  the highest high in the lookback window (H) and the lowest low
        before it (A). The swing must be at least `min_move` (10% daily,
        15% weekly) or the stock gets no Fibonacci setup.
Levels: retracements 23.6 / 38.2 / 50 / 61.8 / 78.6 % of A->H.
Status: Breakout (at or above H), Shallow (<38.2%), 38-50%, Golden pocket
        (50-61.8%), Deep (61.8-78.6%), Very deep (>78.6%), Failed (below A).
Targets:
  breakout  -> extensions of A->H from A: 127.2%, 161.8%, 200%
  pullback  -> T1 = retest of H, T2/T3 = 100% / 161.8% of the swing projected
               from the pullback low C (only once price has turned up from C)
"""
import numpy as np
import pandas as pd

from .config import FIB, WEEKLY_LIVE
from .zones import weekly_bars

RET = [0.236, 0.382, 0.5, 0.618, 0.786]


def analyze(h, l, c, p, supports=()):
    n = len(c)
    L = min(p["lookback"], n)
    if L < 20:
        return None
    hh, ll, cc = h[-L:], l[-L:], c[-L:]
    hi_i = int(np.nanargmax(hh))
    if hi_i < 2:
        return None
    lo_i = int(np.nanargmin(ll[:hi_i + 1]))
    H, A = float(hh[hi_i]), float(ll[lo_i])
    if not (A > 0 and H / A - 1 >= p["min_move"]):
        return None
    price, rng = float(cc[-1]), H - A
    levels = {f"{int(f*1000)/10:g}": round(H - rng * f, 2) for f in RET}
    r = (H - price) / rng
    after = ll[hi_i + 1:] if hi_i < L - 1 else np.array([])
    C = float(np.nanmin(after)) if len(after) else None
    ago = L - 1 - hi_i

    if price < A:
        status = "Failed"
    elif price >= H * 0.99 and ago <= 2:
        status = "Breakout"
    elif r < 0.382:
        status = "Shallow"
    elif r < 0.5:
        status = "38–50%"
    elif r <= 0.618 + 0.02:
        status = "Golden pocket"
    elif r <= 0.786:
        status = "Deep"
    else:
        status = "Very deep"

    targets = []
    if status == "Breakout":
        targets = [("127.2% ext", A + rng * 1.272), ("161.8% ext", A + rng * 1.618), ("200% ext", A + rng * 2.0)]
    elif status != "Failed":
        targets = [("Prior high", H)]
        if C and price >= C * 1.03:        # turned up from the pullback low
            targets += [("100% projection", C + rng), ("161.8% projection", C + rng * 1.618)]
    targets = [{"k": k, "p": round(v, 2), "up": round((v / price - 1) * 100, 1)} for k, v in targets if v > price]

    conf = []
    for name, lv in levels.items():
        for sname, sp in supports:
            if sp and abs(lv / sp - 1) <= FIB["confluence"]:
                conf.append(f"{name}% ≈ {sname}")
    return {"A": round(A, 2), "H": round(H, 2), "C": round(C, 2) if C else None, "ret": round(r * 100, 1),
            "status": status, "lv": levels, "t": targets, "conf": conf[:3], "ago": ago}


def build(px, tickers, ld, lw):
    """Returns {"d": {ticker: fib}, "w": {...}}."""
    close, high, low = px["Close"], px["High"], px["Low"]
    cols = [t for t in tickers if t in close.columns]
    wc, wh, wl = weekly_bars(close[cols], high[cols], low[cols])
    kij = ((wh.rolling(26).max() + wl.rolling(26).min()) / 2).iloc[-1]
    out = {"d": {}, "w": {}}
    for tf, (C, Hh, Ll) in {"d": (close[cols], high[cols], low[cols]), "w": (wc, wh, wl)}.items():
        p = FIB[tf]
        lvls = ld if tf == "d" else lw
        for t in cols:
            c = C[t].to_numpy(float)
            ok = ~np.isnan(c)
            if ok.sum() < 30:
                continue
            f0 = int(np.argmax(ok))
            c = pd.Series(c[f0:]).ffill().to_numpy()
            h = pd.Series(Hh[t].to_numpy(float)[f0:]).fillna(pd.Series(c)).to_numpy()
            l = pd.Series(Ll[t].to_numpy(float)[f0:]).fillna(pd.Series(c)).to_numpy()
            sup = []
            L0 = lvls.get(t) or {}
            if L0.get("sup"):
                sup.append(("support", L0["sup"]["p"]))
            if L0.get("tls"):
                sup.append(("rising trendline", L0["tls"]["v"]))
            if pd.notna(kij.get(t)):
                sup.append(("weekly Kijun", float(kij[t])))
            try:
                r = analyze(h, l, c, p, sup)
            except Exception:
                r = None
            if r:
                out[tf][t] = r
    return out
