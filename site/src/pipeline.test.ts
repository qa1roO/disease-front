import { describe, expect, it } from 'vitest';
import { pipelineView } from './pipeline';
import type { MapData, MapNode } from './types';

const meta = {
  gbdCauses: {
    '554': { name: 'Motor neuron disease', dalys: 1, provinces: 1,
             bar: { phase: 'phase3', trials: 297, url: 'https://clinicaltrials.gov/search?cond=als' } },
    '302': { name: 'Diarrheal diseases', dalys: 1, provinces: 1,
             bar: { phase: 'approved', trials: 40, url: 'https://clinicaltrials.gov/search?cond=d', approved: { D003967: ['CHEMBL1'] } } },
    '999': { name: 'No terms reviewed yet', dalys: 1, provinces: 1 },
  },
  clinicaltrials: { apiVersion: '2.0.5', dataTimestamp: '2026-10-29T09:00:05', registeredSince: '2016-10-29', chembl: 'ChEMBL_37' },
} as unknown as MapData['meta'];

const province = (cause: number | null, extra: Partial<MapNode> = {}): MapNode => ({
  kind: 'category', title: 'x', size: 1, status: null,
  ...(cause == null ? {} : { burden: { dalys: 1, estimated: false, cause, method: 'direct', icd10: 'X' } }),
  ...extra,
});

describe('pipelineView', () => {
  it("shows the cause's furthest phase, its trial count and search link", () => {
    expect(pipelineView(province(554, { pipeline: 'phase3' }), meta)).toEqual({
      step: 3, label: 'Phase 3', trials: 297, url: 'https://clinicaltrials.gov/search?cond=als',
      note: 'furthest phase among 297 interventional trials first posted since 2016-10-29',
    });
  });

  it('says why a cause is Approved: ChEMBL has an approved drug', () => {
    const v = pipelineView(province(302, { pipeline: 'approved' }), meta)!;
    expect([v.step, v.label, v.trials]).toEqual([4, 'Approved', 40]);
    expect(v.note).toBe('ChEMBL (ChEMBL_37) lists an approved drug for this cause');
  });

  it('shows Approved for a held province even when its cause has only reached a trial phase', () => {
    const v = pipelineView(province(554, { pipeline: 'approved', status: 2 }), meta)!;
    expect([v.step, v.label, v.trials]).toEqual([4, 'Approved', 297]);
    expect(v.note).toBe('held: a treatment cures or controls it');
  });

  it('a held province with no GBD cause is Approved without a trial search', () => {
    expect(pipelineView(province(null, { pipeline: 'approved', status: 1 }), meta)).toEqual({
      step: 4, label: 'Approved', note: 'held: a treatment cures or controls it',
    });
  });

  it('zero trials reads No registered trial, not Preclinical', () => {
    const m = { ...meta, gbdCauses: { '1': { name: 'x', dalys: 1, provinces: 1, bar: { phase: 'none', trials: 0, url: 'u' } } } } as unknown as MapData['meta'];
    const v = pipelineView(province(1, { pipeline: 'none' }), m)!;
    expect([v.step, v.label, v.trials]).toEqual([0, 'No registered trial', 0]);
  });

  it('trials that set no phase (devices, behavioural) read No phased trial', () => {
    const m = { ...meta, gbdCauses: { '1': { name: 'x', dalys: 1, provinces: 1, bar: { phase: 'none', trials: 1, url: 'u' } } } } as unknown as MapData['meta'];
    expect(pipelineView(province(1, { pipeline: 'none' }), m)).toEqual({
      step: 0, label: 'No phased trial', trials: 1, url: 'u',
      note: '1 interventional trial first posted since 2016-10-29, none in Phase 1-4 (e.g. device or behavioural studies)',
    });
  });

  it('is no data when the province has no bar', () => {
    expect(pipelineView(province(999), meta)).toBeNull();
    expect(pipelineView(province(null), meta)).toBeNull();
  });
});
