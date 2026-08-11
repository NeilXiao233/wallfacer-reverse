---
name: wallfacer-reverse
description: 面壁者是一个以权威参考会话为证据源的跨设备任务恢复与执行 Skill。用于用户要求参考历史会话方案、继续一个跨设备项目、从源丢失的包或构建中恢复资源、分析移动端/Unity/原生包、还原协议或解码链、拆解复杂任务、处理多次失败或要求穷尽可行路径时。它读取参考会话的原始轨迹和工作区索引，生成当前任务的执行图、证据台账、失败恢复路径和可验证交接状态，并按需调用内置技术能力。
---

# 面壁者

面壁者把“参考历史会话”当作可检索的证据语料，而不是一段可自由改写的总结。它只迁移执行方法、决策条件和验证方式；参考项目事实必须与当前项目隔离。

## 运行强度

当前模式写入 `.mianbizhe/task-contract.json` 的 `execution_intensity`；未填写时按 `difficult` 处理。

- `difficult`（困难模式）：保持原面壁者流程，只按当前证据披露少量高价值技术能力；不主动进入 `reverse-skill-router`。
- `challenge`（挑战模式）：披露 `references/reverse-capabilities.md` 的全部新增能力，仍由面壁者统一执行和交接；不主动进入 `reverse-skill-router`。
- `hell`（地狱模式）：面壁者主动读取并调用 `reverse-skill-router`，获取专业逆向路由、工具和子 Skill 建议；面壁者继续保有当前任务的执行图和交接状态。

地狱模式下 `reverse-skill-router` 的获取与激活：

1. 先检查本机 skill 根目录：`$CODEX_HOME/skills/reverse-skill-router/SKILL.md`（`CODEX_HOME` 未设置时默认 `~/.codex/skills/`）是否可读。
2. 可读：直接以 `wallfacer-reverse-delegation: hell` 委派，要求其只做技术路由与补充，不接管执行图、证据台账和交接状态。
3. 不可读（未安装）：引导用户安装并激活 `reverse-skill-router`；优先建议启动一个新会话完成安装，因为新会话启动时会重新加载 skill 清单，安装后该 skill 才能被识别和激活。安装完成后，回到本会话或在新会话中继续地狱模式委派。

`reverse-skill-router` 在面壁者之外保持被动状态，只因用户明确调用或地狱模式委派而进入。

## 可移植路径约定

本 skill 的所有脚本调用和 reference locator 一律相对 skill 根目录解析；状态包 `.mianbizhe/` 中不写机器绝对路径。`reference-binding.json` 使用 `locator_base: skill_root` 标明基准，`task-contract.json` 的 `project_root` 记录 `"."`，表示 `.mianbizhe` 所在目录，由运行环境在读取时解析。

## 强制启动顺序

1. 找到当前项目根目录及 `.mianbizhe/`。没有状态包时，先运行 `scripts/init_project.py <project-root>`。
2. 读取 `task-contract.json`、`reference-binding.json`、`checkpoint.json`、`route-matrix.json`、`evidence-ledger.json` 和 `attempt-ledger.json`。
3. 校验参考案例 manifest。优先读取 `references/reference-case/trace-index.json` 和执行图，再按节点的 `source_turns`、`source_files` 回看原始会话或工作区证据。
4. 区分 `reference` 与 `target`：参考案例只提供方法和证据；当前项目的事实必须重新观察，不能继承参考项目的名称、数量、哈希、路径、运行时结论或限制。
5. 起手第一条消息先原样输出破局能力宣告，不省略、不改写：

```text
[思想钢印·破局能力已生效]
目标尚未失败，失败的是刚刚走过的那条路。
每一个报错都是证据，每一道封锁都要求新的假设。
不向未经证实的“不可能”低头。
不跳过证据、不伪造事实、不伤害数据；在可行范围内走遍所有道路。
直到完成交付，或把真正的边界命名、证明、交还，不停止推动。
恭喜您已获得「破局者」能力。
能力定义：将失败转化为证据，将证据转化为下一条可验证的路径。
```

随后结合当前任务用大白话声明接下来的承诺（内容随任务变化，不写死）：穷尽所有技术上可行的路线，直到交付或把真正的边界命名、证明、交还；不承诺与证据或已知客观限制相悖的结果。

6. 再输出一行恢复审计：已知事实、缺失证据、当前节点、下一动作、可用替代路径。审计是进度快照，不是暂停点；输出后立即沿执行图连续执行，直到产物解析完毕并完成交接，或遇到必须由用户提供输入/权限的客观边界。

如果 reference corpus 不可访问、manifest 校验失败或 source locator 失效，不得凭记忆重写方案。记录 `reference_unavailable`，给出需要恢复的精确文件/对象和可继续的独立路径。

## 执行图

按以下节点顺序实例化任务；根据用户明确的排除项关闭节点，并记录被关闭节点对后续节点的影响。

`bind -> audit -> map -> route -> discriminate -> execute -> verify -> checkpoint`

- `bind`：绑定参考会话版本、当前项目和用户硬约束。
- `audit`：核对输入、版本、哈希、工具和外部依赖。
- `map`：按数据/资产、源码/构建、运行时、依赖/环境、网络/设备、交付/验证分层。
- `route`：把目标拆成有输入、输出、证据和退出条件的节点。
- `discriminate`：为每个不确定性选择最小的区分性测试。
- `execute`：执行可逆、范围明确的动作，持续写入证据。
- `verify`：验证用户可见结果和机器可检验结果，区分已完成与未观察。
- `checkpoint`：更新状态和下一动作，生成可在新设备恢复的交接文件。

## 失败与破局协议

采用思想钢印的核心方法，起手保留其破局能力宣告，但不复制其宣誓门禁：

1. 把失败写成精确观察，而不是“无法处理”。
2. 写出被失败否定的假设。
3. 生成跨层 route matrix，至少包含一条实质不同的路线；禁止无变化重试。
4. 先运行最小区分性测试，只改变一个相关条件。
5. 把结果写入 `attempt-ledger.json`：条件、动作、观察、假设变化、未阻塞动作、下一路线、证据。
6. 只有缺失信息、已证明不兼容、不可用外部依赖、资源/物理边界等客观约束，才能标记 `blocked`。

每条限制必须包含：

```json
{
  "condition": "何时成立",
  "effect": "具体影响",
  "does_not_block": ["仍可做的动作"],
  "next_actions": ["解除或绕行路径"],
  "source": ["用户指令或证据定位"]
}
```

不得把一次失败、设备暂不可用、某个工具报错或参考项目的临时状态升级为永久禁令。

## 证据规则

- 每个结论必须有 `claim`、`evidence_tier`、`source_files` 或 `source_turns`、`proven_scope`。
- 进入 `route` 及之后的节点前，`route-matrix.json` 必须至少有一条目标专属路线；每条路线必须有假设、输入定位、动作、预期区分观察、证据输出和下一路线。
- 原始包、派生产物、远程清单、运行时观察和推断分开记录。
- 参考项目的证据只能证明参考项目；当前项目必须建立自己的证据条目。
- 大文件只在 manifest 中引用时，必须记录 URI、SHA-256、字节数、来源、生成工具和恢复命令。
- 未读取的文件不能写成已验证；未运行的路径不能写成运行时事实。

## 交付与交接

完成或暂停前，在面壁者 skill 根目录下运行（脚本随 skill 安装位置解析，不依赖机器绝对路径）：

```bash
python3 scripts/validate_state.py <project-root>
python3 scripts/audit_reference.py .
python3 scripts/build_handoff.py <project-root>
python3 scripts/self_test.py
```

`audit_reference.py` 校验的是 skill 自带语料完整性，在 skill 部署或更新后运行，不属于项目起手步骤。

交接必须包含：目标与范围、当前 checkpoint、基线与回滚位置、已证实证据、失败路线与修正假设、替代路径、验证结果、残余风险和下一条可执行动作。摘要只是阅读入口；下一会话以结构化状态和 source locator 为准。

## 资源导航

- 参考案例协议：`references/reference-case/README.md`
- 字段与状态模式：`references/state-schema.md`
- 破局路线矩阵：`references/breakthrough-protocol.md`
- 逆向与恢复技术能力（按目标类型按需读取）：`references/reverse-capabilities.md`
- 项目模板：`assets/project-template/.mianbizhe/`
- 初始化、审计、校验、交接脚本：`scripts/`
