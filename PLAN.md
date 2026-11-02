# campaign-attribution-audit — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Build the pinned, seed-locked universe for **Campaign Math** and get it through the gate.
The tool's job, which this arc serves: four transparent, hand-reproducible attribution
rules that bracket GA4's un-auditable default.

- **Tool:** Campaign Math (`campaignmath.lailarallc.com`). The verdict is "your top campaign depends on a rule nobody chose", plus the unattributable share at full size, in dollars.
- **Universe:** Quellwood Provisions, an invented specialty-food DTC brand (identity reversed at office hours; see DECISIONS). GA4-export-shaped, one fixed quarter, ~$500K online revenue. True journeys come first, then a tracking layer seeds 9 defect classes, exactly logged.
- **Hygiene page:** 9 rows under test B with an honest "documented case" column (Uber on one row, "none published" on the rest). Class 2a goes in a footnote.
- **v1 = measurement version.** The version scored against true journeys is roadmap.
- **Done for this arc:** the gate is pinned (done 2026-10-16), the universe is built and passes `docs/design-gate.md` §2–§5, and the independent adversarial realism review (§6) returns PASS or PASS WITH FINDINGS with every finding answered.

_Confirmed by the owner at /clarify, 2026-10-16._

## Forks — /clarify (2026-10-16) — all resolved, see DECISIONS.md

Asked now:
1. **Hygiene-page slot test.** Applied as written, the decision-impact filter leaves 1 of 9 classes on the page (bots, via Uber). Options A/B/C are in `docs/defect-taxonomy.md`. Recommended: **B**, a documented case *or* a Google-documented mechanism that moves conversion credit, with an honest "documented case" column.
2. **Verdict grammar.** GA4 removed first-click, linear, time-decay and position-based in Nov 2023 (Google doc, READ). "Your top campaign depends on a dropdown" is stale. Recommended: keep the four transparent rules, computed by the tool, and reframe as "depends on a rule nobody chose." GA4's default data-driven model is named as the black box the four rules bracket.
3. **Universe identity.** Cinderhaven's DTC brand vs a fresh brand. The brief leans Cinderhaven identity with standalone data.
4. **Tool name.** Candidates: **Credit Math** (recommended: attribution *is* credit assignment, Google's docs use the word, and the hygiene half is "credit nobody can assign"), Click Math, Track Math, Spend Math. The name decides the subdomain.

Taking the brief's lean unless the owner objects:
5. Rule set: the four standard rules, no time-decay.
6. Hygiene audit quantifies dollars (spend sitting on unattributable traffic).
7. One fixed calendar quarter, stated on every view.

Gate inputs awaiting owner acceptance: A-tags A1–A9 plus the §2/§3 A rows in `docs/design-gate.md`, and a citable Safari share for A8.

## Status (2026-10-22)

- [x] Gate pinned; attribution definitions pinned; verdict branches pre-registered
- [x] Universe generated, byte-stable; bounds 43/43
- [x] Independent adversarial realism review: PASS WITH FINDINGS (third pass), all findings answered
- [x] Static site built on frame v1.5.1, checked at 1440 and 375
- [x] Deploy verified live at campaignmath.lailarallc.com (2026-11-02)
- [x] Max's live-site audit (3 fixes shipped 2026-11-02)
- [x] USPTO screen for "Quellwood": 0 live / 0 dead (2026-11-02)
- [x] README Live line; case study live at lailarallc.com/work/campaign-math
- [x] Max's sign-off on tool and case study (2026-11-02)
- [x] Pre-publish code review + /improve pass (2026-11-02)
- [x] Repo public (owner y, 2026-11-02)
- [ ] Shared OG card (lailara-website manifest entry, then switch og:image)

## Why this arc, why now

Campaign Math is the flagship of the campaign and web analytics lane. A buyer cannot trust a
ROAS figure until the rule and the tracking under it are visible; this arc ships that proof.

## Business question this arc answers

Which campaigns actually worked, and can your data even answer that question?

## Tasks

- [x] Pin the gate, definitions and verdict branches before any data
- [x] Build the universe, engine, bounds check and static site
- [x] Pass the independent adversarial realism review
- [x] Deploy to campaignmath.lailarallc.com; Max's audit fixes
- [x] Public flip (owner, 2026-11-02)
- [ ] Shared OG card

## Out of scope for this arc

- Client mode (scoring a buyer's own export). Roadmap.
- v2 scored against true journeys. Roadmap.
- Non-defect click loss (review F5): accepted as zero, stated on the page.
- SvelteKit 3 / adapter-static 4 major upgrades (deferred, 2026-11-02 improve pass).

## Definition of done for this arc

- [x] Gate pinned; bounds 43/43; realism review PASS WITH FINDINGS, all answered
- [x] Live site matches HEAD; CI regenerates and hash-gates every deploy
- [x] Max's sign-off on tool and case study
- [x] Repo public; README Live line resolves

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.

### [Date completed] — [Goal]
- Outcome: [what shipped or what was decided]
- Tag: [git tag if one was created]

---

## Improvement history

Track when this project was reviewed and improved via /improve.
Each entry records what was found, what was fixed, and when to
check again.

<!-- Entries are added by /improve — don't delete this section -->

### 2026-11-02 — Improvement pass (pre-publish)
- **Trigger:** owner-initiated, as part of the /publish gate
- **What was reviewed:** all code (6-reviewer /ce:code-review: correctness, security, Python, testing, maintainability, standards), workflow files, deps, README, git hygiene; gitleaks over full history
- **What was fixed:** method copy now discloses post-generation corrections; $8,440 footnote wording; A8 card states its 16,678 pre-quarter resets; `select_branch()` extracted with threshold tests (26 -> 38 tests); cf-domain.yml removed; dead code and stale comments; PLAN.md template filled; FAILURES.md backfilled
- **Deferred:** channel_group full-label and credit_key branch tests; `secrets: inherit` -> explicit secrets (fleet pattern, org workflow); roll_parameters ctr_pct basis text (needs parameters.json regen); Frisch source on the bot footnote; spend.csv contiguity assumption; bot sessions on bad links not in seed log; GoatCounter SRI/CSP; dependency major upgrades
- **Next review:** 2026-12-02
