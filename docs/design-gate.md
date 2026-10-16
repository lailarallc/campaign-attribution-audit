# Design gate — realism criteria (pre-registered)

**Status:** DRAFT 2026-10-16. Pinned when the owner accepts it. No data is generated
before that. After pinning, a criterion changes only through a `DECISIONS.md` entry
whose reason is not "the verdict looked better."

Sources: `docs/anchors-research.md`, `docs/defect-taxonomy.md`. Tags:
- **CITE** = published figure used as the criterion.
- **DIR** = published direction or ranking only.
- **STRUCT** = Google platform documentation (exact rules).
- **A** = assumed, proposed, owner acceptance pending.

## 0. What the gate is for

The gate exists for realism, not drama.
- **Not a design input:** whether the four attribution rules disagree, and by how much. If they agree on this world, that is the result, and the copy adapts.
- **Not tuned:** defect rates are not adjusted after any output is seen.

## 1. Generation architecture (fixed by the measurement-version truth fork)

1. **True journeys first.** For each user, generate the real touch sequence (channel, campaign, timestamp, browser) and whether and when they purchase.
2. **Tracking layer second.** Apply the nine defect classes to turn true touches into what GA4 *would record*.
3. **Seed log.** Every defect application is logged with class, row and before/after values. The seeded defects ARE the v1 truth: counts are exact and the unattributable share is known, not estimated.
4. **Seed-locked and byte-stable.** One seed, deterministic, with a hash of the output committed.

Attribution rules run on the *recorded* layer, which is what a real analyst sees. True
journeys are kept for the roadmap's scored version and do not feed v1 claims.

## 2. Universe scale and period

| Criterion | Value | Tag |
|---|---|---|
| Period | One fixed calendar quarter, stated on every view | A (fleet precedent) |
| Online revenue in period | ~$500K (≈ $2M/yr small DTC food brand) | A |
| AOV | $80–120 band; generated mean must fall inside | DIR ([Attribuly](https://blog2.attribuly.com/average-order-value-vs-industry-2025-benchmarks-comparison/), vendor) |
| Site conversion rate | 1.9–3.0% sessions→purchase | CITE-range ([Triple Whale](https://www.triplewhale.com/blog/ecommerce-benchmarks), vendor) |
| Implied sessions | ~170–270K for the quarter (derived, not chosen) | derived |
| Active campaigns | 12–18 across paid search (brand + non-brand), paid social, email, one affiliate/referral | A (no published count) |

## 3. Channel and campaign realism

| Criterion | Pass condition | Tag |
|---|---|---|
| Per-channel CVR **ranking** | Email > paid search ≥ paid social > organic search > organic social (SMS out of scope) | DIR ([ThoughtMetric](https://thoughtmetric.io/blog/e-commerce-conversion-rate-benchmarks-q3-2025), 100-brand panel, vendor) |
| Per-channel CVR **levels** | Each within ±50% of the ThoughtMetric figure. The ranking matters more than the level | A-bounded |
| Email revenue share (true) | 9–25% | DIR (TopGrowth n=2; Vortex IQ, vendor) |
| Spend split Meta / Google / other | A: Google 45%, Meta 40%, other paid 15%. Email has no media spend | A (not found) |
| True ROAS by platform | Inside 1.5–6.0 for each paid platform. No rank order is targeted | A-bounded (TopGrowth n=5: Meta 2.70, Google 4.07) |
| Path length | 25–55% of true revenue from journeys with ≥3 sessions **and** ≥5 days | DIR ([Wolfgang 2016](https://www.wolfgangdigital.com/blog/benchmarking-analytics-time-paths-purchase): ~40%, dated agency) |
| Channel order in journeys | Paid social / non-brand search over-represented at first touch; brand search / email / direct at last touch | DIR (Racklify, Adtriba, vendor) — a property of true journeys, **not** a disagreement target |

## 4. GA4 structure (exact, testable)

| Criterion | Tag |
|---|---|
| Default channel group applied by Google's published rules (case-insensitive; off-spec → Unassigned) | STRUCT ([doc](https://support.google.com/analytics/answer/9756891)) |
| 30-min idle session timeout; new session on page view with none active; `session_start` carries source/medium/campaign/gclid | STRUCT ([doc](https://support.google.com/analytics/answer/9191807)) |
| Event names `page_view`, `view_item`, `add_to_cart`, `begin_checkout`, `purchase`; `purchase` carries `transaction_id`, `value`, `currency`, `items` | STRUCT ([dev guide](https://developers.google.com/analytics/devguides/collection/ga4/ecommerce)) |
| Export shape mirrors the GA4 BigQuery export (event-level rows, no UI dedup). That is where classes 3, 4 and 6 are visible | STRUCT (OWOX, READ) |
| Funnel monotone per channel: views ≥ add_to_cart ≥ begin_checkout ≥ purchase | logic |

## 5. Defect rates — pinned from the taxonomy

All rates are A-tags from `docs/defect-taxonomy.md`. They are proposed and need owner
acceptance. They are pinned here **before** generation and never retuned against the verdict.

| # | Class | Rate | Bound |
|---|---|---|---|
| A1 | Missing UTMs | 6% of paid-social + email sessions untagged | ≤10% vendor heuristic |
| A2a | Case/spelling variants | 12% of tagged sessions (rows fragment, channel unchanged) | none |
| A2b | Off-spec medium | 2% of tagged sessions → Unassigned | none |
| A3 | (not set) source | 1% of sessions (missing session_start). Campaign (not set) is derived from A1/A7, not seeded | none |
| A4a | Duplicate purchase sends | 3% of purchase events | < ~7% (OWOX, one dataset) |
| A4b | Missing transaction_id | 0.5% of purchase events | OWOX demo: present |
| A5 | Gateway self-referral | 4% of purchases | none |
| A6 | Non-human sessions | 3% paid-click / 1% other | ≤8.51% paid clicks (Lunio, vendor) |
| A7 | gclid lost | 2% of Google Ads clicks | none |
| A8 | Safari cookie expiry | mechanical: Safari session share 30% × return gap >7 days | CITE: Safari 30.42% US all-platform, Sep 2026 ([StatCounter](https://gs.statcounter.com/browser-market-share/all/united-states-of-america)) |
| A9 | Platform > GA4 conversions | +20% in the spend table's platform-reported column | 20–30% agency heuristic |

**Aggregate sanity check, not a target:** the resulting unattributable share of
conversions is *reported*, not tuned. No published GA4 aggregate exists to bound it.

## 6. Intent test

20 randomly sampled rows (sessions plus one purchase each), drawn with a fixed seed, are
shown to the owner raw. Pass = the owner judges them "looks like real GA data." On a
fail, the reason goes in FAILURES.md and the fix is to structure, never to defect rates.

## 7. Guardrail check (blocks the build)

- Brand, product names, campaign names and the naming convention are invented. No campaign name, account structure, spend level or result is modeled on any real program operator or client the owner has worked with, or any real account.
- Rates come only from the sources above, never from a client.
- A grep check for real client and brand names runs on the generated data before commit.

## 8. Open items at the gate

1. Owner acceptance of A-tags A1–A9 and the §2/§3 A rows.
2. ~~Safari share (A8)~~: resolved, StatCounter 30.42%.
3. **Verified [READ]:** Google, [Select attribution settings](https://support.google.com/analytics/answer/10596866): "The first click, linear, time decay, and position-based attribution models are no longer available as of November 2023." GA4 now offers data-driven (default), paid-and-organic last click, and Google-paid last click. The brief's "dropdown" verdict grammar is stale for GA4 users. See the fork in `PLAN.md`.
4. ~~Taxonomy filter outcome~~: resolved, test B (`DECISIONS.md`).
