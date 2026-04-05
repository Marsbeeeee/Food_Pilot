const ESTIMATE_COPY = {
  ingredientColumnLabel: '椋熸潗',
  portionColumnLabel: '浠介噺',
  energyColumnLabel: '浼扮畻鐑噺',
  proteinColumnLabel: '铔嬬櫧璐?',
  carbsColumnLabel: '纰虫按',
  fatColumnLabel: '鑴傝偑',
  totalLabel: '浼扮畻鎬荤儹閲?',
};

const CLARIFICATION_COPY = {
  eyebrow: '淇℃伅婢勬竻',
  fallbackTitle: '闇€瑕佽ˉ鍏呬俊鎭?',
  badgeLabel: '寰呮緞娓?',
  riskLabel: '椋庨櫓鏍囩',
  actionLabel: '寤鸿琛ュ厖',
};

export function buildDecisionResultPresentation({
  title,
  confidence,
  description,
  items,
  total,
  estimates = null,
  suggestion = null,
  content = '',
  decisionCard = null,
} = {}) {
  if (decisionCard?.needsClarification) {
    return buildClarificationResultPresentation({
      content,
      decisionCard,
    });
  }

  const normalizedProduct = decisionCard?.normalizedProduct ?? null;
  const nutritionEstimate = decisionCard?.nutritionEstimate ?? null;
  const firstAdjustment = Array.isArray(decisionCard?.adjustments)
    ? decisionCard.adjustments[0]
    : null;

  return {
    variant: 'meal_estimate',
    title: title ?? normalizedProduct?.productName,
    confidence: confidence ?? decisionCard?.confidenceLevel,
    description: description ?? decisionCard?.adaptationNote,
    items: items ?? nutritionEstimate?.items ?? [],
    total: total ?? nutritionEstimate?.totalCalories,
    estimates,
    suggestion: suggestion ?? firstAdjustment ?? null,
    decisionCard,
    needsClarification: false,
    analysisEligible: decisionCard?.analysisEligible ?? null,
    saveEligible: decisionCard?.saveEligible ?? null,
    ...ESTIMATE_COPY,
  };
}

export function buildClarificationResultPresentation({
  content = '',
  decisionCard = null,
} = {}) {
  const normalizedProduct = decisionCard?.normalizedProduct ?? null;

  return {
    variant: 'clarification',
    title: normalizedProduct?.productName ?? decisionCard?.inputSummary ?? CLARIFICATION_COPY.fallbackTitle,
    content,
    description: decisionCard?.adaptationNote ?? null,
    confidence: decisionCard?.confidenceLevel ?? 'unknown',
    inputSummary: decisionCard?.inputSummary ?? '',
    recommendationLevel: decisionCard?.recommendationLevel ?? 'needs_review',
    riskTags: Array.isArray(decisionCard?.riskTags) ? decisionCard.riskTags : [],
    adjustments: Array.isArray(decisionCard?.adjustments) ? decisionCard.adjustments : [],
    decisionCard,
    needsClarification: true,
    analysisEligible: decisionCard?.analysisEligible ?? null,
    saveEligible: decisionCard?.saveEligible ?? null,
    ...CLARIFICATION_COPY,
  };
}
