# 06 · Acceptance pass and first deploy

**Blocked by:** 04, 05
**Spec:** "Acceptance criteria"

## What to do

- Run `python -m pipeline all` from a clean checkout, and fix anything that only worked thanks to leftover local files.
- Go through the spec's 8 acceptance criteria one by one and record the result of each in this ticket.
- Performance: measure load-to-interactive and panning smoothness on a mid-range laptop. If over 3 s, or panning stutters, precompute the layout in stage 8 and/or switch rendering to Canvas.
- "Data as of" dates show for every source in the info panel.
- `npm run build` and publish `site/dist/` to GitHub Pages by hand. This needs a GitHub repo, so create one first.

## Done when

- All 8 acceptance criteria pass, or each failure has its own follow-up ticket.
- The site is live on GitHub Pages and the URL is in a README.
