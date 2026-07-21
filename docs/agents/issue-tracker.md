# Issue tracker: Local Markdown

Issues and specs for this repository live as Markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec is `.scratch/<feature-slug>/spec.md`
- Implementation issues are stored individually at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`
- Triage state is recorded as a `Status:` line near the top
- Comments append under a `## Comments` heading

## Publishing

When a skill says “publish to the issue tracker,” create the appropriate file under `.scratch/<feature-slug>/`.

## Fetching

Read the referenced local file directly. Users will normally provide its path or issue number.

## Wayfinding

- Map: `.scratch/<effort>/map.md`
- Child ticket: `.scratch/<effort>/issues/<NN>-<slug>.md`
- Record `Type:` and `Status:` near the top
- Record dependencies as `Blocked by: NN, NN`
- Claim work by changing its status to `claimed`
- Resolve work by adding an `## Answer`, changing its status to `resolved`, and updating the map
