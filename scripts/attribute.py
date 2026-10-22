"""Campaign Math engine. Reads what an analyst has (the GA4 event export + the spend table),
applies the four rules exactly as pinned in docs/design-gate.md section 1.5, selects the
verdict branch exactly as pre-registered in docs/verdict-branches.md, and writes
data/results.json.

The attribution and the verdict never read data/truth/. The hygiene ledger does, by design:
v1 is the measurement version, and the seeded defects ARE the ledger's truth.
"""

import csv
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path

import cmlib

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LOOKBACK_S = 90 * 86400


def read_gz(path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def sessionize(rows, names):
    sess = {}
    for r in rows:
        key = (r["user_pseudo_id"], int(r["ga_session_id"]))
        ts = int(r["event_timestamp"])
        s = sess.get(key)
        if s is None:
            s = sess[key] = {"user": key[0], "start": ts, "src": None, "med": None, "camp": None}
        s["start"] = min(s["start"], ts)
        if r["event_name"] == "session_start":
            s["src"], s["med"], s["camp"] = r["source"], r["medium"], r["campaign"]
    for s in sess.values():
        if s["src"] is None:   # no session_start: GA4 reports source / medium (not set)
            s["src"] = s["med"] = s["camp"] = "(not set)"
        s["channel"] = cmlib.channel_group(s["src"], s["med"], s["camp"])
        s["key"] = cmlib.credit_key(s["channel"], s["src"], s["camp"], names)
        c = (s["camp"] or "").strip().lower()
        s["matched"] = names.get(c)   # campaign match regardless of channel (untraced-spend measure)
    return sess


def purchases(rows):
    """Deduped on transaction_id as the GA4 UI does; empty ids count once each."""
    seen, out, raw = set(), [], []
    for r in rows:
        if r["event_name"] != "purchase":
            continue
        p = {"user": r["user_pseudo_id"], "sess": int(r["ga_session_id"]), "ts": int(r["event_timestamp"]),
             "value": float(r["value"]), "txn": r["transaction_id"]}
        raw.append(p)
        if p["txn"]:
            if p["txn"] in seen:
                continue
            seen.add(p["txn"])
        out.append(p)
    return out, raw


def attribute_rows(rows, names):
    rows = [{k: str(v) for k, v in r.items()} for r in rows]
    sess = sessionize(rows, names)
    by_user = {}
    for s in sess.values():
        by_user.setdefault(s["user"], []).append(s)
    for ss in by_user.values():
        ss.sort(key=lambda s: s["start"])
    convs, raw = purchases(rows)
    credit = {r: {} for r in cmlib.RULES}
    credit_n = {r: {} for r in cmlib.RULES}
    paths = []
    for p in convs:
        ts = p["ts"]
        path_s = [s for s in by_user.get(p["user"], []) if ts - LOOKBACK_S * 1_000_000 <= s["start"] <= ts]
        path = [s["key"] for s in path_s if s["key"] != cmlib.DIRECT]
        paths.append((p, path, path_s))
        for rule in cmlib.RULES:
            for k, w in cmlib.split_credit(path, rule).items():
                credit[rule][k] = credit[rule].get(k, 0.0) + w * p["value"]
                credit_n[rule][k] = credit_n[rule].get(k, 0.0) + w
    lc = {k: (round(credit_n["last_click"][k]), credit["last_click"][k]) for k in credit["last_click"]}
    return {"sessions": sess, "convs": convs, "raw_purchases": raw, "paths": paths, "credit": credit,
            "credit_n": credit_n, "last_click_by_campaign": lc}


def main():
    spend = list(csv.DictReader(open(DATA / "spend.csv", encoding="utf-8")))
    names = {r["campaign_name"].strip().lower(): r["campaign_id"] for r in spend}
    names.update({r["campaign_id"].lower(): r["campaign_id"] for r in spend})
    rows = read_gz(DATA / "export" / "events.csv.gz")
    res = attribute_rows(rows, names)
    credit = res["credit"]
    paid = [r for r in spend if float(r["spend"]) > 0]
    paid_ids = [r["campaign_id"] for r in paid]

    # ---- per-campaign table ----
    campaigns = []
    for r in spend:
        cid = r["campaign_id"]
        sp = float(r["spend"])
        rev = {rule: round(credit[rule].get(cid, 0.0), 2) for rule in cmlib.RULES}
        roas = {rule: (round(rev[rule] / sp, 3) if sp else None) for rule in cmlib.RULES}
        matched = sum(1 for s in res["sessions"].values() if s["matched"] == cid)
        clicks = int(r["clicks"])
        untraced = sp * max(0, clicks - matched) / clicks if (sp and clicks) else 0.0
        campaigns.append({"campaign_id": cid, "campaign_name": r["campaign_name"], "platform": r["platform"],
                          "spend": round(sp, 2), "clicks": clicks, "ga4_sessions_matched": matched,
                          "untraced_spend": round(untraced, 2), "revenue": rev, "roas": roas,
                          "platform_conversions": int(r["platform_conversions"]),
                          "platform_conversion_value": float(r["platform_conversion_value"])})
    by_cid = {c["campaign_id"]: c for c in campaigns}

    # ---- ranks / top / verdict legs (docs/verdict-branches.md section 1) ----
    ranks, tops = {}, {}
    for rule in cmlib.RULES:
        order = sorted(paid_ids, key=lambda c: (-by_cid[c]["revenue"][rule], c))
        ranks[rule] = {c: order.index(c) + 1 for c in order}
        best = by_cid[order[0]]["revenue"][rule]
        tops[rule] = sorted(c for c in paid_ids if by_cid[c]["revenue"][rule] == best)
    leg1 = all(tops[r] == tops["last_click"] for r in cmlib.RULES)
    wide = []
    for c in paid_ids:
        vals = [by_cid[c]["roas"][r] for r in cmlib.RULES]
        if min(vals) == 0 or max(vals) / min(vals) >= 1.5:
            wide.append(c)
    leg2 = len(wide) < 3
    tau = cmlib.kendall_tau_b([by_cid[c]["revenue"]["first_click"] for c in paid_ids],
                              [by_cid[c]["revenue"]["last_click"] for c in paid_ids])
    leg3 = tau >= 0.6
    branch = "BANK" if (leg1 and leg2 and leg3) else ("B1" if not leg1 else "B2")

    # ---- pinned measures (docs/verdict-branches.md section 2) ----
    total_rev = sum(p["value"] for p in res["convs"])
    U = sum(c["untraced_spend"] for c in campaigns)
    S = sum(c["spend"] for c in campaigns)
    unattr = [(p, path, ps) for p, path, ps in res["paths"]
              if all(k == cmlib.UNATTRIBUTABLE for k in path)]
    lens = {1: 0.0, 2: 0.0, 3: 0.0}
    for p, path, _ in res["paths"]:
        n = len(path)
        lens[1 if n <= 1 else 2 if n == 2 else 3] += p["value"]
    movers = [c for c in paid_ids if max(ranks[r][c] for r in cmlib.RULES) - min(ranks[r][c] for r in cmlib.RULES) >= 2]
    topk = 3
    every_rule = [c for c in paid_ids if all(ranks[r][c] <= topk for r in cmlib.RULES)]

    buckets = {}
    for rule in cmlib.RULES:
        for k, v in credit[rule].items():
            if k in by_cid:
                continue
            buckets.setdefault(k, {})[rule] = round(v, 2)

    results = {
        "quarter": "2026-Q3",
        "branch": branch,
        "legs": {"leg1_same_top": leg1, "leg2_wide_roas_count": len(wide), "leg2_holds": leg2,
                 "leg3_kendall_tau_b": round(tau, 4), "leg3_holds": leg3},
        "tops": tops, "ranks": ranks, "wide_roas": wide, "movers": movers, "every_rule_top3": every_rule,
        "measures": {
            "U_untraced_spend": round(U, 2), "S_total_spend": round(S, 2),
            "conversions": len(res["convs"]), "revenue": round(total_rev, 2),
            "raw_purchase_events": len(res["raw_purchases"]),
            "unattributable_conversions": len(unattr),
            "s_unattributable_share": round(len(unattr) / len(res["convs"]), 4),
            "d_unattributable_revenue": round(sum(p["value"] for p, _, _ in unattr), 2),
            "p1_one_touch_rev_share": round(lens[1] / total_rev, 4),
            "p2_two_touch_rev_share": round(lens[2] / total_rev, 4),
            "p3_three_plus_rev_share": round(lens[3] / total_rev, 4),
            "n_movers": len(movers), "m_paid": len(paid_ids),
        },
        "campaigns": campaigns,
        "non_campaign_credit": buckets,
        "unattributable_txns": sorted(p["txn"] or f"(no id) {p['user']}@{p['ts']}" for p, _, _ in unattr),
    }
    # One-touch revenue by credit key (tests the B2 "closes most of them" clause)
    one = {}
    for p, path, _ in res["paths"]:
        if len(path) == 1:
            one[path[0]] = one.get(path[0], 0.0) + p["value"]
    one_total = sum(one.values())
    top = tops["last_click"][0]
    one_paid = sum(v for k, v in one.items() if k in paid_ids)
    results["one_touch"] = {"top_campaign": top, "top_share_of_one_touch_rev": round(one.get(top, 0) / one_total, 4),
                            "top_share_of_paid_one_touch_rev": round(one.get(top, 0) / one_paid, 4),
                            "by_key": {k: round(v, 2) for k, v in sorted(one.items(), key=lambda kv: -kv[1])}}
    # {Z}: paid campaign with the widest ROAS max/min ratio (slot rule, DECISIONS 2026-10-22)
    def ratio(c):
        v = [by_cid[c]["roas"][r] for r in cmlib.RULES]
        return float("inf") if min(v) == 0 else max(v) / min(v)
    z = max(paid_ids, key=lambda c: (ratio(c), c))
    zr = [by_cid[z]["roas"][r] for r in cmlib.RULES]
    results["Z"] = {"campaign_id": z, "lo": min(zr), "hi": max(zr), "ratio": round(ratio(z), 3)}
    results["measures"]["t_defect_share_of_unattributable"] = defect_share(unattr)
    results["hygiene"] = hygiene_ledger(res, unattr, campaigns)
    (DATA / "results.json").write_text(json.dumps(results, indent=1, sort_keys=False) + "\n",
                                       encoding="utf-8", newline="\n")
    m = results["measures"]
    print(f"branch={branch} legs={results['legs']}")
    print(f"tops={tops}")
    print(f"U=${m['U_untraced_spend']:,.0f} of S=${m['S_total_spend']:,.0f}; unattributable "
          f"{m['s_unattributable_share']:.1%} (${m['d_unattributable_revenue']:,.0f}); p1/p2/p3="
          f"{m['p1_one_touch_rev_share']:.0%}/{m['p2_two_touch_rev_share']:.0%}/{m['p3_three_plus_rev_share']:.0%}")


TAXONOMY = {
    "A1": ("1", "Missing UTMs", "none published", True),
    "A2a": ("2a", "Case / spelling variants", "none published", False),
    "A2b": ("2b", "Off-spec medium → Unassigned", "none published", True),
    "A3": ("3", "(not set) source", "none published", True),
    "A4a": ("4", "Duplicate purchase sends", "none published", True),
    "A4b": ("4", "Missing transaction_id", "none published", True),
    "A5": ("5", "Payment-gateway self-referral", "none published", True),
    "A6": ("6", "Bot / invalid traffic", "Uber / Frisch", True),
    "A7": ("7", "gclid lost on redirect", "none published", True),
    "A8": ("8", "Safari cookie expiry splits journeys", "none published", True),
    "A9": ("9", "Platform reports more than GA4", "none published", True),
}
RATES = {"A1": "6% of paid-social + email sessions", "A2a": "12% of tagged sessions",
         "A2b": "2% of tagged sessions", "A3": "1% of sessions", "A4a": "3% of purchases",
         "A4b": "0.5% of purchases", "A5": "4% of purchases", "A6": "3% of paid clicks / 1% of other sessions",
         "A7": "2% of Google Ads clicks", "A8": "Safari 30.42% of users × return gaps over 7 days",
         "A9": "+20% over GA4 last-click"}


def defect_share(unattr):
    """{t}: share of unattributable conversions whose true journey carries a seeded defect
    that touched a session (A1, A2a, A2b, A3, A5, A7, A8). Truth side, by design."""
    truth = read_gz(DATA / "truth" / "sessions.csv.gz")
    orders = read_gz(DATA / "truth" / "orders.csv.gz")
    log = read_gz(DATA / "truth" / "seed_log.csv.gz")
    sids_hit = {e["sid"] for e in log if e["class"] in ("A1", "A2a", "A2b", "A3", "A7", "A8")}
    gw = {e["ref"] for e in log if e["class"] == "A5"}
    uid_sids = {}
    for t in truth:
        uid_sids.setdefault(t["uid"], set()).add(t["sid"])
    client_uid = {t["client_id"]: t["uid"] for t in truth}
    by_txn = {o["txn"]: o for o in orders}
    hit = 0
    for p, _, _ in unattr:
        o = by_txn.get(p["txn"])
        uid = o["uid"] if o else client_uid.get(p["user"])
        if (o and o["txn"] in gw) or (uid is not None and uid_sids.get(uid, set()) & sids_hit):
            hit += 1
    return round(hit / len(unattr), 4) if unattr else 0.0


def hygiene_ledger(res, unattr, campaigns):
    """Seed-log ledger (truth side). Revenue metric per docs/verdict-branches.md section 6."""
    truth = {int(r["sid"]): r for r in read_gz(DATA / "truth" / "sessions.csv.gz")}
    orders = read_gz(DATA / "truth" / "orders.csv.gz")
    log = read_gz(DATA / "truth" / "seed_log.csv.gz")
    hit = {}
    for r in log:
        hit.setdefault(r["class"], []).append(r)
    journey = {}
    for sid, t in truth.items():
        journey.setdefault(t["uid"], []).append(sid)
    order_val = {o["txn"]: int(o["value_cents"]) / 100 for o in orders}
    order_uid = {o["txn"]: o["uid"] for o in orders}
    out = []
    for cls, (num, label, case, page) in TAXONOMY.items():
        entries = hit.get(cls, [])
        if cls == "A4a":
            rev = sum(order_val[e["ref"]] for e in entries)
        elif cls == "A9":
            rev = sum(c["platform_conversion_value"] for c in campaigns if c["spend"] > 0) - \
                sum(c["platform_conversion_value"] / 1.2 for c in campaigns if c["spend"] > 0)
        elif cls in ("A4b", "A5"):
            rev = sum(order_val[e["ref"]] for e in entries)
        elif cls == "A6":
            rev = 0.0
        else:
            sids = {int(e["sid"]) for e in entries}
            uids = {truth[s]["uid"] for s in sids if s in truth}
            rev = sum(order_val[t] for t, u in order_uid.items() if u in uids and any(
                int(s) in sids for s in journey.get(u, [])))
        spend_hit = 0.0
        if cls == "A6":
            paid_bots = [e for e in entries if e["detail"] == "paid"]
            cpc = {c["campaign_id"]: (c["spend"] / c["clicks"] if c["clicks"] else 0) for c in campaigns}
            spend_hit = sum(cpc.get(truth[int(e["sid"])]["campaign_id"], 0) for e in paid_bots)
        out.append({"class": cls, "taxonomy": num, "label": label, "documented_case": case,
                    "page_eligible": page, "seeded_at": RATES[cls], "instances": len(entries),
                    "revenue_affected": round(rev, 2), "spend_affected": round(spend_hit, 2)})
    return out


if __name__ == "__main__":
    main()
