"""Headlines from Google News RSS: one feed per sector, plus top movers."""
import time
from urllib.parse import quote_plus

from .config import NEWS_PER_SECTOR

SECTOR_QUERY = {
    "Fast Moving Consumer Goods": "FMCG",
    "Oil Gas & Consumable Fuels": "oil gas",
    "Media Entertainment & Publication": "media",
    "Automobile and Auto Components": "auto",
    "Information Technology": "IT",
}


def _feed(query, n):
    import feedparser
    url = ("https://news.google.com/rss/search?q=" + quote_plus(query) +
           "+when:7d&hl=en-IN&gl=IN&ceid=IN:en")
    try:
        f = feedparser.parse(url)
    except Exception as e:
        print(f"  ! news {query}: {e}")
        return []
    items = []
    for e in f.entries[:n]:
        src = getattr(e, "source", {}).get("title", "") if hasattr(e, "source") else ""
        title = e.title.rsplit(" - ", 1)[0] if src and e.title.endswith(src) else e.title
        items.append({"t": title, "u": e.link, "s": src,
                      "d": time.strftime("%d %b", e.published_parsed) if getattr(e, "published_parsed", None) else ""})
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
