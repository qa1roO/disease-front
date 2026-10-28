# ADR 0003: Continuous-world map layout

## Status

Accepted, 2026-10-28.

## Context

A prototype tried three layouts on fake data shaped like the real thing (20 ICD-11 chapters, ~4,100 provinces, skewed burden):

- **A, organic drill-down**: Voronoi regions, one hierarchy level on screen at a time, click to zoom in.
- **B, rectangle drill-down**: the same, as a squarified treemap.
- **C, continuous world**: every province on one map at once, with pan/zoom and labels that change with zoom level.

The prototype is kept on the `prototype/map-layout` branch (`prototype/map-layout.prototype.html`).

## Decision

Use **C, the continuous world**: nested weighted Voronoi cells (chapters → blocks → provinces), all on one pannable, zoomable map.

Inside each block, the polygon is first cut into held | contested | fog bands by burden share, and provinces are laid out inside their band. This guarantees a single straight front line in every block.

## Consequences

- It's the most strategy-game-like option and shows the whole war at once.
- Full layout of ~4,100 provinces took ~0.8 s in the browser. That's fine, and the real pipeline could precompute it.
- Zoomed out, the front line is many short segments, one per block, not one line per chapter. If that reads badly on real data, a fix is to switch zoomed-out territories to a two-band summary view (as in variant A).
- Within a band, status shades are not yet graded smoothly west → east.
