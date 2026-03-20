import type { InsightsAnalyzeData } from '../types/types';

export type InsightsSuccessState = { status: 'success'; data: InsightsAnalyzeData };
export type InsightsCache = Record<string, InsightsSuccessState>;
export type RawInsightsHistoryItem = {
  cacheKey?: unknown;
  cache_key?: unknown;
  mode?: unknown;
  dateRange?: unknown;
  date_range?: unknown;
  data?: unknown;
};

const CACHE_KEY_RANGE_PATTERN = /^(day|week)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})(?:_.*)?$/;

function isValidDateInput(input: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(input)) {
    return false;
  }
  const [year, month, day] = input.split('-').map(Number);
  const normalized = new Date(Date.UTC(year, month - 1, day));
  return normalized.getUTCFullYear() === year
    && normalized.getUTCMonth() + 1 === month
    && normalized.getUTCDate() === day;
}

export function getNormalizedRangeKeyFromCacheKey(cacheKey: string): string | null {
  const normalized = cacheKey.trim();
  const match = normalized.match(CACHE_KEY_RANGE_PATTERN);
  if (!match) {
    return null;
  }
  const [, mode, start, end] = match;
  if (!isValidDateInput(start) || !isValidDateInput(end)) {
    return null;
  }
  return `${mode}_${start}_${end}`;
}

function readHistoryCacheKey(item: RawInsightsHistoryItem): string | null {
  const camelCase = typeof item.cacheKey === 'string' ? item.cacheKey.trim() : '';
  if (camelCase) {
    return camelCase;
  }
  const snakeCase = typeof item.cache_key === 'string' ? item.cache_key.trim() : '';
  if (snakeCase) {
    return snakeCase;
  }
  return null;
}

function getNormalizedRangeKeyFromHistoryItem(item: RawInsightsHistoryItem): string | null {
  const mode = item.mode === 'day' || item.mode === 'week' ? item.mode : null;
  if (!mode) {
    return null;
  }
  const rawDateRange = (
    item.dateRange && typeof item.dateRange === 'object'
      ? item.dateRange
      : item.date_range && typeof item.date_range === 'object'
        ? item.date_range
        : null
  ) as { start?: unknown; end?: unknown } | null;
  if (!rawDateRange) {
    return null;
  }
  const start = typeof rawDateRange.start === 'string' ? rawDateRange.start : '';
  const end = typeof rawDateRange.end === 'string' ? rawDateRange.end : '';
  if (!isValidDateInput(start) || !isValidDateInput(end)) {
    return null;
  }
  return `${mode}_${start}_${end}`;
}

function readHistoryData(item: RawInsightsHistoryItem): InsightsAnalyzeData | null {
  if (!item.data || typeof item.data !== 'object') {
    return null;
  }
  return item.data as InsightsAnalyzeData;
}

export function buildInsightsCacheFromHistoryItems(
  items: readonly RawInsightsHistoryItem[],
): InsightsCache {
  const next: InsightsCache = {};
  for (const item of items) {
    const cacheKey = readHistoryCacheKey(item);
    const rangeKeyFromCacheKey = cacheKey ? getNormalizedRangeKeyFromCacheKey(cacheKey) : null;
    const rangeKeyFromFields = getNormalizedRangeKeyFromHistoryItem(item);
    const rangeKey = rangeKeyFromCacheKey ?? rangeKeyFromFields;
    const effectiveCacheKey = cacheKey || rangeKey;
    const data = readHistoryData(item);
    if (!effectiveCacheKey || !data) {
      continue;
    }

    const state = { status: 'success' as const, data };
    next[effectiveCacheKey] = state;

    if (rangeKey && !(rangeKey in next)) {
      next[rangeKey] = state;
    }
  }
  return next;
}

export function resolveHistoryInsightsState(
  insightsCache: InsightsCache,
  currentCacheKey: string,
): InsightsSuccessState | null {
  const exactMatch = insightsCache[currentCacheKey];
  if (exactMatch) {
    return exactMatch;
  }

  const rangeKey = getNormalizedRangeKeyFromCacheKey(currentCacheKey);
  if (!rangeKey) {
    return null;
  }

  return insightsCache[rangeKey] ?? null;
}
