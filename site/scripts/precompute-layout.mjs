// Runs the map layout once at build time and writes public/layout.json next to map.json (src/precomputed.ts).
// Loads the TypeScript sources through Vite's SSR loader, so the browser and the build share one layout.
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';

const root = fileURLToPath(new URL('..', import.meta.url));
const server = await createServer({ root, appType: 'custom', logLevel: 'error', server: { middlewareMode: true, hmr: false } });
try {
  const { layoutMap } = await server.ssrLoadModule('/src/layout.ts');
  const { packLayout } = await server.ssrLoadModule('/src/precomputed.ts');
  const data = JSON.parse(readFileSync(`${root}public/map.json`, 'utf8'));
  const t0 = performance.now();
  const packed = packLayout(layoutMap(data.root), data.root);
  writeFileSync(`${root}public/layout.json`, JSON.stringify(packed));
  console.log(`layout.json: ${packed.provinceCount} provinces, ${packed.territories.length} territories, ` +
    `${packed.fallbacks} stripe fallbacks, ${Math.round(performance.now() - t0)} ms`);
} finally {
  await server.close();
}
