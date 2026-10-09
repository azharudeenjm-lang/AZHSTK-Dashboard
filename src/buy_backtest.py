"""Long backtest of the Buy criteria rule from 2020, run on GitHub (it needs internet).

  python run.py --buy-backtest      (or tick "Buy criteria backtest" when running the workflow)

Downloads daily prices from Jan 2019 (2020 needs a year of history first), then
replays the rule day by day with ₹10,00,000, up to 10 stocks, 0.15% cost per side,
in four versions:
  friday   buy and sell only at the Friday close (the original rule)
  mid_in   buy on any day the stock qualifies, sell only at the Friday close
  daily    buy and sell at any day's close
  touch    buy any day, sell the moment the price touches the stop (like 30-minute checks)
Unlike the quick tests, liquidity (20-day average turnover of ₹1 crore+) and the
relative-strength ranking use only what was known on each day, so there is no
hindsight there. The stock list is still today's (delisted companies are missing).
Writes docs/buy_backtest.html and docs/buy_backtest_trades.csv.
"""
import json
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from .config import CACHE, DOCS, MIN_AVG_TURNOVER_CR

START = "2019-01-01"
FROM = "2020-01-01"
CAP, SLOTS, COST = 1_000_000, 10, 0.0015
MODES = {"friday": "Buy and sell only at the Friday close",
         "mid_in": "Buy any day, sell only at the Friday close",
         "daily": "Buy and sell at any day's close",
         "touch": "Buy any day, sell the moment the stop is touched"}


def _download(tickers):
    path = CACHE / "bt_daily.pkl"
    try:
        old = pd.read_pickle(path)
        if old["Close"].index[-1] >= pd.Timestamp.now().normalize() - pd.Timedelta(days=5):
            print("  buy backtest: using cached daily history")
            return old
    except Exception:
        pass
    import yfinance as yf
    parts = {f: [] for f in ("Open", "High", "Low", "Close", "Volume")}
    for i in range(0, len(tickers), 40):
        b = tickers[i:i + 40]
        for k in range(2):
            try:
                df = yf.download(b, start=START, interval="1d", auto_adjust=True, group_by="column",
                                 threads=4, timeout=30, progress=False)
                if df is not None and not df.empty:
                    if not isinstance(df.columns, pd.MultiIndex):
                        df.columns = pd.MultiIndex.from_product([df.columns, b])
                    for f in parts:
                        parts[f].append(df[f])
                break
            except Exception as e:
                print(f"  ! batch {i}: {str(e)[:80]}")
                time.sleep(10)
        if (i // 40) % 10 == 0:
            print(f"  buy backtest download {min(i + 40, len(tickers))}/{len(tickers)}")
        time.sleep(2)
    out = {}
    for f, lst in parts.items():
        d = pd.concat(lst, axis=1).sort_index()
        d = d.loc[:, ~d.columns.duplicated()]
        d.index = pd.to_datetime(d.index).tz_localize(None)
        out[f] = d.astype(float)
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        pd.to_pickle(out, path)
    except Exception:
        pass
    return out


def run(tickers, benchmark, names=None):
    names = names or {}
    t0 = time.time()
    D = _download(list(dict.fromkeys([benchmark] + list(tickers))))
    bench = D["Close"].get(benchmark)
    cols = [t for t in tickers if t in D["Close"].columns]
    O, H, L, C, V = (D[f][cols] for f in ("Open", "High", "Low", "Close", "Volume"))
    cnt = C.notna().sum(axis=1)
    keep = cnt >= 0.5 * cnt.max()
    O, H, L, C, V = (x[keep] for x in (O, H, L, C, V))
    days = C.index
    # point-in-time liquidity (yesterday's 20-day average turnover) and listing age
    liquid = ((C * V).rolling(20, min_periods=15).mean().shift(1) / 1e7 >= MIN_AVG_TURNOVER_CR) & \
             (C.notna().cumsum() >= 120)
    # completed weekly bars from daily data
    wk = days + pd.to_timedelta((4 - days.weekday) % 7, unit="D")
    WC = C.groupby(wk).last(); WH = H.groupby(wk).max(); WL = L.groupby(wk).min()
    hh12 = WH.rolling(12, min_periods=12).max(); hi52 = WH.rolling(52, min_periods=40).max()
    sma10 = WC.rolling(10, min_periods=10).mean()
    prev = wk - pd.Timedelta(days=7)

    def at(F, labels):
        G = F.reindex(F.index.union(pd.Index(labels).unique())).ffill()
        return G.loc[labels].to_numpy(float)
    HH, HI, SMp, CP = at(hh12, prev), at(hi52, prev), at(sma10, prev), at(WC, prev)
    C26 = at(WC, prev - pd.Timedelta(weeks=25))
    SMc = at(sma10, wk)
    Cn, On, Ln = C.to_numpy(float), O.to_numpy(float), L.to_numpy(float)
    LIQ = liquid.to_numpy(bool)
    ret26 = np.where(LIQ, Cn / C26 - 1, np.nan)
    RS = pd.DataFrame(ret26).rank(axis=1, pct=True).to_numpy(float)
    with np.errstate(invalid="ignore"):
        SIG = (Cn > HH) & (Cn / CP - 1 >= 0.08) & (RS >= 0.8) & (Cn >= 0.95 * HI) & LIQ
    WKLOW = L.groupby(wk).cummin().to_numpy(float)
    fri = (pd.Series(days).groupby(wk).transform("max").to_numpy() == days.to_numpy())
    wid = wk.strftime("%Y-%m-%d").to_numpy()
    first = int(np.searchsorted(days, pd.Timestamp(FROM)))
    print(f"  buy backtest: {len(cols)} stocks, {days[first]:%d %b %Y} to {days[-1]:%d %b %Y}, prepared in {time.time() - t0:.0f}s")

    results, all_trades = {}, []
    for mode in MODES:
        cash, pos, log, eq = float(CAP), {}, [], []
        for i in range(first, len(days)):
            f = fri[i]
            check_exit = mode in ("daily", "touch") or f
            if check_exit:
                for j in list(pos):
                    p = pos[j]
                    c = Cn[i, j]
                    if not np.isfinite(c):
                        continue
                    sm = SMc[i, j] if (f and mode in ("friday", "mid_in")) else SMp[i, j]
                    tr = max(p["sl"], sm if np.isfinite(sm) else -1)
                    px_ = None
                    if mode == "touch":
                        lo, op = Ln[i, j], On[i, j]
                        if np.isfinite(lo) and lo <= tr:
                            px_ = min(op, tr) if np.isfinite(op) else tr
                    elif c < tr:
                        px_ = c
                    if px_ is not None:
                        cash += p["q"] * px_ * (1 - COST)
                        log.append({"mode": mode, "sym": cols[j][:-3], "name": names.get(cols[j][:-3], ""), "buy": days[p["i"]].strftime("%Y-%m-%d"),
                                    "buy_px": round(p["ep"], 2), "qty": p["q"], "stop": round(p["sl"], 2), "sell": days[i].strftime("%Y-%m-%d"),
                                    "sell_px": round(px_, 2), "why": "Stop-loss" if tr == p["sl"] else "Trailing stop",
                                    "pnl": round(p["q"] * (px_ * (1 - COST) - p["ep"] * (1 + COST)), 0),
                                    "pct": round((px_ * (1 - COST) / (p["ep"] * (1 + COST)) - 1) * 100, 2), "wk": wid[i]})
                        del pos[j]
            buy_now = mode != "friday" or f
            if buy_now and len(pos) < SLOTS:
                val = cash + sum(p["q"] * (Cn[i, j] if np.isfinite(Cn[i, j]) else p["ep"]) for j, p in pos.items())
                sold = {x["sym"] for x in log if x["wk"] == wid[i]}
                cand = [j for j in np.flatnonzero(SIG[i]) if j not in pos and cols[j][:-3] not in sold]
                cand.sort(key=lambda j: -RS[i, j])
                for j in cand:
                    if len(pos) >= SLOTS:
                        break
                    c, sl = Cn[i, j], WKLOW[i, j]
                    if not (np.isfinite(sl) and c > sl):
                        continue
                    q = int(min(val / SLOTS, cash) // (c * (1 + COST)))
                    if q < 1:
                        continue
                    cash -= q * c * (1 + COST)
                    pos[j] = {"q": q, "ep": c, "sl": sl, "i": i}
            eq.append(cash + sum(p["q"] * (Cn[i, j] if np.isfinite(Cn[i, j]) else p["ep"]) for j, p in pos.items()))
        for j, p in pos.items():
            c = Cn[-1, j] if np.isfinite(Cn[-1, j]) else p["ep"]
            log.append({"mode": mode, "sym": cols[j][:-3], "name": names.get(cols[j][:-3], ""), "buy": days[p["i"]].strftime("%Y-%m-%d"),
                        "buy_px": round(p["ep"], 2), "qty": p["q"], "stop": round(p["sl"], 2), "sell": "open", "sell_px": round(c, 2),
                        "why": "Still open", "pnl": round(p["q"] * (c - p["ep"] * (1 + COST)), 0),
                        "pct": round((c / (p["ep"] * (1 + COST)) - 1) * 100, 2), "wk": ""})
        e = pd.Series(eq, index=days[first:])
        closed = [x for x in log if x["sell"] != "open"]
        r = np.array([x["pct"] for x in closed]) if closed else np.array([0.0])
        yr = e.groupby(e.index.year).last()
        prev_v = [CAP] + list(yr.values[:-1])
        results[mode] = {"name": MODES[mode], "final": round(e.iloc[-1]), "ret": round((e.iloc[-1] / CAP - 1) * 100, 1),
                         "cagr": round(((e.iloc[-1] / CAP) ** (365.25 / max(1, (e.index[-1] - e.index[0]).days)) - 1) * 100, 1),
                         "dd": round(((e / e.cummax()) - 1).min() * 100, 1), "trades": len(log),
                         "win": round(float(np.mean(r > 0)) * 100, 0), "avg_win": round(float(r[r > 0].mean()) if (r > 0).any() else 0, 1),
                         "avg_loss": round(float(r[r <= 0].mean()) if (r <= 0).any() else 0, 1),
                         "years": [{"y": int(y), "end": round(v), "ret": round((v / pv - 1) * 100, 1)} for (y, v), pv in zip(yr.items(), prev_v)],
                         "curve": [[d.strftime("%Y-%m-%d"), round(v)] for d, v in e.iloc[::5].items()]}
        all_trades += log
        print(f"  buy backtest {mode}: ₹{e.iloc[-1]:,.0f} ({results[mode]['ret']:+.1f}%), {len(log)} trades")
    bm = None
    if bench is not None:
        b = bench.reindex(days[first:]).ffill().dropna()
        if len(b):
            by = b.groupby(b.index.year).last()
            pv = [b.iloc[0]] + list(by.values[:-1])
            bm = {"ret": round((b.iloc[-1] / b.iloc[0] - 1) * 100, 1),
                  "years": [{"y": int(y), "ret": round((v / p - 1) * 100, 1)} for (y, v), p in zip(by.items(), pv)],
                  "curve": [[d.strftime("%Y-%m-%d"), round(v / b.iloc[0] * CAP)] for d, v in b.iloc[::5].items()]}
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    payload = {"generated": ist.strftime("%d %b %Y, %I:%M %p IST"), "from": days[first].strftime("%Y-%m-%d"),
               "to": days[-1].strftime("%Y-%m-%d"), "stocks": len(cols), "res": results, "bench": bm}
    DOCS.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_trades).drop(columns=["wk"], errors="ignore").to_csv(DOCS / "buy_backtest_trades.csv", index=False)
    (DOCS / "buy_backtest.json").write_text(json.dumps(payload), encoding="utf-8")
    from .buy_backtest_page import render
    render(payload)
    print(f"  buy backtest done in {time.time() - t0:.0f}s")
    return payload
