import { pointer, select, zoom, zoomIdentity, type ZoomTransform } from 'd3';
import './style.css';
import { buildLabels, visibleLabels, type Label, type Measure } from './labels';
import { buildScene, drawScene, ProvinceIndex } from './canvas';
import { chapterSummaries, layoutMap, WORLD, type Layout, type Region } from './layout';
import { renderPanel } from './panel';
import { unpackLayout, type PackedLayout } from './precomputed';
import { fill, FOG, FRONT, STATUS_NAME } from './status';
import type { MapData } from './types';

const canvas = document.getElementById('world') as HTMLCanvasElement;
const svg = select<SVGSVGElement, unknown>('#map');
const status = document.getElementById('status')!;
const panel = document.getElementById('panel')!;

const closed = (p: [number, number][]) => `M${p.map(q => `${q[0].toFixed(2)},${q[1].toFixed(2)}`).join('L')}Z`;

/**
 * Text widths from the real font, so "fits inside its region" holds on screen. A line is measured as its words
 * plus spaces, each word once per font: labels make ~45,000 calls, mostly with repeated words.
 */
function canvasMeasure(): Measure {
  const ctx = document.createElement('canvas').getContext('2d')!;
  const family = getComputedStyle(document.body).fontFamily;
  const cache = new Map<string, number>();
  const width = (word: string, font: string) => {
    const key = `${font}|${word}`;
    let w = cache.get(key);
    if (w === undefined) {
      if (ctx.font !== font) ctx.font = font;
      cache.set(key, (w = ctx.measureText(word).width));
    }
    return w;
  };
  return (text, size, bold) => {
    const font = `${bold ? 600 : 400} ${size}px ${family}`;
    const words = text.split(' ');
    return words.reduce((s, w) => s + width(w, font), 0) + (words.length - 1) * width(' ', font);
  };
}

function legend(el: HTMLElement) {
  const row = (swatch: string, text: string) => `<div class="row">${swatch}<span>${text}</span></div>`;
  const sw = (color: string) => `<span class="sw" style="background:${color}"></span>`;
  el.innerHTML =
    ([1, 2, 3, 4, 5] as const).map(s => row(sw(fill(s)), STATUS_NAME[s])).join('') +
    row(`<span class="sw split"><i style="background:${fill(4)}"></i><i style="background:${fill(4, true)}"></i></span>`, 'Assessed | provisional (lighter)') +
    row(sw(FOG), 'Fog (not assessed)') +
    row(`<span class="sw line" style="background:${FRONT}"></span>`, 'Front line (held | contested)') +
    row(`<span class="sw split"><i style="background:${fill(2)}"></i><i style="background:${fill(4)}"></i><i style="background:${FOG}"></i></span>`, 'Zoomed out: each chapter held | contested | fog by burden') +
    row('<span class="sw line dashed"></span>', 'Edge of fog') +
    row('<span class="sw weights"><i></i><i></i><i></i></span>', 'Borders: chapter, territory, province');
}

/** The layout: precomputed at build time (layout.json), or computed here in dev or if it doesn't match. */
async function loadLayout(data: MapData, packed: Promise<PackedLayout | null>): Promise<Layout> {
  const p = await packed;
  if (p && p.provinceCount === data.meta.counts.provinces) return unpackLayout(p, data.root);
  await new Promise(requestAnimationFrame); // let the "laying out" message paint
  return layoutMap(data.root);
}

async function main() {
  const base = import.meta.env.BASE_URL;
  const packed: Promise<PackedLayout | null> = import.meta.env.PROD
    ? fetch(`${base}layout.json`).then(r => (r.ok ? r.json() : null)).catch(() => null)
    : Promise.resolve(null);
  const data: MapData = await (await fetch(`${base}map.json`)).json();

  const t0 = performance.now();
  const layout = await loadLayout(data, packed);
  const layoutMs = performance.now() - t0;
  const labels = buildLabels(layout, canvasMeasure());
  const labelsMs = performance.now() - t0 - layoutMs;

  // Zoomed out, each chapter shows as one held | contested | fog summary (ADR 0003's fallback); it fades
  // into the province detail as you zoom in.
  const scene = buildScene(layout, chapterSummaries(layout, data.root));
  const ctx = canvas.getContext('2d')!;
  const index = new ProvinceIndex(layout.provinces);
  const overlay = svg.append('g').attr('class', 'world');
  const hover = overlay.append('path').attr('class', 'hover');
  const selection = overlay.append('path').attr('class', 'selected');
  const labelLayer = svg.append('g').attr('class', 'labels');

  let transform: ZoomTransform = zoomIdentity;
  let pending = false;
  const fit = Math.min((innerWidth - 40) / WORLD.width, (innerHeight - 40) / WORLD.height);
  // Summary fully shown up to 1.5× the fitted zoom, gone by 3×.
  const summaryOpacity = (k: number) => Math.max(0, Math.min(1, (3 - k / fit) / 1.5));
  const draw = () => {
    pending = false;
    drawScene(ctx, scene, transform, summaryOpacity(transform.k));
    const w = innerWidth, h = innerHeight, k = transform.k;
    const onScreen = visibleLabels(labels, k).map(l => ({ l, p: transform.apply(l.at) }))
      .filter(({ p }) => p[0] > -200 && p[0] < w + 200 && p[1] > -100 && p[1] < h + 100);
    labelLayer.selectAll<SVGTextElement, { l: Label; p: [number, number] }>('text')
      .data(onScreen, d => d.l.region.node.uri ?? d.l.region.node.title)
      .join(enter => enter.append('text')
        .attr('class', d => `label ${d.l.level}`)
        .attr('font-size', d => d.l.fontSize)
        .each(function (d) {
          const t = select(this), n = d.l.lines.length;
          d.l.lines.forEach((line, i) => t.append('tspan').attr('x', 0).attr('dy', i === 0 ? `${-(n - 1) * 0.575}em` : '1.15em').text(line));
        }))
      .attr('transform', d => `translate(${d.p[0].toFixed(1)},${d.p[1].toFixed(1)})`);
  };
  const redraw = () => { if (!pending) { pending = true; requestAnimationFrame(draw); } };
  const resize = () => {
    canvas.width = Math.round(innerWidth * devicePixelRatio);
    canvas.height = Math.round(innerHeight * devicePixelRatio);
    redraw();
  };
  resize();
  addEventListener('resize', resize);

  const behaviour = zoom<SVGSVGElement, unknown>()
    .scaleExtent([fit * 0.7, fit * 120])
    .on('zoom', e => {
      transform = e.transform;
      overlay.attr('transform', transform.toString());
      redraw();
    });
  svg.call(behaviour).on('dblclick.zoom', null);
  svg.call(behaviour.transform, zoomIdentity
    .translate((innerWidth - WORLD.width * fit) / 2, (innerHeight - WORLD.height * fit) / 2).scale(fit));

  const provinceAt = (e: MouseEvent) => index.at(transform.invert(pointer(e, svg.node())));
  svg.on('click', e => { const r = provinceAt(e); if (r) show(r); });
  svg.on('mousemove', e => {
    if (e.buttons) return;
    const r = provinceAt(e);
    hover.attr('d', r ? closed(r.polygon) : null);
    svg.classed('over-province', !!r);
  });

  function show(region: Region) {
    selection.attr('d', closed(region.polygon));
    renderPanel(panel, region, data.meta, show);
  }

  const expected = data.meta.counts.provinces;
  const drawn = layout.provinces.length;
  const chapters = layout.territories.filter(t => t.depth === 0).length;
  status.innerHTML = `${drawn.toLocaleString('en')} provinces in ${chapters} chapters` +
    (drawn === expected ? '' : ` <b class="warn">(expected ${expected.toLocaleString('en')})</b>`) +
    ` · layout ${Math.round(layoutMs)} ms · labels ${Math.round(labelsMs)} ms` +
    (layout.fallbacks ? ` · ${layout.fallbacks} stripe fallbacks` : '');
  document.getElementById('citation')!.textContent = data.meta.icd11.citation;
  document.getElementById('gbd-citation')!.textContent =
    `Province sizes: ${data.meta.gbd.round} DALYs (${data.meta.gbd.estimateYear}). ${data.meta.gbd.citation}`;
  document.getElementById('crosswalk-note')!.textContent = data.meta.crosswalk;
  const ct = data.meta.clinicaltrials;
  if (ct) {
    document.getElementById('trials-citation')!.textContent =
      `Pipeline bars: ClinicalTrials.gov (data processed ${ct.dataTimestamp.slice(0, 10)}; running trials counted and phase-ranked by this project).`;
  }
  if (data.meta.chembl) {
    document.getElementById('chembl-citation')!.textContent =
      `Status cross-check: ${data.meta.chembl.release.replace('_', ' ')} (released ${data.meta.chembl.releaseDate}) approved-drug indications. ${data.meta.chembl.citation}`;
  }
  Object.assign(window, { diseaseMap: { layout, labels, layoutMs, labelsMs, expected } });
  console.info(`layout: ${drawn} provinces, ${layout.territories.length} territories, ${Math.round(layoutMs)} ms; labels ${Math.round(labelsMs)} ms`);
}

legend(document.getElementById('legend')!);
main().catch(err => { status.textContent = `Failed to load the map: ${err}`; throw err; });
