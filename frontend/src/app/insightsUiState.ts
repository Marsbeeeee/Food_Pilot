export type InsightsPanelStatus = 'idle' | 'loading' | 'success' | 'error';

export function getInsightsAnalyzeButtonText(status: InsightsPanelStatus): string {
  if (status === 'loading') {
    return '分析中...';
  }
  if (status === 'success') {
    return '重新分析';
  }
  return '生成 AI 分析';
}

export function shouldForceReanalyze(status: InsightsPanelStatus): boolean {
  return status === 'success';
}
