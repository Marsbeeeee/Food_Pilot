import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildDateOnlyInsightsCacheKey,
  buildInsightsCacheKey,
  getDateOnlyFromCacheKey,
  normalizeSelectedLogIds,
} from './insightsCacheKey.ts';

test('same date range with different selected ids generates different cache keys', () => {
  const keyA = buildInsightsCacheKey('day', '2026-03-20', '2026-03-20', [1, 2]);
  const keyB = buildInsightsCacheKey('day', '2026-03-20', '2026-03-20', [3, 4]);

  assert.notEqual(keyA, keyB);
});

test('same selected ids still hit the same cache key regardless of order and duplication', () => {
  const keyA = buildInsightsCacheKey('week', '2026-03-16', '2026-03-22', [8, 2, 8, 5]);
  const keyB = buildInsightsCacheKey('week', '2026-03-16', '2026-03-22', [5, 2, 8]);

  assert.equal(keyA, keyB);
});

test('empty selected ids keeps deterministic key for all-logs analysis', () => {
  const dateOnly = buildDateOnlyInsightsCacheKey('day', '2026-03-20', '2026-03-20');
  const key = buildInsightsCacheKey('day', '2026-03-20', '2026-03-20', []);

  assert.equal(key, `${dateOnly}_all`);
});

test('extracts date-only key from full and legacy cache keys', () => {
  assert.equal(
    getDateOnlyFromCacheKey('day_2026-03-20_2026-03-20_ids:1-2-3'),
    'day_2026-03-20_2026-03-20',
  );
  assert.equal(
    getDateOnlyFromCacheKey('week_2026-03-16_2026-03-22'),
    'week_2026-03-16_2026-03-22',
  );
});

test('normalization removes invalid ids, deduplicates and sorts', () => {
  assert.deepEqual(normalizeSelectedLogIds([4, -1, 2, 2, 0, 3.5, 1]), [1, 2, 4]);
});
