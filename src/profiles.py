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


def write(stocks, sectors, zones, hists, lvls, fund, dates, generated, live=None, setups=None, monthly=None, extra=None):
    extra = extra or {}
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
                                              "rsi", "adx", "pdi", "mdi", "chop", "cloud", "macd_x", "stretch", "div")}
                h = hists[tf].get(t) or {}
                keep["segs"], keep["c"] = h.get("segs", []), h.get("c", [])
                for k in ("o", "h", "l"):
                    if k in h:
                        keep[k] = h[k]
                prof["z"][tf] = keep
            if lvls[tf].get(t):
                prof["lv"][tf] = lvls[tf][t]
        prof["rs"] = (extra.get("rs") or {}).get(t)
        prof["earn"] = (extra.get("earn") or {}).get(sym)
        fb = extra.get("fib") or {}
        prof["fib"] = {tf: fb[tf][t] for tf in ("d", "w") if tf in fb and t in fb[tf]}
        sgx = extra.get("sg") or {}
        prof["sg"] = {tf: sgx[tf].get(t, {}) for tf in ("d", "w") if tf in sgx}
        gx = extra.get("geo") or {}
        prof["pat"] = {tf: gx[tf][t] for tf in ("d", "w") if tf in gx and t in gx[tf]}
        ex = extra.get("ew") or {}
        prof["ew"] = {tf: ex[tf][t] for tf in ("d", "w") if tf in ex and t in ex[tf]}
        sym_ = t[:-3] if t.endswith(".NS") else t
        if (extra.get("fu") or {}).get(sym_):
            prof["fu"] = extra["fu"][sym_]
        if (extra.get("al") or {}).get(sym_):
            prof["al"] = [{k: v for k, v in x.items() if k != "e"} for x in extra["al"][sym_]]
        nw = (extra.get("nw") or {}).get(t[:-3] if t.endswith(".NS") else t)
        if nw:
            prof["nw"] = nw[:12]
        sx = extra.get("ser") or {}
        prof["ser"] = {tf: sx[tf].get(t) for tf in ("d", "w") if tf in sx and sx[tf].get(t)}
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
