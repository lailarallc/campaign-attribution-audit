"""Check the generated universe against the pinned design gate (docs/design-gate.md 2-5).
Reports PASS/FAIL per criterion; never adjusts anything. Writes data/bound_check.json.
"""

import csv
import json
from datetime import datetime
from pathlib import Path

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
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def main():
    sess = read_gz(DATA / "truth" / "sessions.csv.gz")
    orders = read_gz(DATA / "truth" / "orders.csv.gz")
    log = read_gz(DATA / "truth" / "seed_log.csv.gz")
    spend = list(csv.DictReader(open(DATA / "spend.csv", encoding="utf-8")))
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
    pur = [r for r in ev if r["event_name"] == "purchase"]
    missing = sum(1 for r in pur if not r["transaction_id"])
    check("4", "Purchases missing transaction_id", missing, missing == sum(1 for e in log if e["class"] == "A4b"),
          "only A4b")

    # Section 5: realized defect rates
    k = {}
    for e in log:
        k[e["class"]] = k.get(e["class"], 0) + 1
    paid_subs = set(PLATFORM)
    humans_all = [s for s in sess if s["bot"] == "0"]
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
        # tolerance: 3 binomial standard errors (A2a/A2b are conditional on surviving A1, so slightly below)
        check("5", f"Realized rate {c}", round(v, 4), abs(v - t) <= max(0.003, 0.25 * t), f"{t} (+/-25% or 0.3pp)")

    out = {"checks": checks, "pass": sum(c["result"] == "PASS" for c in checks),
           "fail": sum(c["result"] == "FAIL" for c in checks)}
    (DATA / "bound_check.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for c in checks:
        print(f"[{c['result']}] {c['section']} {c['criterion']}: {c['value']}  (target {c['target']})")
    print(f"PASS {out['pass']} / FAIL {out['fail']}")


if __name__ == "__main__":
    main()
