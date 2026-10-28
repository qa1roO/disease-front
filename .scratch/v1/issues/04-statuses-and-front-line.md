# 04 · Provisional statuses and the front line

**Blocked by:** 03
**Spec:** pipeline stage 6; "Status proposals and review"; ADR 0001; ADR 0003 (zoomed-out readability)

## What to build

- **Stage 6, status proposals**: for every non-communicable GBD cause, call Claude with the web search tool and write `data/proposals/<cause>.yaml` in the spec's format (status 1–5, nuance, sources, cross_check, `approved: false`).
  - Reject and retry any proposal whose source URLs don't resolve.
  - **ChEMBL cross-check**: flag any status that disagrees with the approved-drug data.
  - Re-running doesn't overwrite a proposal you've already approved or edited.
- **Approval**: only `approved: true` proposals reach `map.json`. Each approval that changes a status appends `{date, cause, from, to}` to `data/events.json`.
- **Stage 8**: every province under an approved cause inherits its status as **provisional**.
- **Map**: status colours with a lighter tint for provisional, held | contested | fog bands in each block, the front line, and the dashed fog edge.
- **Info panel**: status with "provisional" tag, nuance, and source links.

## Done when

- Every non-communicable GBD cause has a proposal file, and flagged ones are visibly marked as flagged.
- With the proposals approved, every block that has both held and contested provinces shows exactly one straight front line.
- The front line is checked zoomed out on real data. If it reads as noise, apply ADR 0003's fallback (two-band summary per territory when zoomed out), or open a follow-up and note why.
- Cost of one full stage-6 run is noted.
