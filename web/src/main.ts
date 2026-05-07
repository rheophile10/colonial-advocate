import { createInitialState } from "../../../plastron/plastron/src/index.js";
import { installDom, el, type VNode } from "../../../plastron/segments/plastron-dom/src/index.js";
import type { Fn, LambdaKey, Segment } from "../../../plastron/plastron/src/types/index.js";

// ========================================================================
// The Colonial Advocate — coming-soon shell.
//
// One segment, one tree cel. The render lambda paints The Chase and a
// "coming soon" banner. As we grow this into a real paper we'll add
// segments per section (editorial, news, the family-compact watch),
// each lazy-loaded the way plastron-spa-demo does it.
// ========================================================================

const renderHome: Fn = (): VNode =>
  el("div", { class: "advocate" },
    el("header", { class: "masthead" },
      el("p", { class: "vol" }, "Vol. I — No. 1"),
      el("h1", { class: "title" }, "The Colonial Advocate"),
      el("p", { class: "motto" },
        "Pledged but to truth, to liberty, and law — no favour sways us, and no fear shall awe."),
    ),
    el("main", { class: "front" },
      el("figure", { class: "chase" },
        el("img", {
          src: `${import.meta.env.BASE_URL}the-chase.png`,
          alt: "The Chase — a coach pursued by riders",
        }),
        el("figcaption", null, "The Chase."),
      ),
      el("section", { class: "coming-soon" },
        el("h2", null, "Coming Soon."),
        el("p", null,
          "A new edition of Mackenzie's old paper, dressed for the present hour — soon to publish."),
      ),
    ),
    el("footer", { class: "colophon" },
      el("p", null, "Toronto. Re-established by friends of the press."),
    ),
  );

const home: Segment = {
  key: "home",
  cels: [
    {
      key: "appTree",
      l: "home:render",
      inputMap: {},
      segment: "home",
    },
  ],
};
const homeFns = new Map<LambdaKey, Fn>([["home:render", renderHome]]);

const state = createInitialState();
const hydrate = state.fns.get("hydrate") as Fn;
const runCycle = state.fns.get("runCycle") as Fn;

hydrate(state, [home], [homeFns]);
await runCycle(state);

const handle = installDom(state, {
  roots: { app: { selector: "#root", cel: "appTree" } },
});

await runCycle(state);
handle.painter.flushNow();

console.log("[colonial-advocate] mounted");
