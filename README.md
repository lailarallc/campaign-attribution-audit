# Campaign Math

<!-- Repo name campaign-attribution-audit is permanent; the tool is Campaign Math. Add **Live:** once deployed. -->

Every marketing report asserts a return on ad spend. The number rests on an attribution rule nobody chose and on tracking data with silent defects. Campaign Math scores one quarter of web orders under four transparent attribution rules (last-click, first-click, linear, position-based), shows each campaign's return on spend as a range rather than a number, and audits the tracking defects that decide how much of the data can be attributed at all.

## What it finds

Quellwood Provisions is an invented specialty-food brand. Its Q3 2026 web data is synthetic, generated from a fixed seed, with nine classes of tracking defect planted at published or stated rates.

- **The verdict.** All four rules name the same top campaign. Below it, the order is a choice. The verdict branch is selected mechanically by a rule committed before the data existed (`docs/verdict-branches.md`).
- **The campaigns.** Paid campaigns' return on spend under every rule, with ranks and ranges.
- **The hygiene audit.** Each defect class's seeded rate, the revenue it touches, and whether a published case exists of it changing a budget decision.

Every number on the page is reproducible by hand from the published event export and daily spend table.

## Method

- Anchors are research-only, cited or labeled assumptions (`docs/anchors-research.md`, `docs/defect-taxonomy.md`).
- Realism criteria were pinned before generation (`docs/design-gate.md`). They were checked by `scripts/bound_check.py` and by independent adversarial reviews (`docs/realism-review.md`).
- Decisions and their reasons are in `DECISIONS.md`.

## Stack

- Python 3.13, standard library only: generator, attribution engine, bounds check.
- SvelteKit 2 static build (`@sveltejs/adapter-static`), Svelte 5, Vite.
- Lailara frame v1.5.1 (vendored CSS and fonts).
- Cloudflare Pages, via the org reusable deploy workflow.

## Run

```
python scripts/roll_parameters.py      # seeded structural parameters
python scripts/generate_universe.py    # regenerate the universe (byte-stable; ~1 min)
python scripts/attribute.py            # four rules, verdict branch, hygiene ledger
python scripts/bound_check.py          # design-gate checks
python -m unittest discover -s tests
python scripts/build_site_data.py && python scripts/split_export.py
npm ci && npm run build
```

CI regenerates the universe and refuses to deploy unless every hash matches `data/manifest.json` and the engine reproduces `data/results.json` exactly.

---

Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.
