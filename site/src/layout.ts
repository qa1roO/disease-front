// The continuous-world layout (ADR 0003): nested weighted Voronoi cells inside one convex continent.
//
// - Every territory's children get weighted Voronoi cells inside the territory's cell, any depth down.
// - Children with a higher held share are seeded further west; ties keep ICD order.
// - A territory's provinces are first cut into held | contested | fog bands west → east, then get cells
//   inside their band, ordered by status. That gives each territory one straight front line.
// - A "mixed" territory (provinces and sub-territories as children) treats its direct provinces as one
//   extra, unnamed child, which is then banded like any other set of provinces.
// - Everything is seeded from the data, so the same map.json always gives the same map.
import { polygonCentroid, polygonContains, polygonHull } from 'd3';
import { voronoiMapSimulation } from 'd3-voronoi-map';
import { area, bandSplit, EAST, hash, NORTH, prng, type Point, type Polygon, type Segment } from './geometry';
import { sideOf, type MapNode, type Side } from './types';

export const WORLD = { width: 2000, height: 1250 };
/**
 * Every province is at least this share of the mean province burden, so rare diseases and fog (size 0) stay
 * clickable when zoomed in.
 */
export const MIN_SHARE = 0.02;

/** The minimum size, in the same unit as `size` (DALYs): MIN_SHARE of the mean province size. */
export function minimumSize(root: MapNode): number {
  let total = 0, count = 0;
  (function walk(n: MapNode) {
    if (n.children) n.children.forEach(walk);
    else { total += n.size ?? 0; count++; }
  })(root);
  return total > 0 ? (MIN_SHARE * total) / count : 1;
}

export interface Region {
  node: MapNode;
  polygon: Polygon;
  /** 0 for chapters, +1 per territory level below. */
  depth: number;
  /** The territory this region sits in (null for chapters). */
  parent: Region | null;
  isProvince: boolean;
}

export interface Border { kind: 'front' | 'fog-edge'; segment: Segment }

export interface Layout {
  territories: Region[];
  provinces: Region[];
  borders: Border[];
  /** Voronoi runs that lost a cell and fell back to straight stripes. */
  fallbacks: number;
}

interface Totals { weight: number; held: number; contested: number; fog: number; order: number }

/** A child to give a cell: a territory, or the bundle of a mixed territory's direct provinces. */
interface Item { node: MapNode | null; provinces: MapNode[]; totals: Totals }

export function continent(): Polygon {
  const r = prng(3), cx = WORLD.width / 2, cy = WORLD.height / 2;
  const rx = WORLD.width * 0.48, ry = WORLD.height * 0.47;
  const pts: Point[] = [];
  for (let i = 0; i < 72; i++) {
    const a = (i / 72) * 2 * Math.PI, k = 1 + (r() - 0.5) * 0.08;
    pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]);
  }
  return polygonHull(pts)!;
}

export function layoutMap(root: MapNode): Layout {
  const minSize = minimumSize(root);
  const totals = new Map<MapNode, Totals>();
  let order = 0;
  (function sum(n: MapNode): Totals {
    const t: Totals = { weight: 0, held: 0, contested: 0, fog: 0, order: order++ };
    if (n.children) {
      for (const c of n.children) {
        const ct = sum(c);
        t.weight += ct.weight; t.held += ct.held; t.contested += ct.contested; t.fog += ct.fog;
      }
    } else {
      t.weight = Math.max(n.size ?? 0, minSize);
      t[sideOf(n.status)] = t.weight;
    }
    totals.set(n, t);
    return t;
  })(root);

  const out: Layout = { territories: [], provinces: [], borders: [], fallbacks: 0 };

  const bundle = (provinces: MapNode[]): Totals => {
    const t: Totals = { weight: 0, held: 0, contested: 0, fog: 0, order: totals.get(provinces[0])!.order };
    for (const p of provinces) {
      const pt = totals.get(p)!;
      t.weight += pt.weight; t.held += pt.held; t.contested += pt.contested; t.fog += pt.fog;
    }
    return t;
  };

  function layoutProvinces(poly: Polygon, provinces: MapNode[], parent: Region, seed: string) {
    const sides: Side[] = ['held', 'contested', 'fog'];
    const bands = sides.map(key => {
      const items = provinces.filter(p => sideOf(p.status) === key)
        .sort((a, b) => (a.status ?? 9) - (b.status ?? 9) || totals.get(a)!.order - totals.get(b)!.order);
      return { key, items, weight: items.reduce((s, p) => s + totals.get(p)!.weight, 0) };
    });
    const { pieces, borders } = bandSplit(poly, bands);
    for (const b of borders) {
      out.borders.push({ kind: b.between[0] === 'held' && b.between[1] === 'contested' ? 'front' : 'fog-edge', segment: b.segment });
    }
    for (const piece of pieces) {
      const items: Item[] = piece.items.map(p => ({ node: p, provinces: [p], totals: totals.get(p)! }));
      for (const cell of cells(piece.polygon, items, false, seed + piece.key)) {
        out.provinces.push({ node: cell.item.node!, polygon: cell.polygon, depth: parent.depth + 1, parent, isProvince: true });
      }
    }
  }

  function layoutTerritory(region: Region) {
    const kids = region.node.children!;
    const seed = region.node.uri ?? region.node.title;
    if (kids.every(k => !k.children)) return layoutProvinces(region.polygon, kids, region, seed);
    const items: Item[] = kids.filter(k => k.children).map(k => ({ node: k, provinces: [], totals: totals.get(k)! }));
    const loose = kids.filter(k => !k.children);
    if (loose.length) items.push({ node: null, provinces: loose, totals: bundle(loose) });
    for (const cell of cells(region.polygon, items, true, seed)) {
      if (cell.item.node) addTerritory(cell.item.node, cell.polygon, region);
      else layoutProvinces(cell.polygon, cell.item.provinces, region, seed + '#provinces');
    }
  }

  function addTerritory(node: MapNode, polygon: Polygon, parent: Region | null) {
    const region: Region = { node, polygon, depth: parent ? parent.depth + 1 : 0, parent, isProvince: false };
    out.territories.push(region);
    layoutTerritory(region);
  }

  /** Weighted Voronoi cells for items inside a convex polygon, seeded west → east. */
  function cells(poly: Polygon, items: Item[], byHeldShare: boolean, seed: string): { item: Item; polygon: Polygon }[] {
    if (items.length === 0) return [];
    if (items.length === 1) return [{ item: items[0], polygon: poly }];
    const ranked = byHeldShare
      ? items.slice().sort((a, b) => b.totals.held / b.totals.weight - a.totals.held / a.totals.weight || a.totals.order - b.totals.order)
      : items;
    try {
      const result = voronoi(poly, ranked, prng(hash(seed)));
      if (result) return result;
    } catch {
      // fall through to stripes
    }
    out.fallbacks++;
    return stripes(poly, ranked);
  }

  for (const chapter of cells(continent(), root.children!.map(c => ({ node: c, provinces: [], totals: totals.get(c)! })), true, 'world')) {
    addTerritory(chapter.item.node!, chapter.polygon, null);
  }
  return out;
}

function voronoi(poly: Polygon, ranked: Item[], random: () => number) {
  const clip = polygonHull(poly);
  if (!clip || area(clip) < 1e-9) return null;
  const c = polygonCentroid(clip) as Point;
  const proj = (p: Point, d: Point) => (p[0] - c[0]) * d[0] + (p[1] - c[1]) * d[1];
  const spanA = Math.max(...clip.map(p => proj(p, EAST))) - Math.min(...clip.map(p => proj(p, EAST)));
  const spanN = Math.max(...clip.map(p => proj(p, NORTH))) - Math.min(...clip.map(p => proj(p, NORTH)));
  const rank = new Map(ranked.map((d, i) => [d, i]));
  const n = ranked.length;
  const sim = voronoiMapSimulation(ranked)
    .weight(d => d.totals.weight)
    .clip(clip)
    .prng(random)
    .maxIterationCount(80)
    .convergenceRatio(0.02)
    .initialPosition(d => {
      const a = ((rank.get(d)! + 0.5) / n - 0.5) * spanA * 0.8;
      const b = (random() - 0.5) * spanN * 0.6;
      let p: Point = [c[0] + EAST[0] * a + NORTH[0] * b, c[1] + EAST[1] * a + NORTH[1] * b];
      // Seeds must start inside the clip polygon: pull them towards the centre until they are.
      for (let i = 0; i < 20 && !polygonContains(clip, p); i++) p = [(p[0] + c[0]) / 2, (p[1] + c[1]) / 2];
      return p;
    })
    .stop();
  let state = sim.state();
  for (let i = 0; !state.ended && i < 200; i++) { sim.tick(); state = sim.state(); }
  if (state.polygons.length !== n) return null;
  return state.polygons.map(p => ({ item: p.site.originalObject.data.originalData as Item, polygon: Array.from(p) as Polygon }));
}

/** Fallback: straight west → east stripes by weight. Always gives every item a cell of the right area. */
function stripes(poly: Polygon, ranked: Item[]) {
  const { pieces } = bandSplit(poly, ranked.map((item, i) => ({ key: String(i), weight: item.totals.weight, items: [item] })));
  return pieces.map(p => ({ item: p.items[0], polygon: p.polygon }));
}

/** Chapter › … › parent territory, for the info panel. */
export function ancestry(region: Region): Region[] {
  const path: Region[] = [];
  for (let r = region.parent; r; r = r.parent) path.unshift(r);
  return path;
}
