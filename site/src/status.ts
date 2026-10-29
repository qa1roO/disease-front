import { interpolateRgb } from 'd3';
import type { Status } from './types';

export const STATUS_NAME: Record<1 | 2 | 3 | 4 | 5, string> = {
  1: 'Eradicated', 2: 'Curable', 3: 'Controlled', 4: 'Treatable', 5: 'Untreatable',
};
const STATUS_COLOR: Record<1 | 2 | 3 | 4 | 5, string> = {
  1: '#0f6b4b', 2: '#2e9e6a', 3: '#8fd1a8', 4: '#f2a65a', 5: '#d64545',
};
export const FOG = '#4f5866';
export const FRONT = '#ffe08a';

/** Fill for a province. A provisional status is the same hue at a lighter tint. */
export function fill(status: Status | undefined, provisional = false): string {
  if (status == null) return FOG;
  return provisional ? interpolateRgb(STATUS_COLOR[status], '#ffffff')(0.4) : STATUS_COLOR[status];
}
