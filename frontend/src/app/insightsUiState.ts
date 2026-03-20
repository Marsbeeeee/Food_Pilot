export type InsightsPanelStatus = 'idle' | 'loading' | 'success' | 'error';
export type InsightsAnalysisMode = 'day' | 'week';

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
