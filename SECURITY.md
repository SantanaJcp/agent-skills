# Security Policy

## Supported versions

There is no supported public release yet. After `v1.0.0`, security support covers the latest repository release and current stable Codex, Claude Code, and skills CLI versions documented for that release.

## Report privately

After publication, use GitHub private vulnerability reporting for malicious instructions, credential exposure, unsafe scripts, path traversal, dependency confusion, unexpected network behavior, or install/update integrity issues.

Do not open a public issue containing exploit details or sensitive data. Before the remote exists, contact the repository maintainer through a private channel rather than committing a report to the local tracker.

Include the affected skill or tooling surface, impact, reproduction steps, tested client versions, and any suggested mitigation. The maintainer will acknowledge the report, assess scope, and coordinate disclosure.

## Safety guarantees

Repository checks reject symlinks, high-confidence secret material, opaque executable formats, path escapes, runtime package imports, and external process execution from skill scripts. Network-capable Node modules generate a manual-review signal. These checks reduce risk but do not replace human review.

An actively unsafe stable skill may be removed immediately under the documented security exception rather than waiting through the normal deprecation window.
