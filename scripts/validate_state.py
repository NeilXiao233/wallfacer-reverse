#!/usr/bin/env python3
"""Validate portable state and reject unverifiable handoffs."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

REQUIRED = ("task-contract.json", "reference-binding.json", "checkpoint.json", "route-matrix.json", "evidence-ledger.json", "attempt-ledger.json", "artifact-manifest.json")
ROUTE_NODES = ("route","discriminate","execute","verify","checkpoint")
SELECTED_ROUTE_NODES = ("discriminate","execute","verify","checkpoint")
ROUTE_STATUSES = {"planned","selected","running","passed","failed","blocked","pending-input"}
EXECUTION_INTENSITIES = {"difficult", "challenge", "hell"}
def load(p: Path):
    try: return json.loads(p.read_text())
    except Exception as e: raise ValueError(f"{p.name}: invalid JSON: {e}")
def is_absolute_path(value: str) -> bool:
    return value.startswith("/") or bool(re.match(r"^[A-Za-z]:[/\\]", value))
def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("project_root"); ns = ap.parse_args()
    state = Path(ns.project_root).expanduser().resolve() / ".mianbizhe"; errors=[]
    docs={}
    for name in REQUIRED:
        p=state/name
        if not p.exists(): errors.append(f"missing {name}"); continue
        try: docs[name]=load(p)
        except ValueError as e: errors.append(str(e))
    contract=docs.get("task-contract.json",{})
    if contract.get("execution_intensity", "difficult") not in EXECUTION_INTENSITIES:
        errors.append("task-contract.execution_intensity must be difficult, challenge, or hell")
    if contract.get("project_id") in (None,"","UNSET"): errors.append("task-contract.project_id is unresolved")
    if contract.get("project_root") and is_absolute_path(str(contract["project_root"])):
        errors.append("task-contract.project_root must be a portable path such as '.'")
    if docs.get("reference-binding.json",{}).get("target_project_id") in (None,"","UNSET"): errors.append("reference-binding.target_project_id is unresolved")
    reference_case=docs.get("reference-binding.json",{}).get("reference_case",{})
    for key in ("bundle_root","trace_index","execution_graph"):
        if reference_case.get(key) and is_absolute_path(str(reference_case[key])):
            errors.append(f"reference-binding.reference_case.{key} must be a portable path relative to skill root")
    if docs.get("checkpoint.json",{}).get("next_action") in (None,"",[]): errors.append("checkpoint.next_action is empty")
    checkpoint=docs.get("checkpoint.json",{})
    routes=docs.get("route-matrix.json",{}).get("routes",[])
    if checkpoint.get("current_node") in ROUTE_NODES and contract.get("objective") in (None,"","UNSET"):
        errors.append("task-contract.objective is unresolved from route node onward")
    if docs.get("route-matrix.json",{}).get("project_id") != contract.get("project_id"):
        errors.append("route-matrix.project_id must match task-contract.project_id")
    if checkpoint.get("current_node") in ROUTE_NODES and not routes:
        errors.append("route-matrix.routes must contain a target-specific route from route node onward")
    route_ids=set()
    for i,r in enumerate(routes):
        if r.get("id"): route_ids.add(r["id"])
        for key in ("id","layer","hypothesis","action","expected_observation","status"):
            if not r.get(key): errors.append(f"route[{i}] missing {key}")
        if not (r.get("input_locator") or r.get("source_files")): errors.append(f"route[{i}] needs input_locator or source_files")
        if not r.get("discriminates"): errors.append(f"route[{i}] needs discriminates")
        if r.get("status") and r["status"] not in ROUTE_STATUSES: errors.append(f"route[{i}] has invalid status {r['status']}")
    selected_route=docs.get("route-matrix.json",{}).get("selected_route")
    if selected_route is not None and selected_route not in route_ids: errors.append("route-matrix.selected_route must identify an existing route")
    if checkpoint.get("current_node") in SELECTED_ROUTE_NODES and not selected_route:
        errors.append("route-matrix.selected_route is required from discriminate node onward")
    evidence=docs.get("evidence-ledger.json",{}).get("entries",[])
    for i,e in enumerate(evidence):
        for key in ("id","claim","evidence_tier","proven_scope"): 
            if not e.get(key): errors.append(f"evidence[{i}] missing {key}")
        if not (e.get("source_files") or e.get("source_turns")): errors.append(f"evidence[{i}] needs source_files or source_turns")
    attempts=docs.get("attempt-ledger.json",{}).get("entries",[])
    for i,a in enumerate(attempts):
        for key in ("id","observation","weakened_hypothesis","next_route"): 
            if not a.get(key): errors.append(f"attempt[{i}] missing {key}")
        if a.get("result") in ("failed","blocked","partial") and not a.get("does_not_block"): errors.append(f"attempt[{i}] must list does_not_block")
    cp=docs.get("checkpoint.json",{})
    if cp.get("status")=="blocked" and not cp.get("next_action"): errors.append("blocked checkpoint needs reopening action")
    if errors:
        print(json.dumps({"valid":False,"errors":errors}, indent=2, ensure_ascii=True)); return 1
    print(json.dumps({"valid":True,"state":str(state),"evidence_count":len(evidence),"attempt_count":len(attempts)}, indent=2, ensure_ascii=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
