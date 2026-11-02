"""Check the generated universe against the pinned design gate (docs/design-gate.md 2-5).
Reports PASS/FAIL per criterion; never adjusts anything. Writes data/bound_check.json.
"""

import csv
import json
from datetime import datetime
from pathlib import Path

import cmlib
from attribute import read_gz

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TM = {"email": 8.43, "paid_search": 3.95, "paid_social": 3.87, "tiktok": 3.07, "organic_search": 2.02,
      "organic_social": 1.42}
GROUP = {"brand_search": "paid_search", "nonbrand_search": "paid_search", "shopping": "shopping",
         "meta_prospecting": "paid_social", "meta_retargeting": "paid_social", "tiktok": "tiktok",
         "email": "email", "organic_search": "organic_search", "organic_social": "organic_social",
         "direct": "direct", "referral": "referral", "affiliate": "affiliate"}
PLATFORM = {"brand_search": "Google", "nonbrand_search": "Google", "shopping": "Google",
            "meta_prospecting": "Meta", "meta_retargeting": "Meta", "tiktok": "Other paid", "affiliate": "Other paid"}


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")


def main():
    sess = read_gz(DATA / "truth" / "sessions.csv.gz")
    truth_by_sid = {t["sid"]: t for t in sess}
    orders = read_gz(DATA / "truth" / "orders.csv.gz")
    log = read_gz(DATA / "truth" / "seed_log.csv.gz")
    with open(DATA / "spend.csv", encoding="utf-8", newline="") as f:
        daily = list(csv.DictReader(f))
    spend = {}
    for r in daily:
        a = spend.setdefault(r["campaign_id"], {"campaign_id": r["campaign_id"], "platform": r["platform"],
                                                "spend": 0.0, "clicks": 0, "impressions": 0, "pconv": 0})
        a["spend"] += float(r["spend"])
        a["clicks"] += int(r["clicks"])
        a["impressions"] += int(r["impressions"] or 0)
        a["pconv"] += int(r["platform_conversions"])
    spend = list(spend.values())
    results = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    checks = []

    def check(section, name, value, ok, target):
        checks.append({"section": section, "criterion": name, "value": value, "target": target,
                       "result": "PASS" if ok else "FAIL"})

    human_q = [s for s in sess if s["in_quarter"] == "1" and s["bot"] == "0"]
    revenue = sum(int(o["value_cents"]) for o in orders) / 100
    aov = revenue / len(orders)
    cvr = len(orders) / len(human_q)
    check("2", "Online revenue in period (true)", round(revenue), 450_000 <= revenue <= 550_000, "~$500K (+/-10%)")
    check("2", "AOV", round(aov, 2), 80 <= aov <= 120, "$80-120")
    check("2", "Site CVR (true, human sessions)", round(cvr * 100, 2), 1.9 <= cvr * 100 <= 3.0, "1.9-3.0%")
    check("2", "Sessions in quarter (human)", len(human_q), 170_000 <= len(human_q) <= 270_000, "170-270K")
    check("2", "Active campaigns", len(spend), 12 <= len(spend) <= 18, "12-18")

    # Per-channel CVR (true, per session): conversions in sessions of the group / sessions of the group
    sc, cc = {}, {}
    for s in human_q:
        g = GROUP[s["sub"]]
        sc[g] = sc.get(g, 0) + 1
        cc[g] = cc.get(g, 0) + int(s["converts"])
    gcvr = {g: 100 * cc.get(g, 0) / sc[g] for g in sc}
    order = ["email", "paid_search", "paid_social", "organic_search", "organic_social"]
    vals = [gcvr[g] for g in order]
    ok_rank = vals[0] > vals[1] >= vals[2] > vals[3] > vals[4]
    check("3", "CVR ranking email > paid search >= paid social > organic search > organic social",
          {g: round(gcvr[g], 2) for g in order}, ok_rank, "ranking (DIR ThoughtMetric)")
    for g in ["email", "paid_search", "paid_social", "tiktok", "organic_search", "organic_social"]:
        check("3", f"CVR level {g}", round(gcvr[g], 2), 0.5 * TM[g] <= gcvr[g] <= 1.5 * TM[g],
              f"{TM[g]}% +/-50%")

    # True journeys: per order, the user's true sessions up to the purchase
    by_uid = {}
    for s in sess:
        by_uid.setdefault(s["uid"], []).append(s)
    sid_ts = {s["sid"]: ts(s["ts"]) for s in sess}
    email_lin = 0.0
    plat_lin = {}
    long_rev = 0.0
    first_counts, last_counts = {}, {}
    for o in orders:
        t_end = sid_ts[o["sid"]]
        path = sorted((s for s in by_uid[o["uid"]] if sid_ts[s["sid"]] <= t_end), key=lambda s: sid_ts[s["sid"]])
        v = int(o["value_cents"]) / 100
        nd = [s for s in path if s["sub"] != "direct"]
        for s in nd:
            if s["sub"] == "email":
                email_lin += v / len(nd)
            if s["sub"] in PLATFORM:
                plat_lin[PLATFORM[s["sub"]]] = plat_lin.get(PLATFORM[s["sub"]], 0) + v / len(nd)
        days = (sid_ts[path[-1]["sid"]] - sid_ts[path[0]["sid"]]).total_seconds() / 86400
        if len(path) >= 3 and days >= 5:
            long_rev += v
        if len(path) >= 2:
            first_counts[path[0]["sub"]] = first_counts.get(path[0]["sub"], 0) + 1
            last_counts[path[-1]["sub"]] = last_counts.get(path[-1]["sub"], 0) + 1
    check("3", "Email revenue share (true linear)", round(100 * email_lin / revenue, 1),
          9 <= 100 * email_lin / revenue <= 25, "9-25%")
    pspend = {}
    for r in spend:
        pspend[r["platform"]] = pspend.get(r["platform"], 0) + float(r["spend"])
    tot = sum(v for k, v in pspend.items() if k != "Email")
    check("3", "Spend split Google/Meta/Other", {k: round(v / tot, 3) for k, v in pspend.items() if k != "Email"},
          all(abs(pspend[k] / tot - t) < 0.005 for k, t in [("Google", .45), ("Meta", .40), ("Other paid", .15)]),
          "45/40/15")
    for p in ["Google", "Meta", "Other paid"]:
        r = plat_lin.get(p, 0) / pspend[p]
        check("3", f"True ROAS {p} (linear)", round(r, 2), 1.5 <= r <= 6.0, "1.5-6.0")
    check("3", "Revenue from journeys >=3 sessions and >=5 days", round(100 * long_rev / revenue, 1),
          25 <= 100 * long_rev / revenue <= 55, "25-55%")
    multi = sum(first_counts.values())
    disc = ["meta_prospecting", "nonbrand_search", "tiktok"]
    close = ["brand_search", "email", "direct"]
    f_disc = sum(first_counts.get(c, 0) for c in disc) / multi
    l_disc = sum(last_counts.get(c, 0) for c in disc) / multi
    f_close = sum(first_counts.get(c, 0) for c in close) / multi
    l_close = sum(last_counts.get(c, 0) for c in close) / multi
    check("3", "Discovery channels over-represented at first touch", {"first": round(f_disc, 3), "last": round(l_disc, 3)},
          f_disc > l_disc, "first > last (DIR)")
    check("3", "Closers over-represented at last touch", {"first": round(f_close, 3), "last": round(l_close, 3)},
          l_close > f_close, "last > first (DIR)")

    # Section 4: structure on the recorded export
    ev = read_gz(DATA / "export" / "events.csv.gz")
    names = {r["event_name"] for r in ev}
    check("4", "Event names", sorted(names), names <= {"session_start", "first_visit", "page_view", "view_item",
                                                        "add_to_cart", "begin_checkout", "purchase"}, "GA4 ecommerce set")
    cnt = {}
    for r in ev:
        cnt[r["event_name"]] = cnt.get(r["event_name"], 0) + 1
    f = [cnt.get(n, 0) for n in ["view_item", "add_to_cart", "begin_checkout", "purchase"]]
    check("4", "Funnel monotone view_item >= add_to_cart >= begin_checkout >= purchase", f,
          f[0] >= f[1] >= f[2] >= f[3], "monotone")
    # Per-channel funnel (pinned per channel). Seeded A5 gateway-return sessions are excluded:
    # a purchase with no begin_checkout is that defect's real signature (DECISIONS 2026-10-22).
    sess_ch, gw_sessions = {}, set()
    for r in ev:
        if r["event_name"] == "session_start":
            key = (r["user_pseudo_id"], r["ga_session_id"])
            sess_ch[key] = cmlib.channel_group(r["source"], r["medium"], r["campaign"])
            if r["source"] == "paypal.com":
                gw_sessions.add(key)
    fun = {}
    for r in ev:
        key = (r["user_pseudo_id"], r["ga_session_id"])
        if key in gw_sessions or r["event_name"] not in ("view_item", "add_to_cart", "begin_checkout", "purchase"):
            continue
        ch = sess_ch.get(key, "Unassigned")
        fun.setdefault(ch, {}).setdefault(r["event_name"], 0)
        fun[ch][r["event_name"]] += 1
    bad = {ch: [f.get(n, 0) for n in ("view_item", "add_to_cart", "begin_checkout", "purchase")]
           for ch, f in fun.items()}
    bad = {ch: v for ch, v in bad.items() if not (v[0] >= v[1] >= v[2] >= v[3])}
    check("4", "Funnel monotone per channel (excl. seeded A5 returns)", bad or "all monotone", not bad, "monotone")
    # 30-minute session rule: a client's new session starts >= 30 min after its previous event
    last_ev, starts = {}, []
    for r in ev:
        c = r["user_pseudo_id"]
        t = int(r["event_timestamp"])
        if r["event_name"] == "session_start" and c in last_ev:
            starts.append(t - last_ev[c])
        last_ev[c] = max(t, last_ev.get(c, 0))
    short = sum(1 for g in starts if g < 30 * 60 * 1_000_000)
    check("4", "New sessions start >= 30 min after the client's previous event", short, short == 0, "0 violations")
    # History (F2)
    fv = {}
    for r in ev:
        if r["event_name"] == "session_start":
            fv.setdefault(r["campaign"].lower(), [0, 0])[0] += 1
            if r["ga_session_number"] == "1":
                fv[r["campaign"].lower()][1] += 1
    # Retention channels reach only users with history. A first visit there is legitimate only when
    # Safari ITP (A8) minted a new client id for a returning user.
    a8_clients = {truth_by_sid[e["sid"]]["client_id"] for e in log if e["class"] == "A8"}
    for camp in ("qw_meta_rt_cart-abandoners", "qw_email_abandoned-cart", "qw_meta_rt_site-visitors"):
        n, f1 = fv.get(camp, [0, 0])
        stray = sum(1 for r in ev if r["event_name"] == "session_start" and r["campaign"].lower() == camp
                    and r["ga_session_number"] == "1" and r["user_pseudo_id"] not in a8_clients)
        check("4", f"First visits on {camp} not explained by A8 resets", {"first_visit_share": round(f1 / n, 3),
              "unexplained": stray}, stray == 0, "0 unexplained")
    # R1 guard: a client with history at its first exported session must carry a pre-quarter id, and
    # session numbers step by exactly 1 across a client's exported sessions.
    # Keyed on every event, not session_start: A3 deliberately drops session_start.
    per_client = {}
    for r in ev:
        per_client.setdefault(r["user_pseudo_id"], {})[int(r["ga_session_id"])] = int(r["ga_session_number"])
    first_num, minted, steps_bad = {}, {}, 0
    for c, ss in per_client.items():
        nums = [n for _, n in sorted(ss.items())]
        first_num[c], minted[c] = nums[0], int(c.split(".")[1])
        steps_bad += sum(1 for a_, b_ in zip(nums, nums[1:]) if b_ != a_ + 1)
    q_start_epoch = 1782878400   # 2026-07-01 00:00 America/New_York
    r1_bad = sum(1 for c, n in first_num.items() if n > 1 and minted[c] >= q_start_epoch)
    check("4", "History without exported sessions has a pre-quarter client id (R1 guard)", r1_bad, r1_bad == 0, "0")
    check("4", "Session numbers step by 1 across a client's exported sessions", steps_bad, steps_bad == 0, "0")
    buyers = {}
    for o in orders:
        buyers[o["uid"]] = buyers.get(o["uid"], 0) + 1
    rep = sum(1 for v in buyers.values() if v > 1)
    check("4", "Repeat buyers in the quarter", rep, rep > 0, "> 0")
    pur = [r for r in ev if r["event_name"] == "purchase"]
    missing = sum(1 for r in pur if not r["transaction_id"])
    check("4", "Purchases missing transaction_id", missing, missing == sum(1 for e in log if e["class"] == "A4b"),
          "only A4b")

    # Section 5: realized defect rates
    k = {}
    for e in log:
        k[e["class"]] = k.get(e["class"], 0) + 1
    paid_subs = set(PLATFORM)
    humans_all = [s for s in sess if s["bot"] == "0" and s["in_quarter"] == "1"]   # seed log is in-quarter only
    a1_base = sum(1 for s in humans_all if s["sub"] in ("meta_prospecting", "meta_retargeting", "tiktok", "email"))
    tagged = sum(1 for s in humans_all if s["sub"] in ("meta_prospecting", "meta_retargeting", "tiktok", "email", "affiliate"))
    goog = sum(1 for s in humans_all if s["sub"] in ("brand_search", "nonbrand_search", "shopping"))
    paid_h = sum(1 for s in sess if s["sub"] in paid_subs and s["in_quarter"] == "1" and s["bot"] == "0")
    bot_paid = sum(1 for e in log if e["class"] == "A6" and e["detail"] == "paid")
    realized = {
        "A1": (k.get("A1", 0) / a1_base, 0.06), "A2a": (k.get("A2a", 0) / tagged, 0.12),
        "A2b": (k.get("A2b", 0) / tagged, 0.02), "A3": (k.get("A3", 0) / len(humans_all), 0.01),
        "A4a": (k.get("A4a", 0) / len(orders), 0.03), "A4b": (k.get("A4b", 0) / len(orders), 0.005),
        "A5": (k.get("A5", 0) / len(orders), 0.04), "A7": (k.get("A7", 0) / goog, 0.02),
        "A6_paid": (bot_paid / (paid_h + bot_paid), 0.03),
    }
    for c, (v, t) in realized.items():
        # tolerance: 25% of the target or 0.3pp, whichever is larger (A2a/A2b are conditional on surviving A1, so slightly below)
        check("5", f"Realized rate {c}", round(v, 4), abs(v - t) <= max(0.003, 0.25 * t), f"{t} (+/-25% or 0.3pp)")

    paid_rows = [r for r in spend if r["spend"] > 0]
    res_c = {c["campaign_id"]: c for c in results["campaigns"]}
    lc_conv = sum(res_c[r["campaign_id"]]["lc_conversions"] for r in paid_rows)
    ratio = sum(r["pconv"] for r in paid_rows) / lc_conv
    check("5", "A9 platform / GA4 last-click conversions (paid, aggregate)", round(ratio, 4),
          abs(ratio - 1.20) <= 0.01, "1.20 (pinned)")
    per = sorted(round(r["pconv"] / res_c[r["campaign_id"]]["lc_conversions"], 3) for r in paid_rows
                 if res_c[r["campaign_id"]]["lc_conversions"])
    check("5", "A9 multiplier differs by campaign", per, per[-1] - per[0] > 0.05, "not uniform (F5)")
    ctrs = sorted(round(100 * r["clicks"] / r["impressions"], 2) for r in paid_rows if r["impressions"])
    check("5", "CTR differs by campaign type", ctrs, len(set(ctrs)) > 3, "not uniform (F5)")
    out = {"checks": checks, "pass": sum(c["result"] == "PASS" for c in checks),
           "fail": sum(c["result"] == "FAIL" for c in checks)}
    (DATA / "bound_check.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for c in checks:
        print(f"[{c['result']}] {c['section']} {c['criterion']}: {c['value']}  (target {c['target']})")
    print(f"PASS {out['pass']} / FAIL {out['fail']}")


if __name__ == "__main__":
    main()
