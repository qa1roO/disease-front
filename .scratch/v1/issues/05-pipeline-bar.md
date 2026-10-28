# 05 · MeSH mapping and the pipeline bar

**Blocked by:** 03
**Spec:** pipeline stages 5, 7; "Pipeline bar (stage 7)"; info panel

Can be worked in parallel with 04. The two only meet in stage 8 and the info panel.

## What to build

- **Stage 5, MeSH mapping**: Claude drafts MeSH search terms for every GBD cause into `data/mesh.yaml`, each entry with `reviewed: false`. Re-running doesn't overwrite reviewed entries.
- **Stage 7, pipeline bar**: for each cause with reviewed terms, query ClinicalTrials.gov API v2 for interventional trials that are active, recruiting or completed and were registered in the last 10 years. The bar value is the furthest phase reached. Write `data/bars.json` with phase, trial count and a search URL.
- **Stage 8**: provinces inherit their cause's bar. Held provinces show "Approved".
- **Info panel**: the pipeline bar (Preclinical / Phase 1 / 2 / 3 / Approved) with trial count and a link to the matching ClinicalTrials.gov search. The activity and access bars stay greyed out as "no data".

## Done when

- Every GBD cause has a MeSH entry, and stage 7 only uses reviewed ones.
- Spot-check five causes by hand. Each bar's phase matches what the ClinicalTrials.gov link shows.
- Stage 7 respects the API's rate limits and can be re-run safely.
