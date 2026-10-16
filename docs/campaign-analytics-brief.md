# Campaign & Web Analytics lane — flagship brief

**Repo:** `campaign-attribution-audit` (private under lailarallc, scaffolded by the owner's standard process; flip public at launch). The repo name is permanent and is not the tool name — the tool's public name gets picked in /clarify and never renames the repo.

**Status:** input to the project process (/ce → clarify → office-hours → plan reviews). The idea and its known forks, not a frozen spec. Open Questions are deliberate /clarify ammunition. House rules: design gate before tool code, intent tests not letter tests, anchors pinned with sources before any data build.

## Why this tool exists

The campaign & web analytics lane of Lailara's three-lane positioning has zero portfolio receipts. This is its flagship: "data hygiene and process hygiene applied to campaign and web analytics" turned from a positioning sentence into a page a marketing-budget owner can click. Feeds the LinkedIn lane rotation.

## The business question

> "Which campaigns actually worked — and can your data even answer that question?"

Every marketing report asserts ROAS. The number rests on two things nobody examines: an attribution rule chosen from a dropdown, and tracking data full of silent defects. The tool makes both visible:

- **The attribution problem:** the same spend and the same conversions, scored under the standard rules (last-click, first-click, linear, position-based), produce different winners. The rule is a choice; the report never says so.
- **The hygiene problem:** missing and malformed UTMs, (not set) rates, duplicate tagging, self-referrals, bot traffic — the defects that decide how much of the data can be attributed at all.

Verdict grammar: "Your top campaign depends on a dropdown: under last-click it's X, under linear it's Y — and Z% of conversions can't be attributed to anything because of tracking defects."

**Honest-both-ways:** some campaigns win under every rule — those are real, and the tool says so at full size. The rest are rule-dependent, and the tool refuses to pick for you. It also shows our own demo data's unattributable share rather than quietly dropping it.

## The truth fork — decide early, lean stated

- **Measurement version (lean — ship first):** rule-disagreement + hygiene audit, both deterministic on observed data. No causal truth needed: computing four attribution rules is arithmetic, and the seeded tracking defects are knowable exactly. Fast, honest, lands the lane's positioning (hygiene!).
- **Scored version (roadmap):** generate user journeys with known true cause per conversion and score each attribution rule against truth, Lift Math-style ("every attribution model, scored against known truth"). Remarkable but heavy — real causal journey modeling, promo-response-scale authoring. Record it as the roadmap differentiator; do not gate v1 on it.

## The universe

Synthetic GA4-style sessions/events plus a campaign spend table, with seeded tracking defects. Open question whether it wears the Cinderhaven brand (Cinderhaven has a DTC channel — "the same brand, through the marketing lens" is a cohesive portfolio story) or a fresh identity; either way it is a standalone dataset in this repo, with zero dependency on Cinderhaven canon.

- Seeded defects deterministic and counted (per the rebate-lane convention: the rules/defects ARE the truth for v1).
- Seed-locked, byte-stable; generation criteria pinned before the build.

**Hard guardrail:** no element may mirror any real client's campaign data, account structure, or results — not any real program operator or client the owner has worked with. Invented brand, invented campaigns.

## Anchors — pinned with sources before the data build

1. Published figures on tracking/data-quality failure rates: (not set) prevalence, UTM error rates, bot-traffic share (industry studies, analytics-vendor benchmarks — CITE with vendor caveat).
2. Attribution-rule disagreement magnitudes from published studies (CITE where they exist; DIRECTION otherwise).
3. Campaign-mix realism: typical channel mix, spend distribution, conversion rates for a small DTC brand (CITE/DIRECTION).
4. ~~**PRACTITIONER anchor class**~~ — **withdrawn for this repo (owner decision, 2026-10-16).** No practitioner interview. Research-only anchor policy (see `DECISIONS.md`):
   - **Taxonomy:** the nine standard tracking-defect classes (`docs/defect-taxonomy.md`). Every class's *existence* is CITE-backed (analytics docs, auditor write-ups, published studies).
   - **Rates:** CITE where published; otherwise an **A-tag** (ASSUMED — Claude's labeled best guess, same convention as the rebate clarify log), bounded by any citable aggregate. Aggregates are bounds, never divided into classes.
   - **Decision-impact filter:** a class earns a hygiene-audit-page slot only with a *documented* case of it changing (or demonstrably distorting) a budget decision. No documented case → demoted to a footnote, demotion recorded per class with reasoning.

## Views (working shape — pressure-test it)

1. **The verdict** — 30-second rule: the dropdown problem in one picture — top campaign under each rule, side by side, plus the unattributable share stated at full size.
2. **The campaigns** — per-campaign table: spend, conversions, ROAS *range* across the four rules (a range, not a number — that is the differentiator), flagged rule-dependent vs every-rule winners.
3. **The hygiene audit** — the defect ledger: each tracking failure class, its prevalence in this data, and which campaigns' numbers it poisons. The "can your data even answer this" view — the lane's positioning as a page.

## Design gate — pre-registered, runs first

- Realism criteria for sessions, campaigns, and defect rates pinned from anchors 1–4 before generation; defect rates never chosen to make the demo dramatic. Where the verdict lands, it lands.
- Intent test: 20 sampled sessions/claims eyeballed by the owner for "looks like real GA data."
- The rule-disagreement result is NOT a design input: if the four rules happen to agree on this world, that is the honest result and the copy adapts (the gate's job is realism, not drama).

## Reuse inventory

Lailara frame v1.5.1 + measure/table rules, static precompute stack (all computation at build; no server), org deploy workflow, full social meta + og card from day one, engagement client-mode scaffold (client brings GA4 export + spend sheet; preflight validates), seed-locked data conventions as process.

## Open questions — /clarify ammunition

1. ~~Practitioner interview (anchor 4)~~ — withdrawn 2026-10-16; replaced by the researched, CITE-backed taxonomy (anchor 4 above).
2. Universe identity: Cinderhaven's DTC marketing vs fresh brand (lean: Cinderhaven brand identity, standalone data).
3. Attribution rule set: the four standard rules, or add time-decay? (Lean: four; more rules dilute the picture.)
4. Does the hygiene audit quantify dollars (spend sitting on unattributable traffic) — lean yes, it is the money-leak grammar.
5. Tool name — series voice, before any view scaffolding. Candidates to beat: **Click Math**, **Spend Math**, **Track Math**. Naming decides the subdomain.
6. Window/period convention: one fixed quarter of data, stated (fleet precedent).

## Estimate

Taxonomy research + design gate: one session. Universe build: ~2–3 days. Tool: ~1–1.5 weeks at fleet rigor. Parallel-safe with the rebate build — different repos, no shared dependencies.
