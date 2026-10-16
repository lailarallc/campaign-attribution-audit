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
