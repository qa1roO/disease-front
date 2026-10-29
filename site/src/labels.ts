// Labels by zoom: each region's label shows from the zoom where it fits inside its region until most of
// its children's labels fit, and never while an ancestor's label is showing. So chapters show zoomed
// out, territories in the middle range and provinces zoomed in, at any nesting depth.
import { polygonCentroid } from 'd3';
import { chords, type Point } from './geometry';
import type { Layout, Region } from './layout';

/** Screen font size in px by level. */
const FONT = { chapter: 15, territory: 11.5, province: 10 };
const LINE_HEIGHT = 1.15;
const MAX_LINES = 3;

export interface Label {
  region: Region;
  at: Point;
  lines: string[];
  fontSize: number;
  level: 'chapter' | 'territory' | 'province';
  /** Shown while fitZoom <= k < hideZoom, k being screen px per world unit. */
  fitZoom: number;
  hideZoom: number;
  parent: Label | null;
}

export type Measure = (text: string, fontSize: number, bold: boolean) => number;
export const estimateWidth: Measure = (text, fontSize, bold) => text.length * fontSize * (bold ? 0.6 : 0.54);

/** Split words into n lines of roughly equal length. */
function wrap(words: string[], n: number): string[] {
  const target = words.join(' ').length / n, lines: string[] = [];
  let line = '';
  for (const w of words) {
    if (line && line.length + w.length / 2 > target && lines.length < n - 1) { lines.push(line); line = w; }
    else line = line ? `${line} ${w}` : w;
  }
  lines.push(line);
  return lines;
}

export function buildLabels(layout: Layout, measure: Measure = estimateWidth): Label[] {
  const byRegion = new Map<Region, Label>();
  const children = new Map<Label, Label[]>();
  const labels: Label[] = [];
  for (const region of [...layout.territories, ...layout.provinces]) {
    const level = region.isProvince ? 'province' : region.depth === 0 ? 'chapter' : 'territory';
    const fontSize = FONT[level];
    const at = polygonCentroid(region.polygon) as Point;
    const { width, height } = chords(region.polygon, at);
    const words = region.node.title.split(/\s+/);
    let best = { lines: [region.node.title], fitZoom: Infinity };
    for (let n = 1; n <= Math.min(MAX_LINES, words.length); n++) {
      const lines = wrap(words, n);
      const w = Math.max(...lines.map(l => measure(l, fontSize, level === 'chapter')));
      const fitZoom = Math.max(w / (0.9 * width), (lines.length * LINE_HEIGHT * fontSize) / (0.85 * height));
      if (fitZoom < best.fitZoom) best = { lines, fitZoom };
    }
    const label: Label = { region, at, fontSize, level, ...best, hideZoom: Infinity, parent: null };
    labels.push(label);
    byRegion.set(region, label);
  }
  for (const label of labels) {
    label.parent = label.region.parent ? byRegion.get(label.region.parent)! : null;
    if (label.parent) {
      if (!children.has(label.parent)) children.set(label.parent, []);
      children.get(label.parent)!.push(label);
    }
  }
  for (const [label, kids] of children) {
    const fits = kids.map(k => k.fitZoom).sort((a, b) => a - b);
    label.hideZoom = Math.max(label.fitZoom, fits[Math.floor(fits.length / 2)]);
  }
  return labels;
}

/** Labels to show at zoom k. Territories come before their descendants in `labels`. */
export function visibleLabels(labels: Label[], k: number): Label[] {
  const showing = new Set<Label>();
  const blocked = new Set<Label>(); // an ancestor is showing
  for (const l of labels) {
    if (l.parent && (showing.has(l.parent) || blocked.has(l.parent))) { blocked.add(l); continue; }
    if (l.fitZoom <= k && k < l.hideZoom) showing.add(l);
  }
  return [...showing];
}
