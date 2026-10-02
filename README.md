# NSE sector rotation dashboard

Groups every NSE-listed stock (~2,000+) into sectors and publishes one page you
can open on your phone, refreshed every trading day:

- Sector RRG vs NIFTY 50, daily and weekly, with rotation tails
- Stock RRG inside each sector, against that sector's own index
- Technicals: 1D/1W/1M/3M returns, RSI, distance from 50/200 DMA and 52-week high, volume spike
- Fundamentals (weekly): market cap, P/E, P/B, ROE, debt/equity, margin, growth
- Breadth per sector (advancers/decliners, % above 50 and 200 DMA)
- News: sector headlines plus headlines for the day's biggest movers
- A second page, `zones.html`, sorting every stock into six technical zones
  (Bearish, Oversold, Accumulation, Bullish, Overbought, Danger zone) using RSI,
  MACD, ADX/DMI, Choppiness Index and the Ichimoku cloud, with the date each stock
  entered its zone and a 30-session zone history

## Zones page

Has a Daily / Weekly switch. Each bar of recent history is classified (120
daily sessions, 104 weeks), so entry dates come straight from price history and
need no database. Weekly uses completed Friday-ending weeks only.

Indicator settings are standard on both timeframes. Rules that count bars are
scaled separately in `ZONE_PARAMS` in `src/config.py`, for example the danger
zone looks at 60 sessions on daily and 26 weeks on weekly. The page lists the
exact rules for whichever timeframe you are viewing under "How each zone is decided".

## Set it up on GitHub (free, runs by itself)

1. Create a free account at github.com, then a new **public** repository
   (for example `nse-sector-radar`). Public repos get free Actions minutes and Pages.
2. Upload every file in this folder, keeping the folder structure
   (including `.github/workflows/update.yml`). The web "Add file > Upload files"
   button works; drag the whole folder in.
3. Settings > Pages: Source = "Deploy from a branch", Branch = `main`, folder = `/docs`. Save.
4. Actions tab: enable workflows if asked. Open "Update dashboard" > "Run workflow",
   tick **Refresh fundamentals**, and run it. The first run takes about an hour
   because it fetches fundamentals for every stock.
5. Your page is at `https://<your-username>.github.io/nse-sector-radar/`.
   Bookmark it on your phone.

After that it updates on its own: prices, RRG and news every weekday at 5:15 PM IST,
fundamentals every Saturday morning.

## Run it on a computer instead

    pip install -r requirements.txt
    python run.py --fundamentals     # first time
    python run.py                    # daily
    python run.py --demo             # test with fake data, no internet

Then open `docs/index.html` (sectors) or `docs/zones.html` (zones).

## Fixing a sector

Add a line to `data/sector_overrides.csv` (`SYMBOL,Sector`). Use NSE's industry
names so it groups correctly: Chemicals, Capital Goods, Healthcare, Financial Services,
Information Technology, Automobile and Auto Components, Fast Moving Consumer Goods,
Metals & Mining, Oil Gas & Consumable Fuels, Power, Realty, Construction,
Construction Materials, Consumer Durables, Consumer Services, Textiles,
Telecommunication, Media Entertainment & Publication, Services, Forest Materials, Diversified.

## How sectors are assigned

1. Your overrides file
2. NSE's official industry from the NIFTY Total Market / 500 / Microcap lists (~750 stocks)
3. Yahoo's sector and industry, mapped to NSE names (the rest)

The detailed industry (for example "Specialty Chemicals" vs "Agricultural Inputs")
shows under each stock name once fundamentals have been fetched.

## Settings

`src/config.py`: benchmark (NIFTY 50 or NIFTY 500), liquidity filter for the RRG
(default Rs 1 crore average daily turnover), RRG window and tail lengths.

## Known limits

- Free data. Yahoo occasionally rate-limits; the run retries and the next run fills gaps.
  NSE sometimes blocks cloud servers; cached lists are used when that happens.
- Small-cap fundamentals on Yahoo can be missing or stale.
- The RRG uses an open approximation of the JdK formula, so values will not match
  paid tools exactly, though quadrant and direction usually agree.
- Research tool only, not investment advice.
