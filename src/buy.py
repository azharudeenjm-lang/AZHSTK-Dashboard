"""Buy criteria: weekly momentum breakout with stop-loss and trailing stop.

Signal (weekly bar, the week in progress counts but is marked "forming"):
  1. Close above the highest high of the previous 12 weeks (breakout)
  2. Up at least 8% on the week (a strong push, not a drift)
  3. Relative strength: 6-month return in the top 20% of liquid stocks
  4. Close within 5% of the 52-week high (strong stocks near highs, not bottom-fishing)
  5. Liquid stock
Flags (shown, not hidden): NSE surveillance (ASM/GSM), promoter pledge over 25%,
results due within 10 days, a wide stop (risk over 15%).

Market filter: new entries only while market breadth (share of liquid stocks closing above their own
50-day MA, on the signal week's last day) is above 60%. Tested on real prices (Oct 2024 - Oct 2026):
average per closed trade +1.1% with no filter, +2.2% above 50%, +2.4% above 60%; in the weak
Jul-Dec 2025 stretch it turned -0.1% (221 trades) into +2.2% (27 trades). Open trades keep their stops.
The page can switch the track record between 60%, 50% and no filter.

Stops:
  Initial stop-loss  = low of the breakout week (exit if a week closes below it)
  Trailing stop      = the higher of the initial stop and the 10-week average;
                       exit on the first weekly close below it.
Tested on the dashboard's own 5-year weekly history (see "track record" on the page):
fewer than half the trades win, but winners are several times bigger than losers.
"""
import numpy as np
import pandas as pd

from .zones import weekly_bars

LOOK_BASE, MIN_GAIN, RS_MIN, NEAR_HI, TRAIL_N = 12, 0.08, 0.80, 0.95, 10
BREADTH_MIN = 0.60       # live rule; the page also shows 0.50 and no filter
VARIANTS = {"60": 0.60, "50": 0.50, "0": None}
SHOW_WEEKS = 26          # trades opened in the last 26 weeks are tracked on the page
META = [
    ("by_new", "Buy criteria: new weekly breakout signal", "e"),
    ("by_act", "Buy criteria: open trade, still above its trailing stop", "s"),
    ("by_watch", "Buy criteria: on the watch list (close to triggering)", "s"),
]


def _f(x, n=2):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def build(px, stocks, facts=None, earn=None, today=None):
    """stocks: list of dicts (sym, name, sector, liquid, price).
    Returns (page data dict, {sym: pop-up record}, {ticker: screener conditions})."""
    facts, earn = facts or {}, earn or {}
    info = {s["sym"]: s for s in stocks}
    cols = [s["sym"] + ".NS" for s in stocks if s["sym"] + ".NS" in px["Close"].columns]
    c, h, l = weekly_bars(px["Close"][cols], px["High"][cols], px["Low"][cols])
    c, h, l = c.ffill(limit=2), h, l
    liquid = pd.Series({t: bool(info[t[:-3]].get("liquid")) for t in cols})
    ret26 = c / c.shift(26) - 1
    rs = ret26.loc[:, liquid[liquid].index].rank(axis=1, pct=True).reindex(columns=cols)
    hh = h.rolling(LOOK_BASE, min_periods=LOOK_BASE).max().shift(1)
    hi52 = h.rolling(52, min_periods=40).max().shift(1)
    wk = c / c.shift(1) - 1
    sma = c.rolling(TRAIL_N, min_periods=TRAIL_N).mean()
    sig = (c > hh) & (wk >= MIN_GAIN) & (rs >= RS_MIN) & (c >= NEAR_HI * hi52)
    sig = sig & liquid.reindex(cols).fillna(False).values
    # market breadth: share of liquid stocks closing above their own 50-day MA (last day of each week)
    lq = [t for t in cols if liquid.get(t)]
    dC = px["Close"][lq]
    d50 = dC.rolling(50, min_periods=50).mean()
    br_d = (dC > d50).sum(axis=1) / d50.notna().sum(axis=1).replace(0, np.nan)
    br_w = br_d.resample("W-FRI").last().reindex(c.index)
    BR = br_w.to_numpy(float)
    sig_raw = sig
    sig = sig_raw & (br_w > BREADTH_MIN).fillna(False).to_numpy()[:, None]

    dates = c.index
    n = len(dates)
    today = pd.Timestamp(today or pd.Timestamp.now(tz="Asia/Kolkata").date())
    forming = bool(n) and dates[-1] > today          # this week's Friday hasn't come yet
    C, H, L, S, G = c.to_numpy(float), h.to_numpy(float), l.to_numpy(float), sma.to_numpy(float), sig.to_numpy(bool)
    HH, HI, RS = hh.to_numpy(float), hi52.to_numpy(float), rs.to_numpy(float)
    ds = [d.strftime("%Y-%m-%d") for d in dates]

    # ---------- walk every stock through its whole history (for the track record) ----------
    def walk(GG):
        """Trades for a signal matrix: (closed trades, open trades, {column: trade still open})."""
        done_, open_, inside_at = [], [], {}
        for j, t in enumerate(cols):
            sym = t[:-3]
            cc, hh_, ll, ss, gg = C[:, j], H[:, j], L[:, j], S[:, j], GG[:, j]
            inside = None
            for i in range(n):
                if np.isnan(cc[i]):
                    continue
                if inside is None:
                    if gg[i]:
                        inside = {"i": i, "e": cc[i], "sl": ll[i], "mx": cc[i]}
                    continue
                inside["mx"] = max(inside["mx"], hh_[i] if np.isfinite(hh_[i]) else cc[i])
                trail = max(inside["sl"], ss[i] if np.isfinite(ss[i]) else -1)
                if cc[i] < trail:
                    done_.append({"sym": sym, "i": inside["i"], "x": i, "e": inside["e"], "xp": cc[i], "r": cc[i] / inside["e"] - 1,
                                  "mx": inside["mx"] / inside["e"] - 1, "br": BR[inside["i"]],
                                  "why": "Stop-loss (breakout-week low)" if trail <= inside["sl"] else "Weekly close below 10-week average"})
                    inside = None
                    if gg[i]:          # a fresh signal on the exit bar starts a new trade
                        inside = {"i": i, "e": cc[i], "sl": ll[i], "mx": cc[i]}
            last = cc[-1] if n else np.nan
            if inside is not None and np.isfinite(last):
                open_.append({"sym": sym, "i": inside["i"], "e": inside["e"], "xp": last, "r": last / inside["e"] - 1,
                              "mx": max(inside["mx"], last) / inside["e"] - 1, "br": BR[inside["i"]]})
            inside_at[j] = inside
        return done_, open_, inside_at

    runs = {k: walk(G if v == BREADTH_MIN else (sig_raw & (br_w > v).fillna(False).to_numpy()[:, None]).to_numpy(bool) if v else sig_raw.to_numpy(bool))
            for k, v in VARIANTS.items()}
    trades_all, open_all, inside_at = runs["60"]
    exits_recent = [x for x in trades_all if x["x"] >= n - 9]
    open_now, watch, recs, sc = [], [], {}, {}
    start_show = n - SHOW_WEEKS
    for j, t in enumerate(cols):
        sym = t[:-3]
        inside = inside_at[j]
        last = C[-1, j] if n else np.nan
        f = facts.get(sym, {})
        flags = []
        if f.get("asm"):
            flags.append(f"Surveillance: {f['asm']}")
        if (f.get("plg") or 0) > 25:
            flags.append(f"Pledge {f['plg']:.0f}%")
        e = earn.get(sym)
        if e:
            dd = (pd.Timestamp(e) - today).days
            if 0 <= dd <= 10:
                flags.append(f"Results in {dd} days")
        if inside is not None and inside["i"] >= max(0, start_show):
            i0 = inside["i"]
            trail = max(inside["sl"], S[-1, j] if np.isfinite(S[-1, j]) else -1)
            risk = 1 - inside["sl"] / inside["e"] if inside["e"] else None
            if risk is not None and risk > 0.15:
                flags.append("Wide stop: size smaller")
            row = {"sym": sym, "name": info[sym]["name"], "sector": info[sym].get("sector"), "grade": f.get("qg"),
                   "sd": ds[i0], "ago": n - 1 - i0, "entry": _f(inside["e"]), "sl": _f(inside["sl"]),
                   "risk": _f(risk * 100 if risk is not None else None, 1),
                   "trail": _f(trail), "price": _f(last), "gain": _f((last / inside["e"] - 1) * 100, 1),
                   "best": _f((inside["mx"] / inside["e"] - 1) * 100, 1),
                   "room": _f((last / trail - 1) * 100, 1) if trail > 0 else None,
                   "rs": _f(RS[i0, j] * 100, 0), "wkg": _f(C[i0, j] / C[i0 - 1, j] * 100 - 100, 1) if i0 > 0 else None,
                   "forming": forming and i0 == n - 1, "flags": flags,
                   "trail_kind": "10-week average" if trail > inside["sl"] else "initial stop (breakout-week low)"}
            open_now.append(row)
            recs[sym] = {"st": "new" if i0 >= n - 2 else "open", **{k: row[k] for k in
                         ("sd", "entry", "sl", "risk", "trail", "gain", "best", "room", "forming", "flags", "trail_kind")}}
            sc[t] = {"by_act": 1}
            if i0 >= n - 10:
                sc[t]["by_new"] = n - 1 - i0
        elif liquid.get(t) and n > 1 and np.isfinite(last):
            # watch list: strong and near highs, within 5% of the 12-week breakout level
            r_, trig, hi = RS[-1, j], HH[-1, j], HI[-1, j]
            if np.isfinite(r_) and r_ >= RS_MIN and np.isfinite(trig) and np.isfinite(hi) and \
                    trig * 0.95 <= last <= trig and last >= 0.9 * hi:
                need = trig * (1 + 0.0001)
                row = {"sym": sym, "name": info[sym]["name"], "sector": info[sym].get("sector"), "grade": f.get("qg"), "price": _f(last),
                       "trig": _f(trig), "dist": _f((trig / last - 1) * 100, 1), "rs": _f(r_ * 100, 0),
                       "hi52": _f((last / hi - 1) * 100, 1), "need8": _f(max(need, (C[-2, j] if forming else C[-1, j]) * (1 + MIN_GAIN))),
                       "flags": flags}
                watch.append(row)
                recs[sym] = {"st": "watch", "trig": row["trig"], "need8": row["need8"], "dist": row["dist"]}
                sc[t] = {"by_watch": 1}

    # ---------- track record of the rule on this data ----------
    def stats_of(done):
        if not done:
            return None
        r = np.array([x["r"] for x in done])
        mx = np.array([x["mx"] for x in done])
        hold = np.array([x["x"] - x["i"] for x in done])
        w, lo = r[r > 0], r[r <= 0]
        return {"n": int(len(r)), "win": _f(len(w) / len(r) * 100, 0), "avg_win": _f(w.mean() * 100 if len(w) else 0, 1),
                "avg_loss": _f(lo.mean() * 100 if len(lo) else 0, 1), "exp": _f(r.mean() * 100, 1),
                "big": _f(np.mean(mx >= 0.5) * 100, 0), "hold": int(np.median(hold)),
                "years": [{"y": y, "n": int(sum(1 for x in done if ds[x["i"]][:4] == y)),
                           "exp": _f(np.mean([x["r"] for x in done if ds[x["i"]][:4] == y]) * 100, 1),
                           "win": _f(np.mean([x["r"] > 0 for x in done if ds[x["i"]][:4] == y]) * 100, 0)}
                          for y in sorted({ds[x["i"]][:4] for x in done})],
                "from": ds[0] if ds else None, "best": sorted(
                    [{"sym": x["sym"], "sd": ds[x["i"]], "r": _f(x["r"] * 100, 0)} for x in done], key=lambda x: -x["r"])[:5]}

    since = (today - pd.Timedelta(days=730)).strftime("%Y-%m-%d")

    def stats2(done, opn):
        """Last 2 years: closed trades, and closed plus open at today's price."""
        d2 = [x["r"] for x in done if ds[x["i"]] >= since]
        a2 = d2 + [x["r"] for x in opn if ds[x["i"]] >= since]
        return {"n": len(d2), "nopen": len(a2) - len(d2), "exp": _f(np.mean(d2) * 100, 1) if d2 else None,
                "win": _f(np.mean(np.array(d2) > 0) * 100, 0) if d2 else None, "exp_all": _f(np.mean(a2) * 100, 1) if a2 else None}

    stats = stats_of(trades_all)
    variants = {k: {"stats": stats_of(v[0]), "two": stats2(v[0], v[1])} for k, v in runs.items()}
    open_now.sort(key=lambda x: (x["ago"], -(x["rs"] or 0)))
    watch.sort(key=lambda x: x["dist"])
    exits = sorted([{"sym": x["sym"], "name": info[x["sym"]]["name"], "sd": ds[x["i"]], "xd": ds[x["x"]],
                     "entry": _f(x["e"]), "exit": _f(x["xp"]), "r": _f(x["r"] * 100, 1)} for x in exits_recent],
                   key=lambda x: x["xd"], reverse=True)
    # every trade of the last 2 years for the "All past trades" tab:
    # sym, signal week, entry, exit week, exit (or price now), gain, max gain, reason, weeks held
    # (+ market breadth % on the signal week)
    def log_of(done, opn):
        out = [[x["sym"], ds[x["i"]], _f(x["e"]), ds[x["x"]], _f(x["xp"]), _f(x["r"] * 100, 1), _f(x["mx"] * 100, 1), x["why"],
                int(x["x"] - x["i"]), _f(x["br"] * 100, 0)] for x in done if ds[x["i"]] >= since]
        out += [[x["sym"], ds[x["i"]], _f(x["e"]), None, _f(x["xp"]), _f(x["r"] * 100, 1), _f(x["mx"] * 100, 1), None,
                 int(n - 1 - x["i"]), _f(x["br"] * 100, 0)] for x in opn if ds[x["i"]] >= since]
        return out

    logs = {k: log_of(v[0], v[1]) for k, v in runs.items()}
    bnow = BR[-1] if n else np.nan
    mkt = {"min": int(BREADTH_MIN * 100), "now": _f(bnow * 100, 0), "ok": bool(np.isfinite(bnow) and bnow > BREADTH_MIN),
           "hist": [[ds[i], _f(BR[i] * 100, 0)] for i in range(max(0, n - 26), n)]}
    # stocks that broke out this week or last but were blocked by the market filter
    blocked = []
    if n:
        SR = sig_raw.to_numpy(bool)
        for i in range(max(0, n - 2), n):
            if not G[i].any() and SR[i].any():
                blocked += [{"sym": cols[j][:-3], "name": info[cols[j][:-3]]["name"], "sd": ds[i], "rs": _f(RS[i, j] * 100, 0),
                             "price": _f(C[-1, j])} for j in np.where(SR[i])[0]]
    page = {"open": open_now, "watch": watch[:60], "exits": exits[:40], "stats": stats, "forming": forming,
            "week": ds[-1] if ds else None, "log": logs["60"], "logs": logs, "variants": variants, "mkt": mkt,
            "blocked": blocked[:40]}
    frames = {"c": c, "l": l, "sma": sma, "sig": sig, "rs": rs, "forming": forming}
    return page, recs, sc, frames
