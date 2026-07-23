/* draw-the-flow topology wiring: ephemeral path emphasis (view state only —
   deliberately NOT part of working state or any export) plus the verdict
   selection line. */
(function () {
  "use strict";
  if (!window.Acta2) return;

  var plot = document.querySelector(".dtf-plot");

  function setFocus(id) {
    if (plot) plot.setAttribute("data-focus", id);
    document.querySelectorAll("[data-flow-focus]").forEach(function (button) {
      button.setAttribute("aria-pressed", String(button.getAttribute("data-flow-focus") === id));
    });
    document.querySelectorAll("[data-path-card]").forEach(function (card) {
      card.setAttribute("data-emphasized", String(card.getAttribute("data-path-card") === id));
    });
  }

  document.addEventListener("click", function (event) {
    var button = event.target instanceof Element ? event.target.closest("button") : null;
    if (!button) return;
    if (button.hasAttribute("data-flow-focus")) {
      setFocus(button.getAttribute("data-flow-focus"));
    } else if (button.hasAttribute("data-acta2-reset")) {
      setFocus("all");
    }
  });

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
        line.textContent = "No verdict proposed yet.";
      }
    }
  });

  window.Acta2.refresh();
})();
