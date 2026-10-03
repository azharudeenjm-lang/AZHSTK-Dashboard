"""Renders docs/levels.html: support, resistance and trendline signals."""
import json
from datetime import datetime, timedelta, timezone

from .config import DOCS, LEVEL_PARAMS


def render(payload, charts=None):
    DOCS.mkdir(parents=True, exist_ok=True)
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    payload["generated"] = ist.strftime("%d %b %Y, %I:%M %p IST")
    payload["params"] = LEVEL_PARAMS
    blob = json.dumps(payload, separators=(",", ":"), allow_nan=False, default=str).replace("</", "<\\/")
    (DOCS / "levels.html").write_text(TEMPLATE.replace("__DATA__", blob), encoding="utf-8")
    # charts are large, so they live in their own file and load after the table
    (DOCS / "levels_charts.json").write_text(
        json.dumps(charts or {}, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    return DOCS / "levels.html"


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>NSE support, resistance and trendlines</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧭</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#EEF2F6; --panel:#FFFFFF; --ink:#16243A; --muted:#5C6B80; --line:#D3DBE5; --up:#1E8F5A; --down:#C2453B; --focus:#2F62C8;
  --s-brk:#1E8F5A; --s-tlb:#13857A; --s-ret:#2F62C8; --s-tls:#6B4BB8; --s-fib:#8A5A12; --s-ns:#4F7C5F; --s-bd:#C2453B; --s-tbd:#A8285E; --s-nr:#C9780F;
  --z-bear:#C2453B; --z-os:#6B4BB8; --z-acc:#2F62C8; --z-bull:#1E8F5A; --z-ob:#C9780F; --z-dang:#A8285E; --z-neu:#A3AFBF;
  --font:"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  box-sizing:border-box; padding-top:env(safe-area-inset-top,0px); padding-bottom:env(safe-area-inset-bottom,0px);
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --bg:#111925; --panel:#18222F; --ink:#E5EBF3; --muted:#93A1B4; --line:#2A3646; --up:#3FBF85; --down:#E9675C; --focus:#6E97F0;
  --s-brk:#3FBF85; --s-tlb:#3BB8AA; --s-ret:#6E97F0; --s-tls:#9C82E6; --s-fib:#D4A049; --s-ns:#7FB08F; --s-bd:#E9675C; --s-tbd:#E0619A; --s-nr:#E5A040;
  --z-bear:#E9675C; --z-os:#9C82E6; --z-acc:#6E97F0; --z-bull:#3FBF85; --z-ob:#E5A040; --z-dang:#E0619A; --z-neu:#5E6B7C;}}
:root[data-theme="dark"]{
  --bg:#111925; --panel:#18222F; --ink:#E5EBF3; --muted:#93A1B4; --line:#2A3646; --up:#3FBF85; --down:#E9675C; --focus:#6E97F0;
  --s-brk:#3FBF85; --s-tlb:#3BB8AA; --s-ret:#6E97F0; --s-tls:#9C82E6; --s-fib:#D4A049; --s-ns:#7FB08F; --s-bd:#E9675C; --s-tbd:#E0619A; --s-nr:#E5A040;
  --z-bear:#E9675C; --z-os:#9C82E6; --z-acc:#6E97F0; --z-bull:#3FBF85; --z-ob:#E5A040; --z-dang:#E0619A; --z-neu:#5E6B7C;}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--font);font-variant-numeric:tabular-nums;-webkit-text-size-adjust:100%}
.wrap{max-width:1180px;margin:0 auto;padding:16px 14px 48px}
header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:6px 16px;margin-bottom:6px}
h1{font-size:1.55rem;font-weight:700;letter-spacing:-.01em;margin:0}
nav{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.9rem}
nav a{color:var(--muted);text-decoration:none}
nav a[aria-current]{color:var(--ink);font-weight:600}
.top{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;justify-content:space-between;margin:0 0 14px}
.stamp{color:var(--muted);font-size:.85rem;margin:0}
h2{font-size:1.1rem;margin:0 0 4px;font-weight:600}
h3{font-size:.9rem;margin:0 0 8px;font-weight:600;color:var(--muted)}
.sub{color:var(--muted);font-size:.85rem;margin:0 0 12px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:16px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:var(--panel)}
.seg button{border:0;background:transparent;color:var(--muted);font:500 .88rem var(--font);padding:7px 16px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
.sigs{display:grid;gap:8px;grid-template-columns:repeat(2,minmax(0,1fr))}
@media(min-width:760px){.sigs.b{grid-template-columns:repeat(3,minmax(0,1fr))}.sigs.r{grid-template-columns:repeat(3,minmax(0,1fr))}}
.sg{border:1px solid var(--line);border-left:5px solid var(--c);background:var(--panel);border-radius:10px;padding:10px 12px;text-align:left;font:inherit;color:var(--ink);cursor:pointer}
.sg .n{font-size:1.6rem;font-weight:700;line-height:1.1;display:block}
.sg .t{font-weight:600;font-size:.88rem}
.sg .s{display:block;font-size:.75rem;color:var(--muted)}
.sg[aria-pressed="true"]{background:color-mix(in srgb,var(--c) 14%,var(--panel));border-color:var(--c)}
.grp-h{display:flex;justify-content:space-between;align-items:baseline;margin:14px 0 8px}
.chip{display:inline-block;padding:1px 7px;border-radius:999px;font-size:.72rem;font-weight:600;color:#fff;background:var(--c);margin:1px 2px 1px 0;white-space:nowrap}
.tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px}
select,input[type=search]{font:inherit;font-size:.86rem;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 9px;min-width:0;max-width:100%}
label.tog{font-size:.85rem;color:var(--muted);display:flex;gap:6px;align-items:center}
button:focus-visible,select:focus-visible,input:focus-visible,tr:focus-visible,a:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{padding:7px 8px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line);vertical-align:middle}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--panel);z-index:1}
td.l,th.l{text-align:left}
th{color:var(--muted);font-weight:500;cursor:pointer;user-select:none;background:var(--panel)}
th[aria-sort]::after{content:" ↓";font-size:.75em} th[aria-sort="ascending"]::after{content:" ↑"}
tbody tr.row{cursor:pointer}
tbody tr.row:hover td{background:color-mix(in srgb,var(--line) 35%,var(--panel))}
tr.open td{background:color-mix(in srgb,var(--focus) 10%,var(--panel))}
tr.big td{padding:10px 8px 14px;background:var(--panel);white-space:normal}
.name small{display:block;color:var(--muted);font-size:.75rem;max-width:170px;overflow:hidden;text-overflow:ellipsis}
.up{color:var(--up)}.down{color:var(--down)}.mut{color:var(--muted)}
.lv b{font-weight:600}.lv small{display:block;color:var(--muted);font-size:.74rem}
.lk{white-space:nowrap}
button.tv{background:transparent;font-family:inherit;line-height:inherit;cursor:pointer}
.tv{font-size:.72rem;font-weight:600;color:var(--focus);text-decoration:none;border:1px solid currentColor;border-radius:6px;padding:0 5px;margin-left:6px;vertical-align:1px}
.tv:hover{background:color-mix(in srgb,currentColor 12%,transparent)}
.bigc{display:block;width:100%;max-width:760px;height:auto;position:sticky;left:8px}
.key{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.76rem;color:var(--muted);margin-top:6px;position:sticky;left:8px}
.key i{display:inline-block;width:16px;height:0;border-top:2px solid var(--c);margin-right:5px;vertical-align:3px}
.key i.d{border-top-style:dashed}
.more{margin-top:10px;font:500 .85rem var(--font);background:transparent;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:6px 12px;cursor:pointer}
details{font-size:.88rem} details summary{cursor:pointer;font-weight:600}
dl{display:grid;grid-template-columns:max-content 1fr;gap:6px 14px;margin:12px 0 0}
dt{font-weight:600} dd{margin:0;color:var(--muted);max-width:70ch}
.empty{color:var(--muted);font-size:.88rem;padding:6px 0}
.note{color:var(--muted);font-size:.78rem;margin-top:24px;max-width:72ch}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Support, resistance and trendlines</h1>
  <div id="gsearch"></div>
  <nav aria-label="Dashboards"><a href="index.html">Sector rotation</a><a href="zones.html">Zones</a><a href="levels.html" aria-current="page">Levels</a><a href="setups.html">Setups</a><a href="watchlist.html">My list</a><a href="backtest.html">Backtest</a></nav>
</header>
<div class="top">
  <p class="stamp" id="gen"></p>
  <div class="seg" role="group" aria-label="Timeframe">
    <button data-tf="d" aria-pressed="true">Daily</button><button data-tf="w" aria-pressed="false">Weekly</button>
  </div>
</div>

<section class="panel" aria-label="Signals">
  <div class="grp-h"><h2 style="margin:0">Bullish setups</h2><span class="sub" style="margin:0">Tap to filter the table</span></div>
  <div class="sigs b" id="sig-b"></div>
  <div class="grp-h"><h2 style="margin:0">Bearish and caution</h2></div>
  <div class="sigs r" id="sig-r"></div>
</section>

<section class="panel" aria-labelledby="h-all" id="all">
  <h2 id="h-all">Stocks</h2>
  <p class="sub">Tap a row to see its chart with the levels and lines that were found. Support and resistance show price, distance from today's close, and number of touches.</p>
  <div class="tools">
    <select id="f-sig" aria-label="Signal"></select>
    <select id="f-zone" aria-label="Technical zone"></select>
    <select id="f-sec" aria-label="Sector"></select>
    <input type="search" id="q" placeholder="Find a stock" aria-label="Find a stock">
    <label class="tog"><input type="checkbox" id="vol"> Breakouts on volume only</label>
    <label class="tog"><input type="checkbox" id="liq" checked> Liquid only</label>
  </div>
  <div class="tbl"><table id="t"></table></div>
  <button class="more" id="more" hidden></button>
</section>

<section class="panel"><details><summary>How levels and lines are found</summary><div id="rules"></div></details></section>
<p class="note">Levels and trendlines are drawn by rules, so they will not always match lines you would draw by hand. Use them as a shortlist and confirm on the chart. Daily data from Yahoo Finance. For research only, not investment advice.</p>
</div>

<script>
const D = __DATA__;
const BULL = ["Breakout","Trendline breakout","Retest","At trendline support","At Fibonacci support","Near support"];
const BEAR = ["Breakdown","Trendline breakdown","Near resistance"];
const SC = {"Breakout":"--s-brk","Trendline breakout":"--s-tlb","Retest":"--s-ret","At trendline support":"--s-tls","At Fibonacci support":"--s-fib","Near support":"--s-ns","Breakdown":"--s-bd","Trendline breakdown":"--s-tbd","Near resistance":"--s-nr"};
const SDESC = {"Breakout":"closed above tested resistance","Trendline breakout":"closed above a falling line","Retest":"pulled back to a broken level","At trendline support":"resting on a rising line","At Fibonacci support":"pulled back into the 50–61.8% zone","Near support":"just above a support level","Breakdown":"closed below tested support","Trendline breakdown":"closed below a rising line","Near resistance":"just under a resistance level"};
const ZORDER = ["Bearish","Oversold","Accumulation","Bullish","Overbought","Danger zone","Neutral"];
const ZC = {"Bearish":"--z-bear","Oversold":"--z-os","Accumulation":"--z-acc","Bullish":"--z-bull","Overbought":"--z-ob","Danger zone":"--z-dang","Neutral":"--z-neu"};
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const esc = s => String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v,d=1) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const sgn = (v,d=1) => v==null ? `<td class="mut">–</td>` : `<td class="${v>0?'up':v<0?'down':''}">${v>0?'+':''}${fmt(v,d)}</td>`;
const tv = (sym, iv) => "https://www.tradingview.com/chart/?symbol=" + encodeURIComponent("NSE:" + sym.replace(/[&-]/g,"_")) + (iv ? "&interval=" + iv : "");
const scr = sym => "https://www.screener.in/company/" + encodeURIComponent(sym) + "/";
const links = (sym, iv) => `<span class="lk"><a class="tv" href="${tv(sym, iv)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Chart</a><a class="tv" href="${scr(sym)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Screener</a></span>`;
const schip = s => `<span class="chip" style="--c:var(${SC[s]})">${esc(s)}</span>`;
const zchip = z => z ? `<span class="chip" style="--c:var(${ZC[z]||'--z-neu'})">${esc(z)}</span>` : "–";

let CH = null;  // chart data, loaded after first paint
let tf = "d", P = D.params.d, S = [], sigF = null, sort = {k:"sig",dir:1}, showAll = false, openSym = null;
function setTF(t){
  tf = t; P = D.params[t]; openSym = null; showAll = false;
  S = D.stocks.filter(s=>s[t]).map(s=>({sym:s.sym,name:s.name,sector:s.sector,liquid:s.liquid,price:s.price,
        r1d:s.r1d,r1w:s.r1w,r1m:s.r1m,vxd:s.vx,zone:t==="d"?s.zd:s.zw,...s[t]}));
  S.forEach(s=>{ s.ch = CH && CH[s.sym] ? CH[s.sym][t] : null; s.top = s.sig.length ? Math.min(...s.sig.map(x=>[...BULL,...BEAR].indexOf(x))) : 99;
                 s.bvx = (s.brk&&s.brk.vx) ?? (s.tlr&&s.tlr.vx) ?? null; });
  document.querySelectorAll("[data-tf]").forEach(b=>b.setAttribute("aria-pressed", b.dataset.tf===t));
  document.getElementById("gen").textContent = `Updated ${D.generated}. ${t==="d" ? "Daily candles." : D.partial ? `Weekly candles. This week is still forming (prices up to ${new Date(D.asof+"T00:00:00").toLocaleDateString("en-IN",{day:"2-digit",month:"short"})}), so weekly signals can change until Friday's close.` : "Weekly candles."}`;
  drawRules(); drawAll();
}
function base(){
  const liq = document.getElementById("liq").checked, sec = document.getElementById("f-sec").value,
        z = document.getElementById("f-zone").value, vol = document.getElementById("vol").checked;
  return S.filter(s => (!liq || s.liquid) && (!sec || s.sector===sec) && (!z || s.zone===z)
    && (!vol || (s.bvx!=null && s.bvx >= P.vol_x)));
}
function tile(sig, b){
  const n = b.filter(s=>s.sig.includes(sig)).length;
  return `<button class="sg" style="--c:var(${SC[sig]})" data-s="${sig}" aria-pressed="${sigF===sig}"><span class="n">${n}</span><span class="t">${sig}</span><span class="s">${SDESC[sig]}</span></button>`;
}
function drawTiles(){
  const b = base();
  document.getElementById("sig-b").innerHTML = BULL.map(s=>tile(s,b)).join("");
  document.getElementById("sig-r").innerHTML = BEAR.map(s=>tile(s,b)).join("");
  document.querySelectorAll(".sg").forEach(el=>el.addEventListener("click",()=>{
    sigF = sigF===el.dataset.s ? null : el.dataset.s; document.getElementById("f-sig").value = sigF||"";
    showAll=false; drawAll(); if (sigF) document.getElementById("all").scrollIntoView({behavior:"smooth"}); }));
}

/* ---------- charts ---------- */
function chart(ch, W, H, big){
  const c = ch.c, n = c.length, pad = big ? {l:6,r:58,t:10,b:18} : {l:2,r:2,t:3,b:3};
  const vals = [...c]; const lv = ch.lv||{};
  Object.values(lv).forEach(v=>vals.push(v));
  ["tlr","tls"].forEach(k=>{ if(ch[k]) vals.push(ch[k][1], ch[k][3]); });
  let lo = Math.min(...c), hi = Math.max(...c); const span = hi-lo || hi*0.05;
  vals.forEach(v=>{ if (v>=lo-span*0.6 && v<=hi+span*0.6){ lo=Math.min(lo,v); hi=Math.max(hi,v); } });
  const m = (hi-lo)*0.06; lo-=m; hi+=m;
  const X = i => pad.l + i/(n-1)*(W-pad.l-pad.r), Y = v => pad.t + (hi-v)/(hi-lo)*(H-pad.t-pad.b);
  const inR = v => v>=lo && v<=hi;
  let g = `<polyline points="${c.map((v,i)=>`${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(" ")}" fill="none" stroke="${css('--ink')}" stroke-width="${big?1.5:1}" stroke-linejoin="round" opacity=".85"/>`;
  const hline = (v, col, dash, label) => { if(!inR(v)) return "";
    return `<line x1="${pad.l}" x2="${W-pad.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="${col}" stroke-width="${big?1.4:1}" ${dash?'stroke-dasharray="4 3"':''}/>` +
      (big ? `<text x="${W-pad.r+4}" y="${Y(v)+4}" font-size="11" fill="${col}">${fmt(v, v<100?2:0)}</text>` : ""); };
  if (lv.res) g += hline(lv.res, css("--down"), true);
  if (lv.sup) g += hline(lv.sup, css("--up"), true);
  if (lv.brk && lv.brk!==lv.sup) g += hline(lv.brk, css("--s-ret"), false);
  if (lv.bdn && lv.bdn!==lv.res) g += hline(lv.bdn, css("--s-tbd"), false);
  [["tlr",css("--down")],["tls",css("--up")]].forEach(([k,col])=>{ const t=ch[k]; if(!t) return;
    g += `<line x1="${X(t[0])}" y1="${Y(t[1])}" x2="${X(t[2])}" y2="${Y(t[3])}" stroke="${col}" stroke-width="${big?1.8:1.2}" opacity=".9"/>`; });
  ["brk_x","bdn_x"].forEach(k=>{ if(ch[k]!=null && ch[k]>=0 && ch[k]<n)
    g += `<circle cx="${X(ch[k])}" cy="${Y(c[ch[k]])}" r="${big?4.5:2.5}" fill="${k==="brk_x"?css("--up"):css("--down")}" stroke="${css('--panel')}" stroke-width="1"/>`; });
  if (big) g += `<text x="${W-pad.r+4}" y="${Y(c[n-1])+4}" font-size="11" font-weight="600" fill="${css('--ink')}">${fmt(c[n-1], c[n-1]<100?2:0)}</text>`;
  return `<svg ${big?'class="bigc"':''} width="${big?'':W}" height="${big?'':H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Price chart with levels">${g}</svg>`;
}
const keyHTML = `<div class="key"><span><i style="--c:var(--ink)"></i>Close</span><span><i class="d" style="--c:var(--down)"></i>Resistance</span><span><i class="d" style="--c:var(--up)"></i>Support</span><span><i style="--c:var(--s-ret)"></i>Broken level</span><span><i style="--c:var(--down)"></i>Falling trendline</span><span><i style="--c:var(--up)"></i>Rising trendline</span></div>`;

/* ---------- table ---------- */
const cols = () => [["sym","Stock"],["price","Price"],["sig","Signals","l"],["zone","Zone","l"],["sup","Support","l"],["res","Resistance","l"],["tl","Trendline","l"],["bvx","Breakout volume ×"],["mini",`Last ${P.chart} ${P.units}`,"l"],[tf==="d"?"r1d":"r1w",tf==="d"?"1D %":"1W %"],["r1m","1M %"]];
function lvCell(o, kind){
  if (!o) return `<td class="l mut">–</td>`;
  return `<td class="l lv"><b>${fmt(o.p, o.p<100?2:1)}</b> <span class="${kind==='sup'?'up':'down'}">${kind==='sup'?'−':'+'}${fmt(o.d)}%</span><small>${o.t} touches</small></td>`;
}
function tlCell(s){
  const parts = [];
  if (s.tlr) parts.push(`<span class="down">Falling</span> ${fmt(s.tlr.v, s.tlr.v<100?2:1)} <small>${s.tlr.d>=0?`${fmt(s.tlr.d)}% above price`:`broken, price ${fmt(-s.tlr.d)}% above`}, ${s.tlr.t} touches</small>`);
  if (s.tls) parts.push(`<span class="up">Rising</span> ${fmt(s.tls.v, s.tls.v<100?2:1)} <small>${s.tls.d>=0?`price ${fmt(s.tls.d)}% above`:`broken, price ${fmt(-s.tls.d)}% below`}, ${s.tls.t} touches</small>`);
  return `<td class="l lv">${parts.length ? parts.join("") : '<span class="mut">–</span>'}</td>`;
}
function drawTable(){
  const q = document.getElementById("q").value.trim().toUpperCase();
  let list = base().filter(s => s.sig.length && (!sigF || s.sig.includes(sigF)) && (!q || s.sym.includes(q) || s.name.toUpperCase().includes(q)));
  const key = (s,k) => k==="sig" ? s.top : k==="zone" ? ZORDER.indexOf(s.zone) : k==="sup" ? s.sup?.d : k==="res" ? s.res?.d
              : k==="tl" ? (s.tlr?.d ?? s.tls?.d) : s[k];
  list.sort((a,b)=>{ let x=key(a,sort.k), y=key(b,sort.k);
    if (x==null) return 1; if (y==null) return -1;
    const r = (typeof x==="string" ? x.localeCompare(y) : x-y) * sort.dir;
    return r || ((b.bvx??0)-(a.bvx??0)); });
  const LIMIT = 150, shown = showAll ? list : list.slice(0, LIMIT), COLS = cols(), iv = tf==="w"?"W":"D";
  const cell = (s,k) => { switch(k){
    case "sym": return `<td class="name"><button class="psym" data-p="${esc(s.sym)}">${esc(s.sym)}</button>${links(s.sym, iv)}<small>${esc(s.sector)}</small></td>`;
    case "price": return `<td>${fmt(s.price,2)}</td>`;
    case "sig": return `<td class="l">${s.sig.map(schip).join("")}${s.brk&&s.brk.ago>0?`<small class="mut"> ${s.brk.ago} ${s.brk.ago===1?P.unit:P.units} ago</small>`:""}</td>`;
    case "zone": return `<td class="l">${zchip(s.zone)}</td>`;
    case "sup": return lvCell(s.sup,"sup"); case "res": return lvCell(s.res,"res");
    case "tl": return tlCell(s);
    case "bvx": return `<td class="${s.bvx>=P.vol_x?'up':''}">${s.bvx!=null?fmt(s.bvx)+'×':'–'}</td>`;
    case "mini": return `<td class="l">${s.ch ? chart(s.ch, 130, 36, false) : (CH ? "" : '<span class="mut">loading…</span>')}</td>`;
    default: return sgn(s[k], k==="r1d"?2:1);
  }};
  const t = document.getElementById("t");
  t.innerHTML = `<thead><tr>${COLS.map(([k,l,c])=>`<th class="${c||''}" data-k="${k}" ${sort.k===k?`aria-sort="${sort.dir>0?'ascending':'descending'}"`:''}>${l}</th>`).join("")}</tr></thead><tbody>${
    shown.length ? shown.map(s=>`<tr class="row ${s.sym===openSym?'open':''}" data-sym="${esc(s.sym)}" tabindex="0" aria-expanded="${s.sym===openSym}">${COLS.map(([k])=>cell(s,k)).join("")}</tr>` +
      (s.sym===openSym && s.ch ? `<tr class="big"><td colspan="${COLS.length}">${chart(s.ch, 760, 260, true)}${keyHTML}</td></tr>` : "")).join("")
    : `<tr><td class="empty" colspan="${COLS.length}">No stocks match these filters. Try another signal, zone or untick a box.</td></tr>`}</tbody>`;
  t.querySelectorAll("th").forEach(th=>th.addEventListener("click",()=>{ const k=th.dataset.k; if(k==="mini") return;
    sort.dir = sort.k===k ? -sort.dir : (["sym","sig","zone","sup","res","tl"].includes(k)?1:-1); sort.k=k; drawTable(); }));
  t.querySelectorAll("tr.row").forEach(tr=>{ const go=()=>{ openSym = openSym===tr.dataset.sym ? null : tr.dataset.sym; drawTable(); };
    tr.addEventListener("click",go); tr.addEventListener("keydown",e=>{ if(e.key==="Enter") go(); }); });
  const m = document.getElementById("more"); m.hidden = showAll || list.length<=LIMIT; m.textContent = `Show all ${list.length}`;
}
function drawAll(){ drawTiles(); drawTable(); }
function drawRules(){
  const p = P, u = p.units;
  document.getElementById("rules").innerHTML = `<p class="sub" style="margin-top:10px">${p.label} settings. A swing high is a ${p.unit} whose high beats the ${p.pivot} ${u} on each side; a swing low is the mirror image. Swing points within ${Math.round(p.tol_min*1000)/10}% of each other (or half the average true range, if larger) form one level, and a level needs at least 2 touches. Up to ${p.lookback} ${u} of history are searched.</p>
  <dl>
    <dt>Breakout</dt><dd>Closed at least ${p.brk*100}% above a resistance level in the last ${p.recent} ${u}, after spending the previous 30 ${u} at or below it. "Breakout volume" compares that ${p.unit}'s volume with its 20-${p.unit} average; ${p.vol_x}× or more counts as confirmed.</dd>
    <dt>Trendline breakout</dt><dd>A falling line through two or more lower swing highs that no close had broken, and price closed at least ${p.brk*100}% above it in the last ${p.recent} ${u}.</dd>
    <dt>Retest</dt><dd>Broke out between ${p.recent} and ${p.retest} ${u} ago and has since pulled back to within a small distance of that level while still closing above it.</dd>
    <dt>At trendline support</dt><dd>A rising line through two or more higher swing lows that no close has broken, with price within ${p.near_tl*100}% above it.</dd>
    <dt>At Fibonacci support</dt><dd>On the latest upswing of at least ${tf==="d"?"10":"15"}%, price has pulled back into the 50–61.8% retracement (the "golden pocket"), or to 38.2–50% where that level lines up with support, a rising trendline or the weekly Kijun. Retracement levels and targets are in each stock's Overview.</dd>
    <dt>Near support</dt><dd>Price is within ${p.near*100}% above the nearest support level.</dd>
    <dt>Breakdown</dt><dd>Closed at least ${p.brk*100}% below a support level in the last ${p.recent} ${u}.</dd>
    <dt>Trendline breakdown</dt><dd>Closed at least ${p.brk*100}% below a valid rising trendline in the last ${p.recent} ${u}.</dd>
    <dt>Near resistance</dt><dd>Price is within ${p.near*100}% below the nearest resistance level.</dd>
  </dl>`;
}

const fsig = document.getElementById("f-sig");
fsig.innerHTML = `<option value="">All signals</option>` + [...BULL,...BEAR].map(s=>`<option>${s}</option>`).join("");
fsig.addEventListener("change",()=>{ sigF = fsig.value||null; showAll=false; drawAll(); });
const fz = document.getElementById("f-zone");
fz.innerHTML = `<option value="">Any zone</option>` + ZORDER.map(z=>`<option>${z}</option>`).join("");
const fs = document.getElementById("f-sec");
fs.innerHTML = `<option value="">All sectors</option>` + [...new Set(D.stocks.map(s=>s.sector))].sort().map(s=>`<option>${esc(s)}</option>`).join("");
["f-zone","f-sec","vol","liq"].forEach(id=>document.getElementById(id).addEventListener("change",()=>{ showAll=false; drawAll(); }));
document.getElementById("q").addEventListener("input",()=>{ showAll=false; drawTable(); });
document.getElementById("more").addEventListener("click",()=>{ showAll=true; drawTable(); });
document.querySelectorAll("[data-tf]").forEach(b=>b.addEventListener("click",()=>setTF(b.dataset.tf)));
setTF("d");
fetch("levels_charts.json").then(r=>r.ok?r.json():null).then(j=>{ CH = j||{}; S.forEach(s=>{ s.ch = CH[s.sym] ? CH[s.sym][tf] : null; }); drawTable(); })
  .catch(()=>{ CH = {}; drawTable(); });
</script>
<script src="profile.js" defer></script>
</body>
</html>
"""
