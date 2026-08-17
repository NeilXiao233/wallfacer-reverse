#!/usr/bin/env python3
"""Run v2 state-index tests in an isolated temporary project."""
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
    return result.stdout + result.stderr


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="wallfacer-reverse-self-test-") as temp_dir:
        project = Path(temp_dir) / "target"
        project.mkdir()
        (project / "README.md").write_text("# Target\n", encoding="utf-8")
        init = ROOT / "scripts" / "init_project.py"
        validate = ROOT / "scripts" / "validate_state.py"
        update = ROOT / "scripts" / "update_checkpoint.py"
        transfer = ROOT / "scripts" / "transfer_owner.py"
        handoff = ROOT / "scripts" / "build_handoff.py"

        missing_gate = run(str(init), str(project), expected=2)
        if "--objective" not in missing_gate:
            raise SystemExit("init accepted a missing confirmation gate")
        run(
            str(init), str(project), "--objective", "Classify the supplied target.",
            "--owner", "coordinator-a", "--authority", "README.md",
        )
        run(str(validate), str(project))
        state_path = project / ".wallfacer" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state["reference"]["status"] != "unbound":
            raise SystemExit("init bound a reference without an explicit selection")
        wrong_owner = run(
            str(update), str(project), "--owner", "observer-b", "--revision", "1",
            "--node", "execute", "--next-action", "run the format probe", expected=2,
        )
        if "owner does not match" not in wrong_owner:
            raise SystemExit("non-owner checkpoint update was accepted")
        run(
            str(update), str(project), "--owner", "coordinator-a", "--revision", "1",
            "--node", "execute", "--next-action", "run the format probe",
        )
        stale_revision = run(
            str(update), str(project), "--owner", "coordinator-a", "--revision", "1",
            "--node", "verify", "--next-action", "inspect the output", expected=2,
        )
        if "stale revision" not in stale_revision:
            raise SystemExit("stale checkpoint update was accepted")
        run(
            str(transfer), str(project), "--owner", "coordinator-a", "--revision", "2",
            "--new-owner", "coordinator-b",
        )
        run(
            str(update), str(project), "--owner", "coordinator-b", "--revision", "3",
            "--node", "verify", "--next-action", "inspect the output",
        )
        run(str(validate), str(project))
        run(str(handoff), str(project))
        rendered = (project / ".wallfacer" / "HANDOFF.md").read_text(encoding="utf-8")
        if "README.md" not in rendered or "Revision: `4`" not in rendered:
            raise SystemExit("handoff did not link authority and revision")

        legacy = Path(temp_dir) / "legacy"
        (legacy / ".wallfacer").mkdir(parents=True)
        (legacy / "README.md").write_text("# Legacy Target\n", encoding="utf-8")
        (legacy / ".wallfacer" / "task-contract.json").write_text("{}\n", encoding="utf-8")
        legacy_result = run(str(validate), str(legacy), expected=1)
        if "v1 state detected" not in legacy_result:
            raise SystemExit("v1 state boundary was not reported")
        run(
            str(init), str(legacy), "--objective", "Resume the confirmed target.",
            "--owner", "coordinator-c", "--authority", "README.md",
            "--archive-v1-to", ".wallfacer-v1-legacy",
        )
        if not (legacy / ".wallfacer-v1-legacy" / "task-contract.json").exists():
            raise SystemExit("explicit v1 archive was not preserved")
        run(str(validate), str(legacy))
    print("wallfacer-reverse v2 self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
