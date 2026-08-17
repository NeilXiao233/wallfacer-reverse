# Wallfacer Reverse (面壁者-逆向) v2.0.0

An evidence-led Codex skill for personal project data analysis and source-lost code recovery. Version 2 makes Wallfacer an opt-in recovery assistant: project-local documentation and evidence remain authoritative, while the optional state index supports only a verified handoff.

## Install

```sh
git clone https://github.com/NeilXiao233/wallfacer-reverse.git "$CODEX_HOME/skills/wallfacer-reverse"
```

Restart Codex after installation.

## When To Use It

Use `$wallfacer-reverse` or 面壁者-逆向 for confirmed, complex recovery work that benefits from a prior method or needs cross-session continuity. Do not create state for a short analysis, a one-off change, or a project that already has an adequate README and handoff.

## v2.0.0 Changes

- State is opt-in and is created only after objective, scope, owner, and project authority are known.
- `.wallfacer/state.json` is a minimal index, not a parallel evidence ledger.
- One owner and an optimistic revision guard prevent parallel sessions from silently overwriting state.
- Reference selection is bounded and optional; no target starts with a fixed Griddle binding.
- No fixed proclamation and no automatic `challenge` escalation.
- v1 state packages are left untouched by default; transfer their useful facts into project materials, then explicitly archive the v1 directory before creating a v2 index.

## How It Works

1. Read-only discovery identifies the task, project root, existing authority, and user constraints.
2. Confirm whether a historical method or cross-session state is actually needed.
3. Select only relevant reference evidence, keeping it separate from target facts.
4. Execute target-specific, minimal discriminating tests and record evidence in the project.
5. When needed, use the state index for one checkpoint and a portable handoff.

Evidence tiers remain `A-runtime`, `B-static`, `C-inference`, and `D-reference-method`. A reference method never proves a target fact.

## State Index

Create a v2 index only after confirmation:

```sh
python3 scripts/init_project.py <project-root> \
  --objective '<confirmed objective>' \
  --owner '<single writer id>' \
  --authority README.md
```

The `--authority` values are existing project-relative paths. They are the handoff's facts and validation entry points. Update the state only through `update_checkpoint.py`; pass the current revision so stale or non-owner writers fail instead of overwriting newer work.

For a v1 state package, first move useful facts into project authority, then explicitly preserve it during v2 initialization with `--archive-v1-to .wallfacer-v1-legacy`. The script only renames the directory when that exact flag is supplied.

Transfer ownership rather than sharing writes:

```sh
python3 scripts/transfer_owner.py <project-root> \
  --owner '<current writer id>' --revision <current revision> \
  --new-owner '<next writer id>'
```

## Included Resources

- `SKILL.md`: activation and execution rules.
- `references/state-schema.md`: v2 state-index schema.
- `references/breakthrough-protocol.md`: minimal-test and failure discipline.
- `references/reverse-capabilities.md`: technical capability catalog.
- `references/reference-case/`: Griddle demo v1.0.0 method corpus.
- `assets/project-template/`: `.wallfacer/state.json` template.
- `scripts/`: initialization, ownership-safe checkpoint update and transfer, validation, handoff, reference audit, and self-test tools.

## Verify The Skill

```sh
python3 scripts/self_test.py
python3 scripts/audit_reference.py .
```

## License

[MIT](LICENSE)

---

# 面壁者-逆向（Wallfacer Reverse）v2.0.0

这是一个用于个人项目数据解析与代码丢失支援找回的 Codex Skill。v2 将面壁者收敛为按需介入的恢复助手：项目内 README、证据和验证脚本始终是事实来源；可选状态索引只承担跨会话交接。

## 何时使用

通过 `$wallfacer-reverse` 或 `面壁者-逆向` 启用。适用于已确认、需要参考既有方法或需要跨会话续作的复杂恢复任务。短期分析、一次性修改，或已有充分交接材料的项目不创建状态。

## v2.0.0 变更

- 确认目标、范围、写者和项目权威材料后，才可创建状态。
- `.wallfacer/state.json` 只是最小索引，不再平行维护证据台账。
- 单写者与乐观修订号阻止并行会话静默覆写状态。
- 参考会话按需、有限检索，不再默认绑定 Griddle。
- 移除固定宣言和自动 `challenge` 升档。
- v1 状态包默认不会被改写；先把有效事实归入项目材料，再明确归档旧目录并创建 v2 索引。

## 工作方式

1. 只读识别任务、项目根、既有材料和用户限制。
2. 确认是否真的需要历史方法或跨会话状态。
3. 仅选择相关参考证据，并与目标事实隔离。
4. 在项目内执行目标专属的最小区分测试并记录证据。
5. 需要续作时，使用状态索引记录一个 checkpoint 并生成可移植交接。

证据分层仍为 `A-runtime`、`B-static`、`C-inference`、`D-reference-method`；参考方法不证明当前目标事实。

## 状态索引

确认后才创建：

```sh
python3 scripts/init_project.py <project-root> \
  --objective '<已确认目标>' \
  --owner '<唯一写者标识>' \
  --authority README.md
```

`--authority` 是既有项目内相对路径，承载事实与验证入口。只能通过 `update_checkpoint.py` 更新状态，并携带当前 revision；过期写者或非 owner 会失败，不能覆盖新状态。

项目已有 v1 状态时，先把有效事实归入项目材料，再在初始化时明确传入 `--archive-v1-to .wallfacer-v1-legacy`。只有该参数存在，脚本才会重命名旧目录。

交接时转移写者，不共享写入权限：

```sh
python3 scripts/transfer_owner.py <project-root> \
  --owner '<当前写者标识>' --revision <当前 revision> \
  --new-owner '<下一写者标识>'
```

## 包含内容

- `SKILL.md`：启用与执行规则。
- `references/state-schema.md`：v2 状态索引格式。
- `references/breakthrough-protocol.md`：最小测试与失败纪律。
- `references/reverse-capabilities.md`：技术能力目录。
- `references/reference-case/`：Griddle demo v1.0.0 方法语料。
- `assets/project-template/`：`.wallfacer/state.json` 模板。
- `scripts/`：初始化、安全 checkpoint 更新和所有权转移、校验、交接、参考审计和自检工具。

## 验证 Skill

```sh
python3 scripts/self_test.py
python3 scripts/audit_reference.py .
```

## 许可证

[MIT](LICENSE)
