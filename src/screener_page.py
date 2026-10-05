"""Renders the Screener tab: build your own screens from 65 conditions on
daily and weekly charts, combine them with ALL / ANY, add filters, save them.

Writes docs/screener.html, docs/screener.json (all stocks + their current
conditions) and docs/screener_meta.json (condition names + preset screens,
also used by the stock pop-up).
"""
import json
from datetime import datetime, timedelta, timezone

from .config import DOCS, SCREENER_EVENT_BARS
from .signals import META

PRESETS = [
    {"name": "Golden cross with RS 70+", "mode": "all", "conds": [{"tf": "d", "id": "gc", "n": 10}], "f": {"rs": 70}},
    {"name": "52-week high on volume", "mode": "all", "conds": [{"tf": "d", "id": "hi52", "n": 3}, {"tf": "d", "id": "vol2x_up", "n": 3}], "f": {}},
    {"name": "Fibonacci 61.8% bounce in an uptrend", "mode": "all", "conds": [{"tf": "d", "id": "fib618", "n": 5}, {"tf": "w", "id": "ab50", "n": 1}], "f": {}},
    {"name": "Weekly breakout, daily RSI 50–70", "mode": "all", "conds": [{"tf": "w", "id": "lv_brk", "n": 1}, {"tf": "d", "id": "rsi_50_70", "n": 1}], "f": {}},
    {"name": "Bullish divergence after a fall", "mode": "all", "conds": [{"tf": "d", "id": "bull_div", "n": 10}], "f": {}},
    {"name": "Tight base near 52-week highs", "mode": "all", "conds": [{"tf": "d", "id": "tight10", "n": 1}, {"tf": "d", "id": "near52", "n": 1}, {"tf": "d", "id": "up200", "n": 1}], "f": {}},
    {"name": "Weekly SuperTrend turned bullish", "mode": "all", "conds": [{"tf": "w", "id": "st_flip", "n": 3}, {"tf": "w", "id": "macd_ab0", "n": 1}], "f": {}},
    {"name": "Weekly cloud breakout", "mode": "all", "conds": [{"tf": "w", "id": "cloud_x", "n": 3}], "f": {"rs": 50}},
    {"name": "Bullish candle at support", "mode": "all", "conds": [{"tf": "d", "id": "lv_sup", "n": 1}, {"tf": "d", "id": "engulf", "n": 3}], "f": {}},
    {"name": "Any bullish reversal candle (weekly)", "mode": "any", "conds": [{"tf": "w", "id": "hammer", "n": 2}, {"tf": "w", "id": "engulf", "n": 2}, {"tf": "w", "id": "mstar", "n": 2}, {"tf": "w", "id": "piercing", "n": 2}], "f": {}},
]


def render(rows, sig):
    """rows: list of dicts per stock; sig: {"d": {sym: {...}}, "w": {...}}."""
    DOCS.mkdir(parents=True, exist_ok=True)
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    meta = {"conds": [{"id": i, "g": g, "l": l, "k": k} for i, g, l, k in META],
            "presets": PRESETS, "nb": SCREENER_EVENT_BARS}
    dump = lambda o: json.dumps(o, separators=(",", ":"), allow_nan=False)
    (DOCS / "screener_meta.json").write_text(dump(meta), encoding="utf-8")
    cols = ["sym", "name", "sector", "liquid", "price", "r1d", "r1m", "r3m", "rs", "zd", "zw", "bucket", "q", "hi", "es"]
    data = {"generated": ist.strftime("%d %b %Y, %I:%M %p IST"), "cols": cols,
            "rows": [[r.get(c) for c in cols] for r in rows],
            "sig": {tf: [sig[tf].get(r["sym"], {}) for r in rows] for tf in ("d", "w")}}
    (DOCS / "screener.json").write_text(dump(data), encoding="utf-8")
    (DOCS / "screener.html").write_text(TEMPLATE, encoding="utf-8")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Screener</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧭</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#EEF2F6;--panel:#FFFFFF;--ink:#16243A;--muted:#5C6B80;--line:#D3DBE5;--up:#1E8F5A;--down:#C2453B;--warn:#C9780F;--focus:#2F62C8;
  --font:"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#111925;--panel:#18222F;--ink:#E5EBF3;--muted:#93A1B4;--line:#2A3646;--up:#3FBF85;--down:#E9675C;--warn:#E5A040;--focus:#6E97F0}}
:root[data-theme="dark"]{--bg:#111925;--panel:#18222F;--ink:#E5EBF3;--muted:#93A1B4;--line:#2A3646;--up:#3FBF85;--down:#E9675C;--warn:#E5A040;--focus:#6E97F0}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--font);font-variant-numeric:tabular-nums;-webkit-text-size-adjust:100%}
.wrap{max-width:1180px;margin:0 auto;padding:16px 14px 48px}
header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:6px 16px;margin-bottom:6px}
h1{font-size:1.55rem;font-weight:700;margin:0}
nav{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.9rem}nav a{color:var(--muted);text-decoration:none}nav a[aria-current]{color:var(--ink);font-weight:600}
.stamp{color:var(--muted);font-size:.85rem;margin:0 0 14px}
h2{font-size:1.1rem;margin:0 0 4px;font-weight:600}
.sub{color:var(--muted);font-size:.85rem;margin:0 0 12px;max-width:80ch}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:16px}
select,input{font:inherit;font-size:.86rem;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 9px;max-width:100%;min-width:0}
input[type=number]{width:90px}
button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.btn{font:600 .84rem var(--font);border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:8px;padding:6px 12px;cursor:pointer}
.btn.pri{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.conds{display:grid;gap:8px;margin:10px 0}
.cond{display:grid;grid-template-columns:auto minmax(0,1fr) auto auto;gap:8px;align-items:center;border:1px solid var(--line);border-radius:10px;padding:8px}
@media(max-width:600px){.cond{grid-template-columns:auto minmax(0,1fr) auto}.cond .within{grid-column:2}}
.cond select.c{width:100%}
.x{font:700 1rem var(--font);background:transparent;border:0;color:var(--muted);cursor:pointer;padding:4px 8px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}
.seg button{border:0;background:transparent;color:var(--muted);font:500 .84rem var(--font);padding:5px 12px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
.filters{display:grid;gap:10px;grid-template-columns:repeat(2,minmax(0,1fr));margin-top:10px}
@media(min-width:760px){.filters{grid-template-columns:repeat(4,minmax(0,1fr))}}
.filters label{font-size:.76rem;color:var(--muted);display:flex;flex-direction:column;gap:3px}
.filters label.tog{flex-direction:row;align-items:center;gap:6px;font-size:.85rem}
.saved{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.saved span{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;padding:2px 4px 2px 10px;font-size:.82rem}
.saved button{all:unset;cursor:pointer;padding:0 6px;color:var(--muted)}
.saved button.ld{color:var(--ink);font-weight:600;padding-left:0}
.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{padding:8px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line);vertical-align:top}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--panel);z-index:1}
td.l,th.l{text-align:left}
th{color:var(--muted);font-weight:500;cursor:pointer;user-select:none;background:var(--panel)}
th[aria-sort]::after{content:" ↓";font-size:.75em}th[aria-sort="ascending"]::after{content:" ↑"}
.name small{display:block;color:var(--muted);font-size:.75rem;max-width:170px;overflow:hidden;text-overflow:ellipsis}
button.psym{all:unset;font-weight:700;cursor:pointer;border-bottom:1px dotted currentColor}
.lk a{font-size:.72rem;font-weight:600;color:var(--focus);text-decoration:none;border:1px solid currentColor;border-radius:6px;padding:0 5px;margin-left:6px}
.chip{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.74rem;font-weight:600;color:#fff;background:var(--c);white-space:nowrap}
.hits{display:flex;flex-wrap:wrap;gap:4px;white-space:normal;max-width:340px}
.hit{font-size:.74rem;border:1px solid var(--line);border-radius:6px;padding:1px 6px}
.up{color:var(--up)}.down{color:var(--down)}.mut{color:var(--muted)}
.count{font-size:1.4rem;font-weight:700}
.more{margin-top:10px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Screener</h1>
  <div id="gsearch"></div>
  <nav aria-label="Dashboards"><a href="index.html">Sector rotation</a><a href="zones.html">Zones</a><a href="levels.html">Levels</a><a href="setups.html">Setups</a><a href="screener.html" aria-current="page">Screener</a><a href="watchlist.html">My list</a><a href="backtest.html">Backtest</a></nav>
</header>
<p class="stamp" id="gen">Loading stocks…</p>

<section class="panel" aria-labelledby="h-build">
  <div class="row" style="justify-content:space-between">
    <h2 id="h-build" style="margin:0">Build a screen</h2>
    <div class="row">
      <select id="preset" aria-label="Load a ready-made screen"><option value="">Ready-made screens…</option></select>
      <button class="btn" id="clear">Clear</button>
    </div>
  </div>
  <div class="row" style="margin-top:10px">
    <span class="sub" style="margin:0">Match</span>
    <div class="seg" role="group" aria-label="Match mode"><button data-m="all" aria-pressed="true">All conditions</button><button data-m="any" aria-pressed="false">Any condition</button></div>
  </div>
  <div class="conds" id="conds"></div>
  <button class="btn" id="add">+ Add condition</button>
  <div class="filters">
    <label>Weekly zone<select id="f-zw"></select></label>
    <label>Daily zone<select id="f-zd"></select></label>
    <label>Setup group<select id="f-bk"><option value="">Any</option><option>Ready</option><option>Setting up</option><option>Watchlist</option><option>Avoid</option></select></label>
    <label>Minimum RS rank<select id="f-rs"><option value="0">Any</option><option>50</option><option>70</option><option>80</option><option>90</option></select></label>
    <label>Sector<select id="f-sec"></select></label>
    <label>Sector on weekly RRG<select id="f-q"><option value="">Any</option><option value="LI">Leading or Improving</option><option>Leading</option><option>Improving</option><option>Weakening</option><option>Lagging</option></select></label>
    <label>Price from ₹<input type="number" id="f-pmin" min="0" inputmode="decimal"></label>
    <label>Price to ₹<input type="number" id="f-pmax" min="0" inputmode="decimal"></label>
    <label class="tog"><input type="checkbox" id="f-liq" checked> Liquid only</label>
    <label class="tog"><input type="checkbox" id="f-es"> Hide results within 2 weeks</label>
  </div>
  <div class="row" style="margin-top:14px">
    <input type="text" id="sname" placeholder="Name this screen" aria-label="Screen name" style="flex:1 1 200px">
    <button class="btn pri" id="save">Save screen</button>
  </div>
  <div class="saved" id="saved"></div>
</section>

<section class="panel" aria-labelledby="h-res">
  <div class="row" style="justify-content:space-between"><h2 id="h-res" style="margin:0"><span class="count" id="cnt">0</span> stocks match</h2><span class="sub" style="margin:0">Tap a column to sort</span></div>
  <div class="tbl" style="margin-top:8px"><table id="t"></table></div>
  <button class="btn more" id="more" hidden></button>
</section>

<section class="panel">
  <h2>How it works</h2>
  <ul class="sub" style="padding-left:18px">
    <li>Every evening each stock is checked against 65 conditions on daily and weekly bars. Crossovers, patterns and new highs are remembered for the last 10 bars, so you can ask for "within 3 bars" and so on.</li>
    <li>Each condition has its own timeframe, so one screen can mix weekly and daily, for example a weekly breakout with daily RSI 50–70.</li>
    <li>Saved screens are stored on this device and are included in the My list backup. Any stock's pop-up shows which conditions it meets and which of your saved screens it matches.</li>
    <li>Weekly bars include the week in progress. End-of-day data. For research only, not investment advice.</li>
  </ul>
</section>
</div>
<script src="profile.js"></script>
<script>
const SCR = window.AZH_SCR, WL = window.AZH_WL;
const esc = s => String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v,d=1) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const pc = (v,d=1) => v==null ? '<span class="mut">–</span>' : `<span class="${v>0?'up':v<0?'down':''}">${v>0?'+':''}${fmt(v,d)}%</span>`;
const tv = s => "https://www.tradingview.com/chart/?symbol=" + encodeURIComponent("NSE:" + s.replace(/[&-]/g,"_")) + "&interval=W";
const scr = s => "https://www.screener.in/company/" + encodeURIComponent(s) + "/";
const ZONES = ["Bearish","Oversold","Accumulation","Bullish","Strong momentum","Extended","Divergence zone","Overbought","Danger zone","Neutral"];
const ZC = {"Bearish":"#C2453B","Oversold":"#6B4BB8","Accumulation":"#2F62C8","Bullish":"#1E8F5A","Strong momentum":"#13857A","Extended":"#0B6B4B","Divergence zone":"#A8285E","Overbought":"#C9780F","Danger zone":"#A8285E","Neutral":"#8C99AB"};
let META, DATA, ROWS = [], screen = SCR.blank(), sort = {k:"rs",dir:-1}, showAll = false;

Promise.all([SCR.meta(), fetch("screener.json").then(r=>r.json())]).then(([m, d])=>{
  META = m; DATA = d;
  ROWS = d.rows.map((r,i)=>{ const o = Object.fromEntries(d.cols.map((c,j)=>[c,r[j]])); o.sig = {d:d.sig.d[i], w:d.sig.w[i]}; return o; });
  document.getElementById("gen").textContent = `Updated ${d.generated}. ${ROWS.length.toLocaleString("en-IN")} stocks.`;
  const zs = [...new Set(ROWS.flatMap(r=>[r.zd,r.zw]).filter(Boolean))];
  const zopts = `<option value="">Any</option>` + ZONES.filter(z=>zs.includes(z)).map(z=>`<option>${z}</option>`).join("");
  document.getElementById("f-zw").innerHTML = zopts; document.getElementById("f-zd").innerHTML = zopts;
  document.getElementById("f-sec").innerHTML = `<option value="">All</option>` + [...new Set(ROWS.map(r=>r.sector))].sort().map(s=>`<option>${esc(s)}</option>`).join("");
  document.getElementById("preset").innerHTML += META.presets.map((p,i)=>`<option value="${i}">${esc(p.name)}</option>`).join("");
  const hash = decodeURIComponent((location.hash.match(/^#screen=(.+)$/)||[])[1]||"");
  const saved = WL.get().screens || [];
  if (hash && saved.find(s=>s.name===hash)) load(saved.find(s=>s.name===hash)); else load(META.presets[1]);
  drawSaved();
});

function condRow(c, i){
  const groups = [...new Set(META.conds.map(x=>x.g))];
  const opts = groups.map(g=>`<optgroup label="${esc(g)}">${META.conds.filter(x=>x.g===g).map(x=>`<option value="${x.id}" ${x.id===c.id?"selected":""}>${esc(x.l)}</option>`).join("")}</optgroup>`).join("");
  const kind = (META.conds.find(x=>x.id===c.id)||{}).k;
  return `<div class="cond" data-i="${i}">
    <div class="seg" role="group" aria-label="Timeframe"><button data-tf="d" aria-pressed="${c.tf==="d"}">D</button><button data-tf="w" aria-pressed="${c.tf==="w"}">W</button></div>
    <select class="c" aria-label="Condition">${opts}</select>
    ${kind==="e" ? `<select class="within" aria-label="How recent"><option value="1" ${c.n==1?"selected":""}>last bar</option><option value="3" ${c.n==3?"selected":""}>within 3 bars</option><option value="5" ${c.n==5?"selected":""}>within 5 bars</option><option value="10" ${c.n==10?"selected":""}>within 10 bars</option></select>` : `<span class="within mut" style="font-size:.8rem">now</span>`}
    <button class="x" aria-label="Remove condition">×</button></div>`;
}
function drawConds(){
  const box = document.getElementById("conds");
  box.innerHTML = screen.conds.map(condRow).join("") || `<p class="sub" style="margin:0">No conditions: only the filters below apply.</p>`;
  box.querySelectorAll(".cond").forEach(el=>{ const i = +el.dataset.i;
    el.querySelectorAll("[data-tf]").forEach(b=>b.onclick=()=>{ screen.conds[i].tf = b.dataset.tf; drawConds(); run(); });
    el.querySelector("select.c").onchange = e => { screen.conds[i].id = e.target.value; screen.conds[i].n = screen.conds[i].n || 3; drawConds(); run(); };
    const w = el.querySelector("select.within"); if (w) w.onchange = e => { screen.conds[i].n = +e.target.value; run(); };
    el.querySelector(".x").onclick = () => { screen.conds.splice(i,1); drawConds(); run(); }; });
  document.querySelectorAll("[data-m]").forEach(b=>b.setAttribute("aria-pressed", b.dataset.m===screen.mode));
}
const F = {zw:"f-zw", zd:"f-zd", bk:"f-bk", rs:"f-rs", sec:"f-sec", q:"f-q", pmin:"f-pmin", pmax:"f-pmax"};
function readFilters(){ const f = {};
  for (const [k,id] of Object.entries(F)){ const v = document.getElementById(id).value; if (v!=="" && v!=="0") f[k] = ["rs","pmin","pmax"].includes(k) ? +v : v; }
  f.liq = document.getElementById("f-liq").checked; f.es = document.getElementById("f-es").checked; return f; }
function writeFilters(f){ f = f||{};
  for (const [k,id] of Object.entries(F)) document.getElementById(id).value = f[k] ?? (k==="rs"?"0":"");
  document.getElementById("f-liq").checked = f.liq !== false; document.getElementById("f-es").checked = !!f.es; }
function load(s){ screen = JSON.parse(JSON.stringify(s)); screen.mode = screen.mode || "all"; screen.conds = screen.conds || [];
  writeFilters(screen.f); document.getElementById("sname").value = s.name && !META.presets.includes(s) ? s.name : ""; drawConds(); run(); }

function run(){
  screen.f = readFilters();
  const L = ROWS.map(r=>({r, hits: SCR.hits(screen, r)})).filter(x=>x.hits);
  const key = (x,k) => k==="hits" ? x.hits.length : x.r[k];
  L.sort((a,b)=>{ const x=key(a,sort.k), y=key(b,sort.k); if (x==null) return 1; if (y==null) return -1; return (typeof x==="string"?x.localeCompare(y):x-y)*sort.dir; });
  document.getElementById("cnt").textContent = L.length.toLocaleString("en-IN");
  const LIM = 150, S = showAll ? L : L.slice(0, LIM), t = document.getElementById("t");
  const COLS = [["sym","Stock"],["price","Price"],["r1d","1D"],["r1m","1M"],["rs","RS"],["zw","Weekly zone"],["bucket","Setup"],["hits","Matched"]];
  t.innerHTML = `<thead><tr>${COLS.map(([k,l])=>`<th class="${["sym","zw","bucket","hits"].includes(k)?'l':''}" data-k="${k}" ${sort.k===k?`aria-sort="${sort.dir>0?'ascending':'descending'}"`:''}>${l}</th>`).join("")}</tr></thead><tbody>${
    S.map(({r,hits})=>`<tr><td class="name"><button class="psym" data-p="${esc(r.sym)}">${esc(r.sym)}</button><span class="lk"><a href="${tv(r.sym)}" target="_blank" rel="noopener">Chart</a><a href="${scr(r.sym)}" target="_blank" rel="noopener">Screener</a></span><small>${esc(r.sector)}</small>${r.es?'<small style="color:var(--warn)">⚠ results soon</small>':""}</td>
      <td>${fmt(r.price,2)}</td><td>${pc(r.r1d,2)}</td><td>${pc(r.r1m)}</td><td>${r.rs??"–"}</td>
      <td class="l">${r.zw?`<span class="chip" style="--c:${ZC[r.zw]||'#8C99AB'}">${esc(r.zw)}</span>`:"–"}</td>
      <td class="l">${esc(r.bucket||"–")}</td>
      <td class="l"><div class="hits">${hits.map(h=>`<span class="hit">${esc(h)}</span>`).join("")}</div></td></tr>`).join("")
    || `<tr><td colspan="${COLS.length}" class="mut">No stocks match. Loosen a condition, widen "within", or untick Liquid only.</td></tr>`}</tbody>`;
  t.querySelectorAll("th").forEach(th=>th.onclick=()=>{ const k=th.dataset.k; sort.dir = sort.k===k ? -sort.dir : (["sym","zw","bucket"].includes(k)?1:-1); sort.k=k; run(); });
  const m = document.getElementById("more"); m.hidden = showAll || L.length<=LIM; m.textContent = `Show all ${L.length}`;
}
function drawSaved(){
  const list = WL.get().screens || [];
  document.getElementById("saved").innerHTML = list.length ? list.map((s,i)=>`<span><button class="ld" data-l="${i}">${esc(s.name)}</button><button data-d="${i}" aria-label="Delete ${esc(s.name)}">×</button></span>`).join("") : `<span class="mut" style="border:0;padding:0">No saved screens yet.</span>`;
  document.querySelectorAll("[data-l]").forEach(b=>b.onclick=()=>load(list[+b.dataset.l]));
  document.querySelectorAll("[data-d]").forEach(b=>b.onclick=()=>{ if (!confirm(`Delete "${list[+b.dataset.d].name}"?`)) return; const d = WL.get(); d.screens.splice(+b.dataset.d,1); WL.save(d); drawSaved(); });
}
document.getElementById("add").onclick = () => { screen.conds.push({tf:"d", id:"rsi_x50", n:3}); drawConds(); run(); };
document.getElementById("clear").onclick = () => load(SCR.blank());
document.getElementById("preset").onchange = e => { if (e.target.value!=="") load(META.presets[+e.target.value]); e.target.value = ""; };
document.querySelectorAll("[data-m]").forEach(b=>b.onclick=()=>{ screen.mode = b.dataset.m; drawConds(); run(); });
Object.values(F).concat(["f-liq","f-es"]).forEach(id=>document.getElementById(id).addEventListener("change", ()=>{ showAll=false; run(); }));
document.getElementById("more").onclick = () => { showAll = true; run(); };
document.getElementById("save").onclick = () => { const name = document.getElementById("sname").value.trim();
  if (!name){ document.getElementById("sname").focus(); return; }
  const d = WL.get(); d.screens = d.screens || []; screen.f = readFilters();
  const rec = {name, mode:screen.mode, conds:screen.conds, f:screen.f}, i = d.screens.findIndex(s=>s.name===name);
  if (i>=0) d.screens[i] = rec; else d.screens.push(rec); WL.save(d); drawSaved(); };
</script>
</body>
</html>
"""
