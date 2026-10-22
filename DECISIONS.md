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
