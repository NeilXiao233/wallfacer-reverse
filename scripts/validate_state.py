#!/usr/bin/env python3
"""Validate a v2 minimal Wallfacer state index without treating it as evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

STATE_VERSION = 2
SKILL_VERSION = "2.0.0"
CHECKPOINT_STATUSES = {"active", "blocked", "complete"}
REFERENCE_STATUSES = {"unbound", "provisional", "confirmed"}
V1_FILES = {
    "task-contract.json", "reference-binding.json", "checkpoint.json", "route-matrix.json",
    "evidence-ledger.json", "attempt-ledger.json", "artifact-manifest.json",
}


def is_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    args = parser.parse_args()
    root = Path(args.project_root).expanduser().resolve()
    state_dir = root / ".wallfacer"
    state_file = state_dir / "state.json"
    errors: list[str] = []
    if not state_file.exists():
        legacy = sorted(path.name for path in state_dir.glob("*.json") if path.name in V1_FILES) if state_dir.exists() else []
        if legacy:
            errors.append("v1 state detected; preserve it and create a v2 index only after moving useful facts into project authority")
        else:
            errors.append("missing .wallfacer/state.json")
        print(json.dumps({"valid": False, "errors": errors}, indent=2, ensure_ascii=True))
        return 1
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"valid": False, "errors": [f"invalid state.json: {exc}"]}, indent=2, ensure_ascii=True))
        return 1

    if state.get("schema_version") != STATE_VERSION:
        errors.append(f"schema_version must be {STATE_VERSION}")
    if state.get("skill_version") != SKILL_VERSION:
        errors.append(f"skill_version must be {SKILL_VERSION}")
    project = state.get("project", {})
    if project.get("root") != ".":
        errors.append("project.root must be '.'")
    if not isinstance(project.get("objective"), str) or not project["objective"].strip():
        errors.append("project.objective is unresolved")
    authority = project.get("authority")
    if not isinstance(authority, list) or not authority:
        errors.append("project.authority must contain at least one project-relative path")
    else:
        for item in authority:
            if not is_relative_path(item):
                errors.append(f"invalid authority path: {item}")
                continue
            resolved = (root / item).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(f"authority escapes project root: {item}")
                continue
            if not resolved.exists():
                errors.append(f"authority does not exist: {item}")

    ownership = state.get("ownership", {})
    if not isinstance(ownership.get("writer"), str) or not ownership["writer"].strip():
        errors.append("ownership.writer is unresolved")
    if not isinstance(ownership.get("revision"), int) or ownership["revision"] < 1:
        errors.append("ownership.revision must be a positive integer")

    reference = state.get("reference", {})
    status = reference.get("status")
    if status not in REFERENCE_STATUSES:
        errors.append("reference.status must be unbound, provisional, or confirmed")
    locator = reference.get("locator")
    basis = reference.get("selection_basis")
    if status == "unbound":
        if locator is not None or basis not in ([], None):
            errors.append("unbound reference must not carry a locator or selection basis")
    else:
        if not isinstance(locator, dict) or not locator.get("id") or not is_relative_path(locator.get("path")):
            errors.append("bound reference needs an id and a skill-root-relative path")
        if not isinstance(basis, list) or not basis or not all(isinstance(item, str) and item.strip() for item in basis):
            errors.append("bound reference needs a nonempty selection_basis")

    checkpoint = state.get("checkpoint", {})
    if checkpoint.get("status") not in CHECKPOINT_STATUSES:
        errors.append("checkpoint.status must be active, blocked, or complete")
    if not isinstance(checkpoint.get("node"), str) or not checkpoint["node"].strip():
        errors.append("checkpoint.node is required")
    if not isinstance(checkpoint.get("next_action"), str) or not checkpoint["next_action"].strip():
        errors.append("checkpoint.next_action is required")
    if not isinstance(checkpoint.get("updated_at"), str) or not checkpoint["updated_at"].strip():
        errors.append("checkpoint.updated_at is required")

    output = {
        "valid": not errors,
        "state": str(state_file),
        "revision": ownership.get("revision"),
        "authority_count": len(authority) if isinstance(authority, list) else 0,
        "errors": errors,
    }
    print(json.dumps(output, indent=2, ensure_ascii=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
