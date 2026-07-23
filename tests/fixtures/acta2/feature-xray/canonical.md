---
acta_protocol: "0.2"
artifact_kind: "feature-explanation"
producer_skill: "feature-xray"
initiative: "tag-filter"
status: "approved"
phase: "accepted"
language: "en"
source_revision: "a8b083705553550eda289ddf9cf1d028df907682"
inputs:
  - "src/catalog.mjs — filterByTag, visibleSkills"
  - "src/url-tag.mjs — parseTagFromSearch"
  - "src/app.mjs — browser glue"
  - "index.html — static catalog markup"
  - "test/catalog.test.mjs — behavior assertions"
decisions:
  - id: "publish-xray"
    selection: "publish-record"
    rationale: "Walked each claim against the code; the map and steps match what actually landed."
    accepted_via: "chat 2026-07-23 — explicit confirmation"
supersedes: null
---

# Feature X-ray — tag filtering

Every render derives from the URL: parseTagFromSearch → filterByTag →
replaceChildren. The no-JS catalog is the baseline the script enhances.
Unknown tags render the accepted empty state; back/forward replay the same
single render path. Claims verified file-by-file at a8b0837.
