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
Exit guide: a close below the 50-day MA.

Tested on this dashboard's 5 years of weekly prices (weekly stand-ins for the daily averages;
entry when a stock first passes all 8, exit on a weekly close below the 10-week average):
  all new passes          38% won, avg win +30%, avg loss -7%, about +7% per trade, 23% reached +50%
  RS 90+ and within 5% of the 52-week high
                          48% won, avg win +42%, avg loss -10%, about +15% per trade, 29% reached +50%
Results swing by year (2023 very strong, 2025 about flat).
"""
import numpy as np
import pandas as pd

from .config import SCREENER_EVENT_BARS as NB

META = [
    ("tt_all", "Trend Template: passes all 8 (Stage 2)", "s"),
    ("tt_new", "Trend Template: just started passing all 8", "e"),
    ("tt_7", "Trend Template: 7 of 8 (one check missing)", "s"),
    ("tt_lead", "Trend Template 8/8 with RS 90+ and within 5% of the 52-week high", "s"),
]
LABELS = ["Price above the 150 and 200-day MAs", "150-day MA above the 200-day MA", "200-day MA rising for 1 month+",
          "50-day MA above the 150 and 200-day MAs", "Price above the 50-day MA", "At least 30% above the 52-week low",
          "Within 25% of the 52-week high", "RS rank 70+"]


def _r(x, n=2):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def build(px, stocks):
    """Returns (page dict, {sym: pop-up record}, {ticker: screener conditions})."""
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
    rows.sort(key=lambda x: (not x.get("lead"), -(x["rs"] or 0)))
    near.sort(key=lambda x: -(x["rs"] or 0))
    return {"all": rows, "near": near[:150], "n_all": len(rows)}, recs, sc
