"""Official NSE end-of-day prices, used to fill in the latest trading days.

Yahoo's daily history is often a day late for NSE stocks: at night it may
have the latest candle for only some of them. NSE publishes an official
end-of-day file (the "bhavcopy") for every listed stock around 6-7 PM IST,
plus a file with every index close. This module downloads those files for
the last few trading days and fills any missing open/high/low/close/volume.

Files tried, in order (NSE has changed formats over the years):
  stocks   1. content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip
           2. products/content/sec_bhavdata_full_DDMMYYYY.csv
  indices  content/indices/ind_close_all_DDMMYYYY.csv
Downloaded files are kept in data/cache/nse_eod/ so a re-run is quick.
"""
import io
import time
import zipfile
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

from .config import CACHE

DIR = CACHE / "nse_eod"
HOSTS = ["https://nsearchives.nseindia.com", "https://archives.nseindia.com"]
HEAD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "*/*", "Referer": "https://www.nseindia.com/"}
SERIES = {"EQ", "BE", "BZ", "SM", "ST"}
INDEX_NAME = {"^NSEI": "Nifty 50", "^CRSLDX": "Nifty 500"}
IST = timezone(timedelta(hours=5, minutes=30))


def _get(session, path):
    for host in HOSTS:
        try:
            r = session.get(host + path, timeout=30)
            if r.ok and len(r.content) > 200:
                return r.content
        except Exception:
            pass
        time.sleep(1)
    return None


def _parse_udiff(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        df = pd.read_csv(z.open(z.namelist()[0]))
    df.columns = [c.strip() for c in df.columns]
    df = df[df["SctySrs"].astype(str).str.strip().isin(SERIES)]
    return pd.DataFrame({"sym": df["TckrSymb"].astype(str).str.strip(),
                         "Open": df["OpnPric"], "High": df["HghPric"], "Low": df["LwPric"],
                         "Close": df["ClsPric"], "Volume": df["TtlTradgVol"]})


def _parse_full(raw):
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [c.strip() for c in df.columns]
    df = df[df["SERIES"].astype(str).str.strip().isin(SERIES)]
    num = lambda c: pd.to_numeric(df[c].astype(str).str.strip(), errors="coerce")
    return pd.DataFrame({"sym": df["SYMBOL"].astype(str).str.strip(),
                         "Open": num("OPEN_PRICE"), "High": num("HIGH_PRICE"), "Low": num("LOW_PRICE"),
                         "Close": num("CLOSE_PRICE"), "Volume": num("TTL_TRD_QNTY")})


def _parse_index(raw, name):
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [c.strip() for c in df.columns]
    row = df[df["Index Name"].astype(str).str.strip().str.lower() == name.lower()]
    if row.empty:
        return None
    r = row.iloc[0]
    num = lambda k: pd.to_numeric(str(r[k]).replace(",", "").strip(), errors="coerce")
    return {"Open": num("Open Index Value"), "High": num("High Index Value"),
            "Low": num("Low Index Value"), "Close": num("Closing Index Value"), "Volume": 0}


def _stocks(session, d):
    cache = DIR / f"eq_{d:%Y%m%d}.csv"
    if cache.exists():
        return pd.read_csv(cache)
    df = None
    raw = _get(session, f"/content/cm/BhavCopy_NSE_CM_0_0_0_{d:%Y%m%d}_F_0000.csv.zip")
    if raw:
        try:
            df = _parse_udiff(raw)
        except Exception as e:
            print(f"  ! NSE file {d:%d %b} (new format): {str(e)[:80]}")
    if df is None:
        raw = _get(session, f"/products/content/sec_bhavdata_full_{d:%d%m%Y}.csv")
        if raw:
            try:
                df = _parse_full(raw)
            except Exception as e:
                print(f"  ! NSE file {d:%d %b} (full format): {str(e)[:80]}")
    if df is not None and len(df):
        DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache, index=False)
        return df
    return None


def _index(session, d, name):
    raw = _get(session, f"/content/indices/ind_close_all_{d:%d%m%Y}.csv")
    if not raw:
        return None
    try:
        return _parse_index(raw, name)
    except Exception:
        return None


def recent_weekdays(n=5, now=None):
    """The last n weekdays whose end-of-day file should exist (after 7 PM IST)."""
    now = now or datetime.now(IST)
    d = now.date() if now.hour >= 19 else now.date() - timedelta(days=1)
    out = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return sorted(out)


def patch(out, benchmark, days=None, session=None):
    """Fill missing prices for recent trading days from NSE's official files.

    out: {"Close","High","Low","Volume","Open": DataFrame(date x ticker)}.
    Returns the list of dates that were filled or added.
    """
    session = session or requests.Session()
    session.headers.update(HEAD)
    try:
        session.get("https://www.nseindia.com/", timeout=15)
    except Exception:
        pass
    cols = out["Close"].columns
    filled = []
    for d in days or recent_weekdays():
        eq = _stocks(session, d)
        if eq is None:
            continue                       # holiday, weekend, or not published yet
        ts = pd.Timestamp(d)
        eq = eq.assign(t=eq["sym"] + ".NS").drop_duplicates("t").set_index("t")
        eq = eq[eq.index.isin(cols)]
        if ts not in out["Close"].index:
            for f in out:
                out[f].loc[ts] = pd.NA
                out[f] = out[f].sort_index()
        before = int(out["Close"].loc[ts].notna().sum())
        for f in ("Open", "High", "Low", "Close", "Volume"):
            if f not in out:
                continue
            row = out[f].loc[ts]
            fill = eq[f].reindex(cols)
            out[f].loc[ts] = row.where(row.notna(), fill).astype(float)
        if benchmark in cols and pd.isna(out["Close"].at[ts, benchmark]):
            ix = _index(session, d, INDEX_NAME.get(benchmark, "Nifty 50"))
            if ix:
                for f, v in ix.items():
                    if f in out:
                        out[f].at[ts, benchmark] = v
        after = int(out["Close"].loc[ts].notna().sum())
        if after > before:
            filled.append(ts)
            print(f"  NSE end-of-day file {d:%a %d %b}: filled {after - before} stocks ({after} now have prices)")
    for f in out:
        out[f] = out[f].astype(float)
    return filled


def price_bands():
    """{symbol: daily price band %} from NSE's security list (circuit limits).
    Stocks with "No Band" (most F&O stocks) are left out."""
    cache = DIR / "sec_list.csv"
    session = requests.Session()
    session.headers.update(HEAD)
    raw = _get(session, "/content/equities/sec_list.csv")
    if raw:
        DIR.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(raw)
    elif cache.exists():
        raw = cache.read_bytes()
    if not raw:
        print("  circuit bands: NSE list not available")
        return {}
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [c.strip().lower() for c in df.columns]
    band = pd.to_numeric(df["band"].astype(str).str.strip(), errors="coerce")
    out = {str(s).strip(): float(b) for s, b in zip(df["symbol"], band) if pd.notna(b) and b > 0}
    print(f"  circuit bands: {len(out)} stocks")
    return out
