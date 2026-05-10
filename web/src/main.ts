import { createInitialState } from "../../../plastron/plastron/src/index.js";
import { installDom } from "../../../plastron/segments/plastron-dom/src/index.js";
import type { Fn } from "../../../plastron/plastron/src/types/index.js";
import { buildArticlesSegment, type Article } from "./segments/articles.js";

// ========================================================================
// The Colonial Advocate — entry.
//
// Hydrates the articles segment with an empty list, mounts the DOM,
// then fetches /articles.json and writes the result onto the
// `articles` cel. The render lambda re-runs on the cycle and the
// painter applies the diff. If the fetch fails we leave the empty
// state visible (renders the "press is warming" placeholder).
// ========================================================================

const state = createInitialState();
const hydrate = state.fns.get("hydrate") as Fn;
const runCycle = state.fns.get("runCycle") as Fn;
const setFn = state.fns.get("set") as Fn;

const articlesBundle = buildArticlesSegment();
hydrate(state, [articlesBundle.segment], [articlesBundle.fns]);

await runCycle(state);

const handle = installDom(state, {
  roots: { app: { selector: "#root", cel: "appTree" } },
});

await runCycle(state);
handle.channel.drain();

// Fetch articles.json off the critical path. If the file is missing
// or malformed, the empty state stays up.
try {
  const url = `${import.meta.env.BASE_URL}articles.json`;
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`articles.json: ${res.status}`);
  const articles = (await res.json()) as Article[];
  if (!Array.isArray(articles)) throw new Error("articles.json is not an array");
  await setFn(state, "articles", articles);
  await runCycle(state);
  handle.channel.drain();
  console.log(`[colonial-advocate] loaded ${articles.length} article(s)`);
} catch (err) {
  console.error("[colonial-advocate] failed to load articles", err);
}

(globalThis as { __plastronState?: unknown }).__plastronState = state;
