import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { area, bandSplit, type Polygon } from './geometry';
import { continent, layoutMap } from './layout';
import type { MapData, MapNode } from './types';

const square: Polygon = [[0, 0], [100, 0], [100, 100], [0, 100]];

describe('bandSplit', () => {
  it('cuts bands with areas proportional to their weights and one border between each pair', () => {
    const { pieces, borders } = bandSplit(square, [
      { key: 'held', weight: 1, items: [] },
      { key: 'contested', weight: 3, items: [] },
      { key: 'fog', weight: 0, items: [] },
    ]);
    expect(pieces.map(p => p.key)).toEqual(['held', 'contested']);
    expect(area(pieces[0].polygon) / area(square)).toBeCloseTo(0.25, 3);
    expect(borders).toHaveLength(1);
    expect(borders[0].between).toEqual(['held', 'contested']);
  });
});

const province = (code: string, status: MapNode['status'] = null): MapNode =>
  ({ kind: 'category', code, title: code, uri: code, size: 1, status });

describe('layoutMap', () => {
  const root: MapNode = {
    kind: 'root', title: 'All', children: [
      { kind: 'chapter', code: '01', title: 'One', uri: '1', children: [
        { kind: 'block', code: 'B1', title: 'Mixed', uri: 'b1', children: [
          province('a', 2), province('b', 5),
          { kind: 'category', code: 'c', title: 'Deep', uri: 'c', children: [province('c.0'), province('c.1')] },
        ] },
      ] },
      { kind: 'chapter', code: '02', title: 'Two', uri: '2', children: [province('d'), province('e', 3)] },
    ],
  };

  it('gives every province one cell, territories at any depth, and areas by size', () => {
    const layout = layoutMap(root);
    expect(layout.provinces.map(p => p.node.code).sort()).toEqual(['a', 'b', 'c.0', 'c.1', 'd', 'e']);
    expect(layout.territories.map(t => [t.node.code, t.depth])).toEqual([['01', 0], ['B1', 1], ['c', 2], ['02', 0]]);
    const total = area(continent());
    for (const p of layout.provinces) expect(area(p.polygon) / total).toBeCloseTo(1 / 6, 1);
  });

  it('draws a front line between held and contested provinces', () => {
    expect(layoutMap(root).borders.map(b => b.kind)).toContain('front');
  });

  it('is deterministic', () => {
    expect(JSON.stringify(layoutMap(root))).toEqual(JSON.stringify(layoutMap(root)));
  });
});

describe('layoutMap on the real map.json', () => {
  const data: MapData = JSON.parse(readFileSync(new URL('../public/map.json', import.meta.url), 'utf8'));

  it('lays out every province, deterministically', () => {
    const t0 = performance.now();
    const first = layoutMap(data.root);
    const ms = performance.now() - t0;
    console.log(`layout: ${first.provinces.length} provinces, ${first.territories.length} territories, ` +
      `${first.fallbacks} stripe fallbacks, ${Math.round(ms)} ms (Node)`);
    expect(first.provinces).toHaveLength(data.meta.counts.provinces);
    expect(first.territories).toHaveLength(data.meta.counts.chapters + data.meta.counts.territories);
    const second = layoutMap(data.root);
    expect(second.provinces.map(p => p.polygon)).toEqual(first.provinces.map(p => p.polygon));
  }, 60_000);
});
