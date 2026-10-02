"""Classifies every stock into one of six technical zones, on daily and on
weekly bars, using RSI, MACD, ADX(+DI/-DI), Choppiness Index and Ichimoku.

Every past bar is classified too, so the date a stock entered its current
zone comes straight from price history; nothing needs to be stored.

Rules, checked in order (first match wins). Bar counts come from
ZONE_PARAMS in config.py and differ between daily and weekly:
  Oversold      RSI <= 30
  Danger zone   stretched uptrend: above the cloud on most recent bars,
                RSI still >= floor, and EITHER RSI was >= 70 on many recent
                bars OR price is far above its moving average
  Overbought    RSI >= 70 (fresh, not yet stretched)
  Bullish       above cloud, Tenkan >= Kijun, MACD > signal, ADX >= 20 with
                +DI leading, Choppiness < 61.8, RSI 50-70
  Bearish       below cloud, MACD < signal, ADX >= 20 with -DI leading, RSI 30-50
  Accumulation  range-bound (Choppiness >= 55 or ADX < 20), RSI 40-60, MACD
                histogram rising, price inside or near the cloud
  Neutral       none of the above
"""
import numpy as np
import pandas as pd

from .config import (ADX_TREND, CHOP_RANGE, CHOP_TRENDING, RSI_OVERBOUGHT,
                     RSI_OVERSOLD, ZONE_PARAMS)

CODE = {"Oversold": "O", "Overbought": "B", "Danger zone": "D", "Bullish": "U",
        "Bearish": "R", "Accumulation": "A", "Neutral": "N", "No data": "-"}
NAME = {v: k for k, v in CODE.items()}
INSTANT = {"O", "B", "D"}  # these start and end on the bar their condition flips


# ---------- bars ----------
def weekly_bars(close, high, low, today=None):
    """Friday-ending weekly OHLC from daily data, completed weeks only."""
    c = close.resample("W-FRI").last()
    h = high.resample("W-FRI").max()
    l = low.resample("W-FRI").min()
    today = pd.Timestamp(today or pd.Timestamp.now(tz="Asia/Kolkata").date())
    done = c.index <= today          # a week counts once its Friday has arrived
    c, h, l = c[done], h[done], l[done]
    keep = c.notna().any(axis=1)     # drop holiday-only weeks
    return c[keep], h[keep], l[keep]


# ---------- indicators on wide frames (rows = dates, cols = tickers) ----------
def wilder(df, n=14):
    return df.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def indicators(c, h, l):
    d = c.diff()
    rsi = 100 - 100 / (1 + wilder(d.clip(lower=0)) / wilder(-d.clip(upper=0)).replace(0, np.nan))

    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    signal = macd.ewm(span=9, adjust=False).mean()

    pc = c.shift()
    tr = np.maximum(np.maximum(h - l, (h - pc).abs()), (l - pc).abs())
    up, dn = h.diff(), -l.diff()
    pdm = up.where((up > dn) & (up > 0), 0.0)
    mdm = dn.where((dn > up) & (dn > 0), 0.0)
    atr = wilder(tr)
    pdi = 100 * wilder(pdm) / atr
    mdi = 100 * wilder(mdm) / atr
    adx = wilder(100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan))

    rng = h.rolling(14).max() - l.rolling(14).min()
    chop = 100 * np.log10(tr.rolling(14).sum() / rng.replace(0, np.nan)) / np.log10(14)

    tenkan = (h.rolling(9).max() + l.rolling(9).min()) / 2
    kijun = (h.rolling(26).max() + l.rolling(26).min()) / 2
    span_a = ((tenkan + kijun) / 2).shift(26)
    span_b = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)

    return dict(rsi=rsi, macd=macd, signal=signal, hist=macd - signal, adx=adx,
                pdi=pdi, mdi=mdi, chop=chop, tenkan=tenkan, kijun=kijun,
                ctop=np.maximum(span_a, span_b), cbot=np.minimum(span_a, span_b))


def classify(c, ind, p):
    """Raw (unconfirmed) zone code for every bar/ticker."""
    r, m, s, hst = ind["rsi"], ind["macd"], ind["signal"], ind["hist"]
    adx, pdi, mdi, chop = ind["adx"], ind["pdi"], ind["mdi"], ind["chop"]
    tk, kj, top, bot = ind["tenkan"], ind["kijun"], ind["ctop"], ind["cbot"]
    above, below = c > top, c < bot

    trend = above.astype(float).rolling(p["trend_window"], min_periods=p["trend_window"]).sum()
    ob = (r >= RSI_OVERBOUGHT).astype(float).rolling(p["ob_window"], min_periods=p["ob_window"]).sum()
    stretch = (c / c.rolling(p["ma"]).mean() - 1) * 100
    danger = ((trend >= p["trend_bars"]) & (r >= p["rsi_floor"])
              & ((ob >= p["ob_bars"]) | (stretch >= p["stretch"])))

    conds = [
        r <= RSI_OVERSOLD,
        danger,
        r >= RSI_OVERBOUGHT,
        above & (tk >= kj) & (m > s) & (adx >= ADX_TREND) & (pdi > mdi)
              & (chop < CHOP_TRENDING) & (r >= 50) & (r < RSI_OVERBOUGHT),
        below & (m < s) & (adx >= ADX_TREND) & (mdi > pdi) & (r < 50) & (r > RSI_OVERSOLD),
        ((chop >= CHOP_RANGE) | (adx < ADX_TREND)) & (r >= 40) & (r <= 60)
              & (hst > hst.shift(p["hist_rise_bars"])) & (c >= bot * 0.97) & (c <= top * 1.05),
    ]
    raw = np.select([x.fillna(False).to_numpy(bool) for x in conds],
                    ["O", "D", "B", "U", "R", "A"], default="N")
    raw[(r.isna() | top.isna() | adx.isna()).to_numpy()] = "-"
    return pd.DataFrame(raw, index=c.index, columns=c.columns), stretch


def confirm(seq, need_bars):
    """Trend zones must hold need_bars bars; INSTANT zones flip immediately.

    Returns (smoothed list, index where current zone started, previous zone).
    """
    cur, start, prev = seq[0], 0, None
    pending, pcount, out = None, 0, [seq[0]]
    for i in range(1, len(seq)):
        v = seq[i]
        if v == cur:
            pending, pcount = None, 0
        else:
            need = 1 if (v in INSTANT or cur in INSTANT or v == "-") else need_bars
            pcount = pcount + 1 if v == pending else 1
            pending = v
            if pcount >= need:
                prev, cur, start = cur, v, i - need + 1
                pending, pcount = None, 0
                for j in range(start, i):
                    out[j] = cur
        out.append(cur)
    return out, start, prev


def build_zones(close, high, low, tickers, tf="d"):
    """Returns ({ticker: zone dict}, last-30 bar dates, lookback start date)."""
    p = ZONE_PARAMS[tf]
    cols = [t for t in tickers if t in close.columns]
    c, h, l = close[cols], high[cols], low[cols]
    if tf == "w":
        c, h, l = weekly_bars(c, h, l)
    ind = indicators(c, h, l)
    raw, stretch = classify(c, ind, p)
    raw = raw.tail(p["lookback"])
    dates = raw.index
    last = {k: v.iloc[-1] for k, v in ind.items()}
    lc, ls = c.iloc[-1], stretch.iloc[-1]

    res = {}
    for t in cols:
        sm, start, prev = confirm(raw[t].tolist(), p["confirm"])
        z = sm[-1]
        bars = len(sm) - start
        top, bot, px = last["ctop"].get(t), last["cbot"].get(t), lc.get(t)
        cloud = None
        if pd.notna(top) and pd.notna(px):
            cloud = "Above" if px > top else "Below" if px < bot else "Inside"
        m, s = last["macd"].get(t), last["signal"].get(t)
        res[t] = {
            "zone": NAME[z],
            "since": dates[start].strftime("%Y-%m-%d") if start > 0 else None,
            "days": bars, "capped": start == 0,
            "prev": NAME.get(prev) if prev else None,
            "new": start > 0 and bars <= p["new_bars"] and z not in ("N", "-"),
            "strip": "".join(sm),
            "rsi": _r(last["rsi"].get(t), 1), "hist": _r(last["hist"].get(t), 2),
            "macd_x": None if pd.isna(m) or pd.isna(s) else ("Above signal" if m > s else "Below signal"),
            "adx": _r(last["adx"].get(t), 1), "pdi": _r(last["pdi"].get(t), 1),
            "mdi": _r(last["mdi"].get(t), 1), "chop": _r(last["chop"].get(t), 1),
            "cloud": cloud, "stretch": _r(ls.get(t), 1),
        }
    return res, [d.strftime("%Y-%m-%d") for d in dates], dates[0].strftime("%Y-%m-%d")


def _r(x, n):
    return None if x is None or pd.isna(x) else round(float(x), n)
