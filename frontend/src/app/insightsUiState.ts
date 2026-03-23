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
    return mode === 'week' ? '周趋势分析中...' : '分析中...';
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
    ? '聚焦一周趋势、波动和工作日/周末节律。'
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
  return mode === 'week' ? '正在分析本周趋势，请稍候…' : '正在分析中，请稍候…';
}

export function getInsightsSnapshotLifecycleHint(mode: InsightsAnalysisMode): string {
  return mode === 'week'
    ? '页面会优先展示本周最近一次分析快照。Food Log 变化后不会自动同步，请点击“重新分析周趋势”获取最新结果。'
    : '页面会优先展示该日期最近一次分析快照。Food Log 变化后不会自动同步，请点击“重新分析”获取最新结果。';
}

export function getInsightsSnapshotNotice(
  mode: InsightsAnalysisMode,
  isHistoryResult: boolean,
  hasSelectionMismatch: boolean,
): InsightsSnapshotNotice {
  if (isHistoryResult || hasSelectionMismatch) {
    return {
      level: 'warning',
      title: '数据可能已变化',
      detail: mode === 'week'
        ? '当前显示的是历史周趋势快照，Food Log 可能已变化，请重新分析周趋势。'
        : '当前显示的是历史分析快照，Food Log 可能已变化，请重新分析。',
    };
  }

  return {
    level: 'info',
    title: '当前结果为快照',
    detail: mode === 'week'
      ? '结果不会随 Food Log 自动更新。修改记录后，请重新分析周趋势。'
      : '结果不会随 Food Log 自动更新。修改记录后，请重新分析。',
  };
}
