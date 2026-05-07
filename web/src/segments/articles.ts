import type { Fn, LambdaKey, Segment } from "../../../../plastron/plastron/src/types/index.js";
import { el, type VNode } from "../../../../plastron/segments/plastron-dom/src/index.js";

// ========================================================================
// articles segment
//
// One value cel (`articles`) holds the array of dehydrated article
// records. main.ts fetches /articles.json at startup and writes that
// array onto the cel via set("articles", ...). Updating the cel
// triggers a cascade through the render lambda.
//
// The render lambda lays out a two-column broadsheet:
//   - lead piece (first article) sits beside The Chase image
//   - remaining articles flow into a CSS-multicolumn block beneath
//
// Each article body is split on blank lines into paragraphs; the
// first paragraph of every piece gets a drop-cap class.
// ========================================================================

export interface Article {
  id: string;
  slug: string;
  headline: string;
  deck: string;
  body: string;
  dateline: string;
  source_topic?: string;
  byline?: string;
  published_at?: string;
  citations?: { url?: string; title?: string }[];
}

export interface SegmentBundle {
  segment: Segment;
  fns: Map<LambdaKey, Fn>;
}

const baseUrl = (): string => {
  // import.meta.env.BASE_URL is "/" on the apex domain; on the
  // github.io subpath (fallback) it's "/colonial-advocate/".
  return import.meta.env.BASE_URL || "/";
};

const paragraphs = (body: string): string[] =>
  body
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter((p) => p.length > 0);

const renderParagraph = (text: string, isFirst: boolean): VNode =>
  el("p", { class: isFirst ? "lede" : "" }, text);

const renderArticleBody = (body: string): VNode[] =>
  paragraphs(body).map((p, i) => renderParagraph(p, i === 0));

const renderArticle = (a: Article, opts: { lead?: boolean } = {}): VNode => {
  const headerChildren: VNode[] = [el("h2", { class: "headline" }, a.headline)];
  if (a.deck) headerChildren.push(el("p", { class: "deck" }, a.deck));

  const bodyChildren: VNode[] = [];
  if (a.dateline) bodyChildren.push(el("span", { class: "dateline" }, a.dateline + " "));
  bodyChildren.push(...renderArticleBody(a.body));

  return el(
    "article",
    { class: opts.lead ? "piece lead" : "piece", id: `a-${a.slug}` },
    ...headerChildren,
    el("div", { class: "body" }, ...bodyChildren),
    el(
      "p",
      { class: "byline" },
      el("span", null, "— "),
      el("strong", null, a.byline || "W. L. M."),
    ),
  );
};

const today = (): string => {
  const d = new Date();
  return d.toLocaleDateString("en-CA", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });
};

const masthead = (): VNode =>
  el(
    "header",
    { class: "masthead" },
    el(
      "p",
      { class: "vol" },
      el("span", null, "Vol. I  No. 1"),
      el("span", null, today()),
      el("span", null, "Price: One Penny"),
    ),
    el("h1", { class: "title" }, "The Colonial Advocate"),
    el(
      "p",
      { class: "motto" },
      "Pledged but to truth, to liberty, and law — no favour sways us, and no fear shall awe.",
    ),
  );

const colophon = (): VNode =>
  el(
    "footer",
    { class: "colophon" },
    el("p", null, "Toronto. Re-established by friends of the press."),
  );

const renderEmptyFront = (): VNode =>
  el(
    "section",
    { class: "front empty" },
    el(
      "figure",
      { class: "chase" },
      el("img", {
        src: `${baseUrl()}the-chase.png`,
        alt: "The Chase — a coach pursued by riders",
      }),
      el("figcaption", null, "The Chase."),
    ),
    el(
      "section",
      { class: "coming-soon" },
      el("h2", null, "The Press Is Warming."),
      el(
        "p",
        null,
        "No edition is yet set in type. The editor's ghost wanders " +
          "the wires for matter worthy of the press.",
      ),
    ),
  );

const renderFront = (articles: Article[]): VNode => {
  if (articles.length === 0) return renderEmptyFront();
  const [lead, ...rest] = articles;

  const blocks: VNode[] = [
    // Lead block: The Chase + lead piece, side by side
    el(
      "section",
      { class: "lead-block" },
      el(
        "figure",
        { class: "chase" },
        el("img", {
          src: `${baseUrl()}the-chase.png`,
          alt: "The Chase — a coach pursued by riders",
        }),
        el("figcaption", null, "The Chase."),
      ),
      renderArticle(lead, { lead: true }),
    ),
  ];
  if (rest.length > 0) {
    blocks.push(
      el(
        "section",
        { class: "columns" },
        ...rest.map((a) => renderArticle(a)),
      ),
    );
  }
  return el("div", { class: "front" }, ...blocks);
};

const renderHome: Fn = ({ articles }: { articles: Article[] }): VNode => {
  const safe = Array.isArray(articles) ? articles : [];
  return el(
    "div",
    { class: "advocate" },
    masthead(),
    renderFront(safe),
    colophon(),
  );
};

export const buildArticlesSegment = (): SegmentBundle => {
  const segment: Segment = {
    key: "articles",
    cels: [
      { key: "articles", v: [] as Article[], segment: "articles" },
      {
        key: "appTree",
        l: "articles:render",
        inputMap: { articles: "articles" },
        segment: "articles",
      },
    ],
  };
  const fns = new Map<LambdaKey, Fn>([["articles:render", renderHome]]);
  return { segment, fns };
};
