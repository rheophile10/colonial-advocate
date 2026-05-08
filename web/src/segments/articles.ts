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
  /** Small-caps red kicker above the headline (optional). */
  kicker?: string;
  headline: string;
  deck: string;
  /** Body markup, paragraphs separated by blank lines. Recognised
   *  per-block prefixes:
   *    "## …"  → boxed red small-caps sub-section header
   *    "> …"   → pull-quote (italic, centered, with rules)
   *    "---"   → "— ✦ —" section break
   */
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

type Block =
  | { kind: "p"; text: string }
  | { kind: "subhead"; text: string }
  | { kind: "pullquote"; text: string }
  | { kind: "break" };

const parseBody = (body: string): Block[] =>
  body
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter((p) => p.length > 0)
    .map<Block>((p) => {
      if (p === "---" || p === "— ✦ —") return { kind: "break" };
      if (p.startsWith("## ")) return { kind: "subhead", text: p.slice(3).trim() };
      if (p.startsWith("> ")) {
        // Allow multi-line pull quotes: every line begins with "> "
        const text = p
          .split("\n")
          .map((l) => l.replace(/^>\s?/, ""))
          .join(" ")
          .trim();
        return { kind: "pullquote", text };
      }
      return { kind: "p", text: p };
    });

const renderBlock = (b: Block, isFirstParagraph: boolean): VNode => {
  switch (b.kind) {
    case "subhead":
      return el(
        "div",
        { class: "subhead" },
        el("h3", null, b.text),
      );
    case "pullquote":
      return el(
        "blockquote",
        { class: "pullquote" },
        el("p", null, b.text),
      );
    case "break":
      return el(
        "div",
        { class: "section-break" },
        el("span", null, "— ✦ —"),
      );
    case "p":
      return el("p", { class: isFirstParagraph ? "lede" : "" }, b.text);
  }
};

const renderArticleBody = (body: string): VNode[] => {
  const blocks = parseBody(body);
  let firstParaSeen = false;
  return blocks.map((b) => {
    const isLede = b.kind === "p" && !firstParaSeen;
    if (b.kind === "p") firstParaSeen = true;
    return renderBlock(b, isLede);
  });
};

const chaseFigure = (): VNode =>
  el(
    "figure",
    { class: "chase" },
    el("img", {
      src: `${baseUrl()}the-chase.png`,
      alt: "The Chase — a coach pursued by riders",
    }),
    el("figcaption", null, "The Chase."),
  );

const renderArticleHeader = (a: Article): VNode => {
  const children: VNode[] = [];
  if (a.kicker) children.push(el("p", { class: "kicker" }, a.kicker));
  children.push(el("h2", { class: "headline" }, a.headline));
  if (a.deck) children.push(el("p", { class: "deck" }, a.deck));
  children.push(
    el(
      "p",
      { class: "byline byline-top" },
      el("span", null, "By "),
      el("strong", null, a.byline || "William Lyon Mackenzie"),
      el("span", null, " — Printer & Publisher"),
    ),
  );
  return el("header", { class: "piece-head" }, ...children);
};

const renderArticle = (a: Article, opts: { lead?: boolean } = {}): VNode => {
  const bodyChildren: VNode[] = [];
  // The Chase floats inside the lead piece so prose wraps it.
  if (opts.lead) bodyChildren.push(chaseFigure());
  if (a.dateline) bodyChildren.push(el("span", { class: "dateline" }, a.dateline + " "));
  bodyChildren.push(...renderArticleBody(a.body));

  return el(
    "article",
    { class: opts.lead ? "piece lead" : "piece", id: `a-${a.slug}` },
    renderArticleHeader(a),
    el("div", { class: "body" }, ...bodyChildren),
    el("div", { class: "section-break end" }, el("span", null, "— ❧ —")),
  );
};

// Convert e.g. "2026-05-08" → "The Eighth of May, in the Year 2026"
const ORDINALS = [
  "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth",
  "Ninth", "Tenth", "Eleventh", "Twelfth", "Thirteenth", "Fourteenth",
  "Fifteenth", "Sixteenth", "Seventeenth", "Eighteenth", "Nineteenth",
  "Twentieth", "Twenty-First", "Twenty-Second", "Twenty-Third",
  "Twenty-Fourth", "Twenty-Fifth", "Twenty-Sixth", "Twenty-Seventh",
  "Twenty-Eighth", "Twenty-Ninth", "Thirtieth", "Thirty-First",
] as const;

const todayFormal = (): string => {
  const d = new Date();
  const day = ORDINALS[d.getDate() - 1] ?? String(d.getDate());
  const month = d.toLocaleString("en-CA", { month: "long" });
  return `The ${day} of ${month}, in the Year ${d.getFullYear()}`;
};

const masthead = (): VNode =>
  el(
    "header",
    { class: "masthead" },
    el("h1", { class: "title" }, "The Colonial Advocate"),
    el(
      "p",
      { class: "motto" },
      "Truth — Industry — Patriotism — Reform",
    ),
    el(
      "p",
      { class: "vol" },
      el("span", null, "Vol. II — No. 21"),
      el("span", null, `York, Upper Canada — ${todayFormal()}`),
      el("span", null, "Price: Four Pence"),
    ),
  );

const colophon = (): VNode =>
  el(
    "footer",
    { class: "colophon" },
    el("div", { class: "section-break end" }, el("span", null, "— ❧ —")),
    el(
      "p",
      null,
      "The Colonial Advocate is printed and published in the spirit of " +
        "William Lyon Mackenzie (1795–1861), who established the original " +
        "Colonial Advocate in 1824 at Queenston, Upper Canada, and thereafter " +
        "at York, where he campaigned against the oligarchy of the Family " +
        "Compact and in defence of the rights and liberties of the common " +
        "people of this Province. The opinions herein are those of a free " +
        "press, beholden to no ministry, no bank, and no power save the " +
        "conscience of its readers.",
    ),
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
    renderArticle(lead, { lead: true }),
    ...rest.map((a) => renderArticle(a)),
  ];
  return el("div", { class: "front" }, ...blocks);
};

const renderHome: Fn = ({ articles }: { articles: Article[] }): VNode => {
  const safe = Array.isArray(articles) ? articles : [];
  return el(
    "div",
    { class: "sheet" },
    el(
      "div",
      { class: "advocate" },
      masthead(),
      renderFront(safe),
      colophon(),
    ),
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
