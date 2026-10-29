import { select, zoom, zoomIdentity, type ZoomTransform } from 'd3';
import './style.css';
import { buildLabels, visibleLabels, type Label, type Measure } from './labels';
import { chapterSummaries, layoutMap, WORLD, type Region } from './layout';
import { renderPanel } from './panel';
import { fill, FOG, FRONT, STATUS_NAME } from './status';
import type { MapData } from './types';

const svg = select<SVGSVGElement, unknown>('#map');
const status = document.getElementById('status')!;
const panel = document.getElementById('panel')!;

const closed = (p: [number, number][]) => `M${p.map(q => `${q[0].toFixed(2)},${q[1].toFixed(2)}`).join('L')}Z`;
const segment = (s: [number, number][]) => `M${s[0][0]},${s[0][1]}L${s[1][0]},${s[1][1]}`;

/** Text widths from the real font, so "fits inside its region" holds on screen. */
function canvasMeasure(): Measure {
  const ctx = document.createElement('canvas').getContext('2d')!;
  const family = getComputedStyle(document.body).fontFamily;
  return (text, size, bold) => {
    ctx.font = `${bold ? 600 : 400} ${size}px ${family}`;
    return ctx.measureText(text).width;
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

async function main() {
  const data: MapData = await (await fetch(`${import.meta.env.BASE_URL}map.json`)).json();
  await new Promise(requestAnimationFrame); // let the "laying out" message paint

  const t0 = performance.now();
  const layout = layoutMap(data.root);
  const layoutMs = performance.now() - t0;
  const labels = buildLabels(layout, canvasMeasure());
  const labelsMs = performance.now() - t0 - layoutMs;

  const world = svg.append('g').attr('class', 'world');
  world.append('g').attr('class', 'provinces').selectAll('path').data(layout.provinces).join('path')
    .attr('d', d => closed(d.polygon)).attr('fill', d => fill(d.node.status, d.node.provisional))
    .on('click', (_, d) => show(d));
  // Zoomed out, each chapter shows as one held | contested | fog summary (ADR 0003's fallback); it fades
  // into the province detail as you zoom in.
  const summaryColor = { held: fill(2), contested: fill(4), fog: FOG };
  const summaries = chapterSummaries(layout, data.root);
  const summary = world.append('g').attr('class', 'summary');
  summary.append('g').selectAll('path').data(summaries.flatMap(s => s.pieces)).join('path')
    .attr('d', d => closed(d.polygon)).attr('fill', d => summaryColor[d.key]);
  summary.append('g').attr('class', 'bands').selectAll('path').data(summaries.flatMap(s => s.borders)).join('path')
    .attr('class', d => `${d.kind} summary-line`).attr('d', d => segment(d.segment));
  const territoryBorders = world.append('g').attr('class', 'border-territory');
  territoryBorders.selectAll('path')
    .data(layout.territories.filter(t => t.depth > 0)).join('path').attr('d', d => closed(d.polygon));
  world.append('g').attr('class', 'border-chapter').selectAll('path')
    .data(layout.territories.filter(t => t.depth === 0)).join('path').attr('d', d => closed(d.polygon));
  const detailBands = world.append('g').attr('class', 'bands');
  detailBands.selectAll('path').data(layout.borders).join('path')
    .attr('class', d => d.kind).attr('d', d => segment(d.segment));
  const selection = world.append('path').attr('class', 'selected');
  const labelLayer = svg.append('g').attr('class', 'labels');

  let transform: ZoomTransform = zoomIdentity;
  let pending = false;
  const drawLabels = () => {
    pending = false;
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

  const fit = Math.min((innerWidth - 40) / WORLD.width, (innerHeight - 40) / WORLD.height);
  // Summary fully shown up to 1.5× the fitted zoom, gone by 3×.
  const summaryOpacity = (k: number) => Math.max(0, Math.min(1, (3 - k / fit) / 1.5));
  const behaviour = zoom<SVGSVGElement, unknown>()
    .scaleExtent([fit * 0.7, fit * 120])
    .on('zoom', e => {
      transform = e.transform;
      world.attr('transform', transform.toString());
      const o = summaryOpacity(transform.k);
      summary.attr('opacity', o).attr('display', o > 0 ? null : 'none');
      detailBands.attr('opacity', 1 - o);
      territoryBorders.attr('opacity', 1 - o);
      if (!pending) { pending = true; requestAnimationFrame(drawLabels); }
    });
  svg.call(behaviour).on('dblclick.zoom', null);
  svg.call(behaviour.transform, zoomIdentity
    .translate((innerWidth - WORLD.width * fit) / 2, (innerHeight - WORLD.height * fit) / 2).scale(fit));
  addEventListener('resize', () => requestAnimationFrame(drawLabels));

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
      `Pipeline bars: ClinicalTrials.gov (data processed ${ct.dataTimestamp.slice(0, 10)}; counted and phase-ranked by this project) ` +
      `and ${ct.chembl.replace('_', ' ')} (Mendez D et al., Nucleic Acids Res. 2019, doi:10.1093/nar/gky1075; CC BY-SA 3.0).`;
  }
  Object.assign(window, { diseaseMap: { layout, labels, layoutMs, labelsMs, expected } });
  console.info(`layout: ${drawn} provinces, ${layout.territories.length} territories, ${Math.round(layoutMs)} ms; labels ${Math.round(labelsMs)} ms`);
}

legend(document.getElementById('legend')!);
main().catch(err => { status.textContent = `Failed to load the map: ${err}`; throw err; });
