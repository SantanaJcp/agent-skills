/* feel-the-flow topology wiring: a real debounced filter over the playground
   list, driven by the working parameters. Typed text is ephemeral view state
   — never exported. setTimeout carries the configured delay so the lag is
   genuinely felt, not described. */
(function () {
  "use strict";
  if (!window.Acta2) return;

  var input = document.querySelector("[data-ftf-input]");
  var pending = document.querySelector("[data-ftf-pending]");
  var empty = document.querySelector("[data-ftf-empty]");
  var rows = Array.prototype.slice.call(document.querySelectorAll("[data-row-name]"));
  var timer = null;
  var firstKeystroke = true;

  function applyFilter(query) {
    var visible = 0;
    rows.forEach(function (row) {
      var match = query === "" || row.getAttribute("data-row-name").indexOf(query) !== -1;
      row.hidden = !match;
      if (match) visible += 1;
    });
    if (empty) empty.hidden = visible !== 0;
    if (pending) pending.textContent = "";
  }

  function scheduleFilter() {
    if (!input) return;
    var working = window.Acta2.getWorking();
    var query = input.value.trim().toLowerCase();
    if (timer) clearTimeout(timer);
    var delay = Number(working.params.debounce) || 0;
    if (firstKeystroke && working.toggles.instantFirst) {
      firstKeystroke = false;
      applyFilter(query);
      return;
    }
    if (query.length < Number(working.params.minChars || 0)) {
      applyFilter("");
      return;
    }
    if (pending && delay > 0) pending.textContent = "…" + delay + " ms";
    timer = setTimeout(function () {
      applyFilter(query);
    }, delay);
  }

  if (input) {
    input.addEventListener("input", scheduleFilter);
  }

  window.Acta2.onRender(function (data, working) {
    data.params.forEach(function (param) {
      var out = document.getElementById("ftf-o-" + param.id);
      if (out) out.textContent = working.params[param.id] + param.unit;
    });
    if (input && input.value !== "") scheduleFilter();
  });

  document.addEventListener("click", function (event) {
    var button = event.target instanceof Element ? event.target.closest("button") : null;
    if (button && button.hasAttribute("data-acta2-reset")) {
      if (input) input.value = "";
      firstKeystroke = true;
      applyFilter("");
    }
  });

  window.Acta2.refresh();
})();
