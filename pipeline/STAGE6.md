# Stage 6: status proposals (drafted from a Claude session)

There is no API call here: a Claude session researches each cause and writes drafts, and Python checks them. The owner chose this on 2026-10-29 over the Claude API, so a run costs no API spend. For comparison, an API run (Opus 5.5 with web search, about 5 searches and 40k input tokens per cause) was estimated at $50–70 for the 173 causes.

The drafts go to `data/raw/stage6-drafts/` (git-ignored). `python -m pipeline 6` turns them into `data/proposals/<id>-<slug>.yaml` and `data/proposals/INDEX.md`.

## Which causes

Every non-communicable GBD cause with at least one province on the map, biggest burden first. That's 173 in GBD 2023 (`proposals.ncd_causes`). Non-communicable causes with no provinces are left out (28 in GBD 2023): 10 are sub-causes counted under a GBD group, and 18 have no ICD-11 province. If a new cross-walk puts one of them on the map, the next run lists it as `no draft`.

## Ask Claude to

1. **Draft** one YAML entry per cause into `data/raw/stage6-drafts/*.yaml` (any file names; entries are keyed by GBD cause id):

   ```yaml
   493:
     status: 3
     nuance: "Typical-patient caveat, e.g. curable if caught early."
     sources:
       - {url: "https://...", title: "Page title, publisher"}
     mesh: ["Coronary Artery Disease", "Myocardial Ischemia"]   # exact MeSH headings
   ```

   - **Status** is for a typical patient at diagnosis (ADR 0001): 2 Curable when standard treatment removes the disease. 3 Controlled when patients live near-normal lives on ongoing treatment. 4 Treatable when treatment slows the disease or eases symptoms. 5 Untreatable when nothing changes its course.
   - For cancers, the 2026-10-29 run used **Curable when SEER 5-year relative survival is about 80% or more** and most cases are found localized. Chronic cancers kept in check on long-term therapy (CML, CLL) are Controlled.
   - **Sources** must be pages that answer HTTP 200 to a script. These work: WHO fact sheets, NHS, MedlinePlus, NCI PDQ, SEER Stat Facts, NHLBI, NIDDK, NIMH, NINDS, NEI, NIAMS, NIDA and NIAAA.
   - Avoid sites that block scripts: NIA, Mayo Clinic, Cleveland Clinic, and some CDC pages.
   - Also avoid NCBI Bookshelf. It answers 200 with a CAPTCHA page for any `NBK` id, so the check can't catch a wrong id.
   - **MeSH headings** feed the ChEMBL cross-check. List the broad heading and the narrower ones drugs are indexed under (e.g. "Breast Neoplasms").
2. **Check titles.** A 200 proves a page exists, not that it is the right page. Have Claude fetch each source and compare the page `<title>` with the draft's title.
3. **Run** `python -m pipeline 6`. It does the following:
   - fetches ChEMBL approved indications into `data/raw/chembl/` on first run;
   - resolves MeSH headings through NLM's lookup API (cached in `data/raw/mesh-lookup.json`);
   - checks every URL (one retry for dropped requests);
   - writes a proposal per passing draft.
   
   It prints any draft it rejects, with the reason: a dead URL, an unknown MeSH heading, a status outside 1–5, or `no draft`. Fix those drafts and run it again.
4. **Re-runs** keep every existing proposal. After changing drafts, `python -m pipeline 6 --refresh` rewrites only the proposals that are neither approved nor edited by hand.

## Review

- Start with the **FLAG** rows in `data/proposals/INDEX.md`. The cross-check flags a status that disagrees with ChEMBL's approved-drug data: Curable or Controlled with no approved drug, or Untreatable with one.
- Many flags are expected: conditions cured by surgery (hernia, cataract, aneurysm repair) or corrected by devices (glasses, hearing aids). They still deserve a look.
- Edit any field you disagree with, then set `approved: true`.
- `python -m pipeline 8` puts approved statuses on the map as provisional. For each approval that changes a cause's status, it appends `{date, cause, name, from, to}` to `data/events.json`.

Cross-check flags derive from ChEMBL (CC BY-SA 3.0), so the proposal files carry that share-alike licence.
