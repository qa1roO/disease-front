// The map drawn on a canvas: SVG with ~9,300 paths stuttered while panning (ticket 06). Shapes are batched into
// one Path2D per fill colour and per line style, so a frame is a few dozen draw calls. Line widths are divided by
// the zoom so strokes keep the same screen width at every zoom, as SVG's non-scaling-stroke did.
import { polygonContains } from 'd3';
import type { Point, Polygon, Segment } from './geometry';
import type { Border, Layout, Region, Summary } from './layout';
import { fill, FOG, FRONT } from './status';

interface Line { path: Path2D; color: string; width: number; dash?: [number, number] }

export interface Scene {
  provinces: { path: Path2D; color: string }[];
  provinceEdges: Line;
  summaryPieces: { path: Path2D; color: string }[];
  summaryLines: Line[];
  territoryBorders: Line;
  chapterBorders: Line;
  detailLines: Line[];
}

const SEA = '#0e1621';
const FOG_EDGE = '#c9d1d9';

function addPolygon(path: Path2D, poly: Polygon) {
  poly.forEach((p, i) => (i ? path.lineTo(p[0], p[1]) : path.moveTo(p[0], p[1])));
  path.closePath();
}

function addSegment(path: Path2D, s: Segment) {
  path.moveTo(s[0][0], s[0][1]);
  path.lineTo(s[1][0], s[1][1]);
}

function byColor<T>(items: T[], color: (t: T) => string, poly: (t: T) => Polygon) {
  const paths = new Map<string, Path2D>();
  for (const item of items) {
    const c = color(item);
    if (!paths.has(c)) paths.set(c, new Path2D());
    addPolygon(paths.get(c)!, poly(item));
  }
  return [...paths].map(([color, path]) => ({ path, color }));
}

function lines(borders: Border[], front: number, fog: number): Line[] {
  const frontPath = new Path2D(), fogPath = new Path2D();
  for (const b of borders) addSegment(b.kind === 'front' ? frontPath : fogPath, b.segment);
  return [{ path: fogPath, color: FOG_EDGE, width: fog, dash: [3, 4] }, { path: frontPath, color: FRONT, width: front }];
}

export function buildScene(layout: Layout, summaries: Summary[]): Scene {
  const outline = (regions: Region[]) => { const p = new Path2D(); regions.forEach(r => addPolygon(p, r.polygon)); return p; };
  const summaryColor = { held: fill(2), contested: fill(4), fog: FOG };
  return {
    provinces: byColor(layout.provinces, r => fill(r.node.status, r.node.provisional), r => r.polygon),
    provinceEdges: { path: outline(layout.provinces), color: SEA, width: 0.35 },
    summaryPieces: byColor(summaries.flatMap(s => s.pieces), p => summaryColor[p.key], p => p.polygon),
    summaryLines: lines(summaries.flatMap(s => s.borders), 3.2, 1.2),
    territoryBorders: { path: outline(layout.territories.filter(t => t.depth > 0)), color: '#05080c', width: 1 },
    chapterBorders: { path: outline(layout.territories.filter(t => t.depth === 0)), color: '#000', width: 2.6 },
    detailLines: lines(layout.borders, 2.2, 0.8),
  };
}

/** Draw the scene at zoom transform (x, y, k); summary is the zoomed-out summary's opacity (0-1). */
export function drawScene(ctx: CanvasRenderingContext2D, scene: Scene, t: { x: number; y: number; k: number }, summary: number) {
  const dpr = devicePixelRatio || 1;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  ctx.setTransform(dpr * t.k, 0, 0, dpr * t.k, dpr * t.x, dpr * t.y);
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  const stroke = (line: Line, alpha = 1) => {
    if (alpha <= 0) return;
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = line.color;
    ctx.lineWidth = line.width / t.k;
    ctx.setLineDash(line.dash ? line.dash.map(d => d / t.k) : []);
    ctx.stroke(line.path);
  };
  const fillAll = (fills: { path: Path2D; color: string }[], alpha = 1) => {
    if (alpha <= 0) return;
    ctx.globalAlpha = alpha;
    for (const f of fills) { ctx.fillStyle = f.color; ctx.fill(f.path); }
  };
  fillAll(scene.provinces);
  stroke(scene.provinceEdges);
  fillAll(scene.summaryPieces, summary);
  scene.summaryLines.forEach(l => stroke(l, summary));
  stroke(scene.territoryBorders, 1 - summary);
  stroke(scene.chapterBorders);
  scene.detailLines.forEach(l => stroke(l, 1 - summary));
  ctx.globalAlpha = 1;
}

/** Which province is at a world point: a grid of bounding boxes, then a point-in-polygon test. */
export class ProvinceIndex {
  private cells = new Map<number, Region[]>();
  private readonly size: number;

  constructor(provinces: Region[], cellSize = 25) {
    this.size = cellSize;
    for (const r of provinces) {
      const xs = r.polygon.map(p => p[0]), ys = r.polygon.map(p => p[1]);
      for (let i = this.cell(Math.min(...xs)); i <= this.cell(Math.max(...xs)); i++) {
        for (let j = this.cell(Math.min(...ys)); j <= this.cell(Math.max(...ys)); j++) {
          const key = i * 100000 + j;
          if (!this.cells.has(key)) this.cells.set(key, []);
          this.cells.get(key)!.push(r);
        }
      }
    }
  }

  private cell(v: number) { return Math.floor(v / this.size); }

  at(p: Point): Region | null {
    return this.cells.get(this.cell(p[0]) * 100000 + this.cell(p[1]))?.find(r => polygonContains(r.polygon, p)) ?? null;
  }
}
