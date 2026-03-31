export type InsightsPanelStatus = 'idle' | 'loading' | 'success' | 'error';
export type InsightsAnalysisMode = 'day' | 'week';
export type InsightsSnapshotNoticeLevel = 'info' | 'warning';

export interface InsightsSnapshotNotice {
  level: InsightsSnapshotNoticeLevel;
  title: string;
  detail: string;
}

export function getInsightsAnalyzeButtonText(
  status: InsightsPanelStatus,
  mode: InsightsAnalysisMode = 'day',
): string {
  if (status === 'loading') {
    return mode === 'week' ? '分析周趋势中...' : '分析中...';
  }
  if (status === 'success') {
    return mode === 'week' ? '重新分析周趋势' : '重新分析';
  }
  return mode === 'week' ? '生成周趋势分析' : '生成 AI 分析';
}

export function shouldForceReanalyze(status: InsightsPanelStatus): boolean {
  return status === 'success';
}

export function getInsightsScopeDescription(mode: InsightsAnalysisMode): string {
  return mode === 'week'
    ? '聚焦一周趋势、波动和工作日 / 周末节律。'
    : '聚焦单日摄入、目标差距和当日调整。';
}

export function getInsightsAIPanelDescription(mode: InsightsAnalysisMode): string {
  return mode === 'week'
    ? '基于本周已选菜品，生成趋势解读、波动提示与改善建议。'
    : '基于当日已选菜品，生成营养摄入分析与改善建议。';
}

export function getInsightsIdleHint(
  mode: InsightsAnalysisMode,
  hasSelectedItems: boolean,
): string {
  if (!hasSelectedItems) {
    return mode === 'week'
      ? '添加饮食记录后，即可生成本周趋势分析。'
      : '添加饮食记录后，即可生成 AI 营养摄入分析。';
  }
  return mode === 'week'
    ? '点击下方按钮开始生成本周趋势分析。'
    : '点击下方按钮开始生成 AI 分析。';
}

export function getInsightsLoadingHint(mode: InsightsAnalysisMode): string {
  return mode === 'week' ? '正在分析本周趋势，请稍候...' : '正在分析中，请稍候...';
}

export function getInsightsSnapshotLifecycleHint(mode: InsightsAnalysisMode): string {
  return mode === 'week'
    ? '左侧周数据会随当前已选菜品立即更新；右侧 AI 周趋势仍优先展示最近一次分析快照。菜品变化后，如需刷新建议，请点击“重新分析周趋势”。'
    : '左侧数据会随当前已选菜品立即更新；右侧 AI 建议仍优先展示该日期最近一次分析快照。菜品变化后，如需刷新建议，请点击“重新分析”。';
}

export function getInsightsSnapshotNotice(
  mode: InsightsAnalysisMode,
  isHistoryResult: boolean,
  hasSelectionMismatch: boolean,
): InsightsSnapshotNotice {
  if (isHistoryResult || hasSelectionMismatch) {
    return {
      level: 'warning',
      title: 'AI 结果可能已过期',
      detail: mode === 'week'
        ? '左侧周数据已按当前已选菜品更新，右侧仍是历史周趋势快照。请重新分析周趋势以刷新 AI 建议。'
        : '左侧数据已按当前已选菜品更新，右侧仍是历史分析快照。请重新分析以刷新 AI 建议。',
    };
  }

  return {
    level: 'info',
    title: 'AI 结果为快照',
    detail: mode === 'week'
      ? '左侧周数据会实时变化，右侧 AI 周趋势不会自动更新。修改菜品后，请重新分析周趋势。'
      : '左侧数据会实时变化，右侧 AI 建议不会自动更新。修改菜品后，请重新分析。',
  };
}
