const ESTIMATE_COPY = {
  ingredientColumnLabel: '食材',
  portionColumnLabel: '份量',
  energyColumnLabel: '热量',
  proteinColumnLabel: '蛋白质',
  carbsColumnLabel: '碳水',
  fatColumnLabel: '脂肪',
  totalLabel: '总热量',
};

const CLARIFICATION_COPY = {
  eyebrow: '需要澄清',
  fallbackTitle: '商品信息待补充',
  badgeLabel: '待确认',
  riskLabel: '当前风险',
  actionLabel: '建议补充',
  missingFieldLabel: '缺少信息',
  comboLabel: '套餐拆分',
};

const MATCH_LEVEL_LABELS = {
  brand_product: '已识别品牌与商品',
  brand_only: '仅识别到品牌',
  category_product: '已识别品类与商品',
  category_only: '仅识别到品类',
  private_item: '按非标准商品处理',
  source_ambiguous: '按来源不明确商品处理',
  unknown: '商品理解不足',
};

const MISSING_FIELD_LABELS = {
  product_subject: '商品主体',
  product_name: '具体商品名',
  combo_items: '套餐构成',
  category: '品类',
  brand: '品牌',
  size_or_spec: '规格',
  sugar_level: '糖度',
  temperature: '冰热',
};

const TEMPLATE_LEVEL_LABELS = {
  brand_template: '品牌模板命中',
  category_template: '品类模板回退',
  generic_template: '通用模板回退',
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
  const estimationMeta = decisionCard?.estimationMeta ?? null;
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
    normalizedProduct,
    estimationMeta,
    summaryBadges: buildSummaryBadges(normalizedProduct),
    templateHitLabel: estimationMeta?.sourceType
      ? TEMPLATE_LEVEL_LABELS[estimationMeta.sourceType] ?? estimationMeta.sourceType
      : null,
    templateSourceLabel: estimationMeta?.sourceLabel ?? null,
    fallbackPathLabels: mapFallbackPath(estimationMeta?.fallbackPath),
    confidenceReasons: Array.isArray(estimationMeta?.confidenceReasons)
      ? estimationMeta.confidenceReasons
      : [],
    appliedRules: Array.isArray(estimationMeta?.appliedRules)
      ? estimationMeta.appliedRules
      : [],
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
  const comboItems = Array.isArray(normalizedProduct?.comboItems)
    ? normalizedProduct.comboItems.map((item) => item?.productName).filter(Boolean)
    : [];

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
    normalizedProduct,
    summaryBadges: buildSummaryBadges(normalizedProduct),
    missingFields: mapMissingFields(normalizedProduct?.missingFields),
    comboItems,
    matchLevelLabel: normalizedProduct?.matchLevel
      ? MATCH_LEVEL_LABELS[normalizedProduct.matchLevel] ?? normalizedProduct.matchLevel
      : null,
    needsClarification: true,
    analysisEligible: decisionCard?.analysisEligible ?? null,
    saveEligible: decisionCard?.saveEligible ?? null,
    ...CLARIFICATION_COPY,
  };
}

function buildSummaryBadges(normalizedProduct) {
  if (!normalizedProduct) {
    return [];
  }

  const values = [
    normalizedProduct.brandName,
    normalizedProduct.categoryName,
    normalizedProduct.sizeOrSpec,
    normalizedProduct.sugarLevel,
    normalizedProduct.milkBase,
    normalizedProduct.temperature,
  ].filter(Boolean);

  return [...new Set(values)];
}

function mapMissingFields(missingFields) {
  if (!Array.isArray(missingFields)) {
    return [];
  }

  return missingFields.map((field) => MISSING_FIELD_LABELS[field] ?? field);
}

function mapFallbackPath(fallbackPath) {
  if (!Array.isArray(fallbackPath)) {
    return [];
  }

  return fallbackPath.map((step) => TEMPLATE_LEVEL_LABELS[step] ?? step);
}
