"""Renders docs/zones.html: stocks sorted into six technical zones."""
import json
from datetime import datetime, timedelta, timezone

from .config import (ADX_TREND, CHOP_RANGE, CHOP_TRENDING, DOCS,
                     RSI_OVERBOUGHT, RSI_OVERSOLD, ZONE_PARAMS)


def render(payload):
    DOCS.mkdir(parents=True, exist_ok=True)
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    payload["generated"] = ist.strftime("%d %b %Y, %I:%M %p IST")
    payload["params"] = ZONE_PARAMS
    payload["th"] = {"ob": RSI_OVERBOUGHT, "os": RSI_OVERSOLD, "adx": ADX_TREND,
                     "cht": CHOP_TRENDING, "chr": CHOP_RANGE}
    blob = json.dumps(payload, separators=(",", ":"), allow_nan=False, default=str).replace("</", "<\\/")
    (DOCS / "zones.html").write_text(TEMPLATE.replace("__DATA__", blob), encoding="utf-8")
    return DOCS / "zones.html"


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>NSE technical zones</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧭</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#EEF2F6; --panel:#FFFFFF; --ink:#16243A; --muted:#5C6B80; --line:#D3DBE5; --up:#1E8F5A; --down:#C2453B; --focus:#2F62C8;
  --z-bear:#C2453B; --z-os:#6B4BB8; --z-acc:#2F62C8; --z-bull:#1E8F5A; --z-ob:#C9780F; --z-dang:#A8285E; --z-neu:#A3AFBF; --z-na:#E1E6ED;
  --font:"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  box-sizing:border-box; padding-top:env(safe-area-inset-top,0px); padding-bottom:env(safe-area-inset-bottom,0px);
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --bg:#111925; --panel:#18222F; --ink:#E5EBF3; --muted:#93A1B4; --line:#2A3646; --up:#3FBF85; --down:#E9675C; --focus:#6E97F0;
  --z-bear:#E9675C; --z-os:#9C82E6; --z-acc:#6E97F0; --z-bull:#3FBF85; --z-ob:#E5A040; --z-dang:#E0619A; --z-neu:#5E6B7C; --z-na:#263140;}}
:root[data-theme="dark"]{
  --bg:#111925; --panel:#18222F; --ink:#E5EBF3; --muted:#93A1B4; --line:#2A3646; --up:#3FBF85; --down:#E9675C; --focus:#6E97F0;
  --z-bear:#E9675C; --z-os:#9C82E6; --z-acc:#6E97F0; --z-bull:#3FBF85; --z-ob:#E5A040; --z-dang:#E0619A; --z-neu:#5E6B7C; --z-na:#263140;}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--font);font-variant-numeric:tabular-nums;-webkit-text-size-adjust:100%}
.wrap{max-width:1180px;margin:0 auto;padding:16px 14px 48px}
header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:6px 16px;margin-bottom:6px}
h1{font-size:1.55rem;font-weight:700;letter-spacing:-.01em;margin:0}
nav{display:flex;gap:14px;font-size:.9rem}
nav a{color:var(--muted);text-decoration:none}
nav a[aria-current]{color:var(--ink);font-weight:600}
.stamp{color:var(--muted);font-size:.85rem;margin:0 0 14px}
h2{font-size:1.1rem;margin:0 0 4px;font-weight:600}
.sub{color:var(--muted);font-size:.85rem;margin:0 0 12px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:16px}

/* the cycle: six zones in market order, bearish back round to danger */
.cycle{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;margin:0 0 16px;border-radius:14px;overflow:hidden;border:1px solid var(--line)}
@media(min-width:760px){.cycle{grid-template-columns:repeat(6,minmax(0,1fr))}}
.z{position:relative;border:0;text-align:left;font:inherit;color:#fff;padding:12px 12px 14px;cursor:pointer;background:var(--c);min-height:108px;
   display:flex;flex-direction:column;justify-content:space-between}
.z .n{font-size:1.8rem;font-weight:700;line-height:1}
.z .t{font-weight:600;font-size:.86rem;overflow-wrap:anywhere;hyphens:auto}
@media(min-width:760px){.z .t{font-size:.95rem}}
.z .s{font-size:.78rem;opacity:.9}
.z .k{font-size:.72rem;opacity:.8}
.z[aria-pressed="true"]{box-shadow:inset 0 0 0 3px var(--panel), inset 0 0 0 5px var(--c)}
.cycle.filtering .z[aria-pressed="false"]{filter:saturate(.35) brightness(1.05);opacity:.75}
.z:focus-visible{outline:3px solid var(--ink);outline-offset:-3px}

.seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:var(--panel)}
.seg button{border:0;background:transparent;color:var(--muted);font:500 .88rem var(--font);padding:7px 16px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
.chip{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.75rem;font-weight:600;color:#fff;background:var(--c)}
.days{display:grid;gap:14px}
.day h3{font-size:.88rem;margin:0 0 6px;font-weight:600}
.day h3 span{color:var(--muted);font-weight:400}
.ent{display:flex;flex-wrap:wrap;gap:6px}
.ent button{font:inherit;font-size:.8rem;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:8px;padding:4px 8px;cursor:pointer;display:flex;gap:6px;align-items:center}
.ent button i{width:8px;height:8px;border-radius:50%;background:var(--c);display:inline-block}
.ent button small{color:var(--muted)}
.empty{color:var(--muted);font-size:.88rem;padding:6px 0}

.tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px}
select,input[type=search]{font:inherit;font-size:.86rem;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 9px;min-width:0;max-width:100%}
label.tog{font-size:.85rem;color:var(--muted);display:flex;gap:6px;align-items:center}
button:focus-visible,select:focus-visible,input:focus-visible,tr:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{padding:7px 8px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--panel);z-index:1}
td.l,th.l{text-align:left}
th{color:var(--muted);font-weight:500;cursor:pointer;user-select:none;background:var(--panel)}
th[aria-sort]::after{content:" ↓";font-size:.75em} th[aria-sort="ascending"]::after{content:" ↑"}
.name small{display:block;color:var(--muted);font-size:.75rem;max-width:170px;overflow:hidden;text-overflow:ellipsis}
.up{color:var(--up)}.down{color:var(--down)}.mut{color:var(--muted)}
.strip{display:block}
tr.hl td{background:color-mix(in srgb,var(--focus) 12%,var(--panel))}
tr.gz td{background:color-mix(in srgb,var(--c) 10%,var(--panel));border-bottom:1px solid var(--line);padding:10px 8px}
tr.gs td{padding:0;background:var(--panel)}
tr.gz td,tr.gs td{text-align:left}
.gl{position:sticky;left:8px;display:inline-flex;gap:8px;align-items:center}
.gs button{font:inherit;font-size:.85rem;color:var(--ink);background:transparent;border:0;padding:8px 8px 8px 22px;cursor:pointer;display:inline-flex;gap:8px;align-items:center;position:sticky;left:0}
.gs button::before{content:"▸";color:var(--muted);transition:transform .15s}
.gs button[aria-expanded="true"]::before{transform:rotate(90deg)}
.gs button b{font-weight:600}
.gs button .cnt{color:var(--muted)}
@media (prefers-reduced-motion:reduce){.gs button::before{transition:none}}
.more{margin-top:10px;font:500 .85rem var(--font);background:transparent;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:6px 12px;cursor:pointer}
details{font-size:.88rem}
details summary{cursor:pointer;font-weight:600}
dl{display:grid;grid-template-columns:max-content 1fr;gap:6px 14px;margin:12px 0 0}
dt{font-weight:600} dd{margin:0;color:var(--muted);max-width:70ch}
.legend{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:.76rem;color:var(--muted);margin-top:8px}
.legend i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:4px;vertical-align:-1px;background:var(--c)}
.lk{white-space:nowrap}
.tv{font-size:.72rem;font-weight:600;color:var(--focus,var(--impr));text-decoration:none;border:1px solid currentColor;border-radius:6px;padding:0 5px;margin-left:6px;vertical-align:1px}
.tv:hover{background:color-mix(in srgb,currentColor 12%,transparent)}
.note{color:var(--muted);font-size:.78rem;margin-top:24px;max-width:72ch}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>NSE technical zones</h1>
  <nav aria-label="Dashboards"><a href="index.html">Sector rotation</a><a href="zones.html" aria-current="page">Zones</a></nav>
</header>
<div style="display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;justify-content:space-between;margin:0 0 14px">
  <p class="stamp" id="gen" style="margin:0"></p>
  <div class="tools" style="margin:0">
    <div class="seg" role="group" aria-label="Timeframe">
      <button data-tf="d" aria-pressed="true">Daily</button><button data-tf="w" aria-pressed="false">Weekly</button>
    </div>
    <label class="tog">Period <select id="period" aria-label="Period to show"></select></label>
  </div>
</div>

<div class="cycle" id="cycle" role="group" aria-label="Filter by zone"></div>

<section class="panel" aria-labelledby="h-new">
  <h2 id="h-new">New entries</h2>
  <p class="sub" id="new-sub"></p>
  <div class="days" id="days"></div>
</section>

<section class="panel" aria-labelledby="h-all" id="all">
  <h2 id="h-all">All stocks</h2>
  <p class="sub" id="all-sub"></p>
  <div class="tools">
    <select id="f-zone" aria-label="Zone"></select>
    <select id="f-sec" aria-label="Sector"></select>
    <select id="f-new" aria-label="Entered"></select>
    <input type="search" id="q" placeholder="Find a stock" aria-label="Find a stock">
    <label class="tog"><input type="checkbox" id="liq" checked> Liquid only</label>
    <label class="tog"><input type="checkbox" id="grp" checked> Group by where they came from</label>
  </div>
  <div class="tbl"><table id="t"></table></div>
  <button class="more" id="more" hidden></button>
  <div class="legend" id="legend"></div>
</section>

<section class="panel">
  <details>
    <summary>How each zone is decided</summary>
    <div id="rules"></div>
  </details>
</section>

<p class="note">Rule-based screening on daily data from Yahoo Finance. Zones describe what the indicators show today; they are not buy or sell signals. For research only, not investment advice.</p>
</div>

<script>
const D = __DATA__;
const ORDER = ["Bearish","Oversold","Accumulation","Bullish","Overbought","Danger zone"];
const ZC = {"Bearish":"--z-bear","Oversold":"--z-os","Accumulation":"--z-acc","Bullish":"--z-bull","Overbought":"--z-ob","Danger zone":"--z-dang","Neutral":"--z-neu","No data":"--z-na"};
const CODE = {R:"Bearish",O:"Oversold",A:"Accumulation",U:"Bullish",B:"Overbought",D:"Danger zone",N:"Neutral","-":"No data"};
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const zc = z => `var(${ZC[z]||"--z-neu"})`;
const esc = s => String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v,d=1) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const sgn = (v,d=1) => v==null ? `<td class="mut">–</td>` : `<td class="${v>0?'up':v<0?'down':''}">${v>0?'+':''}${fmt(v,d)}</td>`;
const dlabel = s => s ? new Date(s+"T00:00:00").toLocaleDateString("en-IN",{day:"2-digit",month:"short"}) : "";
const tv = (sym, iv) => "https://www.tradingview.com/chart/?symbol=" + encodeURIComponent("NSE:" + sym.replace(/[&-]/g,"_")) + (iv ? "&interval=" + iv : "");
const scr = sym => "https://www.screener.in/company/" + encodeURIComponent(sym) + "/";
const tvLink = (sym, iv) => `<span class="lk"><a class="tv" href="${tv(sym, iv)}" target="_blank" rel="noopener" aria-label="Open ${esc(sym)} chart on TradingView" onclick="event.stopPropagation()">Chart</a><a class="tv" href="${scr(sym)}" target="_blank" rel="noopener" aria-label="Open ${esc(sym)} on Screener" onclick="event.stopPropagation()">Screener</a></span>`;
const chip = z => `<span class="chip" style="--c:${zc(z)}">${esc(z)}</span>`;

let zoneF = null, sort = {k:"days",dir:1}, showAll = false, hl = null; const openDays = new Set();
let period = 30, grpOpen = new Map();
let tf = "d", S = [], dates = [], sessIdx = {}, P = D.params.d;
function setTF(t){
  tf = t; P = D.params[t]; dates = D.tf[t].dates;
  S = D.stocks.filter(s=>s[t]).map(s=>({sym:s.sym,name:s.name,sector:s.sector,liquid:s.liquid,price:s.price,r1d:s.r1d,r1w:s.r1w,r1m:s.r1m,...s[t]}));
  sessIdx = {}; dates.forEach((d,i)=>sessIdx[d]=dates.length-1-i);
  document.querySelectorAll("[data-tf]").forEach(b=>b.setAttribute("aria-pressed", b.dataset.tf===t));
  const last = dates[dates.length-1];
  document.getElementById("gen").textContent = `Updated ${D.generated}. ` + (t==="d" ? `Last session ${dlabel(last)}.` : `Last completed week ended ${dlabel(last)}.`);
  const popts = t==="d" ? [5,10,20,30,60,120] : [4,8,13,26,52,104];
  period = t==="d" ? 30 : 26;
  document.getElementById("period").innerHTML = popts.filter(n=>n<=dates.length).map(n=>`<option value="${n}" ${n===period?"selected":""}>Last ${n} ${P.units}</option>`).join("");
  grpOpen.clear();
  const opts = t==="d" ? [1,3,5,10,20] : [1,2,4,8,13];
  document.getElementById("f-new").innerHTML = `<option value="0">Entered any time</option>` + opts.map(n=>`<option value="${n}">${n===1?(t==="d"?"Entered today":"Entered this week"):`In last ${n} ${P.units}`}</option>`).join("");
  drawRules(); showAll=false; setSub(); drawAll();
}
const unitsN = n => `${n} ${n===1?P.unit:P.units}`;
function setSub(){
  document.getElementById("all-sub").textContent = `Tap a column to sort. The strip shows the zone for each of the last ${unitsN(period)}, oldest on the left.`;
}
const entered = s => s.since && sessIdx[s.since]!=null && sessIdx[s.since] < period && ORDER.includes(s.zone);
function drawRules(){
  const T = D.th, p = P, ma = tf==="d" ? `${p.ma}-day` : `${p.ma}-week`;
  document.getElementById("rules").innerHTML = `<p class="sub" style="margin-top:10px">${p.label} rules, checked in this order on each closing bar: oversold, danger zone, overbought, bullish, bearish, accumulation. The first match wins. Bullish, bearish and accumulation must hold for ${unitsN(p.confirm)} before a move counts. Oversold, overbought and danger zone start and end on the bar their condition is met or lost.${tf==="w"?" Weekly bars use completed weeks only, so a week counts once its Friday close is in.":""}</p>
  <dl>
    <dt>Oversold</dt><dd>RSI(14) at or below ${T.os}.</dd>
    <dt>Danger zone</dt><dd>A stretched uptrend that is risky to chase. Price has been above the Ichimoku cloud on at least ${p.trend_bars} of the last ${p.trend_window} ${p.units}, RSI is still ${p.rsi_floor} or higher, and either RSI was at or above ${T.ob} on at least ${p.ob_bars} of the last ${p.ob_window} ${p.units} or price is ${p.stretch}% or more above its ${ma} average. It leaves this zone once RSI cools below ${p.rsi_floor} or the stretch unwinds.</dd>
    <dt>Overbought</dt><dd>RSI(14) at or above ${T.ob}, but not yet stretched enough for the danger zone. Often the first leg of a strong move.</dd>
    <dt>Bullish</dt><dd>Price above the cloud, Tenkan at or above Kijun, MACD above signal, ADX at or above ${T.adx} with +DI leading, Choppiness under ${T.cht} (trending), RSI between 50 and ${T.ob}.</dd>
    <dt>Bearish</dt><dd>Price below the cloud, MACD under signal, ADX at or above ${T.adx} with −DI leading, RSI between ${T.os} and 50.</dd>
    <dt>Accumulation</dt><dd>A sideways base: Choppiness at or above ${T.chr} or ADX under ${T.adx}, RSI between 40 and 60, MACD histogram higher than ${unitsN(p.hist_rise_bars)} ago, and price inside or close to the cloud.</dd>
    <dt>Neutral</dt><dd>None of the above. Not one of the six zones; shown only when you pick it in the zone filter.</dd>
  </dl>`;
}
function base(){
  const liq = document.getElementById("liq").checked;
  const sec = document.getElementById("f-sec").value;
  return S.filter(s => (!liq || s.liquid) && (!sec || s.sector===sec));
}

function drawCycle(){
  const b = base();
  const el = document.getElementById("cycle");
  el.classList.toggle("filtering", !!zoneF);
  el.innerHTML = ORDER.map((z,i)=>{
    const all = b.filter(s=>s.zone===z), nw = all.filter(entered).length;
    return `<button class="z" style="--c:${zc(z)}" data-z="${z}" aria-pressed="${zoneF===z}">
      <span class="k">${i+1}</span><span class="n">${all.length}</span>
      <span><span class="t">${z}</span><br><span class="s">${nw ? `${nw} entered in ${unitsN(period)}` : `none entered in ${unitsN(period)}`}</span></span></button>`;}).join("");
  el.querySelectorAll(".z").forEach(bn=>bn.addEventListener("click",()=>{
    zoneF = zoneF===bn.dataset.z ? null : bn.dataset.z;
    document.getElementById("f-zone").value = zoneF||""; showAll=false; drawAll(); }));
}

function drawNew(){
  const nd = period;
  document.getElementById("new-sub").textContent = `Stocks that moved into their current zone in the last ${unitsN(nd)} and are still in it, newest first. Tap one to find it in the table.`;
  const list = base().filter(s=>entered(s) && (!zoneF || s.zone===zoneF));
  const by = {}; list.forEach(s=>(by[s.since] ??= []).push(s));
  const keys = Object.keys(by).sort().reverse();
  const box = document.getElementById("days");
  if (!keys.length){ box.innerHTML = `<p class="empty">No new entries${zoneF?` into ${zoneF}`:""} in the last ${unitsN(nd)} with these filters.</p>`; return; }
  box.innerHTML = keys.map(d=>{
    const items = by[d].sort((a,b)=>ORDER.indexOf(a.zone)-ORDER.indexOf(b.zone) || a.sym.localeCompare(b.sym));
    const ago = sessIdx[d]; const tag = ago===0 ? (tf==="d"?"today":"latest week") : `${unitsN(ago)} ago`;
    const head = tf==="d" ? dlabel(d) : `Week ending ${dlabel(d)}`;
    const CAP = 24, full = openDays.has(d) || items.length <= CAP;
    return `<div class="day"><h3>${head} <span>${tag}, ${items.length} ${items.length===1?"stock":"stocks"}</span></h3><div class="ent">${
      (full ? items : items.slice(0,CAP)).map(s=>`<button data-sym="${esc(s.sym)}" style="--c:${zc(s.zone)}" title="${esc(s.name)}"><i></i><b>${esc(s.sym)}</b> ${esc(s.zone)}${s.prev?` <small>from ${esc(s.prev)}</small>`:""}</button>`).join("")}${
      full ? "" : `<button class="more" data-day="${d}" style="margin:0">Show all ${items.length}</button>`}</div></div>`;
  }).join("");
  box.querySelectorAll("button[data-day]").forEach(b=>b.addEventListener("click",()=>{ openDays.add(b.dataset.day); drawNew(); }));
  box.querySelectorAll("button[data-sym]").forEach(b=>b.addEventListener("click",()=>{
    hl = b.dataset.sym; document.getElementById("q").value = hl; showAll=false; drawTable();
    document.getElementById("all").scrollIntoView({behavior:"smooth"}); }));
}

function strip(full){
  const code = (full||"").slice(-period), n = code.length;
  const gap = n > 60 ? 0 : 1, w = Math.max(1.4, Math.min(5, 150/n - gap));
  return `<svg class="strip" width="${n*(w+gap)}" height="14" viewBox="0 0 ${n*(w+gap)} 14" role="img" aria-label="Zone history">${
    [...code].map((c,i)=>`<rect x="${i*(w+gap)}" y="1" width="${w}" height="12" rx="1" fill="${zc(CODE[c])}"><title>${dlabel(dates[dates.length-n+i])}: ${CODE[c]}</title></rect>`).join("")}</svg>`;
}

const cols = () => [["sym","Stock"],["price","Price"],["zone","Zone","l"],["since",tf==="d"?"Since":"Since week of","l"],["days",P.units[0].toUpperCase()+P.units.slice(1)],["prev","Came from","l"],["strip",`Last ${unitsN(period)}`,"l"],
  ["rsi","RSI"],["macd_x","MACD","l"],["adx","ADX"],["di","+DI / −DI"],["chop","Chop"],["cloud","Cloud","l"],["stretch",tf==="d"?`vs ${P.ma}-DMA %`:`vs ${P.ma}-WMA %`],
  tf==="d"?["r1d","1D %"]:["r1w","1W %"],["r1m","1M %"]];
function drawTable(){
  const nf = +document.getElementById("f-new").value, q = document.getElementById("q").value.trim().toUpperCase();
  let list = base().filter(s => (!zoneF || s.zone===zoneF) && (!nf || (s.since && sessIdx[s.since]!=null && sessIdx[s.since] < nf && s.zone!=="Neutral")));
  if (!zoneF) list = list.filter(s=>ORDER.includes(s.zone));
  if (q) list = list.filter(s => s.sym.includes(q) || s.name.toUpperCase().includes(q));
  list.sort((a,b)=>{ let k=sort.k, x=a[k], y=b[k];
    if (k==="zone"){ x=ORDER.indexOf(x); y=ORDER.indexOf(y); }
    if (k==="di"){ x=(a.pdi??0)-(a.mdi??0); y=(b.pdi??0)-(b.mdi??0); }
    if (k==="days" && sort.dir===1){ x = a.capped?1e9:x; y = b.capped?1e9:y; }
    if (x==null) return 1; if (y==null) return -1;
    return (typeof x==="string" ? x.localeCompare(y) : x-y) * sort.dir; });
  const grouped = document.getElementById("grp").checked;
  const LIMIT = 150, shown = (showAll || grouped) ? list : list.slice(0,LIMIT);
  const t = document.getElementById("t"), COLS = cols();
  const cell = (s,k) => {
    switch(k){
      case "sym": return `<td class="name"><b>${esc(s.sym)}</b>${tvLink(s.sym, tf==="w"?"W":"D")}<small>${esc(s.sector)}</small></td>`;
      case "price": return `<td>${fmt(s.price,2)}</td>`;
      case "zone": return `<td class="l">${chip(s.zone)}${s.new?' <small class="mut">new</small>':''}</td>`;
      case "since": return `<td class="l">${s.capped ? `<span class="mut">before ${dlabel(D.tf[tf].lb_start)}</span>` : dlabel(s.since)}</td>`;
      case "days": return `<td>${s.capped ? P.lookback+"+" : s.days}</td>`;
      case "prev": return `<td class="l ${s.prev?'':'mut'}">${esc(s.prev||"–")}</td>`;
      case "strip": return `<td class="l">${strip(s.strip||"")}</td>`;
      case "rsi": return `<td class="${s.rsi>=70?'down':s.rsi<=30?'up':''}">${fmt(s.rsi,0)}</td>`;
      case "macd_x": return `<td class="l ${s.macd_x==="Above signal"?'up':s.macd_x?'down':'mut'}">${s.macd_x?esc(s.macd_x):"–"}</td>`;
      case "adx": return `<td>${fmt(s.adx,0)}</td>`;
      case "di": return `<td><span class="up">${fmt(s.pdi,0)}</span> / <span class="down">${fmt(s.mdi,0)}</span></td>`;
      case "chop": return `<td>${fmt(s.chop,0)}</td>`;
      case "cloud": return `<td class="l">${esc(s.cloud||"–")}</td>`;
      case "stretch": return sgn(s.stretch,1);
      case "r1d": return sgn(s.r1d,2); case "r1w": return sgn(s.r1w,1); case "r1m": return sgn(s.r1m,1);
    }};
  t.innerHTML = `<thead><tr>${COLS.map(([k,l,c])=>`<th class="${c||''}" data-k="${k}" ${sort.k===k?`aria-sort="${sort.dir>0?'ascending':'descending'}"`:''}>${l}</th>`).join("")}</tr></thead><tbody>${
    !shown.length ? `<tr><td class="empty" colspan="${COLS.length}">No stocks match these filters. Try “Entered any time” or untick “Liquid only”.</td></tr>`
    : grouped ? groupRows(shown, COLS, cell, !!q)
    : shown.map(s=>`<tr class="${s.sym===hl?'hl':''}">${COLS.map(([k])=>cell(s,k)).join("")}</tr>`).join("") + (false ? `<tr><td class="empty" colspan="${COLS.length}">` : "")}</tbody>`;
  t.querySelectorAll("tr.gs button").forEach(b=>b.addEventListener("click",()=>{
    grpOpen.set(b.dataset.g, b.getAttribute("aria-expanded")!=="true"); drawTable(); }));
  t.querySelectorAll("th").forEach(th=>th.addEventListener("click",()=>{ const k=th.dataset.k; if(k==="strip") return;
    sort.dir = sort.k===k ? -sort.dir : (["sym","zone","prev","cloud","macd_x","days"].includes(k)?1:-1); sort.k=k; drawTable(); }));
  const m = document.getElementById("more"); m.hidden = grouped || showAll || list.length<=LIMIT; m.textContent = `Show all ${list.length}`;
}
function groupRows(list, COLS, cell, forceOpen){
  const zs = zoneF ? [zoneF] : ORDER, lb = dlabel(D.tf[tf].lb_start);
  let html = "";
  zs.forEach(z=>{
    const rows = list.filter(s=>s.zone===z); if (!rows.length) return;
    html += `<tr class="gz" style="--c:${zc(z)}"><td colspan="${COLS.length}"><span class="gl">${chip(z)} <b>${rows.length}</b> <span class="mut">${rows.length===1?"stock":"stocks"}</span></span></td></tr>`;
    const by = new Map();
    rows.forEach(s=>{ const g = s.capped ? `In this zone since before ${lb}` : `From ${s.prev||"no data"}`; if(!by.has(g)) by.set(g,[]); by.get(g).push(s); });
    [...by.entries()].sort((a,b)=>b[1].length-a[1].length).forEach(([g,items])=>{
      const key = z+"|"+g, open = forceOpen || (grpOpen.has(key) ? grpOpen.get(key) : !!zoneF);
      html += `<tr class="gs"><td colspan="${COLS.length}"><button data-g="${esc(key)}" aria-expanded="${open}"><b>${esc(g)}</b><span class="cnt">${items.length}</span></button></td></tr>`;
      if (open) html += items.map(s=>`<tr class="${s.sym===hl?'hl':''}">${COLS.map(([k])=>cell(s,k)).join("")}</tr>`).join("");
    });
  });
  return html;
}
function drawAll(){ drawCycle(); drawNew(); drawTable(); }

const fz = document.getElementById("f-zone");
fz.innerHTML = `<option value="">All six zones</option>` + [...ORDER,"Neutral"].map(z=>`<option>${z}</option>`).join("");
fz.addEventListener("change",()=>{ zoneF = fz.value||null; showAll=false; drawAll(); });
const fs = document.getElementById("f-sec");
fs.innerHTML = `<option value="">All sectors</option>` + [...new Set(D.stocks.map(s=>s.sector))].sort().map(s=>`<option>${esc(s)}</option>`).join("");
fs.addEventListener("change",()=>{ showAll=false; drawAll(); });
document.getElementById("f-new").addEventListener("change",()=>{ showAll=false; drawTable(); });
document.getElementById("liq").addEventListener("change",()=>{ showAll=false; drawAll(); });
document.getElementById("grp").addEventListener("change",()=>{ showAll=false; drawTable(); });
document.getElementById("period").addEventListener("change",e=>{ period=+e.target.value; openDays.clear(); setSub(); drawAll(); });
document.getElementById("q").addEventListener("input",()=>{ hl=null; showAll=false; drawTable(); });
document.getElementById("more").addEventListener("click",()=>{ showAll=true; drawTable(); });
document.getElementById("legend").innerHTML = [...ORDER,"Neutral"].map(z=>`<span><i style="--c:${zc(z)}"></i>${z}</span>`).join("");
document.querySelectorAll("[data-tf]").forEach(b=>b.addEventListener("click",()=>{ openDays.clear(); hl=null; setTF(b.dataset.tf); }));
setTF("d");
</script>
</body>
</html>
"""
