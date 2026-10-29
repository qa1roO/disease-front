# Stage 5: MeSH search terms (drafted from a Claude session)

The spec planned a Claude API call here. On 2026-10-29 the owner chose a Claude session instead, as for stage 6, so there's no API key or API spend. The session writes drafts and Python checks them.

The drafts go to `data/raw/stage5-drafts/` (git-ignored). `python -m pipeline 5` turns them into `data/mesh.yaml`. Stage 7 uses only the entries you've marked `reviewed: true`.

## Which causes

Every GBD cause in `data/burden.json`: 281 in GBD 2023. That includes groups and causes that have no provinces of their own, such as the liver-cancer-by-etiology sub-causes and the HIV/TB combinations. Only causes with provinces affect the map, so review those first. Their entries come first in `mesh.yaml`, because it's sorted by burden.

## Ask Claude to

1. **Draft** one entry per cause into `data/raw/stage5-drafts/*.yaml` (any file names), keyed by GBD cause id:

   ```yaml
   493: [Myocardial Ischemia, Coronary Artery Disease, Coronary Disease, Myocardial Infarction, Angina Pectoris]
   ```

   - **Headings are searched one by one, joined with OR**, as `AREA[ConditionMeshTerm]"<heading>"` on ClinicalTrials.gov. A trial matches when one of its condition MeSH terms is exactly that heading. Narrower headings are not included automatically, so list each one you want.
   - **Leave out symptoms and catch-alls** that pull in unrelated trials, such as `Anxiety` (preoperative anxiety trials), `Sepsis` for neonatal sepsis, or `Respiratory Tract Infections` for lower respiratory infections. A residual GBD cause ("Other …") can only use a broad heading. Its bar is rough, and that's expected.
   - **Use the labels ClinicalTrials.gov indexes under.** These are MeSH **2025** labels (`bars.CTGOV_MESH_YEAR`). MeSH 2026 renamed some headings, and trials are still filed under the old ones. For example, `Depressive Disorder, Major` finds 2,966 trials, but its 2026 label `Major Depressive Disorder` finds 5. Stage 5 accepts a current label or a 2025 one.
   - The 2026-10-29 drafts started from the stage-6 proposals' `mesh` headings (chosen for the ChEMBL cross-check). They were tightened for trial search, and the causes without a proposal were added.
2. **Check every heading against ClinicalTrials.gov.** Count the trials for `AREA[ConditionMeshTerm]"<heading>"` with no other filters. A heading with no trials, or far fewer than expected, is probably the wrong label.
3. **Run** `python -m pipeline 5`. Each heading is resolved through NLM's lookup API, current MeSH first and then 2025. Results are cached in `data/raw/mesh-lookup.json` and `mesh-lookup-2025.json`. The run prints any draft it rejects (unknown heading, empty list or `no draft`) and keeps that cause's older entry. Fix the draft and run again.

## Review

- Open `data/mesh.yaml` and check each entry's `terms`, which map a descriptor ID to its heading. Edit them freely, then set `reviewed: true`.
- **Re-runs never touch a reviewed entry.** Unreviewed entries are rewritten from the current drafts, so mark an entry reviewed to keep your edits.
- Then run `python -m pipeline 7` and `python -m pipeline 8`.

## Stage 7, for reference

For each reviewed cause, stage 7 counts the matching interventional trials on ClinicalTrials.gov:

- **Filters:** trials still running (recruiting, not yet recruiting, enrolling by invitation, or active and not recruiting), first posted within 10 years of the API's `dataTimestamp`. Completed trials don't count.
- **Phase:** it asks Phase 3 (or 4), then Phase 2, then Phase 1 (or Early Phase 1), and stops at the first phase with trials.
- **Approved:** never set here. Held provinces show it, from stage 8.
- **Rate:** about 1 request a second, backing off on HTTP 429 and 5xx.
- **Re-runs:** counts are cached per `dataTimestamp` in `data/raw/ctgov-counts.json`. An interrupted run resumes, and a re-run on the same day's data makes no requests. `--force` rebuilds `data/bars.json` from the cache.
