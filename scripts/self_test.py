#!/usr/bin/env python3
"""Run the portable-state contract tests in an isolated temporary project."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(*args: str, expected: int = 0) -> str:
    result = subprocess.run([sys.executable, *args], text=True, capture_output=True)
    if result.returncode != expected:
        raise SystemExit(f"expected exit {expected}, got {result.returncode}:\n{result.stdout}\n{result.stderr}")
    return result.stdout

def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n")

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="wallfacer-reverse-self-test-") as tmp:
        project = Path(tmp) / "target"
        project.mkdir()
        run(str(ROOT / "scripts" / "init_project.py"), str(project))
        run(str(ROOT / "scripts" / "validate_state.py"), str(project))
        state = project / ".mianbizhe"
        contract = json.loads((state / "task-contract.json").read_text())
        if contract.get("execution_intensity") != "difficult":
            raise SystemExit("default execution intensity is not difficult")
        contract["execution_intensity"] = "challenge"
        write_json(state / "task-contract.json", contract)
        run(str(ROOT / "scripts" / "validate_state.py"), str(project))
        contract["execution_intensity"] = "hell"
        write_json(state / "task-contract.json", contract)
        run(str(ROOT / "scripts" / "validate_state.py"), str(project))
        contract["execution_intensity"] = "invalid"
        write_json(state / "task-contract.json", contract)
        invalid_mode = run(str(ROOT / "scripts" / "validate_state.py"), str(project), expected=1)
        if "execution_intensity" not in invalid_mode:
            raise SystemExit("invalid execution intensity was accepted")
        contract["execution_intensity"] = "difficult"
        contract["objective"] = "Classify a supplied package without a demo."
        write_json(state / "task-contract.json", contract)
        checkpoint = json.loads((state / "checkpoint.json").read_text())
        checkpoint["current_node"] = "route"
        write_json(state / "checkpoint.json", checkpoint)
        missing_route = run(str(ROOT / "scripts" / "validate_state.py"), str(project), expected=1)
        if "route-matrix.routes" not in missing_route:
            raise SystemExit("missing-route gate did not trigger")
        matrix = json.loads((state / "route-matrix.json").read_text())
        matrix["selected_route"] = "route-input-audit"
        matrix["routes"] = [{
            "id": "route-input-audit",
            "layer": "package",
            "hypothesis": "the target input can be identified without execution",
            "input_locator": ["declared target input"],
            "action": "hash and identify the file format",
            "expected_observation": "a recognized format or an explicit opaque boundary",
            "discriminates": ["recognized format", "opaque input"],
            "status": "selected",
            "next_route": "route-format-specific-parser"
        }]
        write_json(state / "route-matrix.json", matrix)
        run(str(ROOT / "scripts" / "validate_state.py"), str(project))
        binding = json.loads((state / "reference-binding.json").read_text())
        binding["reference_case"]["bundle_root"] = "/absolute/path"
        write_json(state / "reference-binding.json", binding)
        abs_path = run(str(ROOT / "scripts" / "validate_state.py"), str(project), expected=1)
        if "portable path" not in abs_path:
            raise SystemExit("absolute reference path was accepted")
    print("wallfacer-reverse self-test passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
