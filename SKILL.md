---
name: wallfacer-reverse
version: 2.0.0
description: 面壁者是用于个人项目数据解析与代码丢失支援找回的按需恢复 Skill。它检索参考会话的方法，不接管当前项目的事实、台账或工作流。
---

# 面壁者

面壁者的职责是：在已确认的复杂恢复任务中，把方法、证据边界、失败观察和下一步整理成可验证、可续作的最小记录。它不猜测任务，不在证据不足时建立权威状态，也不替代项目已有 README、证据、任务卡和验证脚本。

## 使用门槛

先只读识别以下事实：

1. 当前目标、范围、明确排除项，以及本轮是分析还是执行。
2. 项目根目录和已有权威材料（README、任务卡、证据目录、验证脚本）。
3. 是否真的需要历史会话的方法，还是现有项目材料已经足够。

只做分析、定位或短期局部修改时，不创建 `.wallfacer/`，不读取整套参考语料，也不输出固定宣言。

只有用户明确要求跨会话/跨设备交接，或当前任务确实长期、复杂且项目缺少可续作交接时，才创建状态索引。创建前必须已确认目标、状态写者和至少一项项目内权威材料。

## 最小启动顺序

`discover -> confirm -> inspect -> select reference (optional) -> execute -> checkpoint (optional)`

- `discover`：只读定位目标、目录和现有材料。
- `confirm`：确认目标、范围、执行授权及状态是否必要。
- `inspect`：以项目材料为准建立当前事实；不从参考会话继承名称、数量、哈希、路径、运行时结论或限制。
- `select reference`：仅在需要时，以目标标识、任务类型和排除项检索最小相关片段。先为 `provisional`，只有适配依据明确才为 `confirmed`。
- `execute`：优先做最小区分性测试和可逆动作。
- `checkpoint`：仅在需要续作时更新最小索引，指向项目内的权威材料。

用户可见的首次进度只说明事实与下一动作，例如：`已确认：当前任务为中文化；README 与翻译映射是事实来源；本轮无需跨会话状态。`

## 权威性与单写者

项目内 README、任务卡、证据、产物清单和验证脚本是唯一的项目事实来源。`.wallfacer/state.json` 只保存：这些材料的相对路径、一个 checkpoint、参考方法的定位、单一写者和修订号。它不得复制项目证据、资产清单、失败台账或路线矩阵。

默认一个状态索引只能有一个写者。其他会话只能提供带来源的候选发现，不能直接改写共享状态。状态更新必须通过 `scripts/update_checkpoint.py`，并同时匹配 `owner` 与 `revision`；交接时用 `scripts/transfer_owner.py` 显式转移所有权，而不是并行共写。

v1 的七文件状态包不会被 v2 脚本自动迁移或覆盖。先将其中仍有价值的事实归入项目权威材料；只有随后明确传入 `--archive-v1-to .wallfacer-v1-legacy`，初始化脚本才会原子归档旧目录并创建 v2 索引。

## 参考会话与技术能力

参考语料只能证明 `D-reference-method`：方法、决策条件和验证模式。先查索引和相关 turn，再按需读取原始轨迹；不要全量加载，也不要默认绑定 Griddle 或任何案例。

受保护/加密载体已由当前目标证实且密钥未恢复时，密钥提取可以成为该目标的局部最高优先路线。非加密、中文化、GM、UI、资产整理等任务跳过该策略。`challenge` 和 `hell` 都必须由用户明确请求或接受，不自动升级；`hell` 仍只用于调用 `reverse-skill-router` 做技术补充。

## 失败与证据纪律

目标专属尝试才进入项目自己的失败记录：必须包含输入/环境、精确观察、被削弱的假设、仍未阻塞的动作、下一条实质不同路线和证据定位。

状态校验、Skill 更新、参考审计、模板维护、目录迁移和交接格式化不是目标技术尝试，不得计入失败次数，也不得触发能力升级。

每个结论应标记 `A-runtime`、`B-static`、`C-inference` 或 `D-reference-method`，并附当前项目来源和适用范围。一次失败、工具报错或设备暂不可用都不能成为永久禁令。

## 状态索引与交接

创建状态索引：

```bash
python3 scripts/init_project.py <project-root> \
  --objective '<confirmed objective>' \
  --owner '<single writer id>' \
  --authority README.md
```

同一项目已有 v1 状态时，先完成事实迁移，再在上述初始化命令末尾追加 `--archive-v1-to .wallfacer-v1-legacy`。

更新 checkpoint：

```bash
python3 scripts/update_checkpoint.py <project-root> \
  --owner '<single writer id>' --revision <current revision> \
  --node execute --next-action '<one concrete action>'
```

转移写者：

```bash
python3 scripts/transfer_owner.py <project-root> \
  --owner '<current writer id>' --revision <current revision> \
  --new-owner '<next writer id>'
```

在交接前运行：

```bash
python3 scripts/validate_state.py <project-root>
python3 scripts/build_handoff.py <project-root>
```

`audit_reference.py` 和 `self_test.py` 用于 Skill 部署/更新验证，不属于项目启动或目标失败记录。

## 资源导航

- 参考案例协议：`references/reference-case/README.md`
- 状态格式：`references/state-schema.md`
- 失败与最小区分测试：`references/breakthrough-protocol.md`
- 技术能力目录：`references/reverse-capabilities.md`
- 项目模板：`assets/project-template/.wallfacer/`
- 初始化、更新、校验和交接脚本：`scripts/`
