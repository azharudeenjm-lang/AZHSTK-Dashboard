"""Per-stock profile data for the search bar and stock pop-up.

Writes, under docs/:
  search.json       list of every stock (for the search box) + bar dates
  p/<letter>.json   full profile for each stock, split by first letter so the
                    phone only downloads a small file when you open a stock
  profile.js        the shared search box + pop-up used on every page
"""
import json
from collections import defaultdict

from .config import DOCS
from .profile_js import PROFILE_JS


def _shard(sym):
    """First two letters/digits, so each file holds only a handful of stocks."""
    k = "".join(ch for ch in sym.upper() if ch.isalnum())[:2]
    return k or "0"


def write(stocks, sectors, zones, hists, lvls, fund, dates, generated, live=None, setups=None, monthly=None):
    """zones/hists/lvls: {"d": {ticker: ...}, "w": {...}}; fund: {sym: {...}}."""
    secq = {s["sector"]: {"d": s.get("q_d"), "w": s.get("q_w")} for s in sectors}
    index, shards = [], defaultdict(dict)
    for s in stocks:
        sym, t = s["sym"], s["sym"] + ".NS"
        zd, zw = zones["d"].get(t), zones["w"].get(t)
        if not zd:
            continue
        index.append([sym, s["name"], s["sector"], zd["zone"], (zw or {}).get("zone"), int(bool(s["liquid"]))])
        prof = {
            "n": s["name"], "sec": s["sector"], "ind": s.get("industry"), "liq": bool(s["liquid"]),
            "px": s.get("price"), "r1d": s.get("r1d"), "r1w": s.get("r1w"), "r1m": s.get("r1m"),
            "r3m": s.get("r3m"), "r1y": s.get("r1y"), "vs50": s.get("vs50"), "vs200": s.get("vs200"),
            "hi": s.get("from_high"), "f": {k: fund.get(sym, {}).get(k) for k in ("pe", "pb", "roe", "de", "mcap_cr")},
            "sq": secq.get(s["sector"], {}), "rq": {"d": s.get("q_d"), "w": s.get("q_w")},
            "z": {}, "lv": {},
        }
        for tf in ("d", "w"):
            z = zones[tf].get(t)
            if z:
                keep = {k: z.get(k) for k in ("zone", "since", "prev", "entry", "move", "days", "capped",
                                              "rsi", "adx", "pdi", "mdi", "chop", "cloud", "macd_x", "stretch")}
                h = hists[tf].get(t) or {}
                keep["segs"], keep["c"] = h.get("segs", []), h.get("c", [])
                prof["z"][tf] = keep
            if lvls[tf].get(t):
                prof["lv"][tf] = lvls[tf][t]
        if setups and t in setups:
            prof["su"] = setups[t]
        if monthly and t in monthly:
            prof["m"] = monthly[t]
        shards[_shard(sym)][sym] = prof

    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "p").mkdir(exist_ok=True)
    dump = lambda o: json.dumps(o, separators=(",", ":"), allow_nan=False)
    (DOCS / "search.json").write_text(dump({"gen": generated, "dates": dates, "s": index, **(live or {})}), encoding="utf-8")
    for k, v in shards.items():
        (DOCS / "p" / f"{k}.json").write_text(dump(v), encoding="utf-8")
    (DOCS / "profile.js").write_text(PROFILE_JS, encoding="utf-8")
