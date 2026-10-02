"""Central settings. Edit these to tune the dashboard."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = DATA / "cache"
DOCS = ROOT / "docs"          # GitHub Pages serves this folder

BENCHMARK = "^NSEI"           # NIFTY 50. Use "^CRSLDX" for NIFTY 500.
PRICE_HISTORY = "5y"          # weekly Ichimoku needs ~80 weeks of warm-up
BATCH_SIZE = 150              # tickers per yfinance download call

# RRG settings (JdK-style approximation; the original formula is proprietary)
RRG_WINDOW = 14               # smoothing window for RS-Ratio / RS-Momentum
TAIL_DAILY = 10               # points of tail on the daily RRG
TAIL_WEEKLY = 8               # points of tail on the weekly RRG

# A stock enters sector indices and RRGs only if it is liquid enough
MIN_AVG_TURNOVER_CR = 1.0     # 20-day average traded value, in Rs crore
MIN_HISTORY_DAYS = 120

# Sectors with fewer liquid stocks than this are left off the sector RRG
MIN_STOCKS_PER_SECTOR = 5

# Fundamentals are slow to fetch for 2000+ stocks, so refresh weekly
FUNDAMENTALS_MAX_AGE_DAYS = 7
FUNDAMENTALS_SLEEP_SEC = 0.6  # politeness delay between Yahoo calls

NEWS_PER_SECTOR = 6
NEWS_TOP_MOVERS = 10          # also fetch headlines for the biggest movers

# ---------- Zone classifier (zones.html) ----------
# Indicator settings are standard on both timeframes (RSI 14, MACD 12/26/9,
# ADX 14, Choppiness 14, Ichimoku 9/26/52). What changes is every rule that
# counts bars, because one weekly bar is about five daily bars.
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
ADX_TREND = 20               # ADX at or above this = trending
CHOP_TRENDING = 61.8         # Choppiness below this = trending
CHOP_RANGE = 55              # Choppiness at or above this = range-bound / basing

ZONE_PARAMS = {
    "d": {
        "label": "Daily", "unit": "session", "units": "sessions",
        "lookback": 120,          # bars of zone history kept
        "confirm": 2,             # trend zones must hold this many bars
        "new_bars": 5,            # "new entry" window
        "hist_rise_bars": 5,      # accumulation: MACD histogram higher than N bars ago
        "trend_window": 60, "trend_bars": 40,   # danger: above cloud on 40 of last 60
        "ob_window": 20, "ob_bars": 8,          # danger: RSI>=70 on 8 of last 20
        "ma": 50, "stretch": 20,                # danger: 20%+ above 50-day average
        "rsi_floor": 60,                        # danger ends when RSI cools below this
    },
    "w": {
        "label": "Weekly", "unit": "week", "units": "weeks",
        "lookback": 104,          # two years of weekly zones
        "confirm": 1,             # a weekly close is already a filter
        "new_bars": 2,
        "hist_rise_bars": 3,
        "trend_window": 26, "trend_bars": 20,   # above cloud on 20 of last 26 weeks
        "ob_window": 10, "ob_bars": 4,          # weekly RSI>=70 on 4 of last 10 weeks
        "ma": 30, "stretch": 30,                # 30%+ above 30-week average
        "rsi_floor": 60,
    },
}
