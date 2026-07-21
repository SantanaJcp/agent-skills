# Releasing

## Version policy

The collection has one semantic version; skills do not have independent release streams.

- **Patch** — backward-compatible corrections.
- **Minor** — new compatible skills, compatible improvements, and deprecations.
- **Major** — repository-contract breaks and stable-skill removals.

The first public release is `v1.0.0` when the maintainer judges content and governance mature. No `v0.x` release is published.

## Deprecation

Deprecate a stable skill for at least one minor release and document its replacement or migration path before removal in a major release. An actively unsafe skill may be removed immediately with a security advisory and changelog explanation.

## Prepare

1. Confirm every stable skill passed current Codex and Claude smoke trials.
2. Record concrete tested client and skills CLI versions.
3. Set the private package metadata version to the release version.
4. Move the changelog entries from Unreleased into a dated release section.
5. Regenerate catalogs and run `npm run check`.
6. Run `npm run release:check -- <version>` from a clean default branch.

## Publish

Dispatch the release workflow with the version. It reruns acceptance and release checks, creates an annotated `v<version>` tag, and publishes matching GitHub Release notes. It never publishes the authoring package to npm.

After release, verify installation from the public GitHub source and verify the skills.sh owner/repository page. Directory visibility has no guaranteed indexing deadline.
