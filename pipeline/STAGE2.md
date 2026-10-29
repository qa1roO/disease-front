# Stage 2: fetch GBD (run from a Claude session)

The IHME GBD 2023 MCP connector works only inside Claude, so a Claude session runs this stage, not Python. It needs the connector, which signs in with your free IHME account. Everything it writes goes to `data/raw/gbd/`, which is git-ignored: IHME forbids rehosting GBD data ([data sources](../docs/research/data-sources.md), section 3). `python -m pipeline 2` only checks that the files exist.

Ask Claude to do the steps below. Large tool results get saved to disk by Claude Code, and those can be copied verbatim. Small ones have to be written out by hand, so check them as step 5 says.

1. **`causes.csv`**: `list_children(cause_name="All causes", recursive=True, fmt="csv")`. Drop the `note` column. Stage 4 itself drops the five overlapping totals (1026–1029, 1059) and the injuries.
2. **`icd_codes.csv`**: `get_supplementary_data(dataset="icd_codes", limit=700, fmt="csv")`, verbatim. It's about 90 KB, so it's saved to disk.
3. **`dalys_level3.csv`**: `get_top_causes(measure="dalys", n=400, fmt="csv")` returns every level-3 cause (Global, 2023, all ages), verbatim.
4. **`dalys_level4.csv`**: columns `cause_id,count_combined`, one row per level-4 most-detailed **disease** cause. Each comes from `get_cause_burden(cause_id=…, measure="dalys", fmt="csv")`. That's 154 calls in GBD 2023. The connector rate-limits bursts, so send about five at a time.
   - Latent TB (954) and the benign intestinal and cervical/uterine neoplasms (965, 966) have no DALYs in GBD. Record them in `notes.txt`.
5. **Check**: the level-4 children of every level-3 parent should add up to that parent's `count_combined` in `dalys_level3.csv`, within 0.2%. In the 2026-10-29 fetch, every parent passed.
6. **`fetch.json`**: source, fetch date, round (`GBD 2023`), release month (`2025-10`), estimate year (2023), and how each file was made. Stage 4 copies these into `burden.json` as the "data as of" note.

Then run `python -m pipeline all`.

**Alternative:** download one GBD Results Tool CSV instead of steps 3–4: DALYs, Number, every cause, Global, All ages, Both sexes, 2023. That's the canonical source, and only one download. Using it would need a small reader in `pipeline/gbd.py`.
