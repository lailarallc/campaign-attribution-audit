# Verdict branches — pre-registered copy (2026-10-22, before generation)

Owner adopted office-hours forks A, B and C as written (`DECISIONS.md` 2026-10-22).
This file is committed **before** the generator exists. The build fills `{slots}` from
computed results and selects a branch with the rule in §1. Nothing here is edited after
generation except through a `DECISIONS.md` entry whose reason is not the verdict.

## 1. Branch selection (computed, not chosen)

Inputs: the 12 paid campaigns (design-gate §1.5 roster). Each has attributed revenue
under each of the four rules (§1.5 definitions) and a ROAS = attributed revenue ÷ spend
under each rule.

- **Leg 1:** all four rules name the same top paid campaign (by attributed revenue; ties compared as sets).
- **Leg 2:** fewer than 3 paid campaigns have ROAS max ÷ min ≥ 1.5 across the four rules. A campaign whose min ROAS is 0 counts as ≥ 1.5.
- **Leg 3:** Kendall τ-b between the first-click and last-click rankings of the 12 paid campaigns (by attributed revenue) is ≥ 0.6.

Outcome:
- **BANK** if Legs 1, 2 and 3 all hold. The tool does not ship. Results go to the owner with branch B3 ready. B3 ships only on an explicit owner override.
- **B1** if Leg 1 fails.
- **B2** if Leg 1 holds and Leg 2 or Leg 3 fails.

## 2. Pinned measures used in the copy

- **Untraced spend `{U}`.** For each paid campaign: spend × max(0, platform clicks − GA4 sessions matched to that campaign) ÷ platform clicks. Summed over paid campaigns. Reproducible from the spend table plus the GA4 session table.
- **Total paid spend `{S}`.** The sum of the spend table.
- **Unattributable conversions `{s}` / `${d}`.** Deduped conversions whose path, after removing Direct (§1.5), is empty or contains only Unassigned, (not set) or Unmatched touches. `{s}` is the share of deduped conversions; `${d}` is their revenue.
- **Defect share `{t}`.** Of those conversions, the share whose path was altered by at least one seeded defect (from the seed log).
- **Why-mechanics `{p1}` / `{p2}` / `{p3}`.** ~~Shares of deduped revenue whose recorded path has 1 touch, 2 touches, and 3+ touches.~~ **Repaired 2026-10-22 (realism review F1):** shares of deduped revenue whose buyer has exactly 1, exactly 2, and 3+ recorded **visits** (any channel, Direct included) in the 90-day window. That matches the copy's wording, "one recorded visit". `{share}` = `{X}`'s share of the same one-visit revenue. `{u}` (B3 only) = share of multi-visit purchase journeys split by a seeded cookie reset (A8) or a gateway return (A5).
- **Rank movers `{n}` of `{m}`.** Paid campaigns whose rank moves 2+ places between any two rules, out of `{m}` = 12.

## 3. Lead (fork B: dollars first) — always shown, first

> **{U} of this quarter's {S} in paid spend bought clicks that Quellwood's analytics can't tie back to the campaign that paid for them.**

Second line, then the branch body:

> And which campaign worked best depends on a rule nobody chose.

In branch B3, the second line is replaced by the B3 body.

## 4. Branch bodies

**B1 — top campaign differs under at least one rule**

> Last-click names {X}. First-click names {Y}.{ Linear names {Z}.}{ Position-based names {W}.} Each answer is arithmetic on the same quarter of data, and each can be checked by hand. None of them is wrong. The report you get depends on which one somebody picked.

(Only rules naming a top campaign different from last-click get a clause. Rules that agree with last-click are named in one closing clause: "{Rule} agrees with last-click.")

**B2 — every rule names the same top campaign, the order below it moves**

> Every rule names {X} the top campaign. That result is real. Below it, the order is a choice: {n} of {m} paid campaigns move two or more places depending on the rule, and {Z}'s return on spend runs from {lo} to {hi}.
>
> Why the top holds: {p1}% of revenue comes from customers with one recorded visit, where every rule gives the same answer by arithmetic, and among paid campaigns, {X} takes the largest share of those one-visit sales ({share}%).
>
> _(Corrected 2026-10-22 after generation: the pre-registered clause "and {X} closes most of them" was false in this data. See DECISIONS. `{Z}` = the paid campaign with the widest ROAS max/min ratio.)_

**B3 — the four rules mostly agree (ships only on owner override of BANK)**

> On this data the four rules mostly agree. Here is why: {p1}% of revenue comes from customers with one recorded visit, where every rule must give the same answer. Another {p2}% comes from two-visit journeys, where position-based and linear are identical by construction. Only {p3}% of revenue comes from longer journeys, the only place the rules can disagree, and tracking breaks shorten some of those: {u}% of multi-visit journeys were split by a seeded cookie or session break. _(Slot was `{t}`, which §2 defines differently; renamed `{u}` 2026-10-22, review F12.)_ The rule barely matters this quarter. Tracking decides the numbers instead.

## 5. Always-shown lines

> **Every-rule winners:** {list} rank in the top {k} under all four rules. Fund them without argument.

(If the list is empty: "No campaign ranks in the top {k} under all four rules.")

> **Unattributable:** {s}% of conversions, ${d} in revenue, reach no campaign or channel at all. {t}% of those got there through a tracking defect, seeded at the published or stated rate listed below.

> **GA4:** Since November 2023, GA4 offers no first-click, linear or position-based model. Its default is data-driven attribution, which cannot be reproduced outside Google. These four rules can be, and they bracket it.

> **Measurable floor (fork C):** For a brand that sells mostly through retailers, this is the slice of marketing where the math can be checked. Most ad money also moves shelf sales that web analytics never sees.

> **Synthetic data:** Quellwood Provisions is an invented brand. Its quarter of data is generated from a fixed seed, with tracking defects planted at the rates listed below. The method is real.

## 6. Hygiene page order (fork C)

- **Ranking metric:** revenue of deduped conversions whose path contains at least one instance of the class (class 4: duplicate revenue in the raw export; class 9: platform-reported revenue in excess of GA4).
- **Top 4** by that metric show at full size. The rest sit under "Other defects found" (expandable). The documented-case column ("Uber / Frisch" or "none published") stays visible in the expanded view.
- **Class 2a** stays a footnote regardless of rank (test B).
- Every class line says "seeded at {rate}" and "results in {effect}", never "we found."
