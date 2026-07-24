/* concept-lab topology wiring: on every render, recompute the backoff model
   from working state (backoffPlotSpec/deriveBackoff are in scope from the inlined export-core),
   redraw the SVG timeline, rewrite the consequence table, and update the
   parameter outputs and totals line. DOM only — createElementNS / createElement
   / textContent / setAttribute; no markup injection. The geometry and number
   formatting below mirror instruments/concept-lab/body.mjs exactly so the live
   render matches the static no-JS baseline. */
(function () {
  "use strict";
  if (!window.Acta2) return;

  var SVG_NS = "http://www.w3.org/2000/svg";

  function fmtParam(value, unit) {
    if (!unit) return String(value);
    if (unit === "×") return value + "×";
    return value + " " + unit;
  }
  function fmtMs(value) {
    return value + " ms";
  }
  function fmtRange(range) {
    return range[0] + "–" + range[1] + " ms";
  }
  function totalsText(totals) {
    return (
      "Worst-case total across " +
      totals.attempts +
      " attempts: " +
      totals.worstCaseTotalMs +
      " ms · expected ≈ " +
      totals.expectedTotalMs +
      " ms"
    );
  }

  function svgEl(name, attrs, textValue) {
    var node = document.createElementNS(SVG_NS, name);
    for (var key in attrs) {
      if (Object.prototype.hasOwnProperty.call(attrs, key)) {
        node.setAttribute(key, String(attrs[key]));
      }
    }
    if (textValue !== undefined) node.textContent = textValue;
    return node;
  }

  /* Maps the shared plot spec (export-core.backoffPlotSpec, inlined in this
     script) to SVG DOM nodes — the same mapping body.mjs performs with
     strings, so live geometry always equals the static baseline. */
  function drawPlot(plot, spec) {
    while (plot.firstChild) plot.removeChild(plot.firstChild);
    spec.items.forEach(function (it) {
      if (it.el === "axis-line" || it.el === "endmark") {
        plot.appendChild(svgEl("line", {
          x1: it.x1, y1: it.y1, x2: it.x2, y2: it.y2,
          stroke: "var(--acta-rule-strong)", "stroke-width": 1,
        }));
      } else if (it.el === "axis-tick") {
        plot.appendChild(svgEl("line", { x1: it.x, y1: it.y1, x2: it.x, y2: it.y2, stroke: "var(--acta-rule-strong)", "stroke-width": 1 }));
      } else if (it.el === "zero-label") {
        plot.appendChild(svgEl("text", { x: it.x, y: it.y, "font-size": 11, fill: "var(--acta-ink-muted)", "text-anchor": "middle" }, it.text));
      } else if (it.el === "caption") {
        plot.appendChild(svgEl("text", { x: it.x, y: it.y, "font-size": 11, fill: "var(--acta-ink-muted)", "text-anchor": "start" }, it.text));
      } else if (it.el === "band") {
        var bandAttrs = {
          x: it.x, y: it.y, width: it.width, height: it.height,
          fill: "var(--acta-action-tint)",
          stroke: it.capped ? "var(--acta-warning)" : "var(--acta-action)",
          "stroke-width": 1.5,
        };
        if (it.capped) bandAttrs["stroke-dasharray"] = "3 2";
        plot.appendChild(svgEl("rect", bandAttrs));
      } else if (it.el === "tick") {
        plot.appendChild(svgEl("line", { x1: it.x, y1: it.y1, x2: it.x, y2: it.y2, stroke: "var(--acta-ink)", "stroke-width": 1.5 }));
      } else if (it.el === "cap-label") {
        plot.appendChild(svgEl("text", { x: it.x, y: it.y, "font-size": 10, fill: "var(--acta-warning)", "text-anchor": "middle" }, it.text));
      } else if (it.el === "attempt-label") {
        plot.appendChild(svgEl("text", { x: it.x, y: it.y, "font-size": 11, "font-weight": 600, fill: "var(--acta-ink)", "text-anchor": "middle" }, it.text));
      } else if (it.el === "expected-mark") {
        plot.appendChild(svgEl("line", { x1: it.x, y1: it.y1, x2: it.x, y2: it.y2, stroke: "var(--acta-ink-muted)", "stroke-width": 1.5, "stroke-dasharray": "2 3" }, undefined));
      } else if (it.el === "expected-label") {
        plot.appendChild(svgEl("text", { x: it.x, y: it.y, "font-size": 11, fill: "var(--acta-ink-muted)", "text-anchor": "middle" }, it.text));
      } else if (it.el === "total-label") {
        plot.appendChild(svgEl("text", { x: it.x, y: it.y, "font-size": 12, "font-weight": 600, fill: "var(--acta-ink)", "text-anchor": "end" }, it.text));
      }
    });
  }

  function drawTable(tbody, backoff) {
    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
    backoff.rows.forEach(function (row) {
      var tr = document.createElement("tr");

      var tdAttempt = document.createElement("td");
      tdAttempt.className = "num";
      tdAttempt.textContent = String(row.attempt);
      tr.appendChild(tdAttempt);

      var tdDelay = document.createElement("td");
      tdDelay.className = "num";
      tdDelay.textContent = fmtMs(row.delayMs);
      if (row.cappedAtLimit) {
        var cap = document.createElement("span");
        cap.className = "clab-cap";
        cap.textContent = "capped";
        tdDelay.appendChild(cap);
      }
      tr.appendChild(tdDelay);

      var tdRange = document.createElement("td");
      tdRange.textContent = fmtRange(row.rangeMs);
      tr.appendChild(tdRange);

      var tdCum = document.createElement("td");
      tdCum.className = "num";
      tdCum.textContent = fmtMs(row.cumulativeWorstMs);
      tr.appendChild(tdCum);

      tbody.appendChild(tr);
    });
  }

  var plot = document.querySelector("[data-clab-plot]");
  var tbody = document.getElementById("clab-consequences");
  var totalsLine = document.querySelector("[data-bind='totals-line']");
  var unitById = {};
  window.Acta2.data.params.forEach(function (param) {
    unitById[param.id] = param.unit;
  });

  window.Acta2.onRender(function (data, working) {
    var spec = backoffPlotSpec(working.params, working.toggles);
    var backoff = spec.backoff;
    if (plot) drawPlot(plot, spec);
    if (tbody) drawTable(tbody, backoff);
    if (totalsLine) totalsLine.textContent = totalsText(backoff.totals);
    data.params.forEach(function (param) {
      var out = document.getElementById("clab-o-" + param.id);
      if (out) out.textContent = fmtParam(working.params[param.id], unitById[param.id]);
    });
  });

  window.Acta2.refresh();
})();
