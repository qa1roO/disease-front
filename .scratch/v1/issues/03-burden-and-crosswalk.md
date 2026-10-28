# 03 · Burden: GBD cross-walk and province sizes

**Blocked by:** 02
**Spec:** pipeline stages 2, 4; "Cross-walk rules"; ADR 0002

## What to build

- **Stage 2, fetch GBD**: cause hierarchy, cause → ICD-10 codes, and global DALYs per level-4 cause, into `data/raw/gbd/` (respect the licence findings from 01).
- **Stage 4, cross-walk and burden**:
  - ICD-11 disease → ICD-10 codes (WHO mapping table) → GBD cause.
  - Majority rule when the codes point to more than one cause. Ties go to `data/crosswalk-review.yaml`, with a placeholder resolution you edit by hand. LLM proposals for ties can come later.
  - Each GBD cause's DALYs are split equally among its provinces, flagged "estimated".
  - A province with no GBD cause gets the minimum size and stays fog.
  - Output `data/crosswalk.json` and `data/burden.json`.
- **Stage 8**: sizes in `map.json` now come from burden.
- **Info panel**: burden in DALYs with the "size estimated" note, the GBD cause, and the GBD "data as of" date.

## Done when

- Map regions are sized by burden, and every province is either traced to a GBD cause or at minimum size. The info panel says which.
- A short report printed by stage 4 gives: provinces mapped, provinces unmapped (fog), ties sent to review, and the share of total DALYs covered.
- Sizes in `burden.json` add up to the GBD total for the included causes (within rounding).
