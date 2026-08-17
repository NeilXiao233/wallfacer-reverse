# Changelog

## 2.0.0 - 2026-08-18

- Replace the automatic v1 state package with an opt-in, single-file state index.
- Make project-local documentation, evidence, artifacts, and verification scripts authoritative.
- Require an explicit objective, one owner, and project authority paths before initialization.
- Add owner and revision guards for checkpoint updates.
- Remove fixed startup declarations, default Griddle binding, parallel ledgers, and automatic challenge escalation.
- Leave v1 state packages untouched; do not silently migrate or overwrite them.
