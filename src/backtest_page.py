"""Renders the backtest page. Output goes to data/cache/site_backtest/ and is
copied into docs/ on every run, so the page survives between weekly backtests."""
import json
import shutil
from datetime import datetime, timedelta, timezone

from .config import CACHE, DOCS

OUT = CACHE / "site_backtest"
COLS = ["sym", "sec", "in", "out", "pi", "po", "ret", "wk", "peak", "why", "best", "nifty", "open"]


def render(payload):
    OUT.mkdir(parents=True, exist_ok=True)
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    payload["generated"] = ist.strftime("%d %b %Y, %I:%M %p IST")
    trades = payload.pop("trades")
    dump = lambda o: json.dumps(o, separators=(",", ":"), allow_nan=False, default=str)
    for key, rows in trades.items():
        (OUT / f"bt_{key}.json").write_text(dump({"cols": COLS, "rows": [[r.get(c) for c in COLS] for r in rows]}), encoding="utf-8")
    (OUT / "backtest.html").write_text(TEMPLATE.replace("__DATA__", dump(payload).replace("</", "<\\/")), encoding="utf-8")


def publish():
    """Copy the last backtest (if any) into docs/."""
    if OUT.exists():
        for f in OUT.iterdir():
            shutil.copy2(f, DOCS / f.name)


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Zone strategy backtest</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧭</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#EEF2F6;--panel:#FFFFFF;--ink:#16243A;--muted:#5C6B80;--line:#D3DBE5;--up:#1E8F5A;--down:#C2453B;--focus:#2F62C8;
  --z-acc:#2F62C8;--z-bull:#1E8F5A;--z-ob:#13857A;--z-dang:#0B6B4B;
  --font:"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#111925;--panel:#18222F;--ink:#E5EBF3;--muted:#93A1B4;--line:#2A3646;--up:#3FBF85;--down:#E9675C;--focus:#6E97F0;
  --z-acc:#6E97F0;--z-bull:#3FBF85;--z-ob:#3BB8AA;--z-dang:#5CC79A}}
:root[data-theme="dark"]{--bg:#111925;--panel:#18222F;--ink:#E5EBF3;--muted:#93A1B4;--line:#2A3646;--up:#3FBF85;--down:#E9675C;--focus:#6E97F0;
  --z-acc:#6E97F0;--z-bull:#3FBF85;--z-ob:#3BB8AA;--z-dang:#5CC79A}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--font);font-variant-numeric:tabular-nums;-webkit-text-size-adjust:100%}
.wrap{max-width:1180px;margin:0 auto;padding:16px 14px 48px}
header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:6px 16px;margin-bottom:6px}
h1{font-size:1.55rem;font-weight:700;margin:0}
nav{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.9rem}nav a{color:var(--muted);text-decoration:none}nav a[aria-current]{color:var(--ink);font-weight:600}
.stamp{color:var(--muted);font-size:.85rem;margin:0 0 14px}
h2{font-size:1.1rem;margin:0 0 4px;font-weight:600}h3{font-size:.95rem;margin:16px 0 8px}
.sub{color:var(--muted);font-size:.85rem;margin:0 0 12px;max-width:80ch}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:16px}
.flow{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:4px 0 10px}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;font-size:.78rem;font-weight:600;color:#fff;background:var(--c)}
.arrow{color:var(--muted)}
.rules{display:grid;gap:8px;grid-template-columns:minmax(0,1fr);font-size:.88rem}
@media(min-width:760px){.rules{grid-template-columns:repeat(3,minmax(0,1fr))}}
.rules div{border:1px solid var(--line);border-radius:10px;padding:10px 12px}.rules b{display:block;margin-bottom:3px}
.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{padding:7px 8px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--panel);z-index:1}
td.l,th.l{text-align:left}
th{color:var(--muted);font-weight:500;background:var(--panel)}
th.s{cursor:pointer;user-select:none}th[aria-sort]::after{content:" ↓";font-size:.75em}th[aria-sort="ascending"]::after{content:" ↑"}
#vt tbody tr{cursor:pointer}#vt tbody tr:hover td{background:color-mix(in srgb,var(--line) 35%,var(--panel))}
tr.on td{background:color-mix(in srgb,var(--focus) 12%,var(--panel))!important}
.best{font-size:.7rem;font-weight:700;color:var(--up);border:1px solid currentColor;border-radius:6px;padding:0 5px;margin-left:6px}
.up{color:var(--up)}.down{color:var(--down)}.mut{color:var(--muted)}
.kpis{display:grid;gap:10px;grid-template-columns:repeat(2,minmax(0,1fr))}
@media(min-width:760px){.kpis{grid-template-columns:repeat(6,minmax(0,1fr))}}
.kpi{border:1px solid var(--line);border-radius:12px;padding:10px 12px}.kpi>span{display:block;color:var(--muted);font-size:.76rem}.kpi b{font-size:1.3rem}
.grid2{display:grid;gap:16px;grid-template-columns:minmax(0,1fr)}
@media(min-width:900px){.grid2{grid-template-columns:repeat(2,minmax(0,1fr))}}
.bars{display:grid;gap:5px}.bar{display:grid;grid-template-columns:96px 1fr 44px;gap:8px;align-items:center;font-size:.8rem}
.bar i{display:block;height:14px;border-radius:3px;background:var(--c)}
.bar span:last-child{text-align:right;color:var(--muted)}
.tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px}
select,input[type=search]{font:inherit;font-size:.86rem;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 9px;max-width:100%}
label.tog{font-size:.85rem;color:var(--muted);display:flex;gap:6px;align-items:center}
button:focus-visible,select:focus-visible,input:focus-visible,tr:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.more{margin-top:10px;font:500 .85rem var(--font);background:transparent;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:6px 12px;cursor:pointer}
.lk a{font-size:.72rem;font-weight:600;color:var(--focus);text-decoration:none;border:1px solid currentColor;border-radius:6px;padding:0 5px;margin-left:6px}
.name small{display:block;color:var(--muted);font-size:.75rem;max-width:170px;overflow:hidden;text-overflow:ellipsis}
.note{color:var(--muted);font-size:.8rem;max-width:80ch}
.note li{margin-bottom:4px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Zone strategy backtest</h1>
  <div id="gsearch"></div>
  <nav aria-label="Dashboards"><a href="index.html">Sector rotation</a><a href="zones.html">Zones</a><a href="levels.html">Levels</a><a href="setups.html">Setups</a><a href="watchlist.html">My list</a><a href="backtest.html" aria-current="page">Backtest</a></nav>
</header>
<p class="stamp" id="gen"></p>

<section class="panel">
  <h2>The strategy, on weekly charts</h2>
  <div class="flow"><span class="chip" style="--c:var(--z-acc)">Accumulation</span><span class="arrow">→</span><span class="chip" style="--c:var(--z-bull)">Bullish</span><b>buy</b><span class="arrow">→</span><span class="chip" style="--c:var(--z-ob)">Strong momentum</span><span class="arrow">→</span><span class="chip" style="--c:var(--z-dang)">Extended</span><span class="arrow">→</span><b>sell when Extended ends or divergence appears</b></div>
  <div class="rules">
    <div><b>Entry</b>The week a stock moves from Accumulation to Bullish, at that week's close. It must have been liquid at the time.</div>
    <div><b>Exit when it cools</b>The week it leaves Extended, in any direction, or enters the Divergence zone (price higher high, RSI or MACD lower high). The Extended RSI floor (55, 60 or 65) decides how soon Extended ends.</div>
    <div><b>Exit when it fails</b>It drops to Neutral, Bearish, Oversold or Accumulation before reaching Extended. In the "exit" variant, it also sells if Strong momentum slips back to Bullish.</div>
  </div>
</section>

<section class="panel">
  <h2>Six variants compared</h2>
  <p class="sub" id="vsub"></p>
  <div class="tbl"><table id="vt"></table></div>
</section>

<section class="panel" id="detail">
  <h2 id="dh"></h2>
  <p class="sub">Closed trades only, after costs. Open trades are listed further down.</p>
  <div class="kpis" id="kpis"></div>
  <div class="grid2">
    <div><h3>How returns were spread</h3><div class="bars" id="hist"></div></div>
    <div><h3>By how far the trend ran</h3><div class="tbl"><table id="peaks"></table></div>
      <h3>Why trades ended</h3><div class="tbl"><table id="why"></table></div></div>
  </div>
  <div class="grid2">
    <div><h3>By entry year</h3><div class="tbl"><table id="yr"></table></div></div>
    <div><h3>By sector</h3><div class="tbl"><table id="sec"></table></div></div>
  </div>
</section>

<section class="panel" id="trades">
  <h2>Trades</h2>
  <p class="sub" id="tsub"></p>
  <div class="tools">
    <select id="f-st" aria-label="Status"><option value="closed">Closed trades</option><option value="open">Open now (still holding)</option><option value="all">All</option></select>
    <select id="f-peak" aria-label="Furthest zone reached"><option value="">Any furthest zone</option><option>Bullish</option><option>Strong momentum</option><option>Extended</option></select>
    <select id="f-sec" aria-label="Sector"></select>
    <input type="search" id="q" placeholder="Find a stock" aria-label="Find a stock">
  </div>
  <div class="tbl"><table id="tt"></table></div>
  <button class="more" id="more" hidden></button>
</section>

<section class="panel">
  <h2>Read this before trusting the numbers</h2>
  <ul class="note">
    <li><b>Survivorship bias.</b> Only stocks listed today are tested. Companies that were delisted or went bust are missing, which flatters the results a little.</li>
    <li><b>The test window is short.</b> About 80 weeks are used to warm up the indicators, so trades start roughly 18 months into the downloaded history. Check the "By entry year" table to see whether results hold up across different market conditions.</li>
    <li><b>Prices are weekly closes.</b> Real fills on Monday's open can differ, especially for small caps after a strong week.</li>
    <li><b>Trades overlap.</b> Averages describe a typical trade, not a portfolio. Holding many positions at once has different risk.</li>
    <li>For research only. Past results do not predict future returns.</li>
  </ul>
</section>
</div>

<script>
const D = __DATA__;
const esc = s => String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v,d=1) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const pc = (v,d=1) => v==null ? `<span class="mut">–</span>` : `<span class="${v>0?'up':v<0?'down':''}">${v>0?'+':''}${fmt(v,d)}%</span>`;
const dl = s => s ? new Date(s+"T00:00:00").toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"2-digit"}) : "";
const ZC = {"Bullish":"--z-bull","Strong momentum":"--z-ob","Extended":"--z-dang"};
const vname = v => `Extended floor ${v.floor} · ${v.v==="hold"?"hold through pullbacks":"exit if momentum falls back"}`;
const tv = s => "https://www.tradingview.com/chart/?symbol=" + encodeURIComponent("NSE:" + s.replace(/[&-]/g,"_")) + "&interval=W";
const scr = s => "https://www.screener.in/company/" + encodeURIComponent(s) + "/";

document.getElementById("gen").textContent = `Updated ${D.generated}. Weekly data ${dl(D.range[0])} to ${dl(D.range[1])}. Costs ${D.cfg.cost_pct}% per round trip.`;
const V = D.variants; let cur = null, T = null, tsort = {k:"in",dir:-1}, showAll = false;
const ok = V.filter(v=>v.n>=30);
const bestKey = ok.length ? ok.reduce((a,b)=>(b.avg??-1e9)>(a.avg??-1e9)?b:a).key : null;
document.getElementById("vsub").textContent = "Tap a row to see its details and trades. \"Best\" marks the highest average return per trade among variants with at least 30 trades; similar numbers mean the setting barely matters.";

function drawVariants(){
  const t = document.getElementById("vt");
  t.innerHTML = `<thead><tr><th>Variant</th><th>Trades</th><th>Win rate</th><th>Avg / trade</th><th>Median</th><th>Avg win</th><th>Avg loss</th><th>Profit factor</th><th>Avg weeks held</th><th>vs NIFTY</th><th>Reached Extended</th><th>Open now</th></tr></thead><tbody>${
    V.map(v=>`<tr data-k="${v.key}" class="${v.key===cur?'on':''}" tabindex="0"><td class="l">${esc(vname(v))}${v.key===bestKey?'<span class="best">Best</span>':''}</td>
      <td>${v.n}</td><td>${fmt(v.win)}%</td><td>${pc(v.avg,2)}</td><td>${pc(v.med,2)}</td><td>${pc(v.aw)}</td><td>${pc(v.al)}</td>
      <td>${fmt(v.pf,2)}</td><td>${fmt(v.wk)}</td><td>${pc(v.edge,2)}</td><td>${fmt(v.danger)}%</td><td>${v.open}</td></tr>`).join("")}</tbody>`;
  t.querySelectorAll("tbody tr").forEach(tr=>{ const go=()=>select(tr.dataset.k); tr.addEventListener("click",go); tr.addEventListener("keydown",e=>{ if(e.key==="Enter") go(); }); });
}
function small(rows, head, cell){ return `<thead><tr>${head.map((h,i)=>`<th class="${i?'':'l'}">${h}</th>`).join("")}</tr></thead><tbody>${rows.map(cell).join("")||`<tr><td class="mut" colspan="${head.length}">No trades</td></tr>`}</tbody>`; }
function select(key){
  cur = key; const v = V.find(x=>x.key===key); drawVariants(); showAll = false;
  document.getElementById("dh").textContent = vname(v);
  document.getElementById("kpis").innerHTML = [["Closed trades",v.n],["Win rate",fmt(v.win)+"%"],["Avg per trade",pc(v.avg,2)],["Avg weeks held",fmt(v.wk)],["Best trade",pc(v.best)],["Worst trade",pc(v.worst)]]
    .map(([k,x])=>`<div class="kpi"><span>${k}</span><b>${x}</b></div>`).join("");
  const mx = Math.max(1,...v.hist.map(h=>h.n));
  document.getElementById("hist").innerHTML = v.hist.map(h=>`<div class="bar"><span>${h.k}%</span><i style="width:${(h.n/mx*100).toFixed(1)}%;--c:${h.k.startsWith("<")||h.k.startsWith("−")?'var(--down)':'var(--up)'}"></i><span>${h.n}</span></div>`).join("");
  document.getElementById("peaks").innerHTML = small(Object.entries(v.peaks||{}), ["Furthest zone reached","Trades","Win rate","Avg"],
    ([k,p])=>`<tr><td class="l"><span class="chip" style="--c:var(${ZC[k]})">${k}</span></td><td>${p.n}</td><td>${p.win==null?'–':fmt(p.win)+'%'}</td><td>${pc(p.avg,2)}</td></tr>`);
  document.getElementById("why").innerHTML = small(Object.entries(v.reasons||{}).sort((a,b)=>b[1]-a[1]), ["Exit reason","Trades","Share"],
    ([k,n])=>`<tr><td class="l">${esc(k)}</td><td>${n}</td><td>${fmt(n/v.n*100)}%</td></tr>`);
  const row = r => `<tr><td class="l">${esc(r.k)}</td><td>${r.n}</td><td>${fmt(r.win)}%</td><td>${pc(r.avg,2)}</td><td>${pc(r.med,2)}</td></tr>`;
  document.getElementById("yr").innerHTML = small(v.year, ["Year","Trades","Win rate","Avg","Median"], row);
  document.getElementById("sec").innerHTML = small([...v.sector].sort((a,b)=>b.n-a.n), ["Sector","Trades","Win rate","Avg","Median"], row);
  T = null; drawTrades();
  fetch(`bt_${key}.json`).then(r=>r.json()).then(j=>{ if (cur!==key) return;
    T = j.rows.map(r=>Object.fromEntries(j.cols.map((c,i)=>[c,r[i]])));
    const fs = document.getElementById("f-sec"), keep = fs.value;
    fs.innerHTML = `<option value="">All sectors</option>` + [...new Set(T.map(x=>x.sec).filter(Boolean))].sort().map(s=>`<option>${esc(s)}</option>`).join("");
    fs.value = keep; drawTrades(); }).catch(()=>{ T = []; drawTrades(); });
}
const TC = [["sym","Stock"],["in","Entry"],["pi","Entry ₹"],["out","Exit"],["po","Exit ₹"],["ret","Return"],["wk","Weeks"],["peak","Furthest zone"],["best","Best %"],["nifty","NIFTY same period"],["why","Exit reason"]];
function drawTrades(){
  const t = document.getElementById("tt"), sub = document.getElementById("tsub");
  if (!T){ t.innerHTML = `<tbody><tr><td class="mut">Loading trades…</td></tr></tbody>`; return; }
  const st = document.getElementById("f-st").value, pk = document.getElementById("f-peak").value, sc = document.getElementById("f-sec").value, q = document.getElementById("q").value.trim().toUpperCase();
  let L = T.filter(x => (st==="all" || (st==="open") === !!x.open) && (!pk || x.peak===pk) && (!sc || x.sec===sc) && (!q || x.sym.includes(q)));
  L.sort((a,b)=>{ const x=a[tsort.k], y=b[tsort.k]; if(x==null) return 1; if(y==null) return -1; return (typeof x==="string"?x.localeCompare(y):x-y)*tsort.dir; });
  sub.textContent = st==="open" ? `${L.length} stocks are in a trade by these rules right now. Return is up to the latest weekly close.` : `${L.length} trades. Tap a column to sort.`;
  const LIM = 200, S = showAll ? L : L.slice(0, LIM);
  t.innerHTML = `<thead><tr>${TC.map(([k,l])=>`<th class="s ${k==="sym"||k==="peak"||k==="why"?'l':''}" data-k="${k}" ${tsort.k===k?`aria-sort="${tsort.dir>0?'ascending':'descending'}"`:''}>${l}</th>`).join("")}</tr></thead><tbody>${
    S.map(x=>`<tr><td class="name"><button class="psym" data-p="${esc(x.sym)}" style="all:unset;font-weight:700;cursor:pointer;border-bottom:1px dotted currentColor">${esc(x.sym)}</button><span class="lk"><a href="${tv(x.sym)}" target="_blank" rel="noopener">Chart</a><a href="${scr(x.sym)}" target="_blank" rel="noopener">Screener</a></span><small>${esc(x.sec||"")}</small></td>
      <td>${dl(x.in)}</td><td>${fmt(x.pi,2)}</td><td>${x.open?'<span class="mut">open</span>':dl(x.out)}</td><td>${fmt(x.po,2)}</td><td>${pc(x.ret)}</td><td>${x.wk}</td>
      <td class="l"><span class="chip" style="--c:var(${ZC[x.peak]})">${esc(x.peak)}</span></td><td>${pc(x.best)}</td><td>${pc(x.nifty)}</td><td class="l">${esc(x.open?"Still holding":x.why)}</td></tr>`).join("")
    || `<tr><td class="mut" colspan="${TC.length}">No trades match.</td></tr>`}</tbody>`;
  t.querySelectorAll("th.s").forEach(th=>th.addEventListener("click",()=>{ const k=th.dataset.k; tsort.dir = tsort.k===k ? -tsort.dir : (["sym","peak","why"].includes(k)?1:-1); tsort.k=k; drawTrades(); }));
  const m = document.getElementById("more"); m.hidden = showAll || L.length<=LIM; m.textContent = `Show all ${L.length}`;
}
["f-st","f-peak","f-sec"].forEach(id=>document.getElementById(id).addEventListener("change",()=>{ showAll=false; drawTrades(); }));
document.getElementById("q").addEventListener("input",()=>{ showAll=false; drawTrades(); });
document.getElementById("more").addEventListener("click",()=>{ showAll=true; drawTrades(); });
select(bestKey || (V[0] && V[0].key));
</script>
<script src="profile.js" defer></script>
</body>
</html>
"""
