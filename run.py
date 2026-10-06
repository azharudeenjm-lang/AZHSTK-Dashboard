"""Daily/weekly pipeline.

  python run.py                 # daily: prices, technicals, RRG, news
  python run.py --fundamentals  # also refresh fundamentals (run weekly)
  python run.py --demo          # offline test with synthetic data
"""
import argparse
from datetime import datetime, timedelta, timezone
import math
import sys
import time

import pandas as pd

from src import (analytics, backtest, backtest_page, dashboard, earnings, fib, levels, levels_page, profiles, pwa,
                 screener_page, series, setups, setups_page, signals, strength, watchlist_page, zones, zones_page)
import json
from src.config import BENCHMARK, DOCS, NEWS_TOP_MOVERS


def clean(o):
    """Replace NaN/inf with None so the JSON is valid."""
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fundamentals", action="store_true", help="refresh stale fundamentals")
    ap.add_argument("--max-fund", type=int, default=None, help="cap fundamentals calls this run")
    ap.add_argument("--no-news", action="store_true")
    ap.add_argument("--demo", action="store_true", help="synthetic data, no internet needed")
    ap.add_argument("--backtest", action="store_true", help="rerun the weekly zone backtest (slow, weekly)")
    a = ap.parse_args()
    t0 = time.time()

    if a.demo:
        from src.demo import make_demo
        universe, px, fund, news, mover_news = make_demo(BENCHMARK)
    else:
        from src import fundamentals, news as newsmod, prices, universe as uni
        fund = fundamentals.load()
        print("1/5 universe")
        universe = uni.build_universe(fund)
        print(f"  {len(universe)} stocks, {universe['sector'].nunique()} sectors")

        print("2/5 prices")
        px = prices.fetch_prices(universe["ticker"].tolist(), BENCHMARK)
        close, volume = px["Close"], px["Volume"]
        if BENCHMARK not in close.columns:
            sys.exit("Benchmark prices missing; Yahoo may be down. Try again later.")

        if a.fundamentals:
            print("3/5 fundamentals")
            # liquid names first, so the useful ones are done if we hit limits
            tv = (close * volume).rolling(20).mean().iloc[-1].sort_values(ascending=False)
            order = [t[:-3] for t in tv.index if t.endswith(".NS")]
            order += [s for s in universe["symbol"] if s not in set(order)]
            fund = fundamentals.refresh(order, max_calls=a.max_fund)
            universe = uni.build_universe(fund)  # re-map sectors with fresh Yahoo data
        else:
            print("3/5 fundamentals: using cache")
        news, mover_news = None, None

    close, volume = px["Close"], px["Volume"]
    print("4/5 analytics")
    sectors, stocks, bench = analytics.build_analytics(close, volume, universe, BENCHMARK)

    fmap = {}
    if fund is not None and len(fund):
        keep = ["pe", "pb", "roe", "de", "mcap_cr", "margin", "rev_g", "eps_g"]
        fmap = fund.set_index("symbol")[keep].to_dict("index")
    for s in stocks:
        s.update(fmap.get(s["sym"], {}))

    liquid_movers = sorted([s for s in stocks if s["liquid"] and s.get("r1d") is not None],
                           key=lambda s: abs(s["r1d"]), reverse=True)[:NEWS_TOP_MOVERS]
    if not a.demo:
        if a.no_news:
            news, mover_news = {}, {}
        else:
            print("5/5 news")
            news = newsmod.sector_news([s["sector"] for s in sectors])
            mover_news = newsmod.stock_news([(m["sym"], m["name"]) for m in liquid_movers])
    movers = [{"sym": m["sym"], "price": m.get("price"), "r1d": m["r1d"], "news": mover_news.get(m["sym"], [])}
              for m in liquid_movers]

    print("   zones (daily + weekly)")
    tick = universe["ticker"].tolist()
    zd, dates_d, lb_d, hd = zones.build_zones(px["Close"], px["High"], px["Low"], tick, "d", history=True, opens=px.get("Open"))
    zw, dates_w, lb_w, hw = zones.build_zones(px["Close"], px["High"], px["Low"], tick, "w", history=True, opens=px.get("Open"))
    today = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d")
    asof = px["Close"].index[-1].strftime("%Y-%m-%d")
    partial = bool(dates_w) and dates_w[-1] > today      # this week's Friday hasn't come yet
    zrows = []
    for s in stocks:
        t = s["sym"] + ".NS"
        if t in zd:
            zrows.append({"sym": s["sym"], "name": s["name"], "sector": s["sector"],
                          "liquid": s["liquid"], "price": s.get("price"), "r1d": s.get("r1d"), "r1w": s.get("r1w"),
                          "r1m": s.get("r1m"), "d": zd[t], "w": zw.get(t)})
    print("   levels (daily + weekly)")
    ld = levels.build_levels(px["Close"], px["High"], px["Low"], px["Volume"], tick, "d")
    lw = levels.build_levels(px["Close"], px["High"], px["Low"], px["Volume"], tick, "w")
    print("   fibonacci, relative strength, regime, earnings")
    fibs = fib.build(px, tick, ld, lw)
    for tf, lv in (("d", ld), ("w", lw)):          # golden-pocket pullbacks become a Levels signal
        for t, f in fibs[tf].items():
            if f["status"] == "Golden pocket" or (f["status"] == "38–50%" and f["conf"]):
                row = lv.setdefault(t, {"sig": []})
                if "At Fibonacci support" not in row["sig"]:
                    row["sig"].append("At Fibonacci support")
    liq = pd.Series({s["sym"] + ".NS": bool(s["liquid"]) for s in stocks})
    rs = strength.rs_rank(px["Close"].drop(columns=[BENCHMARK], errors="ignore"), liq)
    reg = strength.regime(px["Close"], BENCHMARK, liq)
    earn = {} if a.demo else earnings.fetch()
    if a.demo:   # a few fake dates so the warning can be seen
        earn = {s["sym"]: (datetime.now() + timedelta(days=5 + i)).strftime("%Y-%m-%d") for i, s in enumerate(stocks[:40:3])}
    print(f"  market regime: {reg['state']} (score {reg['score']})")
    (DOCS / "regime.json").write_text(json.dumps(clean(reg)), encoding="utf-8")
    volx = {s["sym"]: s.get("vol_x") for s in stocks}
    lrows = []
    for r in zrows:
        t = r["sym"] + ".NS"
        if t in ld or t in lw:
            lrows.append({**{k: r[k] for k in ("sym", "name", "sector", "liquid", "price", "r1d", "r1w", "r1m")},
                          "zd": r["d"]["zone"], "zw": (r.get("w") or {}).get("zone"),
                          "vx": volx.get(r["sym"]),
                          "d": ld.get(t), "w": lw.get(t)})
    charts = {}
    for r in lrows:
        for tf in ("d", "w"):
            if r.get(tf) and "ch" in r[tf]:
                charts.setdefault(r["sym"], {})[tf] = r[tf].pop("ch")
    levels_page.render(clean({"stocks": lrows, "partial": partial, "asof": asof}), clean(charts))
    print("   trade setups (monthly + weekly + daily)")
    su, mon = setups.build(px, universe, zd, zw, ld, lw, sectors, rs, reg, earn, fibs)
    srows = []
    for s in stocks:
        t = s["sym"] + ".NS"
        if t in su:
            srows.append({"sym": s["sym"], "name": s["name"], "sector": s["sector"], "liquid": s["liquid"],
                          "price": s.get("price"), **su[t]})
    setups_page.render(clean({"stocks": srows, "regime": reg}))
    watchlist_page.render()
    print("   screener")
    sg = signals.build(px, tick, ld, lw, fibs)
    ser = series.build(px, tick)
    secq = {x["sector"]: x.get("q_w") for x in sectors}
    scr_rows = []
    for s_ in stocks:
        t = s_["sym"] + ".NS"
        if t not in zd:
            continue
        u = su.get(t, {})
        scr_rows.append({"sym": s_["sym"], "name": s_["name"], "sector": s_["sector"], "liquid": bool(s_["liquid"]),
                         "price": s_.get("price"), "r1d": s_.get("r1d"), "r1m": s_.get("r1m"), "r3m": s_.get("r3m"),
                         "rs": rs.get(t), "zd": zd[t]["zone"], "zw": (zw.get(t) or {}).get("zone"),
                         "bucket": u.get("bucket"), "q": secq.get(s_["sector"]), "hi": s_.get("from_high"),
                         "es": bool(u.get("earn_soon"))})
    sg_sym = {tf: {t[:-3]: v for t, v in sg[tf].items()} for tf in ("d", "w")}
    ser_sym = {tf: {t[:-3]: v for t, v in ser[tf].items()} for tf in ("d", "w")}
    screener_page.render(clean(scr_rows), clean(sg_sym), clean(ser_sym))
    pwa.write()
    print("   stock profiles")
    gen = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%d %b %Y, %I:%M %p IST")
    profiles.write(clean(stocks), clean(sectors), clean({"d": zd, "w": zw}), clean({"d": hd, "w": hw}),
                   clean({"d": ld, "w": lw}), fmap, {"d": dates_d, "w": dates_w}, gen,
                   {"partial": partial, "asof": asof}, clean(su), clean(mon),
                   extra={"rs": rs, "earn": earn, "fib": clean(fibs), "sg": sg, "ser": clean(ser)})
    zones_page.render(clean({"stocks": zrows,
                             "tf": {"d": {"dates": dates_d, "lb_start": lb_d},
                                    "w": {"dates": dates_w, "lb_start": lb_w,
                                          "partial": partial, "asof": asof}}}))

    out = dashboard.render(clean({"sectors": sectors, "stocks": stocks, "bench": bench,
                                  "news": news, "movers": movers}))
    if a.backtest:
        print("   backtest (weekly, 10 years)")
        if a.demo:
            wk = {f: (px[f].resample("W-FRI").last() if f == "Close" else
                      px[f].resample("W-FRI").max() if f == "High" else
                      px[f].resample("W-FRI").min() if f == "Low" else
                      px[f].resample("W-FRI").sum()) for f in ("Close", "High", "Low", "Volume")}
        else:
            wk = backtest.download_weekly(universe["ticker"].tolist(), BENCHMARK)
        backtest_page.render(clean(backtest.run(wk, universe, BENCHMARK)))
    backtest_page.publish()
    print(f"done in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
