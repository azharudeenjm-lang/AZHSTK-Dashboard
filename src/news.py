"""Headlines and news triggers.

Sector news and top-mover news come from Google News RSS (as before).

Stock news triggers (shown in each stock's pop-up and usable in the Screener):
  1. NSE company filings (results, orders, acquisitions, dividends ...), when
     NSE lets GitHub's servers in; otherwise skipped quietly.
  2. Market-news RSS feeds (Economic Times, Moneycontrol, Mint, Business
     Standard, Financial Express, BusinessLine) plus a few Google News searches
     for typical triggers (order wins, results, upgrades, SEBI action ...).
     Each headline is matched to stocks by company name or NSE symbol.
  3. The per-stock Google News headlines fetched for the day's top movers.
Every item gets a type (results, order win, deal, corporate action, broker
view, regulatory, management, other) and a simple tone (+ / - / neutral)
from keywords. Items are kept for 30 days in data/cache/news_items.json so
each daily run adds to them.
"""
import json
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from .config import CACHE, NEWS_PER_SECTOR

IST = timezone(timedelta(hours=5, minutes=30))
KEEP_DAYS = 30
STORE = CACHE / "news_items.json"

SECTOR_QUERY = {
    "Fast Moving Consumer Goods": "FMCG",
    "Oil Gas & Consumable Fuels": "oil gas",
    "Media Entertainment & Publication": "media",
    "Automobile and Auto Components": "auto",
    "Information Technology": "IT",
}

MARKET_FEEDS = [
    "https://economictimes.indiatimes.com/markets/stocks/news/rssfeeds/2146842.cms",
    "https://economictimes.indiatimes.com/markets/stocks/earnings/rssfeeds/2143429.cms",
    "https://www.moneycontrol.com/rss/business.xml",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://www.moneycontrol.com/rss/results.xml",
    "https://www.moneycontrol.com/rss/buzzingstocks.xml",
    "https://www.livemint.com/rss/markets",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://www.financialexpress.com/market/feed/",
    "https://www.thehindubusinessline.com/markets/stock-markets/feeder/default.rss",
]
GN_QUERIES = ["bags order NSE", "wins order worth crore", "Q2 results net profit", "quarterly results shares",
              "target price upgrade stock", "brokerage downgrade stock", "SEBI order company shares",
              "board approves acquisition", "record date dividend bonus split", "block deal NSE shares",
              "stocks to watch today"]

# ---------------------------------------------------------------- screener metadata
META = [
    ("nw_any", "In the news (any headline or filing)", "e"),
    ("nw_pos", "Positive news", "e"),
    ("nw_neg", "Negative news", "e"),
    ("nw_res", "Results announced / results news", "e"),
    ("nw_ord", "Order or contract win", "e"),
    ("nw_deal", "Deal: acquisition, merger, stake sale or fund raise", "e"),
    ("nw_corp", "Corporate action: dividend, bonus, split or buyback", "e"),
    ("nw_rat", "Broker view: upgrade, downgrade or target change", "e"),
    ("nw_reg", "Regulatory or legal news (SEBI, tax, court ...)", "e"),
    ("nw_fil", "NSE filing by the company", "e"),
]
KINDS = {"res": "Results", "ord": "Order win", "deal": "Deal", "corp": "Corporate action", "rat": "Broker view",
         "reg": "Regulatory", "mgmt": "Management", "oth": "News"}
_K = [
    ("res", r"\bresults?\b|\bq[1-4]\b|quarter|net profit|profit (rises|jumps|falls|declines|up|down|grows|surges|drops)|net loss|revenue|earnings|ebitda|financial result"),
    ("ord", r"\border(s)?\b|contract|\bbags?\b|\bwins?\b|secures?|letter of (award|intent)|\bloa\b|tender|bagging"),
    ("deal", r"acqui|merger|amalgamat|\bstake\b|takeover|demerger|\bqip\b|rights issue|preferential|fund ?rais|\bncds?\b|\bipo\b|joint venture|\bjv\b|\bbonds?\b|raises? (₹|rs)"),
    ("corp", r"dividend|bonus|stock split|\bsplit\b|buy-?back|record date"),
    ("rat", r"upgrade|downgrade|target price|\btarget\b|\brating\b|\bbuy call\b|initiat|brokerage|overweight|underweight|outperform|underperform"),
    ("reg", r"\bsebi\b|penalt|\bfined?\b|probe|\braid|\bed\b|income tax|gst (notice|demand)|\bcourt\b|\bnclt\b|insolvency|fraud|\bban\b|show cause|search operation"),
    ("mgmt", r"\bceo\b|\bcfo\b|\bmd\b|chairman|resign|appoint|steps down|key managerial"),
]
_POS = r"surge|jump|soar|rall(y|ies)|\bgains?\b|\brises?\b|record|beats?\b|upgrade|\bwins?\b|\bbags?\b|secures?|approv|strong|higher|growth|\braised?\b|\bhike|bonus|buy-?back|outperform|overweight|turnaround|expan"
_NEG = r"\bfalls?\b|slump|plunge|tank|\bdrops?\b|declin|\bdown\b|\bloss\b|miss(es)?\b|downgrade|penalt|fraud|resign|probe|\braid|\bcuts?\b|weak|lower|sell-?off|underperform|underweight|default|insolvency|show cause|\bban\b"
# filings that are routine paperwork: not news
_BORING = re.compile(r"trading window|certificate|newspaper|compliance|loss of share|duplicate share|"
                     r"copy of|regulation 74|esop|esos|change in (registrar|rta)|investor complaints|closure of", re.I)
# NSE symbols that are also common words/acronyms in headlines
_SYM_SKIP = {"BSE", "NSE", "IPO", "GDP", "RBI", "FII", "DII", "GST", "CEO", "CFO", "EV", "AI", "FY", "US", "UK", "IT",
             "MD", "ED", "PAT", "NII", "EPS", "ROE", "QIP", "NCD", "LOA", "JV", "MF", "NAV", "SIP", "ETF", "OFS",
             "USA", "INR", "USD", "CPI", "WPI", "PMI", "FPI", "SME", "PSU", "MSCI", "OMC", "EMS", "NBFC", "HFC"}
_ALIAS = {"RIL": "RELIANCE", "HUL": "HINDUNILVR", "SBI": "SBIN", "L&T": "LT", "M&M": "M&M", "Airtel": "BHARTIARTL",
          "Bharti Airtel": "BHARTIARTL", "Infy": "INFY", "Maruti": "MARUTI", "Kotak Bank": "KOTAKBANK",
          "IndiGo": "INDIGO", "Zomato": "ETERNAL", "Paytm": "PAYTM", "Nykaa": "NYKAA", "LIC": "LICI",
          "Coal India": "COALINDIA", "HAL": "HAL", "BEL": "BEL", "IOC": "IOC", "IndusInd Bank": "INDUSINDBK"}
_STOPWORDS = {"Indian", "India", "Bharat", "National", "General", "Global", "United", "Standard", "Capital", "Power",
              "Finance", "International", "Universal", "Premier", "Supreme", "Central", "Western", "Eastern",
              "Southern", "Northern", "Modern", "Advanced", "Allied", "Asian", "Continental", "Diamond", "Future",
              "Sterling", "Prime", "Royal", "Star", "Sun", "Swan", "Kitex", "Hindustan", "Gujarat", "Bombay",
              "Delhi", "Mumbai", "Chennai", "Madras", "Kerala", "Punjab", "Rajasthan", "Orient", "Oriental", "Steel",
              "Cement", "Textiles", "Motors", "Foods", "Pharma", "Chemicals", "Energy", "Infra", "Metal", "Metals"}
_GENERIC_TAIL = {"Industries", "Enterprises", "Corporation", "Company", "Holdings", "Limited", "Ltd"}


def _now():
    return datetime.now(IST)


def _feed(query, n):
    import feedparser
    url = ("https://news.google.com/rss/search?q=" + quote_plus(query) +
           "+when:7d&hl=en-IN&gl=IN&ceid=IN:en")
    return _parse(url, n, query)


def _parse(url, n, label=""):
    import feedparser
    try:
        f = feedparser.parse(url, agent="Mozilla/5.0 (AZHSTK news reader)")
    except Exception as e:
        print(f"  ! news {label or url[:60]}: {e}")
        return []
    items = []
    for e in f.entries[:n]:
        src = getattr(e, "source", {}).get("title", "") if hasattr(e, "source") else ""
        if not src:
            src = (getattr(f, "feed", {}) or {}).get("title", "")[:40]
        title = getattr(e, "title", "") or ""
        if src and title.endswith(" - " + src):
            title = title[: -len(src) - 3]
        pp = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
        items.append({"t": title.strip(), "u": getattr(e, "link", ""), "s": src,
                      "d": time.strftime("%d %b", pp) if pp else "",
                      "iso": time.strftime("%Y-%m-%d", pp) if pp else _now().strftime("%Y-%m-%d")})
    return items


def sector_news(sectors):
    out = {}
    for sec in sectors:
        q = SECTOR_QUERY.get(sec, sec)
        out[sec] = _feed(f'India "{q}" sector stocks', NEWS_PER_SECTOR)
        time.sleep(1)
    return out


def stock_news(stocks):
    """stocks: list of (symbol, company name)."""
    out = {}
    for sym, name in stocks:
        short = name.replace(" Limited", "").replace(" Ltd", "")
        out[sym] = _feed(f'"{short}" NSE', 4)
        time.sleep(1)
    return out


# ---------------------------------------------------------------- classification
def classify(text):
    """(kind code, tone +1/0/-1) from a headline or filing subject."""
    low = text.lower()
    kind = next((k for k, rx in _K if re.search(rx, low)), "oth")
    pos, neg = len(re.findall(_POS, low)), len(re.findall(_NEG, low))
    return kind, (1 if pos > neg else -1 if neg > pos else 0)


def _clean_name(name):
    n = re.sub(r"\s*\((india|i)\)\s*", " ", name, flags=re.I)
    n = re.sub(r"\b(limited|ltd\.?)\s*$", "", n.strip(), flags=re.I).strip(" .,")
    n = re.sub(r"^the\s+", "", n, flags=re.I)
    return re.sub(r"\s+", " ", n)


class Matcher:
    """Finds which listed companies a headline is about (longest name wins)."""

    def __init__(self, stocks):
        names = {}
        for sym, name in stocks:
            nm = _clean_name(name or "")
            if len(nm) >= 4 and nm not in _STOPWORDS:
                names[nm] = sym
            words = nm.split()
            if len(words) >= 2 and words[-1] in _GENERIC_TAIL:
                short = " ".join(words[:-1])
                if len(short) >= 6 and short not in _STOPWORDS and short not in names:
                    names[short] = sym
        known = {s for s, _ in stocks}
        for a, s in _ALIAS.items():
            if s in known:
                names[a] = s
        self.names = names
        alts = sorted(names, key=len, reverse=True)
        self.rx = re.compile(r"(?<![A-Za-z0-9&])(" + "|".join(re.escape(a) for a in alts) + r")(?:'s|’s)?(?![A-Za-z0-9&])") if alts else None
        self.syms = {s for s in known if s.isalpha() and len(s) >= 3 and s not in _SYM_SKIP}

    def find(self, text):
        out = []
        if self.rx:
            for m in self.rx.finditer(text):
                s = self.names[m.group(1)]
                if s not in out:
                    out.append(s)
        for tok in re.findall(r"\b[A-Z][A-Z&]{2,}\b", text):
            if tok in self.syms and tok not in out:
                out.append(tok)
        return out


# ---------------------------------------------------------------- sources
def nse_filings(days=4):
    """[(symbol, iso date, subject, url)] from NSE's corporate-announcements feed."""
    import requests
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                      "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9",
                      "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-announcements"})
    try:
        s.get("https://www.nseindia.com/", timeout=15)
        s.get("https://www.nseindia.com/companies-listing/corporate-filings-announcements", timeout=15)
    except Exception:
        pass
    to, fr = _now(), _now() - timedelta(days=days)
    url = ("https://www.nseindia.com/api/corporate-announcements?index=equities"
           f"&from_date={fr:%d-%m-%Y}&to_date={to:%d-%m-%Y}")
    try:
        r = s.get(url, timeout=30)
        data = r.json() if r.ok else []
    except Exception as e:
        print(f"  NSE filings not available ({str(e)[:60]})")
        return []
    if isinstance(data, dict):
        data = data.get("data") or []
    out = []
    for x in data:
        sym, subj = str(x.get("symbol", "")).strip(), str(x.get("desc", "")).strip()
        txt = str(x.get("attchmntText", "") or "").strip()
        if not sym or _BORING.search(subj + " " + txt[:120]):
            continue
        try:
            iso = datetime.strptime(str(x.get("an_dt") or x.get("sort_date"))[:11], "%d-%b-%Y").strftime("%Y-%m-%d")
        except Exception:
            iso = _now().strftime("%Y-%m-%d")
        head = subj if not txt else f"{subj}: {txt[:160]}"
        out.append((sym, iso, head, x.get("attchmntFile") or ""))
    print(f"  NSE filings: {len(out)} (last {days} days)")
    return out


def _load():
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def stock_triggers(stocks, mover_news=None, demo=False):
    """stocks: [(symbol, name)]. Returns {symbol: [item, ...]} newest first, last 30 days.
    item: {"d": "YYYY-MM-DD", "t": title, "u": url, "s": source, "k": kind, "m": tone, "f": 1 if NSE filing}"""
    store = {} if demo else _load()
    add = []
    if demo:
        add = _demo_items(stocks)
    else:
        m = Matcher(stocks)
        for sym, iso, head, url in nse_filings():
            add.append((sym, {"d": iso, "t": head, "u": url, "s": "NSE filing", "f": 1}))
        heads = []
        for u in MARKET_FEEDS:
            heads += _parse(u, 80)
            time.sleep(0.5)
        for q in GN_QUERIES:
            heads += _feed(q, 60)
            time.sleep(1)
        n_match = 0
        for it in heads:
            for sym in m.find(it["t"])[:3]:          # a "stocks to watch" list names many; keep the first few
                add.append((sym, {"d": it["iso"], "t": it["t"], "u": it["u"], "s": it["s"]}))
                n_match += 1
        for sym, items in (mover_news or {}).items():
            for it in items:
                add.append((sym, {"d": it.get("iso") or _now().strftime("%Y-%m-%d"), "t": it["t"], "u": it["u"], "s": it["s"]}))
        print(f"  news: {len(heads)} market headlines read, {n_match} matched to stocks")
    for sym, it in add:
        it["k"], it["m"] = classify(it["t"])
        lst = store.setdefault(sym, [])
        key = re.sub(r"\W+", "", it["t"].lower())[:90]
        if any(re.sub(r"\W+", "", x["t"].lower())[:90] == key for x in lst):
            continue
        lst.append(it)
    cut = (_now() - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    store = {s: sorted([x for x in v if x["d"] >= cut], key=lambda x: x["d"], reverse=True)[:25]
             for s, v in store.items()}
    store = {s: v for s, v in store.items() if v}
    if not demo:
        try:
            STORE.parent.mkdir(parents=True, exist_ok=True)
            STORE.write_text(json.dumps(store), encoding="utf-8")
        except Exception:
            pass
    print(f"  news triggers: {len(store)} stocks with news in the last {KEEP_DAYS} days")
    return store


def _demo_items(stocks):
    import random
    rnd = random.Random(3)
    samples = [("{n} Q2 results: net profit jumps 32% YoY, revenue up 18%", None),
               ("{n} bags order worth ₹450 crore from NHAI", None),
               ("{n} shares slump after SEBI penalty in disclosure case", None),
               ("Brokerage upgrades {n} to buy, raises target price", None),
               ("{n} board approves acquisition of 51% stake in logistics firm", None),
               ("{n} announces record date for 1:1 bonus issue", None),
               ("{n}: CFO resigns, company appoints interim replacement", None),
               ("Outcome of Board Meeting: {n} approves fund raise via QIP", "NSE filing")]
    out = []
    for i, (sym, name) in enumerate(stocks[::4][:120]):
        for j in range(rnd.randint(1, 3)):
            t, src = samples[rnd.randrange(len(samples))]
            d = (_now() - timedelta(days=rnd.randint(0, 20))).strftime("%Y-%m-%d")
            it = {"d": d, "t": t.format(n=_clean_name(name)), "u": "https://www.nseindia.com/", "s": src or "Demo news"}
            if src:
                it["f"] = 1
            out.append((sym, it))
    return out


# ---------------------------------------------------------------- screener events
def events(store, tickers, dates_d, dates_w):
    """{tf: {ticker: {cond: bars ago}}} for news items within the event window."""
    from bisect import bisect_left
    from .config import SCREENER_EVENT_BARS as NB
    res = {"d": {}, "w": {}}
    known = set(tickers)
    for tf, dates in (("d", dates_d), ("w", dates_w)):
        if not dates:
            continue
        n = len(dates)
        for sym, items in store.items():
            t = sym + ".NS"
            if t not in known:
                continue
            row = {}
            for it in items:
                j = bisect_left(dates, it["d"])     # the bar that includes (or follows) the news day
                ago = max(0, n - 1 - j) if j < n else 0
                if ago >= NB:
                    continue
                keys = ["nw_any"]
                if it.get("m", 0) > 0:
                    keys.append("nw_pos")
                if it.get("m", 0) < 0:
                    keys.append("nw_neg")
                if it.get("k") in ("res", "ord", "deal", "corp", "rat", "reg"):
                    keys.append("nw_" + it["k"])
                if it.get("f"):
                    keys.append("nw_fil")
                for k in keys:
                    row[k] = min(row.get(k, 99), ago)
            if row:
                res[tf][t] = row
    return res
