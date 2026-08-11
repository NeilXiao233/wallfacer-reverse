#!/usr/bin/env python3
"""Initialize a portable .mianbizhe state package without overwriting user state."""
from __future__ import annotations
import argparse, json, shutil
from datetime import datetime, timezone
from pathlib import Path

FILES = ("task-contract.json", "reference-binding.json", "checkpoint.json", "route-matrix.json", "evidence-ledger.json", "attempt-ledger.json", "artifact-manifest.json")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_root")
    ap.add_argument("--force", action="store_true")
    ns = ap.parse_args()
    root = Path(ns.project_root).expanduser().resolve()
    state = root / ".mianbizhe"
    template = Path(__file__).resolve().parents[1] / "assets" / "project-template" / ".mianbizhe"
    state.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        dest = state / name
        if dest.exists() and not ns.force:
            continue
        shutil.copyfile(template / name, dest)
    contract = json.loads((state / "task-contract.json").read_text())
    contract.setdefault("execution_intensity", "difficult")
    contract["project_root"] = "."
    contract["project_id"] = root.name
    contract["project_name"] = root.name
    contract["created_at"] = datetime.now(timezone.utc).isoformat()
    (state / "task-contract.json").write_text(json.dumps(contract, indent=2, ensure_ascii=True) + "\n")
    route_matrix = json.loads((state / "route-matrix.json").read_text())
    route_matrix["project_id"] = root.name
    (state / "route-matrix.json").write_text(json.dumps(route_matrix, indent=2, ensure_ascii=True) + "\n")
    binding = json.loads((state / "reference-binding.json").read_text())
    binding["target_project_id"] = root.name
    binding["reference_case"]["locator_base"] = "skill_root"
    binding["reference_case"]["bundle_root"] = "references/reference-case"
    binding["reference_case"]["trace_index"] = "references/reference-case/trace-index.json"
    binding["reference_case"]["execution_graph"] = "references/reference-case/execution-graph.json"
    binding["binding_reason"] = "Initialized from the bundled Griddle method corpus; target facts remain unset."
    (state / "reference-binding.json").write_text(json.dumps(binding, indent=2, ensure_ascii=True) + "\n")
    checkpoint = json.loads((state / "checkpoint.json").read_text())
    checkpoint["updated_at"] = datetime.now(timezone.utc).isoformat()
    (state / "checkpoint.json").write_text(json.dumps(checkpoint, indent=2, ensure_ascii=True) + "\n")
    print(f"initialized {state}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
