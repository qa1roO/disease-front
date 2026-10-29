// The info panel: what's known about the clicked province or territory. Missing data reads "no data".
import { ancestry, type Region } from './layout';
import { sideOf } from './types';
import { STATUS_NAME } from './status';

const NO_DATA = '<span class="no-data">no data</span>';

const esc = (s: string) => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!);

/** The ICD-11 browser page for an MMS linearization URI. */
export function browserUrl(uri: string, release: string): string {
  return `https://icd.who.int/browse/${release}/mms/en#${uri.replace(/^.*\/mms\//, '')}`;
}

const KIND: Record<string, string> = { chapter: 'Chapter', block: 'Block', category: 'Category' };

function bar(name: string) {
  return `<div class="bar"><span>${name}</span><div class="track off"></div>${NO_DATA}</div>`;
}

export function renderPanel(el: HTMLElement, region: Region, release: string, select: (r: Region) => void) {
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
      <dt>ICD-11 URI</dt><dd><a href="${esc(browserUrl(uri, release))}" target="_blank" rel="noopener">${esc(uri)}</a></dd>`;
  let body: string;
  if (region.isProvince) {
    const status = node.status;
    body = `
      <dt>Status</dt><dd>${status == null ? 'Fog (not assessed)' : STATUS_NAME[status]}</dd>
      <dt>Burden</dt><dd>${NO_DATA}</dd>
      <dt>GBD cause</dt><dd>${NO_DATA}</dd>
    </dl>
    ${bar('Pipeline')}${bar('Activity')}${bar('Access')}`;
  } else {
    const provinces: { status?: number | null }[] = [];
    (function collect(n: typeof node) { if (n.children) n.children.forEach(collect); else provinces.push(n); })(node);
    const share = (side: string) => provinces.filter(p => sideOf(p.status as never) === side).length / provinces.length;
    const pct = (x: number) => `${Math.round(x * 100)}%`;
    body = `
      <dt>Provinces</dt><dd>${provinces.length.toLocaleString('en')}</dd>
      <dt>Burden</dt><dd>${NO_DATA}</dd>
      <dt>Held · contested · fog</dt><dd>${pct(share('held'))} · ${pct(share('contested'))} · ${pct(share('fog'))} <span class="no-data">(by count until burden is in)</span></dd>
    </dl>`;
  }
  el.innerHTML = head + body;
  el.hidden = false;
  el.querySelector<HTMLButtonElement>('.close')!.onclick = () => { el.hidden = true; };
  el.querySelectorAll<HTMLAnchorElement>('.crumbs a').forEach(a => {
    a.onclick = e => { e.preventDefault(); select(path[Number(a.dataset.i)]); };
  });
}
