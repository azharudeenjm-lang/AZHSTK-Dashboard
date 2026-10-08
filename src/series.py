"""Numbers behind the Screener's "your numbers" conditions.

For each stock and timeframe this keeps the last N+1 values (N =
SCREENER_EVENT_BARS) of the key indicators, so the screener in your browser
can test any level you type: RSI crossed above 55, Choppiness below 38.2,
ADX above 22, volume 3x average, a 40-bar high, and so on.

Periods come from fixed lists (sending full price history for every stock
would make the page too heavy for a phone):
  RSI 7 / 9 / 14 / 21      Choppiness 14 / 21      ADX / DMI 14
  MACD 12-26-9             SMA and EMA 5 / 10 / 20 / 30 / 50 / 100 / 150 / 200
  SuperTrend 7-3 / 10-2 / 10-3 / 14-2
Indicator values are stored x10 as integers to keep the files small.
"""
import numpy as np
import pandas as pd

from .config import SCREENER_EVENT_BARS as NB

RSI_P = [7, 9, 14, 21]
CHOP_P = [14, 21]
MA_P = [5, 10, 20, 30, 50, 100, 150, 200]
CHG_N = [1, 5, 10, 20, 60, 120, 250]
RNG_N = [5, 10, 15, 20, 26, 30]
ST_P = [(7, 3), (10, 2), (10, 3), (14, 2)]
ENV_P = [20, 50, 200]
# percent channel periods: label -> bars (daily, weekly); None = not available on that timeframe
PCH = {"1 week": (5, None), "2 weeks": (10, 2), "1 month": (21, 4), "3 months": (63, 13),
       "6 months": (126, 26), "1 year": (250, 52)}
K = NB + 1

G = "Indicators (your numbers)"
FUND_M = ["P/E", "P/B", "ROE %", "Debt to equity", "Market cap (₹ cr)", "Net margin %",
          "Sales growth % (vs same quarter last year)", "Profit growth % (vs same quarter last year)",
          "Dividend yield %", "Promoter holding %", "Promoter holding change (points, last quarter)",
          "Pledged % of promoter shares", "Institutional holding %", "Delivery % (latest day)",
          "Delivery vs its 20-day average (x)", "Quality score (0-5)"]
PMETA = [
    {"id": "p_rsi", "g": G, "l": "RSI", "params": [
        {"k": "per", "t": "sel", "o": RSI_P, "d": 14, "lab": "period"},
        {"k": "op", "t": "op", "o": ["gt", "lt", "xa", "xb"], "d": "xa"},
        {"k": "x", "t": "num", "d": 50, "lab": "level"}]},
    {"id": "p_chop", "g": G, "l": "Choppiness Index", "params": [
        {"k": "per", "t": "sel", "o": CHOP_P, "d": 14, "lab": "period"},
        {"k": "op", "t": "op", "o": ["lt", "gt", "xb", "xa"], "d": "lt"},
        {"k": "x", "t": "num", "d": 38.2, "lab": "level"}]},
    {"id": "p_adx", "g": G, "l": "ADX (14)", "params": [
        {"k": "op", "t": "op", "o": ["gt", "lt", "xa", "xb"], "d": "gt"},
        {"k": "x", "t": "num", "d": 25, "lab": "level"}]},
    {"id": "p_di", "g": G, "l": "+DI vs −DI (14)", "params": [
        {"k": "op", "t": "op", "o": ["gt", "lt", "xa", "xb"], "d": "xa",
         "labels": {"gt": "+DI above −DI", "lt": "+DI below −DI", "xa": "+DI crossed above −DI", "xb": "+DI crossed below −DI"}}]},
    {"id": "p_macd", "g": G, "l": "MACD (12, 26, 9)", "params": [
        {"k": "line", "t": "sel", "o": ["line", "histogram", "signal"], "d": "histogram", "lab": ""},
        {"k": "op", "t": "op", "o": ["gt", "lt", "xa", "xb"], "d": "xa"},
        {"k": "x", "t": "num", "d": 0, "lab": "level"}]},
    {"id": "p_ma", "g": G, "l": "Price vs moving average", "params": [
        {"k": "type", "t": "sel", "o": ["SMA", "EMA"], "d": "SMA", "lab": ""},
        {"k": "per", "t": "sel", "o": MA_P, "d": 50, "lab": "period"},
        {"k": "op", "t": "op", "o": ["gt", "lt", "xa", "xb"], "d": "xa"}]},
    {"id": "p_macross", "g": G, "l": "Moving average crossover", "params": [
        {"k": "type", "t": "sel", "o": ["SMA", "EMA"], "d": "EMA", "lab": ""},
        {"k": "f", "t": "sel", "o": MA_P, "d": 50, "lab": "fast"},
        {"k": "s", "t": "sel", "o": MA_P, "d": 200, "lab": "slow"},
        {"k": "op", "t": "op", "o": ["xa", "xb", "gt", "lt"], "d": "xa"}]},
    {"id": "p_newhi", "g": G, "l": "New high over N bars", "params": [
        {"k": "x", "t": "num", "d": 52, "lab": "bars", "min": 2, "max": 300, "int": True}]},
    {"id": "p_newlo", "g": G, "l": "New low over N bars", "params": [
        {"k": "x", "t": "num", "d": 52, "lab": "bars", "min": 2, "max": 300, "int": True}]},
    {"id": "p_hi52", "g": G, "l": "Within X% of 52-week high", "params": [
        {"k": "x", "t": "num", "d": 5, "lab": "%"}]},
    {"id": "p_vol", "g": G, "l": "Volume vs 20-bar average", "params": [
        {"k": "x", "t": "num", "d": 2, "lab": "× average"},
        {"k": "dir", "t": "sel", "o": ["rising", "falling", "any"], "d": "rising", "lab": "bar"}]},
    {"id": "p_gap", "g": G, "l": "Gap up of at least X%", "params": [
        {"k": "x", "t": "num", "d": 3, "lab": "%"}]},
    {"id": "p_chg", "g": G, "l": "Price change over N bars", "params": [
        {"k": "n", "t": "sel", "o": CHG_N, "d": 20, "lab": "bars"},
        {"k": "op", "t": "op", "o": ["gt", "lt"], "d": "gt", "labels": {"gt": "at least", "lt": "at most"}},
        {"k": "x", "t": "num", "d": 10, "lab": "%"}]},
    {"id": "p_rng", "g": G, "l": "Tight range: high-to-low within X% over N bars", "params": [
        {"k": "n", "t": "sel", "o": RNG_N, "d": 10, "lab": "bars"},
        {"k": "x", "t": "num", "d": 6, "lab": "%"}]},
    {"id": "p_pch", "g": G, "l": "Percent channel: price within ±X% over a period", "params": [
        {"k": "x", "t": "num", "d": 5, "lab": "±%"},
        {"k": "per", "t": "sel", "o": list(PCH), "d": "1 month", "lab": "during last"}]},
    {"id": "p_env", "g": G, "l": "Moving-average envelope", "params": [
        {"k": "type", "t": "sel", "o": ["SMA", "EMA"], "d": "EMA", "lab": ""},
        {"k": "per", "t": "sel", "o": ENV_P, "d": 50, "lab": "period"},
        {"k": "x", "t": "num", "d": 10, "lab": "± %"},
        {"k": "op", "t": "op", "o": ["tu", "xa", "ab", "tl", "xb", "bl", "in"], "d": "tu",
         "labels": {"tu": "touched upper band", "xa": "crossed above upper band", "ab": "closed above upper band",
                    "tl": "touched lower band", "xb": "crossed below lower band", "bl": "closed below lower band",
                    "in": "inside the envelope"}}]},
    {"id": "p_fund", "g": "Fundamentals (your numbers)", "l": "Fundamental value", "params": [
        {"k": "m", "t": "sel", "o": FUND_M, "d": "P/E", "lab": ""},
        {"k": "op", "t": "op", "o": ["lt", "gt"], "d": "lt"},
        {"k": "x", "t": "num", "d": 30, "lab": "value"}]},
    {"id": "p_grade", "g": "Fundamentals (your numbers)", "l": "Quality grade", "params": [
        {"k": "g", "t": "sel", "o": ["A", "A or B", "A, B or C"], "d": "A or B", "lab": "grade"}]},
    {"id": "p_st", "g": G, "l": "SuperTrend", "params": [
        {"k": "set", "t": "sel", "o": [f"{a},{b}" for a, b in ST_P], "d": "10,3", "lab": "(period, multiplier)"},
        {"k": "op", "t": "op", "o": ["bull", "bear", "tb", "tr"], "d": "tb",
         "labels": {"bull": "is bullish", "bear": "is bearish", "tb": "turned bullish", "tr": "turned bearish"}}]},
]


def _w(df, n):
    return df.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def _ok(v):
    """True for a usable number (not missing, not infinite)."""
    try:
        return v is not None and np.isfinite(float(v))
    except (TypeError, ValueError):
        return False


def _i10(v):
    return int(round(float(v) * 10)) if _ok(v) else None


def _sig4(v):
    return float(f"{float(v):.4g}") if _ok(v) else None


def _tail(df, t, f=_i10):
    return [f(x) for x in df[t].tail(K).to_numpy()]


def _st_state(h, l, c, n, m):
    """SuperTrend bullish state for the last K bars as a string of 1/0/-."""
    h, l, c = h[-300:], l[-300:], c[-300:]
    pc = np.roll(c, 1)
    pc[0] = np.nan
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    atr = pd.Series(tr).ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy()
    mid = (h + l) / 2
    up = dn = np.nan
    bull, out = True, []
    for t in range(len(c)):
        if np.isnan(atr[t]) or np.isnan(c[t]):
            out.append("-")
            continue
        nu, nd = mid[t] - m * atr[t], mid[t] + m * atr[t]
        up = nu if np.isnan(up) or c[t - 1] < up else max(nu, up)
        dn = nd if np.isnan(dn) or c[t - 1] > dn else min(nd, dn)
        if bull and c[t] < up:
            bull = False
        elif not bull and c[t] > dn:
            bull = True
        out.append("1" if bull else "0")
    return "".join(out[-K:])


def build_tf(o, h, l, c, v, tf):
    """Wide frames for one timeframe. Returns {ticker: series dict}."""
    per = 1 if tf == "w" else 5
    d = c.diff()
    rsi = {p: 100 - 100 / (1 + _w(d.clip(lower=0), p) / _w(-d.clip(upper=0), p).replace(0, np.nan)) for p in RSI_P}
    pc = c.shift()
    tr = np.maximum(np.maximum(h - l, (h - pc).abs()), (l - pc).abs())
    chop = {p: 100 * np.log10(tr.rolling(p).sum() / (h.rolling(p).max() - l.rolling(p).min()).replace(0, np.nan)) / np.log10(p)
            for p in CHOP_P}
    upm, dnm = h.diff(), -l.diff()
    atr = _w(tr, 14)
    pdi = 100 * _w(upm.where((upm > dnm) & (upm > 0), 0.0), 14) / atr
    mdi = 100 * _w(dnm.where((dnm > upm) & (dnm > 0), 0.0), 14) / atr
    adx = _w(100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan), 14)
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    msig = macd.ewm(span=9, adjust=False).mean()
    mh = macd - msig
    av = v.rolling(20, min_periods=10).mean().shift().replace(0, np.nan)
    vx = (v / av) * np.sign(c.diff()).replace(0, 1)
    gap = (l / h.shift().replace(0, np.nan) - 1) * 100
    chg = {n: (c / c.shift(n).replace(0, np.nan) - 1) * 100 for n in CHG_N}
    rng = {n: (h.rolling(n).max() / l.rolling(n).min().replace(0, np.nan) - 1) * 100 for n in RNG_N}
    hi52 = (1 - c / h.rolling(52 * per, min_periods=int(52 * per * 0.8)).max()) * 100
    sma = {p: c.rolling(p, min_periods=p).mean() for p in MA_P}
    ema = {p: c.ewm(span=p, adjust=False, min_periods=p).mean() for p in MA_P}

    # envelope distances (% of close / high / low from each average), computed once for all stocks
    envf = {}
    for typ, src in (("s", sma), ("e", ema)):
        for p_ in ENV_P:
            m_ = src[p_].tail(K + 1)
            envf[f"{typ}{p_}"] = [(x.tail(K + 1) / m_ - 1) * 100 for x in (c, h, l)]

    def cross_ago(a, b, t, up=True):
        x, y = a[t].tail(K).to_numpy(), b[t].tail(K).to_numpy()
        for back in range(NB):
            i = len(x) - 1 - back
            if i < 1 or np.isnan(x[i]) or np.isnan(y[i]) or np.isnan(x[i - 1]) or np.isnan(y[i - 1]):
                continue
            if (up and x[i] > y[i] and x[i - 1] <= y[i - 1]) or (not up and x[i] < y[i] and x[i - 1] >= y[i - 1]):
                return back
        return None

    H, L, C = h.to_numpy(), l.to_numpy(), c.to_numpy()
    out = {}
    for j, t in enumerate(c.columns):
        if c[t].notna().sum() < 30:
            continue
        s = {"rsi": {str(p): _tail(rsi[p], t) for p in RSI_P},
             "chop": {str(p): _tail(chop[p], t) for p in CHOP_P},
             "adx": _tail(adx, t), "pdi": _tail(pdi, t), "mdi": _tail(mdi, t),
             "macd": _tail(macd, t, _sig4), "msig": _tail(msig, t, _sig4), "mh": _tail(mh, t, _sig4),
             "vx": _tail(vx, t), "gap": _tail(gap, t),
             "chg": {str(n): _i10(chg[n][t].iloc[-1]) for n in CHG_N},
             "rng": {str(n): _i10(rng[n][t].iloc[-1]) for n in RNG_N},
             "hi52": _i10(hi52[t].iloc[-1])}
        # how many bars back the current high/low is the highest/lowest ("new N-bar high")
        hh, ll = H[:, j], L[:, j]
        n = len(hh)
        hia, loa = [], []
        for i in range(n - K, n):
            if i < 0 or np.isnan(hh[i]):
                hia.append(None)
                loa.append(None)
                continue
            prev = np.flatnonzero(hh[:i] > hh[i])
            hia.append(int(min(300, i - 1 - prev[-1] if len(prev) else i)))
            prev = np.flatnonzero(ll[:i] < ll[i])
            loa.append(int(min(300, i - 1 - prev[-1] if len(prev) else i)))
        s["hia"], s["loa"] = hia, loa
        # moving averages: price-above bits, crossings (bars ago), fast/slow pair bits and crossings
        ma = {"s": "", "e": {}, "p": ""}
        for typ, src in (("s", sma), ("e", ema)):
            for p in MA_P:
                last = src[p][t].iloc[-1]
                ma["s"] += "1" if pd.notna(last) and c[t].iloc[-1] > last else "0"
                for up, key in ((True, "xa"), (False, "xb")):
                    a = cross_ago(c, src[p], t, up)
                    if a is not None:
                        ma["e"][f"{key}_{typ}{p}"] = a
        for typ, src in (("s", sma), ("e", ema)):
            for fi, f in enumerate(MA_P):
                for sl in MA_P[fi + 1:]:
                    fv, sv = src[f][t].iloc[-1], src[sl][t].iloc[-1]
                    ma["p"] += "1" if pd.notna(fv) and pd.notna(sv) and fv > sv else "0"
                    for up, key in ((True, "ca"), (False, "cb")):
                        a = cross_ago(src[f], src[sl], t, up)
                        if a is not None:
                            ma["e"][f"{key}_{typ}{f}_{typ}{sl}"] = a
        s["ma"] = ma
        s["st"] = {f"{a},{b}": _st_state(H[:, j], L[:, j], C[:, j], a, b) for a, b in ST_P}
        # percent channels: half-range of closes around their midpoint, in %, per period
        s["pch"] = {}
        for lab, (nd, nw) in PCH.items():
            nb = nd if tf == "d" else nw
            if nb:
                cs = c[t].tail(nb)
                if cs.notna().sum() >= nb * 0.8:
                    hi, lo = cs.max(), cs.min()
                    s["pch"][lab] = _i10((hi - lo) / (hi + lo) * 100)
        # envelopes: % distance of close / high / low from each moving average
        s["env"] = {k_: [_tail(f3[0], t), _tail(f3[1], t), _tail(f3[2], t)] for k_, f3 in envf.items()}
        out[t] = s
    return out


def build(px, tickers):
    from .signals import _bars
    cols = [t for t in tickers if t in px["Close"].columns]
    res = {}
    for tf in ("d", "w"):
        o, c, h, l, v = _bars(px, tf, cols)
        res[tf] = build_tf(o.fillna(c), h, l, c, v, tf)
        print(f"  screener numbers ({tf}): {len(res[tf])} stocks")
    return res
