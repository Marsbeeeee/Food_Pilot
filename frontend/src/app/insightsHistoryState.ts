import { getDateOnlyFromCacheKey } from './insightsCacheKey.ts';
import type { InsightsAnalyzeData } from '../types/types';

export type InsightsSuccessState = { status: 'success'; data: InsightsAnalyzeData };
export type InsightsCache = Record<string, InsightsSuccessState>;

export function resolveHistoryInsightsState(
  insightsCache: InsightsCache,
  currentCacheKey: string,
): InsightsSuccessState | null {
  const exactMatch = insightsCache[currentCacheKey];
  if (exactMatch) {
    return exactMatch;
  }

  const dateOnlyKey = getDateOnlyFromCacheKey(currentCacheKey);
  if (!dateOnlyKey) {
    return null;
  }

  return insightsCache[dateOnlyKey] ?? null;
}
