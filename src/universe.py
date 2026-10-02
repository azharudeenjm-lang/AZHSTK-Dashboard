"""Builds the stock universe (all NSE equities) and assigns each one a sector.

Sector source, in order of preference:
  1. data/sector_overrides.csv   - your own corrections (always win)
  2. NSE index constituent lists  - official NSE industry for ~750 stocks
  3. Yahoo sector/industry        - mapped onto NSE's industry names
  4. "Unclassified"
"""
import io
import time

import pandas as pd
import requests

from .config import CACHE, DATA

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/csv,text/html,*/*",
    "Referer": "https://www.nseindia.com/",
}

EQUITY_LIST_URLS = [
    "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
    "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
]

# Each list carries NSE's official "Industry" column
INDEX_LIST_URLS = [
    "https://www.niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv",
    "https://archives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv",
    "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv",
    "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "https://www.niftyindices.com/IndexConstituent/ind_niftymicrocap250_list.csv",
]

# Yahoo industry keywords -> NSE industry. Checked before the sector map.
YAHOO_INDUSTRY_MAP = [
    (("auto",), "Automobile and Auto Components"),
    (("textile", "apparel", "footwear"), "Textiles"),
    (("steel", "aluminum", "copper", "metal", "gold", "silver", "mining"),
     "Metals & Mining"),
    (("coal", "oil", "gas", "refining"), "Oil Gas & Consumable Fuels"),
    (("building materials", "cement"), "Construction Materials"),
    (("engineering & construction", "infrastructure"), "Construction"),
    (("real estate",), "Realty"),
    (("entertainment", "broadcasting", "publishing", "advertising"),
     "Media Entertainment & Publication"),
    (("restaurant", "lodging", "travel", "leisure", "resort", "retail",
      "education", "personal services"), "Consumer Services"),
    (("airline", "trucking", "shipping", "railroad", "freight", "airport",
      "logistics", "staffing", "consulting"), "Services"),
    (("paper", "lumber"), "Forest Materials"),
    (("chemical", "agricultural inputs", "fertili"), "Chemicals"),
    (("telecom",), "Telecommunication"),
    (("utilities",), "Power"),
    (("drug", "pharma", "biotech", "medical", "diagnostic", "health"),
     "Healthcare"),
    (("bank", "insurance", "capital markets", "credit", "asset management",
      "financial"), "Financial Services"),
    (("software", "information technology", "semiconductor", "computer"),
     "Information Technology"),
]

YAHOO_SECTOR_MAP = {
    "Technology": "Information Technology",
    "Financial Services": "Financial Services",
    "Healthcare": "Healthcare",
    "Utilities": "Power",
    "Real Estate": "Realty",
    "Energy": "Oil Gas & Consumable Fuels",
    "Communication Services": "Telecommunication",
    "Consumer Defensive": "Fast Moving Consumer Goods",
    "Consumer Cyclical": "Consumer Durables",
    "Industrials": "Capital Goods",
    "Basic Materials": "Chemicals",
}


def map_yahoo(sector, industry):
    """Translate Yahoo's sector/industry into an NSE-style industry name."""
    ind = (industry or "").lower()
    for keys, nse in YAHOO_INDUSTRY_MAP:
        if any(k in ind for k in keys):
            return nse
    return YAHOO_SECTOR_MAP.get(sector or "", None)


def _get_csv(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.ok and b"," in r.content[:500]:
                return pd.read_csv(io.BytesIO(r.content))
        except Exception as e:  # network hiccup, try again
            print(f"  ! {url}: {e}")
        time.sleep(2 * (i + 1))
    return None


def fetch_equity_list():
    for url in EQUITY_LIST_URLS:
        df = _get_csv(url)
        if df is not None:
            df.columns = [c.strip() for c in df.columns]
            df = df[df["SERIES"].str.strip().isin(["EQ", "BE"])]
            return pd.DataFrame({
                "symbol": df["SYMBOL"].str.strip(),
                "name": df["NAME OF COMPANY"].str.strip(),
            })
    return None


def fetch_nse_industries():
    frames = []
    for url in INDEX_LIST_URLS:
        df = _get_csv(url)
        if df is not None and "Industry" in df.columns:
            df.columns = [c.strip() for c in df.columns]
            frames.append(df[["Symbol", "Industry"]])
    if not frames:
        return {}
    allx = pd.concat(frames).drop_duplicates("Symbol")
    return dict(zip(allx["Symbol"].str.strip(), allx["Industry"].str.strip()))


def load_overrides():
    path = DATA / "sector_overrides.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, comment="#")
    return dict(zip(df["symbol"].str.strip(), df["sector"].str.strip()))


def build_universe(yahoo_meta=None):
    """Return DataFrame: symbol, name, ticker, sector, industry.

    yahoo_meta: optional DataFrame (symbol, y_sector, y_industry) from the
    fundamentals cache, used for stocks that NSE lists don't classify.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / "universe_raw.csv"

    eq = fetch_equity_list()
    if eq is None:
        if not cached.exists():
            raise RuntimeError("Could not download NSE equity list and no cache exists.")
        print("  using cached equity list")
        eq = pd.read_csv(cached)[["symbol", "name"]]
    else:
        eq.to_csv(cached, index=False)

    nse_ind_cache = CACHE / "nse_industry.csv"
    nse_ind = fetch_nse_industries()
    if nse_ind:
        pd.Series(nse_ind, name="industry").rename_axis("symbol").to_csv(nse_ind_cache)
    elif nse_ind_cache.exists():
        print("  using cached NSE industry map")
        s = pd.read_csv(nse_ind_cache)
        nse_ind = dict(zip(s["symbol"], s["industry"]))

    overrides = load_overrides()
    ymeta = {}
    if yahoo_meta is not None and len(yahoo_meta):
        ymeta = {r.symbol: (r.y_sector, r.y_industry)
                 for r in yahoo_meta.itertuples()}

    sectors, industries = [], []
    for sym in eq["symbol"]:
        ys, yi = ymeta.get(sym, (None, None))
        sec = overrides.get(sym) or nse_ind.get(sym) or map_yahoo(ys, yi) or "Unclassified"
        sectors.append(sec)
        industries.append(yi if isinstance(yi, str) and yi else sec)

    eq["sector"] = sectors
    eq["industry"] = industries
    eq["ticker"] = eq["symbol"] + ".NS"
    return eq.reset_index(drop=True)
