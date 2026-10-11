"""A-plus breakout composite (weekly): a tight base being quietly accumulated, then a breakout on heavy volume.

Weinstein / Minervini / O'Neil / Wyckoff logic with the Choppiness Index regime filter.

Base (the BASE_W weeks before the breakout week):
  * tight: (highest high - lowest low) / lowest low below TIGHT (30%)
  * OBV: on-balance volume above its 10-week average, and that average higher than 4 weeks earlier
  * CMF (21-week Chaikin money flow) above CMF_MIN (0.05) on the breakout week
  * Mansfield RS vs NIFTY (price/NIFTY vs its 52-week average) positive and rising over 4 weeks
  * weekly Choppiness Index (14) at 60+ at some point in the base (it was a real sideways range)
Breakout week:
  * close above the base's highest high
  * Choppiness falling through a threshold (spec 38.2; the page lets you pick 38.2 / 50 / off,
    because on a single breakout week it rarely drops all the way from 60 to 38.2)
  * volume at least 2x its 20-week average (strict: above average + 2 standard deviations)
  * liquidity: 10-week average weekly turnover at least MIN_TURN_CR
Ranking: O'Neil-style RS rank (12 months, latest quarter double), leaders first.
Exit (same as Stage 2 start): first daily close below the 50-day MA, emergency stop 12% below entry.

Every base breakout of the last 2 years is recorded with each condition's result, so the page can
switch conditions on and off and show what each one adds.
"""
import json

import numpy as np
import pandas as pd

from .config import DOCS

BASE_W, TIGHT, CMF_MIN, VOL_X, MIN_TURN_CR, STOP = 15, 0.30, 0.05, 2.0, 5.0, 0.12


def _r(x, n=2):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def build(px, stocks, benchmark, today=None):
    """Writes docs/aplus.json (2-year signal log) and returns the summary for the page."""
    info = {s["sym"]: s for s in stocks}
    cols = [s["sym"] + ".NS" for s in stocks if s.get("liquid") and s["sym"] + ".NS" in px["Close"].columns]
    C, H, L = px["Close"][cols].ffill(limit=3), px["High"][cols], px["Low"][cols]
    O = px["Open"][cols] if "Open" in px else C
    V = px["Volume"][cols].where(lambda x: x > 0) if "Volume" in px else pd.DataFrame(np.nan, index=C.index, columns=cols)
    T = C.index
    # weekly bars (Friday weeks; the week in progress is kept and marked)
    cw, hw, lw, vw = C.resample("W-FRI").last(), H.resample("W-FRI").max(), L.resample("W-FRI").min(), V.resample("W-FRI").sum(min_count=1)
    keep = cw.notna().any(axis=1)
    cw, hw, lw, vw = cw[keep], hw[keep], lw[keep], vw[keep]
    today = pd.Timestamp(today or pd.Timestamp.now(tz="Asia/Kolkata").date())
    forming = bool(len(cw)) and cw.index[-1] > today and T[-1].weekday() < 4
    # indicators
    pc = cw.shift()
    tr = np.maximum(np.maximum(hw - lw, (hw - pc).abs()), (lw - pc).abs())
    chop = 100 * np.log10(tr.rolling(14).sum() / (hw.rolling(14).max() - lw.rolling(14).min()).replace(0, np.nan)) / np.log10(14)
    bhi = hw.shift(1).rolling(BASE_W, min_periods=BASE_W).max()
    blo = lw.shift(1).rolling(BASE_W, min_periods=BASE_W).min()
    tight = (bhi - blo) / blo
    chmax = chop.shift(1).rolling(BASE_W, min_periods=BASE_W - 2).max()
    obv = (np.sign(cw.diff()).fillna(0) * vw.fillna(0)).cumsum()
    obv_ma = obv.rolling(10).mean()
    obv_ok = (obv.shift(1) >= obv_ma.shift(1)) & (obv_ma.shift(1) > obv_ma.shift(5))
    rng = (hw - lw).replace(0, np.nan)
    mfv = ((cw - lw) - (hw - cw)) / rng * vw
    cmf = mfv.rolling(21, min_periods=18).sum() / vw.rolling(21, min_periods=18).sum()
    v20 = vw.shift(1).rolling(20, min_periods=12)
    vx = vw / v20.mean()
    vsd = vw > v20.mean() + 2 * v20.std()
    turn = (cw * vw).rolling(10, min_periods=6).mean() / 1e7
    if benchmark in px["Close"].columns:
        bw = px["Close"][benchmark].resample("W-FRI").last().reindex(cw.index).ffill()
    else:                       # no index: equal-weight market instead
        bw = (1 + C.pct_change(fill_method=None).clip(-.2, .2).mean(axis=1)).cumprod().resample("W-FRI").last().reindex(cw.index)
    rsr = cw.div(bw, axis=0)
    mrs = (rsr / rsr.rolling(52, min_periods=40).mean() - 1) * 100
    mrs_ok = (mrs.shift(1) > 0) & (mrs.shift(1) > mrs.shift(5))
    q = lambda a, b: C.shift(a) / C.shift(b) - 1
    rs = ((0.4 * q(0, 63) + 0.2 * q(63, 126) + 0.2 * q(126, 189) + 0.2 * q(189, 252)).rank(axis=1, pct=True) * 100)
    core = ((cw > bhi) & (tight < TIGHT)).fillna(False)
    # daily data for exits
    Cn, Ln, On = C.to_numpy(float), L.to_numpy(float), O.to_numpy(float)
    S50 = C.rolling(50, min_periods=45).mean().to_numpy(float)
    RS = rs.to_numpy(float)
    day_of = {}                                   # week end -> last daily bar of that week
    wk = T.to_period("W-FRI")
    for k, p in enumerate(wk):
        day_of[p.end_time.normalize()] = k
    since = today - pd.Timedelta(days=730)
    OB, MR, VS = (x.fillna(False).to_numpy(bool) for x in (obv_ok, mrs_ok, vsd))
    CM, CH, CX, VX, TU = (x.to_numpy(float) for x in (cmf, chop, chmax, vx, turn))
    V20 = v20.mean().to_numpy(float)
    log = []
    cmask = core.to_numpy(bool)
    f = lambda x, n=2: round(float(x), n) if np.isfinite(x) else None
    for wi, we in enumerate(cw.index):
        if we < since or we.normalize() not in day_of:
            continue
        i = day_of[we.normalize()]
        live_wk = forming and wi == len(cw.index) - 1
        for j in np.where(cmask[wi])[0]:
            e = Cn[i, j]
            if not np.isfinite(e):
                continue
            xp = why = None
            mx, k_end = e, len(T) - 1
            for k in range(i + 1, len(T)):
                c = Cn[k, j]
                if not np.isfinite(c):
                    continue
                pv = Cn[k - 1, j]
                if np.isfinite(pv) and (c < 0.6 * pv or c > 1.8 * pv):
                    xp = "void"
                    break
                if np.isfinite(Ln[k, j]) and Ln[k, j] <= e * (1 - STOP):
                    o = On[k, j]
                    xp, why, k_end = (min(o, e * (1 - STOP)) if np.isfinite(o) else e * (1 - STOP)), "Emergency stop", k
                    break
                if np.isfinite(S50[k, j]) and c < S50[k, j]:
                    xp, why, k_end = c, "Daily close below 50-day MA", k
                    break
                mx = max(mx, c)
            if xp == "void":
                continue
            last = xp if xp is not None else Cn[-1, j]
            mx = max(mx, last)
            # [sym, entry week, entry, exit date, exit/now, gain, max gain, reason, days,
            #  obv ok, cmf, mansfield ok, chop max in base, chop now, volume x, volume > avg+2sd, turnover cr/week, RS, base tightness %, forming]
            log.append([cols[j][:-3], we.strftime("%Y-%m-%d"), f(e), T[k_end].strftime("%Y-%m-%d") if xp is not None else None, f(last),
                        f((last / e - 1) * 100, 1), f((mx / e - 1) * 100, 1), why, int(k_end - i),
                        bool(OB[wi, j]), f(CM[wi, j], 3), bool(MR[wi, j]),
                        f(CX[wi, j], 0), f(CH[wi, j], 0), f(VX[wi, j], 1), bool(VS[wi, j]) if np.isfinite(VX[wi, j]) else None,
                        f(TU[wi, j], 1), f(RS[i, j], 0), f(tight.iat[wi, j] * 100, 0), bool(live_wk)])
    # watch list: base conditions in place at the last completed week, price near the base high
    wl = []
    wi = len(cw.index) - 1 - (1 if forming else 0)
    if wi > BASE_W + 2:
        nb_hi = hw.iloc[wi - BASE_W + 1:wi + 1].max()
        nb_lo = lw.iloc[wi - BASE_W + 1:wi + 1].min()
        for j, t in enumerate(cols):
            hi_, lo_, c_ = nb_hi[t], nb_lo[t], Cn[-1, j]
            if not (np.isfinite(hi_) and np.isfinite(lo_) and np.isfinite(c_)) or lo_ <= 0:
                continue
            tg = (hi_ - lo_) / lo_
            ob = obv.iat[wi, j] >= obv_ma.iat[wi, j] and obv_ma.iat[wi, j] > obv_ma.iat[wi - 4, j]
            mr = mrs.iat[wi, j] > 0 and mrs.iat[wi, j] > mrs.iat[wi - 4, j]
            cx = chop.iloc[wi - BASE_W + 1:wi + 1, j].max()
            if tg < TIGHT and hi_ * 0.95 <= c_ <= hi_ and np.nan_to_num(TU[wi, j]) >= MIN_TURN_CR:
                wl.append({"sym": t[:-3], "name": info[t[:-3]]["name"], "sector": info[t[:-3]].get("sector"), "price": _r(c_),
                           "trig": _r(hi_), "dist": _r((hi_ / c_ - 1) * 100, 1), "tight": _r(tg * 100, 0), "obv": bool(ob), "mrs": bool(mr),
                           "cmf": _r(cmf.iat[wi, j], 3), "chopmax": _r(cx, 0), "chop": _r(chop.iat[wi, j], 0), "rs": _r(RS[-1, j], 0),
                           "vneed": _r(V20[min(wi + 1, len(V20) - 1), j] * VOL_X / 1e5, 1),
                           "score": int(ob) + int(mr) + int((cmf.iat[wi, j] or 0) > CMF_MIN) + int((cx or 0) >= 60)})
    wl.sort(key=lambda x: (-x["score"], -(x["rs"] or 0)))
    names = {x[0]: info[x[0]]["name"] for x in log}
    names.update({x["sym"]: x["name"] for x in wl})
    out = {"generated": pd.Timestamp.now(tz="Asia/Kolkata").strftime("%d %b %Y, %I:%M %p IST"), "since": since.strftime("%Y-%m-%d"),
           "forming": bool(forming), "params": {"base_w": BASE_W, "tight": TIGHT * 100, "cmf": CMF_MIN, "vol_x": VOL_X, "turn": MIN_TURN_CR, "stop": STOP * 100},
           "names": names, "sectors": {k: info[k].get("sector") for k in names}, "log": log, "watch": wl[:120],
           "has_volume": bool(np.isfinite(VX).any())}
    try:
        DOCS.mkdir(parents=True, exist_ok=True)
        (DOCS / "aplus.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    except Exception as e:
        print(f"  ! aplus.json not written: {str(e)[:80]}")
    return {"n": len(log), "watch": len(wl)}
