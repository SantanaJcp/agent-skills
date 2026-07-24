# Releasing

## Version policy

The collection has one semantic version; skills do not have independent release streams.

- **Patch** — backward-compatible corrections.
- **Minor** — compatible skills/improvements and deprecations.
- **Major** — repository-contract breaks and stable-skill removals.

Acta has an internal authoring version embedded in materialized files. Changing the Acta contract does not replace the collection version; its consumer impact determines the collection release level.

## First release

The first public release is `v1.0.0`. The initial fifteen skills moved from incubator to stable together after the client and end-to-end rows passed. ADR 0005 records the owner's explicit one-time deferral of the browser and accessibility rows; the suite report labels them deferred rather than passed.

Implementation may prepare compatibility records, changelog, and release checks, but tag creation and workflow dispatch remain separate human actions.

## Deprecation

Deprecate a stable skill for at least one minor release with migration guidance before removal in a major release. An actively unsafe skill may be removed immediately with a security advisory.

## Prepare

1. Confirm every stable skill passed current Codex and Claude trials.
2. For the initial cohort, confirm the complete suite QA verdict is passing.
3. Record concrete client, browser, Acta, and skills CLI versions.
4. Set the private package metadata version to the release version.
5. Move changelog entries into a dated release section.
6. Regenerate Acta and catalogs; run `npm run check`.
7. Run `npm run release:check -- <version>` from a clean default branch.

## Publish

A human dispatches the release workflow. It reruns acceptance and release checks, creates the tag, and publishes matching GitHub Release notes. It never publishes the authoring package to npm.

After release, verify complete-bundle and isolated-skill installation from the public source and verify skills.sh visibility without promising an indexing deadline.
