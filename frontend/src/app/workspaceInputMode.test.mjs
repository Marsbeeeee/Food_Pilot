import test from 'node:test';
import assert from 'node:assert/strict';

import {
  DEFAULT_WORKSPACE_INPUT_MODE,
  WORKSPACE_INPUT_MODE_OPTIONS,
  WORKSPACE_INPUT_MODE_STORAGE_KEY,
  buildWorkspaceMessageRequest,
  getStoredWorkspaceInputMode,
  getWorkspaceInputModeConfig,
  persistWorkspaceInputMode,
  validateWorkspaceInput,
} from './workspaceInputMode.js';

test('returns chat mode config by default for unknown mode', () => {
  const config = getWorkspaceInputModeConfig('unknown');

  assert.equal(config.value, 'chat');
  assert.equal(config.label, '普通对话');
});

test('workspace input mode options keep decision entry for launcher menu', () => {
  assert.deepEqual(
    WORKSPACE_INPUT_MODE_OPTIONS.map((option) => option.value),
    ['decision'],
  );
  assert.equal(getWorkspaceInputModeConfig('decision').description, '适合商品标题、套餐描述和品牌 + 商品名。');
});

test('buildWorkspaceMessageRequest carries mode and optional profileId', () => {
  assert.deepEqual(
    buildWorkspaceMessageRequest('瑞幸 生椰拿铁', 12, 'decision'),
    {
      content: '瑞幸 生椰拿铁',
      mode: 'decision',
      profileId: 12,
    },
  );

  assert.deepEqual(
    buildWorkspaceMessageRequest('今天晚饭吃什么', undefined, 'chat'),
    {
      content: '今天晚饭吃什么',
      mode: 'chat',
    },
  );
});

test('getStoredWorkspaceInputMode falls back when storage is empty or invalid', () => {
  const emptyStorage = createStorage();
  const invalidStorage = createStorage({ [WORKSPACE_INPUT_MODE_STORAGE_KEY]: 'other' });

  assert.equal(getStoredWorkspaceInputMode(emptyStorage), DEFAULT_WORKSPACE_INPUT_MODE);
  assert.equal(getStoredWorkspaceInputMode(invalidStorage), DEFAULT_WORKSPACE_INPUT_MODE);
});

test('persistWorkspaceInputMode writes only supported modes', () => {
  const storage = createStorage();

  persistWorkspaceInputMode('decision', storage);
  persistWorkspaceInputMode('other', storage);

  assert.equal(storage.getItem(WORKSPACE_INPUT_MODE_STORAGE_KEY), 'decision');
});

test('validateWorkspaceInput blocks empty and promotion-only decision input', () => {
  assert.equal(
    validateWorkspaceInput('decision', ''),
    '请先输入商品标题、套餐描述，或品牌 + 商品名。',
  );
  assert.equal(
    validateWorkspaceInput('decision', '限时优惠 买一送一'),
    '当前输入更像促销文案，缺少明确商品主体。请补充具体品名、规格或套餐内容。',
  );
  assert.equal(validateWorkspaceInput('decision', '霸王茶姬 伯牙绝弦 大杯 三分糖'), '');
  assert.equal(validateWorkspaceInput('chat', '今天晚饭吃什么'), '');
});

function createStorage(seed = {}) {
  const values = new Map(Object.entries(seed));

  return {
    getItem(key) {
      return values.has(key) ? values.get(key) : null;
    },
    setItem(key, value) {
      values.set(key, String(value));
    },
  };
}
