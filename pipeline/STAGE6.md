# Stage 6: status proposals (drafted from a Claude session)

There is no API call here: a Claude session researches each cause and writes drafts, and Python checks them. The owner chose this on 2026-10-29 over the Claude API, so a run costs no API spend. For comparison, an API run (Opus 5.5 with web search, about 5 searches and 40k input tokens per cause) was estimated at $50–70 for the 173 causes.

The drafts go to `data/raw/stage6-drafts/` (git-ignored). `python -m pipeline 6` turns them into `data/proposals/<id>-<slug>.yaml` and `data/proposals/INDEX.md`.

## Which causes

- **GBD causes:** every GBD cause with at least one province on the map, in every group, biggest burden first: 242 in GBD 2023 (`proposals.causes_on_map`). That's 173 non-communicable, plus 69 communicable, maternal, neonatal and nutritional causes added on 2026-10-29. Causes with no provinces are left out (39): 16 are sub-causes counted under a GBD group, and the rest have no ICD-11 province. If a new cross-walk puts one of them on the map, the next run lists it as `no draft`.
- **Diseases assessed directly:** any draft keyed by an ICD-11 code (e.g. `1E70` for smallpox) instead of a GBD cause id. These go to `data/assessments/`, override the GBD cause's status on that one province, and are shown as assessed, not provisional. Use them for diseases no GBD cause covers, or where one disease differs from its cause.

## Ask Claude to

1. **Draft** one YAML entry per cause into `data/raw/stage6-drafts/*.yaml` (any file names; entries are keyed by GBD cause id, or by ICD-11 code for a direct assessment):

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
   - For acute infections, the owner decided (2026-10-29) that **Curable means a treatment cures it**, even where many patients still die or are harmed for lack of timely care (meningitis, diphtheria). Infections with no specific treatment are Treatable, even when most patients recover on their own (measles, Zika). The nuance carries the mortality.
   - **Controlled** keeps ADR 0001's strict reading (decided 2026-10-29): near-normal lives on ongoing treatment, not just symptoms managed.
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

## Second opinion (optional, cheap)

A reviewer who isn't a clinician can still narrow the list:

1. Have a cheap model (Haiku) assign a status to every cause **blind**. It sees only the cause names (`<id><TAB><name>`) and the scale above, never the proposals, and does no web search.
2. Save its answers as `data/raw/second-opinion-haiku.tsv`, one line per cause: `id, status, confidence, reason`.
3. Compare its answers with the proposals in `data/proposals/SECOND-OPINION.md`, listing the disagreements biggest burden first.

On 2026-10-29 the two agreed on 138 of 173 causes (79% of the burden). This is a consistency check between two AI models, not a clinical review; the site says statuses are AI-proposed.

## Review

- Start with the **FLAG** rows in `data/proposals/INDEX.md`. The cross-check flags a status that disagrees with ChEMBL's approved-drug data: Curable or Controlled with no approved drug, or Untreatable with one.
- Many flags are expected: conditions cured by surgery (hernia, cataract, aneurysm repair) or corrected by devices (glasses, hearing aids). They still deserve a look.
- For infections, ChEMBL often files antibiotics and antiparasitics under broad headings (e.g. "Bacterial Infections") rather than the specific disease. So many Curable infections are flagged too: 22 of the 69 communicable causes on 2026-10-29, such as syphilis and ascariasis.
- Edit any field you disagree with, then set `approved: true`.
- `python -m pipeline 8` puts approved statuses on the map as provisional. For each approval that changes a cause's status, it appends `{date, cause, name, from, to}` to `data/events.json`.

Cross-check flags derive from ChEMBL (CC BY-SA 3.0), so the proposal files carry that share-alike licence.
