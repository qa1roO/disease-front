# disease-front

A strategy-game-style map of human diseases. See [CONTEXT.md](CONTEXT.md) and [docs/spec/v1.md](docs/spec/v1.md).

Site: https://qa1roo.github.io/disease-front/ (not published yet; see [Publishing](#publishing)).

## Running it

Needs Python 3.11+ and Node 20+.

```bash
pip install -r requirements.txt
python -m pipeline all       # stages 1-8; each skips itself when its committed outputs are up to date
python -m unittest discover -s tests -t .
cd site && npm install && npm run dev
```

Each stage records content hashes of its inputs and outputs in `data/stamps.json` and skips itself while they still match; add `--force` to rerun. `data/raw/` is git-ignored. On Windows, clone with `git clone -c core.longpaths=true`, since some proposal file names are long.

Stage 2 (GBD data) runs from a Claude session with the IHME GBD connector, not from Python: see [pipeline/STAGE2.md](pipeline/STAGE2.md). Stages 5 (MeSH search terms) and 6 (status proposals) check drafts written by a Claude session: see [pipeline/STAGE5.md](pipeline/STAGE5.md) and [pipeline/STAGE6.md](pipeline/STAGE6.md). Stage 7 queries ClinicalTrials.gov for the causes whose MeSH terms you've marked `reviewed: true` in `data/mesh.yaml`. Stage 4 prints a coverage report and writes `data/crosswalk-review.yaml`, whose tie resolutions you edit by hand.

Province sizes: GBD 2023 DALYs. Source: Institute for Health Metrics and Evaluation. Used with permission. All rights reserved. The ICD-11 → GBD cause cross-walk (`data/crosswalk.json`, `data/gbd-extra-codes.yaml`) is this project's own work, not a WHO or IHME product.

ICD-11 content: International Classification of Diseases, Eleventh Revision (ICD-11), World Health Organization (WHO) 2019 https://icd.who.int/browse11. Licensed under the Creative Commons Attribution-NoDerivatives 3.0 IGO licence (CC BY-ND 3.0 IGO).

Pipeline bars: ClinicalTrials.gov, with running trials counted and phase-ranked by this project; the processing date is in `data/bars.json`. Status cross-check: ChEMBL 37 approved-drug indications (EMBL-EBI, CC BY-SA 3.0; Mendez D et al., Nucleic Acids Res. 2019;47(D1):D930–D940, doi:10.1093/nar/gky1075). Statuses are proposed by AI (Claude) from cited sources, approved by the owner, and not reviewed by a clinician.

## What a fresh clone can rebuild

Everything the site needs is committed, so `python -m pipeline all` on a fresh clone skips every stage and changes nothing. Checked 2026-10-29 (ticket 06) with no raw files at all, and with only the GBD files. Rebuilding a stage needs:

| Stage | Rebuilds from a fresh clone? | Needs |
|---|---|---|
| 1 ICD-11 | yes | public WHO download, no account |
| 2 GBD | no | a Claude session with the IHME GBD connector, or IHME downloads ([STAGE2.md](pipeline/STAGE2.md)); IHME forbids committing them |
| 3 tree | yes | stage 1 |
| 4 cross-walk and burden | only with the GBD files | stage 2's files in `data/raw/gbd/`; without them it keeps the committed `crosswalk.json` and `burden.json` |
| 5 MeSH terms | only with drafts | a Claude session's drafts in `data/raw/stage5-drafts/` ([STAGE5.md](pipeline/STAGE5.md)); without them it keeps `mesh.yaml` |
| 6 status proposals | only with drafts | a Claude session's drafts in `data/raw/stage6-drafts/` ([STAGE6.md](pipeline/STAGE6.md)); fetches ChEMBL itself; without drafts it keeps `proposals/` and `assessments/` |
| 7 pipeline bars | yes (`--force`) | ClinicalTrials.gov, about 10 minutes; results change as the registry does |
| 8 site data | yes | the committed outputs above |

The site's layout is computed by `npm run build` (`site/scripts/precompute-layout.mjs`), not by the pipeline.

## Publishing

The site is static. `.github/workflows/pages.yml` builds `site/` and deploys `site/dist/` to GitHub Pages. It runs only when started by hand. One-time setup: in the repository's Settings → Pages, set Source to "GitHub Actions". Then run "Deploy site to GitHub Pages" from the Actions tab, or:

```bash
gh workflow run pages.yml
```

Data licences: [data/LICENSE](data/LICENSE).
