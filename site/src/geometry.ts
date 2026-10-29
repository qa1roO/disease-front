// Plane geometry for convex polygons: band cuts along a fixed direction, chords for label fitting.
import { polygonArea } from 'd3';

export type Point = [number, number];
export type Polygon = Point[];
export type Segment = [Point, Point];

export const area = (p: Polygon): number => (p.length < 3 ? 0 : Math.abs(polygonArea(p)));

/** The map's west → east direction: held provinces sit west, contested and fog east. */
export const EAST: Point = [Math.cos(0.21), Math.sin(0.21)];
export const NORTH: Point = [-EAST[1], EAST[0]];
const along = (p: Point, d: Point = EAST) => p[0] * d[0] + p[1] * d[1];

/** Keep the part of a convex polygon west of (keepWest) or east of the line along(p) = t. */
export function clipHalf(poly: Polygon, t: number, keepWest: boolean): Polygon {
  const inside = (p: Point) => (keepWest ? along(p) <= t : along(p) >= t);
  const out: Polygon = [];
  for (let i = 0; i < poly.length; i++) {
    const a = poly[i], b = poly[(i + 1) % poly.length];
    const ia = inside(a), ib = inside(b);
    if (ia) out.push(a);
    if (ia !== ib) {
      const s = (t - along(a)) / (along(b) - along(a));
      out.push([a[0] + s * (b[0] - a[0]), a[1] + s * (b[1] - a[1])]);
    }
  }
  return out;
}

/** The cut position t that leaves `fraction` of the polygon's area west of it. */
export function cutAt(poly: Polygon, fraction: number): number {
  const total = area(poly);
  const ts = poly.map(p => along(p));
  let lo = Math.min(...ts), hi = Math.max(...ts);
  for (let i = 0; i < 40; i++) {
    const mid = (lo + hi) / 2;
    if (area(clipHalf(poly, mid, true)) < fraction * total) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
}

/** Where the line along(p) = t crosses a convex polygon, or null if it misses. */
export function segmentAt(poly: Polygon, t: number): Segment | null {
  const pts: Point[] = [];
  for (let i = 0; i < poly.length; i++) {
    const a = poly[i], b = poly[(i + 1) % poly.length];
    const da = along(a) - t, db = along(b) - t;
    if (da * db < 0) {
      const s = da / (da - db);
      pts.push([a[0] + s * (b[0] - a[0]), a[1] + s * (b[1] - a[1])]);
    }
  }
  return pts.length >= 2 ? [pts[0], pts[1]] : null;
}

export interface Band<T> { key: string; weight: number; items: T[] }
export interface BandPiece<T> extends Band<T> { polygon: Polygon }
export interface BandBorder { between: [string, string]; segment: Segment }

/**
 * Cut a convex polygon into west → east bands, each with an area share equal to its weight share.
 * Empty bands are skipped. Returns the pieces and the straight borders between neighbouring bands.
 */
export function bandSplit<T>(poly: Polygon, bands: Band<T>[]): { pieces: BandPiece<T>[]; borders: BandBorder[] } {
  const kept = bands.filter(b => b.weight > 0);
  const total = kept.reduce((s, b) => s + b.weight, 0);
  const cuts: number[] = [];
  let cumulative = 0;
  for (let i = 0; i < kept.length - 1; i++) {
    cumulative += kept[i].weight;
    cuts.push(cutAt(poly, cumulative / total));
  }
  const pieces = kept.map((band, i) => {
    let p = poly;
    if (i > 0) p = clipHalf(p, cuts[i - 1], false);
    if (i < kept.length - 1) p = clipHalf(p, cuts[i], true);
    return { ...band, polygon: p };
  });
  const borders: BandBorder[] = [];
  cuts.forEach((t, i) => {
    const segment = segmentAt(poly, t);
    if (segment) borders.push({ between: [kept[i].key, kept[i + 1].key], segment });
  });
  return { pieces, borders };
}

/** Width of a convex polygon along the horizontal line through p, and height along the vertical one. */
export function chords(poly: Polygon, p: Point): { width: number; height: number } {
  const span = (axis: 0 | 1) => {
    const other = 1 - axis, hits: number[] = [];
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i], b = poly[(i + 1) % poly.length];
      const da = a[other] - p[other], db = b[other] - p[other];
      if (da === 0) hits.push(a[axis]);
      if (da * db < 0) hits.push(a[axis] + (da / (da - db)) * (b[axis] - a[axis]));
    }
    return hits.length >= 2 ? Math.max(...hits) - Math.min(...hits) : 0;
  };
  return { width: span(0), height: span(1) };
}

/** Deterministic PRNG (mulberry32). */
export function prng(seed: number): () => number {
  let a = seed | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** FNV-1a string hash, for per-territory seeds. */
export const hash = (s: string): number => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
};
