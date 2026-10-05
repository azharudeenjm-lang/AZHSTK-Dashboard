"""Multi-timeframe trade setups: monthly = tide, weekly = wave, daily = ripple.

For every stock it answers six questions and sorts the stock into a bucket:

  1. Monthly trend   price above the 10-month average, monthly RSI >= 50,
                     monthly MACD above its signal (or histogram rising)
  2. Weekly setup    fresh trend (Accumulation -> Bullish recently), pullback
                     inside a Bullish trend (retest / support / trendline),
                     or a weekly breakout
  3. Daily timing    no daily divergence and not extended today (those mean
                     wait), ideally at support, on a breakout or turning up
  4. Sector          sector Leading or Improving on the weekly RRG
  5. Room            reward to the next weekly resistance at least 2x the risk
  6. Stop            a sensible stop exists within 1.5%-15% below the price

  Ready        monthly OK, weekly setup, daily timing good, sector not Lagging
  Setting up   weekly setup with monthly OK or mixed, but daily says wait
               (or the sector is lagging, or the monthly is only mixed)
  Watchlist    monthly OK and a weekly base (Accumulation) is forming
  Avoid        weekly Divergence zone / Bearish / Oversold, or a weekly setup
               fighting a weak monthly trend
"""
import numpy as np
import pandas as pd

from datetime import date

from .config import EARNINGS_WARN_DAYS, SETUP, WEEKLY_LIVE
from .zones import weekly_bars

PULLBACK = {"Retest", "At trendline support", "Near support"}
BREAKOUT = {"Breakout", "Trendline breakout"}


def _rsi(df, n=14):
    d = df.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def monthly(close):
    """Monthly bars from daily closes (current month included while live)."""
    m = close.resample("ME").last()
    if not WEEKLY_LIVE:
        today = pd.Timestamp.now(tz="Asia/Kolkata").normalize().tz_localize(None)
        m = m[m.index <= today]
    m = m.dropna(how="all")
    sma = m.rolling(SETUP["monthly_ma"], min_periods=SETUP["monthly_ma"]).mean()
    rsi = _rsi(m)
    macd = m.ewm(span=12, adjust=False).mean() - m.ewm(span=26, adjust=False).mean()
    sig = macd.ewm(span=9, adjust=False).mean()
    hist = macd - sig
    return m, sma, rsi, macd, sig, hist


def _last_pivot_low(low, k=3, look=30):
    """Most recent confirmed swing low in the last `look` bars."""
    a = low[-look:]
    for i in range(len(a) - 1 - k, k - 1, -1):
        w = a[i - k:i + k + 1]
        if not np.isnan(a[i]) and a[i] <= np.nanmin(w):
            return float(a[i])
    return None


def build(px, universe, zd, zw, ld, lw, sectors, rs=None, regime=None, earn=None, fibs=None):
    rs, earn, fibs = rs or {}, earn or {}, fibs or {"d": {}, "w": {}}
    risk_off = (regime or {}).get("state") == "Risk-off"
    today = date.today()
    close, high, low = px["Close"], px["High"], px["Low"]
    tick = [t for t in universe["ticker"] if t in close.columns]
    secq = {s["sector"]: s.get("q_w") for s in sectors}
    sec_of = dict(zip(universe["ticker"], universe["sector"]))

    m, sma, rsi_m, macd_m, sig_m, hist_m = monthly(close[tick])
    wc, wh, wl = weekly_bars(close[tick], high[tick], low[tick])
    kijun = (wh.rolling(26).max() + wl.rolling(26).min()) / 2
    prev_wk_high = wh.iloc[-2] if len(wh) > 1 else wh.iloc[-1]
    rsi_d = _rsi(close[tick]).iloc[-1]

    out, mdata = {}, {}
    for t in tick:
        c = close[t].dropna()
        if len(c) < 60 or t not in zd or t not in zw:
            continue
        price = float(c.iloc[-1])
        Zd, Zw = zd[t], zw[t]
        Ld, Lw = ld.get(t) or {}, lw.get(t) or {}
        sig_d, sig_w = set(Ld.get("sig", [])), set(Lw.get("sig", []))

        # ---- 1. monthly tide ----
        mc, ms, mr = m[t].iloc[-1], sma[t].iloc[-1], rsi_m[t].iloc[-1]
        mh, mh1 = hist_m[t].iloc[-1], hist_m[t].iloc[-2] if len(hist_m) > 1 else np.nan
        checks = {
            "ma": bool(pd.notna(ms) and mc > ms),
            "rsi": bool(pd.notna(mr) and mr >= SETUP["monthly_rsi"]),
            "macd": bool(pd.notna(mh) and (mh > 0 or (pd.notna(mh1) and mh > mh1))),
        }
        enough = pd.notna(ms) and pd.notna(mr)
        npass = sum(checks.values())
        mon = "No data" if not enough else "OK" if npass == 3 else "Mixed" if npass == 2 else "Weak"
        mon_txt = (f"{'above' if checks['ma'] else 'below'} 10-month avg, RSI {mr:.0f}, "
                   f"MACD {'rising' if checks['macd'] else 'falling'}") if enough else "not enough monthly history"

        # ---- 2. weekly wave ----
        wz, wprev, wdays = Zw.get("zone"), Zw.get("prev"), Zw.get("days") or 99
        setup, wk_txt = None, ""
        if wz == "Bullish" and wprev == "Accumulation" and not Zw.get("capped") and wdays <= SETUP["fresh_weeks"]:
            setup, wk_txt = "Fresh trend", f"Accumulation → Bullish {wdays} {'week' if wdays == 1 else 'weeks'} ago"
        elif sig_w & BREAKOUT and wz in ("Bullish", "Accumulation", "Strong momentum", "Neutral"):
            b = sorted(sig_w & BREAKOUT)[0]
            vx = (Lw.get("brk") or {}).get("vx") or (Lw.get("tlr") or {}).get("vx")
            setup, wk_txt = "Breakout", f"weekly {b.lower()}" + (f", {vx:.1f}× volume" if vx else "")
        elif wz == "Bullish" and (sig_w & PULLBACK or (fibs["w"].get(t) or {}).get("status") in ("Golden pocket", "38–50%")):
            bits = [x.lower() for x in sorted(sig_w & PULLBACK)]
            fs = (fibs["w"].get(t) or {}).get("status")
            if fs in ("Golden pocket", "38–50%"):
                bits.append(f"fib {fs.lower()}")
            setup, wk_txt = "Pullback", "Bullish, " + ", ".join(bits)
        elif wz == "Strong momentum" and not Zw.get("capped") and wdays <= SETUP["fresh_weeks"]:
            setup, wk_txt = "Momentum", f"strong momentum for {wdays} {'week' if wdays == 1 else 'weeks'}"
        elif wz in ("Bullish", "Strong momentum", "Extended"):
            setup, wk_txt = "In trend", f"{wz} for {wdays} weeks, no pullback yet"
        elif wz == "Accumulation":
            setup, wk_txt = "Base", f"Accumulation for {wdays} weeks"
        else:
            wk_txt = f"weekly {wz or 'no data'}"
        wk_ok = setup in ("Fresh trend", "Breakout", "Pullback", "Momentum")
        wk_bad = wz in ("Divergence zone", "Bearish", "Oversold")

        # ---- 3. daily ripple ----
        dz, rd = Zd.get("zone"), rsi_d.get(t)
        trig = bool(pd.notna(prev_wk_high.get(t)) and price > prev_wk_high[t])
        if dz == "Divergence zone":
            day, day_txt = "Wait", "daily divergence: momentum fading, wait"
        elif dz == "Extended" or (pd.notna(rd) and rd >= 80):
            day, day_txt = "Wait", f"daily {'extended' if dz == 'Extended' else 'RSI ' + format(rd, '.0f')}: wait for a dip"
        elif dz in ("Bearish",) or sig_d & {"Breakdown", "Trendline breakdown"}:
            day, day_txt = "Weak", "daily " + (dz.lower() if dz == "Bearish" else ", ".join(sorted(sig_d & {"Breakdown", "Trendline breakdown"})).lower())
        elif dz == "Oversold":
            day, day_txt = "Wait", "daily oversold: wait for it to turn up"
        elif sig_d & (PULLBACK | BREAKOUT) or trig or dz == "Accumulation":
            bits = [x.lower() for x in sorted(sig_d & (PULLBACK | BREAKOUT))]
            if trig:
                bits.append("above last week's high")
            if not bits:
                bits.append("daily base, turning up")
            day, day_txt = "Good", ", ".join(bits)
        elif dz in ("Bullish", "Strong momentum"):
            day, day_txt = "Neutral", f"daily {dz.lower()}, no fresh trigger yet"
        else:
            day, day_txt = "Neutral", f"daily {(dz or 'no data').lower()}"

        # ---- 4. sector ----
        q = secq.get(sec_of.get(t))
        sec = "OK" if q in ("Leading", "Improving") else "Mixed" if q == "Weakening" else "Weak" if q == "Lagging" else "No data"

        # ---- 5/6. stop and room ----
        cands = []
        pl = _last_pivot_low(low[t].to_numpy(float))
        if pl:
            cands.append(("daily swing low", pl * 0.995))
        kj = kijun[t].iloc[-1] if t in kijun else np.nan
        if pd.notna(kj):
            cands.append(("weekly Kijun", float(kj) * 0.995))
        if Ld.get("sup"):
            cands.append(("daily support", Ld["sup"]["p"] * 0.99))
        ok_c = [(n, s) for n, s in cands if SETUP["min_stop_pct"] <= (price - s) / price * 100 <= SETUP["max_stop_pct"]]
        stop = max(ok_c, key=lambda x: x[1]) if ok_c else None
        stop_pct = (price - stop[1]) / price * 100 if stop else None
        res = (Lw.get("res") or {}).get("p")
        room = (res / price - 1) * 100 if res else None
        fw = fibs["w"].get(t) or {}
        tg = [x for x in fw.get("t", []) if x["p"] > price]
        t1 = tg[0] if tg else None
        target = t1["p"] if t1 else res                    # reward measured to fib T1, else resistance
        up = (target / price - 1) * 100 if target else None
        rr = (up / stop_pct) if (up is not None and stop_pct) else None
        room_ok = rr is None or rr >= SETUP["good_rr"]   # no target / resistance overhead counts as room

        # ---- relative strength, earnings ----
        rsr = rs.get(t)
        ed = earn.get(t[:-3])
        edays = (date.fromisoformat(ed) - today).days if ed else None
        earn_soon = edays is not None and 0 <= edays <= EARNINGS_WARN_DAYS

        # ---- bucket ----
        mon_ok, mon_mid = mon == "OK", mon == "Mixed"
        if wk_bad or (wk_ok and mon == "Weak"):
            bucket = "Avoid"
            why = f"weekly {wz.lower()}" if wk_bad else "weekly setup against a weak monthly trend"
        elif (wk_ok and mon_ok and day == "Good" and sec != "Weak" and stop and room_ok
              and not earn_soon and not (risk_off and (sec != "OK" or (rsr or 0) < 70))):
            bucket, why = "Ready", "all three timeframes agree"
        elif wk_ok and mon_ok and day == "Good" and sec != "Weak" and stop and room_ok and earn_soon:
            bucket, why = "Setting up", f"results due in {edays} days: wait until after"
        elif wk_ok and mon_ok and day == "Good" and sec != "Weak" and stop and room_ok and risk_off:
            bucket, why = "Setting up", "risk-off market: needs a Leading or Improving sector and RS 70+"
        elif wk_ok and (mon_ok or mon_mid):
            bucket = "Setting up"
            why = ("daily: " + day_txt) if day != "Good" else ("sector lagging" if sec == "Weak" else
                   "monthly only mixed" if mon_mid else "no sensible stop nearby" if not stop else
                   f"little room to resistance (R:R {rr:.1f})")
        elif setup == "Base" and mon_ok:
            bucket, why = "Watchlist", "weekly base forming in a monthly uptrend"
        else:
            bucket, why = None, ""

        score = (mon_ok + mon_mid * 0.5) + wk_ok + (day == "Good") + (sec == "OK") + bool(room_ok and stop) + bool(stop)
        out[t] = {
            "bucket": bucket, "why": why, "score": round(score, 1),
            "mon": mon, "mon_txt": mon_txt, "mchk": checks,
            "wk": setup, "wk_ok": wk_ok, "wk_txt": wk_txt, "wz": wz,
            "day": day, "day_txt": day_txt, "dz": dz,
            "sec": sec, "q": q,
            "stop": round(stop[1], 2) if stop else None, "stop_pct": round(stop_pct, 1) if stop_pct else None,
            "stop_from": stop[0] if stop else None,
            "res": round(res, 2) if res else None, "room": round(room, 1) if room is not None else None,
            "rr": round(rr, 1) if rr is not None else None,
            "rs": rsr, "earn": ed, "edays": edays, "earn_soon": earn_soon,
            "t1": t1, "t2": tg[1] if len(tg) > 1 else None, "fib": fw.get("status"),
        }
        ser = m[t].dropna().tail(60)
        mdata[t] = {"c": [float(f"{x:.4g}") for x in ser], "d": [d.strftime("%Y-%m") for d in ser.index],
                    "sma": [None if pd.isna(x) else float(f"{x:.4g}") for x in sma[t].reindex(ser.index)],
                    "rsi": None if pd.isna(mr) else round(float(mr), 1), "chk": checks, "status": mon, "txt": mon_txt}
    return out, mdata
