"""Fundamentals from Yahoo, cached and refreshed weekly (2000+ calls is slow)."""
import time
from datetime import datetime, timedelta

import pandas as pd

from .config import CACHE, FUNDAMENTALS_MAX_AGE_DAYS, FUNDAMENTALS_SLEEP_SEC

PATH = CACHE / "fundamentals.parquet"
COLS = ["symbol", "fetched", "pe", "pb", "roe", "de", "mcap_cr",
        "margin", "rev_g", "eps_g", "y_sector", "y_industry"]


def load():
    if PATH.exists():
        return pd.read_parquet(PATH)
    return pd.DataFrame(columns=COLS)


def _num(x, scale=1.0):
    try:
        return round(float(x) * scale, 2)
    except (TypeError, ValueError):
        return None


def _fetch_one(symbol):
    import yfinance as yf
    info = yf.Ticker(symbol + ".NS").info or {}
    de = _num(info.get("debtToEquity"))
    return {
        "symbol": symbol, "fetched": datetime.utcnow().strftime("%Y-%m-%d"),
        "pe": _num(info.get("trailingPE")),
        "pb": _num(info.get("priceToBook")),
        "roe": _num(info.get("returnOnEquity"), 100),
        "de": round(de / 100, 2) if de is not None else None,  # Yahoo gives %
        "mcap_cr": _num(info.get("marketCap"), 1e-7),
        "margin": _num(info.get("profitMargins"), 100),
        "rev_g": _num(info.get("revenueGrowth"), 100),
        "eps_g": _num(info.get("earningsGrowth"), 100),
        "y_sector": info.get("sector"), "y_industry": info.get("industry"),
    }


def refresh(symbols, max_calls=None, force=False):
    """Fetch fundamentals for stale/missing symbols. Returns full table."""
    df = load()
    cutoff = (datetime.utcnow() - timedelta(days=FUNDAMENTALS_MAX_AGE_DAYS)).strftime("%Y-%m-%d")
    fresh = set() if force else set(df.loc[df["fetched"] >= cutoff, "symbol"])
    todo = [s for s in symbols if s not in fresh]
    if max_calls:
        todo = todo[:max_calls]
    print(f"  fundamentals: {len(todo)} to fetch, {len(fresh)} fresh in cache")

    rows = []
    for i, sym in enumerate(todo, 1):
        try:
            rows.append(_fetch_one(sym))
        except Exception as e:
            print(f"  ! {sym}: {e}")
            time.sleep(10)  # likely rate-limited, back off
        time.sleep(FUNDAMENTALS_SLEEP_SEC)
        if i % 100 == 0 or i == len(todo):
            print(f"  fundamentals {i}/{len(todo)}")
            _save(df, rows)  # checkpoint so a crash keeps progress
    return _save(df, rows)


def _save(df, rows):
    if rows:
        new = pd.DataFrame(rows, columns=COLS)
        df = pd.concat([df[~df["symbol"].isin(new["symbol"])], new], ignore_index=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PATH, index=False)
    return df
