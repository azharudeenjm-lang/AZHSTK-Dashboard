"""Daily/weekly pipeline.

  python run.py                 # daily: prices, technicals, RRG, news
  python run.py --fundamentals  # also refresh fundamentals (run weekly)
  python run.py --demo          # offline test with synthetic data
"""
import argparse
import math
import sys
import time

import pandas as pd

from src import analytics, dashboard, zones, zones_page
from src.config import BENCHMARK, NEWS_TOP_MOVERS


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
    movers = [{"sym": m["sym"], "r1d": m["r1d"], "news": mover_news.get(m["sym"], [])}
              for m in liquid_movers]

    print("   zones (daily + weekly)")
    tick = universe["ticker"].tolist()
    zd, dates_d, lb_d = zones.build_zones(px["Close"], px["High"], px["Low"], tick, "d")
    zw, dates_w, lb_w = zones.build_zones(px["Close"], px["High"], px["Low"], tick, "w")
    zrows = []
    for s in stocks:
        t = s["sym"] + ".NS"
        if t in zd:
            zrows.append({"sym": s["sym"], "name": s["name"], "sector": s["sector"],
                          "liquid": s["liquid"], "r1d": s.get("r1d"), "r1w": s.get("r1w"),
                          "r1m": s.get("r1m"), "d": zd[t], "w": zw.get(t)})
    zones_page.render(clean({"stocks": zrows,
                             "tf": {"d": {"dates": dates_d, "lb_start": lb_d},
                                    "w": {"dates": dates_w, "lb_start": lb_w}}}))

    out = dashboard.render(clean({"sectors": sectors, "stocks": stocks, "bench": bench,
                                  "news": news, "movers": movers}))
    print(f"done in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
