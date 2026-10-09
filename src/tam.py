"""TAM screener: the trader's swing and momentum playbook as seven scanners plus a strict filter.

Runs on every update (also the 30-minute market-hours runs) from daily bars; during market
hours the latest bar is the day so far, and its volume is projected to a full day.

Common checks (every listed name):
  * clean structure (higher highs and higher lows over 10 sessions, or a breakout from a tight base)
  * not a circuit lock, new listing (<120 sessions), open-at-high fade, or extended
    (already above the 52-week high and up 8%+ in five sessions)
  * volume confirms (at least 1.5x the 20-day average; scanners ask for more)
  * risk-reward from the safe entry to T1 at least 1:2
Levels:
  R      = highest high of the previous 20 sessions (the resistance / breakout level)
  Safe entry zone = retest of R (R to R+1.5%) when today closed above R, otherwise a dip
                    of 0-2% below the current price; never above the current price
  SL     = just under the lowest low of the last 3 sessions (breakout candle / sweep low),
           but no further than the 20-day base low
  T1     = the next prior high above the entry (52-week high), else the measured move
           (R + base height); T2 = R + 2 x base height
Hourly charts are not available here, so the Elliott check uses the daily count only.
"""
import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from .config import CACHE

IST = timezone(timedelta(hours=5, minutes=30))
HIST = CACHE / "tam_history.json"
MTF_DAY = 0.041          # % interest per day (Groww MTF)
SCAN = {1: "Balanced swing", 2: "Aggressive momentum", 3: "Technical confirmation", 4: "Catalyst",
        5: "Sector volume", 6: "Value + technical", 7: "Explosive single-day"}


def _r(x, n=2):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def _rsi(c, n=14):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _adx(h, l, c, n=14):
    pc = c.shift()
    tr = np.maximum(np.maximum(h - l, (h - pc).abs()), (l - pc).abs())
    atr = tr.ewm(alpha=1 / n, adjust=False).mean()
    upm, dnm = h.diff(), -l.diff()
    pdi = 100 * upm.where((upm > dnm) & (upm > 0), 0.0).ewm(alpha=1 / n, adjust=False).mean() / atr
    mdi = 100 * dnm.where((dnm > upm) & (dnm > 0), 0.0).ewm(alpha=1 / n, adjust=False).mean() / atr
    return (100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)).ewm(alpha=1 / n, adjust=False).mean()


def _ha_last_decisive(o, h, l, c, look=6):
    """Colour of the last decisive Heikin Ashi candle (body at least half its range): 1 green, -1 red, 0 none."""
    o, h, l, c = (np.asarray(x, float)[-60:] for x in (o, h, l, c))
    hc = (o + h + l + c) / 4
    ho = np.empty_like(hc)
    ho[0] = (o[0] + c[0]) / 2
    for i in range(1, len(hc)):
        ho[i] = (ho[i - 1] + hc[i - 1]) / 2
    hh, hl = np.maximum(h, np.maximum(ho, hc)), np.minimum(l, np.minimum(ho, hc))
    for i in range(len(hc) - 1, max(-1, len(hc) - 1 - look), -1):
        rng = hh[i] - hl[i]
        if rng > 0 and abs(hc[i] - ho[i]) >= 0.5 * rng:
            return 1 if hc[i] > ho[i] else -1
    return 0


def _failed_breakout(h, c, look=10):
    """A close above the prior 20-day high in the last `look` sessions that fell back below it within 3 sessions."""
    n = len(c)
    for i in range(max(21, n - 1 - look), n - 1):
        lvl = np.nanmax(h[i - 20:i])
        if c[i] > lvl:
            after = c[i + 1:min(n, i + 4)]
            if len(after) and np.nanmin(after) < lvl:
                return True
    return False


def _load_hist():
    try:
        return json.loads(HIST.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build(px, stocks, sectors, news, fu, benchmark, circuit=None, intraday=False, live=None, demo=False):
    """Returns the page payload."""
    now = datetime.now(IST)
    info = {s["sym"]: s for s in stocks}
    cols = [s["sym"] + ".NS" for s in stocks if s.get("liquid") and s["sym"] + ".NS" in px["Close"].columns]
    O, H, L, C, V = (px[f][cols] for f in ("Open", "High", "Low", "Close", "Volume"))
    last_day = C.index[-1]
    in_session = last_day.date() == now.date() and now.weekday() < 5 and (now.hour * 60 + now.minute) < 15 * 60 + 30
    asof = f"{last_day:%d %b %Y}" + (f", {live}" if live else (f", {now:%I:%M %p} IST (market open, about 15 min delayed)" if in_session else ", close"))
    # volume: projected to a full day while the market is open
    frac = 1.0
    if (intraday or in_session) and last_day.date() == now.date():
        mins = (now.hour * 60 + now.minute) - (9 * 60 + 15)
        frac = float(np.clip(mins / 375, 0.15, 1.0))
    avg20 = V.shift(1).rolling(20, min_periods=15).mean().iloc[-1]
    vr = (V.iloc[-1] / frac) / avg20.replace(0, np.nan)
    c, o, h, l = C.iloc[-1], O.iloc[-1], H.iloc[-1], L.iloc[-1]
    pc, ph = C.iloc[-2], H.iloc[-2]
    chg = (c / pc - 1) * 100
    h52 = H.rolling(250, min_periods=120).max().iloc[-1]
    d52 = (c / h52 - 1) * 100
    r5 = (c / C.iloc[-6] - 1) * 100
    R = H.shift(1).rolling(20, min_periods=15).max().iloc[-1]
    base_lo = L.shift(1).rolling(20, min_periods=15).min().iloc[-1]
    base_rng = (H.shift(1).rolling(15, min_periods=10).max().iloc[-1] / L.shift(1).rolling(15, min_periods=10).min().iloc[-1] - 1) * 100
    hh = H.iloc[-5:].max() > H.iloc[-10:-5].max()
    hl = L.iloc[-5:].min() > L.iloc[-10:-5].min()
    sma20, sma50 = C.rolling(20).mean().iloc[-1], C.rolling(50).mean().iloc[-1]
    rsi = _rsi(C).iloc[-1]
    macd = C.ewm(span=12, adjust=False).mean() - C.ewm(span=26, adjust=False).mean()
    sig = macd.ewm(span=9, adjust=False).mean()
    hist_ = macd - sig
    rolling_over = (macd.iloc[-1] < macd.iloc[-2]) & (hist_.iloc[-1] < hist_.iloc[-2]) & (hist_.iloc[-2] < hist_.iloc[-3])
    adx = _adx(H, L, C).iloc[-1]
    nhist = C.notna().sum()
    sw_lo = L.iloc[-3:].min()

    # ---------- index line ----------
    idx = {}
    if benchmark in px["Close"].columns:
        bc, bh, bl = px["Close"][benchmark].dropna(), px["High"][benchmark].dropna(), px["Low"][benchmark].dropna()
        b20, b50 = bc.rolling(20).mean().iloc[-1], bc.rolling(50).mean().iloc[-1]
        lo5 = bl.iloc[-6:-1].min()
        cancel = max([x for x in (lo5, b20) if x < bc.iloc[-1]] or [lo5])
        drop = (bc.iloc[-1] / bc.iloc[-20:].max() - 1) * 100
        cash, why = False, ""
        if bc.iloc[-1] < b20 and bc.iloc[-1] < b50:
            cash, why = True, "NIFTY is below its 20 and 50 DMA: default to cash"
        elif drop <= -6 and bc.iloc[-1] > bc.iloc[-2]:
            cash, why = True, f"NIFTY is only bouncing off a crash low ({drop:.1f}% from its 20-day high): default to cash"
        idx = {"last": _r(bc.iloc[-1]), "chg": _r((bc.iloc[-1] / bc.iloc[-2] - 1) * 100), "lo": _r(bl.iloc[-1]), "hi": _r(bh.iloc[-1]),
               "cancel": _r(cancel), "dma20": _r(b20), "dma50": _r(b50), "cash": cash, "why": why}

    # ---------- sectors: leaders and the weakest of the day ----------
    sec_day = {}
    for s in stocks:
        if s.get("liquid") and s.get("r1d") is not None:
            sec_day.setdefault(s["sector"], []).append(s["r1d"])
    sec_rank = sorted(((np.mean(v), k) for k, v in sec_day.items() if len(v) >= 3), reverse=True)
    lead = {k for _, k in sec_rank[:max(3, len(sec_rank) // 5)]}
    quad = {x["sector"]: (x.get("q_d"), x.get("q_w")) for x in (sectors or [])}
    lead |= {k for k, (qd, qw) in quad.items() if qw == "Leading" and qd in ("Leading", "Improving")}
    weakest = sec_rank[-1][1] if sec_rank else None
    # sector P/E medians for the value scanner
    pes = {}
    for s in stocks:
        pe = (fu.get(s["sym"]) or {}).get("pe")
        if pe and 0 < pe < 500:
            pes.setdefault(s["sector"], []).append(pe)
    sec_pe = {k: float(np.median(v)) for k, v in pes.items() if len(v) >= 5}

    hist = {} if demo else _load_hist()
    today = now.strftime("%Y-%m-%d")
    recent = {}                       # names shown in the previous 3 sessions
    for d in sorted(hist)[-4:]:
        if d != today:
            for s in hist[d]:
                recent.setdefault(s, d)

    rows, leave = [], []
    for t in cols:
        sym = t[:-3]
        cc, vv = c[t], vr[t]
        if not np.isfinite(cc) or not np.isfinite(vv) or not np.isfinite(h52[t]):
            continue
        # only names that could matter: near highs or moving on volume
        if d52[t] < -7 and not (chg[t] >= 5 and vv > 3):
            continue
        reasons_leave = []
        band = (circuit or {}).get(sym)
        is_circ = cc >= h[t] * 0.999 and chg[t] > 0 and (band and chg[t] >= band - 0.15 or (not band and min(abs(chg[t] - b) for b in (5, 10, 20)) < 0.15))
        if is_circ:
            reasons_leave.append("Upper circuit / locked at the high")
        if nhist[t] < 120:
            reasons_leave.append("New listing (under 120 sessions)")
        if o[t] >= h[t] * 0.997 and cc < o[t] * 0.99:
            reasons_leave.append("Opened at the high and faded")
        if d52[t] >= 0 and r5[t] >= 8:
            reasons_leave.append(f"Extended: through the 52-week high and up {r5[t]:.1f}% in 5 sessions")
        # levels
        brk = cc > R[t]
        zone_lo, zone_hi = (R[t], min(R[t] * 1.015, cc)) if brk else (cc * 0.98, cc)
        entry = (zone_lo + zone_hi) / 2
        # SL: the highest structural low that sits clearly under the entry zone
        lows = [l[t], L[t].iloc[-2], sw_lo[t], L[t].iloc[-10:].min(), base_lo[t]]   # breakout candle, prior day, swing lows
        cap_ = min(zone_lo * 0.99, l[t] * 0.995)        # below the zone and below today's low (already printed)
        sls = [x * 0.995 for x in lows if np.isfinite(x) and x * 0.995 <= cap_ + 1e-9]
        sl = max(sls) if sls else np.nan
        height = R[t] - base_lo[t]
        cands = [x for x in (R[t], h52[t], R[t] + height) if np.isfinite(x) and x > entry * 1.01]
        t1 = min(cands) if cands else np.nan
        t2 = R[t] + 2 * height
        if np.isfinite(t1) and np.isfinite(t2) and t2 <= t1:
            t2 = t1 + height
        risk = entry - sl
        rr = (t1 - entry) / risk if np.isfinite(sl) and risk > 0 and np.isfinite(t1) else np.nan
        dead = np.isfinite(sl) and l[t] < sl                       # traded through the planned SL today
        structure = bool(hh[t] and hl[t]) or (np.isfinite(base_rng[t]) and base_rng[t] <= 12 and cc >= R[t] * 0.97)
        tight_base = np.isfinite(base_rng[t]) and base_rng[t] <= 12 and R[t] * 0.97 <= cc
        above = cc > sma20[t] and cc > sma50[t]
        why = []
        scans = []
        # Scanner 1
        if d52[t] >= -7 and vv >= 2 and (brk or tight_base) and r5[t] <= 8:
            scans.append(1)
        # Scanner 2
        faded = h[t] > cc * 1.02 and o[t] >= h[t] * 0.995
        if vv >= 2.5 and brk and not faded and chg[t] > 0:
            scans.append(2)
        # Scanner 3
        tech = {}
        failed = _failed_breakout(H[t].to_numpy(float), C[t].to_numpy(float))
        tech["structure"] = bool(hh[t] and hl[t]) and not failed
        tech["above"] = bool(above)
        tech["rsi"] = bool(np.isfinite(rsi[t]) and rsi[t] <= 75)
        tech["macd"] = not bool(rolling_over[t])
        tech["adx"] = bool(np.isfinite(adx[t]) and adx[t] >= 20)
        ha = _ha_last_decisive(O[t].to_numpy(float), H[t].to_numpy(float), L[t].to_numpy(float), C[t].to_numpy(float))
        tech["ha"] = ha == 1
        ew_txt, ew_ok = "no clear count", True
        try:
            from .elliott import analyse
            k = min(len(C), 200)
            _, _, g = analyse(H[t].to_numpy(float)[-k:], L[t].to_numpy(float)[-k:], C[t].to_numpy(float)[-k:], "d")
            if g:
                lab = g["pts"][-1][2]
                ew_txt = f"daily {g['d']} count, wave {lab}" + (f", invalid {g.get('ivs', 'below')} ₹{g['iv']:,.2f}" if g.get("iv") else "")
                ew_ok = not (g["d"] == "up" and lab == "5")
        except Exception:
            pass
        tech["elliott"] = ew_ok
        tscore = sum(tech.values())
        if all(tech.values()):
            scans.append(3)
        # Scanner 4: catalyst confirmed by price
        cat = None
        for it in (news.get(sym) or []):
            age = (now.date() - datetime.strptime(it["d"], "%Y-%m-%d").date()).days
            txt = it.get("t", "")
            if age <= 3 and it.get("k") in ("res", "ord", "deal") and it.get("m", 0) >= 0 and \
                    "qip" not in txt.lower() and "rumour" not in txt.lower():
                cat = {"t": txt[:140], "d": it["d"], "k": it.get("k"), "src": it.get("s"),
                       "priced": bool(r5[t] >= 10)}
                break
        if cat and cc > o[t] and chg[t] > 0:
            scans.append(4)
        # Scanner 5
        sec = info[sym].get("sector")
        if sec in lead and sec != weakest and vv >= 1.5 and d52[t] >= -7 and structure:
            scans.append(5)
        # Scanner 6
        f = fu.get(sym) or {}
        val_note = None
        if f.get("pe") and sec in sec_pe:
            if f["pe"] <= 1.3 * sec_pe[sec] and ((f.get("sg") or 0) > 0 or (f.get("pg") or 0) > 0) and (brk or d52[t] >= -7):
                scans.append(6)
            val_note = f"P/E {f['pe']:.1f} vs sector median {sec_pe[sec]:.1f}"
        # Scanner 7
        exp_match = chg[t] >= 5 and vv > 3 and cc > ph[t] and d52[t] >= -5
        if exp_match:
            if chg[t] >= 10:
                reasons_leave.append(f"Explosive match but already up {chg[t]:.1f}% today: matched, not tradeable")
            else:
                scans.append(7)
        if not scans:
            if reasons_leave and (d52[t] >= -7):
                leave.append({"sym": sym, "name": info[sym]["name"], "sector": sec, "cmp": _r(cc), "chg": _r(chg[t], 1), "why": reasons_leave})
            continue
        # common gates
        if vv < 1.5:
            reasons_leave.append(f"Volume only {vv:.1f}x the 20-day average")
        if not structure:
            reasons_leave.append("No clean structure (no higher highs/lows or tight base)")
        if dead:
            reasons_leave.append("Already traded through the planned SL today: setup dead for this session")
        if not np.isfinite(rr) or rr < 2:
            reasons_leave.append(f"Risk-reward to T1 below 1:2 ({rr:.1f})" if np.isfinite(rr) else "No clear T1 above the entry")
        if sym in recent:
            exceptional = vv >= 3 and tscore >= 6
            if not exceptional:
                reasons_leave.append(f"Repeated: already listed on {recent[sym]}")
            else:
                why.append(f"Back again (listed {recent[sym]}): volume {vv:.1f}x and {tscore}/7 technical checks")
        row = {"sym": sym, "name": info[sym]["name"], "sector": sec, "cmp": _r(cc), "chg": _r(chg[t], 1),
               "scans": scans, "vr": _r(vv, 1), "d52": _r(d52[t], 1), "r5": _r(r5[t], 1), "rsi": _r(rsi[t], 0), "adx": _r(adx[t], 0),
               "zone": [_r(zone_lo), _r(zone_hi)], "entry": _r(entry), "sl": _r(sl), "t1": _r(t1), "t2": _r(t2), "rr": _r(rr, 1),
               "tech": tech, "tscore": tscore, "ew": ew_txt, "cat": cat, "val": val_note,
               "above": bool(above), "fresh": sym not in recent, "u1000": bool(cc < 1000)}
        why += [f"{vv:.1f}x volume{' (projected)' if frac < 1 else ''}",
                f"{abs(d52[t]):.1f}% {'below' if d52[t] < 0 else 'above'} the 52-week high",
                "closed above the 20-day high ₹%s" % f"{R[t]:,.2f}" if brk else "tight base just under ₹%s" % f"{R[t]:,.2f}",
                f"up {r5[t]:.1f}% in 5 sessions", f"RSI {rsi[t]:.0f}, ADX {adx[t]:.0f}", ew_txt]
        if cat:
            why.append(f"catalyst: {cat['t'][:80]} ({cat['d']}){' - likely already in the price' if cat['priced'] else ''}")
        if val_note:
            why.append(val_note)
        if 2 in scans:
            why.append("aggressive momentum: higher risk")
        row["why"] = why
        row["cancel"] = (f"A close below ₹{sl:,.2f}" if np.isfinite(sl) else "No structural stop") + (f", or NIFTY below {idx['cancel']:,.0f}" if idx.get("cancel") else "")
        if reasons_leave:
            leave.append({"sym": sym, "name": info[sym]["name"], "sector": sec, "cmp": _r(cc), "chg": _r(chg[t], 1),
                          "why": reasons_leave, "scans": scans, "zone": [_r(zone_lo), _r(zone_hi)], "sl": _r(sl), "t1": _r(t1), "rr": _r(rr, 1)})
            continue
        row["strict"] = bool(r5[t] <= 8 and d52[t] >= -5 and vv >= 2.5 and above and rr >= 2 and zone_hi <= cc)
        rows.append(row)

    # ranking: technical strength, volume, freshness, risk-reward, catalyst; prefer under ₹1,000 on ties
    rows.sort(key=lambda r: (-r["tscore"], -(r["vr"] or 0), not r["fresh"], -(r["rr"] or 0), r["cat"] is None, not r["u1000"]))
    # scanner 5: one name per sector
    seen = set()
    for r in rows:
        if 5 in r["scans"]:
            if r["sector"] in seen:
                r["scans"] = [s for s in r["scans"] if s != 5]
            else:
                seen.add(r["sector"])
    rows = [r for r in rows if r["scans"]]
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    strict = [r for r in rows if r["strict"]]
    action = None
    if strict and not idx.get("cash"):
        a = strict[0]
        action = {"sym": a["sym"], "zone": a["zone"], "sl": a["sl"], "t1": a["t1"], "t2": a["t2"], "rr": a["rr"],
                  "nifty": idx.get("cancel"), "event": bool(a["cat"] and a["cat"]["d"] == today)}
    # remember today's names for the freshness rule
    if not demo:
        hist[today] = sorted({r["sym"] for r in rows})
        hist = {k: hist[k] for k in sorted(hist)[-10:]}
        try:
            HIST.parent.mkdir(parents=True, exist_ok=True)
            HIST.write_text(json.dumps(hist), encoding="utf-8")
        except Exception:
            pass
    stale = not intraday and now.weekday() < 5 and (now.hour * 60 + now.minute) > 9 * 60 + 45 and \
        (now.hour * 60 + now.minute) < 15 * 60 + 30 and last_day.date() < now.date()
    return {"generated": now.strftime("%d %b %Y, %I:%M %p IST"), "gen_iso": now.isoformat(), "asof": asof, "intraday": bool(intraday), "frac": round(frac, 2),
            "stale": bool(stale), "index": idx, "rows": rows, "strict": [r["sym"] for r in strict],
            "leave": sorted(leave, key=lambda x: -(x.get("chg") or 0))[:80], "action": action,
            "lead": sorted(lead), "weakest": weakest, "scan_names": SCAN, "mtf": MTF_DAY}


# ---------------------------------------------------------------- trade tracking
PLANS = CACHE / "tam_plans.json"
WAIT_DAYS, MAX_HOLD = 5, 15        # sessions to wait for the entry zone; maximum holding period


def _load_plans():
    try:
        return json.loads(PLANS.read_text(encoding="utf-8"))
    except Exception:
        pass
    import os
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        try:
            import requests
            r = requests.get(f"https://raw.githubusercontent.com/{repo}/gh-pages/tam_plans.json", timeout=20)
            if r.ok and r.text.startswith("["):
                return r.json()
        except Exception:
            pass
    return []


def _replay(p, O, H, L, C, bench):
    """Follow one plan through the daily bars after its signal day. Returns the plan with status fields."""
    t = p["sym"] + ".NS"
    out = {**p, "status": "waiting", "entry": None, "ed": None, "exit": None, "xd": None, "why": None, "t1_hit": None,
           "pct": None, "last": None}
    if t not in C.columns:
        out["status"] = "no data"
        return out
    d0 = pd.Timestamp(p["sd"][:10])
    idx = [d for d in C.index if d > d0]
    zlo, zhi, sl, t1, t2 = p["zone"][0], p["zone"][1], p["sl"], p["t1"], p["t2"]
    stop, half, waited, held = sl, False, 0, 0
    last = C[t].dropna()
    out["last"] = _r(last.iloc[-1]) if len(last) else None
    for d in idx:
        o, h, l, c = O.at[d, t], H.at[d, t], L.at[d, t], C.at[d, t]
        if not np.isfinite(c):
            continue
        nb = bench.get(d) if bench is not None else None
        if out["status"] == "waiting":
            waited += 1
            if l < sl:                                    # traded through the planned SL before any fill
                out.update(status="cancelled", why="Price went below the SL before the entry zone was reached", xd=d.strftime("%Y-%m-%d"))
                break
            if p.get("nifty") and nb is not None and nb < p["nifty"]:
                out.update(status="cancelled", why=f"NIFTY closed below {p['nifty']:,.0f}", xd=d.strftime("%Y-%m-%d"))
                break
            if l <= zhi:                                  # limit order inside the zone gets filled
                fill = min(zhi, o) if np.isfinite(o) else zhi
                fill = max(fill, zlo) if l <= zlo else fill
                out.update(status="open", entry=_r(fill), ed=d.strftime("%Y-%m-%d"))
            elif waited >= WAIT_DAYS:
                out.update(status="expired", why=f"Entry zone not reached in {WAIT_DAYS} sessions", xd=d.strftime("%Y-%m-%d"))
                break
            else:
                continue
        # open position (a fill on this bar is checked against this bar's close too)
        held += 1
        e = out["entry"]
        if not half and h >= t1:                          # book 50% at T1, stop to breakeven on the rest
            half = True
            out["t1_hit"] = d.strftime("%Y-%m-%d")
            stop = max(stop, e)
        if half and h >= t2:
            out.update(status="closed", exit=_r(t2), xd=d.strftime("%Y-%m-%d"), why="T2 reached (rest booked)")
            break
        if c < stop:
            out.update(status="closed", exit=_r(c), xd=d.strftime("%Y-%m-%d"),
                       why="Breakeven stop after T1" if half else "Closed below the SL")
            break
        if p.get("nifty") and nb is not None and nb < p["nifty"]:
            out.update(status="closed", exit=_r(c), xd=d.strftime("%Y-%m-%d"), why=f"NIFTY closed below {p['nifty']:,.0f}")
            break
        if held >= MAX_HOLD:
            out.update(status="closed", exit=_r(c), xd=d.strftime("%Y-%m-%d"), why=f"Time exit after {MAX_HOLD} sessions")
            break
    e = out["entry"]
    if e:
        px_ = out["exit"] if out["status"] == "closed" else out["last"]
        if px_:
            # blended result: half at T1 when it was reached
            r = (0.5 * (t1 / e - 1) + 0.5 * (px_ / e - 1)) if out["t1_hit"] else (px_ / e - 1)
            out["pct"] = _r(r * 100, 1)
        if out["status"] == "open" and out["t1_hit"]:
            out["status"] = "t1"
        out["stop_now"] = _r(stop)
    return out


def track(page, px, benchmark, demo=False, plans_in=None):
    """Adds Signals and open trades / Watch list / Recent exits to the TAM payload."""
    plans = plans_in if plans_in is not None else ([] if demo else _load_plans())
    today = px["Close"].index[-1].strftime("%Y-%m-%d")          # the signal belongs to the latest bar
    have = {(p["sym"], p["sd"][:10]) for p in plans}
    active = {p["sym"] for p in plans if p.get("_open")}
    for r in page["rows"]:
        if (r["sym"], today) in have or r["sym"] in active or not r.get("sl") or not r.get("t1"):
            continue
        plans.append({"sym": r["sym"], "name": r["name"], "sector": r["sector"], "sd": today, "scans": r["scans"],
                      "strict": r.get("strict", False), "zone": r["zone"], "sl": r["sl"], "t1": r["t1"], "t2": r["t2"],
                      "rr": r["rr"], "cmp": r["cmp"], "nifty": (page.get("index") or {}).get("cancel")})
    O, H, L, C = (px[f] for f in ("Open", "High", "Low", "Close"))
    bench = px["Close"][benchmark] if benchmark in px["Close"].columns else None
    res = [_replay(p, O, H, L, C, bench) for p in plans]
    for p, r in zip(plans, res):
        p["_open"] = r["status"] in ("waiting", "open", "t1")
    # keep 60 days of plans
    cut = (datetime.now(IST) - timedelta(days=60)).strftime("%Y-%m-%d")
    keep = [(p, r) for p, r in zip(plans, res) if p["sd"] >= cut or p["_open"]]
    plans, res = [k[0] for k in keep], [k[1] for k in keep]
    if not demo:
        try:
            PLANS.parent.mkdir(parents=True, exist_ok=True)
            PLANS.write_text(json.dumps(plans), encoding="utf-8")
            from .config import DOCS
            (DOCS / "tam_plans.json").write_text(json.dumps(plans), encoding="utf-8")
        except Exception:
            pass
    live = sorted([r for r in res if r["status"] in ("waiting", "open", "t1")], key=lambda x: x["sd"], reverse=True)
    exits = sorted([r for r in res if r["status"] in ("closed", "cancelled", "expired")], key=lambda x: x["xd"] or "", reverse=True)
    closed = [r for r in exits if r["status"] == "closed" and r["pct"] is not None]
    stats = {"n": len(closed), "win": _r(np.mean([r["pct"] > 0 for r in closed]) * 100, 0) if closed else None,
             "avg": _r(np.mean([r["pct"] for r in closed]), 1) if closed else None,
             "t1": sum(1 for r in closed if r["t1_hit"]), "cancelled": sum(1 for r in exits if r["status"] != "closed")}
    # watch list: matched a scanner but missed only on risk-reward, volume or freshness
    soft = ("Risk-reward", "Volume only", "Repeated", "No clear T1")
    watch = [x for x in page["leave"] if x.get("scans") and all(w.startswith(soft) for w in x["why"])]
    page["_plans"] = plans
    page["trk"] = {"live": live, "exits": exits[:60], "stats": stats, "watch": watch[:40]}
    return page
