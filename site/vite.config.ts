import { defineConfig } from 'vite';

// GitHub Pages serves the project site at https://qa1roo.github.io/disease-front/, so production builds need that
// base path; `npm run dev` keeps serving from /.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/disease-front/' : '/',
}));
