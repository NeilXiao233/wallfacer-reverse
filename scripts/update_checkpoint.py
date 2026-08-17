#!/usr/bin/env python3
"""Safely update the sole checkpoint in a v2 Wallfacer state index."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

CHECKPOINT_STATUSES = ("active", "blocked", "complete")


def write_json_atomic(path: Path, value: object) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--revision", type=int, required=True)
    parser.add_argument("--status", choices=CHECKPOINT_STATUSES, default="active")
    parser.add_argument("--node", required=True)
    parser.add_argument("--next-action", required=True)
    args = parser.parse_args()
    state_dir = Path(args.project_root).expanduser().resolve() / ".wallfacer"
    state_file = state_dir / "state.json"
    lock_file = state_dir / ".state.lock"
    try:
        fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        parser.error(f"state is locked: {lock_file}; do not bypass another writer")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as lock:
            lock.write(f"owner={args.owner}\nrevision={args.revision}\n")
        state = json.loads(state_file.read_text(encoding="utf-8"))
        ownership = state.get("ownership", {})
        if ownership.get("writer") != args.owner:
            parser.error("owner does not match the state writer")
        if ownership.get("revision") != args.revision:
            parser.error(f"stale revision: current state is {ownership.get('revision')}")
        if not args.node.strip() or not args.next_action.strip():
            parser.error("--node and --next-action must not be empty")
        state["checkpoint"] = {
            "status": args.status,
            "node": args.node.strip(),
            "next_action": args.next_action.strip(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        ownership["revision"] += 1
        state["ownership"] = ownership
        write_json_atomic(state_file, state)
        print(json.dumps({"updated": True, "revision": ownership["revision"]}, ensure_ascii=True))
        return 0
    finally:
        lock_file.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
