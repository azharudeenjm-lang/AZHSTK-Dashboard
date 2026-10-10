"""Mark Minervini's Trend Template (Stage 2 filter), on daily prices.

All 8 must pass:
  1. Price above the 150-day and 200-day moving averages
  2. 150-day MA above the 200-day MA
  3. 200-day MA rising for at least 1 month (ideally 4-5 months; shown separately)
  4. 50-day MA above the 150-day and 200-day MAs
  5. Price above the 50-day MA
  6. Price at least 30% above its 52-week low
  7. Price within 25% of its 52-week high
  8. Relative strength rank 70+ (IBD-style: last 12 months, latest quarter weighted double,
     ranked against all liquid stocks; ideally 80-90+)
Exit (dashboard rule, not part of the template): stop-loss 8% below entry,
then a weekly close below the 50-day MA.

Tested on this dashboard's 5 years of weekly prices (weekly stand-ins for the daily averages;
entry when a stock first passes all 8, exit on a weekly close below the 10-week average):
  all new passes          38% won, avg win +30%, avg loss -7%, about +7% per trade, 23% reached +50%
  RS 90+ and within 5% of the 52-week high
                          48% won, avg win +42%, avg loss -10%, about +15% per trade, 29% reached +50%
Results swing by year (2023 very strong, 2025 about flat).
"""
import json
import os

import numpy as np
import pandas as pd

from .config import CACHE, DOCS, SCREENER_EVENT_BARS as NB

HIST = "tt_hist.json"        # results dates and surveillance lists seen so far (history builds up run by run)


def _hist(earn, surv, today):
    """Keeps every results date and the daily surveillance list, so the checks can be measured over time."""
    h = None
    try:
        h = json.loads((CACHE / HIST).read_text(encoding="utf-8"))
    except Exception:
        repo = os.environ.get("GITHUB_REPOSITORY")
        if repo:
            try:
                import requests
                r = requests.get(f"https://raw.githubusercontent.com/{repo}/gh-pages/{HIST}", timeout=20)
                if r.ok and r.text.startswith("{"):
                    h = r.json()
                    print("  trend template: history restored from the published copy")
            except Exception:
                pass
    h = h if isinstance(h, dict) else {}
    res, asm = h.setdefault("res", {}), h.setdefault("asm", {})
    for sym, d in (earn or {}).items():
        if d and d not in res.setdefault(sym, []):
            res[sym] = sorted(res[sym] + [d])[-12:]
    if surv is not None:
        asm[today] = sorted(k for k, v in surv.items() if v)
        for k in sorted(asm)[:-400]:
            del asm[k]
    h.setdefault("since", today)
    txt = json.dumps(h, separators=(",", ":"))
    for path in (CACHE / HIST, DOCS / HIST):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(txt, encoding="utf-8")
        except Exception:
            pass
    return h

META = [
    ("tt_all", "Trend Template: passes all 8 (Stage 2)", "s"),
    ("tt_new", "Trend Template: just started passing all 8", "e"),
    ("tt_7", "Trend Template: 7 of 8 (one check missing)", "s"),
    ("tt_lead", "Trend Template 8/8 with RS 90+ and within 5% of the 52-week high", "s"),
    ("tt_early", "Stage 2 start: 26-week closing-high breakout, RS 80+, above the 50 and 200-day MAs, Choppiness below 38 (early entry)", "e"),
]
STOP = 0.08
STOP_E = 0.12      # Stage 2 start: emergency stop 12% below entry; the main exit is a daily close below the 50-day MA
LABELS = ["Price above the 150 and 200-day MAs", "150-day MA above the 200-day MA", "200-day MA rising for 1 month+",
          "50-day MA above the 150 and 200-day MAs", "Price above the 50-day MA", "At least 30% above the 52-week low",
          "Within 25% of the 52-week high", "RS rank 70+"]


def _r(x, n=2):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def build(px, stocks, earn=None, surv=None, live=False):
    """earn = {sym: next results date}, surv = {sym: "ASM ..." or None}, live = today's bar still trading.
    Returns (page dict, {sym: pop-up record}, {ticker: screener conditions})."""
    info = {s["sym"]: s for s in stocks}
    cols = [s["sym"] + ".NS" for s in stocks if s["sym"] + ".NS" in px["Close"].columns]
    C = px["Close"][cols].ffill(limit=3)
    H, L = px["High"][cols], px["Low"][cols]
    s50, s150, s200 = (C.rolling(n, min_periods=int(n * 0.9)).mean() for n in (50, 150, 200))
    hi52 = H.rolling(250, min_periods=200).max()
    lo52 = L.rolling(250, min_periods=200).min()
    q = lambda a, b: C.shift(a) / C.shift(b) - 1
    raw = 0.4 * q(0, 63) + 0.2 * q(63, 126) + 0.2 * q(126, 189) + 0.2 * q(189, 252)
    liquid = [s["sym"] + ".NS" for s in stocks if s.get("liquid") and s["sym"] + ".NS" in cols]
    rs = raw[liquid].rank(axis=1, pct=True).reindex(columns=cols) * 100
    checks = [(C > s150) & (C > s200), s150 > s200, s200 > s200.shift(21), (s50 > s150) & (s50 > s200), C > s50,
              C >= 1.3 * lo52, C >= 0.75 * hi52, rs >= 70]
    cnt = sum(c.fillna(False).astype(int) for c in checks)
    allp = cnt == 8
    rows, near, recs, sc = [], [], {}, {}
    T = C.index
    for t in liquid:
        k = int(cnt[t].iloc[-1])
        if k < 7:
            continue
        sym = t[:-3]
        p, a50, a150, a200 = C[t].iloc[-1], s50[t].iloc[-1], s150[t].iloc[-1], s200[t].iloc[-1]
        h52, l52, r = hi52[t].iloc[-1], lo52[t].iloc[-1], rs[t].iloc[-1]
        if not all(np.isfinite(x) for x in (p, a50, a150, a200, h52, l52)):
            continue
        # how long has the 200-day MA been rising (days)
        up = (s200[t] > s200[t].shift(21)).to_numpy()
        run = 0
        for v in up[::-1]:
            if not v:
                break
            run += 1
        # days in a row passing all 8
        ap = allp[t].to_numpy()
        days = 0
        for v in ap[::-1]:
            if not v:
                break
            days += 1
        vals = [f"₹{p:,.2f} vs 150-day ₹{a150:,.2f}, 200-day ₹{a200:,.2f}", f"₹{a150:,.2f} vs ₹{a200:,.2f}",
                f"rising {run + 20} days" if run else "not rising", f"₹{a50:,.2f}", f"₹{p:,.2f} vs ₹{a50:,.2f}",
                f"{(p / l52 - 1) * 100:.0f}% above ₹{l52:,.2f}", f"{(p / h52 - 1) * 100:.1f}% from ₹{h52:,.2f}",
                f"RS {r:.0f}" if np.isfinite(r) else "RS –"]
        ok = [bool(c[t].iloc[-1]) if pd.notna(c[t].iloc[-1]) else False for c in checks]
        rec = {"k": k, "checks": [[LABELS[i], ok[i], vals[i]] for i in range(8)], "days": days,
               "ideal": bool(run + 20 >= 80), "rs": _r(r, 0), "hi": _r((p / h52 - 1) * 100, 1), "lo": _r((p / l52 - 1) * 100, 0),
               "exit": _r(a50), "room": _r((p / a50 - 1) * 100, 1)}
        recs[sym] = rec
        row = {"sym": sym, "name": info[sym]["name"], "sector": info[sym].get("sector"), "price": _r(p), **{x: rec[x] for x in ("rs", "hi", "lo", "days", "ideal", "exit", "room")},
               "since": T[-days].strftime("%Y-%m-%d") if days else None,
               "missing": [LABELS[i] for i in range(8) if not ok[i]]}
        if k == 8:
            rows.append(row)
            sc[t] = {"tt_all": 1}
            if days <= NB:
                sc[t]["tt_new"] = max(0, days - 1)
            if (r or 0) >= 90 and (p / h52) >= 0.95:
                sc[t]["tt_lead"] = 1
                row["lead"] = True
        else:
            near.append(row)
            sc[t] = {"tt_7": 1}
    # ---------- Stage 2 start (early): catches the turn before the slow averages line up ----------
    # The 8 checks need the 150 and 200-day MAs stacked and rising, which after a long base takes months,
    # so the template often confirms only after the big move (ASTRAMICRO: base breakout 21 Apr 2026 at 1,110,
    # all 8 only on 26 Jun at 1,719). This rule buys the breakout itself:
    #   close above the highest close of the last 26 weeks, within 10% of the 52-week high,
    #   above the 50 and 200-day MAs, 50-day MA rising, RS 80+, not more than 25% above the 50-day MA,
    #   and only while more than half of all stocks are above their own 50-day MA (market breadth).
    br = (C[liquid] > s50[liquid]).sum(axis=1) / C[liquid].notna().sum(axis=1).replace(0, np.nan)
    hi126 = C.rolling(126, min_periods=100).max().shift(1)
    early = ((C > hi126) & (C >= 0.9 * hi52) & (C > s50) & (C > s200) & (s50 > s50.shift(10)) & (rs >= 80)
             & (C <= 1.25 * s50)).fillna(False)
    early = early & (br > 0.5).to_numpy()[:, None]
    # Choppiness Index (14 days) below 38: the stock is already moving cleanly, not chopping sideways.
    # Tested on real prices (Oct 2025 - Oct 2026): average per closed trade +1.5% -> +3.3%, won 33% -> 37%.
    pc_ = C.shift(1)
    TR = np.maximum(np.maximum(H - L, (H - pc_).abs()), (L - pc_).abs())
    chop = 100 * np.log10(TR.rolling(14).sum() / (H.rolling(14).max() - L.rolling(14).min()).replace(0, np.nan)) / np.log10(14)
    early = early & (chop < 38).fillna(False)
    # volume checks (recorded on every trade; switched on and off on the page)
    if "Volume" in px:
        V = px["Volume"].reindex(index=T, columns=cols).where(lambda x: x > 0)
        v50 = V.rolling(50, min_periods=30).mean().shift(1)
        VR = (V / v50).to_numpy(float)                                   # breakout-day volume vs its 50-day average
        DRY = (V.rolling(10, min_periods=8).mean().shift(1) / v50).to_numpy(float)   # last 10 days before it vs the 50-day average
    else:
        VR = DRY = np.full((len(T), len(cols)), np.nan)
    CH = chop.to_numpy(float)
    today = T[-1].strftime("%Y-%m-%d")
    hist = _hist(earn, surv, today)
    res_h, asm_h = hist.get("res", {}), hist.get("asm", {})
    asm_days = sorted(asm_h)
    h_since = hist.get("since", today)

    def flags(sym, i, j):
        """[volume ratio, dry-up ratio, results within 5 trading days (or None = unknown), under surveillance (None = unknown), chop]"""
        d = T[i]
        ds = d.strftime("%Y-%m-%d")
        rs_ = None
        if ds >= h_since:
            nxt = [x for x in res_h.get(sym, []) if x >= ds]
            rs_ = bool(nxt and (pd.Timestamp(nxt[0]) - d).days <= 7)
        sv = None
        prior = [x for x in asm_days if x <= ds]
        if prior and (pd.Timestamp(ds) - pd.Timestamp(prior[-1])).days <= 7:
            sv = sym in asm_h[prior[-1]]
        f = lambda x, n=2: round(float(x), n) if np.isfinite(x) else None
        return [f(VR[i, j]), f(DRY[i, j]), rs_, sv, f(CH[i, j], 0)]
    # ---------- trades (dashboard rule, not part of the template) ----------
    # entry: close on the day the rule holds (template rules: a fresh pass; after an exit the count must drop first)
    # stop-loss: 8% below entry (Minervini's 7-8% max loss), hit intraday -> exit at the stop (or the open on a gap down)
    # trail: a weekly close (last trading day of the week) below the 50-day MA
    # a one-day move of -40% / +80% is a split or demerger in unadjusted prices: that trade is dropped
    since = T[-1] - pd.Timedelta(days=730)
    sinc = since.strftime("%Y-%m-%d")
    Cn, S50 = C.to_numpy(float), s50.to_numpy(float)
    Ln = L.reindex(columns=cols).to_numpy(float)
    On = px["Open"].reindex(index=T, columns=cols).to_numpy(float) if "Open" in px else np.full_like(Cn, np.nan)
    CNT = cnt.to_numpy(int)
    wk = T.to_period("W-FRI")
    wend = np.r_[wk[1:] != wk[:-1], T[-1].weekday() >= 4]
    col = {t: j for j, t in enumerate(cols)}
    rules = {"8": (CNT >= 8, True), "7": (CNT >= 7, True), "e": (early.to_numpy(bool), False)}
    last_tr = {k: {} for k in rules}
    stats, log = {}, {k: [] for k in rules}
    for rule, (E, fresh) in rules.items():
        done = []
        for t in liquid:
            j = col[t]
            inside, armed = None, not fresh
            for i in range(250, len(T)):
                c_ = Cn[i, j]
                if not np.isfinite(c_):
                    continue
                if inside is None:
                    if not E[i, j]:
                        armed = True
                    elif armed:
                        inside = {"i": i, "e": c_, "sl": c_ * (1 - (STOP_E if rule == "e" else STOP)), "mx": c_}
                        if rule == "e":
                            inside["fl"] = flags(t[:-3], i, j)
                    continue
                pv = Cn[i - 1, j]
                if np.isfinite(pv) and (c_ < 0.6 * pv or c_ > 1.8 * pv):
                    inside, armed = None, not fresh
                    continue
                xp, why = None, None
                inside["mx"] = max(inside["mx"], c_)
                if np.isfinite(Ln[i, j]) and Ln[i, j] <= inside["sl"]:
                    o = On[i, j]
                    xp, why = (min(o, inside["sl"]) if np.isfinite(o) else inside["sl"]), "Stop-loss"
                elif rule == "e" and np.isfinite(S50[i, j]) and c_ < S50[i, j]:
                    xp, why = c_, "Daily close below 50-day MA"
                elif rule != "e" and wend[i] and np.isfinite(S50[i, j]) and c_ < S50[i, j]:
                    xp, why = c_, "Weekly close below 50-day MA"
                if xp is not None:
                    tr = {"ed": T[inside["i"]].strftime("%Y-%m-%d"), "ep": round(float(inside["e"]), 2), "sl": round(float(inside["sl"]), 2),
                          "xd": T[i].strftime("%Y-%m-%d"), "xp": round(float(xp), 2), "g": round(float((xp / inside["e"] - 1) * 100), 1), "why": why,
                          "mx": round(float((inside["mx"] / inside["e"] - 1) * 100), 1)}
                    if rule == "e":
                        tr["fl"] = inside["fl"]
                    last_tr[rule][t[:-3]] = tr
                    if tr["ed"] >= sinc:     # trade log: sym, entry date, entry, exit date, exit, gain, max gain, reason, sessions held
                        done.append((tr["g"], why))
                        log[rule].append([t[:-3], tr["ed"], tr["ep"], tr["xd"], tr["xp"], tr["g"], tr["mx"], why, int(i - inside["i"])]
                                         + (inside["fl"] if rule == "e" else []))
                    inside, armed = None, not fresh
            if inside is not None:
                c_ = Cn[-1, j]
                tr = {"ed": T[inside["i"]].strftime("%Y-%m-%d"), "ep": round(float(inside["e"]), 2), "sl": round(float(inside["sl"]), 2),
                      "xd": None, "xp": None, "g": round(float((c_ / inside["e"] - 1) * 100), 1), "open": True,
                      "mx": round(float((max(inside["mx"], c_) / inside["e"] - 1) * 100), 1)}
                last_tr[rule][t[:-3]] = tr
                if tr["ed"] >= sinc:
                    log[rule].append([t[:-3], tr["ed"], tr["ep"], None, round(float(c_), 2), tr["g"], tr["mx"], None, int(len(T) - 1 - inside["i"])]
                                     + (inside["fl"] if rule == "e" else []))
                if rule == "e":
                    tr["fl"] = inside["fl"]
        g = np.array([x[0] for x in done]) if done else np.array([0.0])
        og = [float(v["g"]) for v in last_tr[rule].values() if v.get("open") and v["ed"] >= sinc]
        n_open = len(og)
        ga = np.array([x[0] for x in done] + og) if done or og else np.array([0.0])
        stats[rule] = {"n": len(done) + n_open, "closed": len(done), "open": n_open,
                       "win": round(float(np.mean(g > 0)) * 100) if done else None,
                       "avg_win": round(float(g[g > 0].mean()), 1) if (g > 0).any() else None,
                       "avg_loss": round(float(g[g <= 0].mean()), 1) if (g <= 0).any() else None,
                       "avg": round(float(g.mean()), 1) if done else None,
                       "sl_hit": round(float(np.mean([x[1] == "Stop-loss" for x in done])) * 100) if done else None,
                       "avg_all": round(float(ga.mean()), 1) if done or og else None,
                       "win_all": round(float(np.mean(ga > 0)) * 100) if done or og else None,
                       "from": sinc}
    for r in rows:
        r["tr"] = last_tr["8"].get(r["sym"])
    for r in near:
        r["tr"] = last_tr["7"].get(r["sym"])
    # Stage 2 start list: every stock whose latest early signal came in the last 3 months (open or exited)
    cut = T[max(0, len(T) - 63)].strftime("%Y-%m-%d")
    erows = []
    for sym, tr in last_tr["e"].items():
        if tr["ed"] < cut:
            continue
        t = sym + ".NS"
        p, a50, h52, r = C[t].iloc[-1], s50[t].iloc[-1], hi52[t].iloc[-1], rs[t].iloc[-1]
        erows.append({"sym": sym, "name": info[sym]["name"], "sector": info[sym].get("sector"), "price": _r(p), "rs": _r(r, 0),
                      "hi": _r((p / h52 - 1) * 100, 1), "exit": _r(a50), "room": _r((p / a50 - 1) * 100, 1), "k": int(cnt[t].iloc[-1]), "tr": tr,
                      "new": bool(tr["ed"] >= T[max(0, len(T) - NB)].strftime("%Y-%m-%d"))})
        if erows[-1]["new"]:
            sc.setdefault(t, {})["tt_early"] = int(len(T) - 1 - T.get_loc(pd.Timestamp(tr["ed"])))
    erows.sort(key=lambda x: x["tr"]["ed"], reverse=True)
    erows.sort(key=lambda x: not x["tr"].get("open"))
    rows.sort(key=lambda x: (not x.get("lead"), -(x["rs"] or 0)))
    near.sort(key=lambda x: -(x["rs"] or 0))
    bnow = br.iloc[-1]
    # the Stage 2 start tab works from its 2-year trade list, so the checks can be switched on the page
    elog = [x for x in log["e"]]
    for r in erows:
        r["chop"] = _r(CH[-1, col[r["sym"] + ".NS"]], 0)
    return {"all": rows, "near": near[:150], "early": erows, "elog": elog, "n_all": len(rows), "stats": stats, "log": log,
            "breadth": _r(bnow * 100, 0) if np.isfinite(bnow) else None, "hist_since": h_since, "live": bool(live),
            "res_soon": {k: v for k, v in (earn or {}).items() if v and (pd.Timestamp(v) - T[-1]).days <= 7 and v >= today}}, recs, sc
