#!/usr/bin/env python3
"""Write a git tree's exact contents into a new directory.

  export_tree.py <repo> <tree-sha> <dest>

Reads the objects directly (ls-tree, cat-file --batch), so nothing in the tree changes what is written:
no .gitattributes (export-ignore, export-subst, eol), no filter drivers, no hooks. Blobs are written with
their mode (644 or 755), symlinks as symlinks, and no path is ever opened through a symlink. A submodule
entry is refused: its contents are not in this repository. <dest> must not exist yet.
"""
import os
import subprocess
import sys

GIT = ["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null"]


def main() -> int:
    repo, tree, dest = sys.argv[1:4]
    os.mkdir(dest, 0o755)
    listing = subprocess.run(GIT + ["-C", repo, "ls-tree", "-r", "-z", "--full-tree", tree],
                             check=True, capture_output=True).stdout
    entries = []
    for record in listing.split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        mode, kind, sha = meta.split()
        if kind != b"blob":
            print(f"export_tree: refusing {kind.decode()} entry {path.decode(errors='replace')}", file=sys.stderr)
            return 1
        parts = path.split(b"/")
        if any(p in (b"", b".", b"..", b".git") for p in parts):
            print(f"export_tree: refusing path {path.decode(errors='replace')}", file=sys.stderr)
            return 1
        entries.append((mode, sha, path))
    batch = subprocess.Popen(GIT + ["-C", repo, "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    root = os.open(dest, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    for mode, sha, path in entries:
        batch.stdin.write(sha + b"\n")
        batch.stdin.flush()
        header = batch.stdout.readline().split()
        size = int(header[2])
        data = batch.stdout.read(size)
        batch.stdout.read(1)  # the newline after each object
        *dirs, name = path.split(b"/")
        parent = root
        for d in dirs:  # walk with dir fds: a symlink planted as a directory name is never followed
            try:
                os.mkdir(d, 0o755, dir_fd=parent)
            except FileExistsError:
                pass
            child = os.open(d, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            if parent != root:
                os.close(parent)
            parent = child
        if mode == b"120000":
            os.symlink(data, name, dir_fd=parent)
        else:
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o755 if mode == b"100755" else 0o644, dir_fd=parent)
            with os.fdopen(fd, "wb") as out:
                out.write(data)
        if parent != root:
            os.close(parent)
    batch.stdin.close()
    if batch.wait() != 0:
        print("export_tree: git cat-file failed", file=sys.stderr)
        return 1
    print(len(entries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
