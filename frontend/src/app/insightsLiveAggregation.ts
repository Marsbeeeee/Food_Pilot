import type { NutritionAggregation } from '../types/types';

type AggregationSourceItem = {
  calories: string | number;
  protein?: string | null;
  carbs?: string | null;
  fat?: string | null;
};

export function extractCaloriesValue(value: string | number): number {
  const match = String(value).match(/(\d+(?:\.\d+)?)/);
  if (!match) {
    return 0;
  }

  const parsed = Number.parseFloat(match[1]);
  return Number.isFinite(parsed) ? Math.ceil(parsed) : 0;
}

export function extractNutritionValue(value?: string | null): number {
  if (!value) {
    return 0;
  }

  const match = String(value).match(/(\d+(?:\.\d+)?)/);
  if (!match) {
    return 0;
  }

  const parsed = Number.parseFloat(match[1]);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function getPercent(value: number, total: number): number {
  if (total <= 0) {
    return 0;
  }
  return Number(((value / total) * 100).toFixed(2));
}

export function buildInsightsLiveAggregation(
  items: readonly AggregationSourceItem[],
): NutritionAggregation {
  const totalCalories = items.reduce(
    (sum, item) => sum + extractCaloriesValue(item.calories),
    0,
  );
  const totalProtein = items.reduce(
    (sum, item) => sum + extractNutritionValue(item.protein),
    0,
  );
  const totalCarbs = items.reduce(
    (sum, item) => sum + extractNutritionValue(item.carbs),
    0,
  );
  const totalFat = items.reduce(
    (sum, item) => sum + extractNutritionValue(item.fat),
    0,
  );
  const macroTotal = totalProtein + totalCarbs + totalFat;

  return {
    totalCalories,
    totalProtein,
    totalCarbs,
    totalFat,
    proteinRatio: getPercent(totalProtein, macroTotal),
    carbsRatio: getPercent(totalCarbs, macroTotal),
    fatRatio: getPercent(totalFat, macroTotal),
    entryCount: items.length,
  };
}
