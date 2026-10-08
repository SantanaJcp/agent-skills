#!/usr/bin/env python3
"""Runs one automation job with the project lock held, in its own process group.

  supervise.py <lock-file> <wait-seconds> <poll-seconds> [--watch DIR]... [--record FILE --run-id ID] -- <command...>

The project is free only when nobody holds the flock, the process group of the previous job is gone,
AND no process of that job has its working directory or an open file inside a --watch directory (the
clone, the gardener's work dirs). A process group cannot contain a descendant that calls setsid(), so the
property that matters, nothing of the job still touching the clone, is checked directly with lsof.
A process that already ran when the job started is not the job's: no descendant can be older than the
job. Just before starting it, the supervisor lists the processes that exist (<lock-file>.before) and
leaves them alone; Docker Desktop's VM keeps the clone's bind-mounted files open after its containers
are gone, and killing it broke Docker until someone reset it by hand (issue #61).
Busy past the wait: runs the command with KITCHEN_LOCK_STATE=busy, so the job records the skip itself.
Acquired: runs it with KITCHEN_LOCK_STATE=held in a new session. When its main process exits, or the
supervisor is told to stop (the signal is forwarded to the group first), the group is terminated, then
every process of the job still holding files in the watched dirs gets TERM, then KILL. Any that survive keep the
project busy; the run's record (--record/--run-id) is marked incomplete with their pids.
"""
import fcntl
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

GRACE = float(os.environ.get("KITCHEN_STOP_GRACE_SECONDS", "10"))
DRAIN = 2.0  # lets the job's log tee flush after its main process exits


def group_alive(pgid: int) -> bool:
    if pgid <= 1:
        return False
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:  # the number now belongs to someone else's processes, not to our job
        return False


def processes() -> frozenset[str]:
    """The running processes as "pid start" lines: with its start time, a pid names one process even once reused."""
    listing = subprocess.run(["ps", "-A", "-o", "pid=,lstart="], capture_output=True, text=True, check=False,
                             env={**os.environ, "LC_ALL": "C"})
    if listing.returncode != 0 or not listing.stdout:
        raise RuntimeError(f"ps failed ({listing.returncode}): {listing.stderr.strip()[:200]}")
    return frozenset(" ".join(line.split()) for line in listing.stdout.splitlines() if line.strip())


def save_before(path: str, before: frozenset[str]) -> None:
    Path(path + ".tmp").write_text("".join(f"{line}\n" for line in sorted(before)))
    os.replace(path + ".tmp", path)


def load_before(path: str) -> frozenset[str]:
    """What the last job's supervisor listed before starting it; empty when no job has run yet."""
    try:
        return frozenset(Path(path).read_text().splitlines())
    except FileNotFoundError:
        return frozenset()


def holders(dirs: list[str], before: frozenset[str] = frozenset()) -> dict[int, str]:
    """pid -> one path it holds (cwd or open file) inside the watched dirs; this supervisor and the processes
    in `before` (they predate the job) excluded."""
    if not dirs:
        return {}
    roots = [os.path.realpath(d) for d in dirs if os.path.exists(d)]
    listing = subprocess.run(["lsof", "-w", "-n", "-P", "-u", str(os.getuid()), "-F", "pn"],
                             capture_output=True, text=True, check=False)
    if listing.returncode not in (0, 1) or not listing.stdout:
        raise RuntimeError(f"lsof failed ({listing.returncode}): {listing.stderr.strip()[:200]}")
    found, pid = {}, 0
    for line in listing.stdout.splitlines():
        if line.startswith("p"):
            pid = int(line[1:])
        elif line.startswith("n") and pid != os.getpid():
            name = line[1:]
            if any(name == root or name.startswith(root + "/") for root in roots):
                found.setdefault(pid, name)
    if found and before:
        running = {int(line.split(" ", 1)[0]): line for line in processes()}
        found = {pid: name for pid, name in found.items() if running.get(pid) not in before}
    return found


def sweep(dirs: list[str], grace: float, before: frozenset[str]) -> dict[int, str]:
    """TERM, then KILL, every process of the job still holding files in the watched dirs; returns the survivors."""
    for sig, wait in ((signal.SIGTERM, grace), (signal.SIGKILL, 3.0)):
        found = holders(dirs, before)
        if not found:
            return {}
        for pid in found:
            try:
                os.kill(pid, sig)
            except (ProcessLookupError, PermissionError):
                pass
        end = time.monotonic() + wait
        while holders(dirs, before) and time.monotonic() < end:
            time.sleep(0.1)
    return holders(dirs, before)


def recorded_group(fd: int) -> int:
    os.lseek(fd, 0, os.SEEK_SET)
    text = os.read(fd, 64).decode(errors="replace").strip()
    return int(text) if text.isdigit() else 0


def record_group(fd: int, pgid: int | None) -> None:
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    if pgid:
        os.write(fd, f"{pgid}\n".encode())


def acquire(fd: int, wait: float, poll: float, dirs: list[str], before_file: str) -> bool:
    deadline = time.monotonic() + wait
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if not group_alive(recorded_group(fd)) and not holders(dirs, load_before(before_file)):
                return True
            fcntl.flock(fd, fcntl.LOCK_UN)
        except BlockingIOError:
            pass
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(poll, remaining))


def stop_group(pgid: int, grace: float) -> None:
    end = time.monotonic() + DRAIN
    while group_alive(pgid) and time.monotonic() < end:
        time.sleep(0.05)
    for sig, wait in ((signal.SIGTERM, grace), (signal.SIGKILL, 5.0)):
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            return
        except PermissionError:
            # killpg fails with EPERM when some member of the group may not be signalled by us; the others may
            # still have received it (seen 2026-10-05: a session ended during the nightly's docker tests and the
            # supervisor crashed here, leaving its run "running"). Keep waiting and escalating: whatever is still
            # running afterwards is found by the sweep and recorded as survivors.
            pass
        end = time.monotonic() + wait
        while group_alive(pgid) and time.monotonic() < end:
            time.sleep(0.05)
        if not group_alive(pgid):
            return


def parse(argv: list[str]):
    lock_file, wait, poll, *rest = argv
    dirs, record, run_id = [], None, None
    while rest and rest[0] != "--":
        option, value, *rest = rest
        if option == "--watch":
            dirs.append(value)
        elif option == "--record":
            record = value
        elif option == "--run-id":
            run_id = value
        else:
            raise SystemExit(f"supervise.py: unknown option {option}")
    if not rest or rest[0] != "--" or len(rest) < 2:
        raise SystemExit("usage: supervise.py <lock-file> <wait> <poll> [--watch DIR]... -- <command...>")
    return lock_file, float(wait), float(poll), dirs, record, run_id, rest[1:]


def mark_survivors(record: str | None, run_id: str | None, survivors: dict[int, str]) -> None:
    pids = " ".join(str(pid) for pid in sorted(survivors))
    print(f"kitchen automation: survivors {pids} still hold files in the clone after TERM and KILL; "
          "the project stays busy until they exit", file=sys.stderr)
    if record and run_id:
        script = Path(__file__).with_name("record.py")
        subprocess.run([sys.executable, str(script), record, "mark-survivors", run_id, pids], check=False)


def main() -> int:
    lock_file, wait, poll, dirs, record, run_id, command = parse(sys.argv[1:])
    fd = os.open(lock_file, os.O_RDWR | os.O_CREAT, 0o644)  # not inherited by the job
    before_file = lock_file + ".before"
    if not acquire(fd, wait, poll, dirs, before_file):
        os.close(fd)
        os.execvpe(command[0], command, {**os.environ, "KITCHEN_LOCK_STATE": "busy"})
    before = processes()  # listed while the job does not exist yet: none of these can be its descendant
    save_before(before_file, before)  # the next acquire tells this job's leftovers from older processes with it
    job = subprocess.Popen(command, env={**os.environ, "KITCHEN_LOCK_STATE": "held"}, start_new_session=True)
    record_group(fd, job.pid)

    def forward(sig, _frame):
        try:
            os.killpg(job.pid, sig)
        except ProcessLookupError:
            pass

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, forward)
    code = job.wait()
    stop_group(job.pid, GRACE)
    survivors = sweep(dirs, GRACE, before)
    if survivors:
        mark_survivors(record, run_id, survivors)
        code = code if code > 0 else 1
    record_group(fd, None)
    os.close(fd)  # releases the flock; survivors still holding files keep the project busy
    return code if code >= 0 else 128 - code


if __name__ == "__main__":
    sys.exit(main())
