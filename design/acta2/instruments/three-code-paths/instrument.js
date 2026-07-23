/* three-code-paths topology wiring: reflect the working selection into the
   comparison columns and the decision panel. */
(function () {
  "use strict";
  if (!window.Acta2) return;
  window.Acta2.onRender(function (data, working) {
    document.querySelectorAll("[data-option]").forEach(function (card) {
      card.setAttribute(
        "data-selected",
        String(card.getAttribute("data-option") === working.selected),
      );
    });
    var line = document.querySelector("[data-bind='selection-line']");
    if (line) {
      if (working.selected) {
        var selected = null;
        data.options.forEach(function (option) {
          if (option.id === working.selected) selected = option;
        });
        line.textContent =
          "Working selection: " +
          (selected ? selected.label : working.selected) +
          " — candidate only, not yet accepted.";
      } else {
        line.textContent = "No path selected yet.";
      }
    }
  });
  window.Acta2.refresh();
})();
