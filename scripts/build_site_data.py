"""Fill the pre-registered copy slots (docs/verdict-branches.md) and the page tables from
data/results.json. Output: src/lib/site.json (imported by the static site at build time).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = json.loads((ROOT / "data" / "results.json").read_text(encoding="utf-8"))
MAN = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
RULES = ["last_click", "first_click", "linear", "position_based"]
RULE_LABEL = {"last_click": "Last-click", "first_click": "First-click", "linear": "Linear",
              "position_based": "Position-based"}


def main():
    m = R["measures"]
    camps = {c["campaign_id"]: c for c in R["campaigns"]}
    paid = [c for c in R["campaigns"] if c["spend"] > 0]
    name = lambda cid: camps[cid]["campaign_name"]
    x = R["tops"]["last_click"][0]

    rows = []
    for c in sorted(paid, key=lambda c: R["ranks"]["last_click"][c["campaign_id"]]):
        cid = c["campaign_id"]
        rev = [c["revenue"][r] for r in RULES]
        roas = [c["roas"][r] for r in RULES]
        ranks = [R["ranks"][r][cid] for r in RULES]
        rows.append({
            "id": cid, "name": c["campaign_name"], "platform": c["platform"], "spend": c["spend"],
            "revenue": dict(zip(RULES, rev)), "roas": dict(zip(RULES, roas)), "ranks": dict(zip(RULES, ranks)),
            "rev_lo": min(rev), "rev_hi": max(rev), "roas_lo": min(roas), "roas_hi": max(roas),
            "rank_lo": min(ranks), "rank_hi": max(ranks),
            "every_rule_top3": cid in R["every_rule_top3"],
            "rule_dependent": cid in R["movers"] or cid in R["wide_roas"],
            "clicks": c["clicks"], "matched": c["ga4_sessions_matched"], "untraced": c["untraced_spend"],
            "platform_conversions": c["platform_conversions"], "platform_value": c["platform_conversion_value"],
        })
    email = [{"id": c["campaign_id"], "name": c["campaign_name"], "revenue": c["revenue"]}
             for c in R["campaigns"] if c["platform"] == "Email"]
    buckets = []
    labels = {"Direct": "Direct (no tracked source)", "Unattributable": "Unassigned, (not set), unmatched",
              "channel:Organic Search": "Organic search", "channel:Referral": "Referral (incl. payment gateway)",
              "channel:Organic Social": "Organic social"}
    for k, v in R["non_campaign_credit"].items():
        buckets.append({"key": k, "label": labels.get(k, k.replace("channel:", "")), "revenue": v})

    hyg = [h for h in R["hygiene"]]
    eligible = sorted([h for h in hyg if h["page_eligible"]], key=lambda h: (-h["revenue_affected"], h["class"]))
    footnote = [h for h in hyg if not h["page_eligible"]]

    # The B2 clause "among paid campaigns, {X} takes the largest share" must be true to print.
    if R["branch"] == "B2" and not R["one_touch"]["top_is_largest_paid"]:
        raise SystemExit("B2 clause false: X is not the largest paid campaign in one-visit sales")
    # The headline unattributable figure and the last-click bucket figures must reconcile (Max audit #3).
    lc_direct = R["non_campaign_credit"]["Direct"]["last_click"]
    assert abs(lc_direct - m["d_direct_only_revenue"]) < 0.01, "Direct bucket != Direct-only paths"
    assert abs(m["d_direct_only_revenue"] + m["d_unattributable_touch_revenue"] - m["d_unattributable_revenue"]) < 0.01
    site = {
        "quarter_label": "Q3 2026 (July 1 – September 30)",
        "branch": R["branch"],
        "legs": R["legs"],
        "lead": {"U": m["U_untraced_spend"], "S": m["S_total_spend"]},
        "X": name(x),
        "tops": {r: [name(c) for c in R["tops"][r]] for r in RULES},
        "n": m["n_movers"], "m": m["m_paid"],
        "Z": {"name": name(R["Z"]["campaign_id"]), "lo": R["Z"]["lo"], "hi": R["Z"]["hi"]},
        "p1": m["p1_one_touch_rev_share"], "p2": m["p2_two_touch_rev_share"], "p3": m["p3_three_plus_rev_share"],
        "share": R["one_touch"]["top_share_of_one_visit_rev"],
        "u": m["u_split_share_of_multivisit"],
        "every_rule": [name(c) for c in R["every_rule_top3"]], "k": 3,
        "s": m["s_unattributable_share"], "d": m["d_unattributable_revenue"],
        "d_direct_only": m["d_direct_only_revenue"], "d_unattr_touch": m["d_unattributable_touch_revenue"],
        "lc_unattr": R["non_campaign_credit"]["Unattributable"]["last_click"],
        "t": m["t_defect_share_of_unattributable"],
        "conversions": m["conversions"], "revenue": m["revenue"], "raw_purchase_events": m["raw_purchase_events"],
        "orders_generated": MAN["orders"], "events": MAN["events"], "sessions": MAN["sessions_in_quarter"],
        "manifest_sha_events": MAN["files"]["export/events.csv.gz"],
        "rule_labels": RULE_LABEL,
        "campaigns": rows, "email": email, "buckets": buckets,
        "hygiene_top": eligible[:4], "hygiene_rest": eligible[4:], "hygiene_footnote": footnote,
    }
    out = ROOT / "src" / "lib" / "site.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(site, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out} (branch {site['branch']}, X={site['X']})")


if __name__ == "__main__":
    main()
