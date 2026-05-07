import { defineConfig } from "vite";

// plastron and plastron-dom are imported directly from sibling
// repository paths (../../plastron). Vite resolves their TypeScript
// sources via the .js → .ts redirect in bundler mode.
export default defineConfig({
  server: { port: 5173 },
  build: {
    sourcemap: true,
    target: "es2022",
  },
});
