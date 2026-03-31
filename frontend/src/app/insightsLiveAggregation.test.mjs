import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildInsightsLiveAggregation,
  extractCaloriesValue,
  extractNutritionValue,
  getPercent,
} from './insightsLiveAggregation.ts';

test('buildInsightsLiveAggregation derives totals and ratios from current selected items', () => {
  assert.deepEqual(
    buildInsightsLiveAggregation([
      {
        calories: '320 kcal',
        protein: '12.4 g',
        carbs: '40.2 g',
        fat: '8.1 g',
      },
      {
        calories: '180',
        protein: '10 g',
        carbs: '5 g',
        fat: '6.5 g',
      },
    ]),
    {
      totalCalories: 500,
      totalProtein: 22.4,
      totalCarbs: 45.2,
      totalFat: 14.6,
      proteinRatio: 27.25,
      carbsRatio: 54.99,
      fatRatio: 17.76,
      entryCount: 2,
    },
  );
});

test('buildInsightsLiveAggregation falls back to zero ratios when macros are absent', () => {
  assert.deepEqual(
    buildInsightsLiveAggregation([
      {
        calories: '210 kcal',
      },
    ]),
    {
      totalCalories: 210,
      totalProtein: 0,
      totalCarbs: 0,
      totalFat: 0,
      proteinRatio: 0,
      carbsRatio: 0,
      fatRatio: 0,
      entryCount: 1,
    },
  );
});

test('parsing helpers keep numeric extraction stable', () => {
  assert.equal(extractCaloriesValue('201.2 kcal'), 202);
  assert.equal(extractCaloriesValue('unknown'), 0);
  assert.equal(extractNutritionValue('18.5 g'), 18.5);
  assert.equal(extractNutritionValue(undefined), 0);
  assert.equal(getPercent(25, 80), 31.25);
  assert.equal(getPercent(25, 0), 0);
});
