/**
 * Calorie recommendation based on BMR, TDEE, goal, and pace.
 * BMR: Mifflin-St Jeor equation
 * TDEE: BMR × activity multiplier
 */

export const PACE_OPTIONS = [
  { value: 'Conservative', label: 'Conservative' },
  { value: 'Moderate', label: 'Moderate' },
  { value: 'Aggressive', label: 'Aggressive' },
] as const;

export type PaceValue = (typeof PACE_OPTIONS)[number]['value'];

const ACTIVITY_MULTIPLIERS: Record<string, number> = {
  Sedentary: 1.2,
  'Lightly active': 1.375,
  'Moderately active': 1.55,
  'Highly active': 1.725,
};

/** Mifflin-St Jeor BMR: 10*weight(kg) + 6.25*height(cm) - 5*age + s (s: +5 male, -161 female) */
export function calculateBMR(age: number, height: number, weight: number, sex: string): number {
  const base = 10 * weight + 6.25 * height - 5 * age;
  let sexFactor = -161;
  if (sex.toLowerCase().includes('male')) sexFactor = 5;
  else if (sex.toLowerCase().includes('prefer') || sex.toLowerCase().includes('not')) sexFactor = -78;
  return Math.round(base + sexFactor);
}

/** TDEE = BMR × activity multiplier */
export function calculateTDEE(bmr: number, activityLevel: string): number {
  const multiplier = ACTIVITY_MULTIPLIERS[activityLevel] ?? 1.2;
  return Math.round(bmr * multiplier);
}

/** Calorie adjustment by pace (kcal/day) */
const PACE_DEFICIT: Record<PaceValue, number> = {
  Conservative: 250,   // ~0.25 kg/week
  Moderate: 500,       // ~0.5 kg/week
  Aggressive: 750,     // ~0.75 kg/week
};

const PACE_SURPLUS: Record<PaceValue, number> = {
  Conservative: 200,
  Moderate: 300,
  Aggressive: 500,
};

/** General health: subtle pace variation around TDEE */
const PACE_MAINTENANCE_OFFSET: Record<PaceValue, number> = {
  Conservative: -100,  // slight under
  Moderate: 0,
  Aggressive: 100,     // slight surplus
};

export interface CalorieRecommendationInput {
  age: number;
  height: number;
  weight: number;
  sex: string;
  activityLevel: string;
  goal: string;
  pace: string;
}

export interface CalorieRecommendationResult {
  bmr: number;
  tdee: number;
  recommendedKcal: number;
  canCalculate: boolean;
}

export function getRecommendedCalories(input: CalorieRecommendationInput): CalorieRecommendationResult {
  const { age, height, weight, sex, activityLevel, goal, pace } = input;

  const hasValidInput =
    age > 0 &&
    height > 0 &&
    weight > 0 &&
    sex &&
    activityLevel &&
    goal &&
    pace;

  if (!hasValidInput) {
    return { bmr: 0, tdee: 0, recommendedKcal: 0, canCalculate: false };
  }

  const bmr = calculateBMR(age, height, weight, sex);
  const tdee = calculateTDEE(bmr, activityLevel);

  const paceKey = (PACE_OPTIONS.some((p) => p.value === pace) ? pace : 'Moderate') as PaceValue;
  const deficit = PACE_DEFICIT[paceKey] ?? 500;
  const surplus = PACE_SURPLUS[paceKey] ?? 300;

  let recommendedKcal: number;
  switch (goal) {
    case 'Fat loss':
      recommendedKcal = Math.max(tdee - deficit, 1200);
      break;
    case 'Muscle gain':
      recommendedKcal = tdee + surplus;
      break;
    case 'Performance':
      recommendedKcal = tdee + (PACE_SURPLUS[paceKey] ?? 200) * 0.5;
      break;
    case 'General health':
    default:
      recommendedKcal = tdee + (PACE_MAINTENANCE_OFFSET[paceKey] ?? 0);
      break;
  }

  return {
    bmr,
    tdee,
    recommendedKcal: Math.round(recommendedKcal),
    canCalculate: true,
  };
}
