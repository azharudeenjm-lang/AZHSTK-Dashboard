"""Renders docs/forward.html: the Forward test tab (paper trading the Buy criteria rule)."""
import json
from datetime import datetime, timedelta, timezone

from .config import DOCS
from .setups_page import TEMPLATE as _SETUPS


def render(payload):
    DOCS.mkdir(parents=True, exist_ok=True)
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    payload["generated"] = ist.strftime("%d %b %Y, %I:%M %p IST")
    blob = json.dumps(payload, separators=(",", ":"), allow_nan=False, default=str).replace("</", "<\\/")
    head = _SETUPS[:_SETUPS.index("</style>")].replace("<title>Trade setups: monthly, weekly, daily</title>", "<title>Forward test</title>")
    (DOCS / "forward.html").write_text(head + TEMPLATE.replace("__DATA__", blob), encoding="utf-8")


TEMPLATE = r"""
.kpi{display:grid;gap:10px;grid-template-columns:repeat(2,minmax(0,1fr))}
@media(min-width:760px){.kpi{grid-template-columns:repeat(4,minmax(0,1fr))}}
.kpi div{border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.kpi b{display:block;font-size:1.35rem}.kpi small{color:var(--muted);font-size:.76rem}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
.tabs button{font:600 .85rem var(--font);border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;padding:6px 14px;cursor:pointer}
.tabs button[aria-selected="true"]{background:var(--ink);color:var(--panel);border-color:var(--ink)}
.key{display:flex;flex-wrap:wrap;gap:14px;font-size:.8rem;color:var(--muted);margin-top:6px}.key i{display:inline-block;width:14px;height:3px;background:var(--c);vertical-align:middle;margin-right:5px}
svg.eq{width:100%;height:auto;display:block}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Forward test</h1>
  <div id="gsearch"></div>
  <nav aria-label="Dashboards"><a href="index.html">Sector rotation</a><a href="zones.html">Zones</a><a href="levels.html">Levels</a><a href="setups.html">Setups</a><a href="buy.html">Buy criteria</a><a href="forward.html" aria-current="page">Forward test</a><a href="watchlist.html">My list</a><a href="backtest.html">Backtest</a></nav>
</header>
<p class="stamp" id="gen"></p>
<section class="panel">
  <h2>Paper trading the Buy criteria, live</h2>
  <p class="sub" id="intro"></p>
  <div class="tabs" role="tablist" id="books"></div>
  <div class="kpi" id="kpi"></div>
</section>
<section class="panel"><h2>Portfolio value</h2><div id="chart"></div></section>
<section class="panel"><h2>Open positions</h2><div class="tbl"><table id="pos"></table></div></section>
<section class="panel" id="pendsec"><h2>Qualifying now, not bought</h2><p class="sub">These stocks meet the Buy criteria right now but were not bought: all 10 slots are full, it was already sold this week, or (for the A/B portfolio) its grade is lower.</p><div class="tbl"><table id="pend"></table></div></section>
<section class="panel"><h2>Closed trades</h2><div class="tbl"><table id="closed"></table></div></section>
<p class="note">Rules: checked on every price update. Sell when the price is below the trailing stop (the higher of the breakout-week low and the 10-week average of completed weeks). Buy when a stock meets the Buy criteria with this week's bar so far (above its 12-week high, up 8%+ on the week, RS top 20%, within 5% of its 52-week high), strongest first, up to 10 stocks, about 10% each, whole shares, stop-loss at the week's low so far. A stock sold this week is not bought back the same week. 0.15% cost on each buy and sell. Prices are about 15 minutes delayed and checks are about 30 minutes apart, so real fills will differ. Paper trading only, not investment advice.</p>
</div>
<script>
const D = __DATA__;
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v, d=2) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const rs_ = v => v==null ? "–" : (v<0?"−":"") + "₹" + Math.abs(Math.round(v)).toLocaleString("en-IN");
const pc = (v, d=1) => v==null ? "–" : `<span class="${v>=0?'ok':'bad'}">${v>0?"+":""}${fmt(v,d)}%</span>`;
const dl = d => d ? new Date(d.slice(0,10)+"T00:00:00").toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"2-digit"}) + (d.length > 10 ? " " + d.slice(11) : "") : "–";
const nm = (s, n) => `<td class="name"><button class="psym" data-p="${esc(s)}">${esc(s)}</button><small>${esc(n||"")}</small></td>`;
let cur = "all";
try { cur = localStorage.getItem("azh:fwbook") || "all"; } catch(e){}
if (!D.books[cur]) cur = "all";
document.getElementById("gen").textContent = `Updated ${D.generated}. Last check: ${D.last_week ? dl(D.last_week) + " IST" : "none yet"}.`;
const H = D.hist || [], first = H.length ? H[0] : null;
const days = Math.max(0, Math.round((new Date() - new Date(D.start+"T00:00:00"))/864e5));
document.getElementById("intro").innerHTML = `Started <b>${dl(D.start)}</b> (${days} days ago) with <b>${rs_(D.capital)}</b> in each portfolio. It trades the Buy criteria rule automatically on every price update (about every 30 minutes while the market is open, plus the evening run): stocks are sold as soon as the price is below the trailing stop and bought as soon as they qualify. Nothing is back-filled, so these are true out-of-sample results.`;
function draw(){
  const B = D.books[cur], keys = Object.keys(D.books);
  document.getElementById("books").innerHTML = keys.map(k=>`<button role="tab" data-b="${k}" aria-selected="${k===cur}">${esc(D.books[k].name)}</button>`).join("");
  document.querySelectorAll("[data-b]").forEach(b=>b.onclick=()=>{ cur=b.dataset.b; try{localStorage.setItem("azh:fwbook",cur);}catch(e){} draw(); });
  const bi = keys.indexOf(cur) + 1, nIdx = keys.length + 1;
  const bench = first && first[nIdx] && H[H.length-1][nIdx] ? (H[H.length-1][nIdx]/first[nIdx]-1)*100 : null;
  const invested = B.pos.reduce((a,p)=>a+p.now,0);
  document.getElementById("kpi").innerHTML = `
    <div><b>${rs_(B.value)}</b><small>portfolio value · ${pc(B.ret,2)}</small></div>
    <div><b>${pc(bench,2)}</b><small>NIFTY 50 over the same days</small></div>
    <div><b>${B.pos.length} / 10</b><small>open positions · ${rs_(invested)} invested · ${rs_(B.cash)} cash</small></div>
    <div><b>${B.n_closed}</b><small>closed trades${B.n_closed?` · ${fmt(B.win,0)}% won · realised ${rs_(B.realised)}`:""}</small></div>`;
  // equity chart: portfolio vs NIFTY 50 rebased to the starting capital
  const el = document.getElementById("chart");
  if (H.length < 2){ el.innerHTML = '<p class="sub">The chart starts after the second daily update.</p>'; }
  else {
    const W = Math.max(320, Math.min(1100, el.clientWidth||900)), Hh = Math.round(Math.max(200, W*0.3)), P={l:8,r:70,t:10,b:22};
    const a = H.map(h=>h[bi]), nb = H.map(h=> first[nIdx] && h[nIdx] ? h[nIdx]/first[nIdx]*D.capital : null);
    const all = [...a, ...nb, D.capital].filter(v=>v!=null); let lo = Math.min(...all), hi = Math.max(...all); const m=(hi-lo)*0.08||1; lo-=m; hi+=m;
    const X = i => P.l + i/(H.length-1)*(W-P.l-P.r), Y = v => P.t + (hi-v)/(hi-lo)*(Hh-P.t-P.b);
    const path = arr => { let d="", pen=false; arr.forEach((v,i)=>{ if(v==null){pen=false;return;} d+=`${pen?"L":"M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`; pen=true; }); return d; };
    let g = `<line x1="${P.l}" x2="${W-P.r}" y1="${Y(D.capital)}" y2="${Y(D.capital)}" stroke="var(--line)" stroke-dasharray="4 4"/>`;
    g += `<path d="${path(nb)}" fill="none" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="5 3"/>`;
    g += `<path d="${path(a)}" fill="none" stroke="var(--focus)" stroke-width="2.2"/>`;
    g += `<text x="${W-P.r+4}" y="${Y(a[a.length-1])+4}" font-size="11" font-weight="700" fill="var(--focus)">${(a[a.length-1]/1e5).toFixed(2)}L</text>`;
    g += `<text x="${W-P.r+4}" y="${Y(D.capital)+4}" font-size="10" fill="var(--muted)">10.00L</text>`;
    [0, H.length-1].forEach((i,k)=>{ g += `<text x="${X(i)}" y="${Hh-6}" font-size="11" fill="var(--muted)" text-anchor="${k?"end":"start"}">${dl(H[i][0])}</text>`; });
    el.innerHTML = `<svg class="eq" viewBox="0 0 ${W} ${Hh}" role="img" aria-label="Portfolio value against NIFTY 50">${g}</svg>
      <div class="key"><span><i style="--c:var(--focus)"></i>${esc(B.name)}</span><span><i style="--c:var(--muted)"></i>NIFTY 50 (same ₹10 lakh)</span></div>`;
  }
  document.getElementById("pos").innerHTML = `<thead><tr><th class="l">Stock</th><th>Bought</th><th>Price</th><th>Qty</th><th>Invested</th><th>Now</th><th>Value</th><th>P&amp;L</th><th>Stop-loss</th><th>Trailing stop</th><th>Room</th><th>Grade</th></tr></thead><tbody>${B.pos.map(p=>`<tr>
    ${nm(p.sym,p.name)}<td>${dl(p.ed)}</td><td>₹${fmt(p.ep)}</td><td>${p.q.toLocaleString("en-IN")}</td><td>${rs_(p.inv)}</td><td>₹${fmt(p.last)}</td><td>${rs_(p.now)}</td><td>${pc(p.pct)}</td>
    <td>₹${fmt(p.sl)}</td><td><b>₹${fmt(p.trail)}</b></td><td>${pc(p.room)}</td><td>${esc(p.grade||"–")}</td></tr>`).join("") || '<tr><td colspan="12" class="mut">No open positions yet. The first buys happen at the first Friday close with signals.</td></tr>'}</tbody>`;
  const held = new Set(B.pos.map(p=>p.sym));
  const pend = (D.pending||[]).filter(x=> !held.has(x.sym));
  document.getElementById("pendsec").hidden = !pend.length;
  document.getElementById("pend").innerHTML = `<thead><tr><th class="l">Stock</th><th>Price</th><th>Stop-loss if bought</th><th>Grade</th></tr></thead><tbody>${pend.map(x=>`<tr>${nm(x.sym,x.name)}<td>₹${fmt(x.price)}</td><td>₹${fmt(x.sl)}</td><td>${esc(x.grade||"–")}</td></tr>`).join("")}</tbody>`;
  document.getElementById("closed").innerHTML = `<thead><tr><th class="l">Stock</th><th>Bought</th><th>Price</th><th>Sold</th><th>Price</th><th>Qty</th><th>Weeks</th><th>Reason</th><th>P&amp;L</th><th>P&amp;L %</th></tr></thead><tbody>${B.closed.map(x=>`<tr>
    ${nm(x.sym,"")}<td>${dl(x.ed)}</td><td>₹${fmt(x.ep)}</td><td>${dl(x.xd)}</td><td>₹${fmt(x.xp)}</td><td>${x.q.toLocaleString("en-IN")}</td><td>${x.weeks}</td><td>${esc(x.why)}</td><td>${x.pnl>=0?'<span class="ok">':'<span class="bad">'}${rs_(x.pnl)}</span></td><td>${pc(x.pct)}</td></tr>`).join("") || '<tr><td colspan="10" class="mut">No closed trades yet.</td></tr>'}</tbody>`;
}
draw();
</script>
<script src="profile.js" defer></script>
</body>
</html>
"""
