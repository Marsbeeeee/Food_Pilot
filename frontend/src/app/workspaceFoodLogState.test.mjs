import assert from 'node:assert/strict';
import test from 'node:test';

import { resolveFoodLogSavePresentation } from './workspaceFoodLogState.js';

test('resolveFoodLogSavePresentation prioritizes saved state', () => {
  const presentation = resolveFoodLogSavePresentation({
    savedEntryId: '123',
    isSaving: false,
    failedMessage: 'Previous save failed',
  });

  assert.deepEqual(presentation, {
    state: 'saved',
    badgeIcon: 'bookmark_added',
    badgeLabel: '已保存',
    saveActionIcon: 'bookmark_add',
    saveActionLabel: '保存到 Food Log',
    helperText: '这条估算结果已经保存到 Food Log。撤销保存后，来源聊天仍会保留。',
  });
});

test('resolveFoodLogSavePresentation returns failed retry state', () => {
  const presentation = resolveFoodLogSavePresentation({
    savedEntryId: null,
    isSaving: false,
    failedMessage: 'Food Log is temporarily unavailable.',
  });

  assert.deepEqual(presentation, {
    state: 'failed',
    badgeIcon: 'error',
    badgeLabel: '保存失败',
    saveActionIcon: 'refresh',
    saveActionLabel: '重试保存',
    helperText: 'Food Log is temporarily unavailable.',
  });
});

test('resolveFoodLogSavePresentation returns saving state before failed state', () => {
  const presentation = resolveFoodLogSavePresentation({
    savedEntryId: null,
    isSaving: true,
    failedMessage: 'Old error',
  });

  assert.deepEqual(presentation, {
    state: 'saving',
    badgeIcon: 'hourglass_top',
    badgeLabel: '保存中',
    saveActionIcon: 'bookmark_add',
    saveActionLabel: '保存中...',
    helperText: 'Food Log 正在保存这条估算结果。',
  });
});

test('resolveFoodLogSavePresentation defaults to not saved state', () => {
  const presentation = resolveFoodLogSavePresentation({
    savedEntryId: null,
    isSaving: false,
    failedMessage: '',
  });

  assert.deepEqual(presentation, {
    state: 'not_saved',
    badgeIcon: 'bookmark_add',
    badgeLabel: '未保存',
    saveActionIcon: 'bookmark_add',
    saveActionLabel: '保存到 Food Log',
    helperText: 'Food Log 会把每次保存的估算结果作为独立记录保存，不会因为餐食文字相同就覆盖旧记录。',
  });
});
