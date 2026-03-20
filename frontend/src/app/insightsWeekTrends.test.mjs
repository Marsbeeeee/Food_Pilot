import assert from 'node:assert/strict';
import test from 'node:test';

import { buildWeeklyTrendSummary } from './insightsWeekTrends.ts';

test('buildWeeklyTrendSummary returns 7 points for a full week and captures rising trend', () => {
  const summary = buildWeeklyTrendSummary({
    weekStart: '2026-03-16',
    weekEnd: '2026-03-22',
    items: [
      { analysisDate: '2026-03-16', calories: '1200 kcal' },
      { analysisDate: '2026-03-17', calories: '1300 kcal' },
      { analysisDate: '2026-03-18', calories: '1400 kcal' },
      { analysisDate: '2026-03-20', calories: '1700 kcal' },
      { analysisDate: '2026-03-21', calories: '1950 kcal' },
      { analysisDate: '2026-03-22', calories: '2100 kcal' },
    ],
  });

  assert.equal(summary.points.length, 7);
  assert.equal(summary.activeDays, 6);
  assert.equal(summary.trendDirection, 'up');
  assert.equal(summary.trendLabel, '后半周摄入走高');
  assert.equal(summary.peakPoint?.date, '2026-03-22');
  assert.equal(summary.lowPoint?.date, '2026-03-16');
  assert.equal(Math.round(summary.swingCalories), 900);
  assert.equal(summary.seriesByMetric.calories.points.length, 7);
});

test('buildWeeklyTrendSummary can identify stronger weekend cycle and high volatility', () => {
  const summary = buildWeeklyTrendSummary({
    weekStart: '2026-03-16',
    weekEnd: '2026-03-22',
    items: [
      { analysisDate: '2026-03-16', calories: 900 },
      { analysisDate: '2026-03-17', calories: 950 },
      { analysisDate: '2026-03-18', calories: 1000 },
      { analysisDate: '2026-03-19', calories: 980 },
      { analysisDate: '2026-03-20', calories: 920 },
      { analysisDate: '2026-03-21', calories: 2400 },
      { analysisDate: '2026-03-22', calories: 2300 },
    ],
  });

  assert.equal(summary.cycleLabel, '周末摄入高于工作日');
  assert.equal(summary.volatilityLevel, 'high');
  assert.ok(summary.weekendAverage > summary.weekdayAverage);
  assert.ok(summary.changeTags.length > 0);
});

test('buildWeeklyTrendSummary supports macro series for single-line metric switching', () => {
  const summary = buildWeeklyTrendSummary({
    weekStart: '2026-03-16',
    weekEnd: '2026-03-22',
    items: [
      { analysisDate: '2026-03-16', calories: 1000, protein: '80g', carbs: '90g', fat: '25g' },
      { analysisDate: '2026-03-17', calories: 1100, protein: '85g', carbs: '120g', fat: '22g' },
      { analysisDate: '2026-03-18', calories: 1300, protein: '95g', carbs: '130g', fat: '30g' },
    ],
  });

  assert.equal(summary.seriesByMetric.protein.points.length, 7);
  assert.equal(summary.seriesByMetric.carbs.unit, 'g');
  assert.equal(summary.seriesByMetric.fat.label, '脂肪');
});

test('buildWeeklyTrendSummary returns safe defaults for invalid date ranges', () => {
  const summary = buildWeeklyTrendSummary({
    weekStart: 'not-a-date',
    weekEnd: '2026-03-22',
    items: [{ analysisDate: '2026-03-20', calories: '1000 kcal' }],
  });

  assert.equal(summary.points.length, 0);
  assert.equal(summary.activeDays, 0);
  assert.equal(summary.trendDirection, 'flat');
  assert.equal(summary.cycleLabel, '暂无周期特征');
});
