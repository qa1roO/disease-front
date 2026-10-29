// The pipeline bar for a province (pipeline stages 7-8): its GBD cause's furthest trial phase, or Approved.
import type { MapData, MapNode, Phase } from './types';

export const STEPS: Record<Phase, { step: number; label: string }> = {
  none: { step: 0, label: 'No registered trial' },
  phase1: { step: 1, label: 'Phase 1' },
  phase2: { step: 2, label: 'Phase 2' },
  phase3: { step: 3, label: 'Phase 3' },
  approved: { step: 4, label: 'Approved' },
};

export interface PipelineView {
  step: number;
  label: string;
  /** The cause's matching ClinicalTrials.gov trials and the search that finds them; absent with no GBD cause. */
  trials?: number;
  url?: string;
  note: string;
}

/** null when the province has no bar: no reviewed MeSH terms for its cause yet, or no cause and not held. */
export function pipelineView(node: MapNode, meta: MapData['meta']): PipelineView | null {
  if (!node.pipeline) return null;
  const bar = node.burden ? meta.gbdCauses[String(node.burden.cause)]?.bar : undefined;
  const { step } = STEPS[node.pipeline];
  let { label } = STEPS[node.pipeline];
  const ct = meta.clinicaltrials;
  const trials = bar ? `${bar.trials.toLocaleString('en')} interventional trial${bar.trials === 1 ? '' : 's'} first posted since ${ct?.registeredSince}` : '';
  let note: string;
  if (node.pipeline === 'approved' && bar?.phase !== 'approved') note = 'held: a treatment cures or controls it';
  else if (node.pipeline === 'approved') note = `ChEMBL (${ct?.chembl}) lists an approved drug for this cause`;
  else if (node.pipeline === 'none' && bar?.trials) {
    // Phase "NA" trials count toward the total but set no phase.
    label = 'No phased trial';
    note = `${trials}, none in Phase 1-4 (e.g. device or behavioural studies)`;
  } else note = `furthest phase among ${trials}`;
  return bar ? { step, label, trials: bar.trials, url: bar.url, note } : { step, label, note };
}
