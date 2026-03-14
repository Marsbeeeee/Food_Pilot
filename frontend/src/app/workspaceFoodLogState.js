export function resolveFoodLogSavePresentation({
  savedEntryId,
  isSaving,
  failedMessage,
}) {
  const state = savedEntryId
    ? 'saved'
    : isSaving
      ? 'saving'
      : failedMessage
        ? 'failed'
        : 'not_saved';

  switch (state) {
    case 'saved':
      return {
        state,
        badgeIcon: 'bookmark_added',
        badgeLabel: 'Saved',
        saveActionIcon: 'bookmark_add',
        saveActionLabel: 'Save to Food Log',
        helperText: 'This analysis is already in Food Log. You can undo the save without losing the source chat.',
      };
    case 'saving':
      return {
        state,
        badgeIcon: 'hourglass_top',
        badgeLabel: 'Saving',
        saveActionIcon: 'bookmark_add',
        saveActionLabel: 'Saving...',
        helperText: 'Food Log is saving this analysis now.',
      };
    case 'failed':
      return {
        state,
        badgeIcon: 'error',
        badgeLabel: 'Save failed',
        saveActionIcon: 'refresh',
        saveActionLabel: 'Retry save',
        helperText: failedMessage ?? 'Food Log could not save this analysis. Try again.',
      };
    default:
      return {
        state: 'not_saved',
        badgeIcon: 'bookmark_add',
        badgeLabel: 'Not saved',
        saveActionIcon: 'bookmark_add',
        saveActionLabel: 'Save to Food Log',
        helperText: 'Food Log keeps each saved analysis as its own record. Saving here will not overwrite older entries just because the meal text matches.',
      };
  }
}
