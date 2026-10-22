# Realism review — Quellwood Provisions 2026-Q3 universe (commit e9f6161)

**Verdict: FAIL.**

The attribution arithmetic is sound. An independent re-implementation of §1.5, written from the
gate text, reproduces every campaign's revenue under all four rules to within $0.005. It also
reproduces Kendall τ-b (0.6061), the ROAS ratios, the B2 branch, {U} and {s}/{d}.

Three things fail:
1. One pinned measure is computed against its own definition, and the error reaches shipped copy
   (F1, critical).
2. Two §4 STRUCT/logic rows fail, both because of how the payment-gateway defect is built (F3).
3. The universe has no history. Every user is born in the quarter, nobody buys twice, and
   cart-abandoner retargeting and abandoned-cart email land on first-time visitors (F2).

A GA4 practitioner would spot F2 within minutes. Every fix belongs in the generator, the engine
or the bounds check. None needs a change to a §5 rate or a pinned A row.

Reviewer: independent session with no stake in the build. Read-only except for this file. Analysis
used Python stdlib only on `data/export/events.csv.gz`, `data/spend.csv`, `data/truth/*.csv.gz`
and `data/results.json`. The data hashes match `data/manifest.json`. The working tree's only
generator change is uncommitted (manifest hashing over decompressed bytes) and does not touch the
data.

## What holds up

- **Engine reproduction is exact.** An independent sessionizer, channel classifier, dedup, 90-day
  lookback, Direct removal and four rules give these results:
  - 5,556 deduped conversions and $503,227 of revenue.
  - 755 unattributable conversions, $69,644, s = 13.59%.
  - All 48 campaign × rule revenues within $0.005.
  - Top paid campaign G01 under all four rules.
  - Wide-ROAS set {G03, M02, M03, M04, M05}.
  - τ-b 0.6061. Branch B2 follows correctly: Leg 1 holds, Leg 2 fails, Leg 3 holds.
  - U = $4,250.33 of S = $75,451.56.
  - t = 22.1%. It is robust: dropping case-only A2a variants, which do not change attribution,
    moves it to 22.1% (166 of 750 vs 167 of 750).
- **Kendall τ-b is implemented correctly.** The code's denominator, (C+D+tx)(C+D+ty), uses
  "tied only in x" and "tied only in y". The product equals the textbook (n0−n1)(n0−n2).
- **Campaign matching follows §1.5.** Matching is case-insensitive after trimming. Spelling
  variants go to Unmatched. Unassigned and (not set) touches stay in the path as Unattributable.
- **Dedup follows §1.5.** It keys on `transaction_id`, keeps the earliest instance, and counts
  each empty id once: 5,708 raw purchase events give 5,556 conversions.
- **Defect rates are at their pins (§5).**

  | Class | Realized |
  |---|---|
  | A1 | 5.89% |
  | A2a | 11.28% |
  | A2b | 1.88% |
  | A3 | 1.00% |
  | A4a | 2.74% (152 dups, 5–90 s apart, median 47 s) |
  | A4b | 0.63% (35) |
  | A5 | 4.28% (238) |
  | A6 | 3.00% paid / 1.00% other |
  | A7 | 1.97% |
  | A8 | 6,369 resets (recomputed exactly from Safari users × gaps > 7 days); human Safari session share 30.6% |

- **Self-referral looks right in aggregate.** PayPal referral sessions make Referral the
  highest-CVR channel (6.6%). Practitioners recognize this signature.
- **Funnel in aggregate is monotone:** view_item 68,145 ≥ add_to_cart 22,259 ≥ begin_checkout
  11,165 ≥ purchase 5,708. Mobile share is 70% of sessions.

## Gate re-check (§2–§5), independent

| § | Criterion | Re-derived | Result |
|---|---|---|---|
| 2 | Revenue ~$500K | $503,227 | PASS |
| 2 | AOV $80–120 | $90.57 (orders) | PASS |
| 2 | Site CVR 1.9–3.0% | 2.41% true human; 2.36% recorded | PASS |
| 2 | Sessions 170–270K | 230,472 human; 235,078 recorded | PASS |
| 2 | Campaigns 12–18 | 15 | PASS |
| 3 | CVR ranking | email 5.65 > paid search 2.74 ≥ paid social 2.31 > organic search 1.30 > organic social 0.93 | PASS |
| 3 | CVR levels ±50% | −31% to −40% for every channel (uniform `cvr_scale` 0.65) | PASS |
| 3 | Email revenue share 9–25% | 15.7% (true linear) | PASS |
| 3 | Spend split 45/40/15 | 45.0 / 40.0 / 15.0 | PASS |
| 3 | True ROAS 1.5–6.0 | Google 3.96, Meta 3.30, Other 2.64 | PASS |
| 3 | Path length 25–55% | 27.0% | PASS |
| 3 | Channel order | discovery 43.5% first vs 17.6% last; closers 19.0% first vs 45.7% last | PASS |
| 4 | Default channel group | independent classifier agrees | PASS |
| 4 | 30-min session timeout | **240 sessions start < 30 min after the same client's previous event (238 are A5)** | **FAIL** (F3) |
| 4 | Event names + purchase params | present | PASS (format tells in F7) |
| 4 | Export shape mirrors BigQuery | event-level, no dedup; many standard fields absent | PASS WITH FINDINGS (F7) |
| 4 | Funnel monotone **per channel** | **Referral: begin_checkout 346 < purchase 417** | **FAIL** (F3) |
| 5 | Rates A1–A9 | see above | PASS |

`bound_check.py` tests funnel monotonicity on the aggregate only, so it reports PASS on a row that
is pinned per channel. It does not test the session timeout at all.

## 20-row sample (seed `random.Random(20261022)`)

Method: 5 sessions drawn from the 5,708-session purchase pool, then 15 from all 235,078
sessions. Times are UTC. "eng" is `engagement_time_msec`.

```
#1  google/organic, new, mobile/Chrome. ss+fv+pv 14:16:19 (eng 54304) -> view_item /products/item
    14:19:18 -> atc /cart -> begin_checkout /checkout -> purchase 14:20:44 QW104247 49.00 USD
    items=QW-PR-01|QW-SB-01|QW-SB-02|QW-CC-01
#2  affiliate partner_network, session_number 4, 4 page_views then funnel, purchase QW109042
    187.00 items=...|QW-GB-01|...|QW-GB-01   (same SKU twice, no quantity)
#3  google/cpc qw_search_brand, gclid=Cj0KCQjw4e24468b39390527 (24 chars), lands
    /pages/our-kitchen, new user, purchase 180.00 (7 lines, 3 repeated SKUs)
#4  (direct), session 4, desktop/Samsung Internet, purchase 151.00
#5  hotsaucenotes.blog/referral, Safari, 7 page_views: /pages/our-kitchen eng=77742 then
    view_item 34 s later (engagement exceeds dwell); purchase 94.00
#6  meta/social_ad (A2b -> Unassigned), new, 2 page_views
#7  google/cpc qw_search_nb_gift-boxes -> lands /collections/chili-crisp, new
#8  giftguide-weekly.net referral, new, 1 page_view
#9  facebook/paid_social lookalike, session 2, mobile/Firefox, 1 page_view
#10 (direct), new, view_item + add_to_cart, no checkout
#11 google/organic, new, 5 page_views (/collections/all twice in a row)
#12 bing/organic, session 2, 02:29 UTC, 1 page_view
#13 l.instagram.com/referral, session 2, mobile/Firefox, view_item + atc
#14 tiktok/paid_social chili-crisp campaign -> lands /collections/spice-blends
#15 google/cpc shopping, new, Safari, lands /products/smoked-chili-crisp (as for 64% of Shopping)
#16 duckduckgo/organic, new, view_item on /products/item after a /collections page
#17 l.instagram.com, session 3, 2 page_views
#18 google/organic, new, 2 page_views
#19 google/cpc qw_search_nb_gift-boxes -> /collections/chili-crisp again, new
#20 quellwood_news/email qw_email_abandoned-cart -> **first_visit** (abandoned-cart email to a
    user who has never visited)
```

**Does it look like a real GA4 export?** At a glance, partly. The column set, the
`session_start`/`first_visit`/`page_view` triplet with a shared timestamp, `user_pseudo_id` as
`rand.epoch`, and `ga_session_id` as session-start epoch seconds are all right. Synthetic tells
in the sample:

- Every timestamp is a whole second.
- Every value is whole dollars.
- `view_item` always fires on the placeholder path `/products/item`.
- Cart, checkout and thank-you pages get no `page_view`.
- Repeated SKUs stand in for quantity.
- Engagement time exceeds dwell.
- Landing pages ignore the campaign.
- gclids are short hex strings.
- An abandoned-cart email reaches a first-time visitor.
- 12 of 20 sessions are a user's first visit.

## Findings

Ranked by severity.

### F1 (Critical): the {p1} measure counts Direct-only paths as "one-touch", and the shipped B2 copy rests on it

**What:** `attribute.py` buckets path length with `lens[1 if n <= 1 else ...]`, so paths of
**length 0** (Direct-only, after Direct removal) land in p1. verdict-branches §2 defines p1 as
revenue "whose recorded path has 1 touch". The B2 body then says "{p1}% of revenue comes from
customers with one recorded visit".

**Evidence (deduped revenue $503,227):**

| Measure | Value |
|---|---|
| Reported p1 | **59.35%** |
| Paths with exactly 1 non-direct touch | 46.91% |
| Direct-only paths (n = 0) | 12.44%. Many have several Direct visits. |
| Conversions with literally one recorded session, any channel | 51.94% |

The same B2 sentence pairs p1 with `{share}`. Its denominator (`one_touch`, `len(path) == 1`)
**excludes** the n = 0 paths, so the two numbers in one sentence describe different
populations. p1 + p2 + p3 = 100% only because n = 0 is folded in.

**Why it is critical:** this is a pinned measure that feeds published copy. The printed figure
overstates its own definition by 12.4 points, and its wording ("one recorded visit") is false
for about 1 in 8 dollars it counts.

**Fix (engine only):**
- Report a separate {p0} (Direct-only) and compute p1 as n == 1 exactly.
- If the copy needs "every rule must agree" revenue, name that slot explicitly as p0 + p1, with
  wording that does not say "one recorded visit".
- Log the change in DECISIONS: a definition repair, not a verdict-driven change.

### F2 (High): the universe has no history; every user is born in Q3, nobody returns after buying, and retention channels hit strangers

**Evidence:**
- **190,687 of 190,687** `user_pseudo_id`s have a `first_visit` inside the quarter.
  - Only 279 client ids were minted before 2026-07-01.
  - All 279 still get a July `first_visit` and `ga_session_number = 1`, which contradicts their
    own id timestamp.
- **Zero repeat purchasers.** No truth `uid` has more than 1 order.
- **Zero sessions** from any purchaser more than 1 hour after the purchase. Each order is a fresh
  user whose journey ends at checkout.
- `first_visit` share of sessions, by campaign:

  | Campaign | First-visit share |
  |---|---|
  | qw_meta_rt_cart-abandoners | **79.2%** |
  | qw_meta_rt_site-visitors | 78.0% |
  | qw_email_abandoned-cart | 77.4% |
  | qw_email_welcome-series | 78.9% |
  | qw_email_weekly-newsletter | 77.6% |
  | qw_search_brand | 77.5% |

  Retargeting and lifecycle email cannot reach users the site has never seen.
- Returning-session share ramps 6.6% (week 1) → 15.8% → ~19% (weeks 3–11) → 29.5% (week 14).
  This is a cold start, not a steady-state store.
- 82% of users have exactly one session.

**Why it matters:** a specialty-food DTC brand's email list, retargeting pools and
brand-search traffic are mostly prior visitors and prior customers. An analyst sees the 78%
new-user share on cart-abandoner retargeting at once. It also affects lookback realism: the
90-day window has nothing before July 1 to reach.

**Fix (generator, separate seeded stream):**
- Seed a pre-quarter population: prior visitors and prior customers with client ids minted before
  July 1. Continue their `ga_session_number`, and emit no `first_visit` for them in the export.
- Draw email and retargeting sessions only from users with qualifying history:
  - list members for the newsletter;
  - carts for abandoned-cart and M05;
  - recent visits for M04;
  - new sign-ups for the welcome series.
- Allow repeat orders from prior customers, and some post-purchase browsing.
- Optionally include a June export (out of the reporting window) so the 90-day lookback has
  something to read.
- Re-run §2/§3. Revenue and CVR targets stay pinned. Only the composition changes.

### F3 (High): the A5 PayPal return breaks two §4 rows (30-minute session rule; per-channel funnel)

**What:** the gateway return opens a new `session_start` (paypal.com/referral) **60–300 s** after
`begin_checkout`, in the same client.

**Evidence:**
- 238 A5 sessions start a median 176 s after the same client's previous event. The pinned rule
  is "new session on page view with none active", with a 30-minute idle timeout. GA4 does not
  start a new session because the traffic source changed.
- The 238 purchase-only sessions give the **Referral** channel 417 purchases against 346
  `begin_checkout`, which breaks "funnel monotone per channel".
- `bound_check.py` only checks the aggregate funnel and has no timeout check, so both failures
  pass silently.
- The 2 other sub-30-minute starts come from journey gaps drawn near zero
  (`expovariate` days + 600–7,200 s).

**Fix:**
- Draw the PayPal return idle time from **≥ 30 minutes**, for example 31–120 minutes, in a separate
  stream. The new referral session is then legitimate GA4 behavior, and the 4% rate is unchanged.
- Floor journey gaps at 30 minutes plus the last event's offset.
- Add both checks to `bound_check.py`: per-channel funnel and per-client session gap ≥ 30 minutes.
- A gateway-return session will still hold a purchase without a `begin_checkout`. That is the
  defect's real signature. Record in DECISIONS that the per-channel monotonicity row is evaluated
  excluding seeded A5 return sessions. The row is a logic tag, not an A row, so this is not a
  retune.

### F4 (Medium): defects are drawn per session, i.i.d., which reads as planted

**Evidence:**
- **127 distinct `campaign` strings** for 15 campaigns.
- qw_meta_pro_chili-crisp alone appears in 14 spellings, each with 30–313 sessions:
  - `QW_meta_Pro_Chili-crisp`, `QW_Meta_Pro_Chili-crisp`, `QW_meta_Pro_chili-crisp`,
    `QW_Meta_pro_Chili-crisp`, … (9 casing permutations);
  - plus `qw-meta-pro-chili-crisp`, `qw meta_pro_chili-crisp`, `qw_meta_pro_chilicrisp` and
    `qw_meta_pro_chilli-crisp`.
- A1, A2a, A3 and A7 are spread evenly over every campaign and every month (A2a: Jul 2,474 /
  Aug 2,642 / Sep 2,550).
- Real fragmentation comes from a few mis-built links: one ad, one email send or one redirect.
  Each carries one consistent bad string, so it clusters by creative and by date.

**Fix:** assign A1, A2a, A2b and A7 at the **link level**: ad × creative, email send, or
landing-page redirect. The share of affected links is drawn so that the expected session share
equals the pinned rate, with the realized rate kept as now. Each bad link carries one fixed
variant string. This changes structure, not rates.

### F5 (Medium): spend-table regularities a media buyer would spot

**Evidence:**
- CTR is **exactly 1.60%** on all 12 paid campaigns. Brand search, Shopping, Meta prospecting and
  TikTok are given identical impressions/clicks ratios.
- `platform_conversions / GA4 last-click` is **1.197–1.208 on every campaign**. Meta's
  view-through gap equals Google's to the third decimal.
- Platform `clicks` equal true in-quarter sessions **one to one**, bots included. The only
  click-to-session loss in the world is the seeded defects. Real ad-click → GA4-session ratios
  run below 1 for reasons outside the nine classes: consent refusals, ad blockers and bounces
  before the tag fires.
- The table is quarter totals only, with no daily rows, so pacing and flighting cannot be checked.
- Affiliate A01 is billed per click ($0.61 CPC); affiliate programs are normally paid on
  commission.

**Fix (separate stream):**
- Per-campaign CTR from type-appropriate ranges: brand search high, prospecting low.
- A per-campaign A9 multiplier whose conversion-weighted mean is held at **exactly +20%**, so the
  pinned aggregate is unchanged and campaigns differ.
- Daily spend rows.
- Affiliate cost as commission on platform-reported sales.
- **Owner call:** non-defect click loss would move {U}. If it stays at zero, the copy should say
  that untraced spend counts only the seeded defects.

### F6 (Medium): flat time structure; no sends, launches or promos, and the clock is UTC

**Evidence:**
- Every campaign's daily sessions have a CV of 0.08–0.19, which is Poisson noise on a flat line.
- `qw_email_weekly-newsletter` spreads evenly across weekdays (876–1,010 sessions per weekday). A
  weekly send produces one spike day and a decay.
- No campaign launches, pauses or promotions. The quarter has a smooth +10% trend and no Labor Day
  effect.
- The hour weights are applied in **UTC**, and `event_date` is derived in UTC:
  - session starts peak at 20:00 UTC (16:00 ET);
  - they bottom out at 01:00–04:00 UTC (21:00–00:00 ET), which is the US evening peak for
    food e-commerce;
  - GA4 writes `event_date` in the property's time zone.

**Fix:**
- Email sessions from discrete send dates with a decay curve.
- Per-campaign flight calendars, including at least one launch and one pause.
- Apply hour weights in America/New_York (or a US time-zone mix), and write `event_date` in the
  property time zone. `event_timestamp` stays UTC.

### F7 (Medium): event-level content tells

**Evidence:**
- **0 of 923,756** timestamps have a sub-second part.
- **0 of 5,708** purchase values have cents. There is no tax, shipping or discount.
- 1,965 orders (35%) repeat a SKU as separate pipe-joined entries instead of a quantity. Items
  carry no price or quantity.
- Every `view_item` is on `/products/item`. Cart, checkout and thank-you pages have no
  `page_view`. `add_to_cart` has no value or items.
- `engagement_time_msec` is uniform 3–90 s and exceeds the time to the next event on **50,134 of
  226,327** page_views (22%).
- Pages per session are **1.64–1.69 in every channel**. Email, brand and prospecting do not
  differ.
- gclids are 24-character hex strings. Real gclids are roughly 90-character base64url.
- Standard export fields are absent: `event_params`, `page_referrer`, `page_title`, geo,
  `platform`, `session_engaged`, and the `user_engagement` and `scroll` events.

**Fix (generator only):**
- Microsecond jitter on timestamps.
- Order value = items + shipping − discount + tax.
- Item lines as SKU:qty:price.
- `view_item` on the actual product URL, plus page_views for cart, checkout and thank-you.
- Engagement bounded by dwell and heavy-tailed.
- Per-channel depth.
- Realistic gclid length.
- Add `page_referrer` at minimum. It is also what makes A5 auditable.

### F8 (Medium): device and browser are drawn independently

**Evidence:**
- Desktop Samsung Internet has 5,618 sessions, more than desktop Safari (4,734).
- Mobile Edge (7,103) outnumbers desktop Edge (3,947).
- Only 554 of 6,828 tablet sessions are Safari, yet iPad dominates US tablets.

**Fix:** draw device × browser jointly from a platform-split table in a separate stream. Hold
Safari's share at 30.42% so A8 stays mechanical and pinned.

### F9 (Medium): the bot signature is a perfect separator

**Evidence:**
- All 4,368 A6 sessions are desktop Chrome, a single `page_view` with
  `engagement_time_msec = 0`, and a new user.
- The filter "engagement = 0" isolates exactly the bot set: 4,368 matches, 0 false positives.
- Undeclared bots in real exports are messier: mixed user agents and mobile emulation, some
  multi-page or engaged sessions, and engagement fields absent rather than 0.

**Fix:** use 2–3 bot profiles from a separate stream, for example single-hit, crawler-like
multi-page, and click-fraud bursts on paid campaigns. Keep the pinned A6 counts.

### F10 (Low): landing pages follow sub-channel, not campaign

**Evidence:**
- `qw_search_nb_gift-boxes` lands on /collections/chili-crisp for 6,170 of 9,827 sessions (63%).
- `qw_search_nb_spice-blends` lands on /collections/chili-crisp too (3,752).
- The cart-abandoner campaign lands on /cart (2,447 sessions), mostly for first-time visitors
  (F2).
- The TikTok chili-crisp campaign lands on /collections/spice-blends in the sample.

**Fix:** map landing pages per campaign (`LANDING` keyed by campaign_id).

### F11 (Low): the hygiene ledger and {t} key on the whole true journey, not the recorded lookback path

**What:** `hygiene_ledger` and `defect_share` count an order as defect-touched if **any** session
of that `uid` was hit, at any time. verdict-branches §2/§6 say "path".

**Evidence:** today the two coincide, because converters have no sessions outside their journey
(F2). They will diverge as soon as F2 is fixed: prior-quarter or post-purchase sessions would
start counting.

**Fix:** restrict to sessions inside the conversion's 90-day lookback, before the purchase, which
the engine already computes as `path_s`. Map truth sid → recorded session through the seed log or
the client_id.

### F12 (Low): B3 defines {t} differently from §2

**What:** B3 says "{t}% of multi-visit journeys were split by a seeded cookie or session break".
§2 and the always-shown line define {t} as the share of *unattributable conversions* touched by
any of seven classes.

**Impact:** none on this build (branch B2). It is wrong if B3 ever ships.

**Fix:** add a distinct slot for B3, or reword it, through a DECISIONS entry.

### F13 (Low): CPCs are a by-product of the spend draw, not a model

**Evidence:** CPC = Dirichlet spend ÷ sessions. That gives:

| Campaign type | CPC |
|---|---|
| Non-brand search | $0.83–0.85 |
| Brand search | $0.52 |
| Shopping | $0.67 |
| Meta prospecting | $0.61–0.63 |
| Meta retargeting | $1.05–1.06 |
| TikTok | $0.96 |

The ordering is plausible. The non-brand level is low for 2026 food search. Nothing ties CPC to
campaign type, so a re-draw could invert brand vs non-brand.

**Fix:** derive spend as clicks × a CPC drawn from type-specific ranges, then rescale to the
pinned 45/40/15 platform split.

## Response (builder)

| Finding | Response |
|---|---|
| F1 | **Fixed (engine).** `{p1}/{p2}/{p3}` count recorded visits in the window (any channel), matching the copy; `{share}` uses the same one-visit population. The build now refuses to ship B2 unless "{X} takes the largest share among paid campaigns" is true. Logged as a definition repair. |
| F2 | **Fixed (generator, v1.1 stream).** Pre-quarter users with minted-earlier client ids, continued `ga_session_number` and no `first_visit`. Retargeting, abandoned-cart and welcome traffic require history. ~10% of orders are repeat orders. 35% of buyers browse after buying. Session numbers count pre-quarter sessions. A June export is **kept out**: the export window is the quarter, stated on the page. |
| F3 | **Fixed.** The PayPal return comes after 31–120 min idle. All of a user's sessions are spaced at least 1 h apart. The bounds check adds the 30-minute rule (0 violations) and a per-channel funnel row, excluding seeded A5 returns per DECISIONS. |
| F4 | **Fixed.** A1, A2a, A2b and A7 are assigned per link: ad, ad group, email send or flow step. Each bad link carries one fixed string. Realized rates stay at the pins. |
| F5 | **Fixed:** per-campaign CTR from type-ordered ranges; a per-campaign A9 multiplier with the aggregate held at exactly 1.20; daily spend rows; affiliate billed as commission. **Kept (owner call):** no non-defect click loss; the footnote says untraced spend counts only seeded defects. |
| F6 | **Fixed.** Weekly newsletter sends (Thursdays plus a Labor Day send) with decay. M01 launches Aug 17, T01 pauses Aug 3–16, G03 is boosted in September. Labor Day weekend lift. Hour weights in America/New_York; `event_date` in property time. |
| F7 | **Fixed:** microsecond timestamps; cents prices; `items` as SKU:qty:price; shipping and tax fields; `view_item` on real product URLs; page_views for cart, checkout and thank-you; engagement bounded by dwell (and absent on some bounces); per-channel depth; ~90-char gclids; `page_referrer`, geo, OS and platform. **Kept:** no `user_engagement`/`scroll` events or nested `event_params` (flattened export by design). |
| F8 | **Fixed.** Device first, then browser conditional on device. Safari stays about 30.4–30.5%. |
| F9 | **Fixed.** Three bot profiles (click-fraud, single-hit, crawler) with mixed devices. Humans also bounce with absent engagement, so no single field separates bots. |
| F10 | **Fixed.** Landing pages are mapped per campaign. |
| F11 | **Fixed.** The ledger, `{t}` and `{u}` use each order's 90-day path window. |
| F12 | **Fixed.** B3 uses the new slot `{u}`, defined in verdict-branches §2. |
| F13 | **Fixed, inverted to respect the pin.** The §1.5 Dirichlet spend split stays pinned. Traffic follows spend ÷ a type-ordered CPC draw, so non-brand always out-costs brand. |
