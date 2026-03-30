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
        badgeLabel: '已保存',
        saveActionIcon: 'bookmark_add',
        saveActionLabel: '保存到饮食记录',
        helperText: '这条估算结果已经保存到饮食记录。撤销保存后，来源聊天仍会保留。',
      };
    case 'saving':
      return {
        state,
        badgeIcon: 'hourglass_top',
        badgeLabel: '保存中',
        saveActionIcon: 'bookmark_add',
        saveActionLabel: '保存中...',
        helperText: '饮食记录正在保存这条估算结果。',
      };
    case 'failed':
      return {
        state,
        badgeIcon: 'error',
        badgeLabel: '保存失败',
        saveActionIcon: 'refresh',
        saveActionLabel: '重试保存',
        helperText: failedMessage ?? '饮食记录暂时无法保存这条估算结果，请稍后重试。',
      };
    default:
      return {
        state: 'not_saved',
        badgeIcon: 'bookmark_add',
        badgeLabel: '未保存',
        saveActionIcon: 'bookmark_add',
        saveActionLabel: '保存到饮食记录',
        helperText: '饮食记录会把每次保存的估算结果作为独立记录保存，不会因为餐食文字相同就覆盖旧记录。',
      };
  }
}
