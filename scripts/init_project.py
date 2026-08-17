#!/usr/bin/env python3
"""Create a v2 Wallfacer state index only for a confirmed project."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "project-template" / ".wallfacer" / "state.json"
V1_FILES = {
    "task-contract.json", "reference-binding.json", "checkpoint.json", "route-matrix.json",
    "evidence-ledger.json", "attempt-ledger.json", "artifact-manifest.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def project_relative_path(root: Path, value: str) -> str:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"authority must be a project-relative path: {value}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"authority escapes the project root: {value}") from exc
    if not resolved.exists():
        raise ValueError(f"authority does not exist: {value}")
    return candidate.as_posix()


def archive_relative_path(root: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or candidate == Path("."):
        raise ValueError(f"archive target must be a new project-relative path: {value}")
    destination = root / candidate
    if destination.exists():
        raise ValueError(f"archive target already exists: {value}")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--authority", action="append", required=True)
    parser.add_argument("--reference-id")
    parser.add_argument("--reference-path")
    parser.add_argument("--reference-basis", action="append")
    parser.add_argument("--archive-v1-to")
    args = parser.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    objective = args.objective.strip()
    owner = args.owner.strip()
    if not root.is_dir():
        parser.error(f"project root is not a directory: {root}")
    if not objective:
        parser.error("--objective must not be empty")
    if not owner:
        parser.error("--owner must not be empty")
    try:
        authority = [project_relative_path(root, item) for item in args.authority]
    except ValueError as exc:
        parser.error(str(exc))

    supplied_reference = [args.reference_id, args.reference_path, args.reference_basis]
    if any(supplied_reference) and not all(supplied_reference):
        parser.error("reference id, path, and at least one basis must be supplied together")
    if args.reference_path:
        reference_path = Path(args.reference_path)
        if reference_path.is_absolute() or ".." in reference_path.parts:
            parser.error("--reference-path must be relative to the skill root")

    state_dir = root / ".wallfacer"
    if state_dir.exists():
        legacy_files = {path.name for path in state_dir.glob("*.json")}
        if legacy_files & V1_FILES:
            if not args.archive_v1_to:
                parser.error(
                    "v1 state exists; move target facts into project authority, then pass "
                    "--archive-v1-to <new-project-relative-directory> to preserve it"
                )
            try:
                archive_dir = archive_relative_path(root, args.archive_v1_to)
            except ValueError as exc:
                parser.error(str(exc))
            os.replace(state_dir, archive_dir)
        else:
            parser.error(f"refusing to initialize an existing state directory: {state_dir}")
    try:
        state_dir.mkdir()
    except FileExistsError:
        parser.error(f"refusing to initialize an existing state directory: {state_dir}")
    state = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    state["project"] = {"root": ".", "objective": objective, "authority": authority}
    state["ownership"] = {"writer": owner, "revision": 1}
    state["checkpoint"]["updated_at"] = utc_now()
    if args.reference_id:
        state["reference"] = {
            "status": "confirmed",
            "locator": {"id": args.reference_id, "path": Path(args.reference_path).as_posix()},
            "selection_basis": args.reference_basis,
        }
    write_json_atomic(state_dir / "state.json", state)
    print(state_dir / "state.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
