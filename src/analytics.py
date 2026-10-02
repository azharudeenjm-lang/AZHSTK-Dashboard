"""Technicals, equal-weight sector indices, and Relative Rotation Graph math."""
import numpy as np
import pandas as pd

from .config import (MIN_AVG_TURNOVER_CR, MIN_HISTORY_DAYS,
                     MIN_STOCKS_PER_SECTOR, RRG_WINDOW, TAIL_DAILY,
                     TAIL_WEEKLY)


# ---------- helpers ----------
def to_weekly(df):
    return df.resample("W-FRI").last().dropna(how="all")


def rsi(series, n=14):
    d = series.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def pct(a, b):
    return (a / b - 1) * 100 if b and not np.isnan(b) and b != 0 else np.nan


def rnd(x, n=2):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)


# ---------- RRG ----------
def rrg(series, bench, window=RRG_WINDOW):
    """JdK-style RS-Ratio and RS-Momentum, both centred on 100.

    RS-Ratio  = 100 + z-score of relative strength (trend of outperformance)
    RS-Momentum = 100 + z-score of RS-Ratio's rate of change
    """
    df = pd.concat([series, bench], axis=1).dropna()
    if len(df) < window * 3:
        return None
    rs = 100 * df.iloc[:, 0] / df.iloc[:, 1]
    ratio = 100 + (rs - rs.rolling(window).mean()) / rs.rolling(window).std(ddof=0)
    roc = ratio.pct_change() * 100
    mom = 100 + (roc - roc.rolling(window).mean()) / roc.rolling(window).std(ddof=0)
    out = pd.DataFrame({"x": ratio, "y": mom}).dropna()
    return out if len(out) else None


def quadrant(x, y):
    if x >= 100 and y >= 100:
        return "Leading"
    if x >= 100:
        return "Weakening"
    if y < 100:
        return "Lagging"
    return "Improving"


def tail(frame, n):
    t = frame.tail(n)
    return {"d": [d.strftime("%d %b") for d in t.index],
            "x": [rnd(v) for v in t["x"]], "y": [rnd(v) for v in t["y"]]}


# ---------- core ----------
def liquid_mask(close, volume):
    turnover = (close * volume).rolling(20).mean().iloc[-1] / 1e7  # Rs crore
    history = close.notna().sum()
    return (turnover >= MIN_AVG_TURNOVER_CR) & (history >= MIN_HISTORY_DAYS), turnover


def sector_indices(close, universe, liquid):
    """Equal-weight index per sector from liquid constituents (base 100)."""
    rets = close.pct_change(fill_method=None).clip(-0.2, 0.2)
    out, members = {}, {}
    for sec, grp in universe.groupby("sector"):
        cols = [t for t in grp["ticker"] if t in rets.columns and liquid.get(t, False)]
        members[sec] = len(cols)
        if len(cols) < MIN_STOCKS_PER_SECTOR:
            continue
        r = rets[cols].mean(axis=1, skipna=True).fillna(0)
        out[sec] = 100 * (1 + r).cumprod()
    return pd.DataFrame(out), members


def stock_technicals(s, v):
    s = s.dropna()
    if len(s) < 25:
        return {}
    last = s.iloc[-1]
    def back(n):
        return s.iloc[-1 - n] if len(s) > n else np.nan
    dma = {n: s.rolling(n).mean().iloc[-1] if len(s) >= n else np.nan
           for n in (20, 50, 200)}
    yr = s.tail(252)
    vv = v.reindex(s.index)
    vol_ratio = vv.iloc[-1] / vv.tail(21).iloc[:-1].mean() if vv.notna().sum() > 21 else np.nan
    return {
        "price": rnd(last),
        "r1d": rnd(pct(last, back(1))), "r1w": rnd(pct(last, back(5))),
        "r1m": rnd(pct(last, back(21))), "r3m": rnd(pct(last, back(63))),
        "r1y": rnd(pct(last, back(250))),
        "rsi": rnd(rsi(s).iloc[-1], 1),
        "vs20": rnd(pct(last, dma[20]), 1), "vs50": rnd(pct(last, dma[50]), 1),
        "vs200": rnd(pct(last, dma[200]), 1),
        "from_high": rnd(pct(last, yr.max()), 1), "from_low": rnd(pct(last, yr.min()), 1),
        "vol_x": rnd(vol_ratio, 1),
    }


def build_analytics(close, volume, universe, benchmark):
    liquid, turnover = liquid_mask(close, volume)
    bench = close[benchmark].dropna()
    sidx, members = sector_indices(close, universe, liquid)

    # ---- sectors ----
    sectors = []
    for sec in sorted(universe["sector"].unique()):
        tick = [t for t in universe.loc[universe["sector"] == sec, "ticker"]
                if t in close.columns]
        last = close[tick].iloc[-1]
        prev = close[tick].iloc[-2]
        chg = (last / prev - 1).dropna()
        above50 = (close[tick].iloc[-1] > close[tick].rolling(50).mean().iloc[-1])
        above200 = (close[tick].iloc[-1] > close[tick].rolling(200).mean().iloc[-1])
        valid50 = close[tick].rolling(50).mean().iloc[-1].notna()
        valid200 = close[tick].rolling(200).mean().iloc[-1].notna()
        row = {
            "sector": sec, "count": len(tick), "liquid": members.get(sec, 0),
            "adv": int((chg > 0).sum()), "dec": int((chg < 0).sum()),
            "above50": rnd(100 * above50[valid50].mean(), 0) if valid50.any() else None,
            "above200": rnd(100 * above200[valid200].mean(), 0) if valid200.any() else None,
            "rrg_d": None, "rrg_w": None, "q_d": None, "q_w": None,
        }
        if sec in sidx:
            s = sidx[sec]
            row.update(stock_technicals(s, pd.Series(np.nan, index=s.index)))
            d = rrg(s, bench)
            w = rrg(to_weekly(s), to_weekly(bench))
            if d is not None:
                row["rrg_d"] = tail(d, TAIL_DAILY)
                row["q_d"] = quadrant(d["x"].iloc[-1], d["y"].iloc[-1])
            if w is not None:
                row["rrg_w"] = tail(w, TAIL_WEEKLY)
                row["q_w"] = quadrant(w["x"].iloc[-1], w["y"].iloc[-1])
        sectors.append(row)

    # ---- stocks ----
    stocks = []
    weekly_close = to_weekly(close)
    weekly_sidx = to_weekly(sidx) if len(sidx.columns) else sidx
    for r in universe.itertuples():
        t = r.ticker
        if t not in close.columns:
            continue
        row = {"sym": r.symbol, "name": r.name, "sector": r.sector,
               "industry": r.industry, "liquid": bool(liquid.get(t, False)),
               "turnover": rnd(turnover.get(t), 2)}
        row.update(stock_technicals(close[t], volume[t]))
        if row["liquid"] and r.sector in sidx:
            d = rrg(close[t], sidx[r.sector])
            w = rrg(weekly_close[t], weekly_sidx[r.sector])
            if d is not None:
                row["rrg_d"] = tail(d, 5)
                row["q_d"] = quadrant(d["x"].iloc[-1], d["y"].iloc[-1])
            if w is not None:
                row["rrg_w"] = tail(w, 5)
                row["q_w"] = quadrant(w["x"].iloc[-1], w["y"].iloc[-1])
        stocks.append(row)

    b = stock_technicals(bench, pd.Series(np.nan, index=bench.index))
    return sectors, stocks, b
