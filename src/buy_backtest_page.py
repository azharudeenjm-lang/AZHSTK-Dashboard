"""Renders docs/buy_backtest.html: results of the Buy criteria backtest from 2020."""
import json

from .config import DOCS
from .setups_page import TEMPLATE as _SETUPS


def render(payload):
    blob = json.dumps(payload, separators=(",", ":"), allow_nan=False, default=str).replace("</", "<\\/")
    head = _SETUPS[:_SETUPS.index("</style>")].replace("<title>Trade setups: monthly, weekly, daily</title>",
                                                        "<title>Buy criteria backtest</title>")
    (DOCS / "buy_backtest.html").write_text(head + TEMPLATE.replace("__DATA__", blob), encoding="utf-8")


TEMPLATE = r"""
svg.eq{width:100%;height:auto;display:block}
.key{display:flex;flex-wrap:wrap;gap:14px;font-size:.8rem;color:var(--muted);margin-top:6px}.key i{display:inline-block;width:14px;height:3px;background:var(--c);vertical-align:middle;margin-right:5px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Buy criteria backtest</h1>
  <div id="gsearch"></div>
  <nav aria-label="Dashboards"><a href="index.html">Sector rotation</a><a href="zones.html">Zones</a><a href="levels.html">Levels</a><a href="setups.html">Setups</a><a href="buy.html">Buy criteria</a><a href="forward.html">Forward test</a><a href="tam.html">TAM screener</a><a href="watchlist.html">My list</a><a href="backtest.html">Backtest</a></nav>
</header>
<p class="stamp" id="gen"></p>
<section class="panel"><h2>₹10,00,000, up to 10 stocks, four ways to run the same rule</h2>
  <p class="sub" id="intro"></p><div class="tbl"><table id="sum"></table></div></section>
<section class="panel"><h2>Return in each year</h2><div class="tbl"><table id="yrs"></table></div></section>
<section class="panel"><h2>Portfolio value</h2><div id="chart"></div></section>
<p class="note">Liquidity (₹1 crore+ average daily turnover) and the relative-strength ranking use only what was known on each day. The stock list is today's, so companies delisted since 2020 are missing, which flatters results somewhat. Prices are daily: "sell when the stop is touched" uses the day's low as a stand-in for 30-minute checks. 0.15% cost per buy and per sell; no taxes or slippage. For information only, not investment advice.</p>
</div>
<script>
const D = __DATA__;
const fmt = (v, d=1) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const pc = v => v==null ? "–" : `<span class="${v>=0?'ok':'bad'}">${v>0?"+":""}${fmt(v)}%</span>`;
const rs = v => "₹" + Math.round(v).toLocaleString("en-IN");
const dl = d => new Date(d+"T00:00:00").toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"});
const M = Object.keys(D.res), COL = {friday:"#2F62C8", mid_in:"#1E8F5A", daily:"#C9780F", touch:"#C2453B"};
document.getElementById("gen").textContent = `Run ${D.generated}.`;
document.getElementById("intro").innerHTML = `${dl(D.from)} to ${dl(D.to)}, ${D.stocks.toLocaleString("en-IN")} stocks. <a href="buy_backtest_trades.csv" download>Download every trade (CSV)</a>.`;
document.getElementById("sum").innerHTML = `<thead><tr><th class="l">Version</th><th>₹10 lakh became</th><th>Total</th><th>Per year</th><th>Worst fall</th><th>Trades</th><th>Won</th><th>Avg win</th><th>Avg loss</th></tr></thead><tbody>${M.map(m=>{ const r=D.res[m]; return `<tr>
  <td class="l"><b style="color:${COL[m]}">●</b> ${r.name}</td><td><b>${rs(r.final)}</b></td><td>${pc(r.ret)}</td><td>${pc(r.cagr)}</td><td>${pc(r.dd)}</td><td>${r.trades}</td><td>${fmt(r.win,0)}%</td><td>${pc(r.avg_win)}</td><td>${pc(r.avg_loss)}</td></tr>`; }).join("")}
  ${D.bench?`<tr><td class="l"><b style="color:var(--muted)">●</b> NIFTY 50, bought and held</td><td>${rs(1000000*(1+D.bench.ret/100))}</td><td>${pc(D.bench.ret)}</td><td colspan="6"></td></tr>`:""}</tbody>`;
const years = D.res[M[0]].years.map(y=>y.y);
document.getElementById("yrs").innerHTML = `<thead><tr><th class="l">Year</th>${M.map(m=>`<th>${({friday:"Friday only",mid_in:"Buy any day, sell Friday",daily:"Daily close",touch:"Stop touched"})[m]||m}</th>`).join("")}${D.bench?"<th>NIFTY 50</th>":""}</tr></thead><tbody>${years.map((y,i)=>`<tr><td class="l">${y}</td>${M.map(m=>`<td>${pc(D.res[m].years[i].ret)}</td>`).join("")}${D.bench?`<td>${pc((D.bench.years.find(b=>b.y===y)||{}).ret)}</td>`:""}</tr>`).join("")}</tbody>`;
(function(){ const el = document.getElementById("chart"), W = Math.max(320, Math.min(1100, el.clientWidth||900)), H = Math.round(Math.max(220, W*0.35)), P={l:8,r:70,t:10,b:22};
  const series = M.map(m=>[COL[m], D.res[m].curve]); if (D.bench) series.push(["var(--muted)", D.bench.curve]);
  const n = D.res[M[0]].curve.length; const vals = series.flatMap(s=>s[1].map(x=>x[1])).filter(v=>v>0);
  const lo = Math.log(Math.min(...vals)*0.95), hi = Math.log(Math.max(...vals)*1.05);
  const X = i => P.l + i/(n-1)*(W-P.l-P.r), Y = v => P.t + (hi-Math.log(v))/(hi-lo)*(H-P.t-P.b);
  let g = "";
  [1e6, 2e6, 5e6, 1e7, 2e7, 5e7].forEach(v=>{ if (Math.log(v)>lo && Math.log(v)<hi) g += `<line x1="${P.l}" x2="${W-P.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="${W-P.r+4}" y="${Y(v)+4}" font-size="10" fill="var(--muted)">${v/1e5}L</text>`; });
  series.forEach(([col, cv])=>{ let d=""; cv.forEach(([_,v],i)=>{ d += `${i?"L":"M"}${X(i).toFixed(1)},${Y(Math.max(v,1)).toFixed(1)}`; }); g += `<path d="${d}" fill="none" stroke="${col}" stroke-width="${col.startsWith("var")?1.4:2}" ${col.startsWith("var")?'stroke-dasharray="5 3"':""}/>`; });
  const c0 = D.res[M[0]].curve; [0, n-1].forEach((i,k)=>{ g += `<text x="${X(i)}" y="${H-6}" font-size="11" fill="var(--muted)" text-anchor="${k?"end":"start"}">${dl(c0[i][0])}</text>`; });
  el.innerHTML = `<svg class="eq" viewBox="0 0 ${W} ${H}" role="img" aria-label="Portfolio value over time, log scale">${g}</svg><div class="key">${M.map(m=>`<span><i style="--c:${COL[m]}"></i>${D.res[m].name}</span>`).join("")}${D.bench?'<span><i style="--c:var(--muted)"></i>NIFTY 50</span>':""}<span>(log scale)</span></div>`;
})();
</script>
<script src="profile.js" defer></script>
</body>
</html>
"""
