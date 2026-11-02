"""Behavior tests for the pinned definitions (docs/design-gate.md 1.5) and the
pre-registered branch selection (docs/verdict-branches.md 1), at each threshold. Run:
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

    def test_ties_on_one_side_only(self):
        # scipy.stats.kendalltau([1,1,2,3],[1,2,3,4]).statistic == 0.9128709 (tau-b)
        self.assertAlmostEqual(cmlib.kendall_tau_b([1, 1, 2, 3], [1, 2, 3, 4]), 0.9128709, places=6)
        self.assertAlmostEqual(cmlib.kendall_tau_b([1, 2, 3, 4], [1, 1, 2, 3]), 0.9128709, places=6)

    def test_fully_tied_side_reads_as_agreement(self):
        self.assertEqual(cmlib.kendall_tau_b([5, 5, 5], [1, 2, 3]), 1.0)


class BranchSelection(unittest.TestCase):
    """docs/verdict-branches.md section 1, at each threshold."""
    agree = {r: ["G01"] for r in cmlib.RULES}
    narrow = {"G01": [2.0, 2.0, 2.0, 2.0], "G02": [1.0, 1.0, 1.0, 1.0], "G03": [1.0, 1.4, 1.2, 1.2]}
    same = ([3, 2, 1], [3, 2, 1])

    def branch(self, tops=None, roas=None, ranks=None):
        return attribute.select_branch(tops or self.agree, roas or self.narrow, *(ranks or self.same))[-1]

    def test_all_legs_hold_is_bank(self):
        self.assertEqual(self.branch(), "BANK")

    def test_different_top_is_b1(self):
        self.assertEqual(self.branch(tops=self.agree | {"first_click": ["G02"]}), "B1")

    def test_tied_top_differs_from_single_top(self):
        self.assertEqual(self.branch(tops=self.agree | {"linear": ["G01", "G02"]}), "B1")

    def test_ratio_exactly_1_5_counts_as_wide(self):
        roas = {c: [1.0, 1.5, 1.2, 1.2] for c in ("A", "B", "C")}
        self.assertEqual(self.branch(roas=roas), "B2")

    def test_ratio_just_under_1_5_is_narrow(self):
        roas = {c: [1.0, 1.4999, 1.2, 1.2] for c in ("A", "B", "C")}
        self.assertEqual(self.branch(roas=roas), "BANK")

    def test_two_wide_holds_three_wide_fails(self):
        two = {"A": [1, 2, 1, 1], "B": [1, 2, 1, 1], "C": [1, 1, 1, 1]}
        self.assertEqual(self.branch(roas=two), "BANK")
        self.assertEqual(self.branch(roas=two | {"C": [1, 2, 1, 1]}), "B2")

    def test_zero_roas_counts_as_wide(self):
        roas = {c: [0.0, 1.0, 1.0, 1.0] for c in ("A", "B", "C")}
        self.assertEqual(self.branch(roas=roas), "B2")

    def test_tau_below_0_6_is_b2(self):
        # tau-b of [1,2,3,4] vs [2,1,4,3] is (4 - 2) / 6 = 1/3
        self.assertEqual(self.branch(ranks=([1, 2, 3, 4], [2, 1, 4, 3])), "B2")

    def test_tau_exactly_0_6_holds(self):
        # five items, two discordant pairs of ten: (8 - 2) / 10 = 0.6
        self.assertEqual(self.branch(ranks=([1, 2, 3, 4, 5], [2, 1, 4, 3, 5])), "BANK")


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

    def test_lookback_is_90_days_inclusive(self):
        day = 86_400

        def ev(t, name, sess, camp="", txn="", value=""):
            return {"event_timestamp": t * 1_000_000, "event_name": name, "user_pseudo_id": "u", "ga_session_id": sess,
                    "source": "facebook" if camp else "", "medium": "paid_social" if camp else "", "campaign": camp,
                    "transaction_id": txn, "value": value}
        t0 = 1_000 * day
        rows = [ev(t0 - 90 * day - 1, "session_start", 1, "qw_old"),    # one second outside the window
                ev(t0 - 90 * day, "session_start", 2, "qw_edge"),       # exactly 90 days: inside
                ev(t0, "purchase", 2, txn="T9", value="10.00"),
                ev(t0 + 1, "session_start", 3, "qw_after")]             # after the purchase: outside
        res = attribute.attribute_rows(rows, {"qw_old": "OLD", "qw_edge": "EDGE", "qw_after": "AFTER"})
        self.assertEqual(res["credit"]["first_click"], {"EDGE": 10.0})
        self.assertEqual(res["credit"]["last_click"], {"EDGE": 10.0})


class GeneratedUniverse(unittest.TestCase):
    """Runs only when the universe has been generated locally."""

    def setUp(self):
        if not (ROOT / "data" / "results.json").exists():
            self.skipTest("run scripts/generate_universe.py and scripts/attribute.py first")
        self.r = json.loads((ROOT / "data" / "results.json").read_text(encoding="utf-8"))

    def test_seeded_universe_selects_b2(self):
        # The seeded result recorded in docs/verdict-branches.md and DECISIONS (2026-10-22).
        self.assertEqual(self.r["branch"], "B2")

    def test_visit_shares_partition_revenue(self):
        m = self.r["measures"]
        self.assertAlmostEqual(m["p1_one_touch_rev_share"] + m["p2_two_touch_rev_share"] + m["p3_three_plus_rev_share"],
                               1.0, delta=0.001)

    def test_b2_clause_is_true_when_b2_ships(self):
        if self.r["branch"] == "B2":
            self.assertTrue(self.r["one_touch"]["top_is_largest_paid"])

    def test_rule_credit_conserves_revenue(self):
        total = self.r["measures"]["revenue"]
        for rule in cmlib.RULES:
            s = sum(c["revenue"][rule] for c in self.r["campaigns"]) + \
                sum(v.get(rule, 0) for v in self.r["non_campaign_credit"].values())
            self.assertAlmostEqual(s, total, delta=1.0)


if __name__ == "__main__":
    unittest.main()
