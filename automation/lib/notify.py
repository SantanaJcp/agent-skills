#!/usr/bin/env python3
"""notify.py <title> <message>: the kitchen's local notification (lib/kitchen/notify.py) for the automation jobs.
Exits 0 when shown, 1 when the notifier failed, 2 when there is none; says why on stderr."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from kitchen.notify import SHOWN, notify  # noqa: E402

code, text = notify(sys.argv[1], sys.argv[2])
if code != SHOWN:
    print(f"kitchen notify: {text}", file=sys.stderr)
sys.exit(code)
