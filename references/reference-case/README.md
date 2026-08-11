# Griddle Reference Case

This is a method corpus for the `Griddle demo v1.0.0` workflow. It is not a target project and must never be copied into a target ledger.

Contents:

- `trace-index.json`: bundled compressed session traces and their original local locators.
- `execution-graph.json`: the observed node order, inputs, outputs, evidence, and stop conditions.
- `artifact-manifest.json`: cold artifacts that stay outside this Skill by default.
- `key-workspace/tools/`: small scripts that show extraction, inventory, and verification boundaries.
- `key-workspace/web/`: optional web-node source only; media and level payloads are intentionally omitted.
- `traces/`: `.jsonl.zst` minimally transformed raw traces. They retain user/assistant messages, reasoning, commands, results, and event order, but remove global prompt/world-state envelopes, embedded media, authentication values, local usernames, emails, and device identifiers. Read the relevant turn ranges through the index; do not replace them with a prose summary.

The corpus can establish only `D-reference-method` facts. Names, counts, hashes, device state, and runtime observations must be re-established for the current project.

`MetadataDump.csproj` does not hardcode a machine path: it resolves Il2CppDumper through the `$(IL2CPP_DUMPER_PATH)` MSBuild property, so the same corpus works on any terminal.
