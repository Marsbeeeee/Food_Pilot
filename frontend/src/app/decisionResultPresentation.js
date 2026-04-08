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

const MISSING_CONFIGURATION_LABELS = {
  size_or_spec: '规格',
  sugar_level: '糖度',
  milk_base: '奶基底',
  temperature: '冰量/温度',
  quantity: '份量',
  addons: '加料',
};

const TEMPLATE_LEVEL_LABELS = {
  brand_template: '品牌模板命中',
  category_template: '品类模板回退',
  generic_template: '通用模板回退',
};

const RECOMMENDATION_LEVEL_LABELS = {
  recommended: '更适合点',
  acceptable: '可以点',
  caution: '可点但有边界',
  not_recommended: '不建议点',
  needs_review: '需要复核',
};

const RISK_TAG_LABELS = {
  allergen_conflict: '过敏原冲突',
  lactose_sensitive: '乳制品风险',
  diet_style_conflict: '饮食风格冲突',
  high_calorie: '热量偏高',
  high_sugar: '糖负担偏高',
  large_portion: '份量偏大',
  low_protein: '蛋白质偏弱',
  low_confidence: '置信度偏低',
  needs_clarification: '信息待补充',
  combo_incomplete: '套餐信息不完整',
  source_ambiguous: '来源不明确',
  missing_product_detail: '商品信息不完整',
  missing_product_subject: '缺少商品主体',
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
    description: decisionCard?.adaptationNote ?? description ?? null,
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
    templateVersionLabel: estimationMeta?.templateVersion
      ? `模板版本：${estimationMeta.templateVersion}`
      : null,
    configVersionLabel: estimationMeta?.configVersion
      ? `规则版本：${estimationMeta.configVersion}`
      : null,
    fallbackPathLabels: mapFallbackPath(estimationMeta?.fallbackPath),
    confidenceReasons: Array.isArray(estimationMeta?.confidenceReasons)
      ? estimationMeta.confidenceReasons
      : [],
    appliedRules: Array.isArray(estimationMeta?.appliedRules)
      ? estimationMeta.appliedRules
      : [],
    missingConfiguration: Array.isArray(estimationMeta?.missingConfiguration)
      ? estimationMeta.missingConfiguration
      : [],
    missingConfigurationLabels: mapMissingConfiguration(estimationMeta?.missingConfiguration),
    recommendationLevel: decisionCard?.recommendationLevel ?? 'needs_review',
    recommendationLabel: mapRecommendationLevel(decisionCard?.recommendationLevel),
    riskTags: Array.isArray(decisionCard?.riskTags) ? decisionCard.riskTags : [],
    riskLabels: mapRiskTags(decisionCard?.riskTags),
    adaptationNote: decisionCard?.adaptationNote ?? description ?? null,
    adjustments: Array.isArray(decisionCard?.adjustments) ? decisionCard.adjustments : [],
    alternatives: Array.isArray(decisionCard?.alternatives) ? decisionCard.alternatives : [],
    isPersonalized: Boolean(decisionCard?.isPersonalized),
    personalizationNote: decisionCard?.personalizationNote ?? null,
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

function mapMissingConfiguration(missingConfiguration) {
  if (!Array.isArray(missingConfiguration)) {
    return [];
  }

  return missingConfiguration.map((field) => MISSING_CONFIGURATION_LABELS[field] ?? field);
}

function mapFallbackPath(fallbackPath) {
  if (!Array.isArray(fallbackPath)) {
    return [];
  }

  return fallbackPath.map((step) => TEMPLATE_LEVEL_LABELS[step] ?? step);
}

function mapRecommendationLevel(level) {
  return RECOMMENDATION_LEVEL_LABELS[level] ?? '需要复核';
}

function mapRiskTags(riskTags) {
  if (!Array.isArray(riskTags)) {
    return [];
  }

  return riskTags.map((tag) => RISK_TAG_LABELS[tag] ?? tag);
}
