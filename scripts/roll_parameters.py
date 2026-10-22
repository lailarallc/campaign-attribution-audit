"""Draw every structural universe parameter the design gate did not pin.

Distance by construction (Galewick pattern): no value here is hand-picked. Each is a seeded
draw from a stepped range whose basis is stated beside it. Seeds are SHA-256 of fixed
strings, mod 2^32: derived, not chosen. Re-running is byte-identical.

Pinned values (docs/design-gate.md) are NOT drawn; they live in generate_universe.py as
constants with their gate reference.

Output: data/parameters.json
"""

import hashlib
import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "parameters.json"


def seed_of(s):
    return int(hashlib.sha256(s.encode()).hexdigest(), 16) % (2**32)


SEED_STRING = "quellwood-provisions/2026-q3/parameters/v1"
ROSTER_SEED_STRING = "quellwood-provisions/campaign-roster/v1"   # design-gate 1.5

# Basis: CITE = published figure (docs/anchors-research.md); DIR = published direction or
# ranking only; STRUCTURAL = no published figure, range set for internal coherence.
RANGES = {
    "aov_target_usd": {"low": 85, "high": 115, "step": 5,
                       "basis": "DIR: food & bev AOV ~$80-120 (Attribuly, vendor); gate 2 band"},
    "cvr_scale": {"low": 0.55, "high": 0.85, "step": 0.05,
                  "basis": "CITE-range: scales ThoughtMetric Q3 2025 per-channel CVRs (ranking kept) "
                           "so the site CVR lands in the 1.9-3.0% band (Triple Whale); each level "
                           "stays within the gate's +/-50%"},
    "cvr_direct_pct": {"low": 2.0, "high": 3.5, "step": 0.25, "basis": "STRUCTURAL: no published DTC direct CVR"},
    "cvr_referral_pct": {"low": 1.25, "high": 2.75, "step": 0.25, "basis": "STRUCTURAL: referral and affiliate CVR"},
    "single_session_share": {"low": 0.35, "high": 0.50, "step": 0.05,
                             "basis": "STRUCTURAL, bounded by gate 3 path-length criterion (DIR Wolfgang 2016)"},
    "extra_sessions_mean": {"low": 1.5, "high": 3.0, "step": 0.25,
                            "basis": "STRUCTURAL: mean extra sessions in multi-session journeys"},
    "gap_days_mean": {"low": 2, "high": 6, "step": 1,
                      "basis": "DIR: ~40% of revenue after >=5 days (Wolfgang 2016)"},
    "blended_roas": {"low": 2.5, "high": 4.0, "step": 0.25,
                     "basis": "DIR: median ROAS Meta 2.70 / Google 4.07 (TopGrowth, n=5); sets total paid spend "
                              "from true linear paid revenue"},
    "a2a_case_share": {"low": 0.60, "high": 0.90, "step": 0.05,
                       "basis": "STRUCTURAL: share of A2a variants that are case-only (recovered by case-insensitive "
                                "match); the rest are spelling variants (Unmatched). Pinned 2026-10-22 before generation"},
    "ctr_pct": {"low": 0.8, "high": 2.4, "step": 0.2,
                "basis": "STRUCTURAL: blended CTR to derive impressions in the spend table"},
}

ROSTER = {
    # platform: [(campaign_id, campaign_name, sub_channel)]  (design-gate 1.5; names invented)
    "Google": [("G01", "qw_search_brand", "brand_search"),
               ("G02", "qw_search_nb_chili-crisp", "nonbrand_search"),
               ("G03", "qw_search_nb_gift-boxes", "nonbrand_search"),
               ("G04", "qw_search_nb_spice-blends", "nonbrand_search"),
               ("G05", "qw_shopping_all-products", "shopping")],
    "Meta": [("M01", "qw_meta_pro_gifting", "meta_prospecting"),
             ("M02", "qw_meta_pro_chili-crisp", "meta_prospecting"),
             ("M03", "qw_meta_pro_lookalike-buyers", "meta_prospecting"),
             ("M04", "qw_meta_rt_site-visitors", "meta_retargeting"),
             ("M05", "qw_meta_rt_cart-abandoners", "meta_retargeting")],
    "Other paid": [("T01", "qw_tiktok_pro_chili-crisp", "tiktok"),
                   ("A01", "qw_affiliate_partner-network", "affiliate")],
}
EMAIL_ROSTER = [("E01", "qw_email_weekly-newsletter", "email"),
                ("E02", "qw_email_abandoned-cart", "email"),
                ("E03", "qw_email_welcome-series", "email")]
DIRICHLET_ALPHA = 4.0   # STRUCTURAL: keeps within-platform shares away from degenerate extremes


def draw(rng, spec):
    n = round((spec["high"] - spec["low"]) / spec["step"])
    v = spec["low"] + rng.randint(0, n) * spec["step"]
    return round(v, 4)


def main():
    rng = random.Random(seed_of(SEED_STRING))
    params = {"seed_string": SEED_STRING, "draws": {}}
    for name, spec in RANGES.items():   # dict order fixes draw order
        params["draws"][name] = {"value": draw(rng, spec), **spec}

    rrng = random.Random(seed_of(ROSTER_SEED_STRING))
    roster = []
    for platform, camps in ROSTER.items():
        g = [rrng.gammavariate(DIRICHLET_ALPHA, 1.0) for _ in camps]
        tot = sum(g)
        for (cid, name, sub), gi in zip(camps, g):
            roster.append({"campaign_id": cid, "campaign_name": name, "platform": platform,
                           "sub_channel": sub, "platform_share": round(gi / tot, 6)})
    for cid, name, sub in EMAIL_ROSTER:
        roster.append({"campaign_id": cid, "campaign_name": name, "platform": "Email",
                       "sub_channel": sub, "platform_share": None})
    params["roster_seed_string"] = ROSTER_SEED_STRING
    params["dirichlet_alpha"] = DIRICHLET_ALPHA
    params["roster"] = roster

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(params, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")
    for k, v in params["draws"].items():
        print(f"  {k} = {v['value']}")


if __name__ == "__main__":
    main()
