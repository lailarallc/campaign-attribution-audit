# Tracking-defect taxonomy (anchor 4 — research-only)

Policy: `DECISIONS.md` 2026-10-16. Raw evidence: `docs/anchors-research.md`.

- **Existence** is CITE-backed for every class.
- **Rate** is CITE where published, otherwise **A-tag** (ASSUMED: Claude's labeled best
  guess). Every A-tag below is **proposed — not owner-accepted yet**. It is bounded by a
  citable aggregate where one exists. Aggregates bound, never divide.
- **Decision-impact filter**: a hygiene-audit-page slot needs a *documented* case where
  the defect changed or demonstrably distorted a budget decision. "Defect found, no
  decision stated" does not qualify. Mechanism-only claims ("this could hurt your
  budget") do not qualify.

Status: **slot test B adopted (owner, 2026-10-16; `DECISIONS.md`).** A class earns a page
slot with a documented decision case **or** a Google-documented mechanism that moves
conversion credit or counts. The "documented case" column is shown on the page honestly.
As-written result (1 of 9) is kept below for the record. **Result under B: 9 page rows
(classes 1, 2b, 3-9), 1 footnote (2a).**

---

| # | Class | Existence | Rate source | Documented decision case | As written | **Under B** |
|---|---|---|---|---|---|---|
| 1 | Missing UTMs | CITE (Google) | A-tag; vendor heuristic | none published | Footnote | **Page**: Google channel rules [READ] |
| 2a | Case/spelling variants | CITE (Google) | A-tag | none published | Footnote | **Footnote**: Google says channel rules are case-insensitive; campaign-row split is vendor-sourced only |
| 2b | Off-spec medium → Unassigned | CITE (Google) | A-tag | none published | Footnote | **Page**: Google channel rules [READ] |
| 3 | (not set) | CITE (Google) | A-tag (largely derived) | none published | Footnote | **Page**: Google, (not set) → Unassigned [READ] |
| 4 | Duplicate tagging / double-counted conversions | CITE (Google) | A-tag; one-dataset bound | none published (Augurian unconfirmed) | Footnote | **Page**: Google dedup rule [READ] |
| 5 | Self-referrals / payment gateways | CITE (Google, READ) | A-tag | none published | Footnote | **Page**: Google unwanted-referrals + cross-domain docs [READ] |
| 6 | Bot / invalid traffic | CITE (Google) | A-tag; vendor paid-click bound | **Uber / Frisch** [READ] | Page | **Page**: documented case |
| 7 | gclid lost / auto-tagging conflict | CITE (Google) | A-tag | none published | Footnote | **Page**: Google traffic-source doc [READ] |
| 8 | Cross-domain / session breaks / cookie loss | CITE (Google, READ) | mechanical (CITE Safari share) | none published | Footnote | **Page**: Google cross-domain doc [READ]; ITP part needs WebKit primary |
| 9 | Platform vs GA4 conversion gap | CITE (Google Ads, READ) | A-tag; agency heuristic | none published | Footnote | **Page**: Google Ads conversion-window doc [READ]; weakest mechanism, Google says only "risk of data discrepancies" |

---

## Per class

### 1. Missing UTMs
- **Existence:** [GA4 default channel group](https://support.google.com/analytics/answer/9756891) [READ]. Untagged clicks land in Direct, Organic or Unassigned.
- **Rate — A1:** 6% of paid-social and email sessions arrive untagged. Email falls to (direct)/(none); paid social keeps its referrer and falls to Organic Social (corrected 2026-10-22, re-review R3; rate unchanged). **Bounds:** the vendor heuristic says <5–10% of a known paid campaign's clicks in Direct is "acceptable" (Terminus, SNIP). The vendor figure ">30% of campaigns" (Trackingplan citing Improvado, no method) is a *campaign-share* ceiling and is not used as a rate.
- **Decision case:** none documented found. The best mechanism-only source is a blueriverd glossary example, which is explicitly hypothetical.
- **Demotion reasoning:** existence and mechanism are solid, but no published case ties it to a budget decision. → footnote.

### 2. Malformed / inconsistent UTMs
- **Existence:** same Google doc [READ]. Channel rules are **case-insensitive**, so case variants fragment source/medium/campaign rows *without* changing channel. Off-spec mediums (e.g., `newsletter`, `email-newsletter`) fall to Unassigned.
- **Rate — A2a:** 12% of tagged sessions carry a case or spelling variant of the canonical source (row fragmentation only). **A2b:** 2% of tagged sessions carry an off-spec medium and fall to Unassigned. **Bound:** none citable. The "40–50% of analytics problems" figure has an undefined denominator and is not usable.
- **Decision case:** none documented found.
- **Demotion reasoning:** no documented case. → footnote.

### 3. (not set)
- **Existence:** [GA4 "(not set)"](https://support.google.com/analytics/answer/13504892) [SNIP] and [Analytics Mania](https://www.analyticsmania.com/post/not-set-in-google-analytics-4/) [READ].
- **Rate — A3:** 1% of sessions have source/medium (not set) from a missing `session_start` (Measurement Protocol / tag-order causes). Campaign (not set) is **derived** from classes 1 and 7, not seeded independently, to avoid double-counting. **Bound:** none. The reader-comment figure (25% of revenue) is an anecdote and is not used.
- **Decision case:** none documented found.
- **Demotion reasoning:** no documented case. It is also largely a *symptom* of other classes, not an independent cause. → footnote.

### 4. Duplicate tagging / double-counted conversions
- **Existence:** [GA4 Measure ecommerce](https://support.google.com/analytics/answer/12313109) [READ]. GA4 dedups on `transaction_id` in the UI only. [OWOX](https://www.owox.com/blog/articles/duplicate-transactions-in-google-analytics.md) [READ]: there is no dedup in the raw BigQuery export.
- **Rate — A4a:** 3% of purchase events are repeat sends of an existing `transaction_id`. **A4b:** 0.5% of purchase events lack `transaction_id`. **Bound:** in Google's public demo dataset, repeats add ~7% of revenue and 906 purchases had no ID (OWOX, READ). This is one dataset, so it is used as an upper reference, not as prevalence. A4a stays below it.
- **Decision case:** the Augurian snippet (double-counted revenue → "better bidding signals") is **unconfirmed**: the fetched page did not contain it. tryscaleup was **checked and failed** [READ]: it gives one hypothetical and no account.
- **Demotion reasoning:** no confirmed documented case. → footnote. *Re-open if the Augurian case is confirmed.*

### 5. Self-referrals / payment gateways
- **Existence:** [Optimize Smart](https://optimizesmart.com/blog/self-referral-google-analytics-4-referral-exclusion-ga4/) [READ]. Gateway returns start referral sessions, and the exclusion list is not retroactive.
- **Rate — A5:** 4% of purchases are credited to a payment-gateway or own-checkout referral. **Bound:** none published.
- **Decision case:** Seer Interactive PayPal guide [SNIP]: one client had up to $60K/month of conversions recovered to organic. The defect was found and sized, but **no decision is stated**, and it concerned organic, not paid.
- **Demotion reasoning:** found but no stated decision consequence. → footnote.

### 6. Bot / invalid traffic — **page slot**
- **Existence:** [GA4 known-bot exclusion](https://support.google.com/analytics/answer/9888366) [SNIP]. Only declared bots are excluded. Undeclared bots and Measurement Protocol spam still reach reports (vendor, SNIP).
- **Rate — A6:** 3% of paid-click sessions and 1% of non-paid sessions are non-human. **Bound:** Lunio 2026 found 8.51% of 2.7B paid clicks invalid (vendor, SNIP). That caps the paid share **upstream of** GA4 filtering. Imperva's 37% bad-bot share is all web traffic including APIs and is **not** a GA4 bound, so it is not used.
- **Decision case — documented [READ]:** Uber. Kevin Frisch, former head of performance marketing, on the Marketing Today podcast, as reported by [Daily Maverick, 2021-01-18](https://www.dailymaverick.co.za/article/2021-01-18-the-digital-advertising-rip-off/):
  - Uber cut two-thirds of a ~$150M rider-side ad budget and rider installs did not change. Paid-credited installs reappeared as organic.
  - Cause: fake background clicks claiming credit for organic installs ("attribution fraud").
  - Caveats: journalism quoting a first-person account, and the primary podcast was not checked. Mobile install attribution, not GA4 web. The class mechanism (invalid clicks credited with conversions) transfers. The channel does not.
- Supporting [SNIP only, not cited until read]: ClickCease anonymized agency case. Daily spend was raised 40% on bot-inflated GA4 engagement, and >90% of that traffic was bots.
- **Placement:** page.

### 7. gclid lost / auto-tagging conflict
- **Existence:** [GA4 traffic-source updates](https://support.google.com/analytics/answer/15593651) [READ]. When the gclid is unusable, GA4 falls back to UTMs, else (not set).
- **Rate — A7:** 2% of Google Ads clicks lose the gclid (redirects) and land as organic or direct. **Bound:** none published.
- **Decision case:** none documented found. A Moz forum thread (auto-tagging off, 141 clicks vs 5 visits) gives no spend decision.
- **Demotion reasoning:** no documented case. → footnote.

### 8. Cross-domain / session breaks / cookie loss
- **Existence:** [GA4 cross-domain](https://support.google.com/analytics/answer/10071811) [SNIP]. Safari ITP 7-day / 24h cookie caps (vendor, SNIP; WebKit primary not read).
- **Rate — A8:** 25% of sessions are Safari. In this world, a Safari user returning more than 7 days after the last visit gets a new client_id, so first touch is lost. The rate is **mechanical**, not chosen: it follows from the browser share and the return-gap distribution. The Safari share itself needs a citable source (StatCounter) at the gate.
- **Decision case:** Stape / Lars Friis [SNIP]: +18% Google Ads conversions after server-side click IDs, but **no decision stated**. Wolfgang/Elverys is qualitative.
- **Demotion reasoning:** found but no stated decision. → footnote.

### 9. Platform vs GA4 conversion gap
- **Existence:** attribution-window and view-through differences (Jon Loomer et al., SNIP). Meta/Google primary docs were not read and must be read before citing.
- **Rate — A9:** platform-reported conversions exceed GA4 by 20%. **Bound:** the agency heuristic says 20–30% is "normal" (SNIP).
- **Decision case:** none for the *defect*. eBay (Blake, Nosko & Tadelis, Econometrica 2015) and Gordon et al. (Marketing Science 2019) are **attribution-rule** evidence: last-click credits sales that would have happened anyway. They belong to the **attribution view**, not the hygiene ledger. The Meta 2016 video-metric error was a platform metric with no stated reallocation.
- **Demotion reasoning:** no documented case for this defect. → footnote. The eBay and Gordon citations move to anchor 2 (the attribution view).

---

## Filter outcome — RESOLVED: test B (owner, 2026-10-16)

Per-class "Demotion reasoning" lines above record the **as-written** outcome. The table's "Under B" column is the live placement.

Applied as written, **the hygiene-audit page holds one class (bots/invalid traffic)** and
eight footnotes. The brief's view 3 ("the defect ledger … the lane's positioning as a
page") assumed several classes.

Why it lands here: published documented-decision cases exist for ad *fraud* (Uber, Chase,
P&G), because those were large and public. Tag-level GA4 defects are fixed quietly. Nobody
publishes "we misallocated budget because of UTMs." The missing published case reflects
publication bias, not proof of noise. But the rule as written can't tell the two apart.

Options:
- **A — keep as written.** Page = bots plus the computed unattributable share. Eight footnotes. Honest but thin, and the lane's "hygiene" positioning rests on one class.
- **B — widen the slot test (recommended):** admit a class if it has *either* a documented decision case *or* a Google-documented mechanism by which it moves the inputs a budget decision reads (channel/campaign conversion credit or conversion counts). Show a "documented decision case" column honestly: "Uber" for one row, "none published" for the rest. Classes whose mechanism doesn't touch conversion credit stay footnotes. Class 2a (case variants) fragments rows without changing channel, so it stays a footnote.
- **C — empirical slot test:** admit a class if removing it moves a campaign's ROAS range in *this* dataset. Rejected as a default: it makes A-tag rates decide page content, which edges toward drama-by-design.

---

## Mechanism citations added for test B (all [READ], 2026-10-16)

- **3:** [GA4 (not set)](https://support.google.com/analytics/answer/13504892): "If the session source / medium is reported as (not set), your traffic will be shown as Unassigned".
- **5:** [GA4 unwanted referrals](https://support.google.com/analytics/answer/10327750) lists "a third-party payment processor" as a domain that should not count as a referral. [GA4 cross-domain](https://support.google.com/analytics/answer/10071811): "Self-referrals may mean that traffic to your site is being attributed incorrectly."
- **8:** [GA4 cross-domain](https://support.google.com/analytics/answer/10071811): without it, one visitor counts as "two users and two sessions instead of one user and one session." The ITP 7-day cap is still vendor-sourced. Read the WebKit primary before citing it on the page.
- **9:** [Google Ads conversion windows](https://support.google.com/google-ads/answer/3123169): defaults are 30-day click and 1-day view. Aligning windows "reduces the risk of data discrepancies." This is the weakest mechanism on the page.
- **A8 Safari share:** [StatCounter US, all platforms, Sep 2026](https://gs.statcounter.com/browser-market-share/all/united-states-of-america): Safari 30.42%.
