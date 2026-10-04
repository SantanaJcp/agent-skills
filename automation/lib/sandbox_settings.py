#!/usr/bin/env python3
"""Claude Code settings that put an OS boundary around the gardener's tools.

  sandbox_settings.py <work-dir> <writable-paths-separated-by-newlines> <domains...> -- <unix-sockets...>

Bash runs in Claude Code's sandbox (Seatbelt on macOS): no reads of credential locations, writes only to
the working directory, the run's work dir and the configured paths, network only to the configured
domains, and no way out (failIfUnavailable, allowUnsandboxedCommands false). The same credential paths are
denied to Read, Edit, Grep and Glob through permission rules. The claude process itself stays outside the
sandbox, so its own login (macOS keychain) and the model API keep working.
"""
import json
import sys

CREDENTIAL_DIRS = ["~/.ssh", "~/Library/Keychains", "~/.config/gh", "~/.aws", "~/.config/gcloud", "~/.azure",
                   "~/.kube", "~/.docker", "~/.gnupg"]
CREDENTIAL_FILES = ["~/.git-credentials", "~/.netrc", "~/.npmrc", "~/.pypirc"]


def main() -> int:
    work_dir, writable, *rest = sys.argv[1:]
    split = rest.index("--") if "--" in rest else len(rest)
    domains, sockets = rest[:split], rest[split + 1:]
    deny_rules = []
    for path in CREDENTIAL_DIRS:
        deny_rules += [f"Read({path}/**)", f"Edit({path}/**)"]
    for path in CREDENTIAL_FILES:
        deny_rules += [f"Read({path})", f"Edit({path})"]
    settings = {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "filesystem": {
                "denyRead": CREDENTIAL_DIRS + CREDENTIAL_FILES,
                "allowWrite": [work_dir] + [line for line in writable.splitlines() if line],
            },
            "network": {"allowedDomains": domains, "allowUnixSockets": sockets},
        },
        "permissions": {"deny": deny_rules},
    }
    print(json.dumps(settings, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
