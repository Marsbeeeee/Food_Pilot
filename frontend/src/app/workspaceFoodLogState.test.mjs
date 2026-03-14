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
    badgeLabel: 'Saved',
    saveActionIcon: 'bookmark_add',
    saveActionLabel: 'Save to Food Log',
    helperText: 'This analysis is already in Food Log. You can undo the save without losing the source chat.',
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
    badgeLabel: 'Save failed',
    saveActionIcon: 'refresh',
    saveActionLabel: 'Retry save',
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
    badgeLabel: 'Saving',
    saveActionIcon: 'bookmark_add',
    saveActionLabel: 'Saving...',
    helperText: 'Food Log is saving this analysis now.',
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
    badgeLabel: 'Not saved',
    saveActionIcon: 'bookmark_add',
    saveActionLabel: 'Save to Food Log',
    helperText: 'Food Log keeps each saved analysis as its own record. Saving here will not overwrite older entries just because the meal text matches.',
  });
});
