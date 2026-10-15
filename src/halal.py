"""Halal (Shariah) check for every stock, shown in the stock pop-up.

Source of truth: the NIFTY500 Shariah index. NSE Indices has every NIFTY 500 stock screened every
month by its Shariah advisor (TASIS) for business activity and finances:
  * excluded: conventional banks, insurance, finance and investment companies, stockbroking;
    alcohol, pork, tobacco; gambling; vulgar entertainment; hotels/restaurants with non-halal offerings
  * interest-based debt at most 25% of total assets
  * interest income (with interest-bearing investments) at most 3% of total income
  * receivables plus cash and bank balances at most 90% of total assets
So a NIFTY 500 stock is compliant if it is in the NIFTY500 Shariah index, and not if it is left out.

Stocks outside the NIFTY 500 are not screened by NSE. For those this module only applies the
business screen (from the sector and the company name) and, when debt data exists, a rough debt
check. That result is labelled "not verified" and must be confirmed with a Shariah screener.
"""
import csv
import io
import json
import os
import re
from datetime import datetime, timedelta

from .config import CACHE, DOCS

PATH = "halal_lists.json"
REFRESH_DAYS = 7
CSV_URLS = {
    "n500": ["https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"],
    "sh500": ["https://www.niftyindices.com/IndexConstituent/ind_nifty500shariah_list.csv",
              "https://www.niftyindices.com/IndexConstituent/ind_nifty500Shariah_list.csv",
              "https://www.niftyindices.com/IndexConstituent/ind_nifty500_shariah_list.csv"],
    "sh50": ["https://www.niftyindices.com/IndexConstituent/ind_nifty50shariah_list.csv",
             "https://www.niftyindices.com/IndexConstituent/ind_nifty50Shariah_list.csv"],
}
NSE_INDEX = {"n500": "NIFTY 500", "sh500": "NIFTY500 SHARIAH", "sh50": "NIFTY50 SHARIAH", "sh25": "NIFTY SHARIAH 25"}

# business screen (company names); sector "Financial Services" is handled separately
NO_NAME = [(r"\bbank\b|\bbanking\b", "Conventional bank"),
           (r"financ|fincorp|finserv|fintrade|\bcredit\b|leasing|microfin|\bnbfc\b|\bloans?\b", "Conventional finance / lending"),
           (r"insurance|assurance|\blife\b.*\binsur", "Conventional insurance"),
           (r"securities|broking|stock ?brok|\bcapital (ltd|limited)|investments? (ltd|limited)", "Finance / investment company"),
           (r"brewer|distill|spirits|\bwines?\b|liquor|vineyard|\bbeer\b", "Alcohol"),
           (r"tobacco|cigarette|\bbidi\b", "Tobacco"),
           (r"casino|gaming|lottery|betting", "Gambling")]
NO_SYM = {"ITC": "Tobacco (cigarettes)", "GODFRYPHLP": "Tobacco (cigarettes)", "VSTIND": "Tobacco (cigarettes)", "NTCIND": "Tobacco",
          "UNITDSPR": "Alcohol", "UBL": "Alcohol", "RADICO": "Alcohol", "SDBL": "Alcohol", "GLOBUSSPR": "Alcohol", "TI": "Alcohol",
          "ABDL": "Alcohol", "PICCADIL": "Alcohol", "SULA": "Alcohol", "TILAKNAGAR": "Alcohol", "IFBAGRO": "Alcohol",
          "DELTACORP": "Gambling (casinos)", "VENKEYS": "Non-halal meat processing"}
DOUBT_NAME = [(r"hotel|resort|\binns?\b|hospitality", "Hotels may earn from alcohol and non-halal food"),
              (r"pictures|cinema|entertainment|broadcast|\btv\b|media", "Entertainment and media content")]
# finance words in a name only count where the company could be a financier (an IT firm called "... Financial Services Software" is not)
FIN_SECTORS = {"Financial Services", "Unclassified", "Diversified", "Services", ""}
FIN_WHY = {"Conventional bank", "Conventional finance / lending", "Conventional insurance", "Finance / investment company"}
DOUBT_SECTOR = {"Media Entertainment & Publication": "Entertainment and media content"}


def _load():
    try:
        return json.loads((CACHE / PATH).read_text(encoding="utf-8"))
    except Exception:
        pass
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        try:
            import requests
            r = requests.get(f"https://raw.githubusercontent.com/{repo}/gh-pages/{PATH}", timeout=20)
            if r.ok and r.text.startswith("{"):
                return r.json()
        except Exception:
            pass
    return {}


def _save(d):
    txt = json.dumps(d, separators=(",", ":"))
    for p in (CACHE / PATH, DOCS / PATH):
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(txt, encoding="utf-8")
        except Exception:
            pass


def _csv(urls):
    import requests
    for u in urls:
        try:
            r = requests.get(u, timeout=20, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            if r.ok and "Symbol" in r.text[:400]:
                rows = list(csv.DictReader(io.StringIO(r.text)))
                syms = sorted({(x.get("Symbol") or "").strip() for x in rows} - {""})
                if len(syms) >= 20:
                    return syms, u
        except Exception:
            pass
    return None, None


def _nse(api, name):
    if api is None:
        return None
    try:
        from .nse_api import walk
        j = api.get("/api/equity-stockIndices", params={"index": name}, referer="/market-data/live-equity-market")
        syms = sorted({x["symbol"] for x in walk(j) if x.get("symbol") and x.get("symbol") != name})
        return syms if len(syms) >= 20 else None
    except Exception:
        return None


def refresh(demo=False, intraday=False):
    """Index lists (NIFTY 500 and its Shariah versions), refreshed weekly in full runs."""
    d = _load()
    if demo:
        return d
    age_ok = d.get("at") and datetime.fromisoformat(d["at"]) > datetime.now() - timedelta(days=REFRESH_DAYS)
    if intraday or (age_ok and d.get("sh500") and d.get("n500")):
        return d
    api = None
    try:
        from .nse_api import NSE
        api = NSE()
    except Exception:
        pass
    got = {}
    for k in ("n500", "sh500", "sh50", "sh25"):
        syms = _nse(api, NSE_INDEX[k])
        src = f"NSE ({NSE_INDEX[k]})" if syms else None
        if not syms and k in CSV_URLS:
            syms, src = _csv(CSV_URLS[k])
        if syms:
            got[k] = syms
            got[k + "_src"] = src
    if got.get("sh500") and got.get("n500"):
        d.update(got)
        d["at"] = datetime.now().isoformat(timespec="seconds")
        _save(d)
        print(f"  halal: NIFTY500 Shariah {len(got['sh500'])} of {len(got['n500'])} NIFTY 500 stocks ({got.get('sh500_src')})")
    else:
        print("  ! halal: NIFTY500 Shariah list not available this run" + (" (using the saved one)" if d.get("sh500") else ""))
    return d


def classify(stocks, fu, lists):
    sh500, n500 = set(lists.get("sh500") or []), set(lists.get("n500") or [])
    sh50, sh25 = set(lists.get("sh50") or []), set(lists.get("sh25") or [])
    asof = (lists.get("at") or "")[:10]
    out = {}
    for s in stocks:
        sym, name, sec = s["sym"], s.get("name") or "", s.get("sector") or ""
        nm = name.lower()
        biz = NO_SYM.get(sym)
        if not biz and sec == "Financial Services":
            biz = "Conventional financial services (bank, NBFC, insurance or broking)"
        if not biz:
            for rx, why in NO_NAME:
                if why in FIN_WHY and sec not in FIN_SECTORS:
                    continue
                if re.search(rx, nm):
                    biz = why
                    break
        doubt = DOUBT_SECTOR.get(sec)
        if not doubt:
            for rx, why in DOUBT_NAME:
                if re.search(rx, nm):
                    doubt = why
                    break
        de = (fu.get(sym) or {}).get("de")
        debt = None
        if de is not None:
            ratio = de / (1 + de) if de >= 0 else None          # debt / (debt + equity) is at least debt / total assets
            debt = "ok" if ratio is not None and ratio <= 0.25 else "high"
        idx = [n for n, S in (("NIFTY50 Shariah", sh50), ("NIFTY Shariah 25", sh25)) if sym in S]
        if sym in sh500:
            r = {"s": "ok", "t": "Shariah compliant", "r": ["In the NIFTY500 Shariah index (screened monthly by NSE's Shariah advisor, TASIS)"] +
                 ([f"Also in {', '.join(idx)}"] if idx else [])}
        elif sym in n500 and sh500:
            r = {"s": "no", "t": "Not Shariah compliant",
                 "r": [f"In the NIFTY 500 but excluded from the NIFTY500 Shariah index" + (f" ({biz[0].lower() + biz[1:]})" if biz else " (fails the business or financial screen)")]}
        elif biz:
            r = {"s": "no", "t": "Not halal (business activity)", "r": [biz + " is not permitted"]}
        elif doubt:
            r = {"s": "doubt", "t": "Doubtful", "r": [doubt + ": check the company's revenue mix"]}
        else:
            r = {"s": "unk", "t": "Not verified", "r": ["Outside the NIFTY 500, so not screened by NSE's Shariah advisor",
                                                       "Business looks permissible from its sector and name"]}
        if r["s"] in ("unk", "doubt"):
            r["r"].append("Debt looks within limits (estimated from debt/equity)" if debt == "ok" else
                          "Debt may be too high (debt/equity suggests over 25% of assets)" if debt == "high" else
                          "Debt, interest income and cash ratios could not be checked")
        r["asof"] = asof or None
        out[sym] = r
    return out
