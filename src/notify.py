"""WhatsApp (and Telegram) alerts, checked on every dashboard update (every 30 minutes in market hours
and after the close).

Where the alert list comes from (both are read and merged):
  * the GitHub Secret ALERTS (private: nobody else can read it), and/or
  * the file alerts.txt in the repository (public if the repository is public).
One rule per line, "#" starts a comment. See alerts.txt for every rule with examples.

Where messages go (GitHub Secrets, never in the code):
  WhatsApp via CallMeBot: WA_PHONE (e.g. +9665xxxxxxxx) and WA_APIKEY
  Telegram (optional):    TG_TOKEN and TG_CHAT
With neither set, the messages are only printed in the Actions log.

Each alert fires once when its condition becomes true and re-arms when it is false again, so a price
alert does not repeat every 30 minutes. What was sent is kept in data/cache/notify_state.json.
If that file is lost, the first run re-arms everything silently instead of resending old alerts.
"""
import json
import os
import re
import time
import urllib.parse
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from .config import CACHE

STATE = "notify_state.json"
FILE = "alerts.txt"
KEYWORDS = {"cpr", "filter", "quiet", "summary", "timezone", "near", "buy", "stage2", "breadth", "hold"}


# ---------------------------------------------------------------- rules
def _rules_text():
    parts = []
    sec = os.environ.get("ALERTS") or ""
    if sec.strip():
        parts.append(sec)
    for p in (FILE, os.path.join(os.path.dirname(os.path.dirname(__file__)), FILE)):
        try:
            parts.append(open(p, encoding="utf-8").read())
            break
        except Exception:
            pass
    return "\n".join(parts)


def _gh(method, path, token, **kw):
    import requests
    return requests.request(method, "https://api.github.com" + path, timeout=20,
                            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}, **kw)


def alerts_repo():
    """Repository whose issues hold alerts: ALERTS_REPO (e.g. a private repo) or this one."""
    return (os.environ.get("ALERTS_REPO") or os.environ.get("GITHUB_REPOSITORY") or "").strip()


def _issue_rules():
    """Open issues titled "Alert: ..." written by the repository owner. Returns [(line, issue number)]."""
    repo = alerts_repo()
    token = os.environ.get("ALERTS_TOKEN") if os.environ.get("ALERTS_REPO") else os.environ.get("GITHUB_TOKEN")
    token = token or os.environ.get("ALERTS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        return []
    owner = repo.split("/")[0].lower()
    me = (os.environ.get("GITHUB_REPOSITORY_OWNER") or owner).lower()
    out = []
    try:
        for page in range(1, 4):
            r = _gh("GET", f"/repos/{repo}/issues", token, params={"state": "open", "per_page": 100, "page": page})
            if not r.ok:
                print(f"  ! alerts: could not read issues of {repo} ({r.status_code})")
                break
            items = r.json()
            for it in items:
                title = (it.get("title") or "").strip()
                who = ((it.get("user") or {}).get("login") or "").lower()
                if "pull_request" in it or not re.match(r"(?i)alerts?\b", title) or who not in (owner, me):
                    continue                   # only your own "Alert: ..." issues count (anyone can open issues on a public repo)
                body = (it.get("body") or "").split("\n---", 1)[0]
                lines = [x for x in body.splitlines() if x.split("#", 1)[0].strip()]
                if not lines:
                    lines = [re.sub(r"(?i)^alerts?\s*[:\-]?\s*", "", title)]
                out += [(x, it["number"]) for x in lines]
            if len(items) < 100:
                break
    except Exception as e:
        print(f"  ! alerts: issues not read: {str(e)[:100]}")
    return out


def comment(num, text):
    repo = alerts_repo()
    token = os.environ.get("ALERTS_TOKEN") if os.environ.get("ALERTS_REPO") else os.environ.get("GITHUB_TOKEN")
    if not (repo and token and num):
        return
    try:
        _gh("POST", f"/repos/{repo}/issues/{num}/comments", token, json={"body": text})
    except Exception:
        pass


def parse(text, extra=()):
    cfg = {"filter": "60", "quiet": None, "summary": False, "tz": "Asia/Riyadh", "near": 3.0}
    rules, bad = [], []
    for raw, src in [(x, None) for x in text.splitlines()] + list(extra):
        n0 = len(rules)
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        w = line.split()
        lw = [x.lower() for x in w]
        k = lw[0]
        try:
            if k == "filter":
                cfg["filter"] = {"off": "0", "none": "0", "0": "0", "50": "50", "60": "60"}[lw[1].rstrip("%")]
            elif k == "quiet":
                a, b = lw[1].split("-")
                cfg["quiet"] = (a, b)
            elif k == "summary":
                cfg["summary"] = lw[1] in ("on", "yes", "true", "1")
            elif k == "timezone":
                cfg["tz"] = w[1]
            elif k == "near":
                cfg["near"] = float(lw[1].rstrip("%"))
            elif k == "cpr":
                rules.append({"t": "cpr_signals"})
            elif k in ("buy", "stage2"):
                what = lw[1] if len(lw) > 1 else "signals"
                if what not in ("signals", "signal", "exits", "exit"):
                    raise ValueError
                rules.append({"t": k + ("_exits" if what.startswith("exit") else "_signals")})
            elif k == "breadth":
                rules.append({"t": "breadth"})
            elif k == "hold":
                sym, rest = w[1].upper(), lw[2:]
                r = {"t": "hold", "sym": sym, "rule": None, "stop": None, "entry": None}
                i = 0
                while i < len(rest):
                    if rest[i] in ("buy", "stage2"):
                        r["rule"] = rest[i]
                    elif rest[i] == "stop":
                        r["stop"] = float(rest[i + 1]); i += 1
                    elif rest[i] in ("entry", "at", "@"):
                        r["entry"] = float(rest[i + 1]); i += 1
                    else:
                        raise ValueError
                    i += 1
                if not (r["rule"] or r["stop"]):
                    r["rule"] = "buy"
                rules.append(r)
            else:                                   # stock rules: SYM what ...
                sym, what, rest = w[0].upper(), lw[1], lw[2:]
                tf = "w" if "weekly" in rest else "d"
                rest = [x for x in rest if x != "weekly"]
                down = "below" in rest or "down" in rest
                num = next((float(x.rstrip("%x×")) for x in rest if re.fullmatch(r"[\d.]+[%x×]?", x)), None)
                if what in ("above", "below"):
                    rules.append({"t": "price", "sym": sym, "dir": what, "p": float(rest[0])})
                elif what in ("resistance", "breakout"):
                    rules.append({"t": "lvl", "sym": sym, "sig": "Breakout", "tf": tf})
                elif what in ("support", "breakdown"):
                    rules.append({"t": "lvl", "sym": sym, "sig": "Breakdown", "tf": tf})
                elif what == "trendline":
                    rules.append({"t": "lvl", "sym": sym, "sig": "Trendline breakdown" if down else "Trendline breakout", "tf": tf})
                elif what == "near":
                    rules.append({"t": "near", "sym": sym, "tf": tf})
                elif what == "ma":
                    rules.append({"t": "ma", "sym": sym, "n": int(num or 50), "dir": "below" if down else "above"})
                elif what == "move":
                    rules.append({"t": "move", "sym": sym, "x": num or 5.0})
                elif what == "volume":
                    rules.append({"t": "vol", "sym": sym, "x": num or 2.0})
                elif what == "rsi":
                    rules.append({"t": "rsi", "sym": sym, "x": num or (30 if down else 70), "dir": "below" if down else "above"})
                elif what in ("signal", "signals"):
                    rules.append({"t": "signal", "sym": sym})
                else:
                    raise ValueError
        except Exception:
            bad.append(raw.strip() + (f" (issue #{src})" if src else ""))
        if src and len(rules) > n0:
            rules[-1]["src"] = src
    return cfg, rules, bad


# ---------------------------------------------------------------- sending
def _send(text):
    """Returns True if at least one channel accepted the message."""
    import requests
    ok = False
    phone, key = os.environ.get("WA_PHONE"), os.environ.get("WA_APIKEY")
    if phone and key:
        for chunk in _chunks(text, 1200):
            try:
                r = requests.get("https://api.callmebot.com/whatsapp.php",
                                 params={"phone": phone, "text": chunk, "apikey": key}, timeout=30)
                good = r.ok and "error" not in r.text.lower()[:300]
                ok = ok or good
                if not good:
                    print(f"  ! whatsapp: {r.status_code} {re.sub(r'<[^>]+>', ' ', r.text)[:160]}")
            except Exception as e:
                print(f"  ! whatsapp: {str(e).replace(key, '***').replace(phone, '***')[:120]}")
            time.sleep(3)                       # CallMeBot asks for a pause between messages
    tok, chat = os.environ.get("TG_TOKEN"), os.environ.get("TG_CHAT")
    if tok and chat:
        for chunk in _chunks(text, 3800):
            try:
                r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                                  data={"chat_id": chat, "text": chunk, "disable_web_page_preview": "true"}, timeout=30)
                ok = ok or r.ok
                if not r.ok:
                    print(f"  ! telegram: {r.status_code} {r.text[:160]}")
            except Exception as e:
                print(f"  ! telegram: {str(e).replace(tok, '***')[:120]}")
    return ok


def _chunks(text, n):
    out, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > n and cur:
            out.append(cur)
            cur = ""
        cur += line + "\n"
    if cur.strip():
        out.append(cur)
    return out


def configured():
    return bool((os.environ.get("WA_PHONE") and os.environ.get("WA_APIKEY")) or (os.environ.get("TG_TOKEN") and os.environ.get("TG_CHAT")))


# ---------------------------------------------------------------- helpers
def _f(x, d=2):
    try:
        return f"{float(x):,.{d}f}"
    except Exception:
        return "–"


def _rsi(c, n=14):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _in_quiet(q, now):
    if not q:
        return False
    a, b = (datetime.strptime(x, "%H:%M").time() for x in q)
    t = now.time()
    return (a <= t < b) if a < b else (t >= a or t < b)


# ---------------------------------------------------------------- main
def run(px, stocks, ld, lw, by_page, by_rec, tt_page, intraday=False, demo=False):
    try:                                 # tells the stock pop-up where its "Add alert" button should open an issue
        from .config import DOCS
        (DOCS / "alerts_cfg.json").write_text(json.dumps({"repo": alerts_repo() or None}), encoding="utf-8")
    except Exception:
        pass
    text = _rules_text()
    cfg, rules, bad = parse(text, [] if demo else _issue_rules())
    if bad:
        print("  ! alerts: could not read " + "; ".join(bad[:5]))
    if not rules and not cfg["summary"]:
        print("  alerts: no rules (add them to the ALERTS secret or alerts.txt)")
        return
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    base = f"https://{repo.split('/')[0]}.github.io/{repo.split('/')[1]}/" if "/" in repo else ""
    link = lambda s: f"{base}index.html#stock={urllib.parse.quote(s)}" if base else ""
    lk = lambda s: "\n" + link(s) if base else ""
    try:
        now = pd.Timestamp.now(tz=cfg["tz"])
    except Exception:
        now = pd.Timestamp.now(tz="Asia/Riyadh")
    info = {s["sym"]: s for s in stocks}
    C = px["Close"]
    V = px["Volume"] if "Volume" in px else None
    last_day = C.index[-1].strftime("%Y-%m-%d")

    def series(sym):
        t = sym + ".NS"
        return C[t].dropna() if t in C.columns else None

    try:
        state = json.loads((CACHE / STATE).read_text(encoding="utf-8"))
        fresh = False
    except Exception:
        state, fresh = {"on": {}, "sent": {}}, True
    on, sent = state.setdefault("on", {}), state.setdefault("sent", {})
    msgs, commit = [], []              # (key, kind, text) ; kind: "edge" uses `on`, "once" uses `sent`

    cur = {"src": None}

    def edge(key, cond, msg):
        if cond and not on.get(key):
            msgs.append((key, "edge", msg, cur["src"]))
        elif not cond and on.get(key):
            commit.append((key, "off"))

    def once(key, msg):
        if key not in sent:
            msgs.append((key, "once", msg, cur["src"]))

    thr = {"60": 60, "50": 50, "0": None}[cfg["filter"]]
    open_rows = by_page.get("open", []) if cfg["filter"] == "60" else (by_page.get("open_v") or {}).get(cfg["filter"], by_page.get("open", []))
    exits_rows = by_page.get("exits", []) if cfg["filter"] == "60" else (by_page.get("exits_v") or {}).get(cfg["filter"], by_page.get("exits", []))
    mkt = by_page.get("mkt") or {}
    early = (tt_page or {}).get("early") or []
    note_id = " (intraday, confirms at the close)" if intraday else ""

    for r in rules:
        t = r["t"]
        cur["src"] = r.get("src")
        if t == "buy_signals":
            for o in open_rows:
                if o.get("ago") == 0:
                    tag = "forming" if o.get("forming") else "confirmed"
                    once(f"buy:{o['sym']}:{o['sd']}:{tag}",
                         f"🟢 BUY signal ({tag}): {o['sym']} ₹{_f(o['price'])} · stop ₹{_f(o['sl'])} (−{_f(o['risk'], 1)}%) · RS {o.get('rs')}"
                         f"{' · breadth ' + str(int(o['br'])) + '%' if o.get('br') is not None else ''}{lk(o['sym'])}")
        elif t == "buy_exits":
            for x in exits_rows:
                once(f"bx:{x['sym']}:{x['xd']}", f"🔴 Buy criteria EXIT: {x['sym']} at ₹{_f(x['exit'])} ({'+' if (x['r'] or 0) > 0 else ''}{_f(x['r'], 1)}%), entered {x['sd']}{lk(x['sym'])}")
        elif t == "stage2_signals":
            for e in early:
                tr = e.get("tr") or {}
                if tr.get("open") and tr.get("ed") == last_day:
                    once(f"s2:{e['sym']}:{tr['ed']}{':i' if intraday else ''}",
                         f"🟢 Stage 2 start{note_id}: {e['sym']} ₹{_f(e.get('price'))} · RS {e.get('rs')} · exit below ₹{_f(e.get('exit'))}{lk(e['sym'])}")
        elif t == "stage2_exits":
            for e in early:
                tr = e.get("tr") or {}
                if tr.get("xd") == last_day and not intraday:
                    once(f"s2x:{e['sym']}:{tr['xd']}", f"🔴 Stage 2 EXIT: {e['sym']} at ₹{_f(tr.get('xp'))} ({'+' if (tr.get('g') or 0) > 0 else ''}{_f(tr.get('g'), 1)}%) · {tr.get('why') or 'closed below the 50-day MA'}{lk(e['sym'])}")
        elif t == "cpr_signals":
            for x in by_page.get("cpr_trig") or []:
                once(f"cpr:{x['sym']}:{x['k']}:{x['d']}", f"🟢 {x['k']}: {x['sym']} ₹{_f(x['e'])} · stop ₹{_f(x['stop'])} · target ₹{_f(x['tgt'])}{lk(x['sym'])}")
        elif t == "breadth":
            now_b, lim = mkt.get("now"), thr or 60
            if now_b is not None:
                ok = now_b > lim
                prev = state.get("breadth_ok")
                if prev is not None and prev != ok:
                    msgs.append(("breadth_ok", "flag:" + str(ok),
                                 f"{'📈' if ok else '📉'} Market breadth {now_b:.0f}% is now {'above' if ok else 'below'} {lim}%: "
                                 f"{'new Buy criteria entries allowed again' if ok else 'no new Buy criteria entries'}", cur["src"]))
                elif prev is None:
                    commit.append(("breadth_ok", "flag:" + str(ok)))
        elif t == "hold":
            sym = r["sym"]
            c = series(sym)
            if c is None or c.empty:
                once(f"miss:{sym}", f"⚠️ Alert rule for {sym}: symbol not found on the dashboard")
                continue
            p = float(c.iloc[-1])
            gain = f" ({'+' if p >= r['entry'] else ''}{(p / r['entry'] - 1) * 100:.1f}% from ₹{_f(r['entry'])})" if r.get("entry") else ""
            if r.get("stop"):
                edge(f"hstop:{sym}:{r['stop']}", p <= r["stop"], f"🔴 {sym} ₹{_f(p)} hit your stop ₹{_f(r['stop'])}{gain}{lk(sym)}")
                edge(f"hnear:{sym}:{r['stop']}", r["stop"] < p <= r["stop"] * (1 + cfg["near"] / 100),
                     f"⚠️ {sym} ₹{_f(p)} is within {cfg['near']:.0f}% of your stop ₹{_f(r['stop'])}{gain}{lk(sym)}")
            if r["rule"] == "buy":
                b = by_rec.get(sym) or {}
                if b.get("st") in ("new", "open") and b.get("trail"):
                    tr_ = float(b["trail"])
                    edge(f"hbx:{sym}", p < tr_, f"🔴 {sym} ₹{_f(p)} is below its trailing stop ₹{_f(tr_)} ({b.get('trail_kind')}). "
                         f"Buy criteria exit if the week closes below it{gain}{lk(sym)}")
                    edge(f"hbn:{sym}", tr_ <= p <= tr_ * (1 + cfg["near"] / 100),
                         f"⚠️ {sym} ₹{_f(p)} is within {cfg['near']:.0f}% of its trailing stop ₹{_f(tr_)}{gain}{lk(sym)}")
                else:
                    x = next((x for x in by_page.get("exits", []) if x["sym"] == sym), None)
                    if x:
                        once(f"hbe:{sym}:{x['xd']}", f"🔴 {sym}: Buy criteria EXIT week of {x['xd']} at ₹{_f(x['exit'])}{gain}{lk(sym)}")
                    else:
                        once(f"hbnone:{sym}", f"ℹ️ {sym} is not an open Buy criteria trade on the dashboard. Add 'stop <price>' to its hold line to track your own stop.")
            if r["rule"] == "stage2":
                s50 = float(c.rolling(50).mean().iloc[-1]) if len(c) >= 50 else None
                if s50:
                    below = p < s50
                    if intraday:
                        edge(f"h2w:{sym}", below, f"⚠️ {sym} ₹{_f(p)} is below its 50-day MA ₹{_f(s50)}: Stage 2 exit if it closes there{gain}{lk(sym)}")
                    else:
                        edge(f"h2x:{sym}", below, f"🔴 {sym} closed ₹{_f(p)}, below its 50-day MA ₹{_f(s50)}: Stage 2 EXIT{gain}{lk(sym)}")
                    edge(f"h2n:{sym}", s50 <= p <= s50 * (1 + cfg["near"] / 100),
                         f"⚠️ {sym} ₹{_f(p)} is within {cfg['near']:.0f}% of its 50-day MA ₹{_f(s50)}{gain}{lk(sym)}")
                if r.get("entry"):
                    edge(f"h2e:{sym}", p <= r["entry"] * 0.88, f"🔴 {sym} ₹{_f(p)}: 12% emergency stop hit (entry ₹{_f(r['entry'])}){lk(sym)}")
        else:
            sym = r["sym"]
            c = series(sym)
            if c is None or len(c) < 2:
                once(f"miss:{sym}", f"⚠️ Alert rule for {sym}: symbol not found on the dashboard")
                continue
            p, pc = float(c.iloc[-1]), float(c.iloc[-2])
            if t == "price":
                cond = p >= r["p"] if r["dir"] == "above" else p <= r["p"]
                edge(f"px:{sym}:{r['dir']}:{r['p']}", cond, f"🔔 {sym} is {r['dir']} ₹{_f(r['p'])}: now ₹{_f(p)} ({(p / pc - 1) * 100:+.1f}% today){lk(sym)}")
            elif t == "lvl":
                row = (ld if r["tf"] == "d" else lw).get(sym + ".NS") or {}
                hit = r["sig"] in (row.get("sig") or [])
                lvl = (row.get("brk") or {}).get("p") if r["sig"] == "Breakout" else (row.get("bdn") or {}).get("p") if r["sig"] == "Breakdown" else \
                      (row.get("tlr") or {}).get("v") if r["sig"] == "Trendline breakout" else (row.get("tls") or {}).get("v")
                word = {"Breakout": "broke above resistance", "Breakdown": "broke below support",
                        "Trendline breakout": "broke above its falling trendline", "Trendline breakdown": "broke below its rising trendline"}[r["sig"]]
                edge(f"lv:{sym}:{r['sig']}:{r['tf']}", hit, f"{'🟢' if 'above' in word else '🔴'} {sym} {word}{' ₹' + _f(lvl) if lvl else ''} "
                     f"({'weekly' if r['tf'] == 'w' else 'daily'}{', intraday' if intraday else ''}): now ₹{_f(p)}{lk(sym)}")
            elif t == "near":
                row = (ld if r["tf"] == "d" else lw).get(sym + ".NS") or {}
                for sg_, lab, key in (("Near resistance", "is near resistance", "res"), ("Near support", "is near support", "sup"),
                                      ("At trendline support", "is at its rising trendline", "tls")):
                    hit = sg_ in (row.get("sig") or [])
                    lv_ = (row.get(key) or {}).get("p") or (row.get(key) or {}).get("v")
                    edge(f"nr:{sym}:{sg_}:{r['tf']}", hit, f"👀 {sym} {lab}{' ₹' + _f(lv_) if lv_ else ''}: now ₹{_f(p)}{lk(sym)}")
            elif t == "ma":
                if len(c) >= r["n"]:
                    ma = float(c.rolling(r["n"]).mean().iloc[-1])
                    cond = p > ma if r["dir"] == "above" else p < ma
                    edge(f"ma:{sym}:{r['n']}:{r['dir']}", cond, f"🔔 {sym} crossed {r['dir']} its {r['n']}-day MA ₹{_f(ma)}: now ₹{_f(p)}{lk(sym)}")
            elif t == "move":
                ch = (p / pc - 1) * 100
                edge(f"mv:{sym}:{r['x']}:{last_day}", abs(ch) >= r["x"], f"{'🚀' if ch > 0 else '⬇️'} {sym} {ch:+.1f}% today: ₹{_f(p)}{lk(sym)}")
            elif t == "vol" and V is not None and sym + ".NS" in V.columns:
                v = V[sym + ".NS"].dropna()
                if len(v) > 21:
                    x = float(v.iloc[-1]) / float(v.iloc[-21:-1].mean() or np.nan)
                    edge(f"vo:{sym}:{r['x']}:{last_day}", np.isfinite(x) and x >= r["x"],
                         f"📊 {sym} volume {x:.1f}× its 20-day average today: ₹{_f(p)} ({(p / pc - 1) * 100:+.1f}%){lk(sym)}")
            elif t == "rsi":
                rv = float(_rsi(c).iloc[-1])
                cond = rv >= r["x"] if r["dir"] == "above" else rv <= r["x"]
                edge(f"rsi:{sym}:{r['x']}:{r['dir']}", cond, f"🔔 {sym} RSI {rv:.0f} is {r['dir']} {r['x']:.0f}: ₹{_f(p)}{lk(sym)}")
            elif t == "signal":
                b = by_rec.get(sym) or {}
                if b.get("st") == "new":
                    once(f"sig:by:{sym}:{b.get('sd')}", f"🟢 {sym}: Buy criteria signal (week of {b.get('sd')}) at ₹{_f(b.get('entry'))}, stop ₹{_f(b.get('sl'))}{lk(sym)}")
                e = next((e for e in early if e["sym"] == sym and (e.get("tr") or {}).get("open") and e["tr"].get("ed") == last_day), None)
                if e:
                    once(f"sig:s2:{sym}:{last_day}{':i' if intraday else ''}", f"🟢 {sym}: Stage 2 start{note_id} at ₹{_f(e.get('price'))}{lk(sym)}")
                row = ld.get(sym + ".NS") or {}
                for sg_ in ("Breakout", "Trendline breakout", "Breakdown", "Trendline breakdown"):
                    edge(f"sig:lv:{sym}:{sg_}", sg_ in (row.get("sig") or []), f"{'🔴' if 'down' in sg_ else '🟢'} {sym}: {sg_} (daily levels): ₹{_f(p)}{lk(sym)}")

    # daily summary after the close
    if cfg["summary"] and not intraday:
        key = f"summary:{last_day}"
        if key not in sent:
            lines = [f"📋 AZHSTK summary {last_day}",
                     f"Breadth {mkt.get('now', '–')}% ({'entries allowed' if (thr is None or (mkt.get('now') or 0) > thr) else 'no new Buy criteria entries'}, filter {'off' if thr is None else str(thr) + '%'})"]
            new_b = [o for o in open_rows if o.get("ago") == 0]
            if new_b:
                lines.append("Buy signals this week: " + ", ".join(f"{o['sym']} ₹{_f(o['price'], 0)}" for o in new_b[:12]))
            new_s = [e for e in early if (e.get("tr") or {}).get("open") and e["tr"].get("ed") == last_day]
            if new_s:
                lines.append("Stage 2 starts today: " + ", ".join(f"{e['sym']} ₹{_f(e.get('price'), 0)}" for e in new_s[:12]))
            for r in rules:
                if r["t"] == "hold":
                    c = series(r["sym"])
                    if c is None or c.empty:
                        continue
                    p = float(c.iloc[-1])
                    bits = [f"{r['sym']} ₹{_f(p)}"]
                    if r.get("entry"):
                        bits.append(f"{(p / r['entry'] - 1) * 100:+.1f}%")
                    b = by_rec.get(r["sym"]) or {}
                    if r["rule"] == "buy" and b.get("trail"):
                        bits.append(f"trail ₹{_f(b['trail'])} ({(p / float(b['trail']) - 1) * 100:.1f}% above)")
                    if r["rule"] == "stage2" and len(c) >= 50:
                        s50 = float(c.rolling(50).mean().iloc[-1])
                        bits.append(f"50-DMA ₹{_f(s50)} ({(p / s50 - 1) * 100:+.1f}%)")
                    if r.get("stop"):
                        bits.append(f"stop ₹{_f(r['stop'])}")
                    lines.append("• " + " · ".join(bits))
            msgs.append((key, "once", "\n".join(lines), None))

    # ---------- deliver ----------
    if fresh and not demo:
        for key, kind, *_ in msgs:
            if kind == "edge":
                on[key] = True
            elif kind.startswith("flag:"):
                state[key] = kind == "flag:True"
            elif not key.startswith("summary:"):
                sent[key] = last_day
        for key, kind in commit:
            if kind.startswith("flag:"):
                state[key] = kind == "flag:True"
        msgs = [m for m in msgs if m[0].startswith("summary:")]
        print("  alerts: first run (no saved state), armed silently")
    for key, kind in commit:
        if kind == "off":
            on.pop(key, None)
        elif kind.startswith("flag:"):
            state[key] = kind == "flag:True"
    if msgs:
        body = "\n\n".join(m[2] for m in msgs)
        if demo or not configured():
            print(f"  alerts: {len(msgs)} message(s) (not sent: {'demo' if demo else 'no WA_PHONE/WA_APIKEY or TG_TOKEN/TG_CHAT secrets'}):")
            for m in msgs[:20]:
                print("    " + m[2].replace("\n", " | "))
        elif _in_quiet(cfg["quiet"], now):
            print(f"  alerts: {len(msgs)} held back (quiet hours)")
            msgs = []
        elif _send(body):
            print(f"  alerts: sent {len(msgs)}")
            for m in msgs:                      # note it on the alert's issue, so each issue keeps its own history
                if m[3]:
                    comment(m[3], f"🔔 Sent {now:%d %b %Y %H:%M}: " + m[2].split("\n")[0])
        else:
            print(f"  ! alerts: sending failed, will retry next run")
            msgs = []
        if not demo and configured():
            for key, kind, *_ in msgs:
                if kind == "edge":
                    on[key] = True
                elif kind.startswith("flag:"):
                    state[key] = kind == "flag:True"
                else:
                    sent[key] = last_day
    else:
        print(f"  alerts: {len(rules)} rule(s) checked, nothing new")
    # forget one-off keys after 60 days
    cut = (pd.Timestamp(last_day) - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
    state["sent"] = {k: v for k, v in sent.items() if not isinstance(v, str) or v >= cut}
    if not demo:
        try:
            CACHE.mkdir(parents=True, exist_ok=True)
            (CACHE / STATE).write_text(json.dumps(state), encoding="utf-8")
        except Exception as e:
            print(f"  ! alerts state not saved: {str(e)[:80]}")
