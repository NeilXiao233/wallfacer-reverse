const MODES = {
  original: {
    manifest: './data/manifest.json',
    levels: 'levels/',
    storageKey: 'griddle-web-recovery-v1',
  },
  animal: {
    manifest: './animal-data/manifest.json',
    levels: 'animal-data/levels/',
    storageKey: 'griddle-web-recovery-v1-animal',
  },
};
const ANIMAL_AVATAR_DIR = './assets/animal/cast/';
const SPRITE_BASE = '../output/unity-extract/assets/images/sprites/';
const PREFS_KEY = 'griddle-web-preferences-v1';

const UI_TEXT = {
  zh: {
    brandTitle: 'Griddle Web',
    brandSubtitleOriginal: '249 个真实关卡 · 代码证据恢复',
    brandSubtitleAnimal: '动物主题 · 第 1-10 关',
    modeLabel: '切换原版与动物版',
    langLabel: '切换语言',
    select: '选关',
    progressTitle: '已完成关卡',
    sourceLevel: '关卡',
    sourceLocal: '本地修订',
    clueBook: '线索本',
    clues: '线索',
    clueHidden: '线索尚未揭示',
    selectItem: '选择物品',
    chooseItem: '这个位置放什么？',
    noItem: '这个格子没有物品',
    notUnlocked: '这个格子还没有解开',
    rowNoItems: '这一行已经没有可放置的物品',
    wrongItem: '不是这里',
    noHint: '没有可以提示的物品',
    hint: '提示：',
    hintLabel: '使用提示',
    eraserLabel: '使用橡皮擦',
    restartLabel: '重开本关',
    closePanelLabel: '关闭选择面板',
    closeDialogLabel: '关闭选关窗口',
    eraserOn: '橡皮擦模式：选择一条当前线索来自动完成',
    eraserOff: '已退出橡皮擦模式',
    noEraserClue: '当前没有可自动完成的线索',
    eraserSolved: '已自动完成线索',
    extraClueLabel: '揭示下一条线索',
    extraClueRevealed: '已揭示新线索',
    noExtraClue: '当前没有可追加的线索',
    erased: '已完成',
    eraseLabel: '自动完成线索',
    prev: '上一关',
    next: '下一关',
    lastLevel: '已经是最后一关',
    firstLevel: '已经是第一关',
    loadFailed: '关卡加载失败: ',
    levelComplete: '完成！',
    winEyebrow: '关卡完成',
    winText: '这一关的全部格子已经解开。',
    nextLevelIs: '下一关是 ',
    continueQuestion: '，要继续吗？',
    lastOfLibrary: '这是题库里的最后一关。',
    playAgain: '再玩一次',
    dialogEyebrow: '关卡库',
    dialogTitle: '选择关卡',
    searchPlaceholder: '搜索标题或关卡号',
    levelPrefix: '关卡',
    localPrefix: '本地',
    items: '个物品',
    curtainLegend: '数字帘',
    keyLegend: '钥匙',
    lockLegend: '锁',
  },
  en: {
    brandTitle: 'Griddle Web',
    brandSubtitleOriginal: '249 recovered levels',
    brandSubtitleAnimal: 'Animal theme · Levels 1-10',
    modeLabel: 'Switch original / animal',
    langLabel: 'Switch language',
    select: 'Levels',
    progressTitle: 'Completed levels',
    sourceLevel: 'Level',
    sourceLocal: 'Local',
    clueBook: 'Clue Book',
    clues: 'Clues',
    clueHidden: 'Clue not revealed yet',
    selectItem: 'Choose an item',
    chooseItem: 'What goes here?',
    noItem: 'This cell has no item',
    notUnlocked: 'This cell is still locked',
    rowNoItems: 'No more items can be placed in this row',
    wrongItem: 'is not the right fit',
    noHint: 'No item can be hinted',
    hint: 'Hint: ',
    hintLabel: 'Use hint',
    eraserLabel: 'Use eraser',
    restartLabel: 'Restart level',
    closePanelLabel: 'Close selection panel',
    closeDialogLabel: 'Close level picker',
    eraserOn: 'Eraser mode: choose a visible clue to solve it',
    eraserOff: 'Eraser mode off',
    noEraserClue: 'There is no visible clue to solve',
    eraserSolved: 'Clue solved',
    extraClueLabel: 'Reveal the next clue',
    extraClueRevealed: 'New clue revealed',
    noExtraClue: 'There is no extra clue available',
    erased: 'Solved',
    eraseLabel: 'Solve clue',
    prev: 'Previous',
    next: 'Next',
    lastLevel: 'This is the last level',
    firstLevel: 'This is the first level',
    loadFailed: 'Failed to load level: ',
    levelComplete: 'Complete!',
    winEyebrow: 'Level Complete',
    winText: 'Every cell in this level is solved.',
    nextLevelIs: 'Next is ',
    continueQuestion: '. Continue?',
    lastOfLibrary: 'That was the last level in the library.',
    playAgain: 'Play again',
    dialogEyebrow: 'Level Library',
    dialogTitle: 'Choose a level',
    searchPlaceholder: 'Search title or level number',
    levelPrefix: 'Level',
    localPrefix: 'Local',
    items: 'items',
    curtainLegend: 'Curtain',
    keyLegend: 'Key',
    lockLegend: 'Lock',
  },
};

const state = {
  mode: 'original',
  lang: 'zh',
  manifest: [],
  levels: [],
  index: 0,
  level: null,
  data: null,
  cells: new Map(),
  slots: [],
  itemsById: new Map(),
  cluesById: new Map(),
  triggerItemIdsByClueId: new Map(),
  revealedItemIds: new Set(),
  revealedClueIds: new Set(),
  completedClueIds: new Set(),
  justRevealed: new Set(),
  clueDisplay: new Map(),
  pendingPlacements: [],
  panelRow: null,
  panelCol: null,
  eraserMode: false,
  progress: { completed: [], current: null },
};

const $ = (id) => document.getElementById(id);

document.addEventListener('DOMContentLoaded', init);

async function init() {
  loadPreferences();
  bindStaticEvents();
  applyModeUI();
  await loadManifest();
  loadProgress();
  renderProgress();
  renderLevelList();
  const savedIndex = state.levels.findIndex((level) => level.file === state.progress.current);
  await openLevel(savedIndex >= 0 ? savedIndex : 0);
}

async function loadManifest() {
  const config = MODES[state.mode];
  const response = await fetch(config.manifest);
  if (!response.ok) {
    throw new Error(`无法加载关卡清单: ${response.status}`);
  }
  state.manifest = await response.json();
  state.levels = state.manifest.levels;
}

function bindStaticEvents() {
  $('modeToggle').addEventListener('click', toggleMode);
  $('langToggle').addEventListener('click', toggleLanguage);
  $('openLevelsButton').addEventListener('click', () => {
    renderLevelList($('levelSearch').value);
    $('levelDialog').showModal();
    $('levelSearch').focus();
  });
  $('dialogCloseButton').addEventListener('click', () => $('levelDialog').close());
  $('levelSearch').addEventListener('input', (event) => renderLevelList(event.target.value));
  $('panelCloseButton').addEventListener('click', hidePanel);
  document.querySelectorAll('[data-close-panel]').forEach((node) => {
    node.addEventListener('click', hidePanel);
  });
  $('hintButton').addEventListener('click', useHint);
  $('eraserButton').addEventListener('click', toggleEraser);
  $('extraClueButton').addEventListener('click', revealNextUnrevealedClue);
  $('restartButton').addEventListener('click', () => openLevel(state.index));
  $('prevButton').addEventListener('click', () => moveLevel(-1));
  $('nextButton').addEventListener('click', () => moveLevel(1));
  $('winNextButton').addEventListener('click', () => {
    hideWin();
    moveLevel(1);
  });
  $('winAgainButton').addEventListener('click', () => {
    hideWin();
    openLevel(state.index);
  });
  document.querySelectorAll('[data-close-win]').forEach((node) => {
    node.addEventListener('click', hideWin);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      hidePanel();
    }
  });
}

function currentConfig() {
  return MODES[state.mode];
}

function storageKey() {
  return currentConfig().storageKey;
}

function uiText(key) {
  const lang = state.mode === 'animal' ? state.lang : 'zh';
  return UI_TEXT[lang][key] || UI_TEXT.zh[key] || key;
}

function localize(value) {
  const lang = state.mode === 'animal' ? state.lang : 'zh';
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value[lang] || value.zh || value.en || '';
  }
  return value == null ? '' : String(value);
}

function clueText(clue) {
  if (state.mode === 'animal') {
    return state.lang === 'en' ? clue.content_en : clue.content_zh;
  }
  return clue.content || '';
}

function levelTitle(level) {
  return localize(level.posterTitle);
}

function loadPreferences() {
  try {
    const saved = JSON.parse(localStorage.getItem(PREFS_KEY));
    if (saved) {
      if (saved.mode === 'original' || saved.mode === 'animal') {
        state.mode = saved.mode;
      }
      if (saved.lang === 'zh' || saved.lang === 'en') {
        state.lang = saved.lang;
      }
    }
  } catch (error) {
    state.mode = 'original';
    state.lang = 'zh';
  }
}

function savePreferences() {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify({ mode: state.mode, lang: state.lang }));
  } catch (error) {
    // Preferences are optional; the game still works without storage.
  }
}

function applyModeUI() {
  const isAnimal = state.mode === 'animal';
  document.body.classList.toggle('animal-theme', isAnimal);
  document.documentElement.lang = isAnimal && state.lang === 'en' ? 'en' : 'zh-CN';
  $('langToggle').hidden = !isAnimal;
  $('langToggle').textContent = state.lang === 'zh' ? '中 / EN' : 'EN / 中';
  $('langToggle').setAttribute('aria-label', uiText('langLabel'));
  $('langToggle').setAttribute('aria-pressed', String(state.lang === 'en'));
  $('modeToggle').setAttribute('aria-label', uiText('modeLabel'));
  $('modeToggle').title = uiText('modeLabel');
  $('extraClueButton').setAttribute('aria-label', uiText('extraClueLabel'));
  $('extraClueButton').title = uiText('extraClueLabel');
  applyStaticI18n();
}

function applyStaticI18n() {
  const subtitleKey = state.mode === 'animal' ? 'brandSubtitleAnimal' : 'brandSubtitleOriginal';
  $('brandTitle').textContent = uiText('brandTitle');
  $('brandSubtitle').textContent = uiText(subtitleKey);
  $('openLevelsLabel').textContent = uiText('select');
  $('openLevelsButton').setAttribute('aria-label', uiText('select'));
  $('cluesEyebrow').textContent = uiText('clueBook');
  $('cluesTitle').textContent = uiText('clues');
  $('panelEyebrow').textContent = uiText('selectItem');
  $('panelTitle').textContent = uiText('chooseItem');
  $('dialogEyebrow').textContent = uiText('dialogEyebrow');
  $('dialogTitle').textContent = uiText('dialogTitle');
  $('levelSearch').placeholder = uiText('searchPlaceholder');
  $('winEyebrow').textContent = uiText('winEyebrow');
  $('winTitle').textContent = uiText('levelComplete');
  $('winNextButton').textContent = uiText('next');
  $('winAgainButton').textContent = uiText('playAgain');
  $('prevButton').textContent = uiText('prev');
  $('nextButton').textContent = uiText('next');
  document.querySelector('.progress-chip')?.setAttribute('title', uiText('progressTitle'));
  document.querySelectorAll('[data-i18n]').forEach((node) => {
    node.textContent = uiText(node.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-aria]').forEach((node) => {
    node.setAttribute('aria-label', uiText(node.dataset.i18nAria));
  });
}

function toggleMode() {
  switchMode(state.mode === 'animal' ? 'original' : 'animal');
}

async function switchMode(nextMode) {
  if (state.mode === nextMode) return;
  state.mode = nextMode;
  savePreferences();
  applyModeUI();
  await loadManifest();
  loadProgress();
  renderProgress();
  renderLevelList();
  const savedIndex = state.levels.findIndex((level) => level.file === state.progress.current);
  const currentIndex = state.level
    ? state.levels.findIndex((level) => level.file === state.level.file)
    : -1;
  const target = savedIndex >= 0 ? savedIndex : currentIndex >= 0 ? currentIndex : 0;
  await openLevel(target);
}

function toggleLanguage() {
  state.lang = state.lang === 'en' ? 'zh' : 'en';
  savePreferences();
  hidePanel();
  applyModeUI();
  renderHeader();
  renderBoard();
  renderClues();
  renderLevelList();
  updateSlotStat();
  document.title = `Griddle Web - ${levelTitle(state.level)}`;
}

function loadProgress() {
  state.progress = { completed: [], current: null };
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey()));
    if (saved && Array.isArray(saved.completed)) {
      state.progress = saved;
    }
  } catch (error) {
    state.progress = { completed: [], current: null };
  }
}

function saveProgress() {
  try {
    localStorage.setItem(storageKey(), JSON.stringify(state.progress));
  } catch (error) {
    // Storage can be unavailable in private contexts; the game still works.
  }
}

function renderProgress() {
  const completed = new Set(state.progress.completed);
  $('progressCount').textContent = `${completed.size} / ${state.levels.length}`;
  $('progressFill').style.width = `${(completed.size / state.levels.length) * 100}%`;
}

function levelLabel(level) {
  if (level.catalogLevel != null) {
    return String(level.catalogLevel).padStart(3, '0');
  }
  const localIndex = state.levels
    .filter((item) => item.catalogLevel == null)
    .findIndex((item) => item.file === level.file);
  return `L${String(localIndex + 1).padStart(2, '0')}`;
}

function cellKey(row, col) {
  return `${row}:${col}`;
}

function cellAt(row, col) {
  return state.cells.get(cellKey(row, col));
}

function isCellBlocked(cell) {
  if (!cell) return true;
  if (cell.curtainCount > 0) return true;
  return Boolean(cell.lockAndKey && cell.lockAndKey.type === 'lock' && !cell.unlocked);
}

async function openLevel(index) {
  if (index < 0 || index >= state.levels.length) return;
  cancelScheduledUpdates();
  state.index = index;
  state.level = state.levels[index];
  state.progress.current = state.level.file;
  saveProgress();

  const response = await fetch(currentConfig().levels + state.level.file);
  if (!response.ok) {
    showToast(`${uiText('loadFailed')}${response.status}`, true);
    return;
  }
  state.data = await response.json();
  resetLevel(state.data);
  renderHeader();
  renderBoard();
  renderClues();
  updateSlotStat();
  renderProgress();
  hidePanel();
  hideWin();
  $('levelDialog').close();
  document.title = `Griddle Web - ${levelTitle(state.level)}`;
}

function renderHeader() {
  const level = state.level;
  const sourceLabel = level.catalogLevel != null ? uiText('sourceLevel') : uiText('sourceLocal');
  $('levelEyebrow').textContent = `${sourceLabel} ${levelLabel(level)} / ${state.levels.length}`;
  $('levelTitle').textContent = levelTitle(level);
}

function resetLevel(data) {
  state.cells = new Map();
  state.slots = [];
  state.itemsById = new Map(data.items.map((item) => [item.id, item]));
  state.cluesById = new Map(data.clues.map((clue) => [clue.id, clue]));
  state.triggerItemIdsByClueId = new Map(data.clues.map((clue) => [clue.id, []]));
  state.revealedItemIds = new Set();
  state.revealedClueIds = new Set();
  state.completedClueIds = new Set();
  state.justRevealed = new Set();
  state.clueDisplay = new Map();
  state.pendingPlacements = [];
  state.eraserMode = false;
  $('eraserButton').setAttribute('aria-pressed', 'false');
  $('clues').replaceChildren();

  for (const item of data.items) {
    for (const clueId of item.connected_to || []) {
      const triggerItemIds = state.triggerItemIdsByClueId.get(clueId);
      if (triggerItemIds && !triggerItemIds.includes(item.id)) {
        triggerItemIds.push(item.id);
      }
    }
  }

  for (const item of data.items) {
    for (const cellData of item.cells || []) {
      const key = cellKey(cellData.row, cellData.column);
      let cell = state.cells.get(key);
      if (!cell) {
        cell = {
          row: cellData.row,
          col: cellData.column,
          curtainCount: 0,
          lockAndKey: null,
          unlocked: false,
          slots: [],
        };
        state.cells.set(key, cell);
      }
      const slot = {
        id: `slot-${state.slots.length + 1}`,
        itemId: item.id,
        row: cellData.row,
        col: cellData.column,
        revealed: false,
      };
      cell.slots.push(slot);
      state.slots.push(slot);
    }
  }

  for (const cellData of data.cells || []) {
    const key = cellKey(cellData.row, cellData.column);
    let cell = state.cells.get(key);
    if (!cell) {
      cell = {
        row: cellData.row,
        col: cellData.column,
        curtainCount: 0,
        lockAndKey: null,
        unlocked: false,
        slots: [],
      };
      state.cells.set(key, cell);
    }
    cell.curtainCount = typeof cellData.lock === 'number' ? cellData.lock : 0;
    cell.lockAndKey = cellData.lock_and_key || null;
  }

  for (const clue of data.clues) {
    if (clue.revealed) {
      state.revealedClueIds.add(clue.id);
    }
  }

  for (const item of data.items) {
    if (item.revealed) {
      revealItem(item.id, true);
    }
  }

  processPendingPlacements();
  refreshClueStates();
}

function revealItem(itemId, isInitial = false) {
  let revealedCount = 0;
  const unlockedColors = new Set();
  for (const slot of state.slots) {
    if (slot.itemId !== itemId || slot.revealed) continue;
    const cell = cellAt(slot.row, slot.col);
    if (isCellBlocked(cell)) {
      if (!state.pendingPlacements.includes(slot.id)) {
        state.pendingPlacements.push(slot.id);
      }
      continue;
    }
    slot.revealed = true;
    state.revealedItemIds.add(itemId);
    if (!isInitial) {
      state.justRevealed.add(slot.id);
    }
    revealedCount += 1;
    if (cell.lockAndKey && cell.lockAndKey.type === 'key') {
      unlockedColors.add(cell.lockAndKey.color);
    }
  }
  for (const color of unlockedColors) unlockLocks(color);
  revealedCount += processPendingPlacements();
  return revealedCount;
}

function unlockLocks(color) {
  let changed = false;
  for (const cell of state.cells.values()) {
    if (
      cell.lockAndKey &&
      cell.lockAndKey.type === 'lock' &&
      cell.lockAndKey.color === color &&
      !cell.unlocked
    ) {
      cell.unlocked = true;
      changed = true;
    }
  }
  return changed;
}

function processPendingPlacements() {
  let changed = true;
  let revealedCount = 0;
  while (changed) {
    changed = false;
    const remaining = [];
    const unlockedColors = new Set();
    for (const slotId of state.pendingPlacements) {
      const slot = state.slots.find((candidate) => candidate.id === slotId);
      if (!slot) continue;
      const cell = cellAt(slot.row, slot.col);
      if (!isCellBlocked(cell)) {
        slot.revealed = true;
        state.revealedItemIds.add(slot.itemId);
        state.justRevealed.add(slot.id);
        if (cell.lockAndKey && cell.lockAndKey.type === 'key') {
          unlockedColors.add(cell.lockAndKey.color);
        }
        revealedCount += 1;
        changed = true;
      } else {
        remaining.push(slotId);
      }
    }
    state.pendingPlacements = remaining;
    for (const color of unlockedColors) {
      if (unlockLocks(color)) changed = true;
    }
  }
  return revealedCount;
}

function decrementCurtains(amount = 1) {
  let revealWave = amount;
  while (revealWave > 0) {
    for (const cell of state.cells.values()) {
      if (cell.curtainCount > 0) {
        cell.curtainCount = Math.max(0, cell.curtainCount - revealWave);
      }
    }
    revealWave = processPendingPlacements();
  }
}

function refreshClueStates() {
  for (const clue of state.data.clues) {
    const triggerItemIds = state.triggerItemIdsByClueId.get(clue.id) || [];
    if (
      !state.revealedClueIds.has(clue.id) &&
      triggerItemIds.length > 0 &&
      areAllItemsRevealed(triggerItemIds)
    ) {
      state.revealedClueIds.add(clue.id);
    }
    const connectedItemIds = clue.connected_to || [];
    if (
      state.revealedClueIds.has(clue.id) &&
      connectedItemIds.length > 0 &&
      areAllItemsRevealed(connectedItemIds)
    ) {
      state.completedClueIds.add(clue.id);
    } else {
      state.completedClueIds.delete(clue.id);
    }
  }
}

function areAllItemsRevealed(itemIds) {
  return itemIds.every((itemId) => {
    const itemSlots = state.slots.filter((slot) => slot.itemId === itemId);
    return itemSlots.length > 0 && itemSlots.every((slot) => slot.revealed);
  });
}

function updateSlotStat() {
  const total = state.slots.length;
  const revealed = state.slots.filter((slot) => slot.revealed).length;
  $('slotStat').textContent = `${revealed} / ${total}`;
}

function renderBoard() {
  const grid = $('board');
  const data = state.data;
  grid.replaceChildren();
  grid.style.setProperty('--cols', data.grid.width);
  grid.dataset.cols = String(data.grid.width);
  grid.dataset.rows = String(data.grid.height);

  const corner = document.createElement('div');
  corner.className = 'board-head';
  corner.setAttribute('aria-hidden', 'true');
  grid.appendChild(corner);

  for (let col = 1; col <= data.grid.width; col += 1) {
    grid.appendChild(renderColumnHeader(col));
  }

  for (let row = 1; row <= data.grid.height; row += 1) {
    const rowHead = document.createElement('div');
    rowHead.className = 'row-head';
    rowHead.textContent = localize(data.grid.row_names[row - 1]) || `Row ${row}`;
    grid.appendChild(rowHead);

    for (let col = 1; col <= data.grid.width; col += 1) {
      grid.appendChild(renderCell(row, col));
    }
  }
  state.justRevealed.clear();
}

function renderColumnHeader(col) {
  const data = state.data;
  const header = data.grid.columns[col - 1] || {};
  const name = localize(header.name);
  const element = document.createElement('div');
  element.className = 'column-head';
  if (state.mode === 'animal' && typeof header.animal_index === 'number') {
    element.classList.add('animal');
    const avatar = document.createElement('img');
    avatar.className = 'animal-avatar';
    avatar.src = `${ANIMAL_AVATAR_DIR}avatar-${String(header.animal_index).padStart(2, '0')}.webp`;
    avatar.alt = '';
    avatar.title = name;
    avatar.width = 192;
    avatar.height = 192;
    element.appendChild(avatar);
  } else {
    const imageUrl = spriteUrl(header.image_cgasset_id);
    if (imageUrl) {
      const img = document.createElement('img');
      img.src = imageUrl;
      img.alt = '';
      img.title = name;
      img.loading = 'lazy';
      element.appendChild(img);
    }
  }
  if (name) {
    const label = document.createElement('span');
    label.className = 'column-name';
    label.textContent = name;
    element.appendChild(label);
  }
  return element;
}

function createItemVisual(item, alt = '') {
  if (state.mode === 'animal' && item.animal_asset) {
    const asset = item.animal_asset;
    const columns = Math.max(1, asset.columns || 1);
    const rows = Math.max(1, asset.rows || 1);
    const index = Math.max(0, asset.index || 0);
    const row = Math.floor(index / columns);
    const col = index % columns;
    const visual = document.createElement('span');
    visual.className = 'animal-item-visual';
    visual.style.backgroundImage = `url('${asset.sheet}')`;
    visual.style.backgroundSize = `${columns * 100}% ${rows * 100}%`;
    visual.style.backgroundPosition = `${columns === 1 ? 0 : (col / (columns - 1)) * 100}% ${rows === 1 ? 0 : (row / (rows - 1)) * 100}%`;
    if (alt) {
      visual.setAttribute('role', 'img');
      visual.setAttribute('aria-label', alt);
    } else {
      visual.setAttribute('aria-hidden', 'true');
    }
    return visual;
  }

  const imageUrl = spriteUrl(item.image_cgasset_id);
  if (!imageUrl) return null;
  const image = document.createElement('img');
  image.src = imageUrl;
  image.alt = alt;
  image.loading = 'lazy';
  return image;
}

function renderCell(row, col) {
  const cell = cellAt(row, col);
  const element = document.createElement('div');
  element.className = 'cell';
  element.dataset.row = String(row);
  element.dataset.col = String(col);
  element.setAttribute('role', 'button');
  element.tabIndex = 0;
  element.setAttribute(
    'aria-label',
    `${localize(state.data.grid.row_names[row - 1])} / ${localize(state.data.grid.columns[col - 1].name)}`
  );

  if (cell) {
    if (cell.curtainCount > 0) {
      element.classList.add('curtained');
      const overlay = document.createElement('div');
      overlay.className = 'curtain-overlay';
      overlay.textContent = String(cell.curtainCount);
      element.appendChild(overlay);
    }
    if (cell.lockAndKey && cell.lockAndKey.type === 'lock' && !cell.unlocked) {
      element.classList.add('locked');
      const overlay = document.createElement('div');
      overlay.className = 'lock-overlay';
      const icon = document.createElement('span');
      icon.textContent = 'lock';
      const color = document.createElement('span');
      color.textContent = cell.lockAndKey.color;
      overlay.append(icon, color);
      element.appendChild(overlay);
    }
    if (cell.lockAndKey && cell.lockAndKey.type === 'key') {
      element.classList.add('key-cell');
      const badge = document.createElement('div');
      badge.className = 'key-badge';
      const icon = document.createElement('span');
      icon.textContent = 'key';
      const color = document.createElement('span');
      color.textContent = cell.lockAndKey.color;
      badge.append(icon, color);
      element.appendChild(badge);
    }

    for (const slot of cell.slots) {
      element.appendChild(renderSlot(slot, cell));
    }
  }

  if (
    !cell ||
    cell.slots.length === 0 ||
    cell.slots.every((slot) => slot.revealed) ||
    isCellBlocked(cell)
  ) {
    element.setAttribute('aria-disabled', 'true');
    element.tabIndex = -1;
  }

  element.addEventListener('click', () => onCellClick(row, col));
  element.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onCellClick(row, col);
    }
  });
  return element;
}

function renderSlot(slot, cell) {
  const item = state.itemsById.get(slot.itemId);
  const itemName = localize(item.name);
  const element = document.createElement('div');
  element.className = 'slot';
  element.dataset.slotId = slot.id;

  if (slot.revealed) {
    element.classList.add('revealed');
    if (state.justRevealed.has(slot.id)) {
      element.classList.add('just-revealed');
    }
    const visual = createItemVisual(item, itemName);
    if (visual) element.appendChild(visual);
    if (!visual) {
      element.append(document.createTextNode(itemName));
    }
  } else {
    element.classList.add('empty');
    element.setAttribute('aria-label', uiText('chooseItem'));
  }
  return element;
}

function spriteUrl(cgAssetId) {
  if (!cgAssetId || !state.level.sprites[cgAssetId]) return '';
  return SPRITE_BASE + state.level.sprites[cgAssetId];
}

function onCellClick(row, col) {
  const cell = cellAt(row, col);
  if (!cell || cell.slots.length === 0) {
    showToast(uiText('noItem'), true);
    return;
  }
  if (isCellBlocked(cell)) {
    showToast(uiText('notUnlocked'), true);
    return;
  }
  openSelection(row, col);
}

function openSelection(row, col) {
  const options = getUnrevealedItemsInRow(row);
  if (options.length === 0) {
    showToast(uiText('rowNoItems'));
    return;
  }
  state.panelRow = row;
  state.panelCol = col;

  const rowName = localize(state.data.grid.row_names[row - 1]);
  const colName = localize(state.data.grid.columns[col - 1].name);
  $('panelEyebrow').textContent = `${rowName} / ${colName}`;
  $('panelTitle').textContent = uiText('chooseItem');
  renderPanelOptions(options);
  $('selectionPanel').hidden = false;
}

function getUnrevealedItemsInRow(row) {
  const itemIds = new Set();
  for (const slot of state.slots) {
    if (slot.row !== row || slot.revealed) continue;
    const cell = cellAt(slot.row, slot.col);
    if (!isCellBlocked(cell)) {
      itemIds.add(slot.itemId);
    }
  }
  return Array.from(itemIds);
}

function renderPanelOptions(itemIds) {
  const container = $('panelOptions');
  container.replaceChildren();
  for (const itemId of itemIds) {
    const item = state.itemsById.get(itemId);
    const button = document.createElement('button');
    button.className = 'option-button';
    button.type = 'button';
    const visual = createItemVisual(item);
    if (visual) button.appendChild(visual);
    button.append(document.createTextNode(localize(item.name)));
    button.setAttribute('aria-label', `${uiText('selectItem')} ${localize(item.name)}`);
    button.addEventListener('click', () => placeItem(itemId));
    container.appendChild(button);
  }
}

function placeItem(itemId) {
  const row = state.panelRow;
  const col = state.panelCol;
  const cell = cellAt(row, col);
  const isCorrect = state.slots.some(
    (slot) =>
      slot.itemId === itemId &&
      !slot.revealed &&
      slot.row === row &&
      slot.col === col &&
      !isCellBlocked(cell)
  );

  if (!isCorrect) {
    flashWrong(row, col);
    const item = state.itemsById.get(itemId);
    showToast(`${item ? localize(item.name) : ''}${uiText('wrongItem')}`, true);
    return;
  }

  state.justRevealed = new Set();
  const revealedCount = revealItem(itemId);
  decrementCurtains(revealedCount);
  refreshClueStates();
  renderBoard();
  updateSlotStat();
  hidePanel();
  scheduleClueUpdate(() => {
    renderClues();
    scheduleWinCheck();
  });
}

function useHint() {
  const candidates = findHintCandidates(true);
  if (candidates.length === 0) candidates.push(...findHintCandidates(false));
  if (candidates.length === 0) {
    showToast(uiText('noHint'));
    return;
  }
  const itemId = candidates[0];
  state.justRevealed = new Set();
  const revealedCount = revealItem(itemId);
  decrementCurtains(revealedCount);
  refreshClueStates();
  renderBoard();
  updateSlotStat();
  showToast(`${uiText('hint')}${localize(state.itemsById.get(itemId).name)}`);
  scheduleClueUpdate(() => {
    renderClues();
    scheduleWinCheck();
  });
}

function findHintCandidates(excludeKeyCells) {
  const candidates = [];
  const activeClues = getActiveClues();
  const preferredItemIds = activeClues.flatMap((clue) => clue.connected_to || []);
  const fallbackItemIds = state.data.items.map((item) => item.id);

  for (const itemId of [...preferredItemIds, ...fallbackItemIds]) {
    if (candidates.includes(itemId) || areAllItemsRevealed([itemId])) continue;
    const canReveal = state.slots.some((slot) => {
      if (slot.itemId !== itemId || slot.revealed) return false;
      const cell = cellAt(slot.row, slot.col);
      if (isCellBlocked(cell)) return false;
      return !excludeKeyCells || !cell.lockAndKey || cell.lockAndKey.type !== 'key';
    });
    if (canReveal) candidates.push(itemId);
  }
  return candidates;
}

function getActiveClues() {
  return state.data.clues.filter(
    (clue) => state.revealedClueIds.has(clue.id) && !state.completedClueIds.has(clue.id)
  );
}

function toggleEraser() {
  const selectableClues = getActiveClues().filter(
    (clue) =>
      (clue.connected_to || []).some((itemId) => !areAllItemsRevealed([itemId]))
  );
  if (!state.eraserMode && selectableClues.length === 0) {
    showToast(uiText('noEraserClue'));
    return;
  }
  state.eraserMode = !state.eraserMode;
  $('eraserButton').setAttribute('aria-pressed', String(state.eraserMode));
  renderClues();
  showToast(state.eraserMode ? uiText('eraserOn') : uiText('eraserOff'));
}

function revealNextUnrevealedClue() {
  const hiddenClue = state.data.clues.find((clue) => !state.revealedClueIds.has(clue.id));
  if (!hiddenClue || getActiveClues().length > 0) {
    showToast(uiText('noExtraClue'));
    return;
  }
  state.revealedClueIds.add(hiddenClue.id);
  refreshClueStates();
  renderClues();
  showToast(uiText('extraClueRevealed'));
}

function completeClueWithEraser(clueId) {
  const clue = state.cluesById.get(clueId);
  if (
    !clue ||
    !state.eraserMode ||
    !state.revealedClueIds.has(clueId) ||
    state.completedClueIds.has(clueId)
  ) {
    return;
  }

  state.eraserMode = false;
  $('eraserButton').setAttribute('aria-pressed', 'false');
  state.justRevealed = new Set();
  for (const itemId of clue.connected_to || []) {
    if (areAllItemsRevealed([itemId])) continue;
    const revealedCount = revealItem(itemId);
    decrementCurtains(revealedCount);
  }
  refreshClueStates();
  renderBoard();
  updateSlotStat();
  showToast(uiText('eraserSolved'));
  scheduleClueUpdate(() => {
    renderClues();
    scheduleWinCheck();
  });
}

function renderClues() {
  const container = $('clues');
  const existing = new Map();
  for (const child of container.children) {
    if (child.dataset.clueId) existing.set(child.dataset.clueId, child);
  }

  for (const clue of state.data.clues) {
    const id = clue.id;
    const isRevealed = state.revealedClueIds.has(id);
    const isCompleted = state.completedClueIds.has(id);
    const next = isCompleted ? 'completed' : isRevealed ? 'revealed' : 'hidden';
    const prev = state.clueDisplay.get(id);

    let element = existing.get(id);
    if (!element) {
      element = document.createElement('div');
      element.className = 'clue';
      element.dataset.clueId = id;
      container.appendChild(element);
    }

    const text = document.createElement('span');
    text.className = 'clue-text';
    if (isRevealed) {
      text.innerHTML = renderClueText(clueText(clue));
    } else {
      text.textContent = uiText('clueHidden');
    }
    element.replaceChildren(text);

    element.classList.remove('entering', 'leaving', 'retired');
    element.classList.toggle('hidden', next === 'hidden');
    element.hidden = false;
    const canUseEraser =
      state.eraserMode &&
      isRevealed &&
      !isCompleted &&
      (clue.connected_to || []).some((itemId) => !areAllItemsRevealed([itemId]));
    element.classList.toggle('eraser-target', canUseEraser);
    if (canUseEraser) {
      element.setAttribute('role', 'button');
      element.tabIndex = 0;
      element.setAttribute('aria-label', `${uiText('eraseLabel')}: ${clueText(clue)}`);
      element.onclick = () => completeClueWithEraser(id);
      element.onkeydown = (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          completeClueWithEraser(id);
        }
      };
    } else {
      element.removeAttribute('role');
      element.removeAttribute('aria-label');
      element.tabIndex = -1;
      element.onclick = null;
      element.onkeydown = null;
    }

    if (next === 'hidden') {
      state.clueDisplay.set(id, 'hidden');
      continue;
    }

    if (next === 'revealed') {
      if (prev != null && prev !== 'revealed' && prev !== 'entering-completed') {
        element.classList.add('entering');
      }
      state.clueDisplay.set(id, 'revealed');
      continue;
    }

    if (prev == null || prev === 'retired' || prev === 'completed') {
      element.hidden = true;
      element.classList.add('retired');
      state.clueDisplay.set(id, 'retired');
      continue;
    }

    if (prev === 'leaving') {
      element.classList.add('completed', 'leaving');
      state.clueDisplay.set(id, 'leaving');
      continue;
    }

    if (prev === 'entering-completed') {
      element.classList.add('entering');
      state.clueDisplay.set(id, 'entering-completed');
      continue;
    }

    if (prev === 'hidden') {
      element.classList.add('entering');
      state.clueDisplay.set(id, 'entering-completed');
      const node = element;
      window.setTimeout(() => {
        if (state.clueDisplay.get(id) !== 'entering-completed') return;
        state.clueDisplay.set(id, 'leaving');
        node.classList.remove('entering');
        node.classList.add('completed', 'leaving');
        window.setTimeout(() => retireClue(node, id), 680);
      }, 900);
      continue;
    }

    element.classList.add('completed', 'leaving');
    state.clueDisplay.set(id, 'leaving');
    const node = element;
    window.setTimeout(() => retireClue(node, id), 680);
  }
  const total = state.data.clues.length;
  const completed = state.completedClueIds.size;
  $('clueCount').textContent = `${completed} / ${total}`;
  const hasHiddenClues = state.data.clues.some((clue) => !state.revealedClueIds.has(clue.id));
  $('extraClueButton').hidden = !hasHiddenClues || getActiveClues().length > 0;
}

function retireClue(node, id) {
  if (state.clueDisplay.get(id) !== 'leaving') return;
  state.clueDisplay.set(id, 'retired');
  node.classList.remove('leaving', 'completed');
  node.classList.add('retired');
  node.hidden = true;
}

function renderClueText(content) {
  const escaped = String(content)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\{([^}]+)\}/g, (_, name) => `<span class="mention mention-col">${escapeHtml(name)}</span>`)
    .replace(/\[([^\]]+)\]/g, (_, name) => `<span class="mention mention-item">${escapeHtml(name)}</span>`)
    .replace(/&lt;b&gt;/g, '<b>')
    .replace(/&lt;\/b&gt;/g, '</b>')
    .replace(/&lt;u&gt;/g, '<u>')
    .replace(/&lt;\/u&gt;/g, '</u>');
  return escaped;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function checkWin() {
  const allRevealed = state.slots.every((slot) => slot.revealed);
  if (!allRevealed) return;
  const key = state.level.file;
  if (!state.progress.completed.includes(key)) {
    state.progress.completed.push(key);
    saveProgress();
    renderProgress();
  }
  const next = state.levels[state.index + 1];
  $('winText').textContent = next
    ? `${uiText('nextLevelIs')}${levelTitle(next)}${uiText('continueQuestion')}`
    : uiText('lastOfLibrary');
  $('winModal').hidden = false;
}

function hidePanel() {
  $('selectionPanel').hidden = true;
  state.panelRow = null;
  state.panelCol = null;
  document.querySelectorAll('.cell.candidate').forEach((node) => node.classList.remove('candidate'));
}

function hideWin() {
  $('winModal').hidden = true;
}

function flashWrong(row, col) {
  const element = document.querySelector(`.cell[data-row="${row}"][data-col="${col}"]`);
  if (!element) return;
  element.classList.remove('wrong');
  void element.offsetWidth;
  element.classList.add('wrong');
  window.setTimeout(() => element.classList.remove('wrong'), 360);
}

function moveLevel(delta) {
  const next = state.index + delta;
  if (next >= 0 && next < state.levels.length) {
    openLevel(next);
  } else {
    showToast(delta > 0 ? uiText('lastLevel') : uiText('firstLevel'));
  }
}

function renderLevelList(filter = '') {
  const container = $('levelList');
  container.replaceChildren();
  const query = filter.trim().toLowerCase();
  const completed = new Set(state.progress.completed);
  const current = state.level ? state.level.file : null;

  state.levels.forEach((level, index) => {
    const title = levelTitle(level).toLowerCase();
    const label = levelLabel(level);
    const haystack = `${title} ${label} ${level.key}`.toLowerCase();
    if (query && !haystack.includes(query)) return;

    const button = document.createElement('button');
    button.className = 'level-card';
    button.type = 'button';
    if (completed.has(level.file)) button.classList.add('done');
    if (current === level.file) button.classList.add('current');

    const number = document.createElement('span');
    number.className = 'level-card-number';
    number.textContent = level.catalogLevel != null
      ? `${uiText('levelPrefix')} ${label}`
      : `${uiText('localPrefix')} ${label}`;

    const titleNode = document.createElement('span');
    titleNode.className = 'level-card-title';
    titleNode.textContent = levelTitle(level) || level.key;

    const meta = document.createElement('span');
    meta.className = 'level-card-meta';
    const badges = [];
    if (level.width && level.height) badges.push(`${level.width} x ${level.height}`);
    badges.push(`${level.itemCount} ${uiText('items')}`);
    if (level.hasCurtain) badges.push(uiText('curtainLegend'));
    if (level.hasLockKey) badges.push(`${uiText('keyLegend')}/${uiText('lockLegend')}`);
    meta.textContent = badges.join(' · ');

    button.append(number, titleNode, meta);
    button.addEventListener('click', () => {
      openLevel(index);
    });
    container.appendChild(button);
  });
}

let toastTimer = null;
let clueUpdateTimer = null;
let winCheckTimer = null;

function cancelScheduledUpdates() {
  if (clueUpdateTimer) {
    window.clearTimeout(clueUpdateTimer);
    clueUpdateTimer = null;
  }
  if (winCheckTimer) {
    window.clearTimeout(winCheckTimer);
    winCheckTimer = null;
  }
}

function scheduleClueUpdate(callback) {
  if (clueUpdateTimer) window.clearTimeout(clueUpdateTimer);
  clueUpdateTimer = window.setTimeout(() => {
    clueUpdateTimer = null;
    callback();
  }, 430);
}

function scheduleWinCheck() {
  if (winCheckTimer) window.clearTimeout(winCheckTimer);
  winCheckTimer = window.setTimeout(() => {
    winCheckTimer = null;
    checkWin();
  }, 2000);
}

function showToast(message, isError = false) {
  const toast = $('toast');
  toast.textContent = message;
  toast.classList.toggle('error', isError);
  toast.classList.add('show');
  if (toastTimer) window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove('show'), 2400);
}
