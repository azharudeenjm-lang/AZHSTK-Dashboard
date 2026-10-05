"""Renders docs/setups.html: multi-timeframe trade setups."""
import json
from datetime import datetime, timedelta, timezone

from .config import DOCS, SETUP


def render(payload):
    DOCS.mkdir(parents=True, exist_ok=True)
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    payload["generated"] = ist.strftime("%d %b %Y, %I:%M %p IST")
    payload["cfg"] = SETUP
    blob = json.dumps(payload, separators=(",", ":"), allow_nan=False, default=str).replace("</", "<\\/")
    (DOCS / "setups.html").write_text(TEMPLATE.replace("__DATA__", blob), encoding="utf-8")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Trade setups: monthly, weekly, daily</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧭</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#EEF2F6;--panel:#FFFFFF;--ink:#16243A;--muted:#5C6B80;--line:#D3DBE5;--up:#1E8F5A;--down:#C2453B;--warn:#C9780F;--focus:#2F62C8;
  --b-ready:#1E8F5A;--b-set:#2F62C8;--b-watch:#6B4BB8;--b-avoid:#C2453B;
  --font:"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#111925;--panel:#18222F;--ink:#E5EBF3;--muted:#93A1B4;--line:#2A3646;--up:#3FBF85;--down:#E9675C;--warn:#E5A040;--focus:#6E97F0;
  --b-ready:#3FBF85;--b-set:#6E97F0;--b-watch:#9C82E6;--b-avoid:#E9675C}}
:root[data-theme="dark"]{--bg:#111925;--panel:#18222F;--ink:#E5EBF3;--muted:#93A1B4;--line:#2A3646;--up:#3FBF85;--down:#E9675C;--warn:#E5A040;--focus:#6E97F0;
  --b-ready:#3FBF85;--b-set:#6E97F0;--b-watch:#9C82E6;--b-avoid:#E9675C}
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
.tf{display:grid;gap:8px;grid-template-columns:minmax(0,1fr)}
@media(min-width:760px){.tf{grid-template-columns:repeat(3,minmax(0,1fr))}}
.tf div{border:1px solid var(--line);border-radius:10px;padding:10px 12px;font-size:.86rem}
.tf b{display:block;font-size:.95rem}.tf span{color:var(--muted)}
.bk{display:grid;gap:10px;grid-template-columns:repeat(2,minmax(0,1fr))}
@media(min-width:760px){.bk{grid-template-columns:repeat(4,minmax(0,1fr))}}
.b{border:1px solid var(--line);border-top:5px solid var(--c);border-radius:12px;padding:10px 12px;background:var(--panel);text-align:left;font:inherit;color:var(--ink);cursor:pointer}
.b .n{font-size:1.8rem;font-weight:700;line-height:1.1;display:block}.b .t{font-weight:600}.b small{display:block;color:var(--muted);font-size:.76rem}
.b[aria-pressed="true"]{background:color-mix(in srgb,var(--c) 12%,var(--panel));border-color:var(--c)}
.tools{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px}
select,input{font:inherit;font-size:.86rem;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 9px;max-width:100%}
input[type=number]{width:120px}
label.tog{font-size:.85rem;color:var(--muted);display:flex;gap:6px;align-items:center}
button:focus-visible,select:focus-visible,input:focus-visible,a:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{padding:8px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line);vertical-align:top}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--panel);z-index:1}
td.l,th.l{text-align:left}
th{color:var(--muted);font-weight:500;cursor:pointer;user-select:none;background:var(--panel)}
th[aria-sort]::after{content:" ↓";font-size:.75em}th[aria-sort="ascending"]::after{content:" ↑"}
.name small{display:block;color:var(--muted);font-size:.75rem;max-width:170px;overflow:hidden;text-overflow:ellipsis}
.chip{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.74rem;font-weight:600;color:#fff;background:var(--c);white-space:nowrap}
.ck{display:flex;gap:6px;align-items:flex-start;white-space:normal;min-width:190px;max-width:260px}
.ck i{font-style:normal;font-weight:700;width:18px;flex-shrink:0;text-align:center}
.ck small{display:block;color:var(--muted);font-size:.76rem;line-height:1.3}
.ok{color:var(--up)}.mid{color:var(--warn)}.bad{color:var(--down)}.mut{color:var(--muted)}
.dots{display:inline-flex;gap:3px;vertical-align:middle}.dots i{width:8px;height:8px;border-radius:50%;background:var(--line)}.dots i.on{background:var(--up)}
.lk{white-space:nowrap}.lk a{font-size:.72rem;font-weight:600;color:var(--focus);text-decoration:none;border:1px solid currentColor;border-radius:6px;padding:0 5px;margin-left:6px}
button.psym{all:unset;font-weight:700;cursor:pointer;border-bottom:1px dotted currentColor}
.more{margin-top:10px;font:500 .85rem var(--font);background:transparent;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:6px 12px;cursor:pointer}
.note{color:var(--muted);font-size:.8rem;max-width:80ch}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Trade setups</h1>
  <div id="gsearch"></div>
  <nav aria-label="Dashboards"><a href="index.html">Sector rotation</a><a href="zones.html">Zones</a><a href="levels.html">Levels</a><a href="setups.html" aria-current="page">Setups</a><a href="watchlist.html">My list</a><a href="backtest.html">Backtest</a></nav>
</header>
<p class="stamp" id="gen"></p>



<section class="panel">
  <div class="bk" id="bk"></div>
</section>

<section class="panel">
  <details><summary style="cursor:pointer;font-weight:600">Three timeframes, three jobs</summary>
  <div class="tf" style="margin-top:10px">
    <div><b>Monthly: the tide</b><span>Is it safe to be long? Price above its 10-month average, monthly RSI 50 or higher, monthly MACD rising.</span></div>
    <div><b>Weekly: the setup</b><span>A fresh trend (Accumulation → Bullish), fresh strong momentum, a pullback inside a Bullish trend, or a weekly breakout.</span></div>
    <div><b>Daily: the timing</b><span>Not overheated today. Best at support, on a breakout, or above last week's high. A daily Divergence zone or Extended means wait.</span></div>
  </div></details>
</section>

<section class="panel" id="list">
  <h2 id="lh"></h2>
  <p class="sub" id="ls"></p>
  <div class="tools">
    <label class="tog">Capital ₹ <input type="number" id="cap" min="0" step="10000" inputmode="numeric" aria-label="Capital in rupees"></label>
    <label class="tog">Risk per trade <input type="number" id="risk" min="0.1" max="5" step="0.1" inputmode="decimal" aria-label="Risk per trade in percent" style="width:70px">%</label>
    <select id="f-wk" aria-label="Weekly setup"><option value="">Any weekly setup</option><option>Fresh trend</option><option>Breakout</option><option>Pullback</option><option>Momentum</option><option>Base</option><option>In trend</option></select>
    <select id="f-rs" aria-label="Minimum relative strength"><option value="0">Any RS</option><option value="50">RS 50+</option><option value="70">RS 70+</option><option value="80">RS 80+ (top 20%)</option><option value="90">RS 90+</option></select>
    <select id="f-sec" aria-label="Sector"></select>
    <label class="tog"><input type="checkbox" id="noearn"> Hide results within 2 weeks</label>
    <input type="search" id="q" placeholder="Find a stock" aria-label="Find a stock">
    <label class="tog"><input type="checkbox" id="liq" checked> Liquid only</label>
  </div>
  <div class="tbl"><table id="t"></table></div>
  <button class="more" id="more" hidden></button>
</section>

<section class="panel">
  <h2>How to read this</h2>
  <ul class="note">
    <li><b>Ready</b> means all three timeframes agree today, the sector isn't lagging, and there's a sensible stop. It is a shortlist to check on the chart, not a buy order.</li>
    <li><b>Setting up</b> means the weekly setup is there but something is not yet in line, usually the daily is overheated. These often become Ready after a few days' dip.</li>
    <li><b>RS</b> ranks each stock's 3, 6, 9 and 12-month performance against all liquid stocks: 90 means stronger than 90% of the market. <b>Target</b> is the first Fibonacci target on the weekly chart (prior high, projection or extension); <b>R:R</b> compares it with the stop.</li>
    <li>In a <b>risk-off</b> market, Ready also needs a Leading or Improving sector and RS 70+. Stocks with results due within 2 weeks move to Setting up.</li>
    <li><b>Stop</b> is the highest of the recent daily swing low, the weekly Kijun line and daily support that sits between 1.5% and 15% below the price. <b>Resistance</b> is the distance to the next weekly resistance; "clear" means none overhead.</li>
    <li><b>Quantity</b> is sized so that hitting the stop loses your chosen risk % of capital. Your capital and risk settings stay on this device only.</li>
    <li>Weekly and monthly bars include the period in progress, so they can change before the week or month closes. For research only, not investment advice.</li>
  </ul>
</section>
</div>

<script>
const D = __DATA__;
const BK = [["Ready","--b-ready","all three timeframes agree"],["Setting up","--b-set","weekly setup, waiting on daily"],["Watchlist","--b-watch","weekly base in a monthly uptrend"],["Avoid","--b-avoid","divergence, broken or against the tide"]];
const QC = {Leading:"--b-ready",Improving:"--b-set",Weakening:"--warn",Lagging:"--b-avoid"};
const esc = s => String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v,d=1) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const tv = s => "https://www.tradingview.com/chart/?symbol=" + encodeURIComponent("NSE:" + s.replace(/[&-]/g,"_")) + "&interval=W";
const scr = s => "https://www.screener.in/company/" + encodeURIComponent(s) + "/";
const mark = st => st==="OK"||st==="Good" ? ['✓','ok'] : st==="Mixed"||st==="Wait"||st==="Neutral" ? ['~','mid'] : st==="No data" ? ['?','mut'] : ['✗','bad'];
const store = { get(k,d){ try { const v = localStorage.getItem("setups:"+k); return v==null ? d : v; } catch(e){ return d; } },
                set(k,v){ try { localStorage.setItem("setups:"+k, v); } catch(e){} } };

document.getElementById("gen").textContent = `Updated ${D.generated}. Weekly and monthly bars include the period in progress.`;
let bucket = "Ready", sort = {k:"score",dir:-1}, showAll = false;
const cap = document.getElementById("cap"), risk = document.getElementById("risk");
cap.value = store.get("cap","500000"); risk.value = store.get("risk","1");

function base(){
  const liq = document.getElementById("liq").checked, sec = document.getElementById("f-sec").value,
        wk = document.getElementById("f-wk").value, q = document.getElementById("q").value.trim().toUpperCase(),
        mrs = +document.getElementById("f-rs").value, ne = document.getElementById("noearn").checked;
  return D.stocks.filter(s => (!liq || s.liquid) && (!sec || s.sector===sec) && (!wk || s.wk===wk)
    && (!mrs || (s.rs||0) >= mrs) && (!ne || !s.earn_soon)
    && (!q || s.sym.includes(q) || s.name.toUpperCase().includes(q)));
}
function drawBuckets(){
  const b = base();
  document.getElementById("bk").innerHTML = BK.map(([k,c,d])=>`<button class="b" style="--c:var(${c})" data-b="${k}" aria-pressed="${bucket===k}"><span class="n">${b.filter(s=>s.bucket===k).length}</span><span class="t">${k}</span><small>${d}</small></button>`).join("");
  document.querySelectorAll(".b").forEach(el=>el.addEventListener("click",()=>{ bucket = el.dataset.b; showAll=false; drawAll(); }));
}
const ck = (st, title, txt) => { const [i,c] = mark(st); return `<td class="l"><div class="ck"><i class="${c}" aria-label="${esc(st)}">${i}</i><div>${esc(title)}<small>${esc(txt)}</small></div></div></td>`; };
const COLS = [["sym","Stock"],["price","Price"],["score","Score"],["rs","RS"],["mon","Monthly","l"],["wk","Weekly","l"],["day","Daily","l"],["q","Sector","l"],["stop_pct","Stop"],["t1u","Target"],["rr","R:R"],["room","Resistance"],["qty","Qty"]];
function drawTable(){
  const C = +cap.value||0, R = (+risk.value||0)/100;
  let L = base().filter(s=>s.bucket===bucket).map(s=>({...s, t1u: s.t1 ? s.t1.up : null, qty: s.stop && s.price>s.stop ? Math.floor(C*R/(s.price-s.stop)) : null}));
  L.sort((a,b)=>{ const x=a[sort.k], y=b[sort.k]; if (x==null) return 1; if (y==null) return -1;
    const r = (typeof x==="string" ? x.localeCompare(y) : x-y) * sort.dir; return r || (b.score-a.score) || ((b.rr??0)-(a.rr??0)); });
  const bk = BK.find(b=>b[0]===bucket);
  document.getElementById("lh").textContent = `${bucket}: ${L.length} ${L.length===1?"stock":"stocks"}`;
  document.getElementById("ls").textContent = {Ready:"All three timeframes line up today. Check each chart before acting.",
    "Setting up":"The weekly setup is in place; the reason it isn't Ready yet is shown under the stock name.",
    Watchlist:"A weekly base is forming while the monthly trend is up. Watch for Accumulation → Bullish.",
    Avoid:"Weekly Divergence zone, Bearish or Oversold, or a weekly setup fighting a weak monthly trend."}[bucket];
  const LIM = 150, S = showAll ? L : L.slice(0, LIM);
  const t = document.getElementById("t");
  t.innerHTML = `<thead><tr>${COLS.map(([k,l,c])=>`<th class="${c||''}" data-k="${k}" ${sort.k===k?`aria-sort="${sort.dir>0?'ascending':'descending'}"`:''}>${l}</th>`).join("")}</tr></thead><tbody>${
    S.map(s=>`<tr>
      <td class="name"><button class="psym" data-p="${esc(s.sym)}">${esc(s.sym)}</button><span class="lk"><a href="${tv(s.sym)}" target="_blank" rel="noopener">Chart</a><a href="${scr(s.sym)}" target="_blank" rel="noopener">Screener</a></span>
        <small>${esc(s.sector)}</small>${s.earn_soon?`<small style="color:var(--warn);font-weight:600">⚠ results in ${s.edays} ${s.edays===1?"day":"days"}</small>`:""}${bucket!=="Ready"?`<small style="max-width:200px;white-space:normal">${esc(s.why)}</small>`:""}</td>
      <td>${fmt(s.price,2)}</td>
      <td><span class="dots" aria-label="Score ${s.score} of 6">${[0,1,2,3,4,5].map(i=>`<i class="${i < Math.round(s.score) ? 'on':''}"></i>`).join("")}</span></td>
      <td class="${s.rs>=80?'ok':s.rs!=null&&s.rs<50?'bad':''}">${s.rs??"–"}</td>
      ${ck(s.mon, {OK:"Monthly uptrend",Mixed:"Monthly mixed",Weak:"Monthly weak"}[s.mon]||"No monthly data", s.mon_txt)}
      ${ck(s.wk_ok?"OK":s.wk==="Base"||s.wk==="In trend"?"Mixed":"Weak", s.wk||"No setup", s.wk_txt)}
      ${ck(s.day, s.day==="Good"?"Timing good":s.day==="Wait"?"Wait":s.day==="Weak"?"Weak":"Neutral", s.day_txt)}
      <td class="l">${s.q?`<span class="chip" style="--c:var(${QC[s.q]||'--muted'})">${esc(s.q)}</span>`:'<span class="mut">–</span>'}</td>
      <td>${s.stop?`₹${fmt(s.stop,2)}<small class="mut" style="display:block">−${fmt(s.stop_pct)}% · ${esc(s.stop_from)}</small>`:'<span class="mut">none</span>'}</td>
      <td>${s.t1?`₹${fmt(s.t1.p,2)} <span class="ok">+${fmt(s.t1.up)}%</span><small class="mut" style="display:block">${esc(s.t1.k)}${s.t2?` · T2 ₹${fmt(s.t2.p,0)}`:""}</small>`:'<span class="mut">–</span>'}</td>
      <td class="${s.rr==null?'mut':s.rr>=D.cfg.good_rr?'ok':'mid'}">${s.rr!=null?fmt(s.rr)+"×":"–"}</td>
      <td>${s.room!=null?`+${fmt(s.room)}%<small class="mut" style="display:block">₹${fmt(s.res,2)}</small>`:'<span class="mut">clear</span>'}</td>
      <td>${s.qty!=null?s.qty.toLocaleString("en-IN"):"–"}</td></tr>`).join("")
    || `<tr><td class="mut" colspan="${COLS.length}">Nothing in this group with these filters today.</td></tr>`}</tbody>`;
  t.querySelectorAll("th").forEach(th=>th.addEventListener("click",()=>{ const k=th.dataset.k;
    sort.dir = sort.k===k ? -sort.dir : (["sym","mon","wk","day","q","stop_pct","room"].includes(k) && k!=="room" ? 1 : -1); sort.k=k; drawTable(); }));
  const m = document.getElementById("more"); m.hidden = showAll || L.length<=LIM; m.textContent = `Show all ${L.length}`;
}
function drawAll(){ drawBuckets(); drawTable(); }
const fs = document.getElementById("f-sec");
fs.innerHTML = `<option value="">All sectors</option>` + [...new Set(D.stocks.map(s=>s.sector))].sort().map(s=>`<option>${esc(s)}</option>`).join("");
["f-sec","f-wk","liq","f-rs","noearn"].forEach(id=>document.getElementById(id).addEventListener("change",()=>{ showAll=false; drawAll(); }));
document.getElementById("q").addEventListener("input",()=>{ showAll=false; drawAll(); });
[cap,risk].forEach(el=>el.addEventListener("input",()=>{ store.set(el.id, el.value); drawTable(); }));
document.getElementById("more").addEventListener("click",()=>{ showAll=true; drawTable(); });
drawAll();
</script>
<script src="profile.js" defer></script>
</body>
</html>
"""
