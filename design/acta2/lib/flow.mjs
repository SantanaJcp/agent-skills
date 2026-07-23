/* Shared node-and-edge diagram renderer for Acta v2 instruments and records.
 *
 * Scenario data authors a small grid graph (columns × rows); this module
 * turns it into a deterministic static SVG string. No runtime dependency —
 * Node-side only, like lib/highlight.mjs. Every label is escaped through the
 * caller-supplied esc().
 *
 * flow = {
 *   nodes: [{ id, label, sub?, col, row, tone? }],   tone: "dark"|"accent"|"danger"|"muted"
 *   edges: [{ from, to, label?, dashed?, tone? }],   tone: "accent"|"danger"
 *   caption?
 * }
 * Grid: col/row are 0-based. Layout constants keep 3–4 columns legible at
 * instrument width; the caller wraps the SVG in a .plotwrap for local scroll.
 */

const GRID = {
  colW: 252,
  rowH: 112,
  nodeW: 186,
  nodeH: 60,
  margin: 24,
};

function nodeCenter(node) {
  return {
    x: GRID.margin + node.col * GRID.colW + GRID.nodeW / 2,
    y: GRID.margin + node.row * GRID.rowH + GRID.nodeH / 2,
  };
}

function strokeFor(tone) {
  if (tone === "accent") return "var(--acta-action)";
  if (tone === "danger") return "var(--acta-danger)";
  return "var(--acta-rule-strong)";
}

/**
 * @param {any} flow @param {(value: unknown) => string} esc
 * @param {{ariaLabel?: string}} [options]
 * @returns {{ svg: string, viewW: number, viewH: number }}
 */
export function renderFlow(flow, esc, options = {}) {
  const nodes = flow.nodes ?? [];
  const edges = flow.edges ?? [];
  const byId = Object.create(null);
  let maxCol = 0;
  let maxRow = 0;
  for (const node of nodes) {
    byId[node.id] = node;
    if (node.col > maxCol) maxCol = node.col;
    if (node.row > maxRow) maxRow = node.row;
  }
  const viewW = GRID.margin * 2 + maxCol * GRID.colW + GRID.nodeW;
  const viewH = GRID.margin * 2 + maxRow * GRID.rowH + GRID.nodeH;

  const parts = [];
  /** @type {string[]} */
  const labelParts = [];

  for (const edge of edges) {
    const from = byId[edge.from];
    const to = byId[edge.to];
    if (!from || !to) continue;
    const a = nodeCenter(from);
    const b = nodeCenter(to);
    const stroke = strokeFor(edge.tone);
    const dash = edge.dashed ? ' stroke-dasharray="4 4"' : "";
    let points;
    let labelX;
    let labelY;
    let end; // arrow tip + direction
    if (from.row === to.row) {
      const direction = b.x > a.x ? 1 : -1;
      const x1 = a.x + (GRID.nodeW / 2) * direction;
      const x2 = b.x - (GRID.nodeW / 2 + 7) * direction;
      points = `${x1},${a.y} ${x2},${a.y}`;
      labelX = (x1 + x2) / 2;
      labelY = a.y - 9;
      end = { x: x2, y: a.y, dx: direction, dy: 0 };
    } else if (from.col === to.col) {
      const direction = b.y > a.y ? 1 : -1;
      const y1 = a.y + (GRID.nodeH / 2) * direction;
      const y2 = b.y - (GRID.nodeH / 2 + 7) * direction;
      points = `${a.x},${y1} ${a.x},${y2}`;
      labelX = a.x + 8;
      labelY = (y1 + y2) / 2;
      end = { x: a.x, y: y2, dx: 0, dy: direction };
    } else {
      /* L-shaped: leave from the bottom/top, turn, enter the side. */
      const vertical = b.y > a.y ? 1 : -1;
      const horizontal = b.x > a.x ? 1 : -1;
      const y1 = a.y + (GRID.nodeH / 2) * vertical;
      const x2 = b.x - (GRID.nodeW / 2 + 7) * horizontal;
      points = `${a.x},${y1} ${a.x},${b.y} ${x2},${b.y}`;
      labelX = a.x + 10 * horizontal;
      labelY = (y1 + b.y) / 2;
      end = { x: x2, y: b.y, dx: horizontal, dy: 0 };
    }
    const pathsAttr = edge.paths ? ` data-paths="${esc(edge.paths.join(" "))}"` : "";
    parts.push(
      `<polyline points="${points}" fill="none" stroke="${stroke}" stroke-width="1.5"${dash}${pathsAttr}></polyline>`,
    );
    const tip = `${end.x + end.dx * 7},${end.y + end.dy * 7}`;
    const wing1 = `${end.x - end.dy * 4},${end.y - end.dx * 4}`;
    const wing2 = `${end.x + end.dy * 4},${end.y + end.dx * 4}`;
    parts.push(`<polygon points="${tip} ${wing1} ${wing2}" fill="${stroke}"${pathsAttr}></polygon>`);
    if (edge.label) {
      const anchor = from.col === to.col || (from.col !== to.col && from.row !== to.row) ? "start" : "middle";
      labelParts.push(
        `<text x="${labelX}" y="${labelY}" font-size="11" fill="${
          edge.tone ? strokeFor(edge.tone) : "var(--acta-ink-muted)"
        }" text-anchor="${anchor}" paint-order="stroke" stroke="#FFFFFF" stroke-width="5" stroke-linejoin="round"${pathsAttr}>${esc(edge.label)}</text>`,
      );
    }
  }

  for (const node of nodes) {
    const x = GRID.margin + node.col * GRID.colW;
    const y = GRID.margin + node.row * GRID.rowH;
    const dark = node.tone === "dark";
    const fill = dark ? "var(--acta-code-bg)" : "var(--acta-paper)";
    const stroke =
      node.tone === "accent"
        ? "var(--acta-action)"
        : node.tone === "danger"
          ? "var(--acta-danger)"
          : dark
            ? "var(--acta-code-bg)"
            : "var(--acta-rule-strong)";
    const labelFill = dark ? "var(--acta-code-ink)" : "var(--acta-ink)";
    const subFill = dark ? "var(--acta-code-muted)" : "var(--acta-ink-muted)";
    const nodePaths = node.paths ? ` data-paths="${esc(node.paths.join(" "))}"` : "";
    parts.push(
      `<rect x="${x}" y="${y}" width="${GRID.nodeW}" height="${GRID.nodeH}" rx="10" fill="${fill}" stroke="${stroke}" stroke-width="1.5"${nodePaths}></rect>`,
    );
    const centerX = x + GRID.nodeW / 2;
    if (node.sub) {
      parts.push(
        `<text x="${centerX}" y="${y + 26}" font-size="12.5" font-weight="600" fill="${labelFill}" text-anchor="middle">${esc(node.label)}</text>`,
      );
      parts.push(
        `<text x="${centerX}" y="${y + 43}" font-size="11" fill="${subFill}" text-anchor="middle">${esc(node.sub)}</text>`,
      );
    } else {
      parts.push(
        `<text x="${centerX}" y="${y + GRID.nodeH / 2 + 4.5}" font-size="12.5" font-weight="600" fill="${labelFill}" text-anchor="middle">${esc(node.label)}</text>`,
      );
    }
  }

  const aria = options.ariaLabel ? ` role="img" aria-label="${esc(options.ariaLabel)}"` : ' aria-hidden="true"';
  const svg = `<svg viewBox="0 0 ${viewW} ${viewH}" class="flowd"${aria} style="min-width:${Math.min(viewW, 640)}px;max-width:${viewW}px">
${parts.join("\n")}
${labelParts.join("\n")}
</svg>`;
  return { svg, viewW, viewH };
}
