import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildInsightsCacheFromHistoryItems,
  getNormalizedRangeKeyFromCacheKey,
  resolveHistoryInsightsState,
} from './insightsHistoryState.ts';

function buildData(summary) {
  return {
    aggregation: {
      totalCalories: 1000,
      totalProtein: 60,
      totalCarbs: 100,
      totalFat: 30,
      proteinRatio: 24,
      carbsRatio: 40,
      fatRatio: 36,
      entryCount: 2,
    },
    entries: [],
    ai: {
      summary,
      risks: [],
      actions: [],
    },
  };
}

test('buildInsightsCacheFromHistoryItems supports cache_key and maps range key', () => {
  const cache = buildInsightsCacheFromHistoryItems([
    {
      cache_key: 'day_2026-03-20_2026-03-20_ids:1-2',
      data: buildData('history'),
    },
  ]);
  const exact = cache['day_2026-03-20_2026-03-20_ids:1-2'];
  const range = cache['day_2026-03-20_2026-03-20'];

  assert.ok(exact);
  assert.ok(range);
  assert.equal(exact?.data.ai.summary, 'history');
  assert.equal(range?.data.ai.summary, 'history');
});

test('refresh scenario: analyzed date resolves from range even if selected ids differ', () => {
  const cache = buildInsightsCacheFromHistoryItems([
    {
      cacheKey: 'day_2026-03-20_2026-03-20_ids:10-20',
      data: buildData('latest'),
    },
  ]);
  const resolved = resolveHistoryInsightsState(cache, 'day_2026-03-20_2026-03-20_all');

  assert.ok(resolved);
  assert.equal(resolved?.data.ai.summary, 'latest');
});

test('keeps first item as latest when multiple history records share the same range', () => {
  const cache = buildInsightsCacheFromHistoryItems([
    {
      cacheKey: 'day_2026-03-20_2026-03-20_ids:9',
      data: buildData('newest'),
    },
    {
      cacheKey: 'day_2026-03-20_2026-03-20_ids:1',
      data: buildData('older'),
    },
  ]);
  const resolved = resolveHistoryInsightsState(cache, 'day_2026-03-20_2026-03-20_all');

  assert.ok(resolved);
  assert.equal(resolved?.data.ai.summary, 'newest');
});

test('returns null when no history exists for mode + date range', () => {
  const cache = buildInsightsCacheFromHistoryItems([
    {
      cacheKey: 'day_2026-03-19_2026-03-19_ids:1',
      data: buildData('another-day'),
    },
  ]);

  const resolved = resolveHistoryInsightsState(cache, 'day_2026-03-20_2026-03-20_ids:1');

  assert.equal(resolved, null);
});

test('does not cross-match between day and week modes', () => {
  const cache = buildInsightsCacheFromHistoryItems([
    {
      cacheKey: 'day_2026-03-20_2026-03-20_ids:1',
      data: buildData('day'),
    },
  ]);

  const resolved = resolveHistoryInsightsState(cache, 'week_2026-03-20_2026-03-20_ids:1');

  assert.equal(resolved, null);
});

test('range key normalization rejects malformed cache keys', () => {
  assert.equal(getNormalizedRangeKeyFromCacheKey('day_2026-13-01_2026-13-01_ids:1'), null);
  assert.equal(getNormalizedRangeKeyFromCacheKey('invalid-key'), null);
  assert.equal(
    getNormalizedRangeKeyFromCacheKey('week_2026-03-16_2026-03-22_ids:2'),
    'week_2026-03-16_2026-03-22',
  );
});

test('falls back to mode + dateRange when cache key cannot be parsed', () => {
  const cache = buildInsightsCacheFromHistoryItems([
    {
      cacheKey: 'legacy-key-without-range',
      mode: 'day',
      dateRange: { start: '2026-03-20', end: '2026-03-20' },
      data: buildData('from-range-fields'),
    },
  ]);

  const resolved = resolveHistoryInsightsState(cache, 'day_2026-03-20_2026-03-20_ids:1');
  assert.ok(resolved);
  assert.equal(resolved?.data.ai.summary, 'from-range-fields');
});
