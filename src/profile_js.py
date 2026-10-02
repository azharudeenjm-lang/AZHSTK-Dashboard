"""Shared search box + stock pop-up, written to docs/profile.js.

Every page includes <div id="gsearch"></div> and <script src="profile.js">.
Any element with data-p="SYMBOL" opens that stock's profile when clicked.
"""

PROFILE_JS = r"""(function(){
const CSS = `
:root{--pz-bear:#C2453B;--pz-os:#6B4BB8;--pz-acc:#2F62C8;--pz-bull:#1E8F5A;--pz-ob:#C9780F;--pz-dang:#A8285E;--pz-neu:#A3AFBF;--pz-na:#E1E6ED;
  --pq-lead:#1E8F5A;--pq-weak:#B9821A;--pq-lag:#C2453B;--pq-impr:#2F62C8;--p-link:#2F62C8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--pz-bear:#E9675C;--pz-os:#9C82E6;--pz-acc:#6E97F0;--pz-bull:#3FBF85;--pz-ob:#E5A040;--pz-dang:#E0619A;--pz-neu:#5E6B7C;--pz-na:#263140;
  --pq-lead:#3FBF85;--pq-weak:#E0AE45;--pq-lag:#E9675C;--pq-impr:#6E97F0;--p-link:#6E97F0}}
.gsearch{position:relative;flex:1 1 260px;max-width:420px}
.gsearch input{width:100%;font:inherit;font-size:.92rem;color:var(--ink);background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:9px 12px}
.gsearch input:focus-visible{outline:2px solid var(--p-link);outline-offset:1px}
.gs-list{position:absolute;z-index:50;left:0;right:0;top:calc(100% + 4px);background:var(--panel);border:1px solid var(--line);border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.15);max-height:60vh;overflow:auto;padding:4px;margin:0;list-style:none}
.gs-list li{display:flex;gap:8px;align-items:center;justify-content:space-between;padding:8px 10px;border-radius:8px;cursor:pointer}
.gs-list li[aria-selected="true"],.gs-list li:hover{background:color-mix(in srgb,var(--p-link) 12%,var(--panel))}
.gs-list .nm{min-width:0}.gs-list .nm b{display:block}.gs-list .nm small{display:block;color:var(--muted);font-size:.75rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:240px}
.gs-list .zz{display:flex;gap:4px;flex-shrink:0}
.pchip{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.72rem;font-weight:600;color:#fff;background:var(--c);white-space:nowrap}
.pchip.o{background:transparent;color:var(--c);border:1px solid var(--c)}
button.psym{all:unset;font-weight:700;cursor:pointer;color:inherit;border-bottom:1px dotted currentColor}
button.psym:hover{color:var(--p-link)}button.psym:focus-visible{outline:2px solid var(--p-link);outline-offset:2px}
dialog.prof{border:0;padding:0;background:var(--panel);color:var(--ink);width:min(980px,100vw);max-width:100vw;max-height:100dvh;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,.3)}
@media(max-width:700px){dialog.prof{width:100vw;height:100dvh;max-height:100dvh;border-radius:0;margin:0}}
dialog.prof::backdrop{background:rgba(10,16,26,.55)}
.pf{padding:16px 16px calc(24px + env(safe-area-inset-bottom,0px));overflow:auto;max-height:100dvh;font-variant-numeric:tabular-nums}
.pf-h{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;position:sticky;top:-16px;background:var(--panel);padding:16px 0 10px;margin-top:-16px;z-index:2;border-bottom:1px solid var(--line)}
.pf-h h2{margin:0;font-size:1.4rem}.pf-h p{margin:2px 0 0;color:var(--muted);font-size:.85rem}
.pf-x{font:600 1.4rem/1 var(--font,system-ui);background:transparent;border:1px solid var(--line);color:var(--ink);border-radius:10px;width:40px;height:40px;cursor:pointer;flex-shrink:0}
.pf-px{font-size:1.25rem;font-weight:700;margin-top:6px}.pf-px span{font-size:.9rem;font-weight:600}
.pf-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;margin:14px 0 10px}
.pf-seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}
.pf-seg button{border:0;background:transparent;color:var(--muted);font:500 .88rem var(--font,system-ui);padding:6px 16px;cursor:pointer}
.pf-seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
.pf-lk a{font-size:.8rem;font-weight:600;color:var(--p-link);text-decoration:none;border:1px solid currentColor;border-radius:7px;padding:3px 9px;margin-left:6px}
.pf-cards{display:grid;gap:10px;grid-template-columns:repeat(2,minmax(0,1fr))}
@media(min-width:760px){.pf-cards{grid-template-columns:repeat(4,minmax(0,1fr))}}
.pf-card{border:1px solid var(--line);border-radius:12px;padding:10px 12px;min-width:0}
.pf-card h3{margin:0 0 6px;font-size:.75rem;font-weight:600;color:var(--muted);text-transform:none}
.pf-card .big{font-size:1.35rem;font-weight:700;line-height:1.2}
.pf-card small{display:block;color:var(--muted);font-size:.78rem;margin-top:3px}
.pf-sec{margin-top:18px}.pf-sec>h3{font-size:1rem;margin:0 0 8px}
.pf-chart{width:100%;height:auto;display:block}
.pf-key{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:.75rem;color:var(--muted);margin-top:6px}
.pf-key i{display:inline-block;width:10px;height:10px;border-radius:2px;background:var(--c);margin-right:4px;vertical-align:-1px}
.tl{list-style:none;margin:0;padding:0}
.tl li{display:grid;grid-template-columns:14px 1fr auto;gap:10px;padding:10px 0;border-bottom:1px solid var(--line);align-items:start}
.tl li:last-child{border-bottom:0}
.tl .rail{width:6px;border-radius:3px;background:var(--c);align-self:stretch;margin-left:4px}
.tl .when{font-size:.85rem}.tl .when small{display:block;color:var(--muted);font-size:.76rem}
.tl .mv{text-align:right;font-size:.85rem;white-space:nowrap}.tl .mv b{font-size:1rem}.tl .mv small{display:block;color:var(--muted);font-size:.74rem}
.pf-up{color:var(--up,#1E8F5A)}.pf-down{color:var(--down,#C2453B)}.pf-mut{color:var(--muted)}
.pf-kv{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 16px;font-size:.86rem}
@media(min-width:760px){.pf-kv{grid-template-columns:repeat(4,minmax(0,1fr))}}
.pf-kv div{display:flex;justify-content:space-between;gap:8px;border-bottom:1px dashed var(--line);padding:4px 0}
.pf-kv span{color:var(--muted)}
.pf-load{padding:40px;text-align:center;color:var(--muted)}
`;
const st = document.createElement("style"); st.textContent = CSS; document.head.appendChild(st);

const ZC = {"Bearish":"--pz-bear","Oversold":"--pz-os","Accumulation":"--pz-acc","Bullish":"--pz-bull","Overbought":"--pz-ob","Danger zone":"--pz-dang","Neutral":"--pz-neu","No data":"--pz-na"};
const CODE = {R:"Bearish",O:"Oversold",A:"Accumulation",U:"Bullish",B:"Overbought",D:"Danger zone",N:"Neutral","-":"No data"};
const QC = {Leading:"--pq-lead",Weakening:"--pq-weak",Lagging:"--pq-lag",Improving:"--pq-impr"};
const LS = {"Breakout":"--pz-bull","Trendline breakout":"--pz-bull","Retest":"--pz-acc","At trendline support":"--pz-os","Near support":"--pz-neu","Breakdown":"--pz-bear","Trendline breakdown":"--pz-dang","Near resistance":"--pz-ob"};
const esc = s => String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = (v,d=1) => v==null ? "–" : Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const pct = (v,d=1) => { if (v==null) return '<span class="pf-mut">–</span>'; if (Math.abs(v) < 0.5*Math.pow(10,-d)) v = 0;
  return `<span class="${v>0?'pf-up':v<0?'pf-down':''}">${v>0?'+':''}${fmt(v,d)}%</span>`; };
const dl = s => s ? new Date(s+"T00:00:00").toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"2-digit"}) : "";
const zchip = (z,o) => z ? `<span class="pchip${o?' o':''}" style="--c:var(${ZC[z]||'--pz-neu'})">${esc(z)}</span>` : '<span class="pf-mut">–</span>';
const qchip = q => q ? `<span class="pchip" style="--c:var(${QC[q]})">${esc(q)}</span>` : '<span class="pf-mut">–</span>';
const cssv = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const tvurl = (s,iv) => "https://www.tradingview.com/chart/?symbol=" + encodeURIComponent("NSE:" + s.replace(/[&-]/g,"_")) + "&interval=" + iv;
const scrurl = s => "https://www.screener.in/company/" + encodeURIComponent(s) + "/";
const shard = s => s.toUpperCase().replace(/[^A-Z0-9]/g,"").slice(0,2) || "0";

let IDX = null, idxP = null; const SH = {};
function loadIndex(){ if (!idxP) idxP = fetch("search.json").then(r=>r.json()).then(j=>IDX=j).catch(()=>IDX={s:[],dates:{d:[],w:[]}}); return idxP; }
function loadStock(sym){ const k = shard(sym);
  if (!SH[k]) SH[k] = fetch(`p/${k}.json`).then(r=>r.json()).catch(()=>({}));
  return SH[k].then(m=>m[sym]); }

/* ---------- search box ---------- */
function mountSearch(){
  const host = document.getElementById("gsearch"); if (!host) return;
  host.classList.add("gsearch");
  host.innerHTML = `<input type="search" id="gs-in" placeholder="Search any stock, e.g. KRONOX" autocomplete="off" role="combobox" aria-expanded="false" aria-controls="gs-list" aria-label="Search any stock"><ul class="gs-list" id="gs-list" role="listbox" hidden></ul>`;
  const inp = host.querySelector("input"), ul = host.querySelector("ul");
  let hits = [], act = -1;
  const close = () => { ul.hidden = true; inp.setAttribute("aria-expanded","false"); act=-1; };
  const draw = () => {
    ul.innerHTML = hits.length ? `<li class="pf-mut" aria-disabled="true" style="cursor:default;font-size:.74rem;padding:4px 10px">Zone: daily (filled) · weekly (outline)</li>` + hits.map((s,i)=>`<li role="option" id="gs-o${i}" aria-selected="${i===act}" data-i="${i}">
      <span class="nm"><b>${esc(s[0])}</b><small>${esc(s[1])} · ${esc(s[2])}</small></span>
      <span class="zz" title="Daily / weekly zone">${zchip(s[3])}${s[4]?zchip(s[4],true):""}</span></li>`).join("")
      : `<li class="pf-mut" aria-disabled="true">No matching stock</li>`;
    ul.hidden = false; inp.setAttribute("aria-expanded","true");
    if (act>=0) inp.setAttribute("aria-activedescendant","gs-o"+act); else inp.removeAttribute("aria-activedescendant");
    ul.querySelectorAll("li[data-i]").forEach(li=>li.addEventListener("mousedown",e=>{ e.preventDefault(); pick(+li.dataset.i); }));
  };
  const pick = i => { const s = hits[i]; if (!s) return; inp.value = ""; close(); inp.blur(); openProfile(s[0]); };
  const find = () => { const q = inp.value.trim().toUpperCase(); if (!q || !IDX){ close(); return; }
    const a = [], b = [], c = [];
    for (const s of IDX.s){ if (s[0]===q) a.push(s); else if (s[0].startsWith(q)) b.push(s); else if (s[1].toUpperCase().includes(q)) c.push(s); if (a.length+b.length>40) break; }
    b.sort((x,y)=>y[5]-x[5] || x[0].length-y[0].length);
    hits = [...a,...b,...c].slice(0,12); act = hits.length ? 0 : -1; draw(); };
  inp.addEventListener("focus",()=>loadIndex());
  inp.addEventListener("input",()=>loadIndex().then(find));
  inp.addEventListener("keydown",e=>{
    if (e.key==="ArrowDown"){ e.preventDefault(); if(hits.length){ act=(act+1)%hits.length; draw(); } }
    else if (e.key==="ArrowUp"){ e.preventDefault(); if(hits.length){ act=(act-1+hits.length)%hits.length; draw(); } }
    else if (e.key==="Enter"){ e.preventDefault(); if (act>=0) pick(act); }
    else if (e.key==="Escape"){ close(); } });
  inp.addEventListener("blur",()=>setTimeout(close,150));
}

/* ---------- profile pop-up ---------- */
let dlg, curSym = null, curTF = "w", curData = null;
function ensureDialog(){
  if (dlg) return dlg;
  dlg = document.createElement("dialog"); dlg.className = "prof"; dlg.setAttribute("aria-labelledby","pf-title");
  document.body.appendChild(dlg);
  dlg.addEventListener("click",e=>{ if (e.target===dlg) dlg.close(); });
  dlg.addEventListener("close",()=>{ if (location.hash.startsWith("#stock=")) history.replaceState(null,"",location.pathname+location.search); });
  return dlg;
}
async function openProfile(sym){
  ensureDialog(); curSym = sym;
  dlg.innerHTML = `<div class="pf"><div class="pf-load">Loading ${esc(sym)}…</div></div>`;
  if (!dlg.open) dlg.showModal();
  history.replaceState(null,"","#stock="+encodeURIComponent(sym));
  const [idx, p] = await Promise.all([loadIndex(), loadStock(sym)]);
  if (curSym!==sym) return;
  if (!p){ dlg.innerHTML = `<div class="pf"><div class="pf-h"><h2 id="pf-title">${esc(sym)}</h2><button class="pf-x" aria-label="Close">×</button></div><p class="pf-load">No data for this stock yet.</p></div>`;
    dlg.querySelector(".pf-x").onclick=()=>dlg.close(); return; }
  curData = p; if (!p.z[curTF]) curTF = p.z.w ? "w" : "d";
  render();
}
window.openProfile = openProfile;

function render(){
  const p = curData, s = curSym, tf = curTF, z = p.z[tf] || {}, lv = p.lv[tf] || {};
  const U = tf==="d" ? ["session","sessions"] : ["week","weeks"], u = n => `${n} ${n===1?U[0]:U[1]}`;
  const dates = (IDX && IDX.dates && IDX.dates[tf]) || [];
  const segs = z.segs || [], cur = segs[segs.length-1];
  const sinceTxt = z.capped ? `since before ${dl(dates[0])}` : `since ${dl(z.since)}, ${u(z.days)}`;
  const sig = (lv.sig||[]);
  dlg.innerHTML = `<div class="pf">
  <div class="pf-h"><div><h2 id="pf-title">${esc(s)}</h2><p>${esc(p.n)} · ${esc(p.sec)}${p.ind && p.ind!==p.sec ? " · "+esc(p.ind) : ""}${p.liq?"":" · low liquidity"}</p>
    <div class="pf-px">₹${fmt(p.px,2)} <span>${pct(p.r1d,2)} today</span></div></div>
    <button class="pf-x" aria-label="Close">×</button></div>
  <div class="pf-bar"><div class="pf-seg" role="group" aria-label="Timeframe">
      <button data-t="d" aria-pressed="${tf==="d"}">Daily</button><button data-t="w" aria-pressed="${tf==="w"}">Weekly</button></div>
    <span class="pf-lk"><a href="${tvurl(s, tf==="w"?"W":"D")}" target="_blank" rel="noopener">TradingView</a><a href="${scrurl(s)}" target="_blank" rel="noopener">Screener</a></span></div>

  <div class="pf-cards">
    <div class="pf-card"><h3>Technical zone</h3><div>${zchip(z.zone)}</div><small>${sinceTxt}</small>${z.prev?`<small>came from ${esc(z.prev)}</small>`:""}</div>
    <div class="pf-card"><h3>Since entering the zone</h3><div class="big">${pct(z.move)}</div><small>entry ₹${fmt(z.entry,2)} → now ₹${fmt(p.px,2)}</small>${cur&&cur[6]!=null?`<small>best ${pct(cur[6])} · worst ${pct(cur[7])}</small>`:""}</div>
    <div class="pf-card"><h3>Sector rotation</h3><div>${qchip(p.sq&&p.sq[tf])}</div><small>${esc(p.sec)} vs NIFTY 50</small><div style="margin-top:6px">${qchip(p.rq&&p.rq[tf])}</div><small>this stock vs its sector</small></div>
    <div class="pf-card"><h3>Levels</h3><div>${sig.length ? sig.map(x=>`<span class="pchip" style="--c:var(${LS[x]})">${esc(x)}</span>`).join(" ") : '<span class="pf-mut">No signal</span>'}</div>
      <small>support ${lv.sup?`₹${fmt(lv.sup.p,2)} (−${fmt(lv.sup.d)}%)`:"–"}</small><small>resistance ${lv.res?`₹${fmt(lv.res.p,2)} (+${fmt(lv.res.d)}%)`:"–"}</small></div>
  </div>

  <div class="pf-sec"><h3>Price and zone history</h3>${chart(z, lv, dates, tf)}
    <div class="pf-key">${["Bullish","Overbought","Danger zone","Bearish","Oversold","Accumulation","Neutral"].map(k=>`<span><i style="--c:var(${ZC[k]})"></i>${k}</span>`).join("")}</div></div>

  <div class="pf-sec"><h3>Zone lifecycle</h3>
    <ul class="tl">${segs.slice().reverse().map((g,i)=>{ const name = CODE[g[0]], now = i===0;
      const mv = g[4] && g[5] ? (g[5]/g[4]-1)*100 : null;
      return `<li style="--c:var(${ZC[name]})"><span class="rail"></span>
        <div class="when">${zchip(name)} ${now?'<b> now</b>':''}<small>${g[8]?`before ${dl(g[1])}`:dl(g[1])} → ${now?"today":dl(g[2])} · ${u(g[3])}</small>
          <small>entry ₹${fmt(g[4],2)} → ${now?"now":"exit"} ₹${fmt(g[5],2)}</small></div>
        <div class="mv"><b>${pct(mv)}</b><small>best ${pct(g[6])}</small><small>worst ${pct(g[7])}</small></div></li>`; }).join("") || '<li class="pf-mut">No zone history yet.</li>'}</ul></div>

  <div class="pf-sec"><h3>Levels and trendlines</h3><div class="pf-kv">
    <div><span>Support</span><b>${lv.sup?`₹${fmt(lv.sup.p,2)} · ${lv.sup.t} touches`:"–"}</b></div>
    <div><span>Resistance</span><b>${lv.res?`₹${fmt(lv.res.p,2)} · ${lv.res.t} touches`:"–"}</b></div>
    <div><span>Falling trendline</span><b>${lv.tlr?`₹${fmt(lv.tlr.v,2)} · ${lv.tlr.t} touches`:"–"}</b></div>
    <div><span>Rising trendline</span><b>${lv.tls?`₹${fmt(lv.tls.v,2)} · ${lv.tls.t} touches`:"–"}</b></div>
    ${lv.brk?`<div><span>Broke out at</span><b>₹${fmt(lv.brk.p,2)}${lv.brk.vx?` · ${fmt(lv.brk.vx)}× vol`:""}</b></div>`:""}
  </div></div>

  <div class="pf-sec"><h3>Snapshot</h3><div class="pf-kv">
    <div><span>RSI</span><b>${fmt(z.rsi,0)}</b></div><div><span>ADX</span><b>${fmt(z.adx,0)}</b></div>
    <div><span>Cloud</span><b>${esc(z.cloud||"–")}</b></div><div><span>MACD</span><b>${esc(z.macd_x||"–")}</b></div>
    <div><span>vs 50-DMA</span><b>${pct(p.vs50)}</b></div><div><span>From 52w high</span><b>${pct(p.hi)}</b></div>
    <div><span>1M</span><b>${pct(p.r1m)}</b></div><div><span>1Y</span><b>${pct(p.r1y)}</b></div>
    <div><span>P/E</span><b>${fmt(p.f.pe)}</b></div><div><span>ROE</span><b>${p.f.roe!=null?fmt(p.f.roe)+"%":"–"}</b></div>
    <div><span>Debt/Equity</span><b>${fmt(p.f.de,2)}</b></div><div><span>Mcap</span><b>${p.f.mcap_cr!=null?"₹"+fmt(p.f.mcap_cr,0)+" cr":"–"}</b></div>
  </div></div>
  </div>`;
  dlg.querySelector(".pf-x").onclick = () => dlg.close();
  dlg.querySelectorAll("[data-t]").forEach(b=>b.onclick=()=>{ curTF=b.dataset.t; render(); });
}

function chart(z, lv, dates, tf){
  const c = z.c || [], n = c.length; if (n<2) return '<p class="pf-mut">No price history.</p>';
  const W = Math.round(Math.max(340, Math.min(900, ((dlg && dlg.clientWidth) || 900) - 32))), H = Math.round(Math.max(200, W*0.3)), P = {l:6,r:58,t:10,b:22};
  const vs = c.filter(v=>v!=null); let lo = Math.min(...vs), hi = Math.max(...vs);
  [lv.sup&&lv.sup.p, lv.res&&lv.res.p].forEach(v=>{ if(v && v>lo*0.85 && v<hi*1.15){ lo=Math.min(lo,v); hi=Math.max(hi,v);} });
  const m=(hi-lo)*0.06||1; lo-=m; hi+=m;
  const X = i => P.l + i/(n-1)*(W-P.l-P.r), Y = v => P.t + (hi-v)/(hi-lo)*(H-P.t-P.b);
  let g = "";
  (z.segs||[]).forEach(s=>{ const a = dates.indexOf(s[1]), b = dates.indexOf(s[2]); if (a<0||b<0) return;
    const x0 = a===0 ? X(0) : (X(a-1)+X(a))/2, x1 = b===n-1 ? X(n-1) : (X(b)+X(b+1))/2;
    g += `<rect x="${x0.toFixed(1)}" y="${P.t}" width="${Math.max(1,x1-x0).toFixed(1)}" height="${H-P.t-P.b}" fill="var(${ZC[CODE[s[0]]]})" opacity=".18"><title>${CODE[s[0]]}: ${dl(s[1])} → ${dl(s[2])}</title></rect>`;
    if (a>0 && s[4]!=null) g += `<circle cx="${X(a)}" cy="${Y(s[4])}" r="3.2" fill="var(${ZC[CODE[s[0]]]})" stroke="var(--panel)" stroke-width="1"><title>Entered ${CODE[s[0]]} ${dl(s[1])} at ₹${fmt(s[4],2)}</title></circle>`; });
  const hl = (v,col,lab) => v && v>=lo && v<=hi ? `<line x1="${P.l}" x2="${W-P.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="${col}" stroke-dasharray="5 4" stroke-width="1.2"/><text x="${W-P.r+4}" y="${Y(v)+4}" font-size="11" fill="${col}">${lab} ${fmt(v, v<100?2:0)}</text>` : "";
  g += hl(lv.res&&lv.res.p, cssv("--down")||"#C2453B", "R") + hl(lv.sup&&lv.sup.p, cssv("--up")||"#1E8F5A", "S");
  let d = "", pen = false;
  c.forEach((v,i)=>{ if (v==null){ pen=false; return; } d += `${pen?"L":"M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`; pen = true; });
  g += `<path d="${d}" fill="none" stroke="var(--ink)" stroke-width="1.6" stroke-linejoin="round"/>`;
  const last = vs[vs.length-1];
  g += `<text x="${W-P.r+4}" y="${Y(last)+4}" font-size="11" font-weight="700" fill="var(--ink)">${fmt(last, last<100?2:0)}</text>`;
  if (dates.length){ [0, Math.floor((n-1)/2), n-1].forEach((i,k)=>{ g += `<text x="${X(i)}" y="${H-6}" font-size="11" fill="var(--muted)" text-anchor="${["start","middle","end"][k]}">${dl(dates[i])}</text>`; }); }
  return `<svg class="pf-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Price chart coloured by technical zone">${g}</svg>`;
}

document.addEventListener("click", e => {
  const el = e.target.closest("[data-p]"); if (!el) return;
  e.preventDefault(); e.stopPropagation(); openProfile(el.dataset.p);
}, true);
document.addEventListener("keydown", e => {
  if (e.key==="/" && !/input|textarea|select/i.test(document.activeElement.tagName)){ const i=document.getElementById("gs-in"); if(i){ e.preventDefault(); i.focus(); } }
});
mountSearch();
const h = decodeURIComponent((location.hash.match(/^#stock=(.+)$/)||[])[1]||""); if (h) openProfile(h);
})();
"""
