# Disease Map

A pet project: an interactive map of human diseases, showing where humanity has the upper hand and where it doesn't yet, with a **front line** between the two and **progress bars** that reflect the real state of research.

Inspiration: [changelog.earth](https://github.com/byalex33/changelog.earth). Real-world data, refreshed by an automated LLM-assisted pipeline, committed as JSON in the repo.

## Goals

- **Portfolio / learning project first.** Data must be credible and sourced, not exhaustive. Built so it could become public later.

## Glossary

- **Territory**: a group of diseases drawn as a region on the map. Territories nest: zooming into a territory splits it into smaller territories or provinces. The nesting follows the ICD-11 hierarchy (chapter → block → … → disease).
- **Province**: a single disease, the leaf of the map.
- **Status**: where a disease stands on the 5-level scale (see [ADR 0001](docs/adr/0001-five-level-status-scale.md)):
  1. **Eradicated**: gone from the human population (smallpox).
  2. **Curable**: a treatment removes the disease (hepatitis C, most bacterial infections).
  3. **Controlled**: patients live near-normal lives on ongoing treatment (HIV, type 1 diabetes).
  4. **Treatable**: treatment slows it or eases symptoms (many cancers, MS).
  5. **Untreatable**: no therapy changes the disease's course (ALS, prion diseases).
- **Front line**: the border between statuses 1–3 (**held**) and 4–5 (**contested**).
- **Provisional status**: a status a province inherits from its GBD cause's assessment, shown in a lighter shade. An individual assessment of the province overrides it.
- **Fog**: provinces with no status at all, neither assessed nor provisional (e.g. no GBD cause covers them). Shown honestly as unknown rather than hidden, at the minimum province size.
- **Burden**: disability-adjusted life years (DALYs) from the Global Burden of Disease study. Sets a province's size.
- **Progress bars**: three per province, each from its own source:
  - **Pipeline**: for a held disease, "approved". For any other disease, how far the most advanced candidate therapy still in trials has got (no registered trial → Phase 1 → 2 → 3), counting only trials still running (recruiting or active). From ClinicalTrials.gov.
  - **Activity**: how much research is happening (active trials, publications).
  - **Access**: share of patients who actually receive the available treatment. Data is patchy.

## Decisions so far

- **Taxonomy**: ICD-11 is the map. Its chapters and blocks are territories and its diseases are provinces, down to the deepest level (see [ADR 0002](docs/adr/0002-icd11-is-the-map.md)). Provinces are assessed in burden order, biggest first; unassessed ones stay in fog.
- **Scope**: diseases only. Left out: GBD's injuries group, and the ICD-11 chapters that aren't diseases (symptoms and signs, injuries and external causes, factors influencing health, special purposes, traditional medicine, functioning, extension codes). Pregnancy-related conditions stay.
- **Residual entries**: ICD-11 "other specified" and "unspecified" entries are not provinces. Their parent's burden is split among the real diseases only.
- **Assessment level**: statuses are assessed per GBD cause and inherited as provisional by every province under it. A disease can also be assessed directly (e.g. smallpox, which no GBD cause covers); that status overrides the inherited one and is not provisional.
- **Province size below GBD level**: GBD reports burden for ~370 causes. Every ICD-11 disease traces back to exactly one GBD cause (via its ICD-10 codes), and provinces under the same cause split its burden equally. Such sizes are marked "size estimated".
- **Straddling diseases**: a province gets the status of a typical patient at diagnosis; the nuance (e.g. "curable if caught early") goes in its info panel.
- **Bars and missing data**: every province shows all three bars; a bar with no data is greyed out as "no data". Activity is shown as a percentile across all diseases.
- **Tech stack**: chosen for fit, not familiarity. A Python data pipeline writes static JSON; a TypeScript front end (Vite + D3) draws the map; deployed as a static site. No database, no server.
- **Update cadence**: a weekly scheduled job refreshes the bars and commits them automatically. Proposed status changes arrive as a pull request; the front line moves only when the owner merges.
- **Disease → trials mapping**: the LLM drafts a list of MeSH terms per GBD cause once; the owner reviews it; it's stored in the repo and reused by every run.
- **LLM**: Claude with its web search tool, so every proposed status cites a real source.
- **Visual style**: modern strategy-game map, with clean flat colours by status. Other themes may come later.
- **v1 scope**: the full ICD-11 map (minus exclusions) drawn and sized, provisional statuses for every GBD cause on the map plus a few direct assessments, the pipeline bar only, no automation.
- **Map layout**: a continuous world, with every province on one pannable, zoomable map; each block is cut into held | contested | fog bands before its provinces are laid out (see [ADR 0003](docs/adr/0003-continuous-world-layout.md)).
- **Zoomed-out front line**: a territory's front line sits at the share of its burden held (statuses 1–3). The same geometry applies at every zoom level.
- **Hosting**: GitHub Pages, published by the same job that commits the data.
- **Province info panel**: name and position in the hierarchy; status with source link and nuance; the three bars; burden in DALYs; history from the events log; "size estimated / data as of" notes.
- **History**: every status change is recorded in an events log ("2014: hepatitis C, Treatable → Curable"). It feeds a "news from the front" feed and, later, a timeline replay.
- **Map metaphor**: a fantasy-style territory map, with territories as regions, diseases as provinces, and the front line as a literal border. A history timeline is a possible later addition.
- **Layout**: inside each territory, provinces are arranged by status, so held provinces sit on one side and contested ones on the other. The front line is one clean line per territory. A status change reshuffles the layout, and that's intended: it shows territory being won.
- **Province size**: proportional to burden, with a minimum size so rare diseases stay clickable.
- **Status assignment**: an LLM proposes a status with a mandatory source, a validator checks the source exists, and a rule-based cross-check against approved drugs (ChEMBL / DrugBank) flags disagreements. The owner reviews before anything is committed.
- **Progress bars**: all three bars (pipeline, activity, access) are in scope.
