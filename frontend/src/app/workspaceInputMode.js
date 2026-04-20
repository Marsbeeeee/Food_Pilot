/** @typedef {import('../types/types').WorkspaceInputMode} WorkspaceInputMode */

/** @type {WorkspaceInputMode} */
export const DEFAULT_WORKSPACE_INPUT_MODE = 'chat';
export const WORKSPACE_INPUT_MODE_STORAGE_KEY = 'foodpilot.workspace.inputMode';

const WORKSPACE_INPUT_MODE_CONFIG = {
  chat: {
    value: 'chat',
    label: '普通对话',
    shortLabel: '对话',
    menuIcon: 'chat_bubble',
    placeholder: '问营养、问推荐，或直接描述你吃了什么',
    description: '适合营养问答、吃什么推荐和自由追问。',
  },
  decision: {
    value: 'decision',
    label: '点单决策',
    shortLabel: '点单',
    menuIcon: 'local_mall',
    placeholder: '粘贴商品标题、套餐描述，或输入品牌 + 商品名',
    description: '适合商品标题、套餐描述和品牌 + 商品名。',
  },
};

export const WORKSPACE_INPUT_MODE_OPTIONS = [
  {
    ...WORKSPACE_INPUT_MODE_CONFIG.decision,
    description: WORKSPACE_INPUT_MODE_CONFIG.decision.description,
  },
];

const DECISION_PROMOTION_ONLY_PHRASES = [
  '限时优惠',
  '限时特惠',
  '今日特价',
  '买一送一',
  '第二杯半价',
  '第二份半价',
  '满减',
  '立减',
  '折扣',
  '优惠',
  '特价',
  '爆款',
  '热销',
];

const DECISION_PRODUCT_HINTS = [
  '套餐',
  '汉堡',
  '鸡腿堡',
  '牛堡',
  '薯条',
  '可乐',
  '奶茶',
  '果茶',
  '咖啡',
  '拿铁',
  '美式',
  '奶昔',
  '冰淇淋',
  '伯牙绝弦',
  '生椰',
  '大杯',
  '中杯',
  '小杯',
  '三分糖',
  '五分糖',
  '七分糖',
  '无糖',
  '少冰',
  '去冰',
  '热',
  '冰',
  '一份',
  '一个',
  '一杯',
  '两杯',
];

/**
 * @param {unknown} value
 * @returns {value is WorkspaceInputMode}
 */
export function isWorkspaceInputMode(value) {
  return value === 'chat' || value === 'decision';
}

/**
 * @param {unknown} mode
 */
export function getWorkspaceInputModeConfig(mode) {
  if (isWorkspaceInputMode(mode)) {
    return WORKSPACE_INPUT_MODE_CONFIG[mode];
  }

  return WORKSPACE_INPUT_MODE_CONFIG[DEFAULT_WORKSPACE_INPUT_MODE];
}

/**
 * @param {Storage | null | undefined} [storage]
 * @returns {WorkspaceInputMode}
 */
export function getStoredWorkspaceInputMode(storage = getDefaultStorage()) {
  if (!storage || typeof storage.getItem !== 'function') {
    return DEFAULT_WORKSPACE_INPUT_MODE;
  }

  const storedMode = storage.getItem(WORKSPACE_INPUT_MODE_STORAGE_KEY);
  return isWorkspaceInputMode(storedMode) ? storedMode : DEFAULT_WORKSPACE_INPUT_MODE;
}

/**
 * @param {unknown} mode
 * @param {Storage | null | undefined} [storage]
 */
export function persistWorkspaceInputMode(mode, storage = getDefaultStorage()) {
  if (!storage || typeof storage.setItem !== 'function' || !isWorkspaceInputMode(mode)) {
    return;
  }

  storage.setItem(WORKSPACE_INPUT_MODE_STORAGE_KEY, mode);
}

/**
 * @param {string} content
 * @param {number | undefined} profileId
 * @param {unknown} [mode]
 */
export function buildWorkspaceMessageRequest(content, profileId, mode = DEFAULT_WORKSPACE_INPUT_MODE) {
  const payload = {
    content,
    mode: isWorkspaceInputMode(mode) ? mode : DEFAULT_WORKSPACE_INPUT_MODE,
  };

  if (typeof profileId === 'number') {
    payload.profileId = profileId;
  }

  return payload;
}

/**
 * @param {unknown} mode
 * @param {unknown} rawValue
 * @returns {string}
 */
export function validateWorkspaceInput(mode, rawValue) {
  const normalizedValue = normalizeInput(rawValue);
  if (!normalizedValue) {
    return isWorkspaceInputMode(mode) && mode === 'decision'
      ? '请先输入商品标题、套餐描述，或品牌 + 商品名。'
      : '请先输入消息内容。';
  }

  if (mode !== 'decision') {
    return '';
  }

  if (normalizedValue.length < 2) {
    return '商品信息太短了，至少补充到品牌 + 商品名或更完整的标题。';
  }

  if (looksLikePromotionOnlyInput(normalizedValue)) {
    return '当前输入更像促销文案，缺少明确商品主体。请补充具体品名、规格或套餐内容。';
  }

  return '';
}

function looksLikePromotionOnlyInput(value) {
  const normalized = normalizeInput(value);
  if (!normalized) {
    return false;
  }

  const hasPromotionSignal = DECISION_PROMOTION_ONLY_PHRASES.some((phrase) => normalized.includes(phrase));
  if (!hasPromotionSignal) {
    return false;
  }

  return !DECISION_PRODUCT_HINTS.some((hint) => normalized.includes(hint));
}

function normalizeInput(value) {
  return typeof value === 'string' ? value.trim().replace(/\s+/g, ' ') : '';
}

/** @returns {Storage | null} */
function getDefaultStorage() {
  return typeof window !== 'undefined' ? window.localStorage : null;
}
