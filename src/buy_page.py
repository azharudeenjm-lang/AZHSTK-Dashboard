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
    <button role="tab" data-v="tte" aria-selected="false">Stage 2 start (early)</button>
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
    <label class="tog">Rule <select id="lg_set" class="sel"><option value="tt8">Trend Template 8/8</option><option value="tt7">Trend Template 7/8</option><option value="tte">Stage 2 start (early)</option><option value="t3">3-touch breakouts (all)</option><option value="t3s">3-touch breakouts (strong only)</option></select></label>
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
  tte: [["Default (open first, newest)", null, 1], ["Entry date", r=>r.tr&&r.tr.ed, -1], RS, ["Gain", r=>r.tr&&r.tr.g, -1], ["Max gain since entry", r=>r.tr&&r.tr.mx, -1],
        ["Exit date", r=>r.tr&&r.tr.xd, -1], ["Nearest 52-week high", r=>r.hi, -1], ["Template checks passed now", r=>r.k, -1], ["Room above the 50-day MA", r=>r.room, 1], ["Price", r=>r.price, -1], NAME],
  t3: [["Default (newest first)", null, 1], ["Breakout date", r=>r.bd, -1], RS, ["Gain", r=>r.xd ? r.xg : r.gain, -1], ["Max gain since breakout", r=>r.mx, -1],
       ["Breakout week gain", r=>r.wk, -1], ["Touches", r=>r.touches, -1], ["Trendline length (weeks)", r=>r.span, -1], ["Strong first", r=>r.strong?1:0, -1], NAME],
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
          sl_hit: cl.length ? Math.round(cl.filter(a=>a[7]==="Stop-loss").length/cl.length*100) : null, from:(D.tt&&D.tt.stats&&D.tt.stats.e||{}).from}; }
// ---------- all past trades (loaded only when the tab is opened) ----------
let LOG = null, logN = 300;
const lg = id => document.getElementById(id);
function logRows(){
  if (!LOG) return [];
  const set = lg("lg_set").value, st = lg("lg_st").value, y = lg("lg_y").value, q = lg("lg_q").value.trim().toUpperCase();
  const src = LOG[set==="t3s" ? "t3" : set] || [];
  const rows = [];
  for (const a of src){
    const r = {sym:a[0], name:LOG.names[a[0]]||"", ed:a[1], ep:a[2], xd:a[3], xp:a[4], g:a[5], mx:a[6], why:a[7], days:a[8], strong:!!a[9]};
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
      const ys = new Set(); ["tt8","tt7","tte","t3"].forEach(k=>(j[k]||[]).forEach(a=>ys.add(a[1].slice(0,4))));
      lg("lg_y").innerHTML = '<option value="">All</option>' + [...ys].sort().reverse().map(y=>`<option>${y}</option>`).join("");
      if (view==="log") draw(); }).catch(()=>{ hint.textContent = "The trade list is not available yet. It appears after the next update."; });
    return;
  }
  const rows = srt(logRows()), weekly = lg("lg_set").value.startsWith("t3");
  const cl = rows.filter(r=>r.xd), w = cl.filter(r=>r.g>0), avg = a => a.length ? a.reduce((s,r)=>s+r.g,0)/a.length : null;
  const sg = v => v==null ? "–" : (v>0?"+":"")+fmt(v,1)+"%";
  hint.innerHTML = `<div class="kpi" style="margin:0 0 10px"><div><b>${rows.length.toLocaleString("en-IN")}</b><small>trades shown (${rows.length-cl.length} still open)</small></div>
    <div><b>${cl.length?fmt(w.length/cl.length*100,0)+"%":"–"}</b><small>of ${cl.length.toLocaleString("en-IN")} closed made money</small></div>
    <div><b class="ok">${sg(avg(w))}</b><small>average winner</small></div><div><b class="bad">${sg(avg(cl.filter(r=>r.g<=0)))}</b><small>average loser</small></div>
    <div><b class="${(avg(cl)||0)>=0?'ok':'bad'}">${sg(avg(cl))}</b><small>average per closed trade · ${sg(avg(rows))} incl. open</small></div></div>
    Every entry and exit the rule made in the last 2 years, with the same entry and exit rules as the tabs. Open trades show today's price. ${weekly ? "Held is in weeks." : "Held is in trading days."} Costs are not included.`;
  const shown = rows.slice(0, logN);
  t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Entry date</th><th>Entry</th><th>Exit date</th><th>Exit / now</th><th>Gain</th><th>Max gain</th><th>Held</th><th class="l">Exit reason</th></tr></thead><tbody>${shown.map(r=>`<tr>
    ${nm(r)}<td>${dl(r.ed)}${r.strong?'<span class="new">strong</span>':""}</td><td>₹${fmt(r.ep)}</td><td>${r.xd?dl(r.xd):'<span class="new">open</span>'}</td>
    <td>₹${fmt(r.xp)}${r.xd?"":'<small class="mut" style="display:block">now</small>'}</td><td>${pc(r.g)}</td><td>${pc(r.mx)}</td><td>${r.days}${weekly?" wk":" d"}</td><td class="l">${esc(r.why||(r.xd?"":"–"))}</td></tr>`).join("") || '<tr><td colspan="9" class="mut">No trades match.</td></tr>'}</tbody>`;
  more.innerHTML = rows.length > logN ? `<button type="button" class="sel" style="cursor:pointer" id="lg_more">Show ${Math.min(500, rows.length-logN)} more (${rows.length-logN} hidden)</button>` : "";
  if (lg("lg_more")) lg("lg_more").onclick = () => { logN += 500; draw(); };
}
["lg_set","lg_st","lg_y"].forEach(id=>lg(id).onchange = () => { logN = 300; draw(); });
lg("lg_q").oninput = () => { logN = 300; draw(); };
lg("lg_csv").onclick = () => {
  const rows = srt(logRows()), q = v => `"${String(v??"").replace(/"/g,'""')}"`;
  const csv = ["Symbol,Name,Entry date,Entry,Exit date,Exit or price now,Gain %,Max gain %,Held,Exit reason,Strong"].concat(rows.map(r=>[r.sym,r.name,r.ed,r.ep,r.xd||"open",r.xp,r.g,r.mx,r.days,r.why||"",r.strong?"yes":""].map(q).join(","))).join("\n");
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([csv], {type:"text/csv"})); a.download = `trades_${lg("lg_set").value}.csv`; document.body.appendChild(a); a.click(); a.remove();
};
function draw(){
  document.querySelectorAll(".tabs button").forEach(b=>b.setAttribute("aria-selected", b.dataset.v===view));
  const t = document.getElementById("t"), hint = document.getElementById("hint");
  lg("logbar").style.display = view === "log" ? "" : "none"; lg("more").innerHTML = "";
  lg("ttebar").style.display = view === "tte" ? "" : "none";
  document.querySelectorAll("#clean,#qab,#risk").forEach(e=>e.closest("label").style.display = view==="log" || (view==="tte" && e.id!=="risk") ? "none" : "");
  if (view==="log"){ drawLog(t, hint); return; }
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
  } else if (view==="tte"){
    const T = D.tt || {}, b = T.breadth;
    const rows = srt((T.early||[]).filter(r=>passE(r.tr && r.tr.fl)));
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
      `Catches the turn <b>before</b> the Trend Template does (ASTRAMICRO broke out of its base on 21 Apr 2026 at ₹1,110 but reached 8/8 only on 26 Jun at ₹1,719). <b>Entry</b> = close above the highest close of the last 26 weeks, within 10% of the 52-week high, above the 50 and 200-day MAs, 50-day MA rising, RS 80+, not more than 25% above the 50-day MA, Choppiness (14 days) below 38, and only when more than half of all stocks are above their 50-day MA. <b>Exit</b>: the first daily close below the 50-day MA, with an emergency stop 12% below entry for gap-downs (tested on real prices: average per closed trade +4.1% vs +3.3% with an 8% stop and a weekly exit). Signals from the last 3 months.${T.live ? " During market hours today's volume is still partial, so the volume check is final only at the close." : ""}` +
      `<div style="margin:8px 0 0"><b>Market breadth now: ${b??"–"}% of stocks above their 50-day MA</b> ${b!=null && b>50 ? '<span class="ok">new entries allowed</span>' : '<span class="bad">below 50%: no new entries until the market improves</span>'}</div>`;
    const yn = (v, good) => v==null ? '<span class="mut">–</span>' : good ? `<span class="ok">${v}</span>` : `<span class="bad">${v}</span>`;
    t.innerHTML = `<thead><tr><th class="l">Stock</th><th>Entry</th><th>Now / exit</th><th>Gain</th><th>RS</th><th>Breakout volume</th><th>Dry-up before</th><th>Chop at entry</th><th>Template now</th><th>Emergency stop (−12%)</th><th>Exit on a daily close below (50-day MA)</th><th>Qty</th><th class="l">Notes</th></tr></thead><tbody>${rows.map(r=>{ const f = (r.tr&&r.tr.fl)||[], rs_ = (T.res_soon||{})[r.sym]; return `<tr>
      ${nm(r)}${trCells(r)}<td><b>${r.rs??"–"}</b>${r.new?'<span class="new">new</span>':""}</td>
      <td>${yn(f[0]!=null?fmt(f[0],1)+"×":null, f[0]>=1.5)}</td><td>${yn(f[1]!=null?Math.round(f[1]*100)+"%":null, f[1]<0.7)}</td><td>${f[4]??"–"}</td><td>${r.k}/8</td>
      <td>${r.tr&&r.tr.open?"₹"+fmt(r.tr.sl):"–"}</td><td>${r.tr&&r.tr.open?"₹"+fmt(r.exit):"–"}</td><td>${r.tr&&r.tr.open?qty(r.price, Math.max(r.tr.sl, r.exit<r.price?r.exit:0)):"–"}</td>
      <td class="l" style="white-space:normal;font-size:.8rem">${f[2]?'<span class="flag">results within 5 days of entry</span>':""}${f[3]?'<span class="flag">under surveillance at entry</span>':""}${rs_&&r.tr&&r.tr.open?`<span class="flag">results on ${dl(rs_)}</span>`:""}</td></tr>`; }).join("") || '<tr><td colspan="13" class="mut">No Stage 2 start signals in the last 3 months that pass the checks you picked.</td></tr>'}</tbody>`;
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
