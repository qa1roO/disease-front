// Shape of site/public/map.json (written by pipeline stage 8, see pipeline/site_data.py).

/** 1 Eradicated … 5 Untreatable (ADR 0001); null is fog. */
export type Status = 1 | 2 | 3 | 4 | 5 | null;

export interface MapNode {
  kind: 'root' | 'chapter' | 'block' | 'category';
  code?: string;
  title: string;
  uri?: string;
  children?: MapNode[];
  /** Provinces only: relative size (burden, later) and status. */
  size?: number;
  status?: Status;
}

export interface MapData {
  meta: {
    icd11: { release: string; version: string; source: string; citation: string };
    counts: { chapters: number; territories: number; provinces: number };
  };
  root: MapNode;
}

export type Side = 'held' | 'contested' | 'fog';
export const sideOf = (s: Status | undefined): Side => (s == null ? 'fog' : s <= 3 ? 'held' : 'contested');
