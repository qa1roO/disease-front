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
  /** Provinces only, absent when no GBD cause covers the province. */
  burden?: Burden;
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
}

export interface MapData {
  meta: {
    icd11: { release: string; version: string; source: string; citation: string };
    counts: { chapters: number; territories: number; provinces: number };
    gbd: { round: string; released: string; estimateYear: number; measure: string; fetched: string; citation: string };
    /** The cross-walk's "project's own work" notice. */
    crosswalk: string;
    gbdCauses: Record<string, GbdCause>;
  };
  root: MapNode;
}

export type Side = 'held' | 'contested' | 'fog';
export const sideOf = (s: Status | undefined): Side => (s == null ? 'fog' : s <= 3 ? 'held' : 'contested');
