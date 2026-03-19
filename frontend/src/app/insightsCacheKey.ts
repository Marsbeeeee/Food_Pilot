export type InsightsAnalysisMode = 'day' | 'week';

export function buildDateOnlyInsightsCacheKey(
  mode: InsightsAnalysisMode,
  start: string,
  end: string,
): string {
  return `${mode}_${start}_${end}`;
}

export function normalizeSelectedLogIds(selectedLogIds: readonly number[] | undefined): number[] {
  if (!selectedLogIds || selectedLogIds.length === 0) {
    return [];
  }

  return Array.from(
    new Set(
      selectedLogIds.filter((id) => Number.isInteger(id) && id > 0),
    ),
  ).sort((a, b) => a - b);
}

export function buildInsightsCacheKey(
  mode: InsightsAnalysisMode,
  start: string,
  end: string,
  selectedLogIds: readonly number[] | undefined,
): string {
  const dateOnly = buildDateOnlyInsightsCacheKey(mode, start, end);
  const normalizedIds = normalizeSelectedLogIds(selectedLogIds);
  if (normalizedIds.length === 0) {
    return `${dateOnly}_all`;
  }
  return `${dateOnly}_ids:${normalizedIds.join('-')}`;
}

export function getDateOnlyFromCacheKey(cacheKey: string): string | null {
  const parts = cacheKey.split('_');
  if (parts.length >= 3) {
    return `${parts[0]}_${parts[1]}_${parts[2]}`;
  }
  return null;
}
