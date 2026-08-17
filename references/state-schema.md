# State Index Schema v2.0.0

`.wallfacer/state.json` is an optional, portable index for one confirmed target. It is not a project ledger, a source of target facts, or a substitute for the project's README, evidence, artifacts, and validation scripts.

```json
{
  "schema_version": 2,
  "skill_version": "2.0.0",
  "project": {
    "root": ".",
    "objective": "confirmed objective",
    "authority": ["README.md", "evidence/ledger.json"]
  },
  "ownership": {"writer": "one-session-or-owner-id", "revision": 1},
  "reference": {
    "status": "unbound",
    "locator": null,
    "selection_basis": []
  },
  "checkpoint": {
    "status": "active",
    "node": "confirmed",
    "next_action": "read the authority materials",
    "updated_at": "RFC 3339 timestamp"
  }
}
```

Required rules:

- `project.authority` contains existing paths relative to the project root. These paths, not the state index, are authoritative.
- `ownership.writer` is the sole writer. `ownership.revision` increments for every checkpoint update. `update_checkpoint.py` rejects another writer or a stale revision.
- `reference.status` is `unbound`, `provisional`, or `confirmed`. A bound reference needs a relative skill-root locator and an explicit selection basis. Reference material may only establish `D-reference-method`.
- `checkpoint` contains one runnable next action. `blocked` requires an objective reopening action; `complete` identifies the project authority that verifies delivery.
- No machine absolute path, `..` traversal, target evidence, asset manifest, attempt log, or route matrix belongs in this file.

v1's `task-contract.json`, `reference-binding.json`, `checkpoint.json`, route matrix, evidence ledger, attempt ledger, and artifact manifest are not read or overwritten by v2. Preserve them as legacy material until useful target facts have been moved into project-local authority documents. Only an explicit `init_project.py --archive-v1-to <new-relative-directory>` atomically renames the v1 directory before creating a new v2 index.
