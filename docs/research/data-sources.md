# Data sources: verified downloads, licences and the real province count

Ticket: [01 · Verify data sources and real province count](../../.scratch/v1/issues/01-verify-data-sources.md). Checked 2026-10-29.

## Summary

| # | Source | Version found | Account? | Raw files in a public repo? |
|---|---|---|---|---|
| 1 | WHO ICD-11 MMS tabulation | 2026-01 (released 16 Feb 2026) | No | Allowed (CC BY-ND 3.0 IGO, verbatim, with attribution). We still git-ignore it. |
| 2 | WHO ICD-10 ↔ ICD-11 mapping tables | 2026-01 | No | Allowed as above, **but building our own crosswalk needs a WHO agreement** (see below) |
| 3 | GBD cause hierarchy + cause → ICD-10 map | GBD 2023 (Oct 2025) | **Yes, IHME** | **No** |
| 4 | GBD global DALYs | GBD 2023, year 2023 | **Yes, IHME** | **No** (derived results only) |
| 5 | ClinicalTrials.gov API v2 | API 2.0.5, data refreshed daily | No | Allowed, with attribution and processing date |
| 6 | ChEMBL drug indications | ChEMBL 37 (2026-05-01) | No | Allowed (CC BY-SA 3.0); derived data must stay CC BY-SA |

**Province count after exclusions: 6,633.** That is under the ~10,000 threshold, so the spec's "layout computed in the browser" assumption holds (see [Province count](#province-count)).

The two findings that matter most:

1. **IHME forbids rehosting GBD data.** Raw GBD files must never be committed, and whether the derived per-province DALYs in `map.json` may sit in a public repo is a judgement call for the owner.
2. **The ICD-11 licence carves out crosswalks.** It says mapping ICD-11 to other classifications "[is] not covered by the Classifications License and [is] subject to a separate written agreement from WHO" (§1.2.4). Our ICD-11 → GBD cause file is such a crosswalk.

---

## 1. WHO ICD-11 MMS tabulation

- **Download:** `https://icdcdn.who.int/static/releasefiles/2026-01/SimpleTabulation-ICD-11-MMS-en.zip` (4.2 MB, `Last-Modified: 27 Jan 2026`). It holds the same table as `.txt` (tab-separated, UTF-8 with BOM) and `.xlsx`, plus a `readme.txt` that describes the columns. It's linked as "Spreadsheet File" from the release's browser page: [icd.who.int/browse/2026-01/mms/en](https://icd.who.int/browse/2026-01/mms/en).
- **Version:** MMS 2026-01. The file header says `Version:2026 Jan 17 - 05:30 UTC`, and WHO lists the release date as 16 February 2026. URL pattern: `releasefiles/<YYYY-MM>/`, with one release a year.
- **Format:** one row per entity (37,052 rows: 28 chapters, 1,360 blocks, 35,664 categories). Columns: `Foundation URI`, `Linearization URI`, `Code`, `BlockId`, `Title` (depth shown as leading `- `), `ClassKind`, `DepthInKind`, `IsResidual`, `ChapterNo`, `BrowserLink`, `isLeaf`, `Primary tabulation`, `Grouping1–5`, `CodingNote`, `Parent` (the parent's foundation URI).
  - **Parsing gotchas:** `CodingNote` can contain raw line breaks (50 records span two lines). Residual rows have an **empty** `Foundation URI`. Only the primary parent is listed, so there are no duplicates for multi-parent entities.
- **Account:** none for the release files. The ICD-API needs free registration, but we don't need the API ([ICD-API](https://icd.who.int/icdapi)).
- **Licence:** CC BY-ND 3.0 IGO ([ICD-11 licence page](https://icd.who.int/docs/icd-api/license); [Terms of Use and License Agreement, PDF](https://icd.who.int/en/docs/ICD11-license.pdf), §1.2–1.3). In short:
  - Verbatim redistribution is fine. Putting ICD-11 into software is not an "adaptation" as long as you don't redistribute it under another name, without attribution, without codes, or without URIs (§1.2.2). Stored or transmitted data "must include Classifications code, title and URI" (§1.2.3).
  - Adding our own fields (burden, status) is allowed if they are clearly marked as not from WHO (§1.2.5).
  - **Crosswalks to other classifications need a separate written agreement from WHO** (§1.2.4).
  - Required citation (§1.3): *International Classification of Diseases, Eleventh Revision (ICD-11), World Health Organization (WHO) 2019 https://icd.who.int/browse11. Licensed under the Creative Commons Attribution-NoDerivatives 3.0 IGO licence (CC BY-ND 3.0 IGO).*
- **Public repo:** committing the unchanged zip would be allowed. We still keep all of `data/raw/` git-ignored (15 MB unzipped) and re-download it in stage 1. **`tree.json` and `map.json` must keep each entity's ICD-11 code, title and URI** to stay within §1.2.2–1.2.3.

## 2. WHO ICD-10 ↔ ICD-11 mapping tables

- **Download:** `https://icdcdn.who.int/static/releasefiles/2026-01/mapping.zip` (6.8 MB, `Last-Modified: 16 Feb 2026`). It contains `.txt` (tab-separated) and `.xlsx` copies of:
  - `11To10MapToOneCategory`: **every ICD-11 MMS entity → exactly one ICD-10 code**. This is the one we need.
  - `10To11MapToOneCategory` and `10To11MapToMultipleCategories`: the other direction.
  - `foundation_*` variants, keyed on Foundation entities.
  - A `readme.txt` describing the columns.
- **Version:** 2026-01 (column header `2026-Jan-17`). It matches the tabulation; URIs carry the release, e.g. `.../release/11/2026-01/mms/...`.
- **Coverage, measured:** all 6,633 provinces appear in `11To10MapToOneCategory`.
  - 6,174 map to an ICD-10 category (e.g. `E10.9`).
  - **391 map only to an ICD-10 block range** (e.g. `Q90-Q99`).
  - **68 map only to an ICD-10 chapter** (e.g. `VI`).
  - 3,877 distinct ICD-10 targets in all.
- **Account:** none.
- **Licence:** part of the ICD-11 release, so the same CC BY-ND 3.0 IGO terms apply (§1.1 covers "any linked coding scheme"). §1.2.4 still applies to the ICD-11 → GBD crosswalk *we* build from it.

## 3. GBD cause hierarchy and cause → ICD-10 code list

- **Cause → ICD map:** GHDx record *GBD 2023 Causes of Death and Nonfatal Causes Mapped to ICD Codes* ([ghdx.healthdata.org/record/ihme-data/gbd-2023-cause-icd-code-mappings](https://ghdx.healthdata.org/record/ihme-data/gbd-2023-cause-icd-code-mappings), DOI [10.6069/vd7t-zt25](https://doi.org/10.6069/vd7t-zt25)). Data published 11 Oct 2025.
  - Files: *GBD 2023 Cause-ICD Codes Map – Nonfatal Causes [XLSX]* (34.6 KB), *GBD 2023 Cause-ICD Codes Map – Causes of Death [XLSX]* (27.0 KB) and a Data Release Information Sheet (PDF).
  - Codes are listed as ICD-9 and ICD-10 codes and ranges per cause. We need **both sheets**: the nonfatal map covers YLD-only causes that have no deaths.
  - Every file link goes to `ghdx.healthdata.org/download-access/login`, so **an IHME login is needed.**
- **Cause hierarchy:** GHDx record *GBD 2023 Cause, REI, and Location Hierarchies* ([ghdx.healthdata.org/record/gbd-2023-cause-rei-and-location-hierarchies](https://ghdx.healthdata.org/record/gbd-2023-cause-rei-and-location-hierarchies)), published 23 Oct 2025. It's an XLSX with Cause, REI and location sheets in the order the GBD tools use. The page would not render in the in-app browser, so its file list wasn't checked directly. Expect the same login gate as the ICD map.
- **Version:** GBD 2023, the latest round (estimates for 1990–2023).
- **Licence:** [IHME Free-of-Charge Non-Commercial User Agreement](https://www.healthdata.org/data-tools-practices/data-practices/ihme-free-charge-non-commercial-user-agreement). Relevant clauses:
  - §1: the user declares they are not a commercial entity, or acting for one, and will make no commercial use.
  - §2: Results may be published on websites, containing only "such portions of the IHME Data … as are necessary", and the user "may not without written permission from UW provide to third parties the ability to download IHME Data Sets from User-provided hosting facilities". Linking to IHME is allowed.
  - §5: no copying, redistribution or derivative data sets, except as §2 allows.
  - §6: publications must carry *"Source: Institute for Health Metrics and Evaluation. Used with permission. All rights reserved."*
  - §8: the agreement lasts five years and IHME may end it at any time.
- **Public repo:** **raw GBD files must not be committed.** `data/raw/gbd/` stays git-ignored.

## 4. GBD global DALYs

- **Where:** GBD Results Tool, [vizhub.healthdata.org/gbd-results](https://vizhub.healthdata.org/gbd-results/). Its [info page](https://www.healthdata.org/data-tools-practices/interactive-visuals/gbd-results) was updated 12 Oct 2025 and covers GBD 2023: 375 diseases and injuries, years 1990–2023, downloaded as CSV. "We require all users to create an account in order to search and download GBD data."
- **Query to run:** GBD Estimate = Cause of death or injury; Measure = DALYs; Metric = Number; Cause = all causes (or just the most-detailed ones); Location = Global; Age = All ages; Sex = Both; Year = 2023. Then download the CSV.
- **"Level-4 cause" is not quite right.** GBD's leaves (most-detailed causes) sit at level 3 *or* level 4. Many level-3 causes have no level-4 children, for example ischaemic heart disease. Stage 2 must take every most-detailed cause from the hierarchy file, not filter on `level == 4`. (Confirm against the hierarchy's most-detailed flag once it's downloaded.)
- **Licence:** same IHME agreement as above.
- **Public repo:** no raw CSV. `burden.json` and `map.json` hold *derived* per-province DALYs (cause totals split equally among provinces). That fits §2's "Results … for publication in … websites". However, publishing the whole JSON in a public repo makes per-cause totals easy to recover, which is close to the "ability to download IHME Data Sets". **This is an owner decision.**

## 5. ClinicalTrials.gov API v2

- **Endpoint:** `GET https://clinicaltrials.gov/api/v2/studies` ([API docs](https://clinicaltrials.gov/data-api/api); OpenAPI spec at `https://clinicaltrials.gov/api/oas/v2`). API version 2.0.5 (`GET /api/v2/version` returns `apiVersion` and `dataTimestamp`, which was `2026-10-29T09:00:05` when checked). Data is refreshed Monday to Friday, generally by 14:00 UTC.
- **Parameters we need** (from the OpenAPI spec):
  - `query.cond`: condition search in Essie syntax. A MeSH-exact search is `AREA[ConditionMeshTerm]"<MeSH heading>"`.
  - `filter.overallStatus`: pipe-separated, e.g. `RECRUITING|ACTIVE_NOT_RECRUITING|COMPLETED|NOT_YET_RECRUITING|ENROLLING_BY_INVITATION`.
  - `filter.advanced`: Essie expression for phase, study type and date, e.g. `AREA[StudyType]INTERVENTIONAL AND AREA[Phase]PHASE3 AND AREA[StudyFirstPostDate]RANGE[2016-10-29,MAX]`.
  - `fields` (e.g. `NCTId|Phase|OverallStatus|StudyFirstPostDate`), `countTotal=true`, `pageSize` (≤ 1000) and `pageToken` (from `nextPageToken`), `format=json|csv`.
  - Phase values: `EARLY_PHASE1`, `PHASE1`, `PHASE2`, `PHASE3`, `PHASE4`, `NA`.
  - Tested: ALS (MeSH), interventional, Phase 3, active/completed, posted since 2016-10-29 returned `totalCount: 34`.
- **Rate limit:** none published in the official docs, and the responses carry no rate-limit headers. Third-party guides report about 50 requests per minute per IP, with HTTP 429 beyond that. Stage 7 should throttle to ~1 request/s and back off on 429. At ~370 causes, a few requests each, a run takes minutes.
- **Account:** none.
- **Terms:** [ClinicalTrials.gov Terms and Conditions](https://clinicaltrials.gov/about-site/terms-conditions) (last updated 31 Jan 2023). The data is free to all. When you publish or distribute it, you should:
  - attribute ClinicalTrials.gov;
  - keep it current;
  - "clearly display the date the data were processed by ClinicalTrials.gov";
  - state any modifications you made.

  The data carries international copyright outside the US. The spec's "data as of" note covers the date requirement. Use `dataTimestamp`.
- **Public repo:** fine to commit derived `bars.json`.
- **Limit for the pipeline bar:** the registry holds only clinical studies, so **"Preclinical" can't be detected** from it. Zero matching trials means "preclinical or nothing", not "preclinical". Phase 4 trials are post-approval studies; ChEMBL is the better source for "Approved".

## 6. ChEMBL approved-drug indications

- **Where:** the `drug_indication` table. **The field is `max_phase_for_ind`**, not `max_phase` (`max_phase` belongs to the molecule). Each row has `molecule_chembl_id`, `parent_molecule_chembl_id`, `mesh_id`, `mesh_heading`, `efo_id`, `efo_term` and `indication_refs` (sources such as ClinicalTrials, FDA, EMA, ATC, DailyMed).
- **REST API:** `https://www.ebi.ac.uk/chembl/api/data/drug_indication.json?max_phase_for_ind=4&limit=1000&offset=…` (`page_meta.total_count` was **8,683** approved indication rows). Nine pages fetch it all, and indications carry **MeSH IDs**, so they join directly to `mesh.yaml`. Status endpoint: `https://www.ebi.ac.uk/chembl/api/data/status.json`.
- **Bulk alternative:** `https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/` (`chembl_37_sqlite.tar.gz` 5.4 GB, `chembl_37_postgresql.tar.gz` 1.9 GB, dated 2026-05-29). That's overkill; use the API.
- **Version:** ChEMBL 37, release date 2026-05-01 (from `status.json`). There are a few releases a year.
- **Account:** none.
- **Licence:** CC BY-SA 3.0 Unported (`LICENSE` in the FTP directory). `REQUIRED.ATTRIBUTION` asks you to cite Mendez D *et al.*, *Nucleic Acids Res.* 2019;47(D1):D930–D940, [doi:10.1093/nar/gky1075](https://doi.org/10.1093/nar/gky1075), and, where ChEMBL is incorporated into other works, to preserve ChEMBL IDs and show the release number.
- **Public repo:** allowed. **Share-alike:** any committed file derived from ChEMBL, such as cross-check flags in `data/proposals/`, must be offered under CC BY-SA 3.0 (or a compatible licence).

---

## Province count

Counted with [`count_provinces.py`](count_provinces.py) on the 2026-01 tabulation:

```
python -I docs/research/count_provinces.py data/raw/icd11/tab/SimpleTabulation-ICD-11-MMS-en.txt data/raw/icd11/map/11To10MapToOneCategory.txt
```

Rules:

- Drop chapters 21–26, V and X (symptoms, injury, external causes, factors influencing health, special purposes, traditional medicine, functioning, extension codes).
- Drop residual categories (`IsResidual = True`, the `.Y` "other specified" and `.Z` "unspecified" codes).
- A province is a remaining category with no children.

| | Count |
|---|---|
| Categories in kept chapters 01–20 | 12,252 |
| Residual categories removed | 3,754 |
| **Provinces (leaf, non-residual)** | **6,633** |
| Territories below chapter level | 2,319 (454 blocks + 1,865 non-leaf categories) |
| Chapters | 20 |

Per chapter, the province counts range from 36 (17, sexual health) to 697 (20, developmental anomalies) and 629 (02, neoplasms). The full table is in the script output.

Notes:

- No category is left childless by removing residuals: every parent with `.Y`/`.Z` children also has real children. So "remove residuals" never turns a territory into a province.
- 167 provinces have "unspecified" in their title but are **not** flagged residual, e.g. `1D92 Coronavirus infection, unspecified site`. They are real ICD-11 categories, so they stay. We trust the `IsResidual` flag rather than matching titles.
- Excluded chapters hold 19,000+ more leaves (15,139 in the extension codes alone). Leaving them out is what keeps the count small.

**Does it break "layout in the browser"? No.** 6,633 is about 1.6× the prototype's ~4,100 provinces, which laid out in ~0.8 s ([ADR 0003](../adr/0003-continuous-world-layout.md)). If it scales linearly that's ~1.3 s, inside the spec's ~2 s budget, and the spec's fallback (precompute in stage 8) still stands. SVG with ~6,600 paths plus ~2,300 territory outlines is plausible, but acceptance criterion 7 (smooth panning) should be checked early.

**But the hierarchy is deeper than the spec assumed.** Territories nest up to 7 levels below the chapter. 1,865 territories are ICD-11 categories with subtypes, not blocks (e.g. diabetes mellitus → type 1, type 2), and **532 parents have both province children and sub-territory children**. The spec's "chapters → blocks → provinces" and "each block is cut into bands" need restating. See below.

## Spec assumptions found wrong (fixed in [v1.md](../spec/v1.md))

1. **"Global DALYs per level-4 cause"**: GBD's most-detailed causes are a mix of level 3 and level 4. Spec now says "most-detailed cause".
2. **"data/raw/ git-ignored where licences forbid redistribution"**: IHME forbids it for GBD, so `data/raw/` is git-ignored as a whole. GBD files never get committed.
3. **GBD is "free account" for DALYs only**: the cause → ICD map and the hierarchy on GHDx also need the IHME login.
4. **Cross-walk "ICD-11 disease → its ICD-10 codes"**: WHO's `11To10MapToOneCategory` gives exactly **one** ICD-10 code per ICD-11 entity. Multiple GBD causes arise only when that code is an ICD-10 block range or chapter (459 provinces), which may span several GBD causes. Majority rule and the review file apply there. Spec updated.
5. **Licences not reflected**: the ICD-11 crosswalk clause (§1.2.4), IHME's no-rehosting rule, ChEMBL's share-alike and the required attributions. Added to the spec's risks and to a new attribution requirement for the site.
6. **Pipeline bar "Preclinical" stage**: ClinicalTrials.gov can't show preclinical work. The lowest stage is now "No registered trial". "Approved" comes from ChEMBL (`max_phase_for_ind = 4` for a reviewed MeSH term), not from trial phases.
7. **ChEMBL "max_phase = 4"** (ticket wording): the indication-level field is `max_phase_for_ind`. Spec now names it.
8. **Layout "chapters → blocks → provinces"**: territories nest up to 7 levels and include non-leaf categories, and 532 parents mix provinces with sub-territories. Spec now says territories nest to any depth. How to band a territory with mixed children is listed as an open question in the spec's risks.
9. **"Real province count could be over 10,000"**: it's 6,633. The browser-layout plan stands. The risk item is marked resolved.

## Steps for the owner

These need you personally; none were attempted.

1. **Create an IHME account** at [healthdata.org](https://www.healthdata.org/) and accept the Free-of-Charge Non-Commercial User Agreement. Check that the §1 declaration fits you: not a commercial entity, nor acting as its employee or agent for this use.
2. **Download the GBD 2023 files** into `data/raw/gbd/` (git-ignored):
   - both *GBD 2023 Cause-ICD Codes Map* XLSX files from the [GHDx ICD map record](https://ghdx.healthdata.org/record/ihme-data/gbd-2023-cause-icd-code-mappings);
   - the *GBD 2023 Cause, REI, and Location Hierarchies* XLSX from its [GHDx record](https://ghdx.healthdata.org/record/gbd-2023-cause-rei-and-location-hierarchies);
   - a GBD Results Tool CSV: DALYs, Number, all causes, Global, All ages, Both sexes, 2023.

   Stage 2 can't be automated past the login, so it reads these files from disk.
3. **Decide on the ICD-11 crosswalk clause (§1.2.4).** Either ask WHO for written permission (via the permissions route on [who.int/copyright](https://www.who.int/copyright)) before the repo or site goes public, or accept the risk for a non-commercial pet project. Asking costs an email.
4. **Decide whether derived DALYs may be public.** Committing `burden.json` and `map.json`, and serving them on GitHub Pages, publishes per-province DALYs from which per-cause totals can be recovered. Options:
   - accept it as "Results for publication on a website" (§2);
   - ask IHME;
   - keep `burden.json` out of git and ship only `map.json`.

   Either way, show the §6 source line on the site.
5. **Pick a licence for committed data files.** Anything derived from ChEMBL must be CC BY-SA 3.0-compatible, and ICD-11 content stays CC BY-ND 3.0 IGO.
