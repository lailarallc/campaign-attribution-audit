# campaign-attribution-audit — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

[No architecture decisions yet.]

---

## Data & Schema

### 2026-10-16 — Anchors are research-only; the PRACTITIONER class is withdrawn for this repo
- **Why:** Owner decision. No practitioner interview here; PRACTITIONER stays a rebate-repo convention only. The nine standard tracking-defect classes are kept as the taxonomy, and every one must stand on published sources.
- **Policy:**
  - **Existence:** every defect class is CITE-backed (Google/platform docs, auditor write-ups, published studies).
  - **Rates:** CITE where a rate is published. Otherwise an **A-tag** (ASSUMED: Claude's labeled best guess, owner-accepted, weaker than CITE), bounded by any citable aggregate. Aggregates are bounds, never divided into per-class rates.
  - **Decision-impact filter:** a class gets a hygiene-audit-page slot only with a documented case of it changing or distorting a budget/channel decision. No documented case → footnote, with the demotion and its reasoning recorded per class in `docs/defect-taxonomy.md`.
- **Scope:** global (taxonomy, generation criteria, hygiene-audit view).
- **Do not:** label anything PRACTITIONER in this repo. Present an A-tag as a citation. Divide a published aggregate into per-class rates. Pick a rate to make the demo dramatic.

### 2026-10-16 — No element mirrors any real client's data or account structure
- **Why:** Hard guardrail from the brief. Invented brand, invented campaigns, invented account structure. Rates come from published sources, not from any client.
- **Scope:** global.
- **Do not:** model campaigns, naming conventions, spend levels or results on any real program operator or client the owner has worked with, or any other real account.

### 2026-10-16 — Hygiene-page slot test relaxed from strict-case to mechanism-or-case (test B)
- **Decision:** a defect class earns a hygiene-audit-page slot with a documented decision case **or** a Google-documented mechanism by which it moves conversion credit or conversion counts. The page carries a "documented case" column: Uber/Frisch on the bot row, "none published" stated plainly on every other row.
- **Why:** strict-case, applied as written, left 1 of 9 classes on the page. The research found published decision cases only for large public ad-fraud events (Uber, Chase, P&G). The cause is **publication bias**: budget misallocations from tag-level tracking defects are not publishable events. Companies fix them quietly, and agencies don't publish their clients' mistakes. The absence of a published case is therefore not evidence that a class is noise, and the strict rule couldn't tell the two apart. Google's own documentation of the mechanism is the strongest available evidence that a class reaches the numbers budgets are set on.
- **Rejected:** A (as written: honest but leaves a one-class "ledger"). C (empirical in this dataset: lets A-tag rates decide page content).
- **Scope:** `docs/defect-taxonomy.md`, hygiene-audit view.
- **Do not:** cite a mechanism as if it were a decision case. Drop the "none published" text to make a row look stronger. Admit a class on a vendor-only mechanism (2a stays a footnote for that reason).

### 2026-10-16 — Verdict grammar: "your top campaign depends on a rule nobody chose"
- **Decision:** the tool computes four transparent rules itself (last-click, first-click, linear, position-based). The copy names the Nov 2023 removal: GA4 replaced the dropdown with a default no one can audit. The four rules are the checkable bracket around that black box. Every number on the page is reproducible by hand. Data-driven attribution appears only as the thing you can't reproduce, cited to [Google's doc](https://support.google.com/analytics/answer/10596866) ("no longer available as of November 2023").
- **Why:** owner decision. The removal strengthens the story. Comparing GA4's own models would rest the flagship on a model that can't be checked, which is what this portfolio exists to refuse.
- **Rejected:** comparing GA4's current models (DDA vs the last-click variants).
- **Scope:** verdict view, all copy.
- **Do not:** say "dropdown" as if the four rules are still in GA4. Present any DDA number as computed by us.

### ~~2026-10-16 — Universe wears the Cinderhaven DTC identity; data is standalone~~ — REVERSED same day, see "Universe identity reversed" below
- **Decision:** the brand is Cinderhaven's DTC channel ("the same brand, through the marketing lens"). The dataset lives in this repo with zero dependency on Cinderhaven canon.
- **Scope:** universe, README (Cinderhaven context section applies).
- **Do not:** import or reconcile figures from Cinderhaven canon. Any shared-looking figure is coincidental and must not be presented as canon.

### 2026-10-16 — Public name: Campaign Math (campaignmath.lailarallc.com)
- **Decision:** the tool is **Campaign Math**, subdomain `campaignmath.lailarallc.com`. The repo stays `campaign-attribution-audit` permanently.
- **Why:** owner pick. A CEO reads it instantly ("the math on our campaigns"), and it fits the family (Lift Math, Slot Math).
- **Rejected:** Credit Math, Click Math, Track Math, Spend Math.

### 2026-10-16 — Design gate pinned
- **Decision:** `docs/design-gate.md` is pinned. The owner accepted every A-tag (A1–A9) and the §2/§3 A rows.
- **Do not:** change a pinned criterion or rate without a DECISIONS entry whose reason is not the verdict. Retune rates after seeing output.

### 2026-10-16 — 20-row owner eyeball gate replaced by an independent adversarial realism review
- **Decision:** a fresh, read-only session reviews the generated universe against the pinned criteria and writes `docs/realism-review.md` (verdict plus findings plus response table). This is the rebate repo's exact pattern, substituted for the same reason. Owner sampling is optional.
- **Do not:** answer a realism finding by changing defect rates.

### 2026-10-16 — Universe identity reversed: fresh invented brand, Quellwood Provisions
- **Decision:** the universe is **Quellwood Provisions**, an invented small-batch specialty-food DTC brand. It is not Cinderhaven. This reverses the Cinderhaven-identity entry above.
- **Only the identity moves.** Pinned scale, AOV, spend split and A-tags A1–A9 are unchanged.
- **Why (office-hours panel finding, verified):**
  - Canon DTC is **$182,672 gross for CY2025 on 5,962 orders** (AOV ≈ $31), per `cinderhaven-data-platform/reference/canonical_values.yml:349-353, 505-508`. channel-profitability-analysis shows it live.
  - The pinned universe is ~$500K **per quarter** at an $80–120 AOV, an ~11x mismatch. A skeptical reader finds it in two clicks.
  - Conforming to canon (~$45K quarters, AOV $31, ~7 events for A4b) guts the dollar grammar.
  - A visible scope-exception disclaimer on a tool whose claim is "every number reproducible" refutes itself.
  - Upside: this lane's buyers aren't CPG-only, so a non-Cinderhaven DTC brand widens who recognizes themselves.
- **Distance discipline (Galewick pattern):** no real company.
  - Name web-screened 2026-10-16: exact-match searches for "Quellwood" and "Quellwood" + food/pantry/provisions returned no business, brand or product.
  - A trademark check (USPTO) is required before launch.
  - Products, campaign names and naming conventions are invented. Within-campaign parameters are seeded draws (`docs/design-gate.md` §1.5).
- **Scope:** universe, all copy, README. The README omits the Cinderhaven context and data-contract sections.
- **Do not:** use the Cinderhaven name, products, retailers or figures anywhere in this repo's output. Vendor the Cinderhaven canon here.

### 2026-10-16 — Attribution definitions pinned so neither "last-click" nor "top campaign" is a tuning lever
- **Decision:** `docs/design-gate.md` §1.5:
  - Last-click = last non-direct click. Direct is removed from paths for all four rules alike. Direct-only paths go to an unattributable Direct bucket. 90-day lookback.
  - Top campaign = the paid campaign with the highest attributed revenue (not ROAS). No tiebreak.
  - Conversions are deduplicated on `transaction_id` as GA4 does.
  - Campaign match is case-insensitive and trimmed. Anything else is Unmatched.
  - 15-campaign roster pinned, with the within-platform split drawn from a derived seed.
- **Why:** the office-hours verdict critic found both terms undefined. Strict last-click could make "(direct)" the top campaign. An unpinned ranking metric, winner set or campaign allocation could each be picked after seeing which rule wins.
- **Do not:** change any §1.5 definition after generation without an entry whose reason is not the verdict.

### 2026-10-22 — Re-review FAIL (R1) answered; A1's recording mechanism corrected to GA4 behavior
- **Re-review (independent):** FAIL on R1 alone (history the export couldn't contain). The engine was re-derived exactly. All R1–R8 are answered in `docs/realism-review.md`.
- **A1 mechanism (R3).** Untagged paid-social clicks keep the social referrer, so GA4 records a social referral (Organic Social), not Direct. Untagged email still falls to Direct. The **rate (6%) is unchanged**. `docs/defect-taxonomy.md` A1 text said "(direct)/(none)"; that was wrong for social, and the change follows Google's channel rules, not the verdict.
- **Downloads.** The event export (31 MB) exceeds Cloudflare Pages' 25 MB per-file limit, so it ships as three monthly files. Joined, their rows reproduce the manifest hash exactly (verified).
- **Result (mechanical):** still B2. τ-b 0.545 now fails Leg 3 as well as Leg 2. Leg 1 holds, so the branch is unchanged. Bounds 41/41.

### 2026-10-22 — Realism review FAIL answered in generator, engine and bounds check; rates and pins untouched
- **Review:** `docs/realism-review.md` (independent session). Verdict FAIL with 13 findings. The engine math was reproduced exactly. Every finding is answered in the response table appended to that file.
- **Measure repairs (definitions, not verdict-driven):**
  - F1: `{p1}`/`{p2}`/`{p3}` now count recorded *visits* (the copy's own words), and `{share}` uses the same population.
  - F12: B3's split statistic gets its own slot, `{u}`.
  - F11: the ledger, `{t}` and `{u}` count each order's 90-day path window, not the buyer's whole history.
- **Bounds-check rows added:**
  - F3: a 30-minute session rule. The per-channel funnel row is evaluated **excluding seeded A5 gateway-return sessions**, because a purchase with no begin_checkout is that defect's real signature. It is a logic row, not an A row.
  - F2: retention-channel first visits must be explained by an A8 reset. Repeat buyers must exist.
  - F5: the A9 aggregate is held at exactly 1.20.
- **New structural randomness comes from a separate v1.1 stream** (`roll_parameters.py` `v1_1`, generator `SEED11`). Every v1.0 draw is unchanged (verified).
  - Traffic inside each platform now follows the pinned Dirichlet spend divided by a type-ordered CPC draw (F13). The pinned spend split is not overridden.
  - Within-platform CVR multipliers are renormalized to the realized traffic mix, so each benchmark group holds its ThoughtMetric level (their stated intent). Without that, retargeting's cheap traffic pushed paid social above paid search.
- **Kept, owner call (F5):** no non-defect click loss was added. It would be a new unpinned rate, and it moves `{U}`. The page footnote states that untraced spend counts only the seeded defects, so a real account's gap would be larger.
- **Result after fixes (mechanical):** still **B2**: same top under all rules (`qw_search_brand`), 6 wide ROAS ranges, τ-b 0.758. Bounds check 41/41.

### 2026-10-22 — Post-generation copy corrections (accuracy only; branch and thresholds untouched)
- **Context:** the engine selected **B2** mechanically. All four rules name `qw_search_brand` top. Leg 2 failed (5 paid campaigns have ROAS max/min ≥ 1.5). Kendall τ-b is 0.606 (Leg 3 holds).
- **Slot rule added for `{Z}`.** The pre-registration left open which campaign's ROAS range B2 quotes. Pinned to the mechanical reading: the paid campaign with the widest max/min ROAS ratio (M02 here). Recorded as made after generation.
- **False clause removed.** The pre-registered B2 sentence "…and {X} closes most of them" is false in this data. `qw_search_brand` takes 11.6% of one-visit revenue (21.2% of paid one-visit revenue; organic search takes more). Replaced with the true, computed statement: "…and among paid campaigns, {X} takes the largest share of those one-visit sales ({share}%)."
- **Why this is not tuning:** the branch, legs and thresholds are untouched. The only change replaces a sentence that would have printed a falsehood.
- **Do not:** print any pre-registered clause without checking it against the computed result.

### 2026-10-22 — Office-hours forks A, B, C adopted as written; copy branches pre-registered
- **A, bank rule:** bank (do not ship) only if all three hold:
  - every rule names the same top paid campaign;
  - fewer than 3 paid campaigns have ROAS max/min ≥ 1.5;
  - Kendall τ-b (first-click vs last-click ranks) ≥ 0.6.
  Otherwise ship branch B1 (top differs) or B2 (top holds, order moves). **Owner rider:** the rules-agree branch (B3) presents agreement as a plain finding about this book ("on this data the four rules mostly agree — here's why"), never spun or buried.
- **B, verdict lead:** dollars first (untraced spend), then "which campaign worked best depends on a rule nobody chose."
- **C, presentation:** top 4 hygiene classes by revenue at full size, the rest expandable with the documented-case column kept, plus a "measurable floor" line for retail-led brands.
- **Pre-registration:** `docs/verdict-branches.md` is committed before any generator code. It holds the selection rule, measure definitions and verbatim copy.
- **Scope:** verdict view, hygiene view.
- **Do not:** edit branch copy, thresholds or measure definitions after generation without an entry whose reason is not the verdict. Ship BANK without an explicit owner override.

### 2026-10-16 — Brief leans adopted (no owner objection)
- Four rules, no time-decay. The hygiene audit quantifies dollars (spend sitting on unattributable traffic). One fixed calendar quarter, stated on every view.

---

## Visualization

[Chart conventions, palette decisions, interactivity choices]

---

## Output Formats

[Decisions about deliverable formats, structure, organization]

---

## Writing & Voice

[Voice, style, terminology decisions specific to this project]

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
