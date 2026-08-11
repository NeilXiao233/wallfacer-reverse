#!/usr/bin/env python3
"""Check the bundled reference corpus and cold-artifact locators."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
def digest(p: Path):
    h=hashlib.sha256(); n=0
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b); n+=len(b)
    return n,h.hexdigest()
def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("skill_root"); ns=ap.parse_args(); root=Path(ns.skill_root).resolve(); errors=[]; checked=[]
    idx=json.loads((root/"references/reference-case/trace-index.json").read_text())
    for t in idx.get("traces",[]):
        p=root/"references/reference-case"/t["bundle"]
        if not p.exists(): errors.append(f"missing trace {t['bundle']}")
        else:
            size, sha256 = digest(p)
            if t.get("bytes") is not None and size != t["bytes"]: errors.append(f"size mismatch {t['bundle']}")
            if t.get("sha256") and sha256 != t["sha256"]: errors.append(f"sha256 mismatch {t['bundle']}")
            checked.append(str(p.relative_to(root)))
    mf=json.loads((root/"references/reference-case/artifact-manifest.json").read_text())
    for a in mf.get("artifacts",[]):
        if a.get("sha256") and a.get("uri","").startswith("external://"):
            checked.append(f"cold:{a['id']}:{a['bytes']}:{a['sha256']}")
    out={"valid":not errors,"errors":errors,"checked":checked,"cold_artifacts":len(mf.get("artifacts",[]))}
    print(json.dumps(out,indent=2,ensure_ascii=True)); return 0 if not errors else 1
if __name__ == "__main__": raise SystemExit(main())
