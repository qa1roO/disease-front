import { polygonCentroid } from 'd3';
import { describe, expect, it } from 'vitest';
import { ProvinceIndex } from './canvas';
import type { Point } from './geometry';
import { layoutMap } from './layout';
import { packLayout, unpackLayout } from './precomputed';
import type { MapNode } from './types';

const province = (code: string, status: MapNode['status'] = null, size = 1): MapNode =>
  ({ kind: 'category', code, title: code, uri: code, size, status });

const root: MapNode = {
  kind: 'root', title: 'All', children: [
    { kind: 'chapter', code: '01', title: 'One', uri: '1', children: [
      { kind: 'block', code: 'B1', title: 'Mixed', uri: 'b1', children: [
        province('a', 2, 5), province('b', 5, 3),
        { kind: 'category', code: 'c', title: 'Deep', uri: 'c', children: [province('c.0'), province('c.1', 4)] },
      ] },
    ] },
    { kind: 'chapter', code: '02', title: 'Two', uri: '2', children: [province('d'), province('e', 3, 8)] },
  ],
};

describe('packLayout / unpackLayout', () => {
  it('restores the same regions, hierarchy and borders, to two decimals', () => {
    const layout = layoutMap(root);
    const restored = unpackLayout(JSON.parse(JSON.stringify(packLayout(layout, root))), root);
    const shape = (l: typeof layout) => ({
      territories: l.territories.map(r => [r.node, r.depth, r.parent?.node ?? null, r.isProvince]),
      provinces: l.provinces.map(r => [r.node, r.depth, r.parent?.node ?? null, r.isProvince]),
      borders: l.borders.map(b => b.kind),
      fallbacks: l.fallbacks,
    });
    expect(shape(restored)).toEqual(shape(layout));
    restored.provinces.forEach((r, i) => r.polygon.forEach((p, j) => {
      expect(p[0]).toBeCloseTo(layout.provinces[i].polygon[j][0], 2);
      expect(p[1]).toBeCloseTo(layout.provinces[i].polygon[j][1], 2);
    }));
  });
});

describe('ProvinceIndex', () => {
  it('finds the province under a point, and nothing off the map', () => {
    const layout = layoutMap(root);
    const index = new ProvinceIndex(layout.provinces);
    for (const r of layout.provinces) expect(index.at(polygonCentroid(r.polygon) as Point)).toBe(r);
    expect(index.at([-50, -50])).toBeNull();
  });
});
