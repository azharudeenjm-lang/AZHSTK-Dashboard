"""Renders docs/buy.html: the Buy criteria tab (weekly momentum breakouts with stops)."""
import json
from datetime import datetime, timedelta, timezone

from .config import DOCS
from .setups_page import TEMPLATE as _SETUPS


def render(payload):
    DOCS.mkdir(parents=True, exist_ok=True)
    ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    payload["generated"] = ist.strftime("%d %b %Y, %I:%M %p IST")
    blob = json.dumps(payload, separators=(",", ":"), allow_nan=False, default=str).replace("</", "<\\/")
    head = _SETUPS[:_SETUPS.index("</style>")]          # same look as the Setups tab
    head = head.replace("<title>Trade setups: monthly, weekly, daily</title>", "<title>Buy criteria</title>")
    (DOCS / "buy.html").write_text(head + TEMPLATE.replace("__DATA__", blob), encoding="utf-8")


TEMPLATE = r"""
.ckl{display:grid;gap:8px;grid-template-columns:minmax(0,1fr)}
@media(min-width:760px){.ckl{grid-template-columns:repeat(2,minmax(0,1fr))}}
.ckl div{border:1px solid var(--line);border-radius:10px;padding:9px 12px;font-size:.86rem}
.ckl b{display:block}.ckl span{color:var(--muted)}
.kpi{display:grid;gap:10px;grid-template-columns:repeat(2,minmax(0,1fr))}
@media(min-width:760px){.kpi{grid-template-columns:repeat(5,minmax(0,1fr))}}
.kpi div{border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.kpi b{display:block;font-size:1.35rem}.kpi small{color:var(--muted);font-size:.76rem}
.flag{display:inline-block;font-size:.72rem;font-weight:600;color:var(--down);border:1px solid currentColor;border-radius:6px;padding:0 5px;margin:2px 4px 0 0;white-space:nowrap}
.new{display:inline-block;font-size:.72rem;font-weight:700;color:#fff;background:var(--up);border-radius:6px;padding:0 6px;margin-left:6px}
.form{background:var(--warn)}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
.tabs button{font:600 .85rem var(--font);border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;padding:6px 14px;cursor:pointer}
.tabs button[aria-selected="true"]{background:var(--ink);color:var(--panel);border-color:var(--ink)}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Buy criteria</h1>
  <div id="gsearch"></div>
  <nav aria-label="Dashboards"><a href="index.html">Sector rotation</a><a href="zones.html">Zones</a><a href="levels.html">Levels</a><a href="setups.html">Setups</a><a href="buy.html" aria-current="page">Buy criteria</a><a href="forward.html">Forward test</a><a href="tam.html">TAM screener</a><a href="watchlist.html">My list</a><a href="backtest.html">Backtest</a></nav>
</header>
<p class="stamp" id="gen"></p>

<section class="panel">
  <h2>Weekly momentum breakout</h2>
  <p class="sub">A stock qualifies on a weekly close when all of these hold. Built from what the biggest movers (like HFCL's April 2026 breakout) had in common, and tested on this dashboard's own 5 years of weekly prices.</p>
  <div class="ckl">
    <div><b>1. Breakout</b><span>Weekly close above the highest high of the previous 12 weeks.</span></div>
    <div><b>2. Strong push</b><span>Up at least 8% on the week.</span></div>
    <div><b>3. Leader</b><span>6-month return in the top 20% of all liquid stocks (RS 80+).</span></div>
    <div><b>4. Near highs</b><span>Close within 5% of the 52-week high.</span></div>
    <div><b>Stop-loss</b><span>Low of the breakout week. Exit if a week closes below it.</span></div>
    <div><b>Trailing stop</b><span>The 10-week average once it rises above the stop-loss. Exit on the first weekly close below it. Never move it down.</span></div>
  </div>
</section>

<section class="panel" id="stats"></section>

<section class="panel">
  <div class="tabs" role="tablist">
    <button role="tab" data-v="open" aria-selected="true">Signals and open trades</button>
    <button role="tab" data-v="watch" aria-selected="false">Watch list</button>
    <button role="tab" data-v="exits" aria-selected="false">Recent exits</button>
    <button role="tab" data-v="tt" aria-selected="false">Trend Template 8/8</button>
    <button role="tab" data-v="tt7" aria-selected="false">Trend Template 7/8</button>
    <button role="tab" data-v="t3" aria-selected="false">3-touch trendline breakouts</button>
    <button role="tab" data-v="t3n" aria-selected="false">Near a 3-touch trendline</button>
  </div>
  <div class="tools">
    <label class="tog">Risk per trade ₹ <input type="number" id="risk" min="0" step="500" placeholder="e.g. 5000"></label>
    <label class="tog"><input type="checkbox" id="clean" checked> Hide stocks under surveillance</label>
    <label class="tog"><input type="checkbox" id="qab"> Quality A or B only</label>
    <label class="tog">Sort by <select id="sortk" style="font:inherit;padding:4px 6px;border-radius:8px;border:1px solid var(--line,#ccc);background:var(--panel,#fff);color:inherit"></select></label>
    <button type="button" id="sortd" class="tog" title="Reverse the order" style="font:inherit;cursor:pointer;padding:4px 10px;border-radius:8px;border:1px solid var(--line,#ccc);background:var(--panel,#fff);color:inherit"></button>
  </div>
  <div class="sub" id="hint" style="margin:0 0 12px"></div>
  <div class="tbl"><table id="t"></table></div>
</section>
<p class="note">Signals use weekly bars. The week in progress is marked <span class="new form">forming</span>: it only counts if it still qualifies at Friday's close. Stops are checked on weekly closes, so a stock can dip below a stop during the week and recover. For information only, not investment advice.</p>
</div>
<script>
const D = __DATA__;
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v, d=2) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const pc = (v, d=1) => v==null ? "–" : `<span class="${v>=0?'ok':'bad'}">${v>0?"+":""}${fmt(v,d)}%</span>`;
const dl = d => d ? new Date(d+"T00:00:00").toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"2-digit"}) : "–";
let view = "open";
const store = { get(k){ try { return localStorage.getItem(k); } catch(e){ return null; } }, set(k,v){ try { localStorage.setItem(k,v); } catch(e){} } };
const riskEl = document.getElementById("risk"), cleanEl = document.getElementById("clean");
riskEl.value = store.get("azh:buyrisk") || "";
document.getElementById("gen").textContent = `Updated ${D.generated}. Week ending ${dl(D.week)}${D.forming ? " (in progress)" : ""}.`;
const S = D.stats;
document.getElementById("stats").innerHTML = S ? `<h2>Track record of this rule</h2>
  <p class="sub">Every signal in the last ~5 years across all stocks here, using exactly these stops. Fewer than half win; the edge comes from letting winners run.</p>
  <div class="kpi"><div><b>${S.n.toLocaleString("en-IN")}</b><small>trades since ${dl(S.from)}</small></div>
    <div><b>${fmt(S.win,0)}%</b><small>closed with a profit</small></div>
    <div><b class="ok">+${fmt(S.avg_win,1)}%</b><small>average winner</small></div>
    <div><b class="bad">${fmt(S.avg_loss,1)}%</b><small>average loser</small></div>
    <div><b class="${S.exp>=0?'ok':'bad'}">${S.exp>0?"+":""}${fmt(S.exp,1)}%</b><small>average per trade · ${S.big}% reached +50% · typical hold ${S.hold} weeks</small></div></div>
  <p class="sub" style="margin:10px 0 0">Biggest winners: ${S.best.map(b=>`<button class="psym" data-p="${esc(b.sym)}">${esc(b.sym)}</button> +${b.r}% (from ${dl(b.sd)})`).join(" · ")}. Costs are not included.</p>
  <p class="sub" style="margin:6px 0 0">By year: ${(S.years||[]).map(y=>`${y.y}: ${y.n} trades, ${y.exp>0?"+":""}${fmt(y.exp,1)}% per trade, ${fmt(y.win,0)}% won`).join(" · ")}. Results swing a lot with the market: big in strong years, close to flat in choppy ones.</p>` : "";
function qty(entry, sl){ const r = +riskEl.value; if (!r || !entry || !sl || entry <= sl) return "–"; const q = Math.floor(r / (entry - sl)); return `${q.toLocaleString("en-IN")} <small class="mut">(₹${Math.round(q*entry).toLocaleString("en-IN")})</small>`; }
const flags = f => (f||[]).map(x=>`<span class="flag">${esc(x)}</span>`).join("");
const qabEl = document.getElementById("qab"); qabEl.checked = store.get("azh:buyqab") === "1";
const keep = r => (!cleanEl.checked || !(r.flags||[]).some(x=>x.startsWith("Surveillance"))) && (!qabEl.checked || ["A","B"].includes(r.grade));
const nm = r => `<td class="name"><button class="psym" data-p="${esc(r.sym)}">${esc(r.sym)}</button><small>${esc(r.name||"")}${r.sector?" · "+esc(r.sector):""}</small></td>`;
const statBox = (S, title) => !S || !S.n ? "" : `<div class="kpi" style="margin:0 0 12px"><div><b>${S.n}</b><small>${esc(title)}: entries since ${dl(S.from)} (${S.open} still open)</small></div>
  <div><b>${S.win!=null?fmt(S.win,0)+"%":"–"}</b><small>of ${S.closed} closed trades made money</small></div>
  <div><b class="ok">${S.avg_win!=null?"+"+fmt(S.avg_win,1)+"%":"–"}</b><small>average winner</small></div>
  <div><b class="bad">${S.avg_loss!=null?fmt(S.avg_loss,1)+"%":"–"}</b><small>average loss when stopped out${S.sl_hit!=null?` · ${S.sl_hit}% hit the first stop-loss`:""}</small></div>
  <div><b class="${(S.avg||0)>=0?'ok':'bad'}">${S.avg!=null?(S.avg>0?"+":"")+fmt(S.avg,1)+"%":"–"}</b><small>average per closed trade</small></div>${S.avg_all!=null?`<div><b class="${S.avg_all>=0?'ok':'bad'}">${(S.avg_all>0?"+":"")+fmt(S.avg_all,1)}%</b><small>average incl. open trades at today's price (${S.win_all}% in profit)</small></div>`:""}</div>`;
const stopOf = r => r.tr && r.tr.open && r.tr.sl ? r.tr.sl : r.price*0.92;
const trCells = r => { const x = r.tr; if (!x) return '<td>–</td><td>–</td><td>–</td>';
  return `<td>₹${fmt(x.ep)}<small class="mut" style="display:block">${dl(x.ed)}</small></td><td>${x.open ? `₹${fmt(r.price)}<small class="mut" style="display:block">now</small>` : `₹${fmt(x.xp)}<small class="bad" style="display:block">exited ${dl(x.xd)}${x.why?" · "+esc(x.why):""}</small>`}</td><td>${pc(x.g)}${x.mx!=null?`<small class="mut" style="display:block">max ${x.mx>0?"+":""}${fmt(x.mx,1)}%</small>`:""}</td>`; };
// ---------- sorting: [label, value of a row, default direction (1 = small first, -1 = big/newest first)] ----------
const NAME = ["Name (A–Z)", r=>r.sym, 1], RS = ["Relative strength (RS)", r=>r.rs, -1];
const TT = since => [["Default (leaders first)", null, 1], ["Entry date", r=>r.tr&&r.tr.ed, -1], RS, ["Gain", r=>r.tr&&r.tr.g, -1], ["Max gain since entry", r=>r.tr&&r.tr.mx, -1],
  ["Exit date", r=>r.tr&&r.tr.xd, -1], ["Nearest 52-week high", r=>r.hi, -1], ["Above 52-week low", r=>r.lo, -1], ["Room above the 50-day MA", r=>r.room, 1],
  ...(since ? [["Passing all 8 since", r=>r.since, -1]] : []), ["Price", r=>r.price, -1], NAME];
const SORTS = {
  open: [["Default", null, 1], ["Signal date", r=>r.sd, -1], RS, ["Gain now", r=>r.gain, -1], ["Max gain since entry", r=>r.best, -1], ["Risk %", r=>r.risk, 1],
         ["Room to the trailing stop", r=>r.room, 1], ["Breakout week gain", r=>r.wkg, -1], ["Quality grade", r=>r.grade, 1], NAME],
  watch: [["Default", null, 1], ["Distance to trigger", r=>r.dist, 1], RS, ["Nearest 52-week high", r=>r.hi52, -1], NAME],
  exits: [["Default", null, 1], ["Exit date", r=>r.xd, -1], ["Signal date", r=>r.sd, -1], ["Result", r=>r.r, -1], NAME],
  tt: TT(true), tt7: TT(false),
  t3: [["Default (newest first)", null, 1], ["Breakout date", r=>r.bd, -1], RS, ["Gain", r=>r.xd ? r.xg : r.gain, -1], ["Max gain since breakout", r=>r.mx, -1],
       ["Breakout week gain", r=>r.wk, -1], ["Touches", r=>r.touches, -1], ["Trendline length (weeks)", r=>r.span, -1], ["Strong first", r=>r.strong?1:0, -1], NAME],
  t3n: [["Default", null, 1], ["Distance to trigger", r=>r.dist, 1], RS, ["Touches", r=>r.touches, -1], ["Trendline length (weeks)", r=>r.span, -1], NAME],
};
const sortK = document.getElementById("sortk"), sortD = document.getElementById("sortd");
let sortView = null, sortDir = 1;
function sortUI(){
  if (sortView === view) return;
  sortView = view;
  const L = SORTS[view] || [];
  sortK.innerHTML = L.map((o,i)=>`<option value="${i}">${esc(o[0])}</option>`).join("");
  const saved = (store.get("azh:sort:"+view) || "").split(",");
  sortK.value = L[+saved[0]] ? saved[0] : "0";
  sortDir = saved[1] ? +saved[1] : (L[+sortK.value]||[0,0,1])[2];
  sortD.textContent = sortDir < 0 ? "↓ high to low" : "↑ low to high";
}
function srt(rows){
  sortUI();
  const o = (SORTS[view]||[])[+sortK.value];
  sortD.style.visibility = o && o[1] ? "visible" : "hidden";
  if (!o || !o[1]) return rows;
  const f = o[1];
  return rows.map((r,i)=>[f(r), i, r]).sort((a,b)=>{
    const x = a[0], y = b[0], nx = x==null || x==="" || (typeof x==="number" && !isFinite(x)), ny = y==null || y==="" || (typeof y==="number" && !isFinite(y));
    if (nx || ny) return nx && ny ? a[1]-b[1] : nx ? 1 : -1;          // blanks always last
    const c = typeof x==="string" ? x.localeCompare(y) : x - y;
    return c ? c * sortDir : a[1]-b[1];
  }).map(z=>z[2]);
}
sortK.onchange = () => { sortDir = ((SORTS[view]||[])[+sortK.value]||[0,0,1])[2]; store.set("azh:sort:"+view, sortK.value+","+sortDir); sortView = null; draw(); };
sortD.onclick = () => { sortDir = -sortDir; store.set("azh:sort:"+view, sortK.value+","+sortDir); sortView = null; draw(); };
function draw(){
  document.querySelectorAll(".tabs button").forEach(b=>b.setAttribute("aria-selected", b.dataset.v===view));
  const t = document.getElementById("t"), hint = document.getElementById("hint");
  if (view==="open"){
    const rows = srt(D.open.filter(keep));
    hint.innerHTML = `${rows.filter(r=>r.ago<=1).length} new signal(s) in the last two weeks, ${rows.length} open trade(s) in all. Enter at about the signal price; the quantity uses your risk per trade and the stop-loss.`;
    t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Signal week</th><th>Entry</th><th>Stop-loss</th><th>Risk</th><th>Trailing stop now</th><th>Price</th><th>Gain</th><th>Room to trail</th><th>Qty</th><th class="l">Notes</th></tr></thead><tbody>${rows.map(r=>`<tr>
      ${nm(r)}<td>${dl(r.sd)}${r.forming?'<span class="new form">forming</span>':r.ago===0?'<span class="new">new</span>':r.ago===1?'<span class="new">last week</span>':""}</td>
      <td>₹${fmt(r.entry)}</td><td>₹${fmt(r.sl)}</td><td>${fmt(r.risk,1)}%</td>
      <td><b>₹${fmt(r.trail)}</b><small class="mut" style="display:block">${esc(r.trail_kind)}</small></td>
      <td>₹${fmt(r.price)}</td><td>${pc(r.gain)}<small class="mut" style="display:block">best ${pc(r.best)}</small></td>
      <td>${pc(r.room)}</td><td>${qty(r.price, r.trail)}</td><td class="l">RS ${r.rs??"–"} · week +${fmt(r.wkg,1)}% · grade ${esc(r.grade||"–")} ${flags(r.flags)}</td></tr>`).join("") || '<tr><td colspan="11" class="mut">No open signals right now.</td></tr>'}</tbody>`;
  } else if (view==="watch"){
    const rows = srt(D.watch.filter(keep));
    hint.innerHTML = "Leaders near their highs, within 5% of the 12-week breakout level. A weekly close above both trigger levels makes it a signal.";
    t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Price</th><th>Breakout level</th><th>Distance</th><th>Weekly close needed (with +8%)</th><th>RS</th><th>From 52-wk high</th><th class="l">Notes</th></tr></thead><tbody>${rows.map(r=>`<tr>
      ${nm(r)}<td>₹${fmt(r.price)}</td><td>₹${fmt(r.trig)}</td><td>${fmt(r.dist,1)}%</td><td><b>₹${fmt(r.need8)}</b></td><td>${r.rs??"–"}</td><td>${pc(r.hi52)}</td><td class="l">${flags(r.flags)}</td></tr>`).join("") || '<tr><td colspan="8" class="mut">Nothing close to triggering.</td></tr>'}</tbody>`;
  } else if (view==="tt" || view==="tt7"){
    const T = D.tt || {all:[], near:[]}, rows = srt((view==="tt" ? T.all : T.near).filter(keep));
    hint.innerHTML = view==="tt" ? `Minervini's Stage 2 filter: price above the 50, 150 and 200-day MAs in that order, the 200-day rising, 30%+ above the 52-week low, within 25% of the high, RS 70+. ${rows.length} stocks pass. <b>Leader</b> = RS 90+ and within 5% of the 52-week high: in testing these did about twice as well as all passes (48% won, about +15% per trade vs +7%).`
      : "Stocks passing 7 of the 8 checks, with the one that is missing.";
    hint.innerHTML = statBox((T.stats||{})[view==="tt"?"8":"7"], view==="tt" ? "Trend Template 8/8" : "Trend Template 7/8") + hint.innerHTML +
      ` <b>Exit rule (dashboard rule, not part of Minervini's template):</b> entry = close on the day the stock freshly reaches ${view==="tt"?"8":"7"} of 8; stop-loss 8% below entry (Minervini's 7–8% max loss); after that, sell on a weekly (Friday) close below the 50-day MA.`;
    t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Entry</th><th>Now / exit</th><th>Gain</th><th>RS</th><th>From 52-wk high</th><th>Above 52-wk low</th><th>${view==="tt"?"Passing since":"Missing"}</th><th>Stop-loss (−8%)</th><th>Weekly close below (50-day MA)</th><th>Room</th><th>Qty</th></tr></thead><tbody>${rows.map(r=>`<tr>
      ${nm(r)}${trCells(r)}<td><b>${r.rs??"–"}</b>${r.lead?'<span class="new">leader</span>':""}</td><td>${pc(r.hi)}</td><td>+${fmt(r.lo,0)}%</td>
      <td class="${view==="tt"?"":"l"}" style="white-space:normal">${view==="tt" ? (r.since?`${dl(r.since)} <small class="mut">(${r.days} sessions)</small>`:"–") : esc(r.missing.join("; "))}${view==="tt"&&r.ideal?'<small class="ok" style="display:block">200-day rising 4+ months</small>':""}</td>
      <td>₹${fmt(stopOf(r))}</td><td>₹${fmt(r.exit)}</td><td>${pc(r.room)}</td><td>${qty(r.price, stopOf(r))}</td></tr>`).join("") || '<tr><td colspan="12" class="mut">None.</td></tr>'}</tbody>`;
  } else if (view==="t3" || view==="t3n"){
    const T = D.t3 || {brk:[], near:[]};
    const tl = r => `${r.touches} touches: ${r.tdates.map(d=>dl(d)).join(", ")} · ${r.span} weeks from the top ₹${fmt(r.top)} (${dl(r.top_d)})`;
    if (view==="t3"){
      const allr = T.brk.filter(keep), rows = srt(allr.filter(r=>r.alive || r.xd)), gone = allr.length - rows.length;
      hint.innerHTML = statBox((T.stats||{}).all, "All 3-touch breakouts") + statBox((T.stats||{}).strong, "Strong ones only") + (gone ? `${gone} breakouts are hidden. ` : "") + "Weekly close above a falling trendline that started at a major top and was touched at least 3 times over 6+ months (like E2E in May 2026). <b>Strong</b> = breakout week up 8%+ and RS in the top 40%: in testing these did about twice as well (47% won, about +12% per trade vs +6.6% for all). Stop-loss = breakout-week low; trailing stop = 10-week average.";
      t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Breakout week</th><th>Line at breakout</th><th>Entry (close)</th><th>Week</th><th>RS</th><th>Stop-loss</th><th>Trailing stop</th><th>Now / exit</th><th>Gain</th><th>Qty</th><th class="l">Trendline</th></tr></thead><tbody>${rows.map(r=>`<tr>
        ${nm(r)}<td>${dl(r.bd)}${r.forming?'<span class="new form">forming</span>':r.ago===0?'<span class="new">new</span>':""}${r.strong?'<span class="new">strong</span>':""}</td>
        <td>₹${fmt(r.lvl)}</td><td>₹${fmt(r.entry)}</td><td>${pc(r.wk)}</td><td>${r.rs??"–"}</td><td>₹${fmt(r.sl)}</td><td><b>₹${fmt(r.trail)}</b>${r.alive?"":'<small class="bad" style="display:block">closed below: exit</small>'}</td>
        <td>${r.xd ? `₹${fmt(r.xp)}<small class="bad" style="display:block">exited ${dl(r.xd)} (${esc(r.why||"")})</small>` : `₹${fmt(r.price)}<small class="mut" style="display:block">now</small>`}</td><td>${pc(r.xd ? r.xg : r.gain)}${r.mx!=null?`<small class="mut" style="display:block">max ${r.mx>0?"+":""}${fmt(r.mx,1)}%</small>`:""}</td><td>${r.xd ? "–" : qty(r.price, r.trail)}</td><td class="l" style="white-space:normal;min-width:240px;font-size:.8rem">${esc(tl(r))}</td></tr>`).join("") || '<tr><td colspan="12" class="mut">No 3-touch trendline breakouts in the last 26 weeks.</td></tr>'}</tbody>`;
    } else {
      const rows = srt(T.near.filter(keep));
      hint.innerHTML = "Still under a falling trendline touched 3+ times, within 5% of it. A weekly close above the trigger (2% over the line) makes it a breakout; best if that week is up 8%+.";
      t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Price</th><th>Line now</th><th>Weekly close needed</th><th>Distance</th><th>RS</th><th class="l">Trendline</th></tr></thead><tbody>${rows.map(r=>`<tr>
        ${nm(r)}<td>₹${fmt(r.price)}</td><td>₹${fmt(r.lvl)}</td><td><b>₹${fmt(r.trig)}</b></td><td>${fmt(r.dist,1)}%</td><td>${r.rs??"–"}</td><td class="l" style="white-space:normal;min-width:240px;font-size:.8rem">${esc(tl(r))}</td></tr>`).join("") || '<tr><td colspan="7" class="mut">Nothing near a 3-touch trendline.</td></tr>'}</tbody>`;
    }
  } else {
    hint.innerHTML = "Trades closed in the last 8 weeks by the stop-loss or trailing stop.";
    t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Signal week</th><th>Entry</th><th>Exit week</th><th>Exit</th><th>Result</th></tr></thead><tbody>${srt(D.exits).map(r=>`<tr>
      ${nm(r)}<td>${dl(r.sd)}</td><td>₹${fmt(r.entry)}</td><td>${dl(r.xd)}</td><td>₹${fmt(r.exit)}</td><td>${pc(r.r)}</td></tr>`).join("") || '<tr><td colspan="6" class="mut">No exits recently.</td></tr>'}</tbody>`;
  }
}
document.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>{ view=b.dataset.v; draw(); });
riskEl.oninput = () => { store.set("azh:buyrisk", riskEl.value); draw(); };
cleanEl.onchange = draw;
qabEl.onchange = () => { store.set("azh:buyqab", qabEl.checked ? "1" : "0"); draw(); };
draw();
fetch("buy_backtest.json", {cache:"no-cache"}).then(r=>r.ok?r.json():null).then(j=>{ if (!j) return;
  const p = document.createElement("p"); p.className = "sub"; p.style.margin = "10px 0 0";
  p.innerHTML = `<a href="buy_backtest.html" style="color:var(--focus);font-weight:600">Backtest from 2020 →</a> ${Object.values(j.res).map(r=>`${r.name}: ${r.ret>0?"+":""}${r.ret}%`).join(" · ")}`;
  document.getElementById("stats").appendChild(p); }).catch(()=>{});
</script>
<script src="profile.js" defer></script>
</body>
</html>
"""
