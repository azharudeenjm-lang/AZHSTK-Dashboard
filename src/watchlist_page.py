"""Renders docs/watchlist.html: your watchlist and trade tracker.

Everything you enter is stored in this browser only (localStorage). The page
pulls each stock's latest data from the daily files (p/*.json) and checks
your trades against stops, targets and zone changes. Use Export / Import to
move your list to another device.
"""
from .config import DOCS


def render():
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "watchlist.html").write_text(TEMPLATE, encoding="utf-8")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>My list: watchlist and trades</title>
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
.kpis{display:grid;gap:10px;grid-template-columns:repeat(2,minmax(0,1fr));margin-bottom:12px}
@media(min-width:760px){.kpis{grid-template-columns:repeat(4,minmax(0,1fr))}}
.kpi{border:1px solid var(--line);border-radius:12px;padding:10px 12px}.kpi>span{display:block;color:var(--muted);font-size:.76rem}.kpi b{font-size:1.25rem}
.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{padding:8px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line);vertical-align:top}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--panel);z-index:1}
td.l,th.l{text-align:left}
th{color:var(--muted);font-weight:500;background:var(--panel)}
.name small{display:block;color:var(--muted);font-size:.75rem;max-width:170px;overflow:hidden;text-overflow:ellipsis}
button.psym{all:unset;font-weight:700;cursor:pointer;border-bottom:1px dotted currentColor}
.chip{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.74rem;font-weight:600;color:#fff;background:var(--c);white-space:nowrap;margin:1px 2px 1px 0}
.w{display:flex;flex-wrap:wrap;gap:4px;white-space:normal;max-width:300px}
.wa{font-size:.74rem;font-weight:600;border-radius:6px;padding:1px 7px;border:1px solid currentColor}
.wa.red{color:var(--down)}.wa.amb{color:var(--warn)}.wa.grn{color:var(--up)}.wa.mut{color:var(--muted)}
.up{color:var(--up)}.down{color:var(--down)}.mut{color:var(--muted)}
.btn{font:600 .8rem var(--font);border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:8px;padding:5px 10px;cursor:pointer}
.btn:focus-visible,button.psym:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.empty{color:var(--muted);padding:14px 0}
textarea{width:100%;min-height:90px;font:12px/1.4 ui-monospace,Menlo,Consolas,monospace;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>My list</h1>
  <div id="gsearch"></div>
  <nav aria-label="Dashboards"><a href="index.html">Sector rotation</a><a href="zones.html">Zones</a><a href="levels.html">Levels</a><a href="setups.html">Setups</a><a href="watchlist.html" aria-current="page">My list</a><a href="backtest.html">Backtest</a></nav>
</header>
<p class="stamp">Search any stock, open it, then tap ☆ Watch or + Track trade. Your list is saved on this device only; use Backup to move it.</p>

<section class="panel" aria-labelledby="h-open">
  <h2 id="h-open">Open trades</h2>
  <div class="kpis" id="kpis"></div>
  <div class="tbl"><table id="t-open"></table></div>
</section>

<section class="panel" aria-labelledby="h-watch">
  <h2 id="h-watch">Watchlist</h2>
  <div class="tbl"><table id="t-watch"></table></div>
</section>

<section class="panel" aria-labelledby="h-closed">
  <h2 id="h-closed">Closed trades</h2>
  <div class="tbl"><table id="t-closed"></table></div>
</section>

<section class="panel" aria-labelledby="h-bak">
  <h2 id="h-bak">Backup</h2>
  <p class="sub">Your list lives in this browser. To use it on another phone or laptop, export here and import there.</p>
  <div class="row"><button class="btn" id="exp">Download backup file</button><button class="btn" id="copy">Copy backup text</button>
    <label class="btn" style="display:inline-block">Import file<input type="file" id="imp" accept="application/json,.json" hidden></label></div>
  <p class="sub" style="margin-top:10px">Or paste backup text and tap Import:</p>
  <textarea id="paste" aria-label="Paste backup text"></textarea>
  <div class="row" style="margin-top:8px"><button class="btn" id="imp2">Import pasted text</button><span class="mut" id="msg" role="status"></span></div>
</section>
</div>

<script src="profile.js"></script>
<script>
const WL = window.AZH_WL;
const esc = s => String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v,d=1) => v==null||isNaN(v) ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const pc = (v,d=1) => v==null||isNaN(v) ? '<span class="mut">–</span>' : `<span class="${v>0?'up':v<0?'down':''}">${v>0?'+':''}${fmt(v,d)}%</span>`;
const rs = v => { if (v==null||isNaN(v)) return '<span class="mut">–</span>'; if (Math.abs(v) < 0.5) return "₹0";
  return `<span class="${v>0?'up':'down'}">${v>0?'+':'−'}₹${fmt(Math.abs(v),0)}</span>`; };
const dl = s => s ? new Date(s+"T00:00:00").toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"2-digit"}) : "";
const ZC = {"Bearish":"#C2453B","Oversold":"#6B4BB8","Accumulation":"#2F62C8","Bullish":"#1E8F5A","Overbought":"#C9780F","Danger zone":"#A8285E","Neutral":"#8C99AB"};
const BC = {"Ready":"#1E8F5A","Setting up":"#2F62C8","Watchlist":"#6B4BB8","Avoid":"#C2453B"};
const chip = (t,c) => t ? `<span class="chip" style="--c:${c||'#8C99AB'}">${esc(t)}</span>` : '<span class="mut">–</span>';
const shard = s => s.toUpperCase().replace(/[^A-Z0-9]/g,"").slice(0,2) || "0";
const cache = {};
function getStock(sym){ const k = shard(sym);
  if (!cache[k]) cache[k] = fetch(`p/${k}.json`).then(r=>r.ok?r.json():{}).catch(()=>({}));
  return cache[k].then(m=>m[sym]); }
const ddays = d => d ? Math.round((new Date(d+"T00:00:00") - new Date(new Date().toDateString()))/864e5) : null;

function warnings(t, p){
  const out = [], px = p.px, zw = (p.z||{}).w || {}, zd = (p.z||{}).d || {};
  if (t.stop && px <= t.stop) out.push(["red","Stop hit"]);
  else if (t.stop && (px/t.stop-1)*100 <= 3) out.push(["amb","Near stop"]);
  if (t.target && px >= t.target) out.push(["grn","Target reached"]);
  const after = (zw.segs||[]).filter(g => g[2] >= t.date);
  if (after.some(g=>g[0]==="D") && zw.zone !== "Danger zone") out.push(["red","Cooled from Danger: exit signal"]);
  if (["Neutral","Bearish","Oversold"].includes(zw.zone)) out.push(["red",`Weekly ${zw.zone.toLowerCase()}: trend broke`]);
  if (zw.zone === "Danger zone") out.push(["amb","Weekly Danger zone: tighten stop"]);
  if (["Overbought","Danger zone"].includes(zd.zone)) out.push(["amb","Daily overheated: consider partial profit"]);
  const e = ddays(p.earn); if (e!=null && e>=0 && e<=14) out.push(["amb",`Results in ${e} ${e===1?"day":"days"}`]);
  if (!out.length) out.push(["mut","No warnings"]);
  return out;
}

async function draw(){
  const d = WL.get(), open = d.trades.filter(t=>!t.closed), closed = d.trades.filter(t=>t.closed);
  const syms = [...new Set([...open.map(t=>t.sym), ...Object.keys(d.watch)])];
  const P = {}; await Promise.all(syms.map(s=>getStock(s).then(p=>{ P[s]=p; })));

  // ---- open trades ----
  let inv = 0, val = 0, risk = 0;
  const to = document.getElementById("t-open");
  to.innerHTML = `<thead><tr><th>Stock</th><th>Entry</th><th>Qty</th><th>Now</th><th>P&amp;L</th><th>Stop</th><th>Target</th><th class="l">Weekly zone</th><th class="l">Warnings</th><th></th></tr></thead><tbody>${
    open.map(t=>{ const p = P[t.sym]; if (!p) return `<tr><td class="name"><b>${esc(t.sym)}</b><small>no data today</small></td><td colspan="9" class="l mut">This stock is not in today's data.</td></tr>`;
      const pl = (p.px/t.price-1)*100, q = t.qty||0; inv += q*t.price; val += q*p.px; if (t.stop) risk += Math.max(0, q*(p.px - t.stop));
      return `<tr><td class="name"><button class="psym" data-p="${esc(t.sym)}">${esc(t.sym)}</button><small>${esc(p.sec)}</small>${t.note?`<small>${esc(t.note)}</small>`:""}</td>
        <td>₹${fmt(t.price,2)}<small class="mut" style="display:block">${dl(t.date)}</small></td><td>${t.qty??"–"}</td><td>₹${fmt(p.px,2)}</td>
        <td>${pc(pl)}<small style="display:block">${q?rs(q*(p.px-t.price)):""}</small></td>
        <td>${t.stop?`₹${fmt(t.stop,2)}<small class="mut" style="display:block">${fmt((p.px/t.stop-1)*100)}% away</small>`:'<span class="mut">–</span>'}</td>
        <td>${t.target?`₹${fmt(t.target,2)}<small class="mut" style="display:block">${fmt((t.target/p.px-1)*100)}% to go</small>`:'<span class="mut">–</span>'}</td>
        <td class="l">${chip(((p.z||{}).w||{}).zone, ZC[((p.z||{}).w||{}).zone])}</td>
        <td class="l"><div class="w">${warnings(t,p).map(([c,x])=>`<span class="wa ${c}">${esc(x)}</span>`).join("")}</div></td>
        <td><button class="btn" data-close="${t.id}">Close</button></td></tr>`; }).join("")
    || `<tr><td colspan="10" class="empty">No open trades. Open any stock and tap “+ Track trade”.</td></tr>`}</tbody>`;
  document.getElementById("kpis").innerHTML = [["Open trades", open.length],["Invested", inv?`₹${fmt(inv,0)}`:"–"],["Unrealised P&L", inv?`${rs(val-inv)} ${pc((val/inv-1)*100)}`:"–"],["At risk if all stops hit", risk?`₹${fmt(risk,0)}`:"–"]]
    .map(([k,v])=>`<div class="kpi"><span>${k}</span><b>${v}</b></div>`).join("");

  // ---- watchlist ----
  const tw = document.getElementById("t-watch"), ws = Object.keys(d.watch).sort();
  tw.innerHTML = `<thead><tr><th>Stock</th><th>Price</th><th>1D</th><th class="l">Weekly zone</th><th class="l">Setup</th><th>RS</th><th class="l">Fibonacci (weekly)</th><th>Next results</th><th></th></tr></thead><tbody>${
    ws.map(s=>{ const p = P[s]; if (!p) return `<tr><td class="name"><b>${esc(s)}</b></td><td colspan="7" class="l mut">Not in today's data</td><td><button class="btn" data-unwatch="${esc(s)}">Remove</button></td></tr>`;
      const zw = (p.z||{}).w || {}, su = p.su || {}, fw = (p.fib||{}).w, e = ddays(p.earn);
      return `<tr><td class="name"><button class="psym" data-p="${esc(s)}">${esc(s)}</button><small>${esc(p.sec)}</small></td>
        <td>₹${fmt(p.px,2)}</td><td>${pc(p.r1d,2)}</td>
        <td class="l">${chip(zw.zone, ZC[zw.zone])}<small class="mut" style="display:block">${zw.capped?"long-standing":zw.since?"since "+dl(zw.since):""}${zw.move!=null?` · ${zw.move>0?"+":""}${fmt(zw.move)}% since entry`:""}</small></td>
        <td class="l">${chip(su.bucket, BC[su.bucket])}<small class="mut" style="display:block;max-width:200px;white-space:normal">${esc(su.bucket?su.why:"")}</small></td>
        <td>${p.rs??"–"}</td>
        <td class="l">${fw?`${esc(fw.status)}${fw.t&&fw.t[0]?`<small class="mut" style="display:block">T1 ₹${fmt(fw.t[0].p,2)} (+${fmt(fw.t[0].up)}%)</small>`:""}`:'<span class="mut">–</span>'}</td>
        <td>${p.earn?`${dl(p.earn)}${e!=null&&e>=0&&e<=14?`<small style="display:block;color:var(--warn)">in ${e} days</small>`:""}`:'<span class="mut">–</span>'}</td>
        <td><button class="btn" data-unwatch="${esc(s)}">Remove</button></td></tr>`; }).join("")
    || `<tr><td colspan="9" class="empty">Nothing on your watchlist yet. Open any stock and tap “☆ Watch”.</td></tr>`}</tbody>`;

  // ---- closed ----
  const tc = document.getElementById("t-closed");
  const wins = closed.filter(t=>t.exitPrice>t.price).length, tot = closed.reduce((a,t)=>a+(t.qty||0)*(t.exitPrice-t.price),0);
  tc.innerHTML = `<thead><tr><th>Stock</th><th>Entry</th><th>Exit</th><th>Return</th><th>P&amp;L</th><th></th></tr></thead><tbody>${
    closed.slice().reverse().map(t=>`<tr><td class="name"><button class="psym" data-p="${esc(t.sym)}">${esc(t.sym)}</button>${t.note?`<small>${esc(t.note)}</small>`:""}</td>
      <td>₹${fmt(t.price,2)}<small class="mut" style="display:block">${dl(t.date)}</small></td><td>₹${fmt(t.exitPrice,2)}<small class="mut" style="display:block">${dl(t.exitDate)}</small></td>
      <td>${pc((t.exitPrice/t.price-1)*100)}</td><td>${t.qty?rs(t.qty*(t.exitPrice-t.price)):"–"}</td><td><button class="btn" data-del="${t.id}">Delete</button></td></tr>`).join("")
    || `<tr><td colspan="6" class="empty">No closed trades yet.</td></tr>`}</tbody>${closed.length?`<tfoot><tr><td><b>${closed.length} trades</b></td><td colspan="2">${fmt(wins/closed.length*100,0)}% winners</td><td></td><td>${rs(tot)}</td><td></td></tr></tfoot>`:""}`;

  document.querySelectorAll("[data-close]").forEach(b=>b.onclick=()=>{ const d2 = WL.get(), t = d2.trades.find(x=>String(x.id)===b.dataset.close); if (!t) return;
    const now = (P[t.sym]||{}).px; const v = prompt(`Exit price for ${t.sym}`, now ?? t.price); if (v===null) return;
    const ex = parseFloat(v); if (isNaN(ex)) return; t.closed = true; t.exitPrice = ex; t.exitDate = new Date().toISOString().slice(0,10); WL.save(d2); draw(); });
  document.querySelectorAll("[data-unwatch]").forEach(b=>b.onclick=()=>{ const d2 = WL.get(); delete d2.watch[b.dataset.unwatch]; WL.save(d2); draw(); });
  document.querySelectorAll("[data-del]").forEach(b=>b.onclick=()=>{ if (!confirm("Delete this closed trade?")) return; const d2 = WL.get(); d2.trades = d2.trades.filter(x=>String(x.id)!==b.dataset.del); WL.save(d2); draw(); });
}

// backup
const msg = t => { document.getElementById("msg").textContent = t; };
document.getElementById("exp").onclick = () => { const blob = new Blob([JSON.stringify(WL.get(), null, 1)], {type:"application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `my-list-${new Date().toISOString().slice(0,10)}.json`; document.body.appendChild(a); a.click(); a.remove(); };
document.getElementById("copy").onclick = () => { navigator.clipboard.writeText(JSON.stringify(WL.get())).then(()=>msg("Copied. Paste it on the other device."), ()=>msg("Couldn't copy; use the download instead.")); };
function doImport(text){ try { const d = JSON.parse(text); if (typeof d!=="object" || !d) throw 0;
    const cur = WL.get(); d.watch = {...cur.watch, ...(d.watch||{})};
    const ids = new Set(cur.trades.map(t=>String(t.id))); d.trades = [...cur.trades, ...(d.trades||[]).filter(t=>!ids.has(String(t.id)))];
    WL.save(d); msg("Imported and merged with what was already here."); draw(); } catch(e){ msg("That doesn't look like a backup from this page."); } }
document.getElementById("imp").onchange = e => { const f = e.target.files[0]; if (f) f.text().then(doImport); };
document.getElementById("imp2").onclick = () => doImport(document.getElementById("paste").value);
document.addEventListener("visibilitychange", () => { if (!document.hidden) draw(); });
document.addEventListener("close", draw, true);   // pop-up edits refresh the list when it closes
draw();
</script>
</body>
</html>
"""
