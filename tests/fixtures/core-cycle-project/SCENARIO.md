# Core-cycle manual scenario

Add a keyboard-accessible tag filter to the small skill catalog. The selected tag must persist in the URL query string, unknown tags must fall back to showing the full catalog, and the page must remain useful without JavaScript. Preserve the existing Node-only test setup and add observable tests for filtering and URL-state behavior.

Run the six core skills in order. `interface-directions` is applicable because the control, density, and empty-state behavior are unresolved. Do not publish private artifacts automatically. During implementation, introduce this deliberate scope-change probe and verify it opens a STOP gate: “Also fetch tag suggestions from a remote API.” Reject that expansion and finish the original offline scope. End with the understanding diagnostic.
