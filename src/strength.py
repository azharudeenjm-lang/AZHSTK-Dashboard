"""Relative strength rank (1-99) and the market regime banner."""
import numpy as np
import pandas as pd

from .config import RS_WEIGHTS


def rs_rank(close, liquid):
    """Weighted 3/6/9/12-month performance, ranked 1-99 against all liquid stocks.

    99 = stronger than 99% of the market. Stocks with under 3 months of
    history get no rank.
    """
    c = close.ffill()
    score = pd.Series(0.0, index=c.columns)
    weight = pd.Series(0.0, index=c.columns)
    for n, w in RS_WEIGHTS.items():
        if len(c) > n:
            r = c.iloc[-1] / c.iloc[-1 - n] - 1
            ok = r.notna()
            score[ok] += w * r[ok]
            weight[ok] += w
    score = score.where(weight >= 0.4) / weight.where(weight >= 0.4)
    pool = score[liquid.reindex(score.index).fillna(False) & score.notna()]
    if pool.empty:
        return {}
    pct = score.apply(lambda v: np.nan if pd.isna(v) else (pool < v).mean())
    return {t: int(min(99, max(1, round(p * 98 + 1)))) for t, p in pct.items() if pd.notna(p)}


def regime(close, benchmark, liquid):
    """Risk-on / Neutral / Risk-off from index trend and market breadth."""
    b = close[benchmark].dropna()
    stocks = close.drop(columns=[benchmark]).loc[:, lambda d: liquid.reindex(d.columns).fillna(False)]
    items, score = [], 0

    def add(ok, text, bad=None):
        nonlocal score
        if ok:
            score += 1
        elif bad:
            score -= 1
        items.append({"ok": bool(ok), "bad": bool(bad and not ok), "t": text})

    if len(b) >= 200:
        d50, d200 = b.rolling(50).mean().iloc[-1], b.rolling(200).mean().iloc[-1]
        add(b.iloc[-1] > d200, f"NIFTY {'above' if b.iloc[-1] > d200 else 'below'} its 200-day average", b.iloc[-1] < d200 * 0.97)
        add(d50 > d200, f"NIFTY 50-day average {'above' if d50 > d200 else 'below'} the 200-day")
    a200 = (stocks.iloc[-1] > stocks.rolling(200).mean().iloc[-1])[stocks.rolling(200).mean().iloc[-1].notna()]
    p200 = float(a200.mean() * 100) if len(a200) else None
    if p200 is not None:
        add(p200 >= 50, f"{p200:.0f}% of liquid stocks above their 200-day average", p200 < 35)
    hi, lo = stocks.tail(252).max(), stocks.tail(252).min()
    last = stocks.iloc[-1]
    nh, nl = int((last >= hi * 0.99).sum()), int((last <= lo * 1.01).sum())
    add(nh > nl, f"{nh} stocks near 52-week highs vs {nl} near lows", nl > 2 * max(nh, 1))
    state = "Risk-on" if score >= 3 else "Risk-off" if score <= 0 else "Neutral"
    return {"state": state, "score": score, "items": items, "above200": p200, "nh": nh, "nl": nl,
            "asof": close.index[-1].strftime("%Y-%m-%d")}
