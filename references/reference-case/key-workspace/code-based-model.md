# Griddle! 玩法 / 出题规则 / 题库模型恢复（代码证据版）

## 0. 证据边界与来源

本文件不把 JSON 字段当作玩法规则，也不凭游戏画面猜测。每条结论都连接到以下可直接核验的代码/二进制证据：

| 证据 | 路径 | 说明 |
| --- | --- | --- |
| IL2CPP metadata | `device/ipa-extracted/Payload/Griddle.app/Data/Managed/Metadata/global-metadata.dat` | metadata v31，未加密，可解析类型/字段/方法/参数 |
| metadata 全量导出 | `output/il2cpp-metadata-full.json` | 19,163 个类型，128,612 个方法 |
| 核心签名阅读版 | `output/il2cpp-core-signatures.txt` | 题库模型、玩法系统、出题调度系统的字段/方法签名 |
| 视图/配置签名阅读版 | `output/il2cpp-view-config-signatures.txt` | `CellView`、`ItemView`、`ClueListView`、教程/机制配置签名 |
| Unity 符号文件 | `device/ipa-extracted/Payload/Griddle.app/Data/Managed/il2cpp.usym` | 含 Jenkins 源码路径：`puzzle_build-griddle-unity-ios/Assets/...` |
| 关卡 JSON | `output/levels/*.json` | 249 个明文关卡/修订，全部来自 `https://cdn.cheer.gs/levels/{key}.json` |
| Saga 关卡配置 | `output/unity-extract/text/Griddle_SagaLevels_240_01.08_OPTIMIZED_LOCKKEYFIRST_214LEVELS__6794640863438724813.json` | 214 关的正式调度配置 |

客观限制：App Store 主二进制 `UnityFramework` 是加密 Mach-O（`cryptid=1`），且缺少 `get-task-allow`，无法附加 LLDB，也不能用 Il2CppDumper 反汇编方法体。因此下面每条规则引用的是“类型/字段/方法/参数签名 + 字符串常量 + 真实关卡数据”，方法体内的具体赋值与分支没有伪装成已反汇编。

---

## 1. 题库模型

### 1.1 顶层模型

`CheerGames.Shared.LevelJsonModel`

- 源码路径：`Assets/_Shared/Scripts/Models/LevelJsonModel.cs`
- 字段（metadata 直接导出）：

```text
EditorVersion, Hash, Revision, PosterId, PosterImageCGAssetId, PosterTitle,
Grid, Items, Clues, Cells, AssetCatalog
```

- 关键方法（metadata 直接导出）：

```text
FromJson(json)
GetHashWithRevision()
GetReferencedCGAssetIds()
IsSpriteUsable(sprite)
TryGetSpriteTexture(sprite, texture)
OnDeserialized(context)
ResolveClueSpritePlaceholders()
ClearRuntimeSprites()
```

实际关卡 JSON 与这些字段一一对应。示例：`output/levels/001_DF4A43E0F299F729FB2303651F47206C_20.json` 顶层包含 `hash`、`revision`、`creator`、`editor_version`、`poster_id`、`poster_title`、`grid`、`items`、`clues`、`cells`、`poster_image_cgasset_id`、`cgasset_catalog`。

### 1.2 网格模型

`GridInfo`：`Width`、`Height`、`Columns`、`RowNames`，并有 `OnDeserialized(context)`。

`ColumnInfo`：`Name`、`ImageId`、`ImageCGAssetId`、`ImageData`、`Sprite`，并有 `HasImageSource`、`ApplySprite(sprite)`、`Base64ToSprite(base64)`。

实际示例：

```json
"grid": {
  "width": 2,
  "height": 2,
  "columns": [
    { "name": "Mom", "image_id": "img-1692", "image_cgasset_id": "5065FF..." },
    { "name": "Dad", "image_id": "img-1684", "image_cgasset_id": "4B88FB..." }
  ],
  "row_names": ["Food", "Drink"]
}
```

### 1.3 物品模型

`Item`（源码文件同样是 `LevelJsonModel.cs`）字段：

```text
Id, Name, Icon, ImageCGAssetId, ImageData, ConnectedTo, Revealed, HideText,
Cells, Sprite, DisplayText, TrimmedSprite, ContentAspect, SpriteAspect
```

计算属性：

```text
IsMultiCell, IsOnlyText, IsImageOnly, HasImage, HasImageSource
```

`ItemCellInfo`：`JsonColumn`、`JsonRow`。JSON 中每个物品的 `cells` 数组就是 `ItemCellInfo` 列表，例如 `[{"column":1,"row":1}]`；一个物品有多个 cell 时，`Item.IsMultiCell` 为真。

### 1.4 线索模型

`ClueData` 字段：

```text
Id, Content, ConnectedItemIds, IsRevealed, DisplayContent
```

关键方法：

```text
ResolveSpritePlaceholders(columnIndexByName, itemIndexByName)
```

`Content` 使用两类占位符，真实关卡数据可验证：

```text
{Mom} eats [Pancakes]
[Pancakes] comes with [Coffee]
```

`{...}` 对应列头（`ColumnInfo.Name`），`[...]` 对应物品（`Item.Name`）。`ClueContentResolver` 和 `ClueSpriteAtlasBuilder` 的源码路径为：

```text
Assets/_Shared/Scripts/Utils/ClueContentResolver.cs
Assets/_Shared/Scripts/Utils/ClueSpriteAtlasBuilder.cs
```

### 1.5 格子与锁/帘模型

`CellData` 字段：

```text
Id, JsonColumn, JsonRow, Lock, LockAndKey
```

`LockAndKeyData` 字段：

```text
Type, Color
```

计算属性：

```text
IsKey, IsLock
```

实际关卡数据中存在两种 cell 数据：

1. 只有数字 `lock`：例如 `output/levels/040_66FC9C99F78D9D271A5034DCBDE70C06_24.json` 中 `{"id":"cell-1","column":3,"row":1,"lock":9}`。
2. 带 `lock_and_key` 对象：例如 `output/levels/025_97C0DE8C1B901EC73EFED917E565F2EE_23.json` 中：

```json
{
  "id": "cell-4",
  "column": 1,
  "row": 4,
  "lock": 0,
  "lock_and_key": { "type": "key", "color": "red" }
}
```

### 1.6 资源目录模型

`CGAssetCatalog`：`Url`、`Assets`，方法 `TryGetEntry(cgAssetId, entry)`。

`CGAssetEntry`：`FileFormat`、`Folder`。

关卡 JSON 中：

```json
"cgasset_catalog": {
  "url": "https://cdn.cheer.gs",
  "assets": {
    "81A147...": { "file_format": "png", "folder": "Posters" },
    "5065FF...": { "file_format": "png", "folder": "Profiles" },
    "B396BC...": { "file_format": "png", "folder": "Icons" }
  }
}
```

---

## 2. 游戏玩法

### 2.1 关卡构建

`GriddleLevelSetupSystem.InitializeLevelAsync(levelModel, cancellationToken)` 负责初始化；`GriddleLegacyLevelBuilder.BuildAsync(levelJsonModel, cancellationToken)` 构建整个关卡。

`GridSpawner.Build(rows, columns, spacing, columnHeaderSpacing, columnInfos, rowNames)` 明确把 `LevelJsonModel.Grid` 转成 `GridModel`。`GridSpawner` 字段还包含 `cellPrefab`、`itemViewPrefab`、`columnHeaderPrefab`、`rowHeaderPrefab`、`keyPrefab`、`keyContainer`、`itemsLayer`、`itemsFlightLayer`。

### 2.2 点选与放置

可确认的调用链（方法名和参数来自 metadata，不是画面推测）：

```text
GriddleCellSelectionSystem.OnCellTapped(row, col)
  -> GetUnrevealedItemsInRow(row)
  -> SelectionPanel.Show(cell, options, cellsInRow, onSelected)
  -> GriddleItemPlacementSystem.OnItemSelected(cellView, selected, itemView)
```

`GriddleCellSelectionSystem` 还有 `OnItemViewTapped(itemView)`、`IsItemPendingClonePlacement(itemId)`；`SelectionPanel.Show` 的 `cellsInRow` 参数说明同一行内的候选物品会一起展示。

放置后进入判定：

```text
GriddleLevelSession.FindSlotForItem(cell, itemId)
GriddleLevelSession.FindUnrevealedSlot(cell)
GriddleLevelSession.AreAllCellsRevealed(grid)
GriddleLevelSession.AreAllItemsRevealedForClue(clue, grid)
GriddleLevelSession.AreAllTriggerItemsRevealed(clueId, grid)
GriddleLevelSession.AreAllItemsRevealedOnGrid(itemIds, grid)
GriddleLevelSession.IsItemRevealedOnGrid(item, grid)
GriddleLevelSession.TryMarkClueCompleted(clueId)
GriddleItemPlacementSystem.TryTriggerLevelCompleted()
```

线索完成后的表现由 `GriddleClueRevealSystem` 处理：

```text
RevealConnectedClues(item, sourceWorldPos, hideCompleted, onCompletedCluesHidden)
HideCompletedClues(useEraserAnimation, onAllHidden)
RevealNextUnrevealedClue()
RevealClueFromExtraButton(clue, autoComplete)
IsExtraClueUnlocked()
```

`ClueListView`/`CluePanelView` 中有 `Init(clues, spriteAsset, revealedClueIds)`、`RevealClue(data, sourceWorldPos, completeAfterReveal)`、`HideClue(clueId, useEraserAnimation, onSlideOutFinished)`，与上面对应。

### 2.3 多格物品

`Item.IsMultiCell`、`Cell.Slots`、`CellSlot`（`Item` + `IsRevealed` + `Reveal()`）说明一个物品可以占据一个格子的多个 slot，也可以占多个格子。

对应放置系统方法：

```text
RevealAllClonesOf(item)
RevealClonesExcluding(item, excludeRow, excludeCol)
ProcessPendingClonePlacements()
ExecuteDeferredPlacement(item, row, col, slotIndex)
```

会话字段 `PendingClonePlacements`、`AnimatedRows`、`AnimatedColumns` 说明多格/跨行列的克隆揭示是延迟/分批动画。

### 2.4 帘幕（数字 lock）

`Cell` 字段/属性：

```text
CurtainCount, IsCurtained, SetCurtain(curtainCount), DecrementCurtain()
```

`CellView` 字段/方法：

```text
curtainOverlay, curtainIcon, curtainCountText, curtainAnimator, curtainParticle
SetCurtain(curtainCount), DecrementCurtain(), PlayCurtainReveal(onComplete),
PlayCurtainOpenAnimation(onComplete), PlayCurtainShake(), PlayCurtainCountPunch()
```

放置系统方法：

```text
DecrementAllCurtains(amount)
PlayCurtainRevealOn(row, col, onComplete)
PlayObstacleReveal(row, col, onComplete)
```

关卡 JSON 中 88 个关卡存在“只有数字 `lock`、没有 `lock_and_key`”的 cell，共 129 个 cell；`CellData.Lock` 是模型中唯一与 `Cell.CurtainCount` 对应的数字字段。具体“`Lock` 读入 `SetCurtain` 的赋值语句”在加密方法体内，尚未反汇编。

### 2.5 钥匙/锁

`LockAndKeyData` 只有 `Type` 和 `Color`，实际 JSON 使用字符串值：

```text
type: key | lock
color: red | green | blue
```

`Cell` 相关：

```text
LockAndKey, IsLocked, IsBlocked, SetLockAndKey(data), ClearNewLock()
```

放置系统相关：

```text
TryUnlockNewLocksByKey(row, col)
FindKeyCell(color)
PlayKeyLockReveal(lockRow, lockCol, onComplete)
```

`GridSpawner`：

```text
PlaceKeyInstances(cellView, count, sprite)
ShakeKeyInstancesForColor(color)
ShakeLock(cellView)
```

`CellView`：

```text
SetLockAndKey(data), GetKeySprite(color), AddKeyInstance(rt),
PlayLockKeyUnlockAnimation(onComplete), ClearLockAndKeyAnimated(onComplete)
```

`LockKeyColorConfig`：`Color`、`LockTopSprite`、`LockBottomSprite`、`KeySprite`。

数据统计：249 关中有 90 关包含 `lock_and_key`，共 224 个 cell；其中 105 个 `key`、119 个 `lock`，颜色为 red/green/blue。

### 2.6 提示与橡皮擦

`HintBoosterManager`：

```text
FindBestHintItem()
FindBestHintItem(excludeKeyCells)
FindAnyUnrevealedItem(excludeKeyCells)
CountUnrevealedItems(clue, excludeKeyCells)
HasUnrevealedSlots(item, excludeKeyCells)
IsKeyCell(cell)
```

`EraserBoosterManager`：

```text
OnEraserRequested(), OnClueSelected(clueId), EndEraser(), ExitEraserMode()
```

配合：

```text
GriddleItemPlacementSystem.OnClueCompletedByEraser(clueId)
GriddleItemPlacementSystem.FlyEraserItem(item, cellView, slotIndex, onComplete)
ClueListView.SetCluesEraserMode(active), EnableClueSelection(onClueSelected)
```

### 2.7 教程

`TutorialController`：

```text
StartTutorial(cell, correctItem, clue, selectionPanel, onCellClicked)
ShowGuidedHint(cell, clues, onCellClicked)
HasCompletedOnboarding
```

`GriddleCellSelectionSystem`：

```text
InitTutorial(), OnTutorialCellClicked()
```

`MechanicIntroductionSystem`：

```text
IsMechanicTutorialLevel(levelIndex, tutorialType)
HasNewMechanicToShow(levelIndex)
GetNextMechanicTutorialType(currentLevelIndex)
GetHeaderText(tutorialType), GetDescriptionText(tutorialType), GetSprite(tutorialType)
```

### 2.8 分析事件

metadata 字符串常量直接包含：

```text
clue_started, clue_completed, clue_id, difficulty,
use_hint, use_eraser, tutorial_begin, tutorial_complete
```

对应方法：

```text
GriddleClueRevealSystem.SendClueStarted(clueId)
GriddleClueRevealSystem.SendClueCompleted(clueId)
GriddleClueRevealSystem.FireInitialClueStartedEvents()
```

---

## 3. 出题 / 题库调度规则

### 3.1 Saga 正式配置

实际 feature flag 文本资产：

```text
Griddle_SagaLevels_240_01.08_OPTIMIZED_LOCKKEYFIRST_214LEVELS__6794640863438724813.json
```

内容：

```json
{
  "name": "Griddle_SagaLevels_240",
  "catalog_name": "01.08_OPTIMIZED_LOCKKEYFIRST_214LEVELS",
  "url": "https://cdn.cheer.gs",
  "levels": {
    "1": {
      "key": "DF4A43E0F299F729FB2303651F47206C_20",
      "difficulty": "NORMAL",
      "is_usable_in_loop": false,
      "tutorial_type": "ONBOARDING",
      "emre_difficulty": "NONE"
    }
  }
}
```

统计：

```text
level_count: 214
difficulty: NORMAL x 214
tutorial_type: ONBOARDING x 1, NONE x 213
is_usable_in_loop: false x 6, true x 208
```

### 3.2 调度模型

`SagaLevelEntryModel`：

```text
Key, IsUsableInLoop, Difficulty, TutorialType
```

`SagaLevelsFFJModel`：

```text
FLAG_NAME, CatalogName, Url, Levels
```

`LevelDecisionSystem` 字段：

```text
_loopLevels
_sagaLevelsFeatureFlagJsonModel
_levelIndexesByHashRevision
_levelIndexToHashRevisionCache
_inGameBoosterTutorials
AssetPrefetchWindow
AvailableLevelIndexesByDifficulty
```

`LevelDecisionSystem` 方法：

```text
InitWithDataAsync(sagaLevelsFeatureFlagJsonModel)
BuildLevelIndexesByHashRevision()
SetLoopLevels()
GetLoopNumber(levelIndex)
GetHashLoopNumber(levelIndex, hashWithRevision)
GetModdedLevelIndex(levelIndex)
GetCurrentLevelDifficulty()
GetLevelDifficulty(levelIndex)
GetLevelHashWithRevision(levelIndex)
GetLevelTutorialType(levelIndex)
UpdateNextLevelJsonModelAsync()
TryLoadLevelModelAsync(levelKey)
ConvertJsonStringToLevelJsonModel(jsonString)
TryGetLevelJsonTextAsync(key)
GetMechanicTutorials()
GetInGameBoosterTutorials()
IsBoosterTutorialLevel(levelIndex)
GetInGameBoosterUnlockStates(levelIndex)
UpdateAvailableLevelsAsync()
```

这些方法名直接说明：关卡号先经过 loop 映射，再按 `hash_revision` 查表；难度、教程、循环可用性都以 `levelIndex` 为输入。

### 3.3 下载与本地保存

`LevelDownloaderSystem` 字段（metadata 直接导出）：

```text
SAVE_LEVEL_VERSION, PARALLEL_DOWNLOADS_IOS, PARALLEL_DOWNLOADS_ANDROID,
LogTag, SavedLevelFolderPath
```

方法：

```text
DownloadLevels(), HasDownloadableLevels(), DownloadLevelsAsync(cancellationToken),
DeleteUnexpectedFilesFromLevelsFolder(levelFolderPath, expectedFiles),
DeleteSavedLevel(), HasSavedLevel()
```

metadata 字符串常量：

```text
/Levels
/Levels/
/SavedLevels
```

### 3.4 出题/上传 API

`CheerGameApiClient` 方法：

```text
GetLevelsMetadata(page, pageSize, sort, latestOnly, creatorId, cancellationToken)
GetLevelRevisionMetadata(hash, revision, cancellationToken)
GetLevelLatestRevisionMetadata(hash, cancellationToken)
GetLevelRevisionMetadataContent(hash, revision, cancellationToken)
GetLevelLatestRevisionMetadataContent(hash, cancellationToken)
GetLevelCatalogs(cancellationToken)
GetLevelCatalogEntries(catalogId, status, cancellationToken)
GetExportedCatalogLevels(catalogId, status, cancellationToken)
GetLevelRevisionsMetadata(hash, cancellationToken)
CreateLevelContent(levelContent, cancellationToken)
CreateLevelRevisionContent(hash, levelContent, cancellationToken)
GetTempLevelContent(cancellationToken)
UpdateTempLevelContent(levelContent, cancellationToken)
CreateLevelAttempt(hash, revision, request, cancellationToken)
```

metadata 字符串常量中的路由：

```text
sdk/games/{0}/levels/{1}/revisions/{2}
sdk/games/{0}/levels/{1}/revisions/{2}/content
sdk/games/{0}/levels/{1}/revisions/{2}/attempts
{0}/levels/{1}_{2}
/level-catalogs
/levels
/levels/temp/
/levels_encrypted/
```

`LevelMetadataResponse`：`Hash`、`Revision`、`GameId`、`CreatorId`、`CreatorEmail`、`EditorVersion`、`CreatedAt`。

`CreateLevelTryRequestJsonModel`：`VideoFileName`、`DeviceId`、`LevelHashWithRevision`、`BuildNumber`、`RecordType`。

自定义/临时出题侧模型：

```text
CustomLevelModel: Hash, Revision, LevelJsonModel
RecentlyCreatedLevelModel: Date, Hash, Revision, Creator
CatalogModel: LevelNumber, Hash
LevelPastedEvent: Input
DeepLinkLevelPopupView.TryLoadLevelAsync(hash, revision)
```

---

## 4. 真实题库规模

来自 `output/levels/*.json` 的 249 个关卡/修订统计：

```text
files: 249
width: 2..5
height: 2..6
items: 4..30
clues: 3..20
multi-cell item levels: 132
hide_text levels: 109
levels with at least one revealed item: 205
levels with at least one revealed clue: 249
levels with non-empty cells array: 166
levels with lock_and_key cells: 90
levels with numeric lock-only cells: 88
```

`output/levels/` 里 214 个文件对应 Saga catalog，35 个 `LOCAL_*` 文件是本地旧修订。`output/level-map.json`、`output/assets-index.json`、`output/recovery-verification.json` 保留逐项校验记录。

---

## 5. 未恢复边界

以下内容不伪装为已恢复：

- `UnityFramework` 的 C# 方法体（IL2CPP native code）仍加密，`GriddleItemPlacementSystem`、`LevelDecisionSystem` 等方法内的分支、阈值、顺序不能反汇编。
- `CellData.Lock` 到 `Cell.CurtainCount` 的具体赋值语句未反汇编；当前依据是“字段名唯一对应 + 关卡数据 + `SetCurtain/DecrementCurtain` 方法签名”。
- 提示/橡皮擦/额外线索的具体消耗、解锁阈值和奖励数值在 `EconomyFFJModel`/`AdvertisementSystemFFJModel` 等方法体内，未恢复。

重新生成证据的命令：

```bash
dotnet run --project tools/metadata-dump -- --full \
  device/ipa-extracted/Payload/Griddle.app/Data/Managed/Metadata/global-metadata.dat \
  output/il2cpp-metadata-full.json
```

