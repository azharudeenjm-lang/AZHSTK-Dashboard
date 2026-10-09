"""Screener conditions for every stock, on daily and weekly bars.

Each condition is either a STATE (true right now, e.g. "price above MA 200")
or an EVENT (happened on a recent bar, e.g. "RSI crossed above 50"). Events
are stored as "bars ago" (0 = the latest bar) for up to SCREENER_EVENT_BARS
bars, so the screener can ask "within the last N bars".
"""
import numpy as np
import pandas as pd

from .config import SCREENER_EVENT_BARS as NB, WEEKLY_LIVE
from . import elliott, lines, patterns
from . import news as _news
from . import ownership as _own
from . import buy as _buy
from . import trend3 as _t3
from . import template as _tt
from .themes_list import META as _TH_META

# id, group, label, kind ("s" state / "e" event)
META = [
    # trend
    ("up200", "Trend", "Bullish trend: above MA 200 and MA 200 rising", "s"),
    ("up50", "Trend", "Bullish trend: above MA 50 and MA 50 rising", "s"),
    ("adx_up", "Trend", "Strong trend: ADX 25+ with +DI leading", "s"),
    ("st_bull", "Trend", "SuperTrend (10, 3) bullish", "s"),
    ("st_flip", "Trend", "SuperTrend turned bullish", "e"),
    # moving averages
    ("ab20", "Moving averages", "Price above MA 20", "s"),
    ("ab50", "Moving averages", "Price above MA 50", "s"),
    ("ab200", "Moving averages", "Price above MA 200", "s"),
    ("x20", "Moving averages", "Price crossed above MA 20", "e"),
    ("x50", "Moving averages", "Price crossed above MA 50", "e"),
    ("x200", "Moving averages", "Price crossed above MA 200", "e"),
    ("xd50", "Moving averages", "Price crossed below MA 50", "e"),
    ("gc", "Moving averages", "Golden cross: EMA 50 crossed above EMA 200", "e"),
    ("e20x50", "Moving averages", "EMA 20 crossed above EMA 50", "e"),
    ("dc", "Moving averages", "Death cross: EMA 50 crossed below EMA 200", "e"),
    # new highs / lows
    ("hi52", "Highs and lows", "New 52-week high", "e"),
    ("hi26", "Highs and lows", "New 26-week high", "e"),
    ("hi13", "Highs and lows", "New 13-week high", "e"),
    ("near52", "Highs and lows", "Within 5% of 52-week high", "s"),
    ("lo52", "Highs and lows", "New 52-week low", "e"),
    # RSI
    ("rsi_x30", "RSI", "RSI crossed above 30", "e"),
    ("rsi_x50", "RSI", "RSI crossed above 50", "e"),
    ("rsi_x70", "RSI", "RSI crossed above 70", "e"),
    ("rsi_gt70", "RSI", "RSI between 70 and 100", "s"),
    ("rsi_50_70", "RSI", "RSI between 50 and 70", "s"),
    ("rsi_lt30", "RSI", "RSI between 0 and 30", "s"),
    ("rsi_up", "RSI", "RSI rising for 5 bars", "s"),
    ("bull_div", "RSI", "Bullish divergence (lower low, RSI higher low)", "e"),
    ("bear_div", "RSI", "Bearish divergence (higher high, RSI or MACD lower high)", "e"),
    # MACD
    ("macd_x", "MACD", "MACD crossed above signal", "e"),
    ("macdh_x0", "MACD", "MACD histogram crossed above zero", "e"),
    ("macd_x0", "MACD", "MACD line crossed above zero", "e"),
    ("macd_ab0", "MACD", "MACD line above zero", "s"),
    ("macdh_up", "MACD", "MACD histogram rising for 3 bars", "s"),
    # Ichimoku
    ("cloud_ab", "Ichimoku", "Price above the cloud", "s"),
    ("cloud_x", "Ichimoku", "Price broke above the cloud", "e"),
    ("tk_x", "Ichimoku", "Tenkan crossed above Kijun", "e"),
    # Bollinger, channels, volatility
    ("bb_up", "Bands and channels", "Touched the upper Bollinger band (20, 2)", "e"),
    ("bb_lo", "Bands and channels", "Touched the lower Bollinger band (20, 2)", "e"),
    ("squeeze", "Bands and channels", "Bollinger squeeze: narrowest bands in 6 months", "s"),
    ("tight10", "Bands and channels", "Tight range: within 6% for 10 bars", "s"),
    ("base26", "Bands and channels", "Base: within 15% for 26 bars", "s"),
    # volume
    ("vol2x_up", "Volume", "Rising on unusual volume (2x average)", "e"),
    ("vol2x_dn", "Volume", "Falling on unusual volume (2x average)", "e"),
    ("vol_trend", "Volume", "Volume trending up (10-bar avg above 50-bar avg)", "s"),
    ("obv_up", "Volume", "On-balance volume at a 50-bar high", "s"),
    # gaps and candles
    ("gap_up", "Candles and gaps", "Gap up (low above previous high)", "e"),
    ("gap_up5", "Candles and gaps", "Gap up of 5% or more", "e"),
    ("long_white", "Candles and gaps", "Long white candle", "e"),
    ("hammer", "Candles and gaps", "Hammer after a dip", "e"),
    ("engulf", "Candles and gaps", "Bullish engulfing", "e"),
    ("piercing", "Candles and gaps", "Piercing line", "e"),
    ("mstar", "Candles and gaps", "Morning star", "e"),
    ("bear_engulf", "Candles and gaps", "Bearish engulfing", "e"),
    # levels and fibonacci (from the Levels page and Fibonacci engine)
    ("lv_brk", "Levels and Fibonacci", "Breakout above resistance", "s"),
    ("lv_tlb", "Levels and Fibonacci", "Trendline breakout", "s"),
    ("lv_ret", "Levels and Fibonacci", "Retest of a broken level", "s"),
    ("lv_tls", "Levels and Fibonacci", "At rising trendline support", "s"),
    ("lv_sup", "Levels and Fibonacci", "Near support", "s"),
    ("lv_res", "Levels and Fibonacci", "Near resistance", "s"),
    ("lv_bd", "Levels and Fibonacci", "Breakdown below support", "s"),
    ("fib382", "Levels and Fibonacci", "Touched Fibonacci 38.2% and reversed up", "e"),
    ("fib50", "Levels and Fibonacci", "Touched Fibonacci 50% and reversed up", "e"),
    ("fib618", "Levels and Fibonacci", "Touched Fibonacci 61.8% and reversed up", "e"),
    ("fib_gp", "Levels and Fibonacci", "In the Fibonacci golden pocket (50–61.8%)", "s"),
]
META += [(i, "Trend lines", l, k) for i, l, k in lines.TL_META]
META += [(i, "Support and resistance", l, k) for i, l, k in lines.SR_META]
META += [(i, "DeMark TD lines", l, k) for i, l, k in lines.TD_META]
META += [(i, "Bands and channels", l, k) for i, l, k in patterns.BAND_META]
META += [(i, "Chart patterns", l, k) for i, l, k in patterns.PAT_META]
META += [(i, "Elliott waves", l, k) for i, l, k in elliott.META]
META += [(i, "News triggers", l, k) for i, l, k in _news.META]
META += [(i, "Ownership and alerts", l, k) for i, l, k in _own.META]
META += [(i, "Buy criteria (weekly)", l, k) for i, l, k in _buy.META]
META += [(i, "Trend lines", l, k) for i, l, k in _t3.META]
META += [(i, "Trend Template (Minervini)", l, k) for i, l, k in _tt.META]
META += [(i, "Themes", l, k) for i, l, k in _TH_META]

LVMAP = {"Breakout": "lv_brk", "Trendline breakout": "lv_tlb", "Retest": "lv_ret",
         "At trendline support": "lv_tls", "Near support": "lv_sup", "Near resistance": "lv_res",
         "Breakdown": "lv_bd"}


def _ago(E):
    """Bars since the latest True in the last NB rows (0 = latest bar), else NaN."""
    tail = E.tail(NB).to_numpy(bool)[::-1]
    hit = tail.any(axis=0)
    first = tail.argmax(axis=0).astype(float)
    first[~hit] = np.nan
    return pd.Series(first, index=E.columns)


def _cross_up(a, b):
    return (a > b) & (a.shift() <= b.shift())


def _wilder(df, n=14):
    return df.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def _bars(px, tf, cols):
    o, c, h, l, v = (px[f][cols] for f in ("Open", "Close", "High", "Low", "Volume"))
    if tf == "d":
        return o, c, h, l, v
    agg = dict(Open="first", Close="last", High="max", Low="min", Volume="sum")
    out = []
    for f, df in zip(("Open", "Close", "High", "Low", "Volume"), (o, c, h, l, v)):
        r = df.resample("W-FRI")
        out.append(getattr(r, agg[f])() if f != "Volume" else r.sum(min_count=1))
    today = pd.Timestamp(pd.Timestamp.now(tz="Asia/Kolkata").date())
    keep = ((out[1].index <= today) | WEEKLY_LIVE) & out[1].notna().any(axis=1).to_numpy()
    return [x[keep] for x in out]


def _supertrend(h, l, c, n=10, m=3.0):
    """Returns (bullish state at last bar, bars since last flip to bullish or NaN)."""
    pc = c.shift()
    tr = np.maximum(np.maximum(h - l, (h - pc).abs()), (l - pc).abs())
    atr = tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy()
    H, L, C = h.to_numpy(), l.to_numpy(), c.to_numpy()
    mid = (H + L) / 2
    up0, dn0 = mid - m * atr, mid + m * atr
    T, K = C.shape
    state = np.zeros(K, bool)
    since = np.full(K, np.nan)
    for k in range(K):
        up, dn, bull, last_flip = np.nan, np.nan, True, None
        for t in range(T):
            if np.isnan(atr[t, k]) or np.isnan(C[t, k]):
                continue
            nu, nd = up0[t, k], dn0[t, k]
            up = nu if np.isnan(up) or C[t - 1, k] < up else max(nu, up)
            dn = nd if np.isnan(dn) or C[t - 1, k] > dn else min(nd, dn)
            if bull and C[t, k] < up:
                bull = False
            elif not bull and C[t, k] > dn:
                bull, last_flip = True, t
        state[k] = bull
        if last_flip is not None and T - 1 - last_flip < NB:
            since[k] = T - 1 - last_flip
    return pd.Series(state, index=c.columns), pd.Series(since, index=c.columns)


def _divergence(c, rsi, macd, k, bull):
    """Bars since the latest confirmed divergence (pivot k bars each side)."""
    C, R, M = c.to_numpy(), rsi.to_numpy(), macd.to_numpy()
    if bull:
        piv = (c == c.rolling(2 * k + 1, center=True).min()) & c.notna()
    else:
        piv = (c == c.rolling(2 * k + 1, center=True).max()) & c.notna()
    T = len(c)
    out = np.full(c.shape[1], np.nan)
    for j in range(c.shape[1]):
        ps = np.flatnonzero(piv.iloc[:, j].to_numpy())[-6:]
        for a, b in zip(ps[:-1][::-1], ps[1:][::-1]):
            if b - a > 12 * k:
                continue
            if bull and C[b, j] < C[a, j] and R[a, j] <= 40 and R[b, j] > R[a, j] + 2:
                ok = True
            elif not bull and C[b, j] > C[a, j] and R[a, j] >= 60 and (R[b, j] < R[a, j] - 2 or (M[a, j] > 0 and M[b, j] < M[a, j])):
                ok = True
            else:
                ok = False
            if ok:
                ago = T - 1 - (b + k)
                if 0 <= ago < NB:
                    out[j] = ago
                break
    return pd.Series(out, index=c.columns)


def build(px, tickers, ld, lw, fibs, circuit=None):
    """Returns {"d": {ticker: {cond: value}}, "w": {...}} with only true conditions.

    Each stock's chart-pattern geometry (for drawing) is stored under "_g".
    circuit: optional {symbol: price band %} from NSE, for circuit-limit hits."""
    cols = [t for t in tickers if t in px["Close"].columns]
    res = {}
    for tf in ("d", "w"):
        o, c, h, l, v = _bars(px, tf, cols)
        o = o.fillna(c)
        last = c.iloc[-1]
        S, E = {}, {}
        ma = {n: c.rolling(n, min_periods=n).mean() for n in (20, 50, 200)}
        ema = {n: c.ewm(span=n, adjust=False, min_periods=n).mean() for n in (20, 50, 200)}
        S["up200"] = (c > ma[200]).iloc[-1] & (ma[200].iloc[-1] > ma[200].shift(20).iloc[-1])
        S["up50"] = (c > ma[50]).iloc[-1] & (ma[50].iloc[-1] > ma[50].shift(10).iloc[-1])
        for n in (20, 50, 200):
            S[f"ab{n}"] = (c > ma[n]).iloc[-1]
            E[f"x{n}"] = _cross_up(c, ma[n])
        E["xd50"] = _cross_up(ma[50], c)
        E["gc"] = _cross_up(ema[50], ema[200])
        E["e20x50"] = _cross_up(ema[20], ema[50])
        E["dc"] = _cross_up(ema[200], ema[50])
        # highs / lows (weeks -> bars)
        per = 1 if tf == "w" else 5
        for wk, key in ((52, "hi52"), (26, "hi26"), (13, "hi13")):
            n = wk * per
            E[key] = h >= h.rolling(n, min_periods=int(n * 0.8)).max()
        n52 = 52 * per
        S["near52"] = (last >= h.rolling(n52, min_periods=int(n52 * 0.8)).max().iloc[-1] * 0.95)
        E["lo52"] = l <= l.rolling(n52, min_periods=int(n52 * 0.8)).min()
        # RSI
        d = c.diff()
        rsi = 100 - 100 / (1 + _wilder(d.clip(lower=0)) / _wilder(-d.clip(upper=0)).replace(0, np.nan))
        for lvl in (30, 50, 70):
            E[f"rsi_x{lvl}"] = _cross_up(rsi, pd.DataFrame(lvl, index=rsi.index, columns=rsi.columns))
        r = rsi.iloc[-1]
        S["rsi_gt70"], S["rsi_50_70"], S["rsi_lt30"] = r >= 70, (r >= 50) & (r < 70), r <= 30
        S["rsi_up"] = (rsi.diff().tail(5) > 0).all()
        # MACD
        macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        sig = macd.ewm(span=9, adjust=False).mean()
        hist = macd - sig
        zero = pd.DataFrame(0.0, index=c.index, columns=c.columns)
        E["macd_x"] = _cross_up(macd, sig)
        E["macdh_x0"] = _cross_up(hist, zero)
        E["macd_x0"] = _cross_up(macd, zero)
        S["macd_ab0"] = macd.iloc[-1] > 0
        S["macdh_up"] = (hist.diff().tail(3) > 0).all()
        # ADX / DMI
        pc = c.shift()
        tr = np.maximum(np.maximum(h - l, (h - pc).abs()), (l - pc).abs())
        up, dn = h.diff(), -l.diff()
        atr = _wilder(tr)
        pdi = 100 * _wilder(up.where((up > dn) & (up > 0), 0.0)) / atr
        mdi = 100 * _wilder(dn.where((dn > up) & (dn > 0), 0.0)) / atr
        adx = _wilder(100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan))
        S["adx_up"] = (adx.iloc[-1] >= 25) & (pdi.iloc[-1] > mdi.iloc[-1])
        st, flip = _supertrend(h, l, c)
        S["st_bull"] = st
        # Ichimoku
        tk = (h.rolling(9).max() + l.rolling(9).min()) / 2
        kj = (h.rolling(26).max() + l.rolling(26).min()) / 2
        top = np.maximum(((tk + kj) / 2).shift(26), ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26))
        S["cloud_ab"] = last > top.iloc[-1]
        E["cloud_x"] = _cross_up(c, top)
        E["tk_x"] = _cross_up(tk, kj)
        # Bollinger, channels
        m20, sd = c.rolling(20).mean(), c.rolling(20).std()
        E["bb_up"] = h >= m20 + 2 * sd
        E["bb_lo"] = l <= m20 - 2 * sd
        bw = (4 * sd / m20)
        S["squeeze"] = bw.iloc[-1] <= bw.rolling(26 * per, min_periods=20).min().iloc[-1] * 1.02
        S["tight10"] = (h.tail(10).max() / l.tail(10).min() - 1) <= 0.06
        S["base26"] = (h.tail(26).max() / l.tail(26).min() - 1) <= 0.15
        # volume
        av = v.rolling(20, min_periods=10).mean().shift()
        E["vol2x_up"] = (v >= 2 * av) & (c > c.shift())
        E["vol2x_dn"] = (v >= 2 * av) & (c < c.shift())
        S["vol_trend"] = v.rolling(10).mean().iloc[-1] > v.rolling(50).mean().iloc[-1]
        obv = (np.sign(c.diff()).fillna(0) * v.fillna(0)).cumsum()
        S["obv_up"] = obv.iloc[-1] >= obv.tail(50).max() * 0.999
        # gaps and candles
        ph = h.shift()
        E["gap_up"] = l > ph
        E["gap_up5"] = l >= ph * 1.05
        body, rng = c - o, (h - l).replace(0, np.nan)
        avg_rng = (h - l).rolling(20).mean()
        lower = np.minimum(o, c) - l
        upper = h - np.maximum(o, c)
        E["long_white"] = (body > 0) & (body >= 0.7 * rng) & (rng >= 1.3 * avg_rng)
        E["hammer"] = (lower >= 2 * body.abs()) & (upper <= 0.3 * rng) & (c < ma[20])
        po, pcl = o.shift(), c.shift()
        E["engulf"] = (pcl < po) & (c > o) & (c >= po) & (o <= pcl)
        E["bear_engulf"] = (pcl > po) & (c < o) & (c <= po) & (o >= pcl)
        E["piercing"] = (pcl < po) & (o < l.shift()) & (c > (po + pcl) / 2) & (c < po)
        o2, c2 = o.shift(2), c.shift(2)
        E["mstar"] = ((c2 < o2) & ((o2 - c2) >= 0.6 * (h.shift(2) - l.shift(2)))
                      & ((c.shift() - o.shift()).abs() <= 0.3 * (o2 - c2)) & (c > o) & (c > (o2 + c2) / 2))
        patterns.add_bands(S, E, o, h, l, c, tf, circuit)
        # assemble
        ago = {k: _ago(e.fillna(False).astype(bool)) for k, e in E.items()}
        ago["st_flip"] = flip
        k_piv = 5 if tf == "d" else 3
        ago["bull_div"] = _divergence(c, rsi, macd, k_piv, True)
        ago["bear_div"] = _divergence(c, rsi, macd, k_piv, False)
        lvls = ld if tf == "d" else lw
        fb = fibs.get(tf, {})
        lo10 = l.tail(NB)
        out = {}
        for t in cols:
            row = {}
            for k, sv in S.items():
                val = sv.get(t)
                if val is not None and pd.notna(val) and bool(val):
                    row[k] = 1
            for k, sv in ago.items():
                val = sv.get(t)
                if val is not None and pd.notna(val):
                    row[k] = int(val)
            for sname in ((lvls.get(t) or {}).get("sig") or []):
                if sname in LVMAP:
                    row[LVMAP[sname]] = 1
            f = fb.get(t)
            if f:
                if f.get("status") == "Golden pocket":
                    row["fib_gp"] = 1
                lows, closes = lo10[t].to_numpy(), c[t].tail(NB).to_numpy()
                for key, lvl in (("fib382", "38.2"), ("fib50", "50"), ("fib618", "61.8")):
                    L = f["lv"].get(lvl)
                    if not L:
                        continue
                    for back in range(len(lows)):
                        i = len(lows) - 1 - back
                        if i > 0 and lows[i] <= L * 1.01 and closes[i] > L and closes[i - 1] > L and closes[i] > closes[i - 1]:
                            row[key] = back
                            break
            if row:
                out[t] = row
        extra = lines.build_tf(o, h, l, c, tf)
        prow, pgeo = patterns.build_tf(o, h, l, c, tf, None)
        erow, egeo = elliott.build_tf(h, l, c, tf)
        for src in (extra, prow, erow):
            for t, r in src.items():
                row = out.setdefault(t, {})
                v = r.pop("_v", None)
                row.update(r)
                if v:
                    row.setdefault("_v", {}).update(v)
        for t, g in pgeo.items():
            out.setdefault(t, {})["_g"] = g
        for t, g in egeo.items():
            out.setdefault(t, {})["_e"] = g
        res[tf] = out
        print(f"  screener signals ({tf}): {len(out)} stocks")
    return res
