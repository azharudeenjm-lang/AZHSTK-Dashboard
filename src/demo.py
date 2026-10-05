"""Synthetic market so the dashboard can be tested without internet."""
import numpy as np
import pandas as pd

SECTORS = ["Chemicals", "Information Technology", "Financial Services", "Healthcare",
           "Automobile and Auto Components", "Capital Goods", "Fast Moving Consumer Goods",
           "Metals & Mining", "Realty", "Power", "Oil Gas & Consumable Fuels",
           "Consumer Durables", "Textiles", "Telecommunication"]


def make_demo(benchmark, n_per=40, days=1250, seed=7):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    days = len(idx)
    mkt = rng.normal(0.0004, 0.009, days)
    close, vol, rows, fund = {}, {}, [], []
    for si, sec in enumerate(SECTORS):
        phase = rng.uniform(0, 2 * np.pi)
        cyc = 0.0012 * np.sin(np.linspace(0, 4 * np.pi, days) + phase)
        sec_f = rng.normal(0, 0.006, days) + cyc
        for k in range(n_per):
            sym = f"{sec[:3].upper()}{k:02d}"
            beta = rng.uniform(0.7, 1.4)
            r = beta * mkt + sec_f + rng.normal(0, 0.015, days)
            p = rng.uniform(50, 3000) * np.exp(np.cumsum(r))
            close[sym + ".NS"] = p
            vol[sym + ".NS"] = rng.lognormal(11 if k < 30 else 7, 0.5, days)
            rows.append({"symbol": sym, "name": f"{sec} Demo {k} Ltd", "sector": sec,
                         "industry": sec, "ticker": sym + ".NS"})
            fund.append({"symbol": sym, "pe": round(rng.uniform(8, 70), 1),
                         "pb": round(rng.uniform(0.8, 12), 2), "roe": round(rng.uniform(-5, 30), 1),
                         "de": round(rng.uniform(0, 1.8), 2), "mcap_cr": round(rng.lognormal(8, 1.5)),
                         "margin": round(rng.uniform(-3, 25), 1), "rev_g": round(rng.uniform(-15, 40), 1),
                         "eps_g": round(rng.uniform(-40, 60), 1)})
    close[benchmark] = 20000 * np.exp(np.cumsum(mkt))
    close = pd.DataFrame(close, index=idx)
    volume = pd.DataFrame(vol, index=idx).reindex(columns=close.columns)
    spread = np.abs(rng.normal(0, 0.008, close.shape))
    high = close * (1 + spread)
    low = close * (1 - np.abs(rng.normal(0, 0.008, close.shape)))
    news = {s: [{"t": f"Sample headline about {s.lower()} stocks", "u": "https://news.google.com",
                 "s": "Demo", "d": "02 Oct"}] for s in SECTORS}
    opn = close.shift(1) * (1 + rng.normal(0, 0.004, close.shape))
    opn = opn.fillna(close).clip(lower=low, upper=high)
    px = {"Close": close, "High": high, "Low": low, "Volume": volume, "Open": opn}
    return pd.DataFrame(rows), px, pd.DataFrame(fund), news, {}
