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
- Zoomed out, the front line is many short segments, one per block, not one line per chapter. If that reads badly on real data, a fix is to switch zoomed-out territories to a two-band summary view (as in variant A). It did (2026-10-29, ticket 04), so zoomed out each chapter now shows as one held | contested | fog summary with a single front line, fading into the detail as you zoom in.
- Within a band, status shades are not yet graded smoothly west → east.

## Alternatives explored: one shared front line

A follow-up asked whether the whole map could share **one** front line instead of one per block, with every chapter still a single territory. Prototypes are on the `prototype/shared-front` branch (`prototype/shared-front*.prototype.html`, v1–v5):

- **Besieged citadel** (radial, front as one loop), **western front** (horizontal strips) and **two countries** (one straight border, chapters in pieces on both sides).
- **Citadel redesigned**, and **two countries with united chapters** (each chapter one band across the border).
- **River front** (chapters strung along a winding river) and **chapter identity** (two countries with per-chapter colours and hover).
- **Archipelago** (each chapter an island across one meandering diagonal line).
- **Nested arches** (the owner's sketch: one horizontal line, each chapter an irregular arch above and below it, taller arches overhanging neighbours, small chapters nested in big ones).

The constraint they all ran into: if one line must cross every chapter, each chapter gets only a short stretch of it, so chapters come out thin (rays, bands, fingers), or the map must become much longer than the screen, or chapters split into pieces.

Outcome, 2026-10-29: stay with the continuous world for now. The shared front, most likely nested arches, may be revisited later.
