import assert from 'node:assert/strict';
import test from 'node:test';

import { resolveHistoryInsightsState } from './insightsHistoryState.ts';

function buildState(summary) {
  return {
    status: 'success',
    data: {
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
    },
  };
}

test('prefers exact cache key match over date-only fallback', () => {
  const exact = buildState('exact');
  const fallback = buildState('fallback');
  const cache = {
    'day_2026-03-20_2026-03-20': fallback,
    'day_2026-03-20_2026-03-20_ids:1-2': exact,
  };

  const resolved = resolveHistoryInsightsState(cache, 'day_2026-03-20_2026-03-20_ids:1-2');

  assert.equal(resolved, exact);
});

test('falls back to date-only key when exact key is missing', () => {
  const fallback = buildState('fallback');
  const cache = {
    'week_2026-03-16_2026-03-22': fallback,
  };

  const resolved = resolveHistoryInsightsState(cache, 'week_2026-03-16_2026-03-22_ids:7-8');

  assert.equal(resolved, fallback);
});

test('returns null when no history exists for mode + date range', () => {
  const cache = {
    'day_2026-03-19_2026-03-19': buildState('another-day'),
  };

  const resolved = resolveHistoryInsightsState(cache, 'day_2026-03-20_2026-03-20_ids:1');

  assert.equal(resolved, null);
});

test('does not cross-match between day and week modes', () => {
  const dayState = buildState('day');
  const cache = {
    'day_2026-03-20_2026-03-20': dayState,
  };

  const resolved = resolveHistoryInsightsState(cache, 'week_2026-03-20_2026-03-20_ids:1');

  assert.equal(resolved, null);
});
