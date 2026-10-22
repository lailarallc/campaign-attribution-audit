"""Behavior tests for the pinned definitions (docs/design-gate.md 1.5) and the
pre-registered branch selection (docs/verdict-branches.md 1). Run:
    python -m unittest discover -s tests
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import cmlib  # noqa: E402
import attribute  # noqa: E402


class ChannelGrouping(unittest.TestCase):
    def test_google_cpc_is_paid_search(self):
        self.assertEqual(cmlib.channel_group("google", "cpc", "qw_search_brand"), "Paid Search")

    def test_shopping_campaign_name_wins_over_paid_search(self):
        self.assertEqual(cmlib.channel_group("google", "cpc", "qw_shopping_all-products"), "Paid Shopping")

    def test_paid_social_medium_matches_paid_regex(self):
        self.assertEqual(cmlib.channel_group("Facebook", "paid_social", "x"), "Paid Social")

    def test_off_spec_email_medium_is_unassigned(self):
        self.assertEqual(cmlib.channel_group("quellwood_news", "newsletter", "x"), "Unassigned")

    def test_off_spec_social_source_is_unassigned(self):
        self.assertEqual(cmlib.channel_group("meta", "social_ad", "x"), "Unassigned")

    def test_direct(self):
        self.assertEqual(cmlib.channel_group("(direct)", "(none)", "(not set)"), "Direct")

    def test_not_set_source_is_unassigned(self):
        self.assertEqual(cmlib.channel_group("(not set)", "(not set)", "(not set)"), "Unassigned")

    def test_social_referrer_is_organic_social(self):
        self.assertEqual(cmlib.channel_group("l.instagram.com", "referral", "(referral)"), "Organic Social")

    def test_paypal_is_referral(self):
        self.assertEqual(cmlib.channel_group("paypal.com", "referral", "(referral)"), "Referral")


class CampaignMatching(unittest.TestCase):
    names = {"qw_meta_pro_gifting": "M01"}

    def test_case_variant_recovered(self):
        self.assertEqual(cmlib.credit_key("Paid Social", "facebook", " QW_Meta_Pro_Gifting ", self.names), "M01")

    def test_spelling_variant_is_unmatched(self):
        self.assertEqual(cmlib.credit_key("Paid Social", "facebook", "qw-meta-pro-gifting", self.names),
                         cmlib.UNATTRIBUTABLE)

    def test_unassigned_touch_is_unattributable_even_with_campaign(self):
        self.assertEqual(cmlib.credit_key("Unassigned", "meta", "qw_meta_pro_gifting", self.names),
                         cmlib.UNATTRIBUTABLE)

    def test_organic_touch_credits_channel(self):
        self.assertEqual(cmlib.credit_key("Organic Search", "google", "(organic)", self.names),
                         "channel:Organic Search")


class Rules(unittest.TestCase):
    def test_direct_only_path_goes_to_direct(self):
        for r in cmlib.RULES:
            self.assertEqual(cmlib.split_credit([], r), {cmlib.DIRECT: 1.0})

    def test_single_touch_all_rules_agree(self):
        for r in cmlib.RULES:
            self.assertEqual(cmlib.split_credit(["A"], r), {"A": 1.0})

    def test_two_touch_position_based_equals_linear(self):
        self.assertEqual(cmlib.split_credit(["A", "B"], "position_based"), cmlib.split_credit(["A", "B"], "linear"))

    def test_three_touch_weights(self):
        p = ["A", "B", "C", "D"]
        self.assertEqual(cmlib.split_credit(p, "last_click"), {"D": 1.0})
        self.assertEqual(cmlib.split_credit(p, "first_click"), {"A": 1.0})
        self.assertAlmostEqual(cmlib.split_credit(p, "linear")["B"], 0.25)
        pb = cmlib.split_credit(p, "position_based")
        self.assertAlmostEqual(pb["A"], 0.4)
        self.assertAlmostEqual(pb["D"], 0.4)
        self.assertAlmostEqual(pb["B"], 0.1)
        self.assertAlmostEqual(sum(pb.values()), 1.0)

    def test_repeated_key_accumulates(self):
        self.assertAlmostEqual(cmlib.split_credit(["A", "B", "A"], "linear")["A"], 2 / 3)


class Kendall(unittest.TestCase):
    def test_identical_ranking_is_one(self):
        self.assertAlmostEqual(cmlib.kendall_tau_b([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)

    def test_reversed_ranking_is_minus_one(self):
        self.assertAlmostEqual(cmlib.kendall_tau_b([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)

    def test_ties_handled(self):
        # scipy.stats.kendalltau([1,2,2,3],[1,2,3,3]).statistic == 0.8 (tau-b)
        self.assertAlmostEqual(cmlib.kendall_tau_b([1, 2, 2, 3], [1, 2, 3, 3]), 0.8)


class EngineOnToyExport(unittest.TestCase):
    def rows(self):
        def ev(t, name, user, sess, src="", med="", camp="", txn="", value=""):
            return {"event_timestamp": t * 1_000_000, "event_name": name, "user_pseudo_id": user,
                    "ga_session_id": sess, "source": src, "medium": med, "campaign": camp,
                    "transaction_id": txn, "value": value}
        return [
            ev(100, "session_start", "u1", 100, "facebook", "paid_social", "qw_meta_pro_gifting"),
            ev(200, "session_start", "u1", 200, "(direct)", "(none)", "(not set)"),
            ev(300, "session_start", "u1", 300, "google", "cpc", "qw_search_brand"),
            ev(310, "purchase", "u1", 300, txn="T1", value="100.00"),
            ev(315, "purchase", "u1", 300, txn="T1", value="100.00"),          # duplicate send
            ev(400, "page_view", "u2", 400),                                    # no session_start
            ev(410, "purchase", "u2", 400, txn="", value="50.00"),
        ]

    def test_dedup_paths_and_rules(self):
        names = {"qw_meta_pro_gifting": "M01", "qw_search_brand": "G01"}
        res = attribute.attribute_rows(self.rows(), names)
        self.assertEqual(len(res["convs"]), 2)          # T1 deduped; empty id counts once
        self.assertEqual(len(res["raw_purchases"]), 3)
        c = res["credit"]
        self.assertAlmostEqual(c["last_click"]["G01"], 100.0)   # direct skipped
        self.assertAlmostEqual(c["first_click"]["M01"], 100.0)
        self.assertAlmostEqual(c["linear"]["M01"], 50.0)
        self.assertAlmostEqual(c["last_click"][cmlib.UNATTRIBUTABLE], 50.0)   # (not set) session


class GeneratedUniverse(unittest.TestCase):
    """Runs only when the universe has been generated locally."""

    def setUp(self):
        if not (ROOT / "data" / "results.json").exists():
            self.skipTest("run scripts/generate_universe.py and scripts/attribute.py first")
        self.r = json.loads((ROOT / "data" / "results.json").read_text(encoding="utf-8"))

    def test_branch_follows_preregistered_rule(self):
        L = self.r["legs"]
        expected = "BANK" if (L["leg1_same_top"] and L["leg2_holds"] and L["leg3_holds"]) else \
            ("B1" if not L["leg1_same_top"] else "B2")
        self.assertEqual(self.r["branch"], expected)

    def test_rule_credit_conserves_revenue(self):
        total = self.r["measures"]["revenue"]
        for rule in cmlib.RULES:
            s = sum(c["revenue"][rule] for c in self.r["campaigns"]) + \
                sum(v.get(rule, 0) for v in self.r["non_campaign_credit"].values())
            self.assertAlmostEqual(s, total, delta=1.0)


if __name__ == "__main__":
    unittest.main()
