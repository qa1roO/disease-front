// The info panel: what's known about the clicked province or territory. Missing data reads "no data".
import { ancestry, type Region } from './layout';
import { sideOf, type MapData, type MapNode } from './types';
import { STATUS_NAME } from './status';

const NO_DATA = '<span class="no-data">no data</span>';

const esc = (s: string) => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!);

/** The ICD-11 browser page for an MMS linearization URI. */
export function browserUrl(uri: string, release: string): string {
  return `https://icd.who.int/browse/${release}/mms/en#${uri.replace(/^.*\/mms\//, '')}`;
}

/** DALYs for reading: 1,218,519 · 3.4 million · 87 million. */
export function formatDalys(x: number): string {
  if (x >= 1e7) return `${Math.round(x / 1e6).toLocaleString('en')} million`;
  if (x >= 1e6) return `${(x / 1e6).toFixed(1)} million`;
  return Math.round(x).toLocaleString('en');
}

/** "Oct 2025" from "2025-10". */
const month = (ym: string) => new Date(`${ym}-01T00:00:00Z`).toLocaleString('en', { month: 'short', year: 'numeric', timeZone: 'UTC' });

const KIND: Record<string, string> = { chapter: 'Chapter', block: 'Block', category: 'Category' };
const METHOD: Record<string, string> = {
  direct: 'all its ICD-10 codes point to this cause',
  majority: 'most of its ICD-10 codes point to this cause',
  review: 'its ICD-10 codes split evenly between causes; picked in the review file',
};

function bar(name: string) {
  return `<div class="bar"><span>${name}</span><div class="track off"></div>${NO_DATA}</div>`;
}

function provinceBurden(node: MapNode, meta: MapData['meta']): string {
  const b = node.burden;
  const asOf = `${meta.gbd.round} (released ${month(meta.gbd.released)}), ${meta.gbd.estimateYear} estimates`;
  if (!b) {
    return `
      <dt>Burden</dt><dd>${NO_DATA} <span class="note">minimum size: no GBD cause covers this disease</span></dd>
      <dt>GBD cause</dt><dd>${NO_DATA}</dd>
      <dt>GBD data</dt><dd>${esc(asOf)}</dd>`;
  }
  const cause = meta.gbdCauses[String(b.cause)];
  const dalys = b.dalys > 0 ? `${formatDalys(b.dalys)} DALYs` : `${NO_DATA} <span class="note">GBD gives this cause no DALYs; minimum size</span>`;
  const estimated = b.estimated && cause?.dalys
    ? `<span class="note">size estimated: an equal 1/${cause.provinces} share of the cause's ${formatDalys(cause.dalys)}</span>`
    : '';
  const members = cause?.members?.length
    ? `<span class="note">GBD has no ICD-10 codes for its sub-causes (${cause.members.map(esc).join('; ')}), so they count here together</span>`
    : '';
  return `
      <dt>Burden</dt><dd>${dalys} ${estimated}</dd>
      <dt>GBD cause</dt><dd>${esc(cause?.name ?? String(b.cause))} ${members}
        <span class="note">via ICD-10 ${esc(b.icd10)}: ${METHOD[b.method] ?? b.method}${b.method === 'review' && !b.reviewed ? ' (placeholder, not yet reviewed)' : ''}</span></dd>
      <dt>GBD data</dt><dd>${esc(asOf)}</dd>`;
}

export function renderPanel(el: HTMLElement, region: Region, meta: MapData['meta'], select: (r: Region) => void) {
  const { node } = region;
  const path = ancestry(region);
  const crumbs = path.map((r, i) => `<a href="#" data-i="${i}">${esc(r.node.title)}</a>`).join(' › ') || 'Top level';
  const uri = node.uri ?? '';
  const head = `
    <button class="close" aria-label="Close">×</button>
    <div class="kind">${region.isProvince ? 'Province' : `Territory · ${KIND[node.kind] ?? node.kind}`}</div>
    <h2>${esc(node.title)}</h2>
    <dl>
      <dt>${node.kind === 'block' ? 'ICD-11 block' : 'ICD-11 code'}</dt><dd>${esc(node.kind === 'chapter' ? `Chapter ${node.code}` : node.code ?? '')}</dd>
      <dt>Hierarchy</dt><dd class="crumbs">${crumbs}</dd>
      <dt>ICD-11 URI</dt><dd><a href="${esc(browserUrl(uri, meta.icd11.release))}" target="_blank" rel="noopener">${esc(uri)}</a></dd>`;
  let body: string;
  if (region.isProvince) {
    const status = node.status;
    body = `
      <dt>Status</dt><dd>${status == null ? 'Fog (not assessed)' : STATUS_NAME[status]}</dd>
      ${provinceBurden(node, meta)}
    </dl>
    ${bar('Pipeline')}${bar('Activity')}${bar('Access')}`;
  } else {
    const provinces: MapNode[] = [];
    (function collect(n: MapNode) { if (n.children) n.children.forEach(collect); else provinces.push(n); })(node);
    const total = provinces.reduce((s, p) => s + (p.burden?.dalys ?? 0), 0);
    const unsized = provinces.filter(p => !p.burden).length;
    // Shares by burden; a territory with no burden at all falls back to counting provinces.
    const weight = (p: MapNode) => (total > 0 ? p.burden?.dalys ?? 0 : 1);
    const all = provinces.reduce((s, p) => s + weight(p), 0);
    const share = (side: string) => provinces.filter(p => sideOf(p.status) === side).reduce((s, p) => s + weight(p), 0) / all;
    const pct = (x: number) => `${Math.round(x * 100)}%`;
    body = `
      <dt>Provinces</dt><dd>${provinces.length.toLocaleString('en')}${unsized ? ` <span class="note">${unsized.toLocaleString('en')} with no GBD cause</span>` : ''}</dd>
      <dt>Burden</dt><dd>${total > 0 ? `${formatDalys(total)} DALYs` : NO_DATA}</dd>
      <dt>Held · contested · fog</dt><dd>${pct(share('held'))} · ${pct(share('contested'))} · ${pct(share('fog'))} <span class="note">${total > 0 ? 'by burden' : 'by count'}</span></dd>
    </dl>`;
  }
  el.innerHTML = head + body;
  el.hidden = false;
  el.querySelector<HTMLButtonElement>('.close')!.onclick = () => { el.hidden = true; };
  el.querySelectorAll<HTMLAnchorElement>('.crumbs a').forEach(a => {
    a.onclick = e => { e.preventDefault(); select(path[Number(a.dataset.i)]); };
  });
}
