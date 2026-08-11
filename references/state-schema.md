# State Schema

`.mianbizhe/` is the portable state package for one target project. It is deliberately split into binding, evidence, attempts, and checkpoint files.

Required files:

- `task-contract.json`: immutable target, scope, exclusions, and deliverables.
- `reference-binding.json`: the exact reference case and its locators. It must not contain target facts. `locator_base: skill_root` means `bundle_root`, `trace_index`, and `execution_graph` resolve relative to the directory containing the 面壁者 skill; portable paths never include a machine absolute path.
- `checkpoint.json`: the current node and one executable next action.
- `route-matrix.json`: target-specific hypotheses, materially different routes, and minimal discriminating tests.
- `evidence-ledger.json`: claims with evidence tier and proven scope.
- `attempt-ledger.json`: every failed or partial route and its changed hypothesis.
- `artifact-manifest.json`: hashes, sizes, URIs, and restore commands for cold artifacts.

Optional task contract field:

- `execution_intensity`: `difficult` (default), `challenge`, or `hell`. It records how much technical capability is disclosed and whether the passive reverse router is delegated to. Automatic routing: `difficult` escalates to `challenge` after two consecutive failed or partial attempts without a passed route; `hell` is entered only on an explicit user request and is never automatic.

Portable path rule: `task-contract.project_root` is `"."` (the directory containing `.mianbizhe`) and reference locators are relative to the skill root. The state package must not store `/Users/...`, `C:\...`, or other machine-specific absolute paths; the validator rejects them.

Evidence tiers are intentionally explicit: `A-runtime`, `B-static`, `C-inference`, and `D-reference-method`. A `D-reference-method` entry can describe how a test was selected, but cannot prove a target fact.

The portable package may contain `UNSET` placeholders after initialization. Before execution, replace them in `task-contract.json` and `reference-binding.json`; the validator rejects unresolved target identity at any time, with or without evidence.

When `checkpoint.current_node` is `route`, `discriminate`, `execute`, `verify`, or `checkpoint`, at least one route must be present and its `status` must be explicit. This prevents a handoff from claiming progress while retaining only a generic plan.

Allowed route statuses are `planned`, `selected`, `running`, `passed`, `failed`, `blocked`, and `pending-input`. `selected_route` must name an existing route. From `discriminate` onward, it is required. The route-matrix project ID must match the task contract.
