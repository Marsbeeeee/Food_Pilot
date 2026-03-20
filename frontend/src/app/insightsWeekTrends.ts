export interface WeekTrendSourceItem {
  analysisDate: string;
  calories: string | number;
  protein?: string | number | null;
  carbs?: string | number | null;
  fat?: string | number | null;
}

export interface WeeklyCaloriePoint {
  date: string;
  label: string;
  calories: number;
  isWeekend: boolean;
  deltaFromPrevious: number | null;
}

export interface WeeklyMetricPoint {
  date: string;
  label: string;
  value: number;
  isWeekend: boolean;
  deltaFromPrevious: number | null;
}

export type WeeklyTrendMetric = 'calories' | 'protein' | 'carbs' | 'fat';

export interface WeeklyMetricSeries {
  metric: WeeklyTrendMetric;
  label: string;
  unit: string;
  points: WeeklyMetricPoint[];
  average: number;
  peakPoint: WeeklyMetricPoint | null;
  lowPoint: WeeklyMetricPoint | null;
}

export interface WeeklyChangeTag {
  date: string;
  label: string;
  delta: number;
  direction: 'up' | 'down';
}

export type WeeklyTrendDirection = 'up' | 'down' | 'flat';
export type WeeklyVolatilityLevel = 'steady' | 'moderate' | 'high';

export interface WeeklyTrendSummary {
  points: WeeklyCaloriePoint[];
  seriesByMetric: Record<WeeklyTrendMetric, WeeklyMetricSeries>;
  activeDays: number;
  averageDailyCalories: number;
  averageActiveDayCalories: number;
  peakPoint: WeeklyCaloriePoint | null;
  lowPoint: WeeklyCaloriePoint | null;
  swingCalories: number;
  trendDirection: WeeklyTrendDirection;
  trendLabel: string;
  trendDetail: string;
  volatilityLevel: WeeklyVolatilityLevel;
  volatilityLabel: string;
  cycleLabel: string;
  cycleDetail: string;
  weekdayAverage: number;
  weekendAverage: number;
  changeTags: WeeklyChangeTag[];
  changeInsightText: string;
}

interface BuildWeeklyTrendSummaryInput {
  weekStart: string;
  weekEnd: string;
  items: readonly WeekTrendSourceItem[];
}

const WEEKDAY_LABELS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

function parseDateOnly(value: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return null;
  }
  const [year, month, day] = value.split('-').map(Number);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  if (
    parsed.getUTCFullYear() !== year
    || parsed.getUTCMonth() + 1 !== month
    || parsed.getUTCDate() !== day
  ) {
    return null;
  }
  return parsed;
}

function formatDateOnly(date: Date): string {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function getDateSpan(start: Date, end: Date): Date[] {
  if (end.getTime() < start.getTime()) {
    return [];
  }
  const dates: Date[] = [];
  let cursor = start.getTime();
  while (cursor <= end.getTime()) {
    dates.push(new Date(cursor));
    cursor += 24 * 60 * 60 * 1000;
  }
  return dates;
}

function extractNumber(value: string | number | null | undefined): number {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? Math.max(0, value) : 0;
  }
  if (value == null) {
    return 0;
  }
  const matched = String(value).match(/(\d+(?:\.\d+)?)/);
  if (!matched) {
    return 0;
  }
  const parsed = Number.parseFloat(matched[1]);
  return Number.isFinite(parsed) ? Math.max(0, parsed) : 0;
}

function computeAverage(values: readonly number[]): number {
  if (values.length === 0) return 0;
  const total = values.reduce((sum, value) => sum + value, 0);
  return total / values.length;
}

function getPeakPoint(points: readonly WeeklyCaloriePoint[]): WeeklyCaloriePoint | null {
  if (points.length === 0) return null;
  return points.reduce((max, point) => (point.calories > max.calories ? point : max), points[0]);
}

function getLowPoint(points: readonly WeeklyCaloriePoint[]): WeeklyCaloriePoint | null {
  if (points.length === 0) return null;
  return points.reduce((min, point) => (point.calories < min.calories ? point : min), points[0]);
}

function getPeakMetricPoint(points: readonly WeeklyMetricPoint[]): WeeklyMetricPoint | null {
  if (points.length === 0) return null;
  return points.reduce((max, point) => (point.value > max.value ? point : max), points[0]);
}

function getLowMetricPoint(points: readonly WeeklyMetricPoint[]): WeeklyMetricPoint | null {
  if (points.length === 0) return null;
  return points.reduce((min, point) => (point.value < min.value ? point : min), points[0]);
}

function buildMetricSeries(
  metric: WeeklyTrendMetric,
  label: string,
  unit: string,
  points: readonly { date: string; label: string; isWeekend: boolean; value: number }[],
): WeeklyMetricSeries {
  const seriesPoints = points.map((point, index) => {
    const previous = index > 0 ? points[index - 1] : null;
    return {
      date: point.date,
      label: point.label,
      value: point.value,
      isWeekend: point.isWeekend,
      deltaFromPrevious: previous ? point.value - previous.value : null,
    };
  });
  return {
    metric,
    label,
    unit,
    points: seriesPoints,
    average: computeAverage(seriesPoints.map((point) => point.value)),
    peakPoint: getPeakMetricPoint(seriesPoints),
    lowPoint: getLowMetricPoint(seriesPoints),
  };
}

export function buildWeeklyTrendSummary(
  input: BuildWeeklyTrendSummaryInput,
): WeeklyTrendSummary {
  const startDate = parseDateOnly(input.weekStart);
  const endDate = parseDateOnly(input.weekEnd);
  if (!startDate || !endDate) {
    const emptySeries: WeeklyMetricSeries = {
      metric: 'calories',
      label: '热量',
      unit: 'kcal',
      points: [],
      average: 0,
      peakPoint: null,
      lowPoint: null,
    };
    return {
      points: [],
      seriesByMetric: {
        calories: emptySeries,
        protein: { ...emptySeries, metric: 'protein', label: '蛋白质', unit: 'g' },
        carbs: { ...emptySeries, metric: 'carbs', label: '碳水', unit: 'g' },
        fat: { ...emptySeries, metric: 'fat', label: '脂肪', unit: 'g' },
      },
      activeDays: 0,
      averageDailyCalories: 0,
      averageActiveDayCalories: 0,
      peakPoint: null,
      lowPoint: null,
      swingCalories: 0,
      trendDirection: 'flat',
      trendLabel: '暂无可用趋势',
      trendDetail: '日期范围无效，无法计算周趋势。',
      volatilityLevel: 'steady',
      volatilityLabel: '平稳',
      cycleLabel: '暂无周期特征',
      cycleDetail: '日期范围无效，无法计算工作日和周末差异。',
      weekdayAverage: 0,
      weekendAverage: 0,
      changeTags: [],
      changeInsightText: '日期范围无效，无法生成变化提示。',
    };
  }

  const span = getDateSpan(startDate, endDate);
  const caloriesByDate = new Map<string, number>();
  const proteinByDate = new Map<string, number>();
  const carbsByDate = new Map<string, number>();
  const fatByDate = new Map<string, number>();
  for (const item of input.items) {
    if (!caloriesByDate.has(item.analysisDate)) {
      caloriesByDate.set(item.analysisDate, 0);
      proteinByDate.set(item.analysisDate, 0);
      carbsByDate.set(item.analysisDate, 0);
      fatByDate.set(item.analysisDate, 0);
    }
    caloriesByDate.set(
      item.analysisDate,
      (caloriesByDate.get(item.analysisDate) ?? 0) + extractNumber(item.calories),
    );
    proteinByDate.set(
      item.analysisDate,
      (proteinByDate.get(item.analysisDate) ?? 0) + extractNumber(item.protein),
    );
    carbsByDate.set(
      item.analysisDate,
      (carbsByDate.get(item.analysisDate) ?? 0) + extractNumber(item.carbs),
    );
    fatByDate.set(
      item.analysisDate,
      (fatByDate.get(item.analysisDate) ?? 0) + extractNumber(item.fat),
    );
  }

  const caloriePoints = span.map((date, index) => {
    const dateKey = formatDateOnly(date);
    const dayIndex = date.getUTCDay();
    const calories = caloriesByDate.get(dateKey) ?? 0;
    const prevCalories = index > 0 ? caloriesByDate.get(formatDateOnly(span[index - 1])) ?? 0 : null;
    return {
      date: dateKey,
      label: WEEKDAY_LABELS[dayIndex] ?? dateKey,
      calories,
      isWeekend: dayIndex === 0 || dayIndex === 6,
      deltaFromPrevious: prevCalories == null ? null : calories - prevCalories,
    };
  });

  const proteinPoints = span.map((date) => {
    const dateKey = formatDateOnly(date);
    const dayIndex = date.getUTCDay();
    return {
      date: dateKey,
      label: WEEKDAY_LABELS[dayIndex] ?? dateKey,
      isWeekend: dayIndex === 0 || dayIndex === 6,
      value: proteinByDate.get(dateKey) ?? 0,
    };
  });
  const carbsPoints = span.map((date) => {
    const dateKey = formatDateOnly(date);
    const dayIndex = date.getUTCDay();
    return {
      date: dateKey,
      label: WEEKDAY_LABELS[dayIndex] ?? dateKey,
      isWeekend: dayIndex === 0 || dayIndex === 6,
      value: carbsByDate.get(dateKey) ?? 0,
    };
  });
  const fatPoints = span.map((date) => {
    const dateKey = formatDateOnly(date);
    const dayIndex = date.getUTCDay();
    return {
      date: dateKey,
      label: WEEKDAY_LABELS[dayIndex] ?? dateKey,
      isWeekend: dayIndex === 0 || dayIndex === 6,
      value: fatByDate.get(dateKey) ?? 0,
    };
  });

  const seriesByMetric: Record<WeeklyTrendMetric, WeeklyMetricSeries> = {
    calories: buildMetricSeries(
      'calories',
      '热量',
      'kcal',
      caloriePoints.map((point) => ({
        date: point.date,
        label: point.label,
        isWeekend: point.isWeekend,
        value: point.calories,
      })),
    ),
    protein: buildMetricSeries('protein', '蛋白质', 'g', proteinPoints),
    carbs: buildMetricSeries('carbs', '碳水', 'g', carbsPoints),
    fat: buildMetricSeries('fat', '脂肪', 'g', fatPoints),
  };

  const activePoints = caloriePoints.filter((point) => point.calories > 0);
  const activeDays = activePoints.length;
  const allCalories = caloriePoints.map((point) => point.calories);
  const averageDailyCalories = computeAverage(allCalories);
  const averageActiveDayCalories = computeAverage(activePoints.map((point) => point.calories));
  const peakPoint = getPeakPoint(activePoints);
  const lowPoint = getLowPoint(activePoints);
  const swingCalories = peakPoint && lowPoint ? Math.max(0, peakPoint.calories - lowPoint.calories) : 0;

  const half = Math.floor(caloriePoints.length / 2);
  const earlyWindow = caloriePoints.slice(0, half);
  const lateWindow = caloriePoints.slice(caloriePoints.length - half);
  const earlyAverage = computeAverage(earlyWindow.map((point) => point.calories));
  const lateAverage = computeAverage(lateWindow.map((point) => point.calories));
  const trendDelta = lateAverage - earlyAverage;
  const trendThreshold = Math.max(80, averageDailyCalories * 0.15);

  let trendDirection: WeeklyTrendDirection = 'flat';
  if (trendDelta > trendThreshold) {
    trendDirection = 'up';
  } else if (trendDelta < -trendThreshold) {
    trendDirection = 'down';
  }

  const trendLabel = trendDirection === 'up'
    ? '后半周摄入走高'
    : trendDirection === 'down'
      ? '后半周摄入回落'
      : '整周摄入相对平稳';
  const trendDetail = `后半周相比前半周变化 ${Math.round(Math.abs(trendDelta))} kcal/天。`;

  const volatilityRatio = averageActiveDayCalories > 0 ? swingCalories / averageActiveDayCalories : 0;
  const volatilityLevel: WeeklyVolatilityLevel = volatilityRatio >= 0.6
    ? 'high'
    : volatilityRatio >= 0.3
      ? 'moderate'
      : 'steady';
  const volatilityLabel = volatilityLevel === 'high'
    ? '波动较大'
    : volatilityLevel === 'moderate'
      ? '中等波动'
      : '相对平稳';

  const weekdayPoints = caloriePoints.filter((point) => !point.isWeekend);
  const weekendPoints = caloriePoints.filter((point) => point.isWeekend);
  const weekdayAverage = computeAverage(weekdayPoints.map((point) => point.calories));
  const weekendAverage = computeAverage(weekendPoints.map((point) => point.calories));
  const cycleDelta = weekendAverage - weekdayAverage;

  let cycleLabel = '工作日与周末摄入接近';
  if (cycleDelta >= 80) {
    cycleLabel = '周末摄入高于工作日';
  } else if (cycleDelta <= -80) {
    cycleLabel = '工作日摄入高于周末';
  }
  const cycleDetail = `工作日日均 ${Math.round(weekdayAverage)} kcal，周末日均 ${Math.round(weekendAverage)} kcal。`;

  const changeTags = caloriePoints
    .filter((point) => point.deltaFromPrevious != null && Math.abs(point.deltaFromPrevious) >= 120)
    .map((point) => ({
      date: point.date,
      label: point.label,
      delta: Math.round(point.deltaFromPrevious ?? 0),
      direction: (point.deltaFromPrevious ?? 0) > 0 ? 'up' as const : 'down' as const,
    }));

  const upDays = changeTags.filter((tag) => tag.direction === 'up').map((tag) => tag.label);
  const downDays = changeTags.filter((tag) => tag.direction === 'down').map((tag) => tag.label);
  let changeInsightText = '本周热量日变化整体平稳。';
  if (changeTags.length > 0) {
    const segments: string[] = [];
    if (upDays.length > 0) {
      segments.push(`本周有 ${upDays.length} 天热量明显上升，集中在${upDays.join('、')}。`);
    }
    if (downDays.length > 0) {
      segments.push(`本周有 ${downDays.length} 天热量明显下降，集中在${downDays.join('、')}。`);
    }
    changeInsightText = segments.join(' ');
  }

  return {
    points: caloriePoints,
    seriesByMetric,
    activeDays,
    averageDailyCalories,
    averageActiveDayCalories,
    peakPoint,
    lowPoint,
    swingCalories,
    trendDirection,
    trendLabel,
    trendDetail,
    volatilityLevel,
    volatilityLabel,
    cycleLabel,
    cycleDetail,
    weekdayAverage,
    weekendAverage,
    changeTags,
    changeInsightText,
  };
}
