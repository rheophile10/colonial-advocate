import { defineConfig } from "vite";

// Built output goes to /docs at the repo root so GitHub Pages can
// serve it from `main` branch → /docs. Site URL:
// https://colonialadvocate.ca/ (custom apex domain) — hence base "/".
// `web/public/CNAME` is copied to docs/CNAME on every build so Pages
// keeps the custom-domain binding after each deploy.
//
// plastron and plastron-dom are imported directly from sibling
// repository paths (../../plastron). Vite resolves their TypeScript
// sources via the .js → .ts redirect in bundler mode.
export default defineConfig({
  base: "/",
  server: { port: 5173 },
  build: {
    outDir: "../docs",
    emptyOutDir: true,
    sourcemap: true,
    target: "es2022",
  },
});
