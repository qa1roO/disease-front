import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { area, bandSplit, type Polygon } from './geometry';
import { chapterSummaries, continent, layoutMap, MIN_SHARE, minimumSize } from './layout';
import { sideOf, type MapData, type MapNode } from './types';

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

  it('draws exactly one straight front line per territory, between its held and contested bands', () => {
    const statuses: MapNode['status'][] = [5, 2, null, 4, 3, 1, 4, null, 5, 2, 3, 4];
    const mixed: MapNode = { kind: 'root', title: 'All', children: [
      { kind: 'chapter', code: '01', title: 'One', uri: '1', children: statuses.map((s, i) => province(`p${i}`, s)) },
      { kind: 'chapter', code: '02', title: 'Two', uri: '2', children: [province('h', 2), province('f')] },
    ] };
    const kinds = layoutMap(mixed).borders.map(b => b.kind);
    expect(kinds.filter(k => k === 'front')).toHaveLength(1);
    // Chapter one's contested | fog edge and chapter two's held | fog edge.
    expect(kinds.filter(k => k === 'fog-edge')).toHaveLength(2);
  });

  it('summarises each chapter zoomed out as held | contested | fog bands by burden, one front line each', () => {
    const sized = (code: string, size: number, status: MapNode['status']): MapNode => ({ ...province(code, status), size });
    const two: MapNode = { kind: 'root', title: 'All', children: [
      { kind: 'chapter', code: '01', title: 'One', uri: '1', children: [
        { kind: 'block', code: 'B', title: 'B', uri: 'b', children: [sized('a', 30, 2), sized('b', 10, 5)] },
        { kind: 'block', code: 'C', title: 'C', uri: 'c', children: [sized('c', 30, 3), sized('d', 30, null)] },
      ] },
      { kind: 'chapter', code: '02', title: 'Two', uri: '2', children: [sized('e', 100, 4)] },
    ] };
    const layout = layoutMap(two);
    const summaries = chapterSummaries(layout, two);
    const one = summaries.find(s => s.region.node.code === '01')!, other = summaries.find(s => s.region.node.code === '02')!;
    expect(one.pieces.map(p => p.key)).toEqual(['held', 'contested', 'fog']);
    expect(area(one.pieces[0].polygon) / area(one.region.polygon)).toBeCloseTo(0.6, 2);
    expect(one.borders.map(b => b.kind)).toEqual(['front', 'fog-edge']);
    expect(other.pieces.map(p => p.key)).toEqual(['contested']);
    expect(other.borders).toHaveLength(0);
  });

  it('gives a province with no burden the minimum size, a share of the mean', () => {
    const sized = (code: string, size: number): MapNode => ({ ...province(code), size });
    const small: MapNode = { kind: 'root', title: 'All', children: [
      { kind: 'chapter', code: '01', title: 'One', uri: '1', children: [sized('big', 100), sized('mid', 50), sized('fog', 0)] },
    ] };
    expect(minimumSize(small)).toBeCloseTo((MIN_SHARE * 150) / 3);
    const layout = layoutMap(small);
    const share = (code: string) => area(layout.provinces.find(p => p.node.code === code)!.polygon) / area(continent());
    expect(share('fog')).toBeGreaterThan(0);
    expect(share('fog')).toBeCloseTo(1 / 151, 2);
    expect(share('big') / share('mid')).toBeCloseTo(2, 0);
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

    // One front line for every set of sibling provinces (a territory's direct provinces) holding both sides.
    let contestedSets = 0;
    (function walk(n: MapNode) {
      if (!n.children) return;
      const sides = new Set(n.children.filter(c => !c.children).map(c => sideOf(c.status)));
      if (sides.has('held') && sides.has('contested')) contestedSets++;
      n.children.forEach(walk);
    })(data.root);
    console.log(`front lines: ${contestedSets} territories hold both held and contested provinces`);
    expect(first.borders.filter(b => b.kind === 'front')).toHaveLength(contestedSets);
  }, 60_000);
});
