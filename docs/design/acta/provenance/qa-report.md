# QA report — Acta component sheet & direction comparator

Date: 2026-07-21 · Tooling: Chrome headless (`--headless=new`) on macOS, Python (stdlib) checks, synthetic-event behavior harness. Files under `/private/tmp/claude-501/-Users-santana-Development-agent-skills/d0672212-37c9-40d1-9a64-f5af76c2f977/scratchpad/`.

## component-sheet.html (Acta v0.1.0)

| Gate | Method | Result |
|---|---|---|
| Offline / file:// | Opened via `file://` in headless Chrome; no external URLs exist in source (grep: no `http` in `src/href` except upstream attribution text) | PASS |
| Tag balance | Python HTMLParser stack check | PASS — no orphans/mismatches |
| Responsive 320 | Iframe harness measuring `scrollWidth` at 320px | PASS — 318 ≤ 320 |
| Responsive 1280 | Same at 1280px | PASS — 1265 ≤ 1280 |
| Contrast AA | Computed WCAG ratios for all 20 token pairs (Python) | PASS — min text pair 5.47:1 (code-dim on inverse); structural rule 3.36:1 (UI, ≥3:1); annotations in sheet corrected to measured values |
| Print | `--print-to-pdf`, pages inspected visually | PASS — provenance/front matter prints, controls hidden, details expanded via beforeprint, inverse blocks flip light, monochrome meaning intact |
| Reduced motion | Global `prefers-reduced-motion` kill-switch; only color/border transitions exist (90ms) | PASS by construction (media query present; no animations) |
| No-JS | All content static in DOM; quiz answer keys inside `<noscript><details>`; NoScriptFallback specimen documents the contract | PASS — reading unaffected without JS |
| Keyboard | Native controls only (details/summary, radio, range, buttons, links); `:focus-visible` outline defined; no drag interactions | PASS by construction (manual tab-through not performed in headless — flagged for a human pass) |
| Safe DOM | JS audited: `textContent`/`createElement` only; no `innerHTML`, no inline handlers; delegated listeners | PASS |
| Clipboard | Behavior harness: copy → headless has no clipboard → fallback ran → StatusRegion announced “Copy failed — select the text manually.” | PASS — honest degradation verified |
| Quiz behavior | Harness: correct answer → good feedback + score “1/2 · 1 answered”; wrong answer on Q2 → bad feedback + “2 answered” | PASS |
| EditorControl | Harness: range → 3 → value text “3 attempts”, derived cells update (“4s ± jitter”, then “—”) | PASS |
| Segmented control | Harness: click toggles `aria-pressed` false/true | PASS |
| Provenance & labels | Sheet opens with full ProvenanceHeader; Fact/Inference/Simplification used in evidence and family proofs; colophon defines them | PASS |
| Exports | Markdown + JSON hidden payloads present; both derive from the same declared state; StatusRegion announces | PASS |

## direcciones-comparador.html

- Tag balance: PASS (after removing one stray `</div>` introduced by table-wrapping automation — caught and fixed).
- Overflow: initially FAIL at 320 (A: unwrapped matrix table; B: `width="700"` SVG forcing grid min-content; C: `pre` inside `.specimen` grid). Fixed via `.tablewrap`, `min-width:0` on grid items, `minmax(0,1fr)` tracks. Re-measured: A 307, B 305, C 305 — all PASS at 320 and 1280.
- Print: 20-page PDF inspected; details auto-expand; buttons hidden (added `@media print` rules); break-inside avoidance on cards/gates/callouts.
- Behavior: shared copy/quiz script identical in pattern to the sheet’s (verified on the sheet).

## Known limitations / flagged for human verification

1. **Real-device keyboard & screen-reader pass** (VoiceOver/NVDA) not performed — headless cannot do it. Structure is native-controls-only, but a human AT pass is required before calling gate 3/4 fully done.
2. **Zoom 400%** was validated indirectly (320px reflow ≈ 1280@400%); a manual browser zoom check is recommended.
3. **Windows font rendering** (Charter absent → Palatino/Georgia fallback) unverified on a real Windows box.
4. Comparator’s B-direction `.dB .rail` sticky behavior at exactly 860–960px widths was not exhaustively swept; the chosen system (Acta) does not use that rail, so this is moot for the final system.
