// The layout computed at build time (scripts/precompute-layout.mjs) and shipped as layout.json, so the browser
// doesn't spend seconds on Voronoi iterations: about 3.5 s at 4× CPU throttling (ticket 06). Regions point at
// map.json's nodes by their index in a pre-order walk of the tree, and coordinates keep two decimals.
import type { Border, Layout, Region } from './layout';
import type { Point, Polygon } from './geometry';
import type { MapNode } from './types';

export interface PackedLayout {
  /** Province count, to catch a layout.json built from a different map.json. */
  provinceCount: number;
  /** [node index, parent territory index or -1, x0, y0, x1, y1, …] */
  territories: number[][];
  provinces: number[][];
  /** [0 front | 1 fog edge, x0, y0, x1, y1] */
  borders: number[][];
  fallbacks: number;
}

function preorder(root: MapNode): MapNode[] {
  const out: MapNode[] = [];
  (function walk(n: MapNode) { out.push(n); n.children?.forEach(walk); })(root);
  return out;
}

const round = (x: number) => Math.round(x * 100) / 100;
const flat = (poly: Polygon) => poly.flatMap(p => [round(p[0]), round(p[1])]);
function points(xs: number[], from: number): Polygon {
  const out: Point[] = [];
  for (let i = from; i < xs.length; i += 2) out.push([xs[i], xs[i + 1]]);
  return out;
}

export function packLayout(layout: Layout, root: MapNode): PackedLayout {
  const index = new Map(preorder(root).map((n, i) => [n, i]));
  const territoryIndex = new Map(layout.territories.map((t, i) => [t, i]));
  const pack = (r: Region) => [index.get(r.node)!, r.parent ? territoryIndex.get(r.parent)! : -1, ...flat(r.polygon)];
  return {
    provinceCount: layout.provinces.length,
    territories: layout.territories.map(pack),
    provinces: layout.provinces.map(pack),
    borders: layout.borders.map(b => [b.kind === 'front' ? 0 : 1, ...flat(b.segment)]),
    fallbacks: layout.fallbacks,
  };
}

export function unpackLayout(packed: PackedLayout, root: MapNode): Layout {
  const nodes = preorder(root);
  const territories: Region[] = [];
  const region = (xs: number[], isProvince: boolean): Region => {
    const parent = xs[1] >= 0 ? territories[xs[1]] : null;
    return { node: nodes[xs[0]], polygon: points(xs, 2), depth: parent ? parent.depth + 1 : 0, parent, isProvince };
  };
  // Parents come before their children, as layoutMap pushes them.
  for (const xs of packed.territories) territories.push(region(xs, false));
  return {
    territories,
    provinces: packed.provinces.map(xs => region(xs, true)),
    borders: packed.borders.map(xs => ({ kind: xs[0] === 0 ? 'front' : 'fog-edge', segment: [[xs[1], xs[2]], [xs[3], xs[4]]] }) as Border),
    fallbacks: packed.fallbacks,
  };
}
