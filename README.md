# Wallfacer Reverse (面壁者-逆向)

An evidence-led Codex skill for cross-device task recovery and execution. Wallfacer Reverse treats an authoritative reference session as a searchable evidence corpus instead of a free-form summary: it transfers execution methods, decision conditions, and verification patterns, while every target fact must be re-observed on the current project.

## Install

Clone this repository into your Codex skills directory:

```sh
git clone https://github.com/NeilXiao233/wallfacer-reverse.git "$CODEX_HOME/skills/wallfacer-reverse"
```

Restart Codex after installation so it can discover the skill.

## When It Activates

Use `$wallfacer-reverse` or 面壁者-逆向 when continuing a cross-device project, recovering resources from a source-lost package or build, analyzing mobile/Unity/native packages, reconstructing protocols or decode chains, or decomposing complex tasks that require exhausting viable paths.

## How It Works

- Reference corpus: the skill reads the original session traces and workspace index; summaries are navigation only.
- Execution graph: `bind -> audit -> map -> route -> discriminate -> execute -> verify -> checkpoint`.
- Evidence tiers: `A-runtime`, `B-static`, `C-inference`, `D-reference-method`. Reference facts cannot prove target facts.
- Breakthrough protocol: failed routes become evidence, every retry requires a materially different cross-layer route, and progress stops only at verified delivery or a named, evidenced boundary.
- Intensity modes: `difficult` is the default (original workflow); `challenge` discloses all absorbed capabilities and is the automatic escalation target after repeated failure; `hell` delegates to reverse-skill-router only when the user explicitly requests it.
- Portable paths: no machine absolute paths; reference locators resolve relative to the skill root (`locator_base: skill_root`).

## Included Resources

- `SKILL.md`: activation rules and the core workflow.
- `references/state-schema.md`: portable state package fields.
- `references/breakthrough-protocol.md`: failure recovery and route-matrix discipline.
- `references/reverse-capabilities.md`: technical capability catalog.
- `references/reference-case/`: Griddle demo v1.0.0 method corpus (unpacked il2cpp metadata, level/asset JSON, web demo source, sanitized traces, execution graph, key workspace).
- `assets/project-template/`: portable `.mianbizhe` state package template.
- `scripts/`: `init_project.py`, `validate_state.py`, `audit_reference.py`, `build_handoff.py`, `self_test.py`, `sanitize_trace.py`.

## License

[MIT](LICENSE)

---

# 面壁者-逆向（Wallfacer Reverse）

面向跨设备任务恢复与执行的 Codex skill。面壁者把权威参考会话当作可检索的证据语料，而不是可自由改写的总结：它只迁移执行方法、决策条件和验证方式，当前项目的每一个事实都必须重新观察。

## 安装

将本仓库克隆到 Codex 的 skills 目录：

```sh
git clone https://github.com/NeilXiao233/wallfacer-reverse.git "$CODEX_HOME/skills/wallfacer-reverse"
```

安装后重启 Codex，使其发现该 skill。

## 适用场景

通过 `$wallfacer-reverse` 或 `面壁者-逆向` 启用。适用于跨设备继续项目、从源丢失的包或构建中恢复资源、分析移动端/Unity/原生包、还原协议或解码链，以及需要穷尽可行路径的复杂任务。

## 工作机制

- 参考语料：读取原始会话轨迹和工作区索引，总结只作导航入口。
- 执行图：`bind -> audit -> map -> route -> discriminate -> execute -> verify -> checkpoint`。
- 证据分层：`A-runtime`、`B-static`、`C-inference`、`D-reference-method`；参考事实不能证明目标事实。
- 破局协议：失败路径转为证据，每次重试必须换一条实质不同的跨层路线，只在验证交付或命名并证明的客观边界处停止。
- 运行强度：默认 `difficult`（原流程）；反复失败自动升级到 `challenge`（披露全部新增能力）；`hell`（委派 reverse-skill-router 做技术路由）只在用户明确请求时启用。
- 可移植路径：状态包不写机器绝对路径，reference locator 相对 skill 根目录解析（`locator_base: skill_root`）。

## 包含内容

- `SKILL.md`：启用规则与核心流程。
- `references/state-schema.md`：可移植状态包字段。
- `references/breakthrough-protocol.md`：失败恢复与路线矩阵纪律。
- `references/reverse-capabilities.md`：技术能力目录。
- `references/reference-case/`：Griddle demo v1.0.0 方法语料（解包 il2cpp 元数据、关卡/资产 JSON、web demo 源码、脱敏轨迹、执行图、关键工作区）。
- `assets/project-template/`：可移植 `.mianbizhe` 状态包模板。
- `scripts/`：`init_project.py`、`validate_state.py`、`audit_reference.py`、`build_handoff.py`、`self_test.py`、`sanitize_trace.py`。

## 许可证

[MIT](LICENSE)
