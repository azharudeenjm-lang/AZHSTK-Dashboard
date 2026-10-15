"""Weekly SMC: change of character, then a pullback into the order block (weekly bars).

Rules (tested on this dashboard's NSE prices, Oct 2024 - Oct 2026):
  1. Downtrend: the last two confirmed weekly swing highs and swing lows are both falling
     (a swing high/low is the highest/lowest of 2 weeks either side, so it is confirmed 2 weeks later).
  2. Bullish change of character (CHoCH): a weekly close above the last (lower) swing high.
  3. Order block: the last red week (close below open) at or just before the low of the move
     that broke structure. Its low-high range is the buy zone.
  4. Entry: within 8 weeks, the first pullback into the zone while price is in the lower half of the
     move ("discount"). Buy at the top of the zone (or the open if it opens below it).
  5. Stop: 0.5% below the order block's low. Target: 3R (3 x the risk), 2R as an alternative.
  6. Best with RS 80+ (6-month return in the top 20% of liquid stocks at the change of character).
Results in testing: order block + 3R about +2.3% per trade (538 trades, both years positive);
with RS 80+ about +8.8% per trade, but on only 73 trades, so treat that as unproven.
"""
import json

import numpy as np
import pandas as pd

from .config import DOCS

K, MAX_WAIT, STOP_BUF = 2, 8, 0.005


def _r(x, n=2):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def build(px, stocks, today=None):
    info = {s["sym"]: s for s in stocks}
    cols = [s["sym"] + ".NS" for s in stocks if s.get("liquid") and s["sym"] + ".NS" in px["Close"].columns]
    today = pd.Timestamp(today or pd.Timestamp.now(tz="Asia/Kolkata").date())
    Cd, Hd, Ld = px["Close"][cols], px["High"][cols], px["Low"][cols]
    Od = px["Open"][cols] if "Open" in px else Cd
    O, H, L, C = Od.resample("W-FRI").first(), Hd.resample("W-FRI").max(), Ld.resample("W-FRI").min(), Cd.resample("W-FRI").last()
    keep = C.notna().any(axis=1)
    O, H, L, C = O[keep], H[keep], L[keep], C[keep]
    W = C.index
    forming = bool(len(W)) and W[-1] > today
    rs = ((C / C.shift(26) - 1).rank(axis=1, pct=True) * 100).to_numpy(float)
    On, Hn, Ln, Cn = (x.to_numpy(float) for x in (O, H, L, C))
    n = len(W)
    ds = [d.strftime("%Y-%m-%d") for d in W]
    since = (today - pd.Timedelta(days=730)).strftime("%Y-%m-%d")
    logs = {"2": [], "3": []}
    setups, holds = [], []
    for j, t in enumerate(cols):
        o, h, l, c = On[:, j], Hn[:, j], Ln[:, j], Cn[:, j]
        if np.isfinite(c).sum() < 40:
            continue
        sym = t[:-3]
        sh, sl = [], []
        pend = None                      # setup waiting for the pullback
        trades = []                      # entries found (same for 2R and 3R)
        for i in range(2 * K, n):
            if not np.isfinite(c[i]):
                continue
            p = i - K
            if np.isfinite(h[p]) and h[p] >= np.nanmax(h[p - K:p + K + 1]):
                sh.append(p)
            if np.isfinite(l[p]) and l[p] <= np.nanmin(l[p - K:p + K + 1]):
                sl.append(p)
            if pend is not None:
                zl, zh = pend["z"]
                if i - pend["b"] > MAX_WAIT or c[i] < zl:
                    pend = None
                elif l[i] <= zh and l[i] <= pend["eq"]:
                    e = min(o[i], zh) if np.isfinite(o[i]) else zh
                    if e > zl:
                        trades.append({"i": i, "e": e, "sl": zl * (1 - STOP_BUF), "b": pend["b"], "rs": pend["rs"], "z": pend["z"]})
                    pend = None
                continue
            if len(sh) >= 2 and len(sl) >= 2:
                lh = sh[-1]
                if h[sh[-1]] < h[sh[-2]] and l[sl[-1]] < l[sl[-2]] and c[i] > h[lh] and np.isfinite(c[i - 1]) and c[i - 1] <= h[lh]:
                    seg = l[lh:i + 1]
                    li = lh + int(np.nanargmin(seg))
                    lo, hi = l[li], np.nanmax(h[li:i + 1])
                    z = None
                    for q in range(li, max(li - 10, 0), -1):
                        if c[q] < o[q]:
                            z = (l[q], h[q])
                            break
                    if z and z[1] > z[0]:
                        pend = {"b": i, "z": z, "eq": (lo + hi) / 2, "rs": rs[i, j]}
            # exits for open trades are simulated below (they depend on the target)
        # current setup waiting for a pullback (a live opportunity)
        if pend is not None and n - 1 - pend["b"] <= MAX_WAIT:
            zl, zh = pend["z"]
            e = zh
            risk = e - zl * (1 - STOP_BUF)
            last = c[-1] if np.isfinite(c[-1]) else np.nan
            setups.append({"sym": sym, "name": info[sym]["name"], "sector": info[sym].get("sector"), "choch": ds[pend["b"]],
                           "weeks": int(n - 1 - pend["b"]), "zl": _r(zl), "zh": _r(zh), "eq": _r(pend["eq"]), "price": _r(last),
                           "dist": _r((last / zh - 1) * 100, 1) if np.isfinite(last) else None, "stop": _r(zl * (1 - STOP_BUF)),
                           "t2": _r(e + 2 * risk), "t3": _r(e + 3 * risk), "risk": _r(risk / e * 100, 1), "rs": _r(pend["rs"], 0),
                           "in_zone": bool(np.isfinite(last) and last <= zh), "discount": bool(np.isfinite(last) and last <= pend["eq"])})
        # simulate exits for both targets
        for tg in (2, 3):
            for tr in trades:
                i, e, stp = tr["i"], tr["e"], tr["sl"]
                tgt = e + tg * (e - stp)
                xp = why = None
                mx = e
                if l[i] <= stp:                       # stopped in the entry week
                    xp, why, k = stp, "Stop-loss", i
                else:
                    k = i
                    for k in range(i + 1, n):
                        if not np.isfinite(c[k]):
                            continue
                        if l[k] <= stp:
                            xp, why = (min(o[k], stp) if np.isfinite(o[k]) else stp), "Stop-loss"
                            break
                        if h[k] >= tgt:
                            xp, why = (max(o[k], tgt) if np.isfinite(o[k]) else tgt), f"Target {tg}R"
                            break
                        mx = max(mx, h[k])
                if ds[i] < since:
                    continue
                last = xp if xp is not None else c[-1]
                row = [sym, ds[i], _r(e), ds[k] if xp is not None else None, _r(last), _r((last / e - 1) * 100, 1), _r((max(mx, last) / e - 1) * 100, 1),
                       why, int((k if xp is not None else n - 1) - i), _r((e - stp) / e * 100, 1), _r(tr["rs"], 0), _r(stp), _r(tgt), ds[tr["b"]]]
                logs[str(tg)].append(row)
                if xp is None and tg == 3:
                    holds.append(sym)
    setups.sort(key=lambda x: (not x["in_zone"], -(x["rs"] or 0)))
    names = {r[0]: [info[r[0]]["name"], info[r[0]].get("sector")] for L_ in logs.values() for r in L_}
    out = {"generated": pd.Timestamp.now(tz="Asia/Kolkata").strftime("%d %b %Y, %I:%M %p IST"), "since": since, "forming": forming,
           "week": ds[-1] if ds else None, "logs": logs, "setups": setups[:150], "names": names}
    try:
        DOCS.mkdir(parents=True, exist_ok=True)
        (DOCS / "smc.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    except Exception as e:
        print(f"  ! smc.json not written: {str(e)[:80]}")
    return {"n": len(logs["3"]), "setups": len(setups), "open": len(holds)}
