/* Constrained vector-figure renderer for Acta v2 (draw-it-in-svg).
 *
 * Figures are AUTHORED as structured vector primitives in scenario JSON —
 * real path data, real composition — but only a whitelisted element/attribute
 * vocabulary ever reaches the SVG string, and every value is escaped. This
 * keeps authored quality without opening a markup sink: scenario data can
 * draw anything, and can execute nothing.
 *
 * figure = {
 *   id, title, desc, viewW, viewH, caption?,
 *   elements: [{ el: "path"|"circle"|"ellipse"|"rect"|"line"|"polyline"|
 *                "polygon"|"text", ...geometry, ...style, text? }]
 * }
 */

const GEOMETRY = {
  path: ["d"],
  circle: ["cx", "cy", "r"],
  ellipse: ["cx", "cy", "rx", "ry"],
  rect: ["x", "y", "width", "height", "rx"],
  line: ["x1", "y1", "x2", "y2"],
  polyline: ["points"],
  polygon: ["points"],
  text: ["x", "y", "font-size", "font-weight", "font-style", "text-anchor", "letter-spacing"],
};

const STYLE = [
  "fill",
  "stroke",
  "stroke-width",
  "stroke-dasharray",
  "stroke-linecap",
  "stroke-linejoin",
  "opacity",
  "fill-opacity",
];

/* Style values may reference Acta tokens or plain colors — never urls or
   expressions. */
const SAFE_STYLE_VALUE = /^(?:var\(--acta-[a-z-]+\)|#[0-9a-fA-F]{3,8}|[a-zA-Z]+|[0-9. ,%-]+)$/;

/**
 * @param {any} figure @param {(value: unknown) => string} esc
 * @returns {{ svg: string, source: string }} svg = renderable markup;
 * source = the same markup for display/copy (caller escapes it).
 */
export function renderFigure(figure, esc) {
  const parts = [];
  for (const element of figure.elements ?? []) {
    const tag = element.el;
    const geometry = GEOMETRY[tag];
    if (!geometry) continue;
    const attrs = [];
    for (const name of geometry) {
      if (element[name] !== undefined) attrs.push(`${name}="${esc(element[name])}"`);
    }
    for (const name of STYLE) {
      const value = element[name];
      if (value === undefined) continue;
      if (!SAFE_STYLE_VALUE.test(String(value))) continue;
      attrs.push(`${name}="${esc(value)}"`);
    }
    if (tag === "text") {
      parts.push(`<text ${attrs.join(" ")}>${esc(element.text ?? "")}</text>`);
    } else {
      parts.push(`<${tag} ${attrs.join(" ")}></${tag}>`);
    }
  }
  const titleId = `fig-t-${figure.id}`;
  const descId = `fig-d-${figure.id}`;
  const svg = `<svg viewBox="0 0 ${Number(figure.viewW) || 640} ${Number(figure.viewH) || 360}" role="img" aria-labelledby="${esc(titleId)} ${esc(descId)}" class="a2-figure">
<title id="${esc(titleId)}">${esc(figure.title)}</title>
<desc id="${esc(descId)}">${esc(figure.desc)}</desc>
${parts.join("\n")}
</svg>`;
  return { svg, source: svg };
}
