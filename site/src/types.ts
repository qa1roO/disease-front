// Shape of site/public/map.json (written by pipeline stage 8, see pipeline/site_data.py).

/** 1 Eradicated … 5 Untreatable (ADR 0001); null is fog. */
export type Status = 1 | 2 | 3 | 4 | 5 | null;

export interface MapNode {
  kind: 'root' | 'chapter' | 'block' | 'category';
  code?: string;
  title: string;
  uri?: string;
  children?: MapNode[];
  /** Provinces only: size in DALYs (0 without a GBD cause: the layout gives it the minimum size) and status. */
  size?: number;
  status?: Status;
  /** True when the status is inherited from the province's GBD cause rather than assessed for it. */
  provisional?: boolean;
  /** Provinces assessed directly (not inherited from a GBD cause): the approved assessment itself. */
  assessment?: Assessment;
  /** Provinces only, absent when no GBD cause covers the province. */
  burden?: Burden;
  /** Pipeline bar: the GBD cause's furthest phase, or 'approved' when held. Absent when there's no bar. */
  pipeline?: Phase;
}

/** No registered trial, Phase 1-3 (running ClinicalTrials.gov trials), Approved (held provinces only). */
export type Phase = 'none' | 'phase1' | 'phase2' | 'phase3' | 'approved';

/** A GBD cause's pipeline bar (pipeline stage 7). */
export interface PipelineBar {
  phase: Exclude<Phase, 'approved'>;
  /** Interventional trials still running (recruiting or active), first posted since meta.clinicaltrials.registeredSince. */
  trials: number;
  /** The same search on ClinicalTrials.gov. */
  url: string;
}

/** How a province got its size (pipeline stage 4). */
export interface Burden {
  dalys: number;
  /** True when the GBD cause's DALYs are split among several provinces. */
  estimated: boolean;
  /** Key into meta.gbdCauses. */
  cause: number;
  /** How the cross-walk picked the cause: every ICD-10 code agreed, a majority did, or the owner's review file. */
  method: 'direct' | 'majority' | 'review';
  /** The ICD-10 code WHO maps this disease to. */
  icd10: string;
  /** method 'review' only: false while the cause is still the review file's placeholder pick. */
  reviewed?: boolean;
}

export interface GbdCause {
  name: string;
  dalys: number | null;
  provinces: number;
  /** For a GBD parent standing in for sub-causes that have no ICD-10 codes of their own. */
  members?: string[];
  /** The owner-approved stage-6 proposal for this cause; its provinces inherit the status as provisional. */
  assessment?: Assessment;
  /** Absent until the cause's MeSH terms are reviewed and stage 7 has run. */
  bar?: PipelineBar;
}

export interface Assessment {
  status: 1 | 2 | 3 | 4 | 5;
  /** Typical-patient caveat, e.g. "curable if caught early"; may be empty. */
  nuance: string;
  sources: { url: string; title: string }[];
  /** "ok", or "flag: …" when the status disagrees with ChEMBL's approved-drug data. */
  crossCheck: string;
}

export interface MapData {
  meta: {
    icd11: { release: string; version: string; source: string; citation: string };
    counts: { chapters: number; territories: number; provinces: number };
    gbd: { round: string; released: string; estimateYear: number; measure: string; fetched: string; citation: string };
    /** The cross-walk's "project's own work" notice. */
    crosswalk: string;
    gbdCauses: Record<string, GbdCause>;
    /** Present once stage 7 has run: the API's data date ("data as of") and the trial window. */
    clinicaltrials?: { apiVersion: string; dataTimestamp: string; registeredSince: string; statuses: string[] };
  };
  root: MapNode;
}

export type Side = 'held' | 'contested' | 'fog';
export const sideOf = (s: Status | undefined): Side => (s == null ? 'fog' : s <= 3 ? 'held' : 'contested');
