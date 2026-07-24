/* build-with-notes topology wiring: reflect the proposed resolution into the
   gate panel and apply the timeline filter. No markup sinks: textContent /
   hidden / setAttribute only. filterEntries is in scope from the inlined core. */
(function () {
  "use strict";
  if (!window.Acta2) return;

  window.Acta2.onRender(function (data, working) {
    var line = document.querySelector("[data-bind='resolution-line']");
    if (line) {
      if (working.resolution) {
        var label = working.resolution;
        (data.gate.options || []).forEach(function (option) {
          if (option.id === working.resolution) label = option.label;
        });
        line.textContent = "Proposed: " + label + " — candidate only, not yet accepted.";
      } else {
        line.textContent = "No resolution proposed yet.";
      }
    }

    var entries = data.entries || [];
    var kept = filterEntries(entries, working.filter);
    var keptIds = {};
    kept.forEach(function (entry) {
      keptIds[entry.id] = true;
    });
    document.querySelectorAll("[data-entry]").forEach(function (node) {
      node.hidden = !keptIds[node.getAttribute("data-entry")];
    });

    var showing = document.querySelector("[data-bind='showing-line']");
    if (showing) {
      showing.textContent =
        working.filter === "all"
          ? "Showing all " + entries.length + " entries."
          : "Showing " + kept.length + " of " + entries.length + " entries.";
    }
  });

  window.Acta2.refresh();
})();
