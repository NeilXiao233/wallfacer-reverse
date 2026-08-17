#!/usr/bin/env python3
"""Build a derived v2 handoff that links project authority instead of duplicating it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    args = parser.parse_args()
    root = Path(args.project_root).expanduser().resolve()
    state_dir = root / ".wallfacer"
    state = json.loads((state_dir / "state.json").read_text(encoding="utf-8"))
    project = state["project"]
    ownership = state["ownership"]
    reference = state["reference"]
    checkpoint = state["checkpoint"]
    lines = [
        "# Wallfacer Handoff v2",
        "",
        "This is a derived index. The linked project materials below are authoritative.",
        "",
        "## Target",
        "",
        f"- Objective: {project['objective']}",
        f"- State writer: `{ownership['writer']}`",
        f"- Revision: `{ownership['revision']}`",
        "",
        "## Project Authority",
        "",
    ]
    lines.extend(f"- `{path}`" for path in project["authority"])
    lines.extend(["", "## Reference Method", ""])
    if reference["status"] == "unbound":
        lines.append("- No reference method is bound.")
    else:
        lines.extend([
            f"- Status: `{reference['status']}`",
            f"- Locator: `{reference['locator']['id']}` at `{reference['locator']['path']}`",
            f"- Selection basis: {'; '.join(reference['selection_basis'])}",
            "- Reference material proves method only, never target facts.",
        ])
    lines.extend([
        "",
        "## Checkpoint",
        "",
        f"- Status: `{checkpoint['status']}`",
        f"- Node: `{checkpoint['node']}`",
        f"- Next action: {checkpoint['next_action']}",
        f"- Updated: `{checkpoint['updated_at']}`",
        "",
    ])
    output = state_dir / "HANDOFF.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
