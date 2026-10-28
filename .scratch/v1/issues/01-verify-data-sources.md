# 01 · Verify data sources and real province count

**Blocked by:** nothing
**Spec:** [docs/spec/v1.md](../../../docs/spec/v1.md), "Risks and things to verify first"

## Why

Every later ticket depends on four external datasets. The spec assumes they exist in a usable form. This ticket confirms that before any pipeline code is written.

## What to do

For each source, find the exact download (URL, format, version, whether an account is needed) and its licence terms, especially whether the raw files may be committed to a public repo:

1. WHO ICD-11 MMS tabulation (the full linearization as a file).
2. WHO ICD-10 → ICD-11 mapping table.
3. GBD cause hierarchy, plus the cause → ICD-10 code list.
4. GBD global DALYs per level-4 cause, latest year.
5. ClinicalTrials.gov API v2: query by condition/MeSH term, filter by phase and status, and rate limits.
6. ChEMBL: where approved-drug indications live (drug_indication with max_phase = 4) and how to query or download them.

Then download the ICD-11 tabulation and count provinces after the agreed exclusions (non-disease chapters, injuries, "other specified" / "unspecified" entries).

## Done when

- `docs/research/data-sources.md` exists and, for every source above, lists the download link, format, version/date, licence and any account requirement, each with a cited primary source.
- That file states the real province count after exclusions, and whether it changes the spec's "layout in the browser" assumption (over ~10,000 provinces probably does).
- Any spec assumption found to be wrong is listed in that file, and the spec is updated to match.
