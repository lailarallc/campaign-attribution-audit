# Office hours — Campaign Math (2026-10-16, panel)

Three independent critics, each on one axis, all read-only against the pinned plan. The
owner asked for two axes to be stressed hardest: verdict resilience and the Cinderhaven
cross-check.

**Verdict: YELLOW → GREEN pending three owner forks (below).** The idea holds. The two
critical gaps (undefined "last-click" and "top campaign") and the identity mismatch are
resolved. What's left is pre-registration and presentation, not viability.

## 1. Verdict resilience (adversarial reviewer)

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | CRIT | "Last-click" undefined. Strict last-click could crown "(direct)" | **Fixed:** last non-direct click, design-gate §1.5 |
| 2 | CRIT | "Top campaign" undefined (metric, winner set, granularity), a hidden tuning lever | **Fixed:** paid only, attributed revenue, 15-campaign roster with seeded split, §1.5 |
| 3 | HIGH | Likely result: first-click dissents alone. On 1-touch paths all rules agree; on 2-touch paths position-based = linear. Estimate 60–75% that first-click names a different top campaign, 25–40% that all four agree | Open → fork A (bank rule) |
| 4 | HIGH | The recorded layer suppresses disagreement: A7/A8 split long journeys, and the late fragment's "first touch" becomes a closer | Kept. Rates are pinned and this is a true property of tracked data. The page must say it. Measure the surviving multi-touch share at build and report it |
| 5 | MED | Hygiene numbers echo the pinned rates (A9 returns exactly +20%) | **Copy rule:** "seeded at" / "results in", never "we found" |
| 6 | MED | The channel-order skew nearly guarantees first-vs-last disagreement | Copy states it is a general property of journeys, not a discovery |

Draft copy branches (pending fork A):
- **B1, top campaign differs under ≥1 rule:** "Your top campaign depends on a rule nobody chose. Last-click names {X}. First-click names {Y}. Both are arithmetic on the same quarter, and either can be checked by hand."
- **B2, top holds, order below moves:** "Every rule names {X} the top campaign. That one is real. Below it, the order is a choice: {n} of {m} paid campaigns move two places or more, and {Z}'s ROAS runs from {lo} to {hi} depending on the rule."
- **B3, rules agree:** bank, or if overridden: "This quarter, the rule barely matters. All four agree on the order, and no paid campaign's ROAS moves more than {k}%. Tracking decides the numbers instead: {s}% of revenue, ${d}, can't be attributed to anything."
- **Always shown:**
  - "{X} wins under every rule. Fund it without argument."
  - "{s}% of conversions, ${d}, reach no campaign at all. The tracking defects behind them are seeded at published or stated rates and listed below."
  - "GA4's default is data-driven attribution. It can't be reproduced. These four rules can, and they bracket it."

## 2. Cinderhaven cross-check (adversarial reviewer)

Verified against `cinderhaven-data-platform/reference/canonical_values.yml`:
- Canon DTC for CY2025 is $182,672.08 gross on 5,962 orders, AOV ≈ $31. That is 0.7% of the $25.3M business.
- The pinned plan has ~$500K per quarter at an $80–120 AOV, about 11x canon.
- Paid spend at ROAS 1.5–6 would exceed canon's whole DTC year.

**Resolved:** the owner reversed to a fresh brand, Quellwood Provisions (DECISIONS). The
scale and A-tags are unchanged.

## 3. Buyer and scope (product-lens reviewer)

| # | Finding | Disposition |
|---|---|---|
| 1 | A CEO clicks on dollars. "Rule nobody chose" is an analyst's concern | Open → fork B (verdict lead) |
| 2 | Nine hygiene rows, eight reading "none published", look to a buyer like "can't prove these matter" | Open → fork C (collapse) |
| 3 | The client base is retail-led, with DTC often under 10%. A DTC-only tool reads as a Shopify-brand tool, and it understates their real problem (paid social moving shelf sales GA4 can't see) | Open → fork C ("measurable floor" line). Retail-halo goes on the roadmap. Fresh brand partly answers this: the lane's buyers aren't CPG-only |
| 4 | Kill signal: rules agree **and** unattributable dollars are trivial | Covered by fork A |
| 5 | Client-mode needs the BigQuery-linked export (classes 3, 4 and 6 are visible only there). Most small brands haven't linked it | **Out of v1.** CTA is a manual offer. Build preflight only after a client says yes |

## Open forks for the owner

- **A. Bank rule.** Pre-register now. Bank only if *all* of these hold: same top paid campaign under all 4 rules; fewer than 3 paid campaigns with ROAS max/min ≥1.5; Kendall τ(first-click vs last-click paid ranks) ≥0.6. Otherwise ship the matching branch.
- **B. Verdict lead.** Dollars first, then rule, or keep rule first (the 2026-10-16 grammar).
- **C. Presentation.** (i) Collapse the hygiene rows: top 3–4 by dollars at full size, the rest expandable with the documented-case column. (ii) A "measurable floor" line for retail-led brands.
