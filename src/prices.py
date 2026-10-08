"""Daily OHLCV for the whole universe from Yahoo Finance.

Downloads gently (small batches, few parallel connections, pauses) because
Yahoo throttles cloud servers such as GitHub's. Tickers that fail are retried
once at the end after a cool-down. Missing tickers are simply left out.
"""
import time

import pandas as pd

from .config import CACHE, PRICE_HISTORY

FIELDS = ["Close", "High", "Low", "Volume", "Open"]
BATCH = 40          # tickers per request
THREADS = 4         # parallel connections per batch
TIMEOUT = 30        # seconds per request
PAUSE = 2           # seconds between batches


def _download(tickers):
    import yfinance as yf
    df = yf.download(tickers, period=PRICE_HISTORY, interval="1d",
                     auto_adjust=True, group_by="column", threads=THREADS,
                     timeout=TIMEOUT, progress=False)
    if df is None or df.empty:
        return None
    if not isinstance(df.columns, pd.MultiIndex):  # single ticker
        df.columns = pd.MultiIndex.from_product([df.columns, tickers])
    return {f: df[f] for f in FIELDS if f in df.columns.get_level_values(0)}


def _run(tickers, parts, label):
    got = set()
    for i in range(0, len(tickers), BATCH):
        batch = tickers[i:i + BATCH]
        try:
            res = _download(batch)
        except Exception as e:
            print(f"  ! {label} batch {i}: {str(e)[:100]}")
            res = None
        if res and "Close" in res:
            ok = res["Close"].columns[res["Close"].notna().any()]
            got.update(ok)
            for f in FIELDS:
                if f in res:
                    parts[f].append(res[f][ok])
        if (i // BATCH) % 10 == 0 or i + BATCH >= len(tickers):
            print(f"  {label}: {min(i + BATCH, len(tickers))}/{len(tickers)} requested, {len(got)} received")
        time.sleep(PAUSE)
    return got


def fetch_prices(tickers, benchmark):
    """Return dict of DataFrames {"Close","High","Low","Volume"}, indexed by
    date, columns = tickers. The benchmark is included."""
    parts = {f: [] for f in FIELDS}
    allt = list(dict.fromkeys([benchmark] + list(tickers)))

    got = _run(allt, parts, "prices")
    missing = [t for t in allt if t not in got]
    if missing:
        print(f"  {len(missing)} tickers missing, waiting 60s then retrying them once")
        time.sleep(60)
        got |= _run(missing, parts, "retry")

    if benchmark not in got or len(got) < 0.3 * len(allt):
        raise SystemExit(
            f"Only {len(got)} of {len(allt)} tickers downloaded (benchmark ok: {benchmark in got}). "
            "Yahoo is blocking this server right now. Re-run later.")
    print(f"  prices done: {len(got)} of {len(allt)} tickers")

    out = {}
    for f in FIELDS:
        df = pd.concat(parts[f], axis=1).sort_index()
        df = df.loc[:, ~df.columns.duplicated()]
        df.index = pd.to_datetime(df.index).tz_localize(None)
        out[f] = df
    # Yahoo is often a day late for NSE: fill the latest trading days from
    # NSE's official end-of-day files before judging which days are complete.
    try:
        from .nse_eod import patch
        patch(out, benchmark)
    except Exception as e:
        print(f"  ! NSE end-of-day files not used: {str(e)[:100]}")
    # Drop "ghost" days: a row that only a few tickers have (e.g. a holiday row
    # from Yahoo, or a day neither Yahoo nor NSE has fully yet). Such a row
    # leaves every other stock with a blank last price.
    cnt = out["Close"].notna().sum(axis=1)
    real = cnt >= 0.5 * cnt.max()
    if (~real).any():
        print("  dropped sparse days:", ", ".join(d.strftime("%d %b %Y") for d in cnt.index[~real]))
        for f in FIELDS:
            out[f] = out[f][real]
    last = out["Close"].index[-1]
    print(f"  latest trading day in the data: {last:%a %d %b %Y} "
          f"({int(out['Close'].loc[last].notna().sum())} stocks)")
    cols = out["Close"].columns
    CACHE.mkdir(parents=True, exist_ok=True)
    for f in FIELDS:
        out[f] = out[f].reindex(index=out["Close"].index, columns=cols)
        try:
            out[f].to_parquet(CACHE / f"{f.lower()}.parquet")
        except Exception:
            pass
    return out


def fetch_intraday(tickers, benchmark):
    """Market-hours refresh: yesterday's full history from the cache plus the
    last 5 days (including today's bar so far) from Yahoo. Takes 1-3 minutes
    instead of downloading 5 years again. Falls back to a full download if
    there is no cache yet."""
    try:
        old = {f: pd.read_parquet(CACHE / f"{f.lower()}.parquet") for f in FIELDS}
    except Exception:
        print("  no cached history yet: doing a full download")
        return fetch_prices(tickers, benchmark)
    import yfinance as yf
    allt = list(dict.fromkeys([benchmark] + list(tickers)))
    new = {f: [] for f in FIELDS}
    got = 0
    for i in range(0, len(allt), 100):
        batch = allt[i:i + 100]
        try:
            df = yf.download(batch, period="5d", interval="1d", auto_adjust=True, group_by="column",
                             threads=THREADS, timeout=TIMEOUT, progress=False)
        except Exception as e:
            print(f"  ! intraday batch {i}: {str(e)[:80]}")
            df = None
        if df is not None and not df.empty:
            if not isinstance(df.columns, pd.MultiIndex):
                df.columns = pd.MultiIndex.from_product([df.columns, batch])
            ok = df["Close"].columns[df["Close"].notna().any()]
            got += len(ok)
            for f in FIELDS:
                if f in df.columns.get_level_values(0):
                    new[f].append(df[f][ok])
        time.sleep(1)
    print(f"  intraday prices: {got} of {len(allt)} tickers")
    if got < 0.3 * len(allt):
        print("  Yahoo returned too little; keeping the last saved prices")
        return {f: old[f] for f in FIELDS}
    out = {}
    for f in FIELDS:
        n = pd.concat(new[f], axis=1) if new[f] else pd.DataFrame()
        n = n.loc[:, ~n.columns.duplicated()]
        n.index = pd.to_datetime(n.index).tz_localize(None).normalize()
        o = old[f]
        out[f] = n.combine_first(o).sort_index()        # fresh values win where both exist
    cnt = out["Close"].notna().sum(axis=1)
    real = cnt >= 0.5 * cnt.max()
    if (~real).any():
        for f in FIELDS:
            out[f] = out[f][real]
    cols = out["Close"].columns
    for f in FIELDS:
        out[f] = out[f].reindex(index=out["Close"].index, columns=cols).astype(float)
    last = out["Close"].index[-1]
    print(f"  latest bar: {last:%a %d %b %Y} ({int(out['Close'].loc[last].notna().sum())} stocks)")
    return out
