"""Renders docs/index.html: one self-contained page, data embedded as JSON."""
import json
from datetime import datetime, timedelta, timezone

from .config import DOCS


def render(payload):
    DOCS.mkdir(parents=True, exist_ok=True)
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    payload["generated"] = ist.strftime("%d %b %Y, %I:%M %p IST")
    blob = json.dumps(payload, separators=(",", ":"), allow_nan=False, default=str)
    blob = blob.replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA__", blob)
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    return DOCS / "index.html"


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>NSE sector rotation</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧭</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#EEF2F6; --panel:#FFFFFF; --ink:#16243A; --muted:#5C6B80; --line:#D3DBE5;
  --lead:#1E8F5A; --weak:#B9821A; --lag:#C2453B; --impr:#2F62C8;
  --up:#1E8F5A; --down:#C2453B; --sel:#16243A;
  --font:"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  box-sizing:border-box;
  padding-top:env(safe-area-inset-top,0px); padding-bottom:env(safe-area-inset-bottom,0px);
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --bg:#111925; --panel:#18222F; --ink:#E5EBF3; --muted:#93A1B4; --line:#2A3646;
  --lead:#3FBF85; --weak:#E0AE45; --lag:#E9675C; --impr:#6E97F0; --up:#3FBF85; --down:#E9675C; --sel:#E5EBF3;}}
:root[data-theme="dark"]{
  --bg:#111925; --panel:#18222F; --ink:#E5EBF3; --muted:#93A1B4; --line:#2A3646;
  --lead:#3FBF85; --weak:#E0AE45; --lag:#E9675C; --impr:#6E97F0; --up:#3FBF85; --down:#E9675C; --sel:#E5EBF3;}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 var(--font);
  font-variant-numeric:tabular-nums;-webkit-text-size-adjust:100%}
.wrap{max-width:1180px;margin:0 auto;padding:16px 14px 48px}
header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:6px 16px;margin-bottom:14px}
h1{font-size:1.55rem;font-weight:700;letter-spacing:-.01em;margin:0}
.stamp{color:var(--muted);font-size:.85rem}
.bench{font-weight:600}
h2{font-size:1.1rem;margin:0 0 4px;font-weight:600}
.sub{color:var(--muted);font-size:.85rem;margin:0 0 12px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:16px}
.grid{display:grid;gap:16px;grid-template-columns:minmax(0,1fr)}
@media(min-width:960px){.grid.two{grid-template-columns:minmax(0,1.05fr) minmax(0,1fr)}}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}
.seg button{border:0;background:transparent;color:var(--muted);font:500 .85rem var(--font);padding:6px 14px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
button:focus-visible,input:focus-visible,select:focus-visible,tr:focus-visible{outline:2px solid var(--impr);outline-offset:2px}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:10px}
.rrg{width:100%;height:auto;display:block;touch-action:manipulation}
.rrg text{font-family:var(--font)}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.8rem;color:var(--muted);margin-top:8px}
.qf{display:flex;flex-wrap:wrap;gap:4px}
.qf button{font:500 .78rem var(--font);color:var(--ink);background:transparent;border:1px solid var(--line);border-radius:999px;padding:3px 9px;cursor:pointer}
.qf button[aria-pressed="false"]{opacity:.45;text-decoration:line-through}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}
.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.86rem}
th,td{padding:7px 8px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--panel);z-index:1}
th{color:var(--muted);font-weight:500;cursor:pointer;user-select:none;position:sticky;top:0;background:var(--panel)}
th[aria-sort]::after{content:" ↓";font-size:.75em}
th[aria-sort="ascending"]::after{content:" ↑"}
tbody tr{cursor:pointer}
tbody tr:hover td{background:color-mix(in srgb,var(--line) 35%,var(--panel))}
tr.on td{background:color-mix(in srgb,var(--impr) 12%,var(--panel))}
.up{color:var(--up)}.down{color:var(--down)}.mut{color:var(--muted)}
.chip{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.75rem;font-weight:600;color:#fff}
.q-Leading{background:var(--lead)}.q-Weakening{background:var(--weak)}.q-Lagging{background:var(--lag)}.q-Improving{background:var(--impr)}
.name small{display:block;color:var(--muted);font-size:.75rem;max-width:180px;overflow:hidden;text-overflow:ellipsis}
.tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
input[type=search],select{font:inherit;font-size:.88rem;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 10px;min-width:0}
label.tog{font-size:.85rem;color:var(--muted);display:flex;gap:6px;align-items:center}
.news{list-style:none;margin:0;padding:0}
.news li{padding:9px 0;border-bottom:1px solid var(--line)}
.news li:last-child{border-bottom:0}
.news a{color:var(--ink);text-decoration:none;font-weight:500}
.news a:hover{text-decoration:underline}
.news span{display:block;color:var(--muted);font-size:.78rem}
.more{margin-top:10px;font:500 .85rem var(--font);background:transparent;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:6px 12px;cursor:pointer}
.empty{color:var(--muted);font-size:.88rem;padding:8px 0}
.kpis{display:flex;flex-wrap:wrap;gap:6px 20px;font-size:.86rem;color:var(--muted);margin-bottom:12px}
.kpis b{color:var(--ink);font-weight:600}
.lk{white-space:nowrap}
.tv{font-size:.72rem;font-weight:600;color:var(--focus,var(--impr));text-decoration:none;border:1px solid currentColor;border-radius:6px;padding:0 5px;margin-left:6px;vertical-align:1px}
.tv:hover{background:color-mix(in srgb,currentColor 12%,transparent)}
.note{color:var(--muted);font-size:.78rem;margin-top:24px;max-width:72ch}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>NSE sector rotation</h1>
  <nav aria-label="Dashboards" style="display:flex;gap:14px;font-size:.9rem"><a href="index.html" aria-current="page" style="color:var(--ink);font-weight:600;text-decoration:none">Sector rotation</a><a href="zones.html" style="color:var(--muted);text-decoration:none">Zones</a></nav>
  <div class="stamp" style="flex-basis:100%"><span class="bench" id="bench"></span> <span id="gen"></span></div>
</header>

<div class="grid two">
  <section class="panel" aria-labelledby="h-rrg">
    <div class="bar">
      <div><h2 id="h-rrg">Sectors vs NIFTY 50</h2></div>
      <div class="seg" role="group" aria-label="Timeframe">
        <button data-tf="d" aria-pressed="true">Daily</button>
        <button data-tf="w" aria-pressed="false">Weekly</button>
      </div>
    </div>
    <p class="sub">Tap a sector to open it and highlight its path. Rotation usually runs clockwise: improving, leading, weakening, lagging.</p>
    <div class="tools" style="margin-bottom:8px">
      <label class="tog">Tail <select id="tail" aria-label="Tail length">
        <option value="1">Off</option><option value="3" selected>3 points</option><option value="4">4 points</option><option value="6">6 points</option><option value="10">10 points</option></select></label>
      <div class="qf" id="legend" role="group" aria-label="Show quadrants"></div>
    </div>
    <svg id="rrg-sec" class="rrg" role="img" aria-label="Relative rotation graph of sectors"></svg>
  </section>

  <section class="panel" aria-labelledby="h-sec">
    <h2 id="h-sec">All sectors</h2>
    <p class="sub">Equal-weight index of liquid stocks in each sector. Breadth is the share of stocks above their 50-day average.</p>
    <div class="tbl"><table id="t-sec"></table></div>
  </section>
</div>

<section class="panel" id="detail" aria-labelledby="h-det">
  <div class="bar">
    <div><h2 id="h-det"></h2><div class="sub" id="det-sub" style="margin:0"></div></div>
    <div class="tools">
      <select id="pick" aria-label="Choose sector"></select>
      <input type="search" id="q" placeholder="Find any stock" aria-label="Find any stock">
    </div>
  </div>
  <div class="kpis" id="kpis"></div>
  <div class="grid two">
    <div>
      <h2 style="font-size:1rem">Stocks vs their sector</h2>
      <p class="sub">Liquid stocks only, against the sector's own index.</p>
      <svg id="rrg-stk" class="rrg" role="img" aria-label="Relative rotation graph of stocks in the sector"></svg>
    </div>
    <div>
      <h2 style="font-size:1rem">Sector news, last 7 days</h2>
      <ul class="news" id="news"></ul>
    </div>
  </div>
  <div class="bar" style="margin-top:16px">
    <div class="seg" role="group" aria-label="Table view">
      <button data-view="tech" aria-pressed="true">Technicals</button>
      <button data-view="fund" aria-pressed="false">Fundamentals</button>
    </div>
    <label class="tog"><input type="checkbox" id="liq" checked> Liquid stocks only</label>
  </div>
  <div class="tbl"><table id="t-stk"></table></div>
  <button class="more" id="more" hidden>Show all</button>
</section>

<section class="panel" aria-labelledby="h-mov">
  <h2 id="h-mov">Big movers in the news</h2>
  <p class="sub">Headlines for today's largest liquid gainers and losers.</p>
  <ul class="news" id="movers"></ul>
</section>

<p class="note">RS-Ratio and RS-Momentum here are an open approximation of the JdK method, so readings will differ slightly from paid RRG tools. Prices and fundamentals come from Yahoo Finance and can have gaps, especially for small caps. For research only, not investment advice.</p>
</div>

<script>
const D = __DATA__;
const QC = {Leading:"--lead",Weakening:"--weak",Lagging:"--lag",Improving:"--impr"};
const SHORT = {"Automobile and Auto Components":"Auto","Capital Goods":"Capital goods","Fast Moving Consumer Goods":"FMCG",
 "Oil Gas & Consumable Fuels":"Oil & gas","Media Entertainment & Publication":"Media","Information Technology":"IT",
 "Financial Services":"Financials","Consumer Durables":"Durables","Consumer Services":"Consumer svcs",
 "Construction Materials":"Cement & materials","Metals & Mining":"Metals","Telecommunication":"Telecom","Forest Materials":"Forest"};
const short = s => SHORT[s] || s;
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const qcol = q => q ? css(QC[q]) : css("--muted");
const fmt = (v,d=1) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const sign = (v,d=1) => v==null ? "<td>–</td>" : `<td class="${v>0?'up':v<0?'down':''}">${v>0?'+':''}${fmt(v,d)}</td>`;
const esc = s => String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const tv = (sym, iv) => "https://www.tradingview.com/chart/?symbol=" + encodeURIComponent("NSE:" + sym.replace(/[&-]/g,"_")) + (iv ? "&interval=" + iv : "");
const scr = sym => "https://www.screener.in/company/" + encodeURIComponent(sym) + "/";
const tvLink = (sym, iv) => `<span class="lk"><a class="tv" href="${tv(sym, iv)}" target="_blank" rel="noopener" aria-label="Open ${esc(sym)} chart on TradingView" onclick="event.stopPropagation()">Chart</a><a class="tv" href="${scr(sym)}" target="_blank" rel="noopener" aria-label="Open ${esc(sym)} on Screener" onclick="event.stopPropagation()">Screener</a></span>`;
const chip = q => q ? `<span class="chip q-${q}">${q}</span>` : "–";

let picked = false, tf = "d", view = "tech", cur = null, showAll = false, tailLen = 3; const hiddenQ = new Set();
let secSort = {k:"r1d",dir:-1}, stkSort = {k:"r1d",dir:-1};
const bySec = {}; D.stocks.forEach(s => (bySec[s.sector] ??= []).push(s));

document.getElementById("gen").textContent = "Updated " + D.generated;
const b = D.bench || {};
document.getElementById("bench").innerHTML = b.price ? `NIFTY 50 ${fmt(b.price,0)} <span class="${b.r1d>=0?'up':'down'}">${b.r1d>0?'+':''}${fmt(b.r1d,2)}%</span> ·` : "";
function drawLegend(){
  const el = document.getElementById("legend");
  el.innerHTML = Object.keys(QC).map(q=>`<button data-q="${q}" aria-pressed="${!hiddenQ.has(q)}"><i class="dot" style="background:${qcol(q)}"></i>${q}</button>`).join("");
  el.querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{
    const q=b.dataset.q; hiddenQ.has(q)?hiddenQ.delete(q):hiddenQ.add(q);
    if (hiddenQ.size===4) hiddenQ.clear();
    drawLegend(); renderSectorRRG(); renderStocks(); }));
}
drawLegend();
document.getElementById("tail").addEventListener("change",e=>{ tailLen=+e.target.value; renderSectorRRG(); renderStocks(); });

/* ---------- RRG drawing ---------- */
function drawRRG(svg, items, opts={}){
  const W = Math.round(Math.max(340, Math.min(640, svg.clientWidth || 640))), H = Math.round(W*0.86), P = {l:30,r:12,t:14,b:30};
  svg.setAttribute("viewBox",`0 0 ${W} ${H}`);
  const tl = opts.tailLen ?? 5, sel = opts.sel;
  items = items.filter(i => !hiddenQ.has(i.q) || i.key===sel).map(i=>{
    const keep = i.key===sel ? Math.max(tl, 3) : Math.max(1, tl);
    const t = {x:i.tail.x.slice(-keep), y:i.tail.y.slice(-keep), d:(i.tail.d||[]).slice(-keep)};
    return {...i, tail:t};
  }).filter(i=>i.tail.x.length && i.tail.x.at(-1)!=null);
  if (!items.length){ svg.innerHTML = `<text x="${W/2}" y="${H/2}" text-anchor="middle" fill="${css('--muted')}" font-size="15">Nothing to plot with these filters.</text>`; return; }
  // robust scale: fit the heads fully, let long tails run off the edge
  const dev = (arr) => arr.map(v=>Math.abs(v-100)).filter(v=>!isNaN(v)).sort((a,b)=>a-b);
  const q = (arr,p) => arr.length ? arr[Math.min(arr.length-1, Math.floor(p*(arr.length-1)))] : 0;
  const hx = dev(items.map(i=>i.tail.x.at(-1))), hy = dev(items.map(i=>i.tail.y.at(-1)));
  const ax = dev(items.flatMap(i=>i.tail.x)), ay = dev(items.flatMap(i=>i.tail.y));
  const dx = Math.max(1.0, q(hx,1)*1.15, q(ax,.9)*1.1), dy = Math.max(1.0, q(hy,1)*1.15, q(ay,.9)*1.1);
  const clamp = (v,a,b)=>Math.min(b,Math.max(a,v));
  const X = v => clamp(P.l + (v-(100-dx))/(2*dx)*(W-P.l-P.r), P.l+2, W-P.r-2);
  const Y = v => clamp(H-P.b - (v-(100-dy))/(2*dy)*(H-P.t-P.b), P.t+2, H-P.b-2);
  const cx = X(100), cy = Y(100), mut = css("--muted"), line = css("--line");
  let g = "";
  const quad = [[cx,P.t,W-P.r-cx,cy-P.t,"Leading","end",W-P.r-8,P.t+18],[cx,cy,W-P.r-cx,H-P.b-cy,"Weakening","end",W-P.r-8,H-P.b-8],
                [P.l,cy,cx-P.l,H-P.b-cy,"Lagging","start",P.l+8,H-P.b-8],[P.l,P.t,cx-P.l,cy-P.t,"Improving","start",P.l+8,P.t+18]];
  quad.forEach(([x,y,w,h,qq,a,tx,ty])=>{ g += `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${qcol(qq)}" opacity=".07"/>
    <text x="${tx}" y="${ty}" text-anchor="${a}" font-size="13" font-weight="600" fill="${qcol(qq)}" opacity=".8">${qq}</text>`; });
  g += `<line x1="${cx}" x2="${cx}" y1="${P.t}" y2="${H-P.b}" stroke="${line}"/><line x1="${P.l}" x2="${W-P.r}" y1="${cy}" y2="${cy}" stroke="${line}"/>`;
  g += `<text x="${(W+P.l)/2}" y="${H-8}" text-anchor="middle" font-size="12" fill="${mut}">RS-Ratio (trend of relative strength)</text>
        <text transform="translate(12 ${(H-P.b+P.t)/2}) rotate(-90)" text-anchor="middle" font-size="12" fill="${mut}">RS-Momentum</text>`;
  // smooth curve through tail points (Catmull-Rom to Bezier)
  const curve = pts => { if (pts.length<2) return "";
    let d = `M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
    for (let i=0;i<pts.length-1;i++){ const p0=pts[i-1]||pts[i], p1=pts[i], p2=pts[i+1], p3=pts[i+2]||p2;
      d += ` C${(p1[0]+(p2[0]-p0[0])/6).toFixed(1)},${(p1[1]+(p2[1]-p0[1])/6).toFixed(1)} ${(p2[0]-(p3[0]-p1[0])/6).toFixed(1)},${(p2[1]-(p3[1]-p1[1])/6).toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`; }
    return d; };
  const labels = [], many = items.length > (opts.labelMax ?? 40);
  // draw the selected item last so it sits on top
  items.sort((a,b)=>(a.key===sel)-(b.key===sel));
  items.forEach(it=>{
    const t = it.tail, n = t.x.length, col = qcol(it.q), on = sel===it.key;
    const pts = t.x.map((x,k)=>[X(x),Y(t.y[k])]);
    const op = sel && !on ? .3 : 1;
    let s = `<g data-key="${esc(it.key)}" style="cursor:pointer" opacity="${op}" tabindex="0" role="button" aria-label="${esc(it.label)}, ${it.q}">`;
    if (n>1){
      s += `<path d="${curve(pts)}" fill="none" stroke="${col}" stroke-width="${on?2.6:1.3}" stroke-linecap="round" opacity="${on?.95:.45}"/>`;
      pts.slice(0,-1).forEach(([x,y],k)=>{ s+=`<circle cx="${x}" cy="${y}" r="${on?3:2}" fill="${col}" opacity="${.2+.6*k/n}"><title>${esc(it.label)} ${esc(t.d[k]||"")}</title></circle>`; });
    }
    const [hx2,hy2] = pts[n-1];
    s += `<circle cx="${hx2}" cy="${hy2}" r="${on?7.5:5.5}" fill="${col}" stroke="${css('--panel')}" stroke-width="1.5"/>`;
    s += `<title>${esc(it.label)}: ${it.q} (RS-Ratio ${fmt(t.x[n-1],2)}, Momentum ${fmt(t.y[n-1],2)})</title></g>`;
    g += s; if (!many || on) labels.push({x:hx2,y:hy2,text:it.label,on,op});
  });
  // label placement: try above, below, right, left; skip if no room (tooltip still works)
  const placed=[], lw = t => t.length*6.4+4;
  labels.sort((a,b)=>b.on-a.on);
  labels.forEach(l=>{ const w=lw(l.text);
    const tries=[[0,-10,"middle"],[0,17,"middle"],[w/2+8,4,"middle"],[-w/2-8,4,"middle"],[0,-23,"middle"],[0,30,"middle"]];
    for (const [ox,oy] of tries){ const x=clamp(l.x+ox, P.l+w/2, W-P.r-w/2), y=l.y+oy;
      if (y<P.t+10 || y>H-P.b-2) continue;
      if (placed.some(p=>Math.abs(p.x-x)<(w+p.w)/2 && Math.abs(p.y-y)<12)) continue;
      placed.push({x,y,w});
      g += `<text x="${x}" y="${y}" text-anchor="middle" font-size="${l.on?13:11.5}" font-weight="${l.on?700:500}" fill="${css('--ink')}" opacity="${l.op}" pointer-events="none" paint-order="stroke" stroke="${css('--panel')}" stroke-width="3">${esc(l.text)}</text>`;
      break; } });
  svg.innerHTML = g;
  svg.querySelectorAll("g[data-key]").forEach(el=>{
    const go = ()=>opts.onPick && opts.onPick(el.dataset.key);
    el.addEventListener("click",go); el.addEventListener("keydown",e=>{ if(e.key==="Enter"||e.key===" "){e.preventDefault();go();} });
  });
}

/* ---------- sector side ---------- */
function renderSectorRRG(){
  const items = D.sectors.filter(s=>s["rrg_"+tf]).map(s=>({key:s.sector,label:short(s.sector),tail:s["rrg_"+tf],q:s["q_"+tf]}));
  drawRRG(document.getElementById("rrg-sec"), items, {sel:picked?cur:null, tailLen, onPick:openSector});
}
const SCOLS = [["sector","Sector"],["q","Quadrant"],["r1d","1D %"],["r1w","1W %"],["r1m","1M %"],["r3m","3M %"],["above50","Breadth"],["ad","Adv / Dec"],["count","Stocks"]];
function renderSectorTable(){
  const rows = D.sectors.map(s=>({...s,q:s["q_"+tf],ad:s.adv-s.dec}));
  sortRows(rows, secSort);
  const t = document.getElementById("t-sec");
  t.innerHTML = `<thead><tr>${SCOLS.map(([k,l])=>`<th data-k="${k}" ${secSort.k===k?`aria-sort="${secSort.dir>0?'ascending':'descending'}"`:''}>${l}</th>`).join("")}</tr></thead><tbody>${
    rows.map(s=>`<tr data-s="${esc(s.sector)}" tabindex="0" class="${s.sector===cur?'on':''}"><td>${esc(short(s.sector))}</td><td>${chip(s.q)}</td>${sign(s.r1d,2)}${sign(s.r1w)}${sign(s.r1m)}${sign(s.r3m)}<td>${s.above50==null?'–':s.above50+'%'}</td><td><span class="up">${s.adv}</span> / <span class="down">${s.dec}</span></td><td>${s.count}</td></tr>`).join("")}</tbody>`;
  bindTable(t, secSort, renderSectorTable, tr=>openSector(tr.dataset.s));
}

/* ---------- detail ---------- */
const TECH = [["sym","Stock"],["price","Price"],["r1d","1D %"],["r1w","1W %"],["r1m","1M %"],["r3m","3M %"],["rsi","RSI"],["vs50","vs 50DMA"],["vs200","vs 200DMA"],["from_high","From 52w high"],["vol_x","Volume ×"],["q","RRG"]];
const FUND = [["sym","Stock"],["price","Price"],["mcap_cr","Mcap ₹cr"],["pe","P/E"],["pb","P/B"],["roe","ROE %"],["de","Debt/Eq"],["margin","Net margin %"],["rev_g","Revenue growth %"],["eps_g","Earnings growth %"],["r1y","1Y %"]];
function openSector(sec, focusSym, auto){
  if (!auto) picked = true;
  cur = sec; showAll = false;
  const s = D.sectors.find(x=>x.sector===sec) || {};
  document.getElementById("h-det").textContent = sec;
  document.getElementById("pick").value = sec;
  document.getElementById("det-sub").textContent = s["q_"+tf] ? `${s["q_"+tf]} on the ${tf==="d"?"daily":"weekly"} RRG` : "Too few liquid stocks for a sector RRG";
  document.getElementById("kpis").innerHTML = [["Stocks",s.count],["Liquid",s.liquid],["Above 50DMA",s.above50==null?"–":s.above50+"%"],["Above 200DMA",s.above200==null?"–":s.above200+"%"],["RSI",fmt(s.rsi)],["1M",s.r1m==null?"–":fmt(s.r1m)+"%"]].map(([k,v])=>`<span>${k} <b>${v??"–"}</b></span>`).join("");
  const news = (D.news||{})[sec]||[];
  document.getElementById("news").innerHTML = news.length ? news.map(n=>`<li><a href="${esc(n.u)}" target="_blank" rel="noopener">${esc(n.t)}</a><span>${esc(n.s)} ${esc(n.d)}</span></li>`).join("") : `<li class="empty">No headlines found for this sector this week.</li>`;
  renderStocks(focusSym); renderSectorRRG(); renderSectorTable();
}
function renderStockRRG(list, sel){
  const items = list.filter(s=>s["rrg_"+tf]).map(s=>({key:s.sym,label:s.sym,tail:s["rrg_"+tf],q:s["q_"+tf]}));
  drawRRG(document.getElementById("rrg-stk"), items, {tailLen: items.length<=15 ? tailLen : 1, labelMax:25, sel, onPick:k=>renderStocks(k)});
}
let selStock = null;
function renderStocks(focusSym){
  if (focusSym!==undefined) selStock = focusSym;
  const liqOnly = document.getElementById("liq").checked;
  let list = (bySec[cur]||[]).map(s=>({...s,q:s["q_"+tf]}));
  renderStockRRG(list, selStock);
  if (liqOnly) list = list.filter(s=>s.liquid || s.sym===selStock);
  sortRows(list, stkSort);
  if (selStock){ const i=list.findIndex(s=>s.sym===selStock); if(i>0) list.unshift(...list.splice(i,1)); }
  const cols = view==="tech"?TECH:FUND, LIMIT=120, shown = showAll?list:list.slice(0,LIMIT);
  const cell = (s,k)=>{
    if(k==="sym") return `<td class="name"><b>${esc(s.sym)}</b>${tvLink(s.sym, tf==="w"?"W":"D")}<small>${esc(s.industry&&s.industry!==s.sector?s.industry:s.name)}</small></td>`;
    if(k==="q") return `<td>${chip(s.q)}</td>`;
    if(["r1d","r1w","r1m","r3m","r1y","vs50","vs200","from_high","rev_g","eps_g"].includes(k)) return sign(s[k], k==="r1d"?2:1);
    if(k==="price") return `<td>${fmt(s.price,2)}</td>`;
    if(k==="mcap_cr") return `<td>${fmt(s.mcap_cr,0)}</td>`;
    if(k==="rsi") return `<td class="${s.rsi>=70?'down':s.rsi<=30?'up':''}">${fmt(s.rsi,0)}</td>`;
    return `<td>${fmt(s[k], k==="de"||k==="pb"?2:1)}</td>`; };
  const t = document.getElementById("t-stk");
  t.innerHTML = `<thead><tr>${cols.map(([k,l])=>`<th data-k="${k}" ${stkSort.k===k?`aria-sort="${stkSort.dir>0?'ascending':'descending'}"`:''}>${l}</th>`).join("")}</tr></thead><tbody>${
    shown.length ? shown.map(s=>`<tr data-sym="${esc(s.sym)}" tabindex="0" class="${s.sym===selStock?'on':''}">${cols.map(([k])=>cell(s,k)).join("")}</tr>`).join("") : `<tr><td class="empty" colspan="${cols.length}">No stocks match. Untick “Liquid stocks only” to see the rest.</td></tr>`}</tbody>`;
  bindTable(t, stkSort, ()=>renderStocks(), tr=>renderStocks(tr.dataset.sym===selStock?null:tr.dataset.sym));
  const m = document.getElementById("more"); m.hidden = showAll || list.length<=LIMIT; m.textContent = `Show all ${list.length}`;
}

/* ---------- shared ---------- */
function sortRows(rows, st){
  rows.sort((a,b)=>{ let x=a[st.k], y=b[st.k];
    if (st.k==="q"){ const o={Leading:0,Improving:1,Weakening:2,Lagging:3}; x=o[x]??9; y=o[y]??9; }
    if (x==null) return 1; if (y==null) return -1;
    return (typeof x==="string" ? x.localeCompare(y) : x-y) * st.dir; });
}
function bindTable(t, st, redraw, onRow){
  t.querySelectorAll("th").forEach(th=>th.addEventListener("click",()=>{ const k=th.dataset.k;
    st.dir = st.k===k ? -st.dir : (k==="sym"||k==="sector"||k==="q" ? 1 : -1); st.k=k; redraw(); }));
  t.querySelectorAll("tbody tr[data-s],tbody tr[data-sym]").forEach(tr=>{
    tr.addEventListener("click",()=>onRow(tr));
    tr.addEventListener("keydown",e=>{ if(e.key==="Enter"){ onRow(tr);} }); });
}
document.querySelectorAll("[data-tf]").forEach(bn=>bn.addEventListener("click",()=>{
  tf = bn.dataset.tf; document.querySelectorAll("[data-tf]").forEach(x=>x.setAttribute("aria-pressed",x===bn)); openSector(cur, selStock, !picked); }));
document.querySelectorAll("[data-view]").forEach(bn=>bn.addEventListener("click",()=>{
  view = bn.dataset.view; document.querySelectorAll("[data-view]").forEach(x=>x.setAttribute("aria-pressed",x===bn));
  stkSort = view==="fund" ? {k:"mcap_cr",dir:-1} : {k:"r1d",dir:-1}; renderStocks(); }));
document.getElementById("liq").addEventListener("change",()=>renderStocks());
document.getElementById("more").addEventListener("click",()=>{ showAll=true; renderStocks(); });
const pick = document.getElementById("pick");
pick.innerHTML = D.sectors.map(s=>`<option value="${esc(s.sector)}">${esc(short(s.sector))} (${s.count})</option>`).join("");
pick.addEventListener("change",()=>openSector(pick.value, null));
const q = document.getElementById("q");
q.addEventListener("keydown",e=>{ if(e.key!=="Enter") return; const v=q.value.trim().toUpperCase(); if(!v) return;
  const hit = D.stocks.find(s=>s.sym===v) || D.stocks.find(s=>s.sym.startsWith(v)) || D.stocks.find(s=>s.name.toUpperCase().includes(v));
  if (hit){ document.getElementById("liq").checked = hit.liquid; openSector(hit.sector, hit.sym); document.getElementById("detail").scrollIntoView({behavior:"smooth"}); }
  else q.setCustomValidity("No stock matches"), q.reportValidity(), setTimeout(()=>q.setCustomValidity(""),1500); });

const mv = D.movers||[];
document.getElementById("movers").innerHTML = mv.length ? mv.map(m=>`<li><b>${esc(m.sym)}</b>${tvLink(m.sym,"D")} <span style="display:inline" class="mut">${fmt(m.price,2)}</span> <span style="display:inline" class="${m.r1d>=0?'up':'down'}">${m.r1d>0?'+':''}${fmt(m.r1d,2)}%</span>${
  m.news.length ? m.news.slice(0,2).map(n=>`<br><a href="${esc(n.u)}" target="_blank" rel="noopener">${esc(n.t)}</a><span>${esc(n.s)} ${esc(n.d)}</span>`).join("") : `<span>No headlines found.</span>`}</li>`).join("") : `<li class="empty">No mover headlines in this run.</li>`;

const first = [...D.sectors].filter(s=>s.q_d).sort((a,b)=>(b.r1d??-99)-(a.r1d??-99))[0] || D.sectors[0];
openSector(first.sector, null, true);
let rz; addEventListener("resize",()=>{clearTimeout(rz); rz=setTimeout(()=>openSector(cur, selStock, !picked),200);});
</script>
</body>
</html>
"""
