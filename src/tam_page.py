"""Renders docs/tam.html: the TAM screener tab."""
import json

from .config import DOCS
from .setups_page import TEMPLATE as _SETUPS


def render(payload):
    DOCS.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(payload, separators=(",", ":"), allow_nan=False, default=str).replace("</", "<\\/")
    head = _SETUPS[:_SETUPS.index("</style>")].replace("<title>Trade setups: monthly, weekly, daily</title>", "<title>TAM screener</title>")
    (DOCS / "tam.html").write_text(head + TEMPLATE.replace("__DATA__", blob), encoding="utf-8")


TEMPLATE = r"""
.idx{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:baseline;font-size:.92rem}
.idx b{font-size:1.1rem}
.warn{border-left:5px solid var(--down);background:color-mix(in srgb,var(--down) 8%,var(--panel))}
.okb{border-left:5px solid var(--up)}
.act{font-size:1rem;line-height:1.5}
.scn{display:inline-block;font-size:.72rem;font-weight:700;border:1px solid var(--focus);color:var(--focus);border-radius:6px;padding:0 5px;margin:1px 3px 1px 0;white-space:nowrap}
.why{white-space:normal;min-width:260px;max-width:420px;text-align:left;font-size:.8rem;color:var(--muted)}
.why b{color:var(--ink);font-weight:600}
.cx{white-space:normal;min-width:170px;max-width:240px;text-align:left;font-size:.8rem}
.st{display:inline-block;font-size:.7rem;font-weight:700;color:#fff;background:var(--up);border-radius:6px;padding:0 6px;margin-left:6px}
.sc h3{font-size:.98rem;margin:14px 0 4px}
.none{color:var(--muted);font-size:.86rem;margin:0 0 6px}
td.l2{text-align:left;white-space:normal}
td.name{text-align:left}
.tb{font:600 .85rem var(--font);border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;padding:6px 14px;cursor:pointer}
.tb[aria-selected="true"]{background:var(--ink);color:var(--panel);border-color:var(--ink)}
.stt{display:inline-block;font-size:.72rem;font-weight:700;color:#fff;border-radius:6px;padding:0 6px;white-space:nowrap}
.card{border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin:0 0 10px}
.card .t{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.card .g{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 12px;font-size:.84rem;margin:8px 0}
.card .g span{color:var(--muted)}.card .g b{font-weight:600}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>TAM screener</h1>
  <div id="gsearch"></div>
  <nav aria-label="Dashboards"><a href="index.html">Sector rotation</a><a href="zones.html">Zones</a><a href="levels.html">Levels</a><a href="setups.html">Setups</a><a href="buy.html">Buy criteria</a><a href="forward.html">Forward test</a><a href="tam.html" aria-current="page">TAM screener</a><a href="watchlist.html">My list</a><a href="backtest.html">Backtest</a></nav>
</header>
<p class="stamp" id="gen"></p>
<section class="panel" id="idx"></section>
<section class="panel" id="act"></section>
<section class="panel">
  <div class="tabs" role="tablist" style="display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px">
    <button role="tab" class="tb" data-v="live" aria-selected="true">Signals and open trades</button>
    <button role="tab" class="tb" data-v="watch" aria-selected="false">Watch list</button>
    <button role="tab" class="tb" data-v="exits" aria-selected="false">Recent exits</button>
  </div>
  <p class="sub" id="trkhint"></p>
  <div id="trk"></div>
</section>
<section class="panel">
  <div class="tools">
    <label class="tog">Capital ₹ <input type="number" id="cap" min="0" step="10000" placeholder="100000"></label>
    <label class="tog"><input type="checkbox" id="u1k"> Under ₹1,000 only</label>
  </div>
  <h2>Special strict list</h2>
  <p class="sub">Passes every strict line: not up more than 8% in 5 sessions, within 5% of the 52-week high, volume 2.5x+, above the 20 and 50 DMA, at least 1:2 from the safe entry to T1, entry on the dip or retest. If nothing passes, it says cash.</p>
  <div id="strict"></div>
</section>
<section class="panel sc"><h2>Regular scanners</h2><p class="sub">Only names that pass. Ranked by technical strength, then volume, freshness, risk-reward and catalyst.</p><div id="scans"></div></section>
<section class="panel"><h2>Leave table</h2><p class="sub">Circuits, faded spikes, repeated names, extended moves and anything that matched a scanner but failed a rule. Not tradeable today.</p><div class="tbl"><table id="leave"></table></div></section>
<p class="note">Prices are from the dashboard's latest update (Yahoo, about 15 minutes delayed during market hours) and NSE's end-of-day file after the close. Check the live price in Groww before placing any order. During market hours today's volume is projected to a full day. Hourly charts are not available here, so the Elliott check is daily only. MTF interest is shown at 0.041% per day. For information only, not investment advice.</p>
</div>
<script>
const D = __DATA__;
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v, d=2) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const pc = (v, d=1) => v==null ? "–" : `<span class="${v>=0?'ok':'bad'}">${v>0?"+":""}${fmt(v,d)}%</span>`;
const store = { get(k){ try { return localStorage.getItem(k); } catch(e){ return null; } }, set(k,v){ try { localStorage.setItem(k,v); } catch(e){} } };
const capEl = document.getElementById("cap"), u1kEl = document.getElementById("u1k");
capEl.value = store.get("azh:tamcap") || ""; u1kEl.checked = store.get("azh:tamu1k") === "1";
const ageMin = (Date.now() - new Date(D.gen_iso).getTime()) / 60000;
const ist = new Date(Date.now() + (330 + new Date().getTimezoneOffset())*60000), mins = ist.getHours()*60 + ist.getMinutes();
const marketOpen = ist.getDay()>=1 && ist.getDay()<=5 && mins >= 555 && mins <= 930;
const stale = D.stale || (marketOpen && ageMin > 50);
document.getElementById("gen").innerHTML = `Updated ${esc(D.generated)}. Prices as of <b>${esc(D.asof)}</b>.` + (D.stale ? ` <span class="bad"><b>Stale: these prices are from ${esc(D.asof)}, not today. Do not trade off them.</b></span>` : stale ? ` <span class="bad"><b>Stale: the last update is ${Math.round(ageMin)} minutes old while the market is open. Do not trade off these prices.</b></span>` : "");
const I = D.index;
document.getElementById("idx").className = "panel " + (I.cash ? "warn" : "okb");
document.getElementById("idx").innerHTML = I.last ? `<div class="idx"><span>NIFTY 50 <b>${fmt(I.last)}</b> ${pc(I.chg,2)}</span><span>Day range ${fmt(I.lo)} – ${fmt(I.hi)}</span><span>20 DMA ${fmt(I.dma20,0)} · 50 DMA ${fmt(I.dma50,0)}</span><span><b>Scan cancels below ${fmt(I.cancel,0)}</b></span></div>${I.cash?`<p class="bad" style="margin:6px 0 0"><b>${esc(I.why)}.</b> A stock does not override a broken index.</p>`:""}` : '<p class="sub">NIFTY data not available.</p>';
const cap = () => +capEl.value || 100000;
const qty = r => { const q = Math.floor(cap() / (r.entry || r.cmp)); return q > 0 ? q : 0; };
const mtf = r => { const v = qty(r) * (r.entry || r.cmp); return `₹${Math.round(v*D.mtf/100*5).toLocaleString("en-IN")} / ₹${Math.round(v*D.mtf/100*10).toLocaleString("en-IN")}`; };
function act(){
  const el = document.getElementById("act"), a = D.action;
  if (!a){ el.className = "panel warn"; el.innerHTML = `<p class="act"><b>Action: cash.</b> ${I.cash ? esc(I.why) + "." : "Nothing passes the strict filter, and the filter is not loosened to fill the table."}</p>`; return; }
  const r = D.rows.find(x=>x.sym===a.sym) || {};
  el.className = "panel okb";
  el.innerHTML = `<p class="act"><b>Action: <button class="psym" data-p="${esc(a.sym)}">${esc(a.sym)}</button></b> · buy in the zone <b>₹${fmt(a.zone[0])} – ₹${fmt(a.zone[1])}</b> (limit order, not at the day's high) · SL <b>₹${fmt(a.sl)}</b> on a closing basis · T1 ₹${fmt(a.t1)} (book 50%), T2 ₹${fmt(a.t2)} · R:R 1:${fmt(a.rr,1)} · cancel if NIFTY closes below <b>${fmt(a.nifty,0)}</b>.
    ${a.event ? '<br><span class="bad">Event day: do not use a market order into the close.</span>' : ""}
    <br><span class="mut">With ₹${cap().toLocaleString("en-IN")}: about ${qty(r)} shares · MTF interest ${mtf(r)} for 5 / 10 days.</span></p>`;
}
const head = `<thead><tr><th>#</th><th class="l">Stock</th><th>CMP</th><th class="l">Scanner</th><th class="l">Why it qualifies</th><th>Safe entry zone</th><th>SL</th><th>T1</th><th>T2</th><th>R:R</th><th>Qty · MTF 5/10d</th><th class="l">What cancels it</th></tr></thead>`;
const row = r => `<tr><td>${r.rank}</td><td class="name"><button class="psym" data-p="${esc(r.sym)}">${esc(r.sym)}</button>${r.strict?'<span class="st">strict</span>':""}<small>${esc(r.sector||"")}</small></td>
  <td>₹${fmt(r.cmp)}<small class="mut" style="display:block">${pc(r.chg)} · ${esc(D.asof)}</small></td>
  <td class="l2">${r.scans.map(s=>`<span class="scn" title="${esc(D.scan_names[s])}">${s} ${esc(D.scan_names[s])}</span>`).join("")}</td>
  <td class="why">${r.why.map(esc).join(" · ")}<br><b>Checks ${r.tscore}/7</b>: ${Object.entries(r.tech).map(([k,v])=>`${v?"✓":"✗"} ${({structure:"HH/HL",above:"20/50 DMA",rsi:"RSI≤75",macd:"MACD",adx:"ADX",ha:"Heikin Ashi",elliott:"Elliott"})[k]}`).join(", ")}</td>
  <td>₹${fmt(r.zone[0])} – ₹${fmt(r.zone[1])}</td><td>₹${fmt(r.sl)}</td><td>₹${fmt(r.t1)}</td><td>₹${fmt(r.t2)}</td><td>1:${fmt(r.rr,1)}</td>
  <td>${qty(r).toLocaleString("en-IN")}<small class="mut" style="display:block">${mtf(r)}</small></td><td class="cx">${esc(r.cancel)}</td></tr>`;
const narrow = () => window.innerWidth < 700;
const card = r => `<div class="card"><div class="t"><span><b>#${r.rank}</b> <button class="psym" data-p="${esc(r.sym)}">${esc(r.sym)}</button>${r.strict?'<span class="st">strict</span>':""} <small class="mut">${esc(r.sector||"")}</small></span><span>₹${fmt(r.cmp)} ${pc(r.chg)}</span></div>
  <div>${r.scans.map(s=>`<span class="scn">${s} ${esc(D.scan_names[s])}</span>`).join("")}</div>
  <div class="g"><div><span>Safe entry</span><br><b>₹${fmt(r.zone[0])} – ₹${fmt(r.zone[1])}</b></div><div><span>SL</span><br><b>₹${fmt(r.sl)}</b></div>
    <div><span>T1 / T2</span><br><b>₹${fmt(r.t1)} / ₹${fmt(r.t2)}</b></div><div><span>R:R · Qty</span><br><b>1:${fmt(r.rr,1)} · ${qty(r).toLocaleString("en-IN")}</b></div>
    <div><span>MTF 5 / 10 days</span><br><b>${mtf(r)}</b></div><div><span>Checks</span><br><b>${r.tscore}/7</b></div></div>
  <div class="why" style="max-width:none">${r.why.map(esc).join(" · ")}</div><div class="cx" style="max-width:none;margin-top:4px"><b>Cancels:</b> ${esc(r.cancel)}</div></div>`;
const list = rs => narrow() ? rs.map(card).join("") : `<div class="tbl"><table>${head}<tbody>${rs.map(row).join("")}</tbody></table></div>`;
window.addEventListener("resize", ()=>{ clearTimeout(window.__t); window.__t = setTimeout(draw, 200); });
function draw(){
  const keep = r => !u1kEl.checked || r.cmp < 1000;
  const st = D.rows.filter(r=>r.strict && keep(r));
  document.getElementById("strict").outerHTML = `<div id="strict">${st.length ? list(st) : `<p class="none">None pass the strict filter${u1kEl.checked?" under ₹1,000":""}. Cash.</p>`}</div>`;
  document.getElementById("scans").innerHTML = Object.entries(D.scan_names).map(([k,n])=>{ const rs = D.rows.filter(r=>r.scans.includes(+k) && keep(r));
    return `<h3>Scanner ${k}: ${esc(n)} <span class="mut" style="font-weight:400">(${rs.length})</span></h3>` + (rs.length ? list(rs) : '<p class="none">None.</p>'); }).join("");
  document.getElementById("leave").innerHTML = `<thead><tr><th class="l">Stock</th><th>CMP</th><th>Today</th><th class="l">Why it is left out</th></tr></thead><tbody>${D.leave.filter(keep).map(x=>`<tr><td class="name"><button class="psym" data-p="${esc(x.sym)}">${esc(x.sym)}</button><small>${esc(x.sector||"")}</small></td><td>₹${fmt(x.cmp)}</td><td>${pc(x.chg)}</td><td class="l2">${x.why.map(esc).join("; ")}${x.scans?` <span class="mut">(matched scanner ${x.scans.join(", ")})</span>`:""}</td></tr>`).join("") || '<tr><td colspan="4" class="mut">Nothing.</td></tr>'}</tbody>`;
  act();
  trk();
}
let tv = "live";
const ST = {waiting:["Waiting for entry","var(--warn)"], open:["Open","var(--focus)"], t1:["T1 booked, rest running","var(--up)"],
            closed:["Closed","var(--muted)"], cancelled:["Cancelled","var(--down)"], expired:["Expired","var(--muted)"]};
const stt = s => `<span class="stt" style="background:${(ST[s]||["",""])[1]}">${(ST[s]||[s])[0]}</span>`;
const dd = d => d ? new Date(d.slice(0,10)+"T00:00:00").toLocaleDateString("en-IN",{day:"2-digit",month:"short"}) : "–";
function trk(){
  const T = D.trk || {live:[],exits:[],watch:[],stats:{}}, el = document.getElementById("trk"), hint = document.getElementById("trkhint");
  document.querySelectorAll(".tb").forEach(b=>b.setAttribute("aria-selected", b.dataset.v===tv));
  const keep = r => !u1kEl.checked || (r.cmp||r.last||0) < 1000;
  if (tv==="live"){
    const rs = T.live.filter(keep);
    hint.innerHTML = `Every name the scanners list is tracked as a plan: a limit order in the safe entry zone for ${5} sessions, SL on a closing basis, 50% booked at T1 with the stop moved to the entry price, the rest out at T2, a close below the stop, NIFTY below its cancel level, or after 15 sessions.`;
    el.innerHTML = rs.length ? `<div class="tbl"><table><thead><tr><th class="l">Stock</th><th>Signal</th><th>Status</th><th>Entry zone</th><th>Filled</th><th>SL / stop now</th><th>T1</th><th>T2</th><th>Price</th><th>Result</th><th>Qty · MTF 5/10d</th></tr></thead><tbody>${rs.map(r=>`<tr>
      <td class="name"><button class="psym" data-p="${esc(r.sym)}">${esc(r.sym)}</button>${r.strict?'<span class="st">strict</span>':""}<small>${esc(r.sector||"")} · scanner ${r.scans.join(", ")}</small></td>
      <td>${dd(r.sd)}</td><td>${stt(r.status)}</td><td>₹${fmt(r.zone[0])} – ₹${fmt(r.zone[1])}</td>
      <td>${r.entry?`₹${fmt(r.entry)}<small class="mut" style="display:block">${dd(r.ed)}</small>`:"–"}</td>
      <td>₹${fmt(r.sl)}${r.stop_now && r.stop_now!==r.sl?`<small class="mut" style="display:block">now ₹${fmt(r.stop_now)}</small>`:""}</td>
      <td>₹${fmt(r.t1)}${r.t1_hit?'<small class="ok" style="display:block">hit '+dd(r.t1_hit)+'</small>':""}</td><td>₹${fmt(r.t2)}</td>
      <td>₹${fmt(r.last)}</td><td>${r.pct!=null?pc(r.pct):"–"}</td><td>${qty({entry:r.entry||r.zone[1]})} <small class="mut" style="display:block">${mtf({entry:r.entry||r.zone[1]})}</small></td></tr>`).join("")}</tbody></table></div>`
      : '<p class="none">No signals or open trades right now.</p>';
  } else if (tv==="watch"){
    const rs = T.watch.filter(keep);
    hint.innerHTML = "Names that matched a scanner but missed on risk-reward, volume or freshness. They join the signals if the missing piece appears.";
    el.innerHTML = rs.length ? `<div class="tbl"><table><thead><tr><th class="l">Stock</th><th>Price</th><th>Today</th><th class="l">Scanner</th><th>Entry zone</th><th>SL</th><th>T1</th><th>R:R</th><th class="l">What is missing</th></tr></thead><tbody>${rs.map(x=>`<tr>
      <td class="name"><button class="psym" data-p="${esc(x.sym)}">${esc(x.sym)}</button><small>${esc(x.sector||"")}</small></td><td>₹${fmt(x.cmp)}</td><td>${pc(x.chg)}</td>
      <td class="l2">${(x.scans||[]).map(s=>`<span class="scn">${s} ${esc(D.scan_names[s])}</span>`).join("")}</td>
      <td>${x.zone?`₹${fmt(x.zone[0])} – ₹${fmt(x.zone[1])}`:"–"}</td><td>${x.sl?`₹${fmt(x.sl)}`:"–"}</td><td>${x.t1?`₹${fmt(x.t1)}`:"–"}</td><td>${x.rr!=null?"1:"+fmt(x.rr,1):"–"}</td>
      <td class="l2">${x.why.map(esc).join("; ")}</td></tr>`).join("")}</tbody></table></div>` : '<p class="none">Nothing close right now.</p>';
  } else {
    const S = T.stats || {};
    hint.innerHTML = S.n ? `${S.n} closed trades: ${fmt(S.win,0)}% made money, average ${pc(S.avg)} (half booked at T1 when reached), ${S.t1} reached T1. ${S.cancelled} plans were cancelled or expired before entry.` : "Closed, cancelled and expired plans from the last 60 days.";
    const rs = T.exits.filter(keep);
    el.innerHTML = rs.length ? `<div class="tbl"><table><thead><tr><th class="l">Stock</th><th>Signal</th><th>Status</th><th>Entry</th><th>Exit</th><th>Result</th><th class="l">Reason</th></tr></thead><tbody>${rs.map(r=>`<tr>
      <td class="name"><button class="psym" data-p="${esc(r.sym)}">${esc(r.sym)}</button><small>scanner ${r.scans.join(", ")}</small></td><td>${dd(r.sd)}</td><td>${stt(r.status)}</td>
      <td>${r.entry?`₹${fmt(r.entry)} <small class="mut">${dd(r.ed)}</small>`:"–"}</td><td>${r.exit?`₹${fmt(r.exit)} <small class="mut">${dd(r.xd)}</small>`:dd(r.xd)}</td>
      <td>${r.pct!=null?pc(r.pct):"–"}</td><td class="l2">${esc(r.why||"")}${r.t1_hit?` · T1 booked ${dd(r.t1_hit)}`:""}</td></tr>`).join("")}</tbody></table></div>` : '<p class="none">No exits yet.</p>';
  }
}
document.querySelectorAll(".tb").forEach(b=>b.onclick=()=>{ tv=b.dataset.v; trk(); });
capEl.oninput = () => { store.set("azh:tamcap", capEl.value); draw(); };
u1kEl.onchange = () => { store.set("azh:tamu1k", u1kEl.checked ? "1" : "0"); draw(); };
draw();
</script>
<script src="profile.js" defer></script>
</body>
</html>
"""
