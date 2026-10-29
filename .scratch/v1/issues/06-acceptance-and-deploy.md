# 06 · Acceptance pass and first deploy

**Blocked by:** 04, 05
**Spec:** "Acceptance criteria"

## What to do

- Run `python -m pipeline all` from a clean checkout, and fix anything that only worked thanks to leftover local files.
- Go through the spec's 8 acceptance criteria one by one and record the result of each in this ticket.
- Performance: measure load-to-interactive and panning smoothness on a mid-range laptop. If over 3 s, or panning stutters, precompute the layout in stage 8 and/or switch rendering to Canvas.
- "Data as of" dates show for every source in the info panel.
- `npm run build` and publish `site/dist/` to GitHub Pages by hand. This needs a GitHub repo, so create one first.

## Done when

- All 8 acceptance criteria pass, or each failure has its own follow-up ticket.
- The site is live on GitHub Pages and the URL is in a README.

## Results (2026-10-29)

### Fresh-clone rebuild

`python -m pipeline all` was run in fresh clones of this branch: once with no raw files, once with only the IHME files in `data/raw/gbd/`. Both runs took about 2 s, made no ClinicalTrials.gov requests, and left `git status` clean. A forced rebuild (`--force`, all raw files present) reproduced every committed output byte for byte.

Fixed along the way, since a fresh clone had only worked thanks to leftover local files:

- **Stage 7 re-queried ClinicalTrials.gov for about 10 minutes.** A clone gives every file its checkout time as mtime, so mtime freshness reran stages whose committed outputs were fine. Stages now record content hashes of their inputs and outputs in `data/stamps.json`, with line endings normalised for CRLF checkouts, and skip while those match.
- **Stage 6 dropped smallpox from `data/assessments/INDEX.md`** when there were no drafts. Existing assessment files now count as subjects too.
- **Stage 2 aborted the whole run without the IHME files.** Stages 4, 5 and 6 now skip themselves when their Claude-session inputs (GBD files, drafts) are missing, and the committed outputs stand.
- **Windows:** cloning into a deep path fails on long proposal file names unless `core.longpaths` is on. The README says so.

The README table "What a fresh clone can rebuild" lists, per stage, what a fresh clone can and can't rebuild.

### Acceptance criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `pipeline all` runs 1–8 or skips up-to-date stages, produces `map.json` | **Pass** | Fresh-clone runs above. With every input present, `--force` regenerates the same files. |
| 2 | All disease chapters except excluded ones; province count matches `tree.json` | **Pass** | 20 chapters drawn (01–20). 6,633 provinces drawn = `tree.json` counts (20 chapters, 2,318 territories, 6,633 provinces). |
| 3 | Every province's size traces to a GBD cause or is the minimum size, and the panel says which | **Pass** | 5,625 sized from a GBD cause ("size estimated" when split). 5 under a cause GBD gives no DALYs (panel: "GBD gives this cause no DALYs; minimum size"). 1,003 with no cause (panel: "minimum size: no GBD cause covers this disease"). No other cases. |
| 4 | Every GBD cause on the map has an approved status with a working source; provinces with neither cause nor assessment are fog | **Pass** | 242 of 242 causes on the map are approved, plus smallpox assessed directly (243 files). All 335 distinct source URLs answered HTTP 200 when re-checked today. 5,629 provinces inherit their cause's status as provisional and 1 is assessed directly. The 1,003 with neither are fog. |
| 5 | Every block with held and contested provinces shows exactly one straight front line | **Pass** | 95 groups of sibling provinces hold both sides, and there are 95 front-line segments, one straight segment each. `layout.test.ts` checks this on real data. |
| 6 | Clicking any province opens the panel with all fields; missing data reads "no data" | **Pass** (after a fix) | All 6,633 province panels and 2,338 territory panels were rendered by script. Each province panel has code, hierarchy, URI, status, sources, burden, GBD cause, "data as of", and the pipeline, activity and access bars. None contains blank values or "undefined"/"NaN"/"null". Fixed: fog provinces had no Sources row; they now show "Sources: no data". |
| 7 | Loads and becomes interactive in < 3 s on a mid-range laptop; panning is smooth | **Pass** (after a fix) | See below. Before: 4.8–5.5 s and ~20 fps panning at 4× CPU throttle. After: 1.9–2.3 s, panning p95 ≤ 21 ms. |
| 8 | Same data, same map on every load | **Pass** | The layout is precomputed at build time, so every load draws the same polygons. A hash of every province polygon was identical across loads: 4 headless loads before the change and 10 after. The before and after hashes differ only because precomputed coordinates are rounded to two decimals. Dev mode, which computes the layout live, puts the same province at the same spot. |

### Performance

Measured in headless Edge 152 at 1366×768 over the DevTools protocol (`Emulation.setCPUThrottlingRate`), serving the production build locally. The dev machine has 16 cores, so **4× throttling stands in for a mid-range laptop**; no real mid-range laptop was tested. "Interactive" is when the zoom behaviour is attached and the first frame is drawn. Panning is a 60-step mouse drag, with frame times from `requestAnimationFrame`.

| Build | CPU | Interactive | Layout | Labels | Pan, fitted (median / p95 / max ms) | Pan, zoomed in 4× |
|---|---|---|---|---|---|---|
| Before (SVG, layout in browser) | 1× | 0.75–0.92 s | 482–530 ms | 135–161 ms | 8–33 / 50–58 / 58–125 | not measured |
| Before | 4× | 4.8–5.5 s | 3.2–3.7 s | 0.9–1.0 s | 46–50 / 58–67 / 71–79 | not measured |
| After (Canvas, precomputed) | 1× | 0.40–0.43 s | 1–6 ms | 127–155 ms | 4.2 / 17–21 / 25 | 4.2 / 4.3 / 9 |
| After | 4× | 1.9–2.2 s | 7 ms | 0.7–0.9 s | 4.3 / 17–21 / 25 | 4.2 / 8–12 / 13 |
| After | 6× | 3.1–3.2 s | 11–13 ms | 1.2 s | 12.5 / 17–21 / 25 | 4.2 / 17 / 21–25 |

Over the network, add the download: `map.json` is 2.36 MB (252 KB gzipped) and `layout.json` 0.70 MB (199 KB gzipped). GitHub Pages serves both gzipped.

What changed:

- **Layout precomputed** by `npm run build` (`site/scripts/precompute-layout.mjs`, the same TypeScript run through Vite's SSR loader) into `layout.json`. It's done in the site build, not Python stage 8, so the pipeline stays Python-only. `npm run dev` still computes it live.
- **Canvas rendering** (`site/src/canvas.ts`): one `Path2D` per fill colour and per line style. Clicks and hover use a grid index plus point-in-polygon. Labels, hover and selection stay in the SVG on top.
- Labels are now the largest cost left (0.7–0.9 s at 4×). Caching text widths per word didn't help much. Precomputing label anchors at build time would be the next step if needed.

### Data as of and attributions

- The info panel has a **Data as of** row on provinces and territories: ICD-11 MMS 2026-01; GBD 2023 (released Oct 2025), 2023 estimates; ClinicalTrials.gov data processed 2026-10-29; ChEMBL 37 (2026-05-01). The ChEMBL release now reaches `map.json` through a committed `data/chembl-release.json`, written by stage 6.
- The footer carries:
  - the ICD-11 CC BY-ND 3.0 IGO citation;
  - the IHME source line;
  - the cross-walk "project's own work" note;
  - ClinicalTrials.gov with its processing date and the modification statement;
  - ChEMBL 37 with CC BY-SA 3.0 and the Mendez et al. citation;
  - the AI-proposed, not clinically reviewed note, "Not medical advice";
  - links to `data/LICENSE` and the source.
- `data/LICENSE` was added. **Note:** the repository is already public, so this note was overdue.

### Deploy

- `site/vite.config.ts` sets `base: '/disease-front/'` for production builds.
- `.github/workflows/pages.yml` builds `site/` (tests, then build) and deploys `site/dist/` to GitHub Pages. It runs on `workflow_dispatch` only, so nothing deploys unless started by hand.
- **Waiting on the owner (not done):**
  1. merge the PR;
  2. Settings → Pages → Source: **GitHub Actions**;
  3. Actions → "Deploy site to GitHub Pages" → Run workflow (or `gh workflow run pages.yml`).

  The site will then be at https://qa1roo.github.io/disease-front/, the URL already in the README. "The site is live on GitHub Pages" stays open until then.

### Follow-ups

None of the 8 criteria failed, so there are no follow-up tickets.
