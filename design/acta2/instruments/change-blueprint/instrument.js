/* change-blueprint topology wiring: reflect the proposed gate resolution
   into the selection line. */
(function () {
  "use strict";
  if (!window.Acta2) return;
  window.Acta2.onRender(function (data, working) {
    var line = document.querySelector("[data-bind='selection-line']");
    if (line) {
      if (working.selected) {
        var selected = null;
        data.options.forEach(function (option) {
          if (option.id === working.selected) selected = option;
        });
        line.textContent =
          "Proposed: " +
          (selected ? selected.label : working.selected) +
          " — candidate only, not yet accepted.";
      } else {
        line.textContent = "No resolution proposed yet.";
      }
    }
  });
  window.Acta2.refresh();
})();
