#!/usr/bin/env python3
"""Transfer v2 state ownership with the same revision guard as checkpoint updates."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


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
    parser.add_argument("--new-owner", required=True)
    args = parser.parse_args()
    new_owner = args.new_owner.strip()
    if not new_owner:
        parser.error("--new-owner must not be empty")
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
        ownership["writer"] = new_owner
        ownership["revision"] += 1
        state["ownership"] = ownership
        write_json_atomic(state_file, state)
        print(json.dumps({"transferred": True, "owner": new_owner, "revision": ownership["revision"]}, ensure_ascii=True))
        return 0
    finally:
        lock_file.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
