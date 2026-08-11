#!/usr/bin/env python3
"""Build a concise, evidence-linked handoff from state JSON files."""
from __future__ import annotations
import argparse, json
from pathlib import Path
def j(p): return json.loads(p.read_text())
def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("project_root"); ns=ap.parse_args(); root=Path(ns.project_root).expanduser().resolve(); s=root/".mianbizhe"
    c=j(s/"task-contract.json"); b=j(s/"reference-binding.json"); cp=j(s/"checkpoint.json"); rm=j(s/"route-matrix.json"); ev=j(s/"evidence-ledger.json"); at=j(s/"attempt-ledger.json"); am=j(s/"artifact-manifest.json")
    lines=["# 面壁者交接", "", f"- project: `{c.get('project_id')}`", f"- execution intensity: `{c.get('execution_intensity', 'difficult')}`", f"- objective: {c.get('objective')}", f"- current node: `{cp.get('current_node')}`", f"- status: `{cp.get('status')}`", "", "## Scope", "", f"- webapp demo: `{c.get('scope',{}).get('include_webapp_demo')}`", f"- authorized runtime: `{c.get('scope',{}).get('authorized_runtime')}`", f"- exclusions: {json.dumps(c.get('exclusions',[]), ensure_ascii=True)}", "", "## Proven Evidence", ""]
    if not ev.get("entries"): lines.append("- No target evidence has been entered yet.")
    for e in ev.get("entries",[]): lines.append(f"- `{e.get('id')}` [{e.get('evidence_tier')}]: {e.get('claim')} (scope: {e.get('proven_scope')}; source: {', '.join(e.get('source_files',[])+e.get('source_turns',[]))})")
    lines += ["", "## Failed Or Partial Routes", ""]
    if not at.get("entries"): lines.append("- No failed routes have been entered.")
    for a in at.get("entries",[]): lines.append(f"- `{a.get('id')}` [{a.get('result','unknown')}]: {a.get('observation')}; next route: {a.get('next_route')}")
    lines += ["", "## Route Matrix", ""]
    if not rm.get("routes"): lines.append("- No target route has been selected yet.")
    for route in rm.get("routes",[]): lines.append(f"- `{route.get('id')}` [{route.get('status')} / {route.get('layer')}]: {route.get('action')} -> {route.get('expected_observation')}")
    lines += ["", "## Reference Binding", "", f"- case: `{b.get('reference_case',{}).get('id')}`", "- Reference material provides method only; target facts must be reproven.", "", "## Artifacts", ""]
    for a in am.get("artifacts",[]): lines.append(f"- `{a.get('id')}`: {a.get('kind')} ({a.get('bytes')} bytes, sha256={a.get('sha256') or 'not recorded'})")
    lines += ["", "## Next Action", "", f"`{cp.get('next_action')}`", ""]
    out=s/"HANDOFF.md"; out.write_text("\n".join(lines)); print(out); return 0
if __name__ == "__main__": raise SystemExit(main())
