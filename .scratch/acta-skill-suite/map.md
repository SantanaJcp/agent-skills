# Acta development suite implementation map

Type: feature-map
Status: blocked

| Issue | Work | Status | Blocked by |
| --- | --- | --- | --- |
| 01 | Artifact protocol and design provenance | resolved | — |
| 02 | Acta source and materialization | resolved | 01 |
| 03 | Six core skills | resolved | 02 |
| 04 | Nine autonomous tools | resolved | 02 |
| 05 | Publisher validation and documentation | resolved | 01–04 |
| 06 | Manual suite evaluation | pending | 05 |
| 07 | Joint stable promotion | blocked | 06 |
| 08 | v1.0.0 release preparation | blocked | 07 |

## Current blocker

Deterministic implementation is green (`npm run check`: 38 tests). Issue 06 requires human evidence from current Codex, Claude Code, Chrome, Safari, Firefox, VoiceOver, and NVDA before any suite member can move to stable.
