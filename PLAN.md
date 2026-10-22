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
- [ ] Deploy verified live at campaignmath.lailarallc.com
- [ ] Max's live-site audit
- [ ] Launch: USPTO check, repo public, shared OG card, README Live line

## Why this arc, why now

[One or two sentences. The reason matters when you come back in three
weeks and wonder why this was the priority.]

## Business question this arc answers

[One sentence. Direct connection to the project-level business question
in CLAUDE.md.]

## Tasks

Work in vertical slices — one section/feature end-to-end before moving
to the next. Visualizations get reviewed in their own slice, not
deferred to a polish phase.

- [ ] Specific, scoped, actionable
- [ ] Each one is a thing Claude Code could plausibly finish in one
      session
- [ ] If a task feels too big, break it down before adding it
- [x] Completed items stay struck or checked, so the trail is visible

## Out of scope for this arc

- Things explicitly NOT being done in this round
- Captures the decisions about what to defer
- Prevents scope creep mid-session

## Definition of done for this arc

- [ ] Specific, verifiable conditions
- [ ] Not "the prose is better" — "every section's executive summary
      has been reviewed and either approved or marked for domain
      insertion"
- [ ] When all of these are checked, the arc is done and a new PLAN.md
      arc gets defined

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
