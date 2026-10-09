"""Shared search box + stock pop-up, written to docs/profile.js.

Every page includes <div id="gsearch"></div> and <script src="profile.js">.
Any element with data-p="SYMBOL" opens that stock's profile when clicked.
"""

PROFILE_JS = r"""(function(){
const CSS = `
:root{--pz-bear:#C2453B;--pz-os:#6B4BB8;--pz-acc:#2F62C8;--pz-bull:#1E8F5A;--pz-ob:#13857A;--pz-dang:#0B6B4B;--pz-div:#A8285E;--pz-neu:#A3AFBF;--pz-na:#E1E6ED;
  --pq-lead:#1E8F5A;--pq-weak:#B9821A;--pq-lag:#C2453B;--pq-impr:#2F62C8;--p-link:#2F62C8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--pz-bear:#E9675C;--pz-os:#9C82E6;--pz-acc:#6E97F0;--pz-bull:#3FBF85;--pz-ob:#3BB8AA;--pz-dang:#5CC79A;--pz-div:#E0619A;--pz-neu:#5E6B7C;--pz-na:#263140;
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
.pf-su{display:grid;gap:8px;grid-template-columns:minmax(0,1fr);border:1px solid var(--line);border-left:5px solid var(--c);border-radius:12px;padding:10px 12px;margin:0 0 12px}
@media(min-width:760px){.pf-su{grid-template-columns:minmax(150px,auto) repeat(3,minmax(0,1fr))}}
.pf-su .hd b{display:block;font-size:1.05rem}.pf-su .hd small{color:var(--muted);font-size:.78rem}
.pf-su .it{font-size:.84rem;display:flex;gap:6px}.pf-su .it i{font-style:normal;font-weight:700;width:16px;text-align:center}
.pf-su .it small{display:block;color:var(--muted);font-size:.76rem}
.regime{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;border:1px solid var(--line);border-left:5px solid var(--c);background:var(--panel);border-radius:12px;padding:8px 12px;margin:0 0 14px;font-size:.88rem}
.regime b{font-size:.95rem}.regime details{flex-basis:100%}.regime summary{cursor:pointer;color:var(--muted);font-size:.8rem}
.regime ul{margin:6px 0 0;padding-left:18px;color:var(--muted);font-size:.82rem}
.pf-act{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.pf-snapm{position:absolute;right:0;top:calc(100% + 4px);z-index:20;min-width:220px;background:var(--p-bg,var(--panel,#fff));border:1px solid var(--line);border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.18);padding:4px 0}
.pf-snapm button{display:block;width:100%;text-align:left;background:none;border:0;color:inherit;font:inherit;font-size:.86rem;padding:8px 12px;cursor:pointer}
.pf-snapm button:hover,.pf-snapm button:focus-visible{background:var(--line)}
.pf-btn{font:600 .82rem var(--font,system-ui);border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:8px;padding:6px 12px;cursor:pointer}
.pf-btn.on{border-color:#C9780F;color:#C9780F}
.pf-btn.pri{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.pf-form{border:1px solid var(--line);border-radius:12px;padding:12px;margin:0 0 12px;display:grid;gap:10px;grid-template-columns:repeat(2,minmax(0,1fr))}
@media(min-width:760px){.pf-form{grid-template-columns:repeat(6,minmax(0,1fr))}}
.pf-form label{font-size:.76rem;color:var(--muted);display:flex;flex-direction:column;gap:3px}
.pf-form input{font:inherit;font-size:.9rem;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 8px;width:100%}
.pf-form .full{grid-column:1/-1;display:flex;gap:8px;justify-content:flex-end}
.pf-warn{border:1px solid #C9780F;color:#C9780F;border-radius:10px;padding:8px 12px;font-size:.85rem;margin:0 0 12px}
.pf-fib{display:grid;gap:10px;grid-template-columns:minmax(0,1fr)}
@media(min-width:760px){.pf-fib{grid-template-columns:repeat(2,minmax(0,1fr))}}
.pf-fib table{width:100%;border-collapse:collapse;font-size:.85rem}
.pf-fib td{padding:5px 6px;border-bottom:1px solid var(--line)}.pf-fib td:last-child{text-align:right}
.pf-fib tr.now td{font-weight:700}
.pf-ok{color:var(--up,#1E8F5A)}.pf-mid{color:#C9780F}.pf-bad{color:var(--down,#C2453B)}
`;
const st = document.createElement("style"); st.textContent = CSS; document.head.appendChild(st);

const ZC = {"Bearish":"--pz-bear","Oversold":"--pz-os","Accumulation":"--pz-acc","Bullish":"--pz-bull","Strong momentum":"--pz-ob","Extended":"--pz-dang","Divergence zone":"--pz-div","Neutral":"--pz-neu","No data":"--pz-na"};
const CODE = {R:"Bearish",O:"Oversold",A:"Accumulation",U:"Bullish",B:"Strong momentum",D:"Extended",V:"Divergence zone",N:"Neutral","-":"No data"};
const QC = {Leading:"--pq-lead",Weakening:"--pq-weak",Lagging:"--pq-lag",Improving:"--pq-impr"};
const LS = {"Breakout":"--pz-bull","Trendline breakout":"--pz-bull","Retest":"--pz-acc","At trendline support":"--pz-os","At Fibonacci support":"--pq-weak","Near support":"--pz-neu","Breakdown":"--pz-bear","Trendline breakdown":"--pz-div","Near resistance":"--pq-weak"};
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
const WL = {
  load(){ try { return JSON.parse(localStorage.getItem("azh:wl") || "{}"); } catch(e){ return {}; } },
  save(d){ try { localStorage.setItem("azh:wl", JSON.stringify(d)); } catch(e){} },
  get(){ const d = this.load(); d.watch = d.watch || {}; d.trades = d.trades || []; return d; },
};
window.AZH_WL = WL;

/* ---------- screener: shared evaluator (Screener tab + pop-up) ---------- */
const FUNDK = {"P/E":"pe","P/B":"pb","ROE %":"roe","Debt to equity":"de","Market cap (₹ cr)":"mc","Net margin %":"npm",
  "Sales growth % (vs same quarter last year)":"sg","Profit growth % (vs same quarter last year)":"pg","Dividend yield %":"dy",
  "Promoter holding %":"prom","Promoter holding change (points, last quarter)":"pchg","Pledged % of promoter shares":"plg",
  "Institutional holding %":"inst","Delivery % (latest day)":"dlv","Delivery vs its 20-day average (x)":"dlvx","Quality score (0-5)":"qs"};
let SMETA = null;
const SCR = {
  meta(){
    if (!SMETA) SMETA = fetch("screener_meta.json").then(r=>r.ok?r.json():{conds:[],presets:[]}).catch(()=>({conds:[],presets:[]}))
      .then(m=>{ m._by = Object.fromEntries((m.conds||[]).map(x=>[x.id,x])); m._p = Object.fromEntries((m.pconds||[]).map(x=>[x.id,x])); SCR._m = m; return m; });
    return SMETA; },
  blank(){ return {name:"", mode:"all", conds:[], f:{liq:true}}; },
  isP(c){ return String(c.id).startsWith("p_"); },
  pdef(m, c){ const d = m._p[c.id]; const o = {}; (d ? d.params : []).forEach(q=>{ o[q.k] = (c.p && c.p[q.k] !== undefined) ? c.p[q.k] : q.d; }); return o; },
  pEvent(m, c){ const o = SCR.pdef(m, c);
    if (["p_newhi","p_newlo","p_vol","p_gap"].includes(c.id)) return true;
    if (c.id==="p_env") return ["tu","xa","tl","xb"].includes(o.op);
    if (c.id==="p_pch") return false;
    return ["xa","xb","tb","tr"].includes(o.op); },
  pLabel(m, c, v){ const d = m._p[c.id]; if (!d) return c.id; const o = SCR.pdef(m, c);
    const opq = (d.params.find(q=>q.k==="op")||{}), opl = k => (opq.labels||{})[k] || ({gt:"above",lt:"below",xa:"crossed above",xb:"crossed below"})[k] || k;
    let t;
    switch (c.id){
      case "p_rsi": t = `RSI(${o.per}) ${opl(o.op)} ${o.x}`; break;
      case "p_chop": t = `Choppiness(${o.per}) ${opl(o.op)} ${o.x}`; break;
      case "p_adx": t = `ADX(14) ${opl(o.op)} ${o.x}`; break;
      case "p_di": t = opl(o.op); break;
      case "p_macd": t = `MACD ${o.line} ${opl(o.op)} ${o.x}`; break;
      case "p_ma": t = `Price ${opl(o.op)} ${o.type} ${o.per}`; break;
      case "p_macross": t = `${o.type} ${o.f} ${({xa:"crossed above",xb:"crossed below",gt:"above",lt:"below"})[o.op]} ${o.type} ${o.s}`; break;
      case "p_newhi": t = `New ${o.x}-bar high`; break;
      case "p_newlo": t = `New ${o.x}-bar low`; break;
      case "p_hi52": t = `Within ${o.x}% of 52-week high`; break;
      case "p_vol": t = `Volume ${o.x}× average (${o.dir} bar)`; break;
      case "p_gap": t = `Gap up ${o.x}%+`; break;
      case "p_chg": t = `Price ${o.op==="gt"?"up at least":"changed at most"} ${o.x}% over ${o.n} bars`; break;
      case "p_rng": t = `Range within ${o.x}% over ${o.n} bars`; break;
      case "p_st": t = `SuperTrend(${o.set}) ${opl(o.op)}`; break;
      case "p_pch": t = `Price within ±${o.x}% channel during last ${o.per}`; break;
      case "p_env": t = `${o.type} ${o.per} ±${o.x}% envelope: ${opl(o.op)}`; break;
      case "p_fund": return `${o.m} ${o.op==="gt"?"above":"below"} ${o.x}`;
      case "p_grade": return `Quality grade ${o.g}`;
      default: t = d.l;
    }
    return `${c.tf==="w"?"W":"D"}: ${t}${SCR.pEvent(m,c) && v>0 ? ` (${v} ${c.tf==="w"?"wk":(v===1?"bar":"bars")} ago)` : ""}`; },
  // bars-ago (0 = latest) when the condition holds, else null
  pEval(m, c, ser){
    if (!ser) return null;
    const o = SCR.pdef(m, c), n = Math.max(1, c.n || 1), X = +o.x;
    const thr = (a, op, x) => { if (!a) return null; const L = a.length - 1;
      if (op==="gt") return a[L]!=null && a[L] > x ? 0 : null;
      if (op==="lt") return a[L]!=null && a[L] < x ? 0 : null;
      for (let b=0; b<n && L-b>=1; b++){ const v1 = a[L-b], v0 = a[L-b-1]; if (v1==null||v0==null) continue;
        if (op==="xa" && v1 > x && v0 <= x) return b; if (op==="xb" && v1 < x && v0 >= x) return b; }
      return null; };
    const anyBar = (a, f) => { if (!a) return null; const L = a.length - 1; for (let b=0; b<n && L-b>=0; b++){ if (a[L-b]!=null && f(a[L-b])) return b; } return null; };
    const P = [5,10,20,30,50,100,150,200];
    switch (c.id){
      case "p_rsi": return thr((ser.rsi||{})[o.per], o.op, X*10);
      case "p_chop": return thr((ser.chop||{})[o.per], o.op, X*10);
      case "p_adx": return thr(ser.adx, o.op, X*10);
      case "p_di": { const a = (ser.pdi||[]).map((v,i)=> v==null||ser.mdi[i]==null ? null : v - ser.mdi[i]); return thr(a, o.op, 0); }
      case "p_macd": return thr(o.line==="line" ? ser.macd : o.line==="signal" ? ser.msig : ser.mh, o.op, X);
      case "p_newhi": return anyBar(ser.hia, v => v >= X - 1);
      case "p_newlo": return anyBar(ser.loa, v => v >= X - 1);
      case "p_hi52": return ser.hi52!=null && ser.hi52 <= X*10 ? 0 : null;
      case "p_vol": return anyBar(ser.vx, v => o.dir==="rising" ? v >= X*10 : o.dir==="falling" ? v <= -X*10 : Math.abs(v) >= X*10);
      case "p_gap": return anyBar(ser.gap, v => v >= X*10);
      case "p_chg": { const v = (ser.chg||{})[o.n]; if (v==null) return null; return (o.op==="gt" ? v >= X*10 : v <= X*10) ? 0 : null; }
      case "p_rng": { const v = (ser.rng||{})[o.n]; return v!=null && v <= X*10 ? 0 : null; }
      case "p_ma": { const ma = ser.ma||{}, i = (o.type==="EMA"?8:0) + P.indexOf(+o.per);
        if (o.op==="gt") return ma.s && ma.s[i]==="1" ? 0 : null;
        if (o.op==="lt") return ma.s && ma.s[i]==="0" ? 0 : null;
        const a = (ma.e||{})[`${o.op}_${o.type==="EMA"?"e":"s"}${o.per}`]; return a!=null && a < n ? a : null; }
      case "p_macross": { let f = +o.f, sl = +o.s; if (f===sl) return null;
        let op = o.op; if (f > sl){ [f, sl] = [sl, f]; op = ({xa:"xb",xb:"xa",gt:"lt",lt:"gt"})[op]; }
        const ma = ser.ma||{}, ty = o.type==="EMA"?"e":"s";
        if (op==="gt" || op==="lt"){ let k = 0, idx = -1; for (let a=0;a<P.length;a++) for (let b=a+1;b<P.length;b++){ if (P[a]===f && P[b]===sl) idx = k; k++; }
          const bit = (ma.p||"")[(ty==="e"?28:0) + idx]; return (op==="gt" ? bit==="1" : bit==="0") ? 0 : null; }
        const a = (ma.e||{})[`${op==="xa"?"ca":"cb"}_${ty}${f}_${ty}${sl}`]; return a!=null && a < n ? a : null; }
      case "p_pch": { const v = (ser.pch||{})[o.per]; return v!=null && v <= X*10 ? 0 : null; }
      case "p_env": { const e = (ser.env||{})[`${o.type==="EMA"?"e":"s"}${o.per}`]; if (!e) return null;
        const [cl, hi, lo] = e, U = X*10, Lw = -X*10, Lc = cl.length - 1;
        if (o.op==="ab") return cl[Lc]!=null && cl[Lc] > U ? 0 : null;
        if (o.op==="bl") return cl[Lc]!=null && cl[Lc] < Lw ? 0 : null;
        if (o.op==="in") return cl[Lc]!=null && cl[Lc] <= U && cl[Lc] >= Lw ? 0 : null;
        for (let b=0; b<n && Lc-b>=1; b++){ const i = Lc-b;
          if (o.op==="tu" && hi[i]!=null && hi[i] >= U && cl[i] <= U) return b;
          if (o.op==="tl" && lo[i]!=null && lo[i] <= Lw && cl[i] >= Lw) return b;
          if (o.op==="xa" && cl[i]!=null && cl[i-1]!=null && cl[i] > U && cl[i-1] <= U) return b;
          if (o.op==="xb" && cl[i]!=null && cl[i-1]!=null && cl[i] < Lw && cl[i-1] >= Lw) return b; }
        return null; }
      case "p_fund": { const f = ser.fu || {}, k = FUNDK[o.m]; const v = k ? f[k] : null; if (v==null) return null;
        return (o.op==="gt" ? v > X : v < X) ? 0 : null; }
      case "p_grade": { const g = (ser.fu||{}).qg; if (!g) return null; return ({"A":"A","A or B":"AB","A, B or C":"ABC"})[o.g].includes(g) ? 0 : null; }
      case "p_st": { const st = (ser.st||{})[o.set]; if (!st) return null; const L = st.length - 1;
        if (o.op==="bull") return st[L]==="1" ? 0 : null; if (o.op==="bear") return st[L]==="0" ? 0 : null;
        for (let b=0; b<n && L-b>=1; b++){ const a1 = st[L-b], a0 = st[L-b-1];
          if (o.op==="tb" && a1==="1" && a0==="0") return b; if (o.op==="tr" && a1==="0" && a0==="1") return b; }
        return null; }
    }
    return null; },
  lvl(r, c){ const v = (((r.sig||{})[c.tf]||{})._v||{})[c.id]; return v ? ` · ${String(c.id).startsWith("tl_")?"line":({ew_w2:"wave 1 high",ew_w3x:"wave 1 high",ew_w4:"wave 4 zone"})[c.id]||(String(c.id).startsWith("ew_")?"wave target":"level")} ₹${Number(v).toLocaleString("en-IN",{maximumFractionDigits:2})}` : ""; },
  label(m, c, v){ if (SCR.isP(c)) return SCR.pLabel(m, c, v); const x = m._by[c.id]; if (!x) return c.id;
    return `${c.tf==="w"?"W":"D"}: ${x.l}${x.k==="e" && v>0 ? ` (${v} ${c.tf==="w"?"wk":(v===1?"bar":"bars")} ago)` : ""}`; },
  hits(screen, r, m){
    m = m || SCR._m; if (!m) return null;
    const f = screen.f || {};
    if (f.liq !== false && !r.liquid) return null;
    if (f.es && r.es) return null;
    if (f.zw && r.zw !== f.zw) return null;
    if (f.zd && r.zd !== f.zd) return null;
    if (f.bk && r.bucket !== f.bk) return null;
    if (f.rs && !(r.rs >= f.rs)) return null;
    if (f.sec && r.sector !== f.sec) return null;
    if (f.q && !(f.q==="LI" ? ["Leading","Improving"].includes(r.q) : r.q===f.q)) return null;
    if (f.pmin && !(r.price >= f.pmin)) return null;
    if (f.pmax && !(r.price <= f.pmax)) return null;
    const out = []; let n = 0;
    for (const c of screen.conds || []){
      let v, ok;
      if (SCR.isP(c)){ v = SCR.pEval(m, c, (r.ser||{})[c.tf]); ok = v != null; }
      else { const x = m._by[c.id]; v = ((r.sig||{})[c.tf]||{})[c.id]; ok = x && v != null && (x.k === "s" || v < (c.n || 1)); }
      if (ok){ n++; out.push(SCR.label(m, c, v) + (SCR.isP(c) ? "" : SCR.lvl(r, c))); }
      else if ((screen.mode||"all") === "all") return null;
    }
    if ((screen.conds||[]).length && !n) return null;
    return out;
  },
};
window.AZH_SCR = SCR;
function mountRegime(){
  const wrap = document.querySelector(".wrap"), head = wrap && wrap.querySelector("header");
  if (!head) return;
  fetch("regime.json").then(r=>r.ok?r.json():null).then(g=>{ if (!g) return;
    const col = {"Risk-on":"--pq-lead","Neutral":"--pq-weak","Risk-off":"--pq-lag"}[g.state] || "--pz-neu";
    const msg = {"Risk-on":"breakouts tend to follow through","Neutral":"be selective, favour leading sectors","Risk-off":"most breakouts fail; Setups are stricter"}[g.state] || "";
    const el = document.createElement("div"); el.className = "regime"; el.style.setProperty("--c", `var(${col})`);
    const pd_ = g.asof ? new Date(g.asof+"T00:00:00").toLocaleDateString("en-IN",{weekday:"short",day:"2-digit",month:"short"}) : "";
    el.innerHTML = `<b>Market: ${esc(g.state)}</b><span class="pf-mut">${esc(msg)}</span>${g.live ? `<span style="margin-left:auto;font-size:.82rem">Prices: <b>live, ${esc(pd_)} ${esc(g.live)}</b> <span class="pf-mut">(market open; can lag up to 15 min)</span></span>` : pd_?`<span style="margin-left:auto;font-size:.82rem">Prices: close of <b>${esc(pd_)}</b></span>`:""}
      <details><summary>Why</summary><ul>${g.items.map(i=>`<li>${i.ok?"✓":i.bad?"✗":"~"} ${esc(i.t)}</li>`).join("")}</ul></details>`;
    head.insertAdjacentElement("afterend", el); }).catch(()=>{});
}
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
  ensureDialog(); curSym = sym; formOpen = false;
  dlg.innerHTML = `<div class="pf"><div class="pf-load">Loading ${esc(sym)}…</div></div>`;
  if (!dlg.open) dlg.showModal();
  history.replaceState(null,"","#stock="+encodeURIComponent(sym));
  const [idx, p] = await Promise.all([loadIndex(), loadStock(sym), SCR.meta()]);
  if (curSym!==sym) return;
  if (!p){ dlg.innerHTML = `<div class="pf"><div class="pf-h"><h2 id="pf-title">${esc(sym)}</h2><button class="pf-x" aria-label="Close">×</button></div><p class="pf-load">No data for this stock yet.</p></div>`;
    dlg.querySelector(".pf-x").onclick=()=>dlg.close(); return; }
  curData = p; if (curTF!=="m" && !p.z[curTF]) curTF = p.z.w ? "w" : "d";
  render();
}
window.openProfile = openProfile;

const BKC = {"Ready":"--pq-lead","Setting up":"--pq-impr","Watchlist":"--pz-os","Avoid":"--pq-lag"};
const mk = st => st==="OK"||st==="Good" ? ['✓','pf-ok'] : st==="Mixed"||st==="Wait"||st==="Neutral" ? ['~','pf-mid'] : st==="No data" ? ['?','pf-mut'] : ['✗','pf-bad'];
function buyStrip(p){
  const b = p.by; if (!b) return "";
  const fl = (b.flags||[]).map(x=>`<span class="pchip o" style="--c:var(--down,#C2453B);margin-left:4px">${esc(x)}</span>`).join("");
  if (b.st==="watch") return `<div class="pf-su" style="--c:#6B4BB8"><div class="hd"><b>Buy criteria: watch</b><small>within ${fmt(b.dist,1)}% of the 12-week breakout level ₹${fmt(b.trig,2)}. A weekly close at or above ₹${fmt(b.need8,2)} would trigger the signal.</small></div></div>`;
  return `<div class="pf-su" style="--c:var(--up,#1E8F5A)"><div class="hd"><b>Buy criteria: ${b.st==="new"?"new signal":"open trade"}${b.forming?" (week still forming)":""}</b>
    <small>signal week ${dl(b.sd)} at ₹${fmt(b.entry,2)} · now ${b.gain>0?"+":""}${fmt(b.gain,1)}% (best ${fmt(b.best,1)}%)</small>
    <small style="display:block"><b>Stop-loss ₹${fmt(b.sl,2)}</b> (risk ${fmt(b.risk,1)}%) · <b>Trailing stop ₹${fmt(b.trail,2)}</b> (${esc(b.trail_kind)}) · exit on a weekly close below it${fl}</small></div>
    <div class="it"><i class="ok">✓</i><div><a href="buy.html" style="color:inherit">See all buy signals</a><small>${fmt(b.room,1)}% above the trailing stop</small></div></div></div>`;
}
function setupStrip(su){
  if (!su) return "";
  const it = (st, t, d) => { const [i,c]=mk(st); return `<div class="it"><i class="${c}">${i}</i><div>${esc(t)}<small>${esc(d)}</small></div></div>`; };
  const b = su.bucket || "No setup";
  return `<div class="pf-su" style="--c:var(${BKC[b]||'--pz-neu'})"><div class="hd"><b>${esc(b)}</b><small>${esc(su.why || "no multi-timeframe setup right now")}</small>
      ${su.stop?`<small style="display:block">stop ₹${fmt(su.stop,2)} (−${fmt(su.stop_pct)}%)${su.rr!=null?` · R:R ${fmt(su.rr)}×`:""}</small>`:""}</div>
    ${it(su.mon, {OK:"Monthly uptrend",Mixed:"Monthly mixed",Weak:"Monthly weak"}[su.mon]||"No monthly data", su.mon_txt)}
    ${it(su.wk_ok?"OK":su.wk==="Base"||su.wk==="In trend"?"Mixed":"Weak", "Weekly: "+(su.wk||"no setup"), su.wk_txt)}
    ${it(su.day, "Daily: "+(su.day==="Good"?"timing good":su.day.toLowerCase()), su.day_txt)}</div>`;
}
let formOpen = false;
function actions(s){
  const d = WL.get(), w = !!d.watch[s], open = d.trades.find(t=>t.sym===s && !t.closed);
  return `<button class="pf-btn ${w?'on':''}" data-a="watch">${w?"★ Watching":"☆ Watch"}</button>
    <button class="pf-btn" data-a="trade">${open?"Edit trade":"+ Track trade"}</button>
    <a class="pf-btn" href="watchlist.html" style="text-decoration:none">My list</a>
    <button class="pf-btn" data-a="share" aria-expanded="${shareOpen}" title="Share or copy this stock">⤴ Share</button>
    ${shareOpen ? `<div class="pf-share" style="flex-basis:100%;display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:6px;padding:8px;border:1px solid var(--line);border-radius:10px">
      <button class="pf-btn" data-a="shtxt">📋 Copy summary text</button><button class="pf-btn" data-a="shlink">🔗 Copy link</button>
      <span class="pf-mut" id="pf-shmsg" role="status" style="font-size:.8rem">For a picture of the chart, use the 📷 button above the chart.</span></div>` : ""}`;
}
let shareOpen = false;
const stockLink = s => `${location.origin}${location.pathname.replace(/[^/]*$/,"")}index.html#stock=${encodeURIComponent(s)}`;
function shareText(p, s, tf){
  const z = (p.z||{}), lv = (p.lv||{})[tf] || {}, f = p.fu || {}, ew = (p.ew||{})[tf], su = p.su || {};
  const T = tf==="w" ? "Weekly" : "Daily", L = [];
  L.push(`*${s}* · ${p.n||""}`);
  L.push(`₹${fmt(p.px,2)} (${p.r1d>0?"+":""}${fmt(p.r1d,2)}% today) · ${p.sec||""}`);
  L.push(`Zones: weekly *${(z.w||{}).zone||"–"}*, daily *${(z.d||{}).zone||"–"}*`);
  if (su.bucket) L.push(`Setup: *${su.bucket}*${su.why?` – ${su.why}`:""}${su.stop?` (stop ₹${fmt(su.stop,2)})`:""}`);
  if (lv.sup || lv.res) L.push(`${T} support ₹${lv.sup?fmt(lv.sup.p,2):"–"} · resistance ₹${lv.res?fmt(lv.res.p,2):"–"}`);
  const fb = (p.fib||{})[tf]; if (fb && fb.t && fb.t.length) L.push(`Fibonacci targets: ${fb.t.slice(0,2).map(t=>"₹"+fmt(t.p,2)).join(", ")}`);
  if (ew && ew.s) L.push(`Elliott (${T.toLowerCase()}, auto): ${ew.s}${ew.tg?` · target ₹${fmt(ew.tg,2)}`:""}${ew.iv?` · wrong ${ew.ivs||(ew.d==="up"?"below":"above")} ₹${fmt(ew.iv,2)}`:""}`);
  const fx = [f.qg?`Quality *${f.qg}*`:"", f.pe!=null?`P/E ${fmt(f.pe)}`:"", f.sg!=null?`sales ${f.sg>0?"+":""}${fmt(f.sg)}%`:"", f.pg!=null?`profit ${f.pg>0?"+":""}${fmt(f.pg)}%`:"", f.prom!=null?`promoters ${fmt(f.prom,1)}%`:"", f.plg?`pledged ${fmt(f.plg,1)}%`:""].filter(Boolean);
  if (fx.length) L.push(fx.join(" · "));
  (p.al||[]).slice(0,2).forEach(x=>L.push(`${x.m<0?"🔻":x.m>0?"🔺":"•"} ${x.t}`));
  (p.nw||[]).slice(0,1).forEach(x=>L.push(`📰 ${x.t} (${newsAgo(x.d)})`));
  if (p.earn) L.push(`Results due ${dl(p.earn)}`);
  L.push(stockLink(s));
  return L.join("\n");
}
function snapInfo(p, s, tf){
  const z = (p.z||{})[tf] || {}, lv = (p.lv||{})[tf] || {}, ew = (p.ew||{})[tf], su = p.su || {}, f = p.fu || {};
  const L = [];
  L.push(`Zone: ${z.zone||"–"}${su.bucket?` · Setup: ${su.bucket}`:""}${lv.sup?` · Support ₹${fmt(lv.sup.p,2)}`:""}${lv.res?` · Resistance ₹${fmt(lv.res.p,2)}`:""}`);
  if (ew && ew.s) L.push(`Elliott (auto): ${ew.s}${ew.tg?` · target ₹${fmt(ew.tg,2)}`:""}${ew.iv?` · wrong ${ew.ivs||"below"} ₹${fmt(ew.iv,2)}`:""}`);
  const fx = [f.qg?`Quality ${f.qg}`:"", f.pe!=null?`P/E ${fmt(f.pe)}`:"", f.prom!=null?`Promoters ${fmt(f.prom,1)}%`:"", f.plg?`Pledged ${fmt(f.plg,1)}%`:"", f.dlv!=null?`Delivery ${fmt(f.dlv,0)}%`:""].filter(Boolean);
  if (fx.length) L.push(fx.join(" · "));
  return {sym: s, name: p.n, px: p.px, r1d: p.r1d, tf, lines: L};
}
function shMsg(t){ const el = dlg.querySelector("#pf-shmsg"); if (el) el.textContent = t; }
async function copyText(t){ try { await navigator.clipboard.writeText(t); return true; } catch(e){
  const ta = document.createElement("textarea"); ta.value = t; ta.style.position="fixed"; ta.style.opacity="0"; document.body.appendChild(ta); ta.select();
  let ok = false; try { ok = document.execCommand("copy"); } catch(e2){} ta.remove(); return ok; } }

function earnWarn(p){
  if (!p.earn) return "";
  const days = Math.round((new Date(p.earn+"T00:00:00") - new Date(new Date().toDateString())) / 864e5);
  if (days < 0 || days > 14) return "";
  return `<div class="pf-warn">⚠ Results due ${days===0?"today":days===1?"tomorrow":`in ${days} days`} (${dl(p.earn)}). Prices can gap either way.</div>`;
}
function tradeBox(s, p){
  const d = WL.get(), open = d.trades.find(t=>t.sym===s && !t.closed);
  if (!formOpen) {
    if (!open) return "";
    const pl = (p.px/open.price-1)*100;
    return `<div class="pf-warn" style="border-color:var(--line);color:var(--ink)">Open trade: ${open.qty||"–"} @ ₹${fmt(open.price,2)} since ${dl(open.date)} · now ${pct(pl)}${open.stop?` · stop ₹${fmt(open.stop,2)}`:""}${open.target?` · target ₹${fmt(open.target,2)}`:""}</div>`;
  }
  const su = p.su || {}, fw = (p.fib||{}).w || {}, t1 = (fw.t||[])[0];
  const v = open || {price:p.px, date:new Date().toISOString().slice(0,10), stop:su.stop, target:t1?t1.p:(su.res||null), qty:""};
  return `<form class="pf-form" data-f="trade">
    <label>Entry price<input name="price" type="number" step="0.05" required value="${v.price??""}"></label>
    <label>Date<input name="date" type="date" required value="${v.date}"></label>
    <label>Quantity<input name="qty" type="number" step="1" min="0" value="${v.qty??""}"></label>
    <label>Stop<input name="stop" type="number" step="0.05" value="${v.stop??""}"></label>
    <label>Target<input name="target" type="number" step="0.05" value="${v.target??""}"></label>
    <label>Note<input name="note" type="text" maxlength="80" value="${esc(v.note||"")}"></label>
    <div class="full">${open?`<button type="button" class="pf-btn" data-a="del">Delete</button>`:""}<button type="button" class="pf-btn" data-a="cancel">Cancel</button><button type="submit" class="pf-btn pri">${open?"Save":"Add trade"}</button></div>
  </form>`;
}
function wireActions(){
  dlg.querySelectorAll("[data-a]").forEach(b=>b.onclick=e=>{
    const a = b.dataset.a, d = WL.get(), s = curSym;
    if (a==="watch"){ if (d.watch[s]) delete d.watch[s]; else d.watch[s] = {added:new Date().toISOString().slice(0,10)}; WL.save(d); render(); }
    if (a==="trade"){ formOpen = true; render(); }
    if (a==="share"){ shareOpen = !shareOpen; render(); }
    if (a==="shtxt"){ const t = shareText(curData, s, curTF==="m"?"w":curTF);
      if (navigator.share && /Android|iPhone|iPad/i.test(navigator.userAgent)){ navigator.share({text: t}).then(()=>shMsg("Shared.")).catch(()=>copyText(t).then(ok=>shMsg(ok?"Summary copied.":"Couldn't copy."))); }
      else copyText(t).then(ok=>shMsg(ok ? "Summary copied. Paste it into WhatsApp." : "Couldn't copy on this browser.")); }
    if (a==="shlink"){ copyText(stockLink(s)).then(ok=>shMsg(ok ? "Link copied." : "Couldn't copy.")); }

    if (a==="cancel"){ formOpen = false; render(); }
    if (a==="del"){ d.trades = d.trades.filter(t=>!(t.sym===s && !t.closed)); WL.save(d); formOpen=false; render(); }
  });
  const f = dlg.querySelector("form[data-f=trade]");
  if (f) f.onsubmit = e => { e.preventDefault(); const fd = new FormData(f), d = WL.get(), s = curSym;
    const num = k => fd.get(k)==="" ? null : +fd.get(k);
    const rec = {sym:s, price:num("price"), date:fd.get("date"), qty:num("qty"), stop:num("stop"), target:num("target"), note:fd.get("note")||""};
    const i = d.trades.findIndex(t=>t.sym===s && !t.closed);
    if (i>=0) d.trades[i] = {...d.trades[i], ...rec}; else d.trades.push({id:Date.now(), ...rec});
    d.watch[s] = d.watch[s] || {added:rec.date}; WL.save(d); formOpen = false; render(); };
}
function fibBlock(f, tf, px){
  if (!f) return `<div class="pf-sec"><h3>Fibonacci (${tf==="w"?"weekly":"daily"})</h3><p class="pf-mut">No upswing of ${tf==="w"?"15":"10"}% or more in the last ${tf==="w"?"year":"6 months"}, so no Fibonacci setup.</p></div>`;
  const rows = Object.entries(f.lv).map(([k,v])=>`<tr><td>${k}% retracement</td><td>₹${fmt(v,2)}</td></tr>`).join("");
  return `<div class="pf-sec"><h3>Fibonacci (${tf==="w"?"weekly":"daily"})</h3>
    <p style="margin:0 0 8px;font-size:.88rem"><span class="pchip" style="--c:var(${f.status==="Golden pocket"?"--pz-ob":f.status==="Breakout"?"--pz-bull":f.status==="Failed"?"--pz-bear":"--pz-acc"})">${esc(f.status)}</span>
      swing ₹${fmt(f.A,2)} → ₹${fmt(f.H,2)}${f.ago?` (high ${f.ago} ${tf==="w"?"weeks":"sessions"} ago)`:""}, now ${fmt(f.ret)}% retraced${f.conf.length?` · confluence: ${esc(f.conf.join(", "))}`:""}</p>
    <div class="pf-fib"><table><tbody><tr><td>Swing high</td><td>₹${fmt(f.H,2)}</td></tr>${rows}<tr><td>Swing low</td><td>₹${fmt(f.A,2)}</td></tr></tbody></table>
      <table><tbody>${f.t.length ? f.t.map((t,i)=>`<tr><td>T${i+1} · ${esc(t.k)}</td><td>₹${fmt(t.p,2)} <span class="pf-ok">+${fmt(t.up)}%</span></td></tr>`).join("") : `<tr><td class="pf-mut">No target above the current price yet${f.C && f.status!=="Breakout"?"; projections appear once price turns up from the pullback low":""}.</td><td></td></tr>`}</tbody></table></div></div>`;
}
function screenerBlock(p, tf){
  const m = SCR._m; if (!m || !p.sg) return "";
  const sig = p.sg[tf] || {}, by = m._by;
  const groups = {};
  Object.entries(sig).forEach(([id,v])=>{ const x = by[id]; if (!x) return; (groups[x.g] ??= []).push(SCR.label(m, {id, tf}, v).replace(/^[DW]: /,"") + SCR.lvl({sig:p.sg}, {id, tf})); });
  const r = {zd:(p.z.d||{}).zone, zw:(p.z.w||{}).zone, bucket:(p.su||{}).bucket, rs:p.rs, q:(p.sq||{}).w, price:p.px, liquid:p.liq,
             es:(p.su||{}).earn_soon, sector:p.sec, sig:p.sg, ser:p.ser};
  const saved = (WL.get().screens || []).filter(s=>SCR.hits(s, {...r, liquid:true}, m));
  const presets = (m.presets || []).filter(s=>SCR.hits(s, {...r, liquid:true}, m));
  const g = Object.entries(groups);
  return `<div class="pf-sec"><h3>Screener signals (${tf==="w"?"weekly":"daily"})</h3>
    ${g.length ? `<div class="pf-kv" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr))">${g.map(([k,v])=>`<div style="display:block"><span>${esc(k)}</span><b style="display:block;font-weight:500;font-size:.84rem">${v.map(esc).join("<br>")}</b></div>`).join("")}</div>` : '<p class="pf-mut">No screener conditions met on this timeframe.</p>'}
    <p style="font-size:.85rem;margin:10px 0 0"><span class="pf-mut">Your saved screens:</span> ${saved.length ? saved.map(s=>`<a href="screener.html#screen=${encodeURIComponent(s.name)}" style="color:var(--p-link)">${esc(s.name)}</a>`).join(", ") : '<span class="pf-mut">none matched</span>'}</p>
    <p style="font-size:.85rem;margin:4px 0 0"><span class="pf-mut">Ready-made screens:</span> ${presets.length ? presets.map(s=>esc(s.name)).join(", ") : '<span class="pf-mut">none matched</span>'}</p></div>`;
}
const NWK = {res:["Results","#2F62C8"], ord:["Order win","#1E8F5A"], deal:["Deal","#7A3FC8"], corp:["Corporate action","#13857A"],
             rat:["Broker view","#C9780F"], reg:["Regulatory","#C2453B"], mgmt:["Management","#5B6472"], oth:["News","#5B6472"]};
function newsAgo(iso){ const d = Math.round((new Date(new Date().toISOString().slice(0,10)) - new Date(iso)) / 864e5);
  return d<=0 ? "today" : d===1 ? "yesterday" : `${d} days ago`; }
const QGC = {A:"#1E8F5A", B:"#2F62C8", C:"#C9780F", D:"#C2453B"};
function fundBlock(p){
  const f = p.fu || {}, al = p.al || [];
  const v = (x, d=1, suf="") => x==null ? "–" : fmt(x, d) + suf;
  const sgn = (x, d=1, suf="%") => x==null ? "–" : `<span style="color:${x>=0?"var(--up,#1E8F5A)":"var(--down,#C2453B)"}">${x>0?"+":""}${fmt(x,d)}${suf}</span>`;
  const qd = f.qe ? new Date(f.qe+"T00:00:00").toLocaleDateString("en-IN",{month:"short",year:"numeric"}) : null;
  const cells = [
    ["P/E", v(f.pe)], ["P/B", v(f.pb)], ["ROE", v(f.roe,1,"%")], ["Debt / equity", v(f.de,2)],
    ["Market cap", f.mc!=null ? "₹"+fmt(f.mc,0)+" cr" : "–"], ["Net margin", v(f.npm,1,"%")],
    [`Sales growth${qd?` (${qd} qtr, YoY)`:" (YoY)"}`, sgn(f.sg)], [`Profit growth${qd?` (${qd} qtr, YoY)`:" (YoY)"}`, sgn(f.pg)],
    ["Dividend yield", v(f.dy,2,"%")], ["Institutions hold", v(f.inst,1,"%")],
    ["Promoters hold", v(f.prom,2,"%") + (f.pchg!=null ? ` <small>(${f.pchg>0?"+":""}${fmt(f.pchg,2)} last qtr)</small>` : "")],
    ["Pledged (of promoter shares)", f.plg!=null ? `<span style="color:${f.plg>25?"var(--down,#C2453B)":"inherit"}">${fmt(f.plg,1)}%</span>` : "–"],
    ["Delivery % (latest day)", f.dlv!=null ? `${fmt(f.dlv,0)}%${f.dlvx!=null?` <small>(${fmt(f.dlvx,1)}× its 20-day avg)</small>`:""}` : "–"],
    ["Surveillance", f.asm ? `<span style="color:var(--down,#C2453B)">${esc(f.asm)}</span>` : "none"]];
  const tone = m => m>0 ? ["▲","var(--up,#1E8F5A)"] : m<0 ? ["▼","var(--down,#C2453B)"] : ["•","var(--muted)"];
  const alerts = al.slice(0, 8).map(x=>{ const t = tone(x.m); return `<li style="display:flex;gap:8px;padding:5px 0;border-top:1px solid var(--line);font-size:.85rem"><b style="color:${t[1]}">${t[0]}</b><span style="flex:1">${esc(x.t)}<br><small class="pf-mut">${newsAgo(x.d)}</small></span></li>`; }).join("");
  const grade = f.qg ? `<span class="pchip" style="--c:${QGC[f.qg]};margin-left:6px" title="Quality score ${fmt(f.qs,1)} of 5">Quality ${f.qg}</span>` : "";
  return `<div class="pf-sec"><h3>Fundamentals and alerts ${grade}</h3>
    ${alerts ? `<ul style="list-style:none;margin:0 0 10px;padding:0">${alerts}</ul>` : `<p class="pf-mut" style="font-size:.85rem;margin:0 0 8px">No promoter, insider, pledge, bulk-deal or surveillance alerts.</p>`}
    <div class="pf-kv">${cells.map(([k,x])=>`<div><span>${k}</span><b>${x}</b></div>`).join("")}</div>
    <p class="pf-mut" style="font-size:.75rem;margin:6px 0 0">Quality grade: ROE 15%+, sales and profit growth 10%+, net margin 8%+, debt/equity 1 or less (not used for banks and finance companies), one grade lower if over 25% of promoter shares are pledged or the stock is under surveillance. Sources: NSE results, insider and pledge filings, bulk/block deals and delivery data; Yahoo for ROE, P/B and debt when available. "–" means not available yet.</p></div>`;
}
function newsBlock(p){
  const items = p.nw || [];
  if (!items.length) return `<div class="pf-sec"><h3>News and triggers</h3><p class="pf-mut" style="font-size:.85rem">No company filings or headlines matched this stock in the last 30 days.</p></div>`;
  const row = x => { const k = NWK[x.k] || NWK.oth, tone = x.m>0 ? ["▲","var(--up,#1E8F5A)","positive"] : x.m<0 ? ["▼","var(--down,#C2453B)","negative"] : ["•","var(--muted)","neutral"];
    const t = x.u && /^https?:\/\//i.test(x.u) ? `<a href="${esc(x.u)}" target="_blank" rel="noopener" style="color:inherit">${esc(x.t)}</a>` : esc(x.t);
    return `<li style="display:flex;gap:8px;align-items:baseline;padding:6px 0;border-top:1px solid var(--line);font-size:.86rem">
      <b style="color:${tone[1]}" title="${tone[2]} tone" aria-label="${tone[2]} tone">${tone[0]}</b>
      <span style="flex:1">${t}<br><small class="pf-mut">${newsAgo(x.d)} · ${esc(x.s||"")}</small></span>
      <span class="pchip" style="--c:${k[1]};white-space:nowrap">${x.f?"Filing · ":""}${k[0]}</span></li>`; };
  const recent = items.filter(x => (new Date() - new Date(x.d)) / 864e5 <= 3);
  const top = items.slice(0, 5), rest = items.slice(5);
  return `<div class="pf-sec"><h3>News and triggers ${recent.length ? `<span class="pchip" style="--c:#C9780F;margin-left:6px">${recent.length} in the last 3 days</span>` : ""}</h3>
    <ul style="list-style:none;margin:0;padding:0">${top.map(row).join("")}</ul>
    ${rest.length ? `<details style="margin-top:4px"><summary class="pf-mut" style="cursor:pointer;font-size:.82rem">${rest.length} older item${rest.length>1?"s":""}</summary><ul style="list-style:none;margin:0;padding:0">${rest.map(row).join("")}</ul></details>` : ""}
    <p class="pf-mut" style="font-size:.75rem;margin:6px 0 0">From NSE company filings and market news feeds, matched by company name. Tone (▲ ▼) is a keyword guess. Read the item before acting.</p></div>`;
}
function renderMonthly(p, s){
  const m = p.m;
  const body = !m || !m.c || m.c.length < 2 ? '<p class="pf-mut">Not enough monthly history.</p>' : (()=>{
    const c = m.c, n = c.length, W = Math.round(Math.max(340, Math.min(900, (dlg.clientWidth||900) - 32))), H = Math.round(Math.max(200, W*0.3)), P = {l:6,r:58,t:10,b:22};
    const vals = [...c, ...m.sma.filter(v=>v!=null)]; let lo = Math.min(...vals), hi = Math.max(...vals); const g0=(hi-lo)*0.06||1; lo-=g0; hi+=g0;
    const X = i => P.l + i/(n-1)*(W-P.l-P.r), Y = v => P.t + (hi-v)/(hi-lo)*(H-P.t-P.b);
    const path = arr => { let d="", pen=false; arr.forEach((v,i)=>{ if(v==null){pen=false;return;} d+=`${pen?"L":"M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`; pen=true; }); return d; };
    let g = `<path d="${path(m.sma)}" fill="none" stroke="var(--pq-impr)" stroke-width="1.6" stroke-dasharray="5 4"/>`;
    g += `<path d="${path(c)}" fill="none" stroke="var(--ink)" stroke-width="1.8" stroke-linejoin="round"/>`;
    g += `<text x="${W-P.r+4}" y="${Y(c[n-1])+4}" font-size="11" font-weight="700" fill="var(--ink)">${fmt(c[n-1], c[n-1]<100?2:0)}</text>`;
    const lab = d => new Date(d+"-01T00:00:00").toLocaleDateString("en-IN",{month:"short",year:"2-digit"});
    [0, Math.floor((n-1)/2), n-1].forEach((i,k)=>{ g += `<text x="${X(i)}" y="${H-6}" font-size="11" fill="var(--muted)" text-anchor="${["start","middle","end"][k]}">${lab(m.d[i])}</text>`; });
    return `<svg class="pf-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Monthly closes with 10-month average">${g}</svg>
      <div class="pf-key"><span><i style="--c:var(--ink)"></i>Monthly close</span><span><i style="--c:var(--pq-impr)"></i>10-month average</span></div>`; })();
  const chk = m ? [["Above 10-month average", m.chk.ma],["Monthly RSI 50 or higher"+(m.rsi!=null?` (${fmt(m.rsi,0)})`:""), m.chk.rsi],["Monthly MACD rising", m.chk.macd]] : [];
  return `<div class="pf-cards" style="grid-template-columns:repeat(auto-fit,minmax(200px,1fr))">
      <div class="pf-card"><h3>Monthly trend</h3><div class="big">${esc(m ? ({OK:"Uptrend",Mixed:"Mixed",Weak:"Weak"}[m.status]||m.status) : "No data")}</div><small>${esc(m ? m.txt : "")}</small></div>
      <div class="pf-card"><h3>Checks</h3>${chk.map(([t,ok])=>`<small class="${ok?'pf-ok':'pf-bad'}">${ok?'✓':'✗'} ${esc(t)}</small>`).join("")}</div></div>
    <div class="pf-sec"><h3>Last 5 years, monthly</h3>${body}</div>
    <p class="pf-mut" style="font-size:.8rem">The monthly view is a trend filter only. Zones and levels are calculated on daily and weekly bars. The current month is included while it is still forming.</p>`;
}
function render(){
  const p = curData, s = curSym, tf = curTF, z = p.z[tf] || {}, lv = p.lv[tf] || {};
  const U = tf==="d" ? ["session","sessions"] : ["week","weeks"], u = n => `${n} ${n===1?U[0]:U[1]}`;
  const dates = (IDX && IDX.dates && IDX.dates[tf]) || [];
  const segs = z.segs || [], cur = segs[segs.length-1];
  const sinceTxt = z.capped ? `since before ${dl(dates[0])}` : `since ${dl(z.since)}, ${u(z.days)}`;
  const sig = (lv.sig||[]);
  const keepTop = (dlg.querySelector(".pf")||{}).scrollTop || 0;
  dlg.innerHTML = `<div class="pf">
  <div class="pf-h"><div><h2 id="pf-title">${esc(s)}</h2><p>${esc(p.n)} · ${esc(p.sec)}${p.ind && p.ind!==p.sec ? " · "+esc(p.ind) : ""}${p.liq?"":" · low liquidity"}</p>
    <div class="pf-px">₹${fmt(p.px,2)} <span>${pct(p.r1d,2)} today</span></div>
    <div class="pf-act">${actions(s)}</div></div>
    <button class="pf-x" aria-label="Close">×</button></div>
  <div class="pf-bar"><div class="pf-seg" role="group" aria-label="Timeframe">
      <button data-t="d" aria-pressed="${tf==="d"}">Daily</button><button data-t="w" aria-pressed="${tf==="w"}">Weekly</button><button data-t="m" aria-pressed="${tf==="m"}">Monthly</button></div>
    <span class="pf-lk"><a href="${tvurl(s, tf==="m"?"M":tf==="w"?"W":"D")}" target="_blank" rel="noopener">TradingView</a><a href="${scrurl(s)}" target="_blank" rel="noopener">Screener</a></span></div>

  ${earnWarn(p)}${tradeBox(s, p)}
  ${setupStrip(p.su)}
  ${buyStrip(p)}
  ${fundBlock(p)}
  ${newsBlock(p)}
  ${tf==="m" ? renderMonthly(p, s) : `  ${tf==="w" && IDX && IDX.partial ? `<p class="pf-mut" style="font-size:.8rem;margin:0 0 10px">This week is still forming (prices up to ${dl(IDX.asof)}), so the weekly zone can change until Friday's close.</p>` : ""}
  <div class="pf-cards">
    <div class="pf-card"><h3>Technical zone</h3><div>${zchip(z.zone)}</div><small>${sinceTxt}</small>${z.prev?`<small>came from ${esc(z.prev)}</small>`:""}${z.div?`<small style="color:var(--pz-div)">${esc(z.div.kind)} divergence: high ₹${fmt(z.div.p1,2)} (${dl(z.div.d1)}, RSI ${fmt(z.div.r1,0)}) → higher high ₹${fmt(z.div.p2,2)} (${dl(z.div.d2)}, RSI ${fmt(z.div.r2,0)})</small>`:""}</div>
    <div class="pf-card"><h3>Since entering the zone</h3><div class="big">${pct(z.move)}</div><small>entry ₹${fmt(z.entry,2)} → now ₹${fmt(p.px,2)}</small>${cur&&cur[6]!=null?`<small>best ${pct(cur[6])} · worst ${pct(cur[7])}</small>`:""}</div>
    <div class="pf-card"><h3>Sector rotation</h3><div>${qchip(p.sq&&p.sq[tf])}</div><small>${esc(p.sec)} vs NIFTY 50</small><div style="margin-top:6px">${qchip(p.rq&&p.rq[tf])}</div><small>this stock vs its sector</small></div>
    <div class="pf-card"><h3>Levels</h3><div>${sig.length ? sig.map(x=>`<span class="pchip" style="--c:var(${LS[x]})">${esc(x)}</span>`).join(" ") : '<span class="pf-mut">No signal</span>'}</div>
      <small>support ${lv.sup?`₹${fmt(lv.sup.p,2)} (−${fmt(lv.sup.d)}%)`:"–"}</small><small>resistance ${lv.res?`₹${fmt(lv.res.p,2)} (+${fmt(lv.res.d)}%)`:"–"}</small></div>
  </div>

  <div class="pf-sec"><h3>Price chart (${tf==="w"?"weekly":"daily"} candles)</h3>${chart(z, lv, dates, tf, (p.fib||{})[tf], {pat: (p.pat||{})[tf], ew: (p.ew||{})[tf], sym: s, snap: snapInfo(p, s, tf)})}
    <div class="pf-key">${["Bullish","Strong momentum","Extended","Divergence zone","Bearish","Oversold","Accumulation","Neutral"].map(k=>`<span><i style="--c:var(${ZC[k]})"></i>${k}</span>`).join("")}</div></div>

  ${fibBlock((p.fib||{})[tf], tf, p.px)}

  <div class="pf-sec"><h3>Zone lifecycle</h3>
    <ul class="tl">${segs.slice().reverse().map((g,i)=>{ const name = CODE[g[0]], now = i===0;
      const mv = g[4] && g[5] ? (g[5]/g[4]-1)*100 : null;
      return `<li style="--c:var(${ZC[name]})"><span class="rail"></span>
        <div class="when">${zchip(name)} ${now?'<b> now</b>':''}<small>${g[8]?`before ${dl(g[1])}`:(tf==="w"?"week of "+dl(g[1]):dl(g[1]))} → ${now?"today":dl(g[2])} · ${u(g[3])}${now && tf==="w" && IDX && IDX.partial ? " (this week in progress)" : ""}</small>
          <small>entry ₹${fmt(g[4],2)} → ${now?"now":"exit"} ₹${fmt(g[5],2)}</small></div>
        <div class="mv"><b>${pct(mv)}</b><small>best ${pct(g[6])}</small><small>worst ${pct(g[7])}</small></div></li>`; }).join("") || '<li class="pf-mut">No zone history yet.</li>'}</ul></div>

  <div class="pf-sec"><h3>Levels and trendlines</h3><div class="pf-kv">
    <div><span>Support</span><b>${lv.sup?`₹${fmt(lv.sup.p,2)} · ${lv.sup.t} touches`:"–"}</b></div>
    <div><span>Resistance</span><b>${lv.res?`₹${fmt(lv.res.p,2)} · ${lv.res.t} touches`:"–"}</b></div>
    <div><span>Falling trendline</span><b>${lv.tlr?`₹${fmt(lv.tlr.v,2)} · ${lv.tlr.t} touches`:"–"}</b></div>
    <div><span>Rising trendline</span><b>${lv.tls?`₹${fmt(lv.tls.v,2)} · ${lv.tls.t} touches`:"–"}</b></div>
    ${lv.brk?`<div><span>Broke out at</span><b>₹${fmt(lv.brk.p,2)}${lv.brk.vx?` · ${fmt(lv.brk.vx)}× vol`:""}</b></div>`:""}
  </div></div>

  ${screenerBlock(p, tf)}

  <div class="pf-sec"><h3>Snapshot</h3><div class="pf-kv">
    <div><span>RSI</span><b>${fmt(z.rsi,0)}</b></div><div><span>ADX</span><b>${fmt(z.adx,0)}</b></div>
    <div><span>Cloud</span><b>${esc(z.cloud||"–")}</b></div><div><span>MACD</span><b>${esc(z.macd_x||"–")}</b></div>
    <div><span>vs 50-DMA</span><b>${pct(p.vs50)}</b></div><div><span>From 52w high</span><b>${pct(p.hi)}</b></div>
    <div><span>1M</span><b>${pct(p.r1m)}</b></div><div><span>1Y</span><b>${pct(p.r1y)}</b></div>
    <div><span>RS rank</span><b>${p.rs??"–"}</b></div><div><span>Next results</span><b>${p.earn?dl(p.earn):"–"}</b></div>
  </div></div>`}
  </div>`;
  if (keepTop) dlg.querySelector(".pf").scrollTop = keepTop;
  dlg.querySelector(".pf-x").onclick = () => dlg.close();
  dlg.querySelectorAll("[data-t]").forEach(b=>b.onclick=()=>{ curTF=b.dataset.t; render(); });
  wireActions();
}

/* ---------- candlestick chart with line studies ---------- */
const CH_KEY = "azh:chart";
const chOpts = () => { try { return {zones:true, sr:true, tl:true, fib:true, ma:false, pat:true, ew:true, ...JSON.parse(localStorage.getItem(CH_KEY)||"{}")}; } catch(e){ return {zones:true,sr:true,tl:true,fib:true,ma:false,pat:true,ew:true}; } };
function chart(z, lv, dates, tf, fb, opt){
  opt = opt || {};
  const host = opt.width || ((dlg && dlg.open && dlg.clientWidth) || 900);
  const W = Math.round(Math.max(340, Math.min(1000, host - 32)));
  const T = chOpts(), id = "ch" + Math.random().toString(36).slice(2,8);
  // zoom: number of bars shown; older bars come from px/<shard>.json, loaded on first zoom-out
  const ZO = tf==="w" ? [["1Y",52],["2Y",104],["3Y",156],["5Y",260]] : [["3M",60],["6M",120],["1Y",250],["2Y",500]];
  const want = T["z"+tf] || (W < 600 ? ZO[0][1] : ZO[1][1]);
  let zc = z.c || [], zo = z.o, zh = z.h, zl = z.l, zdates = dates || [], more = false, loading = false;
  if (want > zc.length && opt.sym){
    const L = longData(opt.sym, tf);
    if (L === undefined){ loading = true; loadLong(opt.sym).then(()=>{ if (opt.redraw) opt.redraw(); else if (dlg && dlg.open) render(); }); }
    else if (L){ const pad = a => a || zc.map(()=>null);
      zo = [...L.o, ...(zo || zc)]; zh = [...L.h, ...pad(zh)]; zl = [...L.l, ...pad(zl)]; zc = [...L.c, ...zc]; zdates = [...L.dates, ...zdates]; more = true; }
  }
  const full = zc.length, cut = Math.max(0, full - want);
  const sl = a => (a || []).slice(cut);
  let c = sl(zc); const lead = c.findIndex(v=>v!=null);          // skip bars before the stock listed
  const cut2 = cut + Math.max(0, lead);
  const sl2 = a => (a || []).slice(cut2);
  c = sl2(zc); const n = c.length; if (n<2) return '<p class="pf-mut">No price history.</p>';
  const o = zo ? sl2(zo) : c.map((v,i)=>i ? c[i-1] : v), h = zh ? sl2(zh) : c, l = zl ? sl2(zl) : c;
  dates = sl2(zdates);
  const H = Math.round(Math.max(240, W*0.42)), P = {l:6,r:62,t:12,b:24};
  const hv = h.filter(v=>v!=null), lw = l.filter(v=>v!=null);
  if (!hv.length) return '<p class="pf-mut">No price history.</p>';
  let lo = Math.min(...lw), hi = Math.max(...hv);
  const near = v => v && v > lo*0.9 && v < hi*1.1;
  [lv.sup&&lv.sup.p, lv.res&&lv.res.p].forEach(v=>{ if (T.sr && near(v)){ lo=Math.min(lo,v); hi=Math.max(hi,v);} });
  const m=(hi-lo)*0.05||1; lo-=m; hi+=m;
  const step = (W-P.l-P.r)/n, X = i => P.l + (i+0.5)*step, Y = v => P.t + (hi-v)/(hi-lo)*(H-P.t-P.b);
  const inR = v => v!=null && v>=lo && v<=hi;
  const up = cssv("--up")||"#1E8F5A", dn = cssv("--down")||"#C2453B";
  let g = "";
  // zone shading
  if (T.zones) (z.segs||[]).forEach(s=>{ let a = dates.indexOf(s[1]); const b = dates.indexOf(s[2]); if (b<0) return; if (a<0) a = 0;
    g += `<rect x="${(P.l+a*step).toFixed(1)}" y="${P.t}" width="${Math.max(1,(b-a+1)*step).toFixed(1)}" height="${H-P.t-P.b}" fill="var(${ZC[CODE[s[0]]]})" opacity=".13"><title>${CODE[s[0]]}: ${dl(s[1])} → ${dl(s[2])}</title></rect>`; });
  // horizontal grid
  for (let k=1;k<4;k++){ const v = lo + (hi-lo)*k/4; g += `<line x1="${P.l}" x2="${W-P.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)" stroke-width=".6"/><text x="${W-P.r+4}" y="${Y(v)+4}" font-size="10" fill="var(--muted)">${fmt(v, v<100?2:0)}</text>`; }
  // moving averages
  if (T.ma) [[20,"#2F62C8"],[50,"#C9780F"]].forEach(([p,col])=>{ let d="", pen=false;
    for (let i=0;i<n;i++){ if (i<p-1){ continue; } let sum=0, ok=true; for (let j=i-p+1;j<=i;j++){ if (c[j]==null){ ok=false; break; } sum+=c[j]; }
      if (!ok){ pen=false; continue; } const v=sum/p; d += `${pen?"L":"M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`; pen=true; }
    g += `<path d="${d}" fill="none" stroke="${col}" stroke-width="1.3" opacity=".9"/>`; });
  // candles
  const bw = Math.max(1, Math.min(10, step*0.68));
  if (step < 2.2){ let d="", pen=false; for (let i=0;i<n;i++){ if (c[i]==null){ pen=false; continue; } d += `${pen?"L":"M"}${X(i).toFixed(1)},${Y(c[i]).toFixed(1)}`; pen=true; }
    g += `<path d="${d}" fill="none" stroke="var(--ink)" stroke-width="1.3"/>`; }
  else for (let i=0;i<n;i++){ if (c[i]==null || h[i]==null || l[i]==null) continue;
    const op = o[i]!=null ? o[i] : (i ? c[i-1] : c[i]), col = c[i] >= op ? up : dn, x = X(i);
    const yT = Y(Math.max(op,c[i])), yB = Y(Math.min(op,c[i]));
    g += `<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${Y(h[i]).toFixed(1)}" y2="${Y(l[i]).toFixed(1)}" stroke="${col}" stroke-width="1"/>`;
    g += `<rect x="${(x-bw/2).toFixed(1)}" y="${yT.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(1,yB-yT).toFixed(1)}" fill="${col}"/>`; }
  // zone entry markers
  if (T.zones) (z.segs||[]).forEach(s=>{ const a = dates.indexOf(s[1]); if (a>0 && s[4]!=null && inR(s[4]))
    g += `<path d="M${X(a)},${(Y(l[a]??s[4])+6).toFixed(1)} l-4,7 h8 z" fill="var(${ZC[CODE[s[0]]]})"><title>Entered ${CODE[s[0]]} ${dl(s[1])} at ₹${fmt(s[4],2)}</title></path>`; });
  // support / resistance
  const hl = (v,col,lab,dash) => inR(v) ? `<line x1="${P.l}" x2="${W-P.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="${col}" stroke-dasharray="${dash||"6 4"}" stroke-width="1.3"/><text x="${W-P.r+4}" y="${Y(v)+4}" font-size="11" font-weight="600" fill="${col}">${lab} ${fmt(v, v<100?2:0)}</text>` : "";
  if (T.sr){ g += hl(lv.res&&lv.res.p, dn, "R") + hl(lv.sup&&lv.sup.p, up, "S"); }
  // trendlines: start point is `ag` bars before the last bar
  if (T.tl) [["tlr", dn, "Falling trendline"],["tls", up, "Rising trendline"]].forEach(([k,col,name])=>{ const t = lv[k]; if (!t || t.ag==null || t.va==null) return;
    const ia = (n-1) - t.ag, slope = t.ag ? (t.v - t.va)/t.ag : 0, x0 = Math.max(0, ia), y0 = t.va + slope*(x0 - ia);
    const x1 = n - 1 + 3, y1 = t.v + slope*3;
    g += `<line x1="${X(x0).toFixed(1)}" y1="${Y(y0).toFixed(1)}" x2="${Math.min(W-P.r, X(x1)).toFixed(1)}" y2="${Y(y1).toFixed(1)}" stroke="${col}" stroke-width="1.8"><title>${name}: ₹${fmt(t.v,2)} now, ${t.t} touches</title></line>`; });
  // chart pattern (same lines the screener used)
  const pgs = Array.isArray(opt.pat) ? opt.pat : (opt.pat ? [opt.pat] : []);
  if (T.pat) pgs.forEach((pg, pi)=>{
    const col = ["#7A3FC8","#B5338A","#2C7A8C"][pi % 3];
    pg.lines.forEach(([a0, v0, a1, v1])=>{ let i0 = (n-1)-a0, i1 = (n-1)-a1; if (i1 < 0) return;
      let y0 = v0; if (i0 < 0){ y0 = v0 + (v1-v0) * (0 - i0)/(i1 - i0); i0 = 0; }
      g += `<line x1="${X(i0).toFixed(1)}" y1="${Y(y0).toFixed(1)}" x2="${X(i1).toFixed(1)}" y2="${Y(v1).toFixed(1)}" stroke="${col}" stroke-width="2" stroke-dasharray="7 3"><title>${esc(pg.name)}</title></line>`; });
    const a = pg.lines[0], ia = Math.max(0, (n-1)-a[0]);
    g += `<text x="${X(ia)+2}" y="${P.t+12+pi*13}" font-size="11" font-weight="700" fill="${col}">${esc(pg.name)}</text>`;
  });
  // Elliott wave count (automatic): labelled swing points, target and invalidation levels
  const ew = opt.ew;
  if (T.ew && ew && ew.pts){ const col = ew.d==="up" ? "#1F6FB2" : "#B5338A"; let d="";
    const vis = ew.pts.map(([a,v,lab])=>[(n-1)-a, v, lab]).filter(([i])=>i>=0);
    vis.forEach(([i,v],k)=>{ d += `${k?"L":"M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`; });
    g += `<path d="${d}" fill="none" stroke="${col}" stroke-width="1.6" opacity=".85"/>`;
    vis.forEach(([i,v,lab], k)=>{ const all = ew.pts.length, j = all - vis.length + k;
      const isHigh = (j%2===1) === (ew.d==="up");
      const y = Y(v) + (isHigh ? -9 : 17);
      g += `<circle cx="${X(i).toFixed(1)}" cy="${(y-4).toFixed(1)}" r="7.5" fill="var(--card,#fff)" stroke="${col}" stroke-width="1.2"/><text x="${X(i).toFixed(1)}" y="${y.toFixed(1)}" font-size="10" font-weight="700" text-anchor="middle" fill="${col}">${lab==="0"?"·":lab}</text>`; });
    if (inR(ew.tg)) g += `<line x1="${P.l}" x2="${W-P.r}" y1="${Y(ew.tg)}" y2="${Y(ew.tg)}" stroke="${col}" stroke-width="1" stroke-dasharray="10 4"/><text x="${W-P.r+4}" y="${Y(ew.tg)+4}" font-size="10" font-weight="600" fill="${col}">EW ${fmt(ew.tg, ew.tg<100?2:0)}</text>`;
    if (inR(ew.iv)) g += `<line x1="${P.l}" x2="${W-P.r}" y1="${Y(ew.iv)}" y2="${Y(ew.iv)}" stroke="var(--muted)" stroke-width="1" stroke-dasharray="1 3"/><text x="${(P.l + (W-P.r-P.l)*0.4).toFixed(0)}" y="${Y(ew.iv)+12}" font-size="10" fill="var(--muted)">EW count wrong ${ew.ivs||(ew.d==="up"?"below":"above")} ${fmt(ew.iv, ew.iv<100?2:0)}</text>`;
  }
  // fibonacci
  if (T.fib && fb){ ["38.2","50","61.8"].forEach(k=>{ const v = fb.lv[k]; if (inR(v))
      g += `<line x1="${P.l}" x2="${W-P.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="#C9780F" stroke-width="1" stroke-dasharray="2 3"/><text x="${P.l+4}" y="${Y(v)-3}" font-size="10" fill="#C9780F">Fib ${k}%</text>`; });
    (fb.t||[]).slice(0,2).forEach((t,i)=>{ if (inR(t.p)) g += `<line x1="${P.l}" x2="${W-P.r}" y1="${Y(t.p)}" y2="${Y(t.p)}" stroke="#13857A" stroke-width="1" stroke-dasharray="8 3"/><text x="${P.l+4}" y="${Y(t.p)-3}" font-size="10" fill="#13857A">T${i+1} ${fmt(t.p, t.p<100?2:0)}</text>`; }); }
  // last price tag
  const last = c[n-1]; if (last!=null){ const col = c[n-1] >= (o[n-1]??c[n-2]??last) ? up : dn;
    g += `<rect x="${W-P.r+1}" y="${Y(last)-9}" width="${P.r-3}" height="17" rx="3" fill="${col}"/><text x="${W-P.r+5}" y="${Y(last)+4}" font-size="11" font-weight="700" fill="#fff">${fmt(last, last<100?2:0)}</text>`; }
  if (dates.length){ [0, Math.floor((n-1)/2), n-1].forEach((i,k)=>{ g += `<text x="${X(i)}" y="${H-7}" font-size="11" fill="var(--muted)" text-anchor="${["start","middle","end"][k]}">${dl(dates[i])}</text>`; }); }
  g += `<line class="cx" x1="0" x2="0" y1="${P.t}" y2="${H-P.b}" stroke="var(--muted)" stroke-dasharray="3 3" visibility="hidden"/>`;
  const btn = (k, label) => `<button type="button" class="pf-btn ${T[k]?'on':''}" data-ct="${k}" aria-pressed="${!!T[k]}" style="padding:3px 9px;font-size:.76rem">${label}</button>`;
  const html = `<div class="pf-act" style="margin:0 0 6px">${btn("zones","Zones")}${btn("sr","Support / resistance")}${btn("tl","Trendlines")}${btn("fib","Fibonacci")}${btn("pat","Pattern")}${btn("ew","Elliott")}${btn("ma","MA 20 / 50")}<span style="position:relative;margin-left:auto"><button type="button" class="pf-btn" data-snap aria-haspopup="menu" aria-expanded="false" title="Chart snapshot" style="padding:3px 10px;font-size:.9rem">📷</button><div class="pf-snapm" role="menu" hidden></div></span></div>
    ${T.ew && ew && ew.s ? `<div style="font-size:.8rem;margin:0 0 4px"><b style="color:${ew.d==="up"?"#1F6FB2":"#B5338A"}">Elliott (auto count):</b> ${esc(ew.s)}${ew.tg?` · target ₹${fmt(ew.tg,2)}`:""}${ew.iv?` · count is wrong ${ew.ivs||(ew.d==="up"?"below":"above")} ₹${fmt(ew.iv,2)}`:""}</div>` : ""}
    <div class="pf-act" style="margin:0 0 6px" role="group" aria-label="Zoom">${ZO.map(([lab,b])=>`<button type="button" class="pf-btn ${want===b?'on':''}" data-cz="${b}" aria-pressed="${want===b}" style="padding:3px 9px;font-size:.76rem">${lab}</button>`).join("")}</div>
    <div class="pf-mut" id="${id}-r" style="font-size:.78rem;min-height:1.2em">${loading ? "Loading older prices… " : ""}${n} ${tf==="w"?"weeks":"sessions"} shown${step < 2.2 ? " (closing-price line; zoom in for candles)" : ""}. Tap or hover for prices.</div>
    <svg id="${id}" class="pf-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Candlestick chart with support, resistance, trendlines and Fibonacci levels" style="touch-action:pan-y">${g}</svg>`;
  setTimeout(()=>{ const svg = document.getElementById(id); if (!svg) return;
    const r = document.getElementById(id+"-r"), cx = svg.querySelector(".cx");
    const show = ev => { const pt = svg.getBoundingClientRect(), x = (ev.clientX - pt.left) * W / pt.width;
      const i = Math.max(0, Math.min(n-1, Math.floor((x - P.l)/step))); if (c[i]==null) return;
      cx.setAttribute("x1", X(i)); cx.setAttribute("x2", X(i)); cx.setAttribute("visibility","visible");
      const ch = i ? (c[i]/c[i-1]-1)*100 : null;
      r.innerHTML = `<b>${dl(dates[i])}</b> · O ${fmt(o[i],2)} · H ${fmt(h[i],2)} · L ${fmt(l[i],2)} · C ${fmt(c[i],2)}${ch!=null?` (${pct(ch,2)})`:""}`; };
    svg.addEventListener("pointermove", show); svg.addEventListener("pointerdown", show);
    const wrap = svg.parentElement;
    const sb = wrap.querySelector("[data-snap]"), sm = wrap.querySelector(".pf-snapm");
    if (sb && sm){
      const canFiles = !!(navigator.canShare && (()=>{ try { return navigator.canShare({files:[new File([""],"a.png",{type:"image/png"})]}); } catch(e){ return false; } })());
      const items = [["dl","⬇ Download image"],["copy","⧉ Copy image"],["link","🔗 Copy link"],["tab","↗ Open in new tab"]];
      if (canFiles) items.unshift(["share","⤴ Share image (WhatsApp…)"]);
      sm.innerHTML = `<div class="pf-mut" style="font-size:.7rem;letter-spacing:.06em;padding:4px 10px">CHART SNAPSHOT</div>` +
        items.map(([k,l])=>`<button type="button" role="menuitem" data-sn="${k}">${l}</button>`).join("") + `<div class="pf-mut" data-snmsg style="font-size:.75rem;padding:4px 10px;max-width:230px"></div>`;
      const msg = t => { const m = sm.querySelector("[data-snmsg]"); if (m) m.textContent = t; };
      const close = () => { sm.hidden = true; sb.setAttribute("aria-expanded","false"); document.removeEventListener("pointerdown", outside, true); };
      const outside = ev => { if (!sm.contains(ev.target) && ev.target !== sb) close(); };
      sb.onclick = () => { if (!sm.hidden){ close(); return; } sm.hidden = false; sb.setAttribute("aria-expanded","true"); msg(""); document.addEventListener("pointerdown", outside, true); };
      const info = opt.snap || {sym: opt.sym, tf};
      const fname = `${info.sym||"chart"}-${tf==="w"?"weekly":"daily"}-${new Date().toISOString().slice(0,10)}.png`;
      sm.querySelectorAll("[data-sn]").forEach(b=>b.onclick=()=>{
        const k = b.dataset.sn;
        if (k==="link"){ copyText(stockLink(info.sym||"")).then(ok=>msg(ok?"Link copied.":"Couldn't copy the link.")); return; }
        if (k==="copy"){
          if (!(window.ClipboardItem && navigator.clipboard && navigator.clipboard.write)){ msg("This browser can't copy images. Use Download image."); return; }
          // the image is passed as a promise so the browser still treats it as part of the click
          navigator.clipboard.write([new ClipboardItem({"image/png": snapBlob(svg, info, W, H)})])
            .then(()=>msg("Image copied. Paste it in WhatsApp (Ctrl+V)."))
            .catch(()=>msg("Copy blocked by this browser (often on office laptops). Use Download image."));
          return; }
        if (k==="tab"){ const w = window.open("", "_blank");
          snapBlob(svg, info, W, H).then(bl=>{ const u = URL.createObjectURL(bl); if (w) w.location = u; else { saveBlob(bl, fname); msg("Pop-up blocked, so it was downloaded."); } }); return; }
        snapBlob(svg, info, W, H).then(bl=>{
          if (k==="share"){ const f = new File([bl], fname, {type:"image/png"});
            navigator.share({files:[f], title: info.sym}).then(()=>{ close(); }).catch(e=>{ if (!e || e.name!=="AbortError"){ saveBlob(bl, fname); msg("Sharing failed, so it was downloaded."); } }); return; }
          saveBlob(bl, fname); msg("Downloaded."); }).catch(()=>msg("Couldn't make the image."));
      });
    }
    wrap.querySelectorAll("[data-cz]").forEach(b=>b.onclick=()=>{ const t = chOpts(); t["z"+tf] = +b.dataset.cz;
      try { localStorage.setItem(CH_KEY, JSON.stringify(t)); } catch(e){}
      if (opt.redraw) opt.redraw(); else if (dlg && dlg.open) render(); });
    wrap.querySelectorAll("[data-ct]").forEach(b=>b.onclick=()=>{ const t = chOpts(); t[b.dataset.ct] = !t[b.dataset.ct];
      try { localStorage.setItem(CH_KEY, JSON.stringify(t)); } catch(e){}
      if (opt.redraw) opt.redraw(); else if (dlg && dlg.open) render(); });
  }, 0);
  return opt.bare ? html : `<div>${html}</div>`;
}
function saveBlob(bl, name){ const a = document.createElement("a"); a.href = URL.createObjectURL(bl); a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(a.href), 4000); }
// Picture of the chart: the chart's own SVG drawn onto a canvas with a title bar and a footer.
// No page capture, so it is quick and light on memory.
function snapBlob(svg, info, W, H){
  return new Promise((resolve, reject)=>{
    const host = svg.closest(".pf") || document.body, cs = getComputedStyle(host);
    const rv = v => v.replace(/var\((--[\w-]+)(?:,\s*([^)]+))?\)/g, (m, n, fb) => (cs.getPropertyValue(n).trim() || (fb||"").trim() || "#888"));
    const cl = svg.cloneNode(true);
    cl.setAttribute("xmlns", "http://www.w3.org/2000/svg"); cl.setAttribute("width", W); cl.setAttribute("height", H);
    cl.querySelectorAll(".cx").forEach(e=>e.remove());
    [cl, ...cl.querySelectorAll("*")].forEach(e=>{ for (const at of ["fill","stroke","style","stop-color"]){ const v = e.getAttribute(at); if (v && v.includes("var(")) e.setAttribute(at, rv(v)); } });
    const font = cs.fontFamily || "system-ui, sans-serif";
    cl.setAttribute("style", `font-family:${font}`);
    const img = new Image();
    img.onload = () => {
      const lines = (info.lines || []).filter(Boolean), top = 58, foot = 26 + lines.length * 19, S = 2;
      const cv = document.createElement("canvas"); cv.width = W * S; cv.height = (top + H + foot) * S;
      const g = cv.getContext("2d"); g.scale(S, S);
      const bg = getComputedStyle(svg.closest("dialog") || document.body).backgroundColor;
      g.fillStyle = (!bg || bg === "rgba(0, 0, 0, 0)") ? "#ffffff" : bg; g.fillRect(0, 0, W, top + H + foot);
      const ink = cs.getPropertyValue("--ink").trim() || "#16243A", mut = cs.getPropertyValue("--muted").trim() || "#5C6B80";
      g.fillStyle = ink; g.font = `700 20px ${font}`; g.textBaseline = "alphabetic";
      const t1 = `${info.sym || ""}`; g.fillText(t1, 10, 26);
      let x = 18 + g.measureText(t1).width;
      if (info.px != null){ g.font = `600 17px ${font}`; const pt = `₹${Number(info.px).toLocaleString("en-IN",{maximumFractionDigits:2})}`; g.fillText(pt, x, 26); x += 10 + g.measureText(pt).width;
        if (info.r1d != null){ g.fillStyle = info.r1d >= 0 ? (cs.getPropertyValue("--up").trim()||"#1E8F5A") : (cs.getPropertyValue("--down").trim()||"#C2453B");
          g.fillText(`${info.r1d>0?"+":""}${Number(info.r1d).toFixed(2)}%`, x, 26); } }
      g.fillStyle = mut; g.font = `400 13px ${font}`;
      g.fillText(`${info.name ? info.name + " · " : ""}${info.tf==="w"?"Weekly":"Daily"} candles · ${new Date().toLocaleString("en-IN",{day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"})}`, 10, 46);
      g.drawImage(img, 0, top, W, H);
      g.fillStyle = ink; g.font = `500 13px ${font}`;
      lines.forEach((t, i)=>g.fillText(t, 10, top + H + 18 + i * 19));
      g.fillStyle = mut; g.font = `400 11px ${font}`;
      g.fillText("AZHSTK dashboard · for information, not investment advice", 10, top + H + foot - 8);
      cv.toBlob(b => b ? resolve(b) : reject(new Error("blob")), "image/png");
    };
    img.onerror = () => reject(new Error("svg"));
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(cl));
  });
}
const LONG = {}, LONGV = {};
function loadLong(sym){ const k = shard(sym);
  if (!LONG[k]) LONG[k] = fetch(`px/${k}.json`).then(r=>r.ok?r.json():{dates:{},s:{}}).catch(()=>({dates:{},s:{}})).then(j=>{ LONGV[k]=j; return j; });
  return LONG[k]; }
function longData(sym, tf){ const k = shard(sym), j = LONGV[k]; if (!j) return undefined;
  const r = (j.s||{})[sym], d = (j.dates||{})[tf]; if (!r || !r[tf] || !d) return null;
  const [o,h,l,c] = r[tf]; return {o, h, l, c, dates: d}; }
window.AZH_CHART = (z, lv, dates, tf, fb, opt) => chart(z, lv, dates, tf, fb, opt);
window.AZH_STOCK = sym => loadStock(sym);
window.AZH_INDEX = () => loadIndex();

document.addEventListener("click", e => {
  const el = e.target.closest("[data-p]"); if (!el) return;
  e.preventDefault(); e.stopPropagation(); openProfile(el.dataset.p);
}, true);
document.addEventListener("keydown", e => {
  if (e.key==="/" && !/input|textarea|select/i.test(document.activeElement.tagName)){ const i=document.getElementById("gs-in"); if(i){ e.preventDefault(); i.focus(); } }
});
mountSearch();
mountRegime();
(function addScreenerLink(){
  const nav = document.querySelector("header nav"); if (!nav || nav.querySelector('a[href="screener.html"]')) return;
  const a = document.createElement("a"); a.href = "screener.html"; a.textContent = "Screener";
  if (getComputedStyle(nav).display) a.style.cssText = nav.querySelector("a") ? nav.querySelector("a").style.cssText : "";
  const after = nav.querySelector('a[href="setups.html"]') || nav.lastElementChild;
  after ? after.insertAdjacentElement("afterend", a) : nav.appendChild(a);
})();
(function addForwardLink(){
  setTimeout(()=>{ const nav = document.querySelector("header nav"); if (!nav || nav.querySelector('a[href="forward.html"]')) return;
    const a = document.createElement("a"); a.href = "forward.html"; a.textContent = "Forward test";
    if (nav.querySelector("a")) a.style.cssText = nav.querySelector("a").style.cssText;
    const after = nav.querySelector('a[href="buy.html"]') || nav.lastElementChild;
    after ? after.insertAdjacentElement("afterend", a) : nav.appendChild(a); }, 0);
})();
(function addBuyLink(){
  const nav = document.querySelector("header nav"); if (!nav || nav.querySelector('a[href="buy.html"]')) return;
  const a = document.createElement("a"); a.href = "buy.html"; a.textContent = "Buy criteria";
  if (nav.querySelector("a")) a.style.cssText = nav.querySelector("a").style.cssText;
  const after = nav.querySelector('a[href="screener.html"]') || nav.querySelector('a[href="setups.html"]') || nav.lastElementChild;
  after ? after.insertAdjacentElement("afterend", a) : nav.appendChild(a);
})();
(function pwa(){
  const add = (tag, attrs) => { const el = document.createElement(tag); Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v)); document.head.appendChild(el); };
  if (!document.querySelector('link[rel="manifest"]')) add("link", {rel:"manifest", href:"manifest.webmanifest"});
  add("link", {rel:"apple-touch-icon", href:"icon-192.png"});
  add("meta", {name:"apple-mobile-web-app-capable", content:"yes"});
  add("meta", {name:"mobile-web-app-capable", content:"yes"});
  add("meta", {name:"apple-mobile-web-app-title", content:"AZH Stocks"});
  add("meta", {name:"theme-color", content:"#16243A"});
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(()=>{});
})();
const h = decodeURIComponent((location.hash.match(/^#stock=(.+)$/)||[])[1]||""); if (h) openProfile(h);
})();
"""
