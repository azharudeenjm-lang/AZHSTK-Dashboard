"""Daily OHLCV for the whole universe from Yahoo Finance, in batches."""
import time

import pandas as pd

from .config import BATCH_SIZE, CACHE, PRICE_HISTORY

FIELDS = ["Close", "High", "Low", "Volume"]


def _download(tickers):
    import yfinance as yf
    df = yf.download(tickers, period=PRICE_HISTORY, interval="1d",
                     auto_adjust=True, group_by="column", threads=True,
                     progress=False)
    if df is None or df.empty:
        return None
    if not isinstance(df.columns, pd.MultiIndex):  # single ticker
        df.columns = pd.MultiIndex.from_product([df.columns, tickers])
    return {f: df[f] for f in FIELDS}


def fetch_prices(tickers, benchmark):
    """Return dict of DataFrames {"Close","High","Low","Volume"}, indexed by
    date, columns = tickers. The benchmark is included. Failed tickers are missing.
    """
    parts = {f: [] for f in FIELDS}
    allt = list(dict.fromkeys([benchmark] + list(tickers)))
    for i in range(0, len(allt), BATCH_SIZE):
        batch = allt[i:i + BATCH_SIZE]
        for attempt in range(3):
            try:
                got = _download(batch)
                if got is not None:
                    for f in FIELDS:
                        parts[f].append(got[f])
                break
            except Exception as e:
                print(f"  ! batch {i}: {e}; retrying")
                time.sleep(5 * (attempt + 1))
        print(f"  prices {min(i + BATCH_SIZE, len(allt))}/{len(allt)}")
        time.sleep(1)

    out = {}
    for f in FIELDS:
        df = pd.concat(parts[f], axis=1).sort_index()
        df = df.loc[:, ~df.columns.duplicated()]
        df.index = pd.to_datetime(df.index).tz_localize(None)
        out[f] = df
    keep = out["Close"].dropna(axis=1, how="all").columns
    CACHE.mkdir(parents=True, exist_ok=True)
    for f in FIELDS:
        out[f] = out[f].reindex(index=out["Close"].index, columns=keep)
        out[f].to_parquet(CACHE / f"{f.lower()}.parquet")
    return out
