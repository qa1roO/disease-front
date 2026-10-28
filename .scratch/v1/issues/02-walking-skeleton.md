# 02 · Walking skeleton: real ICD-11 tree on the continuous map

**Blocked by:** 01
**Spec:** pipeline stages 1, 3, 8; "The map"; "Layout rules"; "Front end"; ADR 0003

## Why

This is the tracer bullet. It's the thinnest path through every layer, from a raw download to a pannable map in the browser. Later tickets add one kind of data each onto something that already works.

## What to build

- `pipeline/` Python package with a `python -m pipeline <stage>` entry point. Each stage reads and writes files under `data/` and skips itself if its output is up to date.
- **Stage 1, fetch ICD-11**: download the MMS tabulation into `data/raw/icd11/`.
- **Stage 3, build the tree**: write `data/tree.json` with territories (chapters, blocks) and provinces (diseases), excluding non-disease chapters, injuries, and "other specified" / "unspecified" entries.
- **Stage 8, build site data**: write `site/public/map.json` from the tree. For now every province has the same size and is fog.
- **`site/`**: Vite + TypeScript + D3. Port the layout from the `prototype/map-layout` branch (nested weighted Voronoi, continent shape, band split per block), rewritten properly rather than copied. Include pan/zoom, three border weights, labels that change with zoom, and a legend.
- Minimal info panel on click: name, ICD-11 code, position in the hierarchy. Everything else reads "no data".

## Done when

- `python -m pipeline all` (stages 1, 3, 8 for now) produces `site/public/map.json`.
- `npm run dev` in `site/` shows every non-excluded ICD-11 chapter, and the province count matches `tree.json`.
- Pan, zoom and labels changing with zoom all work, and the same data always gives the same map.
- Layout time on the real tree is measured and noted in the PR or commit. If it's over ~2 s, open a follow-up to precompute it.
