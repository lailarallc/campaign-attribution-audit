# Anchor research — raw findings (2026-10-16)

Input to the design gate. Not yet pinned. Research-only policy (`DECISIONS.md`,
2026-10-16): no PRACTITIONER anchors in this repo.

**Read status:** [READ] = page fetched in full. [SNIP] = search-result summary only;
cite only after a fetch confirms it. **Type:** Google/platform doc · independent ·
vendor (benchmark or blog) · agency anecdote. Vendor caveat applies to every vendor row.

---

## Anchor 1 — tracking-defect existence and rates

Per-class detail, A-tags and decision-impact verdicts live in `docs/defect-taxonomy.md`.
This section holds the raw evidence only.

### 1. Missing UTMs

| Evidence | Source | Read | Type |
|---|---|---|---|
| Channel rules key off source/medium; non-match → Unassigned | [GA4 default channel group](https://support.google.com/analytics/answer/9756891) | READ | Google doc |
| Missing UTMs → (not set) in reporting | [GA4 traffic-source dims / tagging](https://support.google.com/analytics/answer/11242870) | SNIP | Google doc |
| Untagged paid social, redirects dropping query strings, in-app browsers; iOS 17 LTP strips gclid/fbclid, not utm_* | [Terminus](https://www.terminusapp.com/blog/why-paid-traffic-shows-as-direct-in-ga4/) | SNIP | Vendor |
| **Rate:** ">30% of campaigns" ship without UTMs | [Trackingplan](https://www.trackingplan.com/blog/utm-tracking-audit), citing Improvado; no method, no n | READ (secondhand) | Vendor |
| **Heuristic:** acceptable Direct 5–20% of site traffic; <5–10% of a known paid campaign's clicks | Terminus (above) | SNIP | Vendor heuristic |

### 2. Malformed / inconsistent UTMs

| Evidence | Source | Read | Type |
|---|---|---|---|
| Email = only email/e-mail/e_mail/e mail; Paid Social needs social source + medium `^(.*cp.*\|ppc\|retargeting\|paid.*)$`; non-match → Unassigned; rules **not case-sensitive** | [GA4 default channel group](https://support.google.com/analytics/answer/9756891) | READ | Google doc |
| UTM values stored as received → "Facebook"/"facebook"/"Facebook Ads" separate rows | [Search Atlas](https://searchatlas.com/blog/utm-rules-in-ga4/), [WeAreTG](https://www.wearetg.com/?p=15798) | SNIP | Vendor/agency |
| **Rate:** "40–50% of analytics problems" from inconsistent naming | Trackingplan citing Marketing Mojo; undefined denominator | READ (secondhand) | Vendor — not usable as a rate |

**Design consequence:** case variants fragment rows but do **not** change channel. Only
off-spec mediums/sources move traffic to Unassigned.

### 3. (not set)

| Evidence | Source | Read | Type |
|---|---|---|---|
| Placeholder for "no information received"; session source/medium (not set) when session_start missing → Unassigned; landing page (not set) without page_view; unlinked Ads accounts | [GA4 "(not set)"](https://support.google.com/analytics/answer/13504892) | SNIP | Google doc |
| Causes by dimension: timeouts, midnight-crossing sessions, MP hits without session_id, tags firing before Google tag, sGTM misconfig | [Analytics Mania](https://www.analyticsmania.com/post/not-set-in-google-analytics-4/) | READ | Agency |
| **Rate:** none published. Reader comments (25% of revenue (not set) on a server-side Shopify store) are anecdotes | same | READ | Anecdote — do not cite |

### 4. Duplicate tagging / double-counted conversions

| Evidence | Source | Read | Type |
|---|---|---|---|
| GA4 dedups purchases sharing transaction_id (web streams only); empty/reused IDs break it | [GA4 Measure ecommerce](https://support.google.com/analytics/answer/12313109) | READ | Google doc |
| Dedup does **not** apply to the BigQuery raw export | [OWOX](https://www.owox.com/blog/articles/duplicate-transactions-in-google-analytics.md) | READ | Vendor |
| **Quantified example:** Google's public GA4 demo dataset (Nov 2020–Jan 2021): 326 order IDs sent >1×, repeats add ~7% revenue (330,348 vs 308,200); 906 purchases with no transaction_id (31,817 revenue) | OWOX (above) | READ | Vendor analysis of one demo store — not prevalence |
| **Heuristic:** 5–15% platform-vs-orders gap normal; >30% almost always duplicate tags | [tryscaleup](https://tryscaleup.org/resources/fix-double-counting-google-ads-conversions) | SNIP | Vendor heuristic |

### 5. Self-referrals / payment gateways

| Evidence | Source | Read | Type |
|---|---|---|---|
| GA4 auto-corrects self-referrals only when both pages are tagged or cross-domain + _gl present; gateway returns show as referral; unwanted-referral list not retroactive | [Optimize Smart](https://optimizesmart.com/blog/self-referral-google-analytics-4-referral-exclusion-ga4/) | READ | Agency |
| Excluding paypal.com is not a guaranteed fix | [Optimize Smart newsletter](https://optimizesmart.com/p/ga4-misattributing-sales-to-paypal-here-s-the-real-fix) | SNIP | Agency |
| **Rate:** none published | — | — | — |

### 6. Bot / non-human traffic

| Evidence | Source | Read | Type |
|---|---|---|---|
| GA4 auto-excludes known bots (Google research + IAB list); exclusion can't be disabled or measured | [GA4 known-bot exclusion](https://support.google.com/analytics/answer/9888366) | SNIP | Google doc |
| Undeclared bots and Measurement Protocol ghost spam still reach reports | ClickCease, Stape, Mediavine help | SNIP | Vendor |
| **Rate:** 51% of web traffic automated, 37% bad bots (2024) — **all web traffic incl. APIs, not GA4 sessions** | Imperva Bad Bot Report 2025 via TechRadar | SNIP | Vendor |
| **Rate:** 8.51% of paid clicks invalid, 2.7B clicks, Aug 2024–Aug 2025 (TikTok 24.2%) — **paid clicks, not GA4 sessions** | Lunio 2026 via mediacat.uk / insideradio | SNIP | Vendor |
| No figure found for share of GA4-reported sessions that are non-human | — | — | — |

### 7. gclid lost / auto-tagging conflict

| Evidence | Source | Read | Type |
|---|---|---|---|
| gclid is primary; if unusable (e.g., ad_user_data denied) GA4 falls back to UTMs, else (not set). Caveat: page says enhancements apply to allowlisted properties | [GA4 traffic-source updates](https://support.google.com/analytics/answer/15593651) | READ | Google doc |
| Auto-tagging takes precedence over manual tags | [GA4 auto-tagging benefits](https://support.google.com/analytics/answer/10723328) | SNIP | Google doc |
| 302 redirect stripped gclid → paid shown as organic | Moz forum | SNIP | Anecdote |
| **Rate:** none published. "~30% of (direct)/(none) originates elsewhere" | Terminus | SNIP | Vendor, unverified |

### 8. Cross-domain / session breaks / cookie loss

| Evidence | Source | Read | Type |
|---|---|---|---|
| Without cross-domain config + referral exclusions, a hop to an owned/payment domain starts a new referral session | [GA4 cross-domain](https://support.google.com/analytics/answer/10071811) | SNIP | Google doc |
| Safari ITP caps JS-set first-party cookies at 7 days; 24h when arriving via decorated URLs | Segmentstream, Hardal, Louder | SNIP | Vendor (WebKit primary not read) |
| **Rate:** consent-mode modeling recovers ">70% of ad-click-to-conversion journeys" lost to declined consent (advanced mode) | [Google blog, 2021-05-13](https://blog.google/products/ads-commerce/future-proof-measurement-privacy-safe-solutions) | READ | Google claim, 5 yrs old |
| **Rate:** ITP+ETP+ad blockers remove 30–40% of pixel-only conversion data | adtribute glossary | SNIP | Vendor, undated |
| No rate for GA4 cross-domain break frequency | — | — | — |

### 9. Platform vs GA4 conversion gap

| Evidence | Source | Read | Type |
|---|---|---|---|
| Different windows (Meta 7d-click/1d-view default; Google Ads 30d click), view-through, modeled conversions, GA4 DDA | [Jon Loomer](https://www.jonloomer.com/qvt/ads-manager-reporting-and-ga4-dont-line-up/), Taggrs, Trackingplan | SNIP | Agency/vendor (Meta/Google primaries not read) |
| **Heuristic:** 20–30% gap "normal", <10% "suspiciously clean" | easyinsights | SNIP | Agency |
| ~10–15% of Meta-reported conversions view-through | Jon Loomer | SNIP | Anecdote |
| "Meta ~26% higher", "GA4 underreports 18–35%" | untraceable | — | **Do not cite** |

---

## Anchor 2 — attribution-rule disagreement

- **Magnitude:** not found. Anderl et al. 2016 (IJRM, Markov graph attribution, 4 datasets ≥7 channels) report results "differ substantially" from last-click; no figures retrieved. Li & Kannan 2014 (JMR 51(1)) and Shao & Li 2011: no comparison figures retrieved. **DIRECTION only.**
- **Direction (vendor/practitioner):** first-click favors top-of-funnel (paid social, display); last-click favors closers (branded search, email, retargeting). [Racklify](https://racklify.com/encyclopedia/first-click-attribution-vs-last-click-and-multi-touch-models-a-practical-comparison/), [Adtriba](https://help.adtriba.com/en/articles/3339719-comparison-of-attribution-models).
- **GA4 fact — verified [READ] against [Google](https://support.google.com/analytics/answer/10596866), "no longer available as of November 2023":** first-click, linear, time-decay and position-based were **removed from GA4 in late 2023**; remaining: data-driven (default), paid-and-organic last click, Google-paid last click. [Polar](https://www.polaranalytics.com/post/ga4-attribution-models), [EasyInsights](https://easyinsights.ai/blog/attribution-model-comparison-in-google-analytics-4/). **→ affects the "dropdown" framing; see forks.**
- Per the brief, disagreement magnitude is **not a design input** regardless.

## Anchor 3 — campaign-mix realism (small DTC food)

| Metric | Figure | Source | Type |
|---|---|---|---|
| CVR by channel (100 brands, Q3 2025) | SMS 11.92%, Email 8.43%, Google Ads 3.95%, Meta 3.87%, TikTok 3.07%, organic search 2.02%, organic social 1.42% | [ThoughtMetric](https://thoughtmetric.io/blog/e-commerce-conversion-rate-benchmarks-q3-2025) | Vendor, one panel |
| Overall ecommerce CVR | ~1.9–2%; Shopify 2.5–3% | [Triple Whale](https://www.triplewhale.com/blog/ecommerce-benchmarks) | Vendor |
| Food & bev CVR | 2.4% (Q1 2026) — page not verified | Statista | Unverified |
| Food & bev AOV | ~$80–120, thin public data | [Attribuly](https://blog2.attribuly.com/average-order-value-vs-industry-2025-benchmarks-comparison/) | Vendor |
| Email share of revenue | 9–15% (n=2); 15–25% "healthy" | TopGrowth, Vortex IQ | Agency/vendor, weak |
| Median ROAS (n=5) | Meta 2.70, Google 4.07 | [TopGrowth](https://topgrowthmarketing.com/dtc-benchmarks-2026/) | Agency, n=5 |
| Path length | 40% of revenue after ≥3 same-device clicks and ≥5 days (online-only retailers, 2016) | [Wolfgang Digital](https://www.wolfgangdigital.com/blog/benchmarking-analytics-time-paths-purchase) | Agency, dated |
| Spend split Meta/Google/email; # active campaigns; direct CVR | not found | — | → A-tag |

Channel **ranking** is more reliable than absolute levels (mixed denominators).

## GA4 data shape (platform docs — structural, not rates)

- Session: 30-min idle timeout default; new session on page view with none active; `session_start` carries gclid/UTMs/referrer. Default key-event lookback 90 days; reporting uses last non-direct click. [GA session doc](https://support.google.com/analytics/answer/9191807).
- Default channel group: rules above; case-insensitive; not editable; non-match → Unassigned. [doc](https://support.google.com/analytics/answer/9756891).
- Ecommerce events `view_item`, `add_to_cart`, `begin_checkout`, `purchase`; `transaction_id` required for purchases/refunds; `value`, `currency`, `items`. [dev guide](https://developers.google.com/analytics/devguides/collection/ga4/ecommerce).

## Gaps

No independent per-class prevalence rate exists for any of the nine classes. Every
per-class rate in the synthetic world will be an **A-tag** bounded where a citable
aggregate exists (classes 4, 6, 1-heuristic). Decision-impact cases: dedicated pass
pending (see `docs/defect-taxonomy.md`).
