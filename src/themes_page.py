"""Renders docs/themes.html: the Themes tab."""
import json

from .config import DOCS
from .setups_page import TEMPLATE as _SETUPS


def render(payload):
    DOCS.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(payload, separators=(",", ":"), allow_nan=False, default=str).replace("</", "<\\/")
    head = _SETUPS[:_SETUPS.index("</style>")].replace("<title>Trade setups: monthly, weekly, daily</title>", "<title>Themes</title>")
    (DOCS / "themes.html").write_text(head + TEMPLATE.replace("__DATA__", blob), encoding="utf-8")


TEMPLATE = r"""
.grid{display:grid;gap:10px;grid-template-columns:minmax(0,1fr)}
@media(min-width:700px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(min-width:1050px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
.tc{border:1px solid var(--line);border-left:5px solid var(--c);border-radius:12px;padding:10px 12px;background:var(--panel);text-align:left;font:inherit;color:var(--ink);cursor:pointer;width:100%}
.tc[aria-pressed="true"]{outline:2px solid var(--c)}
.tc .h{display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.tc .h b{font-size:.95rem}
.tc .n{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:2px 8px;font-size:.8rem;margin-top:6px}
.tc .n span{color:var(--muted);display:block;font-size:.72rem}
.chipq{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.72rem;font-weight:700;color:#fff;background:var(--c);white-space:nowrap}
.ttl{list-style:none;margin:8px 0 0;padding:0;border-left:2px solid var(--line)}
.ttl li{position:relative;padding:0 0 8px 14px;font-size:.86rem}
.ttl li::before{content:"";position:absolute;left:-6px;top:5px;width:10px;height:10px;border-radius:50%;background:var(--focus)}
.ttl b{display:block;font-size:.8rem;color:var(--muted)}
svg.eq{width:100%;height:auto;display:block}
.yr{margin:10px 0 4px;font-weight:600}
.nw{list-style:none;margin:0;padding:0}.nw li{font-size:.85rem;padding:4px 0;border-top:1px solid var(--line)}
.nw small{color:var(--muted)}
.key{display:flex;flex-wrap:wrap;gap:14px;font-size:.8rem;color:var(--muted);margin-top:6px}.key i{display:inline-block;width:14px;height:3px;background:var(--c);vertical-align:middle;margin-right:5px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Themes</h1>
  <div id="gsearch"></div>
  <nav aria-label="Dashboards"><a href="index.html">Sector rotation</a><a href="zones.html">Zones</a><a href="themes.html" aria-current="page">Themes</a><a href="levels.html">Levels</a><a href="setups.html">Setups</a><a href="buy.html">Buy criteria</a><a href="forward.html">Forward test</a><a href="tam.html">TAM screener</a><a href="watchlist.html">My list</a><a href="backtest.html">Backtest</a></nav>
</header>
<p class="stamp" id="gen"></p>
<section class="panel">
  <h2>Big structural stories and the stocks riding them</h2>
  <p class="sub">China+1 chemicals, semiconductors, defence and the rest: each theme is an equal-weight basket of its stocks, compared with NIFTY 50. <b>Improving</b> is the early signal (weaker than NIFTY but gaining), <b>Leading</b> is the strong phase, <b>Weakening</b> means losing pace, <b>Lagging</b> means out of favour.</p>
  <div id="map"></div>
</section>
<section class="panel"><div class="grid" id="cards"></div></section>
<section class="panel" id="detail" hidden></section>
<p class="note">Theme lists, theses and timelines are short summaries for orientation; check details before relying on them. To add a theme or change its stocks, put a themes.json file in the repository root (same fields as the built-in list). News history is collected year by year from each theme's start, a few years per daily run, then kept up to date. For information only, not investment advice.</p>
</div>
<script>
const D = __DATA__;
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v, d=1) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const pc = (v, d=1) => v==null ? "–" : `<span class="${v>=0?'ok':'bad'}">${v>0?"+":""}${fmt(v,d)}%</span>`;
const QC = {Leading:"#1E8F5A", Improving:"#2F62C8", Weakening:"#C9780F", Lagging:"#C2453B"};
const chip = s => s ? `<span class="chipq" style="--c:${QC[s]}">${s}</span>` : '<span class="mut">–</span>';
document.getElementById("gen").textContent = `Updated ${D.generated}.`;
let cur = decodeURIComponent(location.hash.slice(1)) || null, NEWS = null;
// rotation map
(function(){ const el = document.getElementById("map"), T = D.themes.filter(t=>t.rs!=null && t.mom!=null); if (!T.length) return;
  const W = Math.max(320, Math.min(1100, el.clientWidth||900)), H = Math.round(Math.max(260, W*0.42)), P = 34;
  const xs = T.flatMap(t=>[t.rs, ...t.trail.map(p=>p[0])]), ys = T.flatMap(t=>[t.mom, ...t.trail.map(p=>p[1])]);
  const span = (a, c) => { const m = Math.max(...a.map(v=>Math.abs(v-c)), 2) * 1.15; return [c-m, c+m]; };
  const [x0,x1] = span(xs,100), [y0,y1] = span(ys,100);
  const X = v => P + (v-x0)/(x1-x0)*(W-2*P), Y = v => H-P - (v-y0)/(y1-y0)*(H-2*P);
  let g = `<rect x="${X(100)}" y="${P}" width="${W-P-X(100)}" height="${Y(100)-P}" fill="${QC.Leading}" opacity=".06"/><rect x="${P}" y="${P}" width="${X(100)-P}" height="${Y(100)-P}" fill="${QC.Improving}" opacity=".06"/>
    <rect x="${X(100)}" y="${Y(100)}" width="${W-P-X(100)}" height="${H-P-Y(100)}" fill="${QC.Weakening}" opacity=".06"/><rect x="${P}" y="${Y(100)}" width="${X(100)-P}" height="${H-P-Y(100)}" fill="${QC.Lagging}" opacity=".06"/>
    <line x1="${X(100)}" x2="${X(100)}" y1="${P}" y2="${H-P}" stroke="var(--line)"/><line x1="${P}" x2="${W-P}" y1="${Y(100)}" y2="${Y(100)}" stroke="var(--line)"/>
    <text x="${W-P-4}" y="${P+14}" text-anchor="end" font-size="11" fill="${QC.Leading}" font-weight="700">Leading</text><text x="${P+4}" y="${P+14}" font-size="11" fill="${QC.Improving}" font-weight="700">Improving</text>
    <text x="${W-P-4}" y="${H-P-6}" text-anchor="end" font-size="11" fill="${QC.Weakening}" font-weight="700">Weakening</text><text x="${P+4}" y="${H-P-6}" font-size="11" fill="${QC.Lagging}" font-weight="700">Lagging</text>
    <text x="${W/2}" y="${H-8}" text-anchor="middle" font-size="10" fill="var(--muted)">strength vs NIFTY →</text><text x="10" y="${H/2}" font-size="10" fill="var(--muted)" transform="rotate(-90 10 ${H/2})" text-anchor="middle">momentum →</text>`;
  T.forEach(t=>{ const col = QC[t.state]||"#888"; if (t.trail.length>1) g += `<path d="${t.trail.map((p,i)=>`${i?"L":"M"}${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join("")}" fill="none" stroke="${col}" stroke-width="1.2" opacity=".5"/>`;
    g += `<circle cx="${X(t.rs)}" cy="${Y(t.mom)}" r="6" fill="${col}"><title>${esc(t.name)}: ${t.state}</title></circle><text x="${X(t.rs)+8}" y="${Y(t.mom)+4}" font-size="10.5" fill="var(--ink)" style="cursor:pointer" data-th="${esc(t.id)}">${esc(t.name.split(":")[0].split(" and ")[0])}</text>`; });
  el.innerHTML = `<svg class="eq" viewBox="0 0 ${W} ${H}" role="img" aria-label="Theme rotation map">${g}</svg><p class="sub" style="margin:4px 0 0">Dots are today; lines show the last 8 weeks. Themes move clockwise: Improving → Leading → Weakening → Lagging. Tap a name for details.</p>`;
  el.querySelectorAll("[data-th]").forEach(n=>n.onclick=()=>open_(n.dataset.th));
})();
function cards(){
  document.getElementById("cards").innerHTML = D.themes.map(t=>`<button class="tc" data-th="${esc(t.id)}" aria-pressed="${t.id===cur}" style="--c:${QC[t.state]||"#888"}">
    <div class="h"><b>${esc(t.name)}</b>${chip(t.state)}</div>
    <div class="n"><div><span>1 month</span>${pc(t.r1m)}</div><div><span>3 months</span>${pc(t.r3m)}</div><div><span>1 year</span>${pc(t.r1y)}</div>
      <div><span>3 years</span>${pc(t.r3y)}</div><div><span>Above 50 DMA</span>${fmt(t.a50,0)}%</div><div><span>Near 52-wk high</span>${fmt(t.near,0)}%</div></div>
    <div class="mut" style="font-size:.76rem;margin-top:6px">${t.n} stocks${t.buys?` · <b class="ok">${t.buys} Buy criteria signal${t.buys>1?"s":""}</b>`:""}${t.tams?` · ${t.tams} in TAM screener`:""} · since ${t.start}</div></button>`).join("");
  document.querySelectorAll(".tc").forEach(b=>b.onclick=()=>open_(b.dataset.th));
}
function chart(t){
  const c = t.curve, b = t.bcurve; if (!c || c.length < 3) return "";
  const W = Math.max(320, Math.min(1100, (document.getElementById("detail").clientWidth||900)-28)), H = Math.round(Math.max(200, W*0.32)), P={l:6,r:54,t:10,b:22};
  const vals = [...c.map(x=>x[1]), ...b.map(x=>x[1])].filter(v=>v>0), lo = Math.log(Math.min(...vals)*0.95), hi = Math.log(Math.max(...vals)*1.05);
  const X = i => P.l + i/(c.length-1)*(W-P.l-P.r), Y = v => P.t + (hi-Math.log(v))/(hi-lo)*(H-P.t-P.b);
  const path = a => a.map((x,i)=>`${i?"L":"M"}${X(i).toFixed(1)},${Y(Math.max(x[1],0.01)).toFixed(1)}`).join("");
  const dl = d => new Date(d+"T00:00:00").toLocaleDateString("en-IN",{month:"short",year:"numeric"});
  let g = `<path d="${path(b)}" fill="none" stroke="var(--muted)" stroke-width="1.3" stroke-dasharray="5 3"/><path d="${path(c)}" fill="none" stroke="${QC[t.state]||"var(--focus)"}" stroke-width="2.2"/>`;
  g += `<text x="${W-P.r+4}" y="${Y(c[c.length-1][1])+4}" font-size="11" font-weight="700" fill="${QC[t.state]||"var(--focus)"}">${fmt(c[c.length-1][1]/100,1)}x</text>`;
  [0, Math.floor((c.length-1)/2), c.length-1].forEach((i,k)=>{ g += `<text x="${X(i)}" y="${H-6}" font-size="11" fill="var(--muted)" text-anchor="${["start","middle","end"][k]}">${dl(c[i][0])}</text>`; });
  return `<svg class="eq" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(t.name)} basket against NIFTY 50">${g}</svg><div class="key"><span><i style="--c:${QC[t.state]||"var(--focus)"}"></i>${esc(t.name)} basket (equal weight)</span><span><i style="--c:var(--muted)"></i>NIFTY 50</span><span>log scale, both start at 1x</span></div>`;
}
function open_(id){
  cur = id; history.replaceState(null, "", "#" + id); cards();
  const t = D.themes.find(x=>x.id===id), el = document.getElementById("detail"); if (!t){ el.hidden = true; return; }
  el.hidden = false;
  el.innerHTML = `<h2>${esc(t.name)} ${chip(t.state)}</h2><p class="sub" style="max-width:90ch">${esc(t.thesis||"")}</p>
    <div class="kpi" style="display:flex;flex-wrap:wrap;gap:6px 18px;font-size:.88rem;margin:0 0 10px">${[["1 week",t.r1w],["1 month",t.r1m],["3 months",t.r3m],["6 months",t.r6m],["1 year",t.r1y],["3 years",t.r3y],[`Since ${new Date(t.since_d+"T00:00:00").toLocaleDateString("en-IN",{month:"short",year:"numeric"})}`,t.since]].map(([k,v])=>`<span><span class="mut">${k}</span> ${pc(v)}</span>`).join("")}</div>
    ${chart(t)}
    <h3 style="font-size:1rem;margin:14px 0 0">Timeline</h3><ul class="ttl">${(t.timeline||[]).map(([d,x])=>`<li><b>${esc(d)}</b> ${esc(x)}</li>`).join("")}</ul>
    <h3 style="font-size:1rem;margin:14px 0 6px">Stocks (${t.n})</h3>
    <div class="tbl"><table><thead><tr><th class="l">Stock</th><th>Price</th><th>1M</th><th>3M</th><th>1Y</th><th>3Y</th><th>From 52-wk high</th><th>Weekly zone</th><th class="l">Signals</th></tr></thead><tbody>${t.stocks.map(r=>`<tr>
      <td class="name"><button class="psym" data-p="${esc(r.sym)}">${esc(r.sym)}</button><small>${esc(r.name||"")}</small></td><td>₹${fmt(r.px,2)}</td><td>${pc(r.r1m)}</td><td>${pc(r.r3m)}</td><td>${pc(r.r1y)}</td><td>${pc(r.r3y)}</td><td>${pc(r.hi)}</td>
      <td>${esc(r.zw||"–")}</td><td class="l">${[r.buy?`<span class="ok">Buy criteria: ${esc(r.buy)}</span>`:"", r.tam?"TAM screener":"", r.a50===false?'<span class="mut">below 50 DMA</span>':""].filter(Boolean).join(" · ")||'<span class="mut">–</span>'}</td></tr>`).join("")}</tbody></table></div>
    <h3 style="font-size:1rem;margin:16px 0 4px">News history</h3><div id="news"><p class="sub">Loading…</p></div>`;
  el.scrollIntoView({behavior:"smooth", block:"start"});
  const show = () => { const items = (NEWS||{})[id] || [], box = document.getElementById("news"); if (!box) return;
    if (!items.length){ box.innerHTML = '<p class="sub">No headlines collected yet. History fills in over the next few daily runs.</p>'; return; }
    const by = {}; items.forEach(x=>{ (by[x.d.slice(0,4)] ??= []).push(x); });
    const yrs = Object.keys(by).sort().reverse();
    box.innerHTML = `<p class="sub">${items.length} headlines from ${yrs[yrs.length-1]} to ${yrs[0]}: ${yrs.map(y=>`${y} (${by[y].length})`).join(" · ")}</p>` +
      yrs.map((y,k)=>`<details ${k===0?"open":""}><summary class="yr">${y} · ${by[y].length} headlines</summary><ul class="nw">${by[y].slice(0,60).map(x=>`<li>${/^https?:\/\//i.test(x.u)?`<a href="${esc(x.u)}" target="_blank" rel="noopener" style="color:inherit">${esc(x.t)}</a>`:esc(x.t)} <small>${new Date(x.d+"T00:00:00").toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"})} · ${esc(x.s||"")}</small></li>`).join("")}</ul></details>`).join(""); };
  if (NEWS) show(); else fetch("themes_news.json", {cache:"no-cache"}).then(r=>r.ok?r.json():{}).catch(()=>({})).then(j=>{ NEWS = j; show(); });
}
cards();
if (cur) open_(cur);
</script>
<script src="profile.js" defer></script>
</body>
</html>
"""
