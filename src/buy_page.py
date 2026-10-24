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
    <div><b>5. Market filter</b><span>New entries only while market breadth is above 60%: more than 60% of liquid stocks closing above their own 50-day average. Below that, no new entries; open trades keep their stops.</span></div>
    <div><b>Stop-loss</b><span>Low of the breakout week. Exit if a week closes below it.</span></div>
    <div><b>Trailing stop</b><span>The 10-week average once it rises above the stop-loss. Exit on the first weekly close below it. Never move it down.</span></div>
  </div>
</section>

<section class="panel" id="mkt"></section>
<section class="panel" id="stats"></section>

<section class="panel">
  <div class="tabs" role="tablist">
    <button role="tab" data-v="open" aria-selected="true">Signals and open trades</button>
    <button role="tab" data-v="watch" aria-selected="false">Watch list</button>
    <button role="tab" data-v="exits" aria-selected="false">Recent exits</button>
    <button role="tab" data-v="tt" aria-selected="false">Trend Template 8/8</button>
    <button role="tab" data-v="tt7" aria-selected="false">Trend Template 7/8</button>
    <button role="tab" data-v="tte" aria-selected="false">Stage 2 start (early)</button>
    <button role="tab" data-v="ap" aria-selected="false">A-plus breakout</button>
    <button role="tab" data-v="smc" aria-selected="false">Weekly SMC</button>
    <button role="tab" data-v="cpr" aria-selected="false">CPR screener</button>
    <button role="tab" data-v="t3" aria-selected="false">3-touch trendline breakouts</button>
    <button role="tab" data-v="t3n" aria-selected="false">Near a 3-touch trendline</button>
    <button role="tab" data-v="log" aria-selected="false">All past trades (2 years)</button>
  </div>
  <div class="tools">
    <label class="tog">Risk per trade ₹ <input type="number" id="risk" min="0" step="500" placeholder="e.g. 5000"></label>
    <label class="tog"><input type="checkbox" id="clean" checked> Hide stocks under surveillance</label>
    <label class="tog"><input type="checkbox" id="qab"> Quality A or B only</label>
    <label class="tog">Sort by <select id="sortk" class="sel"></select></label>
    <button type="button" id="sortd" class="tog sel" title="Reverse the order" style="cursor:pointer"></button>
  </div>
  <div class="tools" id="logbar" style="display:none">
    <label class="tog">Rule <select id="lg_set" class="sel"><option value="by">Weekly momentum breakout (Buy criteria rule, breadth &gt; 60%)</option><option value="by50">Weekly momentum breakout, breadth &gt; 50%</option><option value="by0">Weekly momentum breakout, no market filter</option><option value="tt8">Trend Template 8/8</option><option value="tt7">Trend Template 7/8</option><option value="tte">Stage 2 start (early)</option><option value="t3">3-touch breakouts (all)</option><option value="t3s">3-touch breakouts (strong only)</option></select></label>
    <label class="tog">Show <select id="lg_st" class="sel"><option value="">All trades</option><option value="open">Still open</option><option value="closed">Closed</option><option value="win">Closed with a profit</option><option value="loss">Closed with a loss</option></select></label>
    <label class="tog">Entry year <select id="lg_y" class="sel"><option value="">All</option></select></label>
    <label class="tog">Stock <input type="search" id="lg_q" placeholder="e.g. HFCL" style="width:110px"></label>
    <button type="button" id="lg_csv" class="tog sel" style="cursor:pointer">⬇ Download CSV</button>
  </div>
  <div class="tools" id="ttebar" style="display:none">
    <b style="font-size:.85rem">Extra checks:</b>
    <label class="tog"><input type="checkbox" data-ck="vol"> Breakout volume ≥ 1.5× its 50-day average</label>
    <label class="tog"><input type="checkbox" data-ck="dry"> Volume dry-up before (10-day avg &lt; 70% of 50-day)</label>
    <label class="tog"><input type="checkbox" data-ck="res"> No entry within 5 trading days before results</label>
    <label class="tog"><input type="checkbox" data-ck="asm"> Skip stocks under ASM / GSM surveillance</label>
    <label class="tog">Show <select id="tte_span" class="sel"><option value="">signals of the last 3 months (latest per stock)</option><option value="all">every trade of the last 2 years</option></select></label>
  </div>
  <div class="tools" id="apbar" style="display:none">
    <b style="font-size:.85rem">Conditions:</b>
    <label class="tog"><input type="checkbox" data-ap="obv" checked> OBV rising in the base</label>
    <label class="tog"><input type="checkbox" data-ap="cmf" checked> CMF (21-wk) &gt; 0.05</label>
    <label class="tog"><input type="checkbox" data-ap="mrs" checked> Mansfield RS positive and rising</label>
    <label class="tog"><input type="checkbox" data-ap="cbase" checked> Choppiness 60+ in the base</label>
    <label class="tog">Choppiness on breakout week <select id="ap_chop" class="sel"><option value="50">below 50</option><option value="38.2">below 38.2 (strict)</option><option value="">any</option></select></label>
    <label class="tog">Breakout volume <select id="ap_vol" class="sel"><option value="2">≥ 2× its 20-wk average</option><option value="sd">&gt; average + 2 std dev (strict)</option><option value="">any</option></select></label>
    <label class="tog">RS at breakout <select id="ap_rs" class="sel"><option value="">any</option><option value="70">70+</option><option value="80">80+</option><option value="90">90+</option></select></label>
    <label class="tog">Show trades <select id="ap_span" class="sel"><option value="91">last 3 months</option><option value="">all 2 years</option></select></label>
  </div>
  <div class="tools" id="smcbar" style="display:none">
    <label class="tog">Target <select id="smc_tg" class="sel"><option value="3">3R (3 × risk)</option><option value="2">2R (2 × risk)</option></select></label>
    <label class="tog">RS at change of character <select id="smc_rs" class="sel"><option value="80">80+</option><option value="70">70+</option><option value="">any</option></select></label>
    <label class="tog">Show trades <select id="smc_span" class="sel"><option value="91">last 3 months</option><option value="">all 2 years</option></select></label>
  </div>
  <div class="tools" id="cprbar" style="display:none">
    <label class="tog">Show <select id="cp_view" class="sel"><option value="scr">Screener: setups now</option><option value="log">Trades of the last 2 years</option></select></label>
    <label class="tog">Levels <select id="cp_tf" class="sel"><option value="w">Weekly (from last week)</option><option value="m">Monthly (from last month)</option></select></label>
    <label class="tog">Setup <select id="cp_st" class="sel"><option value="b">Breakout above H4</option><option value="r">Reversal: back above L3</option></select></label>
    <label class="tog" id="cp_oz_l"><input type="checkbox" id="cp_oz" checked> Opened between H3 and H4</label>
    <label class="tog">RS <select id="cp_rs" class="sel"><option value="0">any</option><option value="70">70+</option><option value="80">80+</option><option value="90">90+</option></select></label>
    <label class="tog">Market breadth <select id="cp_br" class="sel"><option value="0">any</option><option value="50">above 50%</option><option value="60">above 60%</option></select></label>
    <label class="tog"><input type="checkbox" id="cp_up"> Above its 50-day MA</label>
    <label class="tog">CPR width <select id="cp_nw" class="sel"><option value="0">any</option><option value="2">narrow (under 2%)</option><option value="1">very narrow (under 1%)</option></select></label>
    <label class="tog" id="cp_all_l"><input type="checkbox" id="cp_all"> Show all stocks (not just setups)</label>
    <span class="tog" style="gap:6px">Best tested: <button type="button" class="sel" id="cp_p1" style="cursor:pointer">Weekly breakout, RS 80+</button><button type="button" class="sel" id="cp_p2" style="cursor:pointer">Monthly reversal, breadth 60%+</button></span>
  </div>
  <div class="sub" id="hint" style="margin:0 0 12px"></div>
  <div class="tbl"><table id="t"></table></div>
  <div id="more" style="margin:10px 0 0"></div>
</section>
<p class="note">Signals use weekly bars. The week in progress is marked <span class="new form">forming</span>: it only counts if it still qualifies at Friday's close. Stops are checked on weekly closes, so a stock can dip below a stop during the week and recover. For information only, not investment advice.</p>
</div>
<style>.sel{font:inherit;padding:4px 8px;border-radius:8px;border:1px solid var(--line,#ccc);background:var(--panel,#fff);color:inherit}</style>
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
const VLAB = {"60":"breadth above 60% (the rule)","50":"breadth above 50%","0":"no market filter"};
let bv = store.get("azh:bybv"); if (!VLAB[bv]) bv = "60";
const M = D.mkt || null;
const curOpen = () => bv==="60" ? D.open : ((D.open_v||{})[bv] || D.open);
const curExits = () => bv==="60" ? D.exits : ((D.exits_v||{})[bv] || D.exits);
function drawMkt(){
  if (!M) return;
  const thr = bv==="0" ? null : +bv, ok = thr==null || (M.now!=null && M.now > thr), line = thr ?? M.min;
  document.getElementById("mkt").innerHTML = `<h2>Market filter: ${thr==null ? '<span class="mut">off</span> (every breakout is a signal)' : ok ? '<span class="ok">new entries allowed</span>' : '<span class="bad">no new entries</span>'}</h2>
  <div class="tools" style="margin:0 0 8px"><label class="tog">Signals use <select id="bv" class="sel">${["60","50","0"].map(k=>`<option value="${k}"${k===bv?" selected":""}>${VLAB[k]}</option>`).join("")}</select></label></div>
  <p class="sub" style="margin:0">Market breadth now <b>${M.now ?? "–"}%</b> of liquid stocks above their 50-day average. ${thr==null ? "With the filter off you also get breakouts in weak markets: more trades, but in testing they averaged far less per trade." : ok ? `Above ${thr}%, so breakouts this week count as signals.` : `Breakouts are not taken until breadth is back above ${thr}%. Open trades keep their stops.`} This switch changes the signals, open trades, recent exits and track record on this page; the stock pop-up and the forward test follow the ${M.min}% rule.</p>
  <p class="sub" style="margin:6px 0 0">Last 26 weeks: ${(M.hist||[]).map(h=>`<span title="${dl(h[0])}: ${h[1]??"–"}%" style="display:inline-block;width:9px;height:${Math.max(3,(h[1]||0)/4)}px;margin-right:2px;vertical-align:bottom;border-radius:2px;background:${(h[1]||0)>line?'var(--up)':'var(--down)'}"></span>`).join("")} <small class="mut">green = above ${line}%</small></p>
  ${bv==="60" && (D.blocked||[]).length ? `<p class="sub" style="margin:6px 0 0">Breakouts skipped by the filter (this week and last): ${D.blocked.map(b=>`<button class="psym" data-p="${esc(b.sym)}">${esc(b.sym)}</button> <small class="mut">RS ${b.rs??"–"}</small>`).join(" · ")} <small class="mut">(switch to "no market filter" to see them as trades)</small></p>` : ""}`;
  const sel = document.getElementById("bv");
  sel.onchange = () => { bv = sel.value; store.set("azh:bybv", bv); drawMkt(); drawStats(); draw(); };
}
drawMkt();
function drawStats(){
  const V = (D.variants||{})[bv] || {}, S = V.stats || D.stats, T2 = V.two || {};
  const sg = v => v==null ? "–" : (v>0?"+":"")+fmt(v,1)+"%";
  const cmp = D.variants ? `<details style="margin:10px 0 0"><summary style="cursor:pointer"><b>Compare the market filters</b></summary><div class="tbl" style="margin:8px 0 0"><table><thead><tr><th class="l">Market filter</th><th>Trades (5 yr)</th><th>Won</th><th>Avg per trade (5 yr)</th><th>Trades (2 yr)</th><th>Avg per closed trade (2 yr)</th><th>Incl. open</th></tr></thead><tbody>${
      ["60","50","0"].map(k=>{ const x = D.variants[k]||{}, a = x.stats||{}, b = x.two||{}; return `<tr${k===bv?' style="font-weight:700"':""}><td class="l">${VLAB[k]}</td><td>${a.n??"–"}</td><td>${a.win!=null?a.win+"%":"–"}</td><td>${sg(a.exp)}</td><td>${b.n??"–"}</td><td>${sg(b.exp)}</td><td>${sg(b.exp_all)}</td></tr>`; }).join("")}</tbody></table></div></details>` : "";
  document.getElementById("stats").innerHTML = S ? `<h2>Track record of this rule</h2>
  <p class="sub">Every signal in the last ~5 years across all stocks here, using exactly these stops. Fewer than half win; the edge comes from letting winners run.</p>
  ${D.variants ? `<p class="sub" style="margin:0 0 10px">Market filter: <b>${VLAB[bv]}</b> <small class="mut">(change it at the top of the page)</small></p>` : ""}
  <div class="kpi"><div><b>${S.n.toLocaleString("en-IN")}</b><small>trades since ${dl(S.from)}</small></div>
    <div><b>${fmt(S.win,0)}%</b><small>closed with a profit</small></div>
    <div><b class="ok">+${fmt(S.avg_win,1)}%</b><small>average winner</small></div>
    <div><b class="bad">${fmt(S.avg_loss,1)}%</b><small>average loser</small></div>
    <div><b class="${S.exp>=0?'ok':'bad'}">${S.exp>0?"+":""}${fmt(S.exp,1)}%</b><small>average per trade · ${S.big}% reached +50% · typical hold ${S.hold} weeks</small></div></div>
  ${T2.n!=null ? `<p class="sub" style="margin:10px 0 0"><b>Last 2 years:</b> ${T2.n} closed trades, ${T2.win??"–"}% won, ${sg(T2.exp)} per closed trade; ${sg(T2.exp_all)} including ${T2.nopen} open trade${T2.nopen===1?"":"s"} at today's price.</p>` : ""}
  <p class="sub" style="margin:10px 0 0">Biggest winners: ${S.best.map(b=>`<button class="psym" data-p="${esc(b.sym)}">${esc(b.sym)}</button> +${b.r}% (from ${dl(b.sd)})`).join(" · ")}. Costs are not included.</p>
  <p class="sub" style="margin:6px 0 0">By year: ${(S.years||[]).map(y=>`${y.y}: ${y.n} trades, ${y.exp>0?"+":""}${fmt(y.exp,1)}% per trade, ${fmt(y.win,0)}% won`).join(" · ")}. Results swing a lot with the market: big in strong years, close to flat in choppy ones.</p>
  ${cmp}
  <p class="sub" style="margin:6px 0 0"><a href="#" id="seeby" style="color:var(--focus);font-weight:600">See every trade of the last 2 years →</a></p>` : "";
}
drawStats();
document.addEventListener("click", ev => { if (ev.target && ev.target.id === "seeby"){ ev.preventDefault();
  document.getElementById("lg_set").value = bv === "60" ? "by" : "by" + bv; view = "log"; logN = 300; draw(); document.querySelector(".tabs").scrollIntoView({behavior:"smooth"}); } });
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
  tte: [["Default (open first, newest)", null, 1], ["Entry date", r=>r.tr&&r.tr.ed, -1], ["RS at entry", r=>r.tr&&r.tr.fl&&r.tr.fl[5], -1], ["RS now", r=>r.rs, -1], ["Gain", r=>r.tr&&r.tr.g, -1], ["Max gain since entry", r=>r.tr&&r.tr.mx, -1],
        ["Exit date", r=>r.tr&&r.tr.xd, -1], ["Divergence warning first", r=>r.tr&&r.tr.div?(r.tr.div.ago<=20?2:1):0, -1], ["Nearest 52-week high", r=>r.hi, -1], ["Template checks passed now", r=>r.k, -1], ["Room above the 50-day MA", r=>r.room, 1], ["Price", r=>r.price, -1], NAME],
  t3: [["Default (newest first)", null, 1], ["Breakout date", r=>r.bd, -1], RS, ["Gain", r=>r.xd ? r.xg : r.gain, -1], ["Max gain since breakout", r=>r.mx, -1],
       ["Breakout week gain", r=>r.wk, -1], ["Touches", r=>r.touches, -1], ["Trendline length (weeks)", r=>r.span, -1], ["Strong first", r=>r.strong?1:0, -1], NAME],
  cpr: [["Default (entries first, then closest to the trigger)", null, 1], ["RS", r=>r.rs, -1], ["Distance to trigger", r=>r.dist, 1], ["CPR width (narrowest)", r=>r.cw, 1], ["Entry date", r=>r.ed, -1], ["Gain", r=>r.g, -1], ["Price", r=>r.price, -1], NAME],
  smc: [["Entry week (newest)", r=>r.ed, -1], ["Gain", r=>r.g, -1], ["Max gain", r=>r.mx, -1], ["RS", r=>r.rs, -1], ["Still open first", r=>r.open?1:0, -1], NAME],
  ap: [["Breakout week (newest)", r=>r.ed, -1], RS, ["Gain", r=>r.g, -1], ["Max gain", r=>r.mx, -1], ["Volume ×", r=>r.a[14], -1], ["Still open first", r=>r.open?1:0, -1], NAME],
  log: [["Entry date", r=>r.ed, -1], ["Exit date", r=>r.xd, -1], ["Gain", r=>r.g, -1], ["Max gain", r=>r.mx, -1], ["Days / weeks held", r=>r.days, -1], ["Entry price", r=>r.ep, -1], NAME],
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
  sortK.value = saved[0] !== "" && L[+saved[0]] ? saved[0] : "0";
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
// ---------- Stage 2 start: extra checks, switched on the page ----------
const ECK = ["vol","dry","res","asm"], ELAB = {vol:"breakout volume", dry:"volume dry-up", res:"no results within 5 days", asm:"no surveillance"};
const eck = {}; ECK.forEach(k=>eck[k] = store.get("azh:eck:"+k) === "1");
document.querySelectorAll("#ttebar [data-ck]").forEach(cb=>{ cb.checked = eck[cb.dataset.ck]; cb.onchange = () => { eck[cb.dataset.ck] = cb.checked; store.set("azh:eck:"+cb.dataset.ck, cb.checked?"1":"0"); draw(); }; });
// f = [volume ratio, dry-up ratio, results soon, surveillance, chop]; a check that can't be measured passes
function passE(f, c){ c = c || eck; f = f || [];
  if (c.vol && f[0]!=null && !(f[0] >= 1.5)) return false;
  if (c.dry && f[1]!=null && !(f[1] < 0.7)) return false;
  if (c.res && f[2]===true) return false;
  if (c.asm && f[3]===true) return false;
  return true; }
function estats(L){
  const cl = L.filter(a=>a[3]), g = cl.map(a=>a[5]), all = L.map(a=>a[5]), w = g.filter(x=>x>0), l = g.filter(x=>x<=0), m = a => a.length ? a.reduce((s,x)=>s+x,0)/a.length : null, r1 = v => v==null ? null : Math.round(v*10)/10;
  return {n:L.length, closed:cl.length, open:L.length-cl.length, win: cl.length ? Math.round(w.length/cl.length*100) : null, avg_win:r1(m(w)), avg_loss:r1(m(l)), avg:r1(m(g)),
          avg_all:r1(m(all)), win_all: all.length ? Math.round(all.filter(x=>x>0).length/all.length*100) : null, big: all.length ? Math.round(L.filter(a=>a[6]>=30).length/all.length*100) : null,
          sl_hit: cl.length ? Math.round(cl.filter(a=>a[7]==="Stop-loss"||a[7]==="Emergency stop").length/cl.length*100) : null, from:(D.tt&&D.tt.stats&&D.tt.stats.e||{}).from}; }
// ---------- A-plus breakout composite (aplus.json, loaded when the tab is opened) ----------
const $id = id => document.getElementById(id);
let AP = null, apLoading = false;
const APK = ["obv","cmf","mrs","cbase"];
const apc = {}; APK.forEach(k=>{ const v = store.get("azh:ap:"+k); apc[k] = v===null ? true : v==="1"; });
document.querySelectorAll("#apbar [data-ap]").forEach(cb=>{ cb.checked = apc[cb.dataset.ap]; cb.onchange = () => { apc[cb.dataset.ap] = cb.checked; store.set("azh:ap:"+cb.dataset.ap, cb.checked?"1":"0"); draw(); }; });
let apN = 200;
["ap_chop","ap_vol","ap_rs","ap_span","tte_span"].forEach(id=>{ const el = $id(id), v = store.get("azh:"+id); if (v!==null) el.value = v; el.onchange = () => { store.set("azh:"+id, el.value); apN = 200; draw(); }; });
// log row: 9 OBV ok, 10 CMF, 11 Mansfield ok, 12 chop max in base, 13 chop now, 14 volume x, 15 vol > avg+2sd, 16 turnover, 17 RS, 18 base %, 19 forming
function apPass(a, c){
  c = c || {obv:apc.obv, cmf:apc.cmf, mrs:apc.mrs, cbase:apc.cbase, chop:$id("ap_chop").value, vol:$id("ap_vol").value, rs:$id("ap_rs").value};
  if (c.obv && !a[9]) return false;
  if (c.cmf && !(a[10] > 0.05)) return false;
  if (c.mrs && !a[11]) return false;
  if (c.cbase && !(a[12] >= 60)) return false;
  if (c.chop && !(a[13] != null && a[13] < +c.chop)) return false;
  if (c.vol === "2" && !(a[14] >= 2)) return false;
  if (c.vol === "sd" && !a[15]) return false;
  if (c.rs && !(a[17] >= +c.rs)) return false;
  return true; }
function apStats(L){ return estats(L); }
function drawAP(t, hint){
  if (!AP){
    hint.textContent = "Loading the A-plus breakout list…"; t.innerHTML = "";
    if (!apLoading){ apLoading = true;
      fetch("aplus.json", {cache:"no-cache"}).then(r=>r.ok?r.json():Promise.reject()).then(j=>{ AP = j; if (view==="ap") draw(); })
        .catch(()=>{ hint.textContent = "The A-plus list appears after the next full update."; }); }
    return;
  }
  const P = AP.params, L = AP.log, sel = L.filter(a=>apPass(a)), S = apStats(sel);
  const ALL = {obv:1, cmf:1, mrs:1, cbase:1, chop:"50", vol:"2", rs:""};
  const rowsC = [["Tight base breakout only", {}], ["+ OBV rising", {obv:1}], ["+ CMF > 0.05", {cmf:1}], ["+ Mansfield RS rising", {mrs:1}],
    ["+ Choppiness 60+ → below 50", {cbase:1, chop:"50"}], ["+ Choppiness 60+ → below 38.2", {cbase:1, chop:"38.2"}],
    ["+ volume ≥ 2×", {vol:"2"}], ["+ volume > avg + 2 sd", {vol:"sd"}], ["+ RS 80+", {rs:"80"}], ["+ RS 90+", {rs:"90"}], ["+ volume 2× and RS 90+", {vol:"2", rs:"90"}],
    ["A-plus (all, Chop < 50, vol 2×)", ALL], ["A-plus strict (Chop < 38.2, vol + 2 sd)", {...ALL, chop:"38.2", vol:"sd"}], ["A-plus + RS 80+", {...ALL, rs:"80"}]];
  const sg = v => v==null ? "–" : (v>0?"+":"")+fmt(v,1)+"%";
  hint.innerHTML = statBox({...S, from: AP.since}, "A-plus breakouts with your settings") +
    `<details style="margin:0 0 10px"><summary style="cursor:pointer"><b>Compare the conditions</b> (every tight-base breakout of the last 2 years)</summary><div class="tbl" style="margin:8px 0 0"><table style="font-size:.85rem"><thead><tr><th class="l">Rule</th><th>Trades</th><th>Won</th><th>Avg win</th><th>Avg loss</th><th>Per closed trade</th><th>Incl. open</th><th>Hit +30%</th></tr></thead><tbody>${
      rowsC.map(([n, c])=>{ const X = estats(L.filter(a=>apPass(a, c))); return `<tr><td class="l">${n}</td><td>${X.n}</td><td>${X.win!=null?X.win+"%":"–"}</td><td class="ok">${sg(X.avg_win)}</td><td class="bad">${sg(X.avg_loss)}</td><td><b>${sg(X.avg)}</b></td><td>${sg(X.avg_all)}</td><td>${X.big!=null?X.big+"%":"–"}</td></tr>`; }).join("")}</tbody></table></div></details>` +
    `Weekly setup: a ${P.base_w}-week base whose range is under ${P.tight}% of its low, quietly accumulated (OBV above its rising 10-week average, CMF above ${P.cmf}, Mansfield RS vs NIFTY positive and rising, Choppiness 60+ = a real sideways range), then a weekly close above the base high on volume at least ${P.vol_x}× normal with Choppiness falling. Liquidity: at least ₹${P.turn} crore traded a week. Ranked by RS. <b>Exit</b>: first daily close below the 50-day MA, emergency stop ${P.stop}% below entry.${AP.has_volume ? "" : " <b>Volume data is missing, so the volume, OBV and CMF conditions can't be checked yet.</b>"}`;
  const span = $id("ap_span").value, cut = span ? new Date(Date.now() - (+span)*864e5).toISOString().slice(0,10) : "";
  let rows = sel.filter(a=>a[1] >= cut).map(a=>({sym:a[0], name:AP.names[a[0]], sector:(AP.sectors||{})[a[0]], a, ed:a[1], g:a[5], mx:a[6], rs:a[17], open:!a[3]}));
  rows = srt(rows);
  const total = rows.length; rows = rows.slice(0, apN);
  const more = $id("more");
  more.innerHTML = total > apN ? `<button type="button" class="sel" style="cursor:pointer" id="ap_more">Show ${Math.min(300, total-apN)} more (${total-apN} hidden)</button>` : "";
  if ($id("ap_more")) $id("ap_more").onclick = () => { apN += 300; draw(); };
  const W = AP.watch.filter(w=>(!apc.obv || w.obv) && (!apc.mrs || w.mrs) && (!apc.cmf || w.cmf > 0.05) && (!apc.cbase || w.chopmax >= 60));
  const yes = (v, txt) => v ? `<span class="ok">${txt||"✓"}</span>` : `<span class="bad">${txt||"✗"}</span>`;
  t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Breakout week</th><th>Entry</th><th>Now / exit</th><th>Gain</th><th>RS</th><th>Volume</th><th>CMF</th><th>OBV</th><th>Mansfield</th><th>Choppiness base → week</th><th>Base range</th><th>Emergency stop</th><th>Qty</th></tr></thead><tbody><tr><td colspan="14" class="l"><b>${total} trade${total===1?"":"s"}</b> <span class="mut">${span ? "from the last 3 months" : "from the last 2 years"} with your settings${total>apN?`, showing ${apN}`:""}</span></td></tr>${rows.map(r=>{ const a = r.a; return `<tr>
    ${nm(r)}<td>${dl(a[1])}${a[19]?'<span class="new form">forming</span>':""}</td><td>₹${fmt(a[2])}</td>
    <td>₹${fmt(a[4])}${a[3]?`<small class="bad" style="display:block">exited ${dl(a[3])} · ${esc(a[7]||"")}</small>`:'<small class="mut" style="display:block">now</small>'}</td>
    <td>${pc(a[5])}<small class="mut" style="display:block">max ${a[6]>0?"+":""}${fmt(a[6],1)}%</small></td><td><b>${a[17]??"–"}</b></td>
    <td>${a[14]!=null?yes(a[14]>=2, fmt(a[14],1)+"×"):"–"}${a[15]?'<small class="ok" style="display:block">+2 sd</small>':""}</td><td>${a[10]!=null?yes(a[10]>0.05, fmt(a[10],2)):"–"}</td>
    <td>${yes(a[9])}</td><td>${yes(a[11])}</td><td>${a[12]??"–"} → ${a[13]??"–"}</td><td>${a[18]??"–"}%</td>
    <td>${a[3]?"–":"₹"+fmt(a[2]*(1-P.stop/100))}</td><td>${a[3]?"–":qty(a[4], a[2]*(1-P.stop/100))}</td></tr>`; }).join("") || '<tr><td colspan="14" class="mut">No A-plus breakouts with these settings in this period.</td></tr>'}</tbody>
    <tbody><tr><td colspan="14" class="l" style="padding-top:18px"><b>Watch list: bases forming now</b> <span class="mut">(tight ${P.base_w}-week base, price within 5% of the base high, conditions you ticked already met; a weekly close above the trigger on heavy volume makes it a breakout)</span></td></tr>
    ${W.slice(0,60).map(w=>`<tr>${nm(w)}<td colspan="2">Trigger <b>₹${fmt(w.trig)}</b> <span class="mut">(${fmt(w.dist,1)}% away)</span></td><td>₹${fmt(w.price)}</td><td></td><td><b>${w.rs??"–"}</b></td><td></td><td>${w.cmf!=null?yes(w.cmf>0.05, fmt(w.cmf,2)):"–"}</td><td>${yes(w.obv)}</td><td>${yes(w.mrs)}</td><td>${w.chopmax??"–"} → ${w.chop??"–"}</td><td>${w.tight}%</td><td colspan="2"></td></tr>`).join("") || '<tr><td colspan="14" class="mut">No bases close to breaking out with these conditions.</td></tr>'}</tbody>`;
}
// ---------- CPR screener (cpr.json, loaded when the tab is opened) ----------
let CPR = null, cprLoading = false, cpN = 200;
const CPI = ["cp_view","cp_tf","cp_st","cp_oz","cp_rs","cp_br","cp_up","cp_nw","cp_all"];
CPI.forEach(id=>{ const el = document.getElementById(id), v = store.get("azh:"+id);
  if (v!==null){ if (el.type==="checkbox") el.checked = v==="1"; else el.value = v; }
  el.onchange = () => { store.set("azh:"+id, el.type==="checkbox" ? (el.checked?"1":"0") : el.value); cpN = 200; draw(); }; });
if (store.get("azh:cp_rs")===null) document.getElementById("cp_rs").value = "80";
function cpPreset(v){ const set = (id, x) => { const el = document.getElementById(id); if (el.type==="checkbox") el.checked = !!x; else el.value = x; store.set("azh:"+id, el.type==="checkbox" ? (x?"1":"0") : String(x)); };
  Object.entries(v).forEach(([k, x])=>set(k, x)); cpN = 200; draw(); }
document.getElementById("cp_p1").onclick = () => cpPreset({cp_tf:"w", cp_st:"b", cp_oz:1, cp_rs:"80", cp_br:"0", cp_up:0, cp_nw:"0"});
document.getElementById("cp_p2").onclick = () => cpPreset({cp_tf:"m", cp_st:"r", cp_rs:"0", cp_br:"60", cp_up:0, cp_nw:"0"});
const CPST = {waiting:"Waiting", entered:"Entered", failed:"Failed", below:"Below L3 now"};
// log row: 0 sym, 1 entry date, 2 entry, 3 exit date (null = running), 4 exit/now, 5 gain, 6 reason, 7 days, 8 stop, 9 target,
//          10 opened H3-H4 / inside, 11 RS, 12 above 50-DMA, 13 breadth, 14 CPR width
function drawCPR(t, hint){
  const $ = id => document.getElementById(id);
  if (!CPR){
    hint.textContent = "Loading the CPR levels…"; t.innerHTML = "";
    if (!cprLoading){ cprLoading = true;
      fetch("cpr.json", {cache:"no-cache"}).then(r=>r.ok?r.json():Promise.reject()).then(j=>{ CPR = j; if (view==="cpr") draw(); })
        .catch(()=>{ hint.textContent = "The CPR screener appears after the next update."; }); }
    return;
  }
  const tf = $("cp_tf").value, st = $("cp_st").value, rsMin = +$("cp_rs").value, brMin = +$("cp_br").value, up = $("cp_up").checked,
        nw = +$("cp_nw").value, oz = st==="b" && $("cp_oz").checked, mode = $("cp_view").value, all = $("cp_all").checked;
  $("cp_oz_l").style.display = st==="b" ? "" : "none"; $("cp_all_l").style.display = mode==="scr" ? "" : "none";
  const per = tf==="w" ? "week" : "month", key = tf + st, sg = v => v==null ? "–" : (v>0?"+":"")+fmt(v,2)+"%";
  const S = (CPR.stats||{})[`${key}|${oz?1:0}|${rsMin}|${brMin}|${up?1:0}|${nw}`];
  const rule = st==="b" ? `${oz?"the "+per+" opened between H3 and H4; ":""}buy when price goes above <b>H4</b>; stop <b>H3</b>; target <b>H5</b>`
                        : `price dips below <b>L3</b> and closes back above it: buy that close; stop <b>L4</b>; target <b>H3</b>`;
  const label = `${tf==="w"?"Weekly":"Monthly"} ${st==="b"?"breakout":"reversal"}${rsMin?`, RS ${rsMin}+`:""}${brMin?`, breadth above ${brMin}%`:""}${up?", above the 50-day MA":""}${nw?`, CPR under ${nw}%`:""}`;
  const statHtml = S ? `<div class="kpi" style="margin:0 0 10px"><div><b>${S[0].toLocaleString("en-IN")}</b><small>${esc(label)}: trades in 2 years</small></div>
      <div><b>${S[1]}%</b><small>won</small></div><div><b class="ok">${sg(S[3])}</b><small>average winner</small></div><div><b class="bad">${sg(S[4])}</b><small>average loser</small></div>
      <div><b class="${S[2]>=0?'ok':'bad'}">${sg(S[2])}</b><small>average per trade after costs · year 1 ${sg(S[5])} (${S[8]}) · year 2 ${sg(S[6])} (${S[9]}) · typical hold ${S[7]} day${S[7]===1?"":"s"}</small></div></div>`
    : `<p class="sub">No tested trades with these settings.</p>`;
  const cmp = [["Weekly breakout (opened H3–H4)","wb|1|0|0|0|0"],["Weekly breakout, RS 80+","wb|1|80|0|0|0"],["Weekly breakout, any open","wb|0|0|0|0|0"],["Weekly reversal","wr|0|0|0|0|0"],
               ["Monthly breakout (opened H3–H4)","mb|1|0|0|0|0"],["Monthly reversal","mr|0|0|0|0|0"],["Monthly reversal, breadth 60%+","mr|0|0|60|0|0"],["Monthly reversal, breadth 60%+, RS 80+, above 50-DMA","mr|0|80|60|1|0"]];
  const cmpHtml = `<details style="margin:0 0 10px"><summary style="cursor:pointer"><b>Compare the versions</b> (2 years, 0.15% costs)</summary><div class="tbl" style="margin:8px 0 0"><table><thead><tr><th class="l">Version</th><th>Trades</th><th>Won</th><th>Avg per trade</th><th>Year 1</th><th>Year 2</th></tr></thead><tbody>${
      cmp.map(([n,k])=>{ const x = (CPR.stats||{})[k]; return x ? `<tr><td class="l">${n}</td><td>${x[0]}</td><td>${x[1]}%</td><td><b>${sg(x[2])}</b></td><td>${sg(x[5])}</td><td>${sg(x[6])}</td></tr>` : ""; }).join("")}</tbody></table></div>
      <p class="sub" style="margin:6px 0 0">Levels from the previous ${per}: H3 = C + 1.1×range/4, H4 = C + 1.1×range/2, H5 = C × H/L, L3 = C − 1.1×range/4, L4 = C − 1.1×range/2. CPR = pivot (H+L+C)/3 with BC = (H+L)/2 and TC = 2×pivot − BC; narrow CPR = a quiet ${per} before. A trade still open when the ${per} ends is closed at its last close. Entries assume a fill exactly at H4 / L3, so gaps and slippage will cost a little more.</p></details>`;
  const brNow = CPR.breadth;
  const brWarn = brMin && brNow!=null && brNow <= brMin ? `<p class="sub" style="margin:0 0 8px"><span class="flag">Market breadth is ${brNow}% now, below your ${brMin}% filter: new entries are not taken.</span></p>` : "";
  const more = $("more");
  if (mode === "log"){
    const L = ((CPR.logs||{})[key]||[]).filter(a=>(!oz || a[10]) && (a[11]||0) >= rsMin && (!brMin || (a[13]||0) > brMin) && (!up || a[12]) && (!nw || (a[14]!=null && a[14] < nw)));
    const limited = key==="wr" ? `Trade list: the last 3 months only (the full ${CPR.since ? "2 years" : ""} is in the numbers above).` : key==="mr" && brMin < 60 ? "Trade list: all trades with breadth above 60%, and every trade of the last 3 months." : "";
    hint.innerHTML = statHtml + cmpHtml + `<p class="sub" style="margin:0 0 8px">${esc(label)}: ${rule}. ${limited}</p>`;
    let rows = L.map(a=>({sym:a[0], name:(CPR.names[a[0]]||[])[0], sector:(CPR.names[a[0]]||[])[1], a, ed:a[1], g:a[5], rs:a[11], dist:null, cw:a[14], price:a[4]}));
    rows = srt(rows); const total = rows.length; rows = rows.slice(0, cpN);
    more.innerHTML = total > cpN ? `<button type="button" class="sel" style="cursor:pointer" id="cp_more">Show ${Math.min(500,total-cpN)} more (${total-cpN} hidden)</button>` : "";
    if ($("cp_more")) $("cp_more").onclick = () => { cpN += 500; draw(); };
    t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Entry</th><th>Exit</th><th>Gain</th><th>Stop</th><th>Target</th><th>Days</th><th>RS</th><th>Breadth</th><th>CPR width</th></tr></thead><tbody>${rows.map(r=>{ const a = r.a; return `<tr>${nm(r)}
      <td>₹${fmt(a[2])}<small class="mut" style="display:block">${dl(a[1])}</small></td>
      <td>₹${fmt(a[4])}<small class="${a[3]?(a[5]>0?'ok':'bad'):'mut'}" style="display:block">${a[3]?dl(a[3])+" · "+esc(a[6]||""):"running"}</small></td>
      <td>${pc(a[5],2)}</td><td>₹${fmt(a[8])}</td><td>₹${fmt(a[9])}</td><td>${a[7]}</td><td>${a[11]??"–"}</td><td>${a[13]??"–"}%</td><td>${a[14]!=null?fmt(a[14],2)+"%":"–"}</td></tr>`; }).join("") || '<tr><td colspan="10" class="mut">No trades with these settings.</td></tr>'}</tbody>`;
    return;
  }
  // screener: every liquid stock against this period's levels
  let rows = (CPR.rows||[]).map(r=>{ const z = r[tf]||{}, d = z[st]||{};
    const trig = st==="b" ? z.h4 : z.l3, dist = trig && r.price ? (trig / r.price - 1) * 100 : null;
    const pri = d.st==="entered" ? (d.x ? 2 : 0) : (st==="b" ? (d.st==="waiting" && d.oz ? 1 : 3) : (d.st==="below" ? 1 : 3));
    return {...r, z, d, dist: st==="b" ? dist : (d.st==="below" ? -dist : dist), cw: z.w, ed: d.st==="entered" ? d.ago : null, g: d.g, pri}; })
    .filter(r=>(r.rs||0) >= rsMin && (!up || r.up) && (!nw || (r.cw!=null && r.cw < nw)));
  if (!all) rows = rows.filter(r=> st==="b" ? ((r.d.st==="waiting" || r.d.st==="entered") && (!oz || r.d.oz)) : (r.d.st==="below" || r.d.st==="entered"));
  const nE = rows.filter(r=>r.d.st==="entered").length, nW = rows.filter(r=>r.d.st==="waiting" || r.d.st==="below").length;
  rows = srt(rows);
  if (+sortK.value === 0) rows.sort((a,b)=> a.pri-b.pri || (a.d.ago??99)-(b.d.ago??99) || Math.abs(a.dist??99)-Math.abs(b.dist??99));
  const total = rows.length; rows = rows.slice(0, cpN);
  more.innerHTML = total > cpN ? `<button type="button" class="sel" style="cursor:pointer" id="cp_more">Show ${Math.min(500,total-cpN)} more (${total-cpN} hidden)</button>` : "";
  if ($("cp_more")) $("cp_more").onclick = () => { cpN += 500; draw(); };
  hint.innerHTML = statHtml + cmpHtml + brWarn + `<p class="sub" style="margin:0 0 8px"><b>${esc(label)}</b>: ${rule}. This ${per}: <b>${nE}</b> entered, <b>${nW}</b> ${st==="b"?"waiting for a break above H4":"below L3 now (a close back above L3 is the entry)"}. Levels as of ${dl(CPR.asof)}; market breadth ${brNow ?? "–"}%.</p>`;
  const zl = {">H4":"above H4","H3-H4":"H3–H4","L3-H3":"inside","L4-L3":"L4–L3","<L4":"below L4"};
  t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Status</th><th>Price</th><th>${st==="b"?"Buy above (H4)":"Buy on a close above (L3)"}</th><th>Stop (${st==="b"?"H3":"L4"})</th><th>Target (${st==="b"?"H5":"H3"})</th><th>Now / opened</th><th>CPR width</th><th>RS</th><th>50-DMA</th></tr></thead><tbody>${rows.map(r=>{ const z = r.z, d = r.d;
    const stx = d.st==="entered" ? (d.x ? `<span class="mut">entered ${d.ago}d ago, closed</span><small class="${d.g>0?'ok':'bad'}" style="display:block">${esc(d.x)} · ${pc(d.g,1)}</small>`
              : `<span class="new">${d.ago===0?"entered today":"entered "+d.ago+"d ago"}</span><small class="mut" style="display:block">at ₹${fmt(d.e)} · ${pc(d.g,1)} now</small>`)
              : d.st==="failed" ? `<span class="mut">${st==="b"?"failed (fell below H3)":"failed (hit L4)"}</span>` : `${esc(CPST[d.st]||"–")}${st==="b" && d.st==="waiting" && !d.oz ? '<small class="mut" style="display:block">did not open H3–H4</small>' : ""}`;
    return `<tr>${nm(r)}<td>${stx}</td><td>₹${fmt(r.price)}</td>
      <td><b>₹${fmt(st==="b"?z.h4:z.l3)}</b>${r.dist!=null && d.st!=="entered"?`<small class="mut" style="display:block">${fmt(Math.abs(r.dist),1)}% ${st==="b"?(r.dist>0?"away":"above"):(d.st==="below"?"above price":"below price")}</small>`:""}</td>
      <td>₹${fmt(st==="b"?z.h3:z.l4)}</td><td>₹${fmt(st==="b"?z.h5:z.h3)}</td>
      <td>${zl[z.zn]||"–"}<small class="mut" style="display:block">opened ${zl[z.zo]||"–"}</small></td>
      <td>${z.w!=null?fmt(z.w,2)+"%":"–"}<small class="mut" style="display:block">${z.rise==="higher"?"rising":z.rise==="lower"?"falling":z.rise?"flat":""}</small></td>
      <td>${r.rs??"–"}</td><td>${r.up==null?"–":r.up?'<span class="ok">above</span>':'<span class="bad">below</span>'}</td></tr>`; }).join("") || '<tr><td colspan="10" class="mut">No stocks match right now. Tick "Show all stocks" to see every stock against its levels.</td></tr>'}</tbody>`;
}
// ---------- Weekly SMC (smc.json, loaded when the tab is opened) ----------
let SMC = null, smcLoading = false, smcN = 200;
["smc_tg","smc_rs","smc_span"].forEach(id=>{ const el = document.getElementById(id), v = store.get("azh:"+id); if (v!==null) el.value = v;
  el.onchange = () => { store.set("azh:"+id, el.value); smcN = 200; draw(); }; });
// log row: 0 sym, 1 entry week, 2 entry, 3 exit week, 4 exit/now, 5 gain, 6 max gain, 7 reason, 8 weeks, 9 risk %, 10 RS, 11 stop, 12 target, 13 CHoCH week
function drawSMC(t, hint){
  const $ = id => document.getElementById(id);
  if (!SMC){
    hint.textContent = "Loading the weekly SMC list…"; t.innerHTML = "";
    if (!smcLoading){ smcLoading = true;
      fetch("smc.json", {cache:"no-cache"}).then(r=>r.ok?r.json():Promise.reject()).then(j=>{ SMC = j; if (view==="smc") draw(); })
        .catch(()=>{ hint.textContent = "The weekly SMC list appears after the next full update."; }); }
    return;
  }
  const tg = $("smc_tg").value, rsMin = $("smc_rs").value, L = (SMC.logs||{})[tg] || [];
  const ok = (a, r) => !r || (a[10] != null && a[10] >= +r);
  const sel = L.filter(a=>ok(a, rsMin));
  const sg = v => v==null ? "–" : (v>0?"+":"")+fmt(v,1)+"%";
  const cmpRows = [["2R, any RS","2",""],["3R, any RS","3",""],["2R, RS 70+","2","70"],["3R, RS 70+","3","70"],["2R, RS 80+","2","80"],["3R, RS 80+","3","80"]];
  hint.innerHTML = statBox({...estats(sel), from: SMC.since}, `Weekly SMC, ${tg}R target${rsMin?`, RS ${rsMin}+`:""}`) +
    `<details style="margin:0 0 10px"><summary style="cursor:pointer"><b>Compare targets and RS filters</b> (last 2 years)</summary><div class="tbl" style="margin:8px 0 0"><table style="font-size:.85rem"><thead><tr><th class="l">Version</th><th>Trades</th><th>Won</th><th>Avg win</th><th>Avg loss</th><th>Per closed trade</th><th>Incl. open</th></tr></thead><tbody>${
      cmpRows.map(([n, g, r])=>{ const X = estats(((SMC.logs||{})[g]||[]).filter(a=>ok(a, r))); return `<tr><td class="l">${n}</td><td>${X.n}</td><td>${X.win!=null?X.win+"%":"–"}</td><td class="ok">${sg(X.avg_win)}</td><td class="bad">${sg(X.avg_loss)}</td><td><b>${sg(X.avg)}</b></td><td>${sg(X.avg_all)}</td></tr>`; }).join("")}</tbody></table></div></details>` +
    `Weekly charts. <b>Setup</b>: in a downtrend (falling swing highs and lows), a weekly close above the last swing high is a change of character. The <b>order block</b> is the last red week at the start of that move. <b>Entry</b>: within 8 weeks, buy the first pullback into the order block while price is in the lower half of the move, at the top of the block. <b>Stop</b>: just below the block. <b>Target</b>: ${tg}× the risk. Weekly stops are wide (often 7–10%), so size positions from the stop. In testing: about +2.3% per trade overall, and +8% with RS 80+ but on few trades, so treat that as unproven.`;
  const S = (SMC.setups||[]).filter(x=>!rsMin || (x.rs!=null && x.rs >= +rsMin));
  const span = $("smc_span").value, cut = span ? new Date(Date.now() - (+span)*864e5).toISOString().slice(0,10) : "";
  let rows = sel.filter(a=>a[1] >= cut).map(a=>({sym:a[0], name:(SMC.names[a[0]]||[])[0], sector:(SMC.names[a[0]]||[])[1], a, ed:a[1], g:a[5], mx:a[6], rs:a[10], open:!a[3]}));
  rows = srt(rows); const total = rows.length; rows = rows.slice(0, smcN);
  const more = $("more");
  more.innerHTML = total > smcN ? `<button type="button" class="sel" style="cursor:pointer" id="smc_more">Show ${Math.min(300,total-smcN)} more (${total-smcN} hidden)</button>` : "";
  if ($("smc_more")) $("smc_more").onclick = () => { smcN += 300; draw(); };
  t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Change of character</th><th>Order block (buy zone)</th><th>Price now</th><th>Stop</th><th>Target</th><th>Risk</th><th>RS</th><th class="l">Status</th></tr></thead>
    <tbody><tr><td colspan="9" class="l"><b>Setups waiting for a pullback</b> <span class="mut">(${S.length}; place a buy at the top of the zone with the stop below it)</span></td></tr>
    ${S.slice(0,80).map(x=>`<tr>${nm(x)}<td>${dl(x.choch)} <small class="mut">(${x.weeks} wk ago)</small></td><td>₹${fmt(x.zl)} – <b>₹${fmt(x.zh)}</b></td><td>₹${fmt(x.price)}<small class="mut" style="display:block">${x.dist>0?fmt(x.dist,1)+"% above the zone":"in the zone"}</small></td>
      <td>₹${fmt(x.stop)}</td><td>₹${fmt(tg==="3"?x.t3:x.t2)}</td><td>${fmt(x.risk,1)}%</td><td><b>${x.rs??"–"}</b></td>
      <td class="l">${x.in_zone?(x.discount?'<span class="new">buy zone now</span>':'<span class="flag">in zone, not yet in discount</span>'):'<span class="mut">waiting</span>'}</td></tr>`).join("") || '<tr><td colspan="9" class="mut">No setups waiting right now.</td></tr>'}</tbody>
    <thead><tr><th class="l">Stock</th><th>Entry week</th><th>Entry</th><th>Now / exit</th><th>Gain</th><th>Stop</th><th>Target</th><th>Risk</th><th>RS</th></tr></thead>
    <tbody><tr><td colspan="9" class="l"><b>${total} trade${total===1?"":"s"}</b> <span class="mut">${span?"in the last 3 months":"in the last 2 years"}${total>smcN?`, showing ${smcN}`:""}</span></td></tr>
    ${rows.map(r=>{ const a = r.a; return `<tr>${nm(r)}<td>${dl(a[1])}<small class="mut" style="display:block">CHoCH ${dl(a[13])}</small></td><td>₹${fmt(a[2])}</td>
      <td>₹${fmt(a[4])}${a[3]?`<small class="${a[5]>0?'ok':'bad'}" style="display:block">${dl(a[3])} · ${esc(a[7]||"")}</small>`:'<small class="mut" style="display:block">open</small>'}</td>
      <td>${pc(a[5])}<small class="mut" style="display:block">max ${a[6]>0?"+":""}${fmt(a[6],1)}%</small></td><td>₹${fmt(a[11])}</td><td>₹${fmt(a[12])}</td><td>${fmt(a[9],1)}%</td><td><b>${a[10]??"–"}</b></td></tr>`; }).join("") || '<tr><td colspan="9" class="mut">No trades with these settings in this period.</td></tr>'}</tbody>`;
}
// ---------- all past trades (loaded only when the tab is opened) ----------
let LOG = null, logN = 300;
const lg = id => document.getElementById(id);
function logRows(){
  if (!LOG) return [];
  const set = lg("lg_set").value, st = lg("lg_st").value, y = lg("lg_y").value, q = lg("lg_q").value.trim().toUpperCase();
  const src = LOG[set==="t3s" ? "t3" : set] || [];
  const rows = [];
  for (const a of src){
    const r = {sym:a[0], name:LOG.names[a[0]]||"", ed:a[1], ep:a[2], xd:a[3], xp:a[4], g:a[5], mx:a[6], why:a[7], days:a[8], strong:set.startsWith("t3") && !!a[9], br:set.startsWith("by") ? a[9] : null};
    if (set==="t3s" && !r.strong) continue;
    if (st==="open" && r.xd) continue;
    if (st==="closed" && !r.xd) continue;
    if (st==="win" && !(r.xd && r.g > 0)) continue;
    if (st==="loss" && !(r.xd && r.g <= 0)) continue;
    if (y && !r.ed.startsWith(y)) continue;
    if (q && !r.sym.includes(q) && !r.name.toUpperCase().includes(q)) continue;
    rows.push(r);
  }
  return rows;
}
function drawLog(t, hint){
  const more = lg("more");
  if (!LOG){
    hint.textContent = "Loading every trade of the last 2 years…"; t.innerHTML = ""; more.innerHTML = "";
    fetch("trade_log.json", {cache:"no-cache"}).then(r=>r.ok?r.json():Promise.reject()).then(j=>{ LOG = j;
      const ys = new Set(); ["by","tt8","tt7","tte","t3"].forEach(k=>(j[k]||[]).forEach(a=>ys.add(a[1].slice(0,4))));
      lg("lg_y").innerHTML = '<option value="">All</option>' + [...ys].sort().reverse().map(y=>`<option>${y}</option>`).join("");
      if (view==="log") draw(); }).catch(()=>{ hint.textContent = "The trade list is not available yet. It appears after the next update."; });
    return;
  }
  const rows = srt(logRows()), weekly = lg("lg_set").value.startsWith("t3") || lg("lg_set").value.startsWith("by");
  const cl = rows.filter(r=>r.xd), w = cl.filter(r=>r.g>0), avg = a => a.length ? a.reduce((s,r)=>s+r.g,0)/a.length : null;
  const sg = v => v==null ? "–" : (v>0?"+":"")+fmt(v,1)+"%";
  hint.innerHTML = `<div class="kpi" style="margin:0 0 10px"><div><b>${rows.length.toLocaleString("en-IN")}</b><small>trades shown (${rows.length-cl.length} still open)</small></div>
    <div><b>${cl.length?fmt(w.length/cl.length*100,0)+"%":"–"}</b><small>of ${cl.length.toLocaleString("en-IN")} closed made money</small></div>
    <div><b class="ok">${sg(avg(w))}</b><small>average winner</small></div><div><b class="bad">${sg(avg(cl.filter(r=>r.g<=0)))}</b><small>average loser</small></div>
    <div><b class="${(avg(cl)||0)>=0?'ok':'bad'}">${sg(avg(cl))}</b><small>average per closed trade · ${sg(avg(rows))} incl. open</small></div></div>
    Every entry and exit the rule made in the last 2 years, with the same entry and exit rules as the tabs. Open trades show today's price. ${weekly ? "Held is in weeks." : "Held is in trading days."} Costs are not included.`;
  const shown = rows.slice(0, logN);
  t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Entry date</th><th>Entry</th><th>Exit date</th><th>Exit / now</th><th>Gain</th><th>Max gain</th><th>Held</th><th class="l">Exit reason</th></tr></thead><tbody>${shown.map(r=>`<tr>
    ${nm(r)}<td>${dl(r.ed)}${r.strong?'<span class="new">strong</span>':""}${r.br!=null?`<small class="mut" style="display:block">breadth ${r.br}%</small>`:""}</td><td>₹${fmt(r.ep)}</td><td>${r.xd?dl(r.xd):'<span class="new">open</span>'}</td>
    <td>₹${fmt(r.xp)}${r.xd?"":'<small class="mut" style="display:block">now</small>'}</td><td>${pc(r.g)}</td><td>${pc(r.mx)}</td><td>${r.days}${weekly?" wk":" d"}</td><td class="l">${esc(r.why||(r.xd?"":"–"))}</td></tr>`).join("") || '<tr><td colspan="9" class="mut">No trades match.</td></tr>'}</tbody>`;
  more.innerHTML = rows.length > logN ? `<button type="button" class="sel" style="cursor:pointer" id="lg_more">Show ${Math.min(500, rows.length-logN)} more (${rows.length-logN} hidden)</button>` : "";
  if (lg("lg_more")) lg("lg_more").onclick = () => { logN += 500; draw(); };
}
["lg_set","lg_st","lg_y"].forEach(id=>lg(id).onchange = () => { logN = 300; draw(); });
lg("lg_q").oninput = () => { logN = 300; draw(); };
lg("lg_csv").onclick = () => {
  const rows = srt(logRows()), q = v => `"${String(v??"").replace(/"/g,'""')}"`;
  const csv = ["Symbol,Name,Entry date,Entry,Exit date,Exit or price now,Gain %,Max gain %,Held,Exit reason,Strong,Breadth at signal %"].concat(rows.map(r=>[r.sym,r.name,r.ed,r.ep,r.xd||"open",r.xp,r.g,r.mx,r.days,r.why||"",r.strong?"yes":"",r.br??""].map(q).join(","))).join("\n");
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([csv], {type:"text/csv"})); a.download = `trades_${lg("lg_set").value}.csv`; document.body.appendChild(a); a.click(); a.remove();
};
function draw(){
  document.querySelectorAll(".tabs button").forEach(b=>b.setAttribute("aria-selected", b.dataset.v===view));
  const t = document.getElementById("t"), hint = document.getElementById("hint");
  lg("logbar").style.display = view === "log" ? "" : "none"; lg("more").innerHTML = "";
  lg("ttebar").style.display = view === "tte" ? "" : "none";
  lg("apbar").style.display = view === "ap" ? "" : "none";
  lg("smcbar").style.display = view === "smc" ? "" : "none";
  lg("cprbar").style.display = view === "cpr" ? "" : "none";
  hint.style.maxWidth = (view === "ap" || view === "tte" || view === "smc" || view === "cpr") ? "none" : "";
  document.querySelectorAll("#clean,#qab,#risk").forEach(e=>e.closest("label").style.display = view==="log" || view==="cpr" || ((view==="tte" || view==="ap" || view==="smc") && e.id!=="risk") ? "none" : "");
  if (view==="log"){ drawLog(t, hint); return; }
  if (view==="ap"){ drawAP(t, hint); return; }
  if (view==="smc"){ drawSMC(t, hint); return; }
  if (view==="cpr"){ drawCPR(t, hint); return; }
  if (view==="open"){
    const rows = srt(curOpen().filter(keep));
    hint.innerHTML = `Market filter: <b>${VLAB[bv]}</b>. ${rows.filter(r=>r.ago<=1).length} new signal(s) in the last two weeks, ${rows.length} open trade(s) in all. Enter at about the signal price; the quantity uses your risk per trade and the stop-loss.`;
    t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Signal week</th><th>Entry</th><th>Stop-loss</th><th>Risk</th><th>Trailing stop now</th><th>Price</th><th>Gain</th><th>Room to trail</th><th>Qty</th><th class="l">Notes</th></tr></thead><tbody>${rows.map(r=>`<tr>
      ${nm(r)}<td>${dl(r.sd)}${r.forming?'<span class="new form">forming</span>':r.ago===0?'<span class="new">new</span>':r.ago===1?'<span class="new">last week</span>':""}</td>
      <td>₹${fmt(r.entry)}</td><td>₹${fmt(r.sl)}</td><td>${fmt(r.risk,1)}%</td>
      <td><b>₹${fmt(r.trail)}</b><small class="mut" style="display:block">${esc(r.trail_kind)}</small></td>
      <td>₹${fmt(r.price)}</td><td>${pc(r.gain)}<small class="mut" style="display:block">best ${pc(r.best)}</small></td>
      <td>${pc(r.room)}</td><td>${qty(r.price, r.trail)}</td><td class="l">RS ${r.rs??"–"} · week +${fmt(r.wkg,1)}%${r.br!=null?` · breadth ${r.br}%`:""} · grade ${esc(r.grade||"–")} ${flags(r.flags)}</td></tr>`).join("") || '<tr><td colspan="11" class="mut">No open signals right now.</td></tr>'}</tbody>`;
  } else if (view==="watch"){
    const openSyms = new Set(curOpen().map(r=>r.sym));
    const rows = srt(D.watch.filter(r=>keep(r) && !openSyms.has(r.sym)));
    hint.innerHTML = "Leaders near their highs, within 5% of the 12-week breakout level. A weekly close above both trigger levels makes it a signal.";
    t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Price</th><th>Breakout level</th><th>Distance</th><th>Weekly close needed (with +8%)</th><th>RS</th><th>From 52-wk high</th><th class="l">Notes</th></tr></thead><tbody>${rows.map(r=>`<tr>
      ${nm(r)}<td>₹${fmt(r.price)}</td><td>₹${fmt(r.trig)}</td><td>${fmt(r.dist,1)}%</td><td><b>₹${fmt(r.need8)}</b></td><td>${r.rs??"–"}</td><td>${pc(r.hi52)}</td><td class="l">${flags(r.flags)}</td></tr>`).join("") || '<tr><td colspan="8" class="mut">Nothing close to triggering.</td></tr>'}</tbody>`;
  } else if (view==="tte"){
    const T = D.tt || {}, b = T.breadth;
    const allMode = $id("tte_span").value === "all";
    const curM = {}; (T.early||[]).forEach(r=>{ if (r.tr) curM[r.sym+"|"+r.tr.ed] = r; });
    const src = allMode ? (T.elog||[]).map(a=>{ const c = curM[a[0]+"|"+a[1]], nmS = (T.enames||{})[a[0]]||[];
        return c || {sym:a[0], name:nmS[0], sector:nmS[1], price:a[4], rs:null, k:"–", exit:null,
                     tr:{ed:a[1], ep:a[2], xd:a[3], xp:a[3]?a[4]:null, g:a[5], mx:a[6], why:a[7], open:!a[3], sl:a[2]*0.88, fl:a.slice(9)}}; }) : (T.early||[]);
    let rows = srt(src.filter(r=>passE(r.tr && r.tr.fl)));
    const nd = rows.filter(r=>r.tr&&r.tr.open&&r.tr.div).length, total = rows.length;
    rows = rows.slice(0, apN);
    const moreEl = $id("more");
    moreEl.innerHTML = total > apN ? `<button type="button" class="sel" style="cursor:pointer" id="tte_more">Show ${Math.min(300, total-apN)} more (${total-apN} hidden)</button>` : "";
    if ($id("tte_more")) $id("tte_more").onclick = () => { apN += 300; draw(); };
    const L = (T.elog||[]), on = ECK.filter(k=>eck[k]).map(k=>ELAB[k]);
    const cur = estats(L.filter(a=>passE(a.slice(9))));
    const known = (i, f) => L.filter(a=>a[9+i]!=null).length;
    const vk = known(0), rk = known(2), sk = known(3);
    hint.innerHTML = statBox(cur, "Stage 2 start" + (on.length ? " with " + on.join(", ") : "")) +
      `<details style="margin:0 0 10px"><summary style="cursor:pointer"><b>Compare the checks</b> (same 2 years of trades)</summary><div class="tbl" style="margin:8px 0 0"><table><thead><tr><th class="l">Rule</th><th>Trades</th><th>Won</th><th>Avg winner</th><th>Avg loser</th><th>Avg per closed trade</th><th>Incl. open</th><th>Reached +30%</th></tr></thead><tbody>${
        [["Rule only", {}], ["+ breakout volume", {vol:1}], ["+ volume dry-up", {dry:1}], ["+ both volume checks", {vol:1, dry:1}], ["+ no results within 5 days", {res:1}], ["+ skip surveillance", {asm:1}], ["All four checks", {vol:1, dry:1, res:1, asm:1}]]
        .map(([n, c])=>{ const S = estats(L.filter(a=>passE(a.slice(9), c))); const sg = v => v==null ? "–" : (v>0?"+":"")+fmt(v,1)+"%";
          return `<tr><td class="l">${n}</td><td>${S.n}</td><td>${S.win!=null?S.win+"%":"–"}</td><td class="ok">${sg(S.avg_win)}</td><td class="bad">${sg(S.avg_loss)}</td><td><b>${sg(S.avg)}</b></td><td>${sg(S.avg_all)}</td><td>${S.big!=null?S.big+"%":"–"}</td></tr>`; }).join("")}</tbody></table></div>
        <p class="sub" style="margin:6px 0 0">Volume known for ${vk} of ${L.length} trades. Results dates and surveillance lists are only kept from ${dl(T.hist_since)} onwards (NSE gives upcoming dates only), so those two checks cover ${rk} and ${sk} trades so far and fill in as the dashboard runs. Trades where a check can't be measured are kept.</p></details>` +
      `Catches the turn <b>before</b> the Trend Template does (ASTRAMICRO broke out of its base on 21 Apr 2026 at ₹1,110 but reached 8/8 only on 26 Jun at ₹1,719). <b>Entry</b> = close above the highest close of the last 26 weeks, within 10% of the 52-week high, above the 50 and 200-day MAs, 50-day MA rising, RS 80+, not more than 25% above the 50-day MA, Choppiness (14 days) below 38, and only when more than half of all stocks are above their 50-day MA. <b>Exit</b>: the first daily close below the 50-day MA, with an emergency stop 12% below entry for gap-downs (tested on real prices: average per closed trade +4.1% vs +3.3% with an 8% stop and a weekly exit). Signals from the last 3 months.${nd ? ` <b>${nd} open trade${nd>1?"s show":" shows"} a bearish RSI divergence in the last 10 sessions</b> (⚠ in Notes): price made a higher high but RSI a lower one, an early sign the move is tiring. Tested as an exit it won 79% of trades and halved the worst fall, but earned less because it sells big winners early, so it is a warning for you to judge (hold, sell half or tighten the stop), not part of the rule.` : ""}${T.live ? " During market hours today's volume is still partial, so the volume check is final only at the close." : ""}` +
      `<div style="margin:8px 0 0"><b>Market breadth now: ${b??"–"}% of stocks above their 50-day MA</b> ${b!=null && b>50 ? '<span class="ok">new entries allowed</span>' : '<span class="bad">below 50%: no new entries until the market improves</span>'}</div>`;
    const yn = (v, good) => v==null ? '<span class="mut">–</span>' : good ? `<span class="ok">${v}</span>` : `<span class="bad">${v}</span>`;
    t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Entry</th><th>Now / exit</th><th>Gain</th><th>RS at entry</th><th>Breakout volume</th><th>Dry-up before</th><th>Chop at entry</th><th>Template now</th><th>Emergency stop (−12%)</th><th>Exit on a daily close below (50-day MA)</th><th>Qty</th><th class="l">Notes</th></tr></thead><tbody><tr><td colspan="13" class="l"><b>${total} trade${total===1?"":"s"}</b> <span class="mut">${allMode ? "in the last 2 years (every entry and exit)" : "with signals in the last 3 months (each stock's latest trade)"}${total>apN?`, showing ${apN}`:""}.</span></td></tr>${rows.map(r=>{ const f = (r.tr&&r.tr.fl)||[], rs_ = (T.res_soon||{})[r.sym]; return `<tr>
      ${nm(r)}${trCells(r)}<td><b>${f[5]??"–"}</b>${r.new?'<span class="new">new</span>':""}<small class="mut" style="display:block">now ${r.rs??"–"}</small></td>
      <td>${yn(f[0]!=null?fmt(f[0],1)+"×":null, f[0]>=1.5)}</td><td>${yn(f[1]!=null?Math.round(f[1]*100)+"%":null, f[1]<0.7)}</td><td>${f[4]??"–"}</td><td>${r.k}/8</td>
      <td>${r.tr&&r.tr.open?"₹"+fmt(r.tr.sl):"–"}</td><td>${r.tr&&r.tr.open&&r.exit!=null?"₹"+fmt(r.exit):"–"}</td><td>${r.tr&&r.tr.open?qty(r.price, Math.max(r.tr.sl, r.exit!=null&&r.exit<r.price?r.exit:0)):"–"}</td>
      <td class="l" style="white-space:normal;font-size:.8rem">${r.tr&&r.tr.div?`<span class="flag" style="background:#fdecc8;color:#8a5a00" title="Price made a higher high (₹${fmt(r.tr.div.p2)} vs ₹${fmt(r.tr.div.p1)}) but RSI made a lower high (${r.tr.div.r2} vs ${r.tr.div.r1}). Consider selling, selling half or tightening the stop.">⚠ Bearish RSI divergence ${dl(r.tr.div.d)}: price ₹${fmt(r.tr.div.p2)} &gt; ₹${fmt(r.tr.div.p1)}, RSI ${r.tr.div.r2} &lt; ${r.tr.div.r1}</span>`:""}${f[2]?'<span class="flag">results within 5 days of entry</span>':""}${f[3]?'<span class="flag">under surveillance at entry</span>':""}${rs_&&r.tr&&r.tr.open?`<span class="flag">results on ${dl(rs_)}</span>`:""}</td></tr>`; }).join("") || '<tr><td colspan="13" class="mut">No Stage 2 start signals in the last 3 months that pass the checks you picked.</td></tr>'}</tbody>`;
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
    t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Signal week</th><th>Entry</th><th>Exit week</th><th>Exit</th><th>Result</th></tr></thead><tbody>${srt(curExits()).map(r=>`<tr>
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
