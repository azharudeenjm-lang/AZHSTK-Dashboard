"""CPR + Camarilla (weekly and monthly levels), traded on daily prices. Long trades only.

Levels for a week (or month) come from the previous week's (month's) high H, low L and close C:
  CPR:  pivot P = (H+L+C)/3, BC = (H+L)/2, TC = 2P - BC; width = |TC-BC| / P (narrow = quiet period before)
  Camarilla (R = H-L):  H3 = C + 1.1R/4   H4 = C + 1.1R/2   H5 = C x H/L
                        L3 = C - 1.1R/4   L4 = C - 1.1R/2
Breakout: the period opens between H3 and H4; buy when price goes above H4; stop H3; target H5.
          (If price falls below H3 before reaching H4, the setup has failed.)
Reversal: price dips below L3 and closes back above it (without touching L4 first): buy that close;
          stop L4; target H3.
A trade still open when the period ends is closed at that period's last close.

Tested on the dashboard's prices (Oct 2024 - Oct 2026, 1,506 liquid stocks, 0.15% costs):
  weekly breakout  +0.56% per trade (2,973 trades); with RS 80+  +0.78% (384), both years positive
  monthly reversal  -0.63% overall, but +1.00% when market breadth is above 60% (3,252), both years positive
  monthly breakout +2.4% (103 trades: too few to rely on); weekly reversal about 0
  A narrow CPR did not help; breakouts without the "opened between H3 and H4" condition lost money.
"""
import json

import numpy as np
import pandas as pd

from .config import DOCS

COST = 0.15
META = [
    ("cpr_wb_set", "CPR weekly: opened between H3 and H4, waiting for a break above H4", "s"),
    ("cpr_wb_go", "CPR weekly: broke above H4 after opening between H3 and H4 (breakout entry)", "e"),
    ("cpr_wr_go", "CPR weekly: dipped below L3 and closed back above it (reversal entry)", "e"),
    ("cpr_mb_set", "CPR monthly: opened between H3 and H4, waiting for a break above H4", "s"),
    ("cpr_mb_go", "CPR monthly: broke above H4 after opening between H3 and H4 (breakout entry)", "e"),
    ("cpr_mr_go", "CPR monthly: dipped below L3 and closed back above it (reversal entry)", "e"),
    ("cpr_w_narrow", "CPR weekly: narrow CPR (under 1%)", "s"),
    ("cpr_w_up", "CPR weekly: price above H4 now", "s"),
    ("cpr_w_rise", "CPR weekly: CPR higher than last week's (rising value)", "s"),
]


def _r(x, n=2):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def _levels(O, H, L, C, freq):
    idx = C.index
    g = idx.to_period(freq).astype(str).to_numpy()
    keys = list(dict.fromkeys(g))
    ph = H.groupby(g).max().reindex(keys)
    pl = L.groupby(g).min().reindex(keys)
    pc = C.groupby(g).last().reindex(keys)
    po = O.groupby(g).first().reindex(keys)
    Hp, Lp, Cp = ph.shift(1), pl.shift(1), pc.shift(1)
    P = (Hp + Lp + Cp) / 3
    BC = (Hp + Lp) / 2
    TC = 2 * P - BC
    R = Hp - Lp
    lv = {"H3": Cp + 1.1 * R / 4, "H4": Cp + 1.1 * R / 2, "L3": Cp - 1.1 * R / 4, "L4": Cp - 1.1 * R / 2,
          "H5": Cp * Hp / Lp, "P": P, "w": (TC - BC).abs() / P * 100, "op": po}
    lv = {k: v.to_numpy(float) for k, v in lv.items()}
    pos = {k: i for i, k in enumerate(keys)}
    pid = np.array([pos[x] for x in g])
    starts = [int(np.argmax(pid == p)) for p in range(len(keys))]
    return lv, pid, starts, keys


def _simulate(j, p, s, e_, setup, lv, Ov, Hv, Lv, Cv):
    """One period of one stock. Returns (trade dict or None, status dict for the screener)."""
    h3, h4, h5, l3, l4, op = (lv[k][p, j] for k in ("H3", "H4", "H5", "L3", "L4", "op"))
    st = {"st": None}
    if not (np.isfinite(h4) and np.isfinite(op)):
        return None, st
    entry = ei = None
    if setup == "b":
        oz = h3 <= op < h4
        for i in range(s, e_):
            if not np.isfinite(Hv[i, j]):
                continue
            if oz and Lv[i, j] <= h3 and Hv[i, j] < h4:
                st = {"st": "failed", "i": i}
                break
            if Hv[i, j] >= h4:
                entry, ei = (max(Ov[i, j], h4) if np.isfinite(Ov[i, j]) else h4), i
                break
        stop, tgt = h3, h5
    else:
        oz = l3 < op < h3 or l4 < op <= l3
        dipped = False
        for i in range(s, e_):
            if not np.isfinite(Lv[i, j]):
                continue
            if Lv[i, j] <= l4:
                st = {"st": "failed", "i": i}
                break
            if Lv[i, j] < l3:
                dipped = True
                if Cv[i, j] > l3:
                    entry, ei = Cv[i, j], i
                    break
        if entry is None and dipped and st["st"] is None:
            st = {"st": "below"}
        stop, tgt = l4, h3
    if entry is None:
        if st["st"] is None:
            st = {"st": "waiting"}
        st["oz"] = bool(oz)
        return None, st
    xp = why = None
    k = ei
    for k in range(ei, e_):
        if not np.isfinite(Cv[k, j]):
            continue
        if k == ei:
            if setup == "b" and Cv[k, j] <= stop:          # closed back below the stop on the entry day
                xp, why = stop, "Stop (H3)"
                break
            if setup == "b" and Hv[k, j] >= tgt and Cv[k, j] >= tgt * 0.995:
                xp, why = tgt, "Target (H5)"
                break
            continue
        if Lv[k, j] <= stop:
            xp, why = (min(Ov[k, j], stop) if np.isfinite(Ov[k, j]) else stop), "Stop (H3)" if setup == "b" else "Stop (L4)"
            break
        if Hv[k, j] >= tgt:
            xp, why = (max(Ov[k, j], tgt) if np.isfinite(Ov[k, j]) else tgt), "Target (H5)" if setup == "b" else "Target (H3)"
            break
    tr = {"ei": ei, "e": entry, "stop": stop, "tgt": tgt, "oz": bool(oz)}
    if xp is not None:
        tr.update(xp=xp, xi=k, why=why)
    else:
        last = e_ - 1
        while last > ei and not np.isfinite(Cv[last, j]):
            last -= 1
        tr.update(xp=Cv[last, j], xi=last, why=None)      # closed at period end (or still running)
    return tr, {"st": "entered", "i": ei, "oz": bool(oz)}


def build(px, stocks, today=None):
    info = {s["sym"]: s for s in stocks}
    cols = [s["sym"] + ".NS" for s in stocks if s.get("liquid") and s["sym"] + ".NS" in px["Close"].columns]
    C = px["Close"][cols].ffill(limit=3)
    H, L = px["High"][cols].fillna(C), px["Low"][cols].fillna(C)
    O = (px["Open"][cols] if "Open" in px else C).fillna(C)
    idx = C.index
    n = len(idx)
    today = pd.Timestamp(today or pd.Timestamp.now(tz="Asia/Kolkata").date())
    since = (today - pd.Timedelta(days=730)).strftime("%Y-%m-%d")
    rs = ((C / C.shift(126) - 1).rank(axis=1, pct=True) * 100).to_numpy(float)     # 6-month return rank (as tested)
    s50 = C.rolling(50, min_periods=45).mean().to_numpy(float)
    Ov, Hv, Lv, Cv = (x.to_numpy(float) for x in (O, H, L, C))
    brd = np.nansum(Cv > s50, axis=1) / np.maximum(np.isfinite(s50).sum(axis=1), 1) * 100
    ds = [d.strftime("%Y-%m-%d") for d in idx]
    logs, now, sc = {}, {}, {}
    for freq, tf in (("W", "w"), ("M", "m")):
        lv, pid, starts, keys = _levels(O, H, L, C, freq)
        np_ = len(starts)
        for setup in ("b", "r"):
            key = tf + setup
            rows = []
            for j in range(len(cols)):
                for p in range(1, np_):
                    s = starts[p]
                    e_ = starts[p + 1] if p + 1 < np_ else n
                    if s == 0:
                        continue
                    tr, st = _simulate(j, p, s, e_, setup, lv, Ov, Hv, Lv, Cv)
                    if p == np_ - 1:                  # current period: remember the status for the screener
                        now.setdefault(cols[j], {})[key] = (st, tr)
                    if tr is None or ds[tr["ei"]] < since:
                        continue
                    k0 = s - 1                        # filters as of the day before the period
                    r = (tr["xp"] / tr["e"] - 1) * 100 - COST
                    done = tr["why"] is not None or p < np_ - 1
                    # [sym, entry date, entry, exit date (None = running), exit/now, gain %, reason, days,
                    #  stop, target, opened H3-H4 (b) / opened inside (r), RS, above 50-DMA, breadth %, CPR width %]
                    rows.append([cols[j][:-3], ds[tr["ei"]], _r(tr["e"]), ds[tr["xi"]] if done else None, _r(tr["xp"]), _r(r, 2),
                                 tr["why"] or ("Period end" if done else None), int(tr["xi"] - tr["ei"]),
                                 _r(tr["stop"]), _r(tr["tgt"]), tr["oz"], _r(rs[k0, j], 0),
                                 bool(Cv[k0, j] > s50[k0, j]) if np.isfinite(s50[k0, j]) else None, _r(brd[k0], 0), _r(lv["w"][p, j], 2)])
            logs[key] = rows
        # the screener: every liquid stock against this period's levels
        p = np_ - 1
        s = starts[p]
        prev_p = p - 1
        for j, t in enumerate(cols):
            c = Cv[-1, j]
            if not np.isfinite(c) or not np.isfinite(lv["H4"][p, j]):
                continue
            g = lambda k: lv[k][p, j]
            zone = lambda x: ">H4" if x >= g("H4") else "H3-H4" if x >= g("H3") else "L3-H3" if x > g("L3") else "L4-L3" if x > g("L4") else "<L4"
            rise = None
            if np.isfinite(lv["P"][prev_p, j]):
                rise = "higher" if g("P") > lv["P"][prev_p, j] * 1.002 else "lower" if g("P") < lv["P"][prev_p, j] * 0.998 else "same"
            row = {"zo": zone(g("op")), "zn": zone(c), "w": _r(g("w"), 2), "rise": rise,
                   **{k.lower(): _r(g(k)) for k in ("H3", "H4", "H5", "L3", "L4")}}
            for setup in ("b", "r"):
                st, tr = now.get(t, {}).get(tf + setup, ({"st": None}, None))
                d = {"st": st.get("st"), "oz": st.get("oz")}
                if st.get("i") is not None:
                    d["ago"] = int(n - 1 - st["i"])
                if tr:
                    d.update(e=_r(tr["e"]), g=_r(((tr["xp"] if tr["why"] else c) / tr["e"] - 1) * 100, 1), x=tr["why"])
                row[setup] = d
            now[t][tf] = row
    # rows for the page
    out_rows = []
    for j, t in enumerate(cols):
        x = now.get(t) or {}
        if "w" not in x:
            continue
        out_rows.append({"sym": t[:-3], "name": info[t[:-3]]["name"], "sector": info[t[:-3]].get("sector"), "price": _r(Cv[-1, j]),
                         "rs": _r(rs[-1, j], 0), "up": bool(Cv[-1, j] > s50[-1, j]) if np.isfinite(s50[-1, j]) else None,
                         "w": x.get("w"), "m": x.get("m")})
        # screener conditions (state = 1; entry events = trading days ago)
        c_ = {}
        for tf in ("w", "m"):
            z = x.get(tf) or {}
            b, r = z.get("b") or {}, z.get("r") or {}
            if b.get("st") == "waiting" and b.get("oz"):
                c_[f"cpr_{tf}b_set"] = 1
            if b.get("st") == "entered" and b.get("oz") and b.get("ago") is not None and b.get("ago") < 10:
                c_[f"cpr_{tf}b_go"] = b["ago"]
            if r.get("st") == "entered" and r.get("ago") is not None and r.get("ago") < 10:
                c_[f"cpr_{tf}r_go"] = r["ago"]
        w = x.get("w") or {}
        if w.get("w") is not None and w["w"] < 1:
            c_["cpr_w_narrow"] = 1
        if w.get("zn") == ">H4":
            c_["cpr_w_up"] = 1
        if w.get("rise") == "higher":
            c_["cpr_w_rise"] = 1
        if c_:
            sc[t] = c_
    # stats for every filter combination (the page's switches), from the full 2-year logs
    stats = {}
    for key, rows in logs.items():
        for oz in ((1, 0) if key[1] == "b" else (0,)):
            for rmin in (0, 70, 80, 90):
                for bmin in (0, 50, 60):
                    for up in (0, 1):
                        for nw in (0, 2, 1):
                            sel = [x for x in rows if x[3] and (not oz or x[10]) and (x[11] or 0) >= rmin and (not bmin or (x[13] or 0) > bmin)
                                   and (not up or x[12]) and (not nw or (x[14] is not None and x[14] < nw))]
                            if not sel:
                                continue
                            r = np.array([x[5] for x in sel])
                            yr = lambda a, b: [x[5] for x in sel if a <= x[1] < b]
                            mid = (pd.Timestamp(since) + pd.Timedelta(days=365)).strftime("%Y-%m-%d")
                            y1, y2 = yr(since, mid), yr(mid, "9999")
                            w, lo = r[r > 0], r[r <= 0]
                            stats[f"{key}|{oz}|{rmin}|{bmin}|{up}|{nw}"] = [
                                len(r), _r(len(w) / len(r) * 100, 0), _r(r.mean(), 2), _r(w.mean() if len(w) else 0, 1),
                                _r(lo.mean() if len(lo) else 0, 1), _r(np.mean(y1), 2) if y1 else None, _r(np.mean(y2), 2) if y2 else None,
                                _r(float(np.median([x[7] for x in sel])), 0), len(y1), len(y2)]
    # trade lists kept on the page: the breakouts that opened between H3 and H4 (the tested rule), the monthly
    # reversals in strong markets (breadth > 60%), and everything from the last 3 months
    cut3 = (today - pd.Timedelta(days=91)).strftime("%Y-%m-%d")
    keep = {"wb": lambda x: x[10], "mb": lambda x: x[10], "mr": lambda x: (x[13] or 0) > 60 or x[1] >= cut3,
            "wr": lambda x: x[1] >= cut3}
    logs = {k: [x for x in v if keep[k](x) and (k[1] != "b" or x[10])] for k, v in logs.items()}
    names = {r_[0]: [info[r_[0]]["name"], info[r_[0]].get("sector")] for L_ in logs.values() for r_ in L_}
    page = {"generated": pd.Timestamp.now(tz="Asia/Kolkata").strftime("%d %b %Y, %I:%M %p IST"), "since": since, "cut3": cut3,
            "asof": ds[-1], "breadth": _r(brd[-1], 0), "rows": out_rows, "logs": logs, "names": names, "stats": stats}
    try:
        DOCS.mkdir(parents=True, exist_ok=True)
        (DOCS / "cpr.json").write_text(json.dumps(page, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    except Exception as e:
        print(f"  ! cpr.json not written: {str(e)[:80]}")
    # new entries today for alerts: weekly breakout with RS 80+, monthly reversal with breadth > 60%
    trig = []
    for r_ in out_rows:
        wb = (r_["w"] or {}).get("b") or {}
        mr = (r_["m"] or {}).get("r") or {}
        if wb.get("st") == "entered" and wb.get("oz") and wb.get("ago") == 0 and (r_["rs"] or 0) >= 80:
            trig.append({"sym": r_["sym"], "k": "Weekly CPR breakout above H4", "e": wb.get("e"), "stop": r_["w"]["h3"], "tgt": r_["w"]["h5"], "d": ds[-1]})
        if mr.get("st") == "entered" and mr.get("ago") == 0 and (brd[-1] or 0) > 60:
            trig.append({"sym": r_["sym"], "k": "Monthly CPR reversal at L3", "e": mr.get("e"), "stop": r_["m"]["l4"], "tgt": r_["m"]["h3"], "d": ds[-1]})
    return {"n": {k: len(v) for k, v in logs.items()}, "rows": len(out_rows), "trig": trig}, sc
