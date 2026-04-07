const CONFIDENCE_LABELS = {
  high: '高置信',
  medium: '中等置信',
  low: '低置信',
  unknown: '待确认',
};

const MATCH_LEVEL_LABELS = {
  brand_product: '品牌商品已命中',
  brand_only: '仅识别到品牌',
  category_product: '品类商品已命中',
  category_only: '仅识别到品类',
  private_item: '按私有商品处理',
  source_ambiguous: '按来源不明确处理',
  unknown: '商品理解不足',
};

const ITEM_ROLE_LABELS = {
  top_level_item: '主结果',
  single_item: '单品',
  main_item: '主食',
  combo_item: '组成项',
  combo_side: '配餐',
  combo_drink: '饮品',
  component: '组成项',
  unknown: '待确认',
};

const PRODUCT_SCOPE_LABELS = {
  single_item: '单品决策',
  multi_item: '套餐 / 多组成项',
  unknown: '对象待确认',
};

function getDecisionTone(decisionCard) {
  if (!decisionCard) {
    return 'neutral';
  }
  if (decisionCard.needsClarification) {
    return 'clarification';
  }
  if (decisionCard.confidenceLevel === 'low' || (decisionCard.riskTags || []).includes('low_confidence')) {
    return 'low_confidence';
  }
  return 'success';
}

function getSaveTarget(decisionCard) {
  if (!decisionCard) {
    return {
      title: '保存信息待补齐',
      detail: '当前结果缺少稳定的结构化归档字段，暂时只作为聊天结果展示。',
    };
  }

  if (!decisionCard.saveEligible) {
    return {
      title: '暂不可保存',
      detail: '当前结果还缺少可归档的营养快照或商品信息，建议先补充再保存。',
    };
  }

  const normalizedProduct = decisionCard.normalizedProduct || {};
  const matchLevel = normalizedProduct.matchLevel || 'unknown';

  if (matchLevel === 'source_ambiguous') {
    return {
      title: '未明确来源容器',
      detail: '当前估算允许保存，但会先进入未明确来源容器，后续可再补来源信息。',
    };
  }

  if (matchLevel === 'private_item') {
    return {
      title: '用户私有商品容器',
      detail: '这条结果会按你的私有商品归档，不强行映射公共品牌商品目录。',
    };
  }

  const brandName = normalizedProduct.brandName;
  const categoryName = normalizedProduct.categoryName;
  const productName = normalizedProduct.productName;
  const catalogLabel = [brandName, categoryName, productName].filter(Boolean).join(' / ');

  return {
    title: '正式分类容器',
    detail: catalogLabel
      ? `保存后会按 ${catalogLabel} 归档，便于在收藏夹继续回看和复用。`
      : '保存后会进入正式分类容器，并保留当前识别到的分类标签。',
  };
}

function getAnalysisMeta(decisionCard, { isSaved = false } = {}) {
  if (!decisionCard) {
    return {
      title: '分析信息待补齐',
      detail: '当前结果缺少分析准入字段，暂时无法判断是否可以进入营养分析。',
    };
  }

  if (!decisionCard.analysisEligible) {
    if (decisionCard.needsClarification) {
      return {
        title: '暂不可加入分析',
        detail: '这条结果还需要补充商品主体、规格或套餐构成，暂时不能进入 Insights。',
      };
    }

    if (decisionCard.saveEligible) {
      return {
        title: '可保存但暂不分析',
        detail: '这条结果允许归档，但目前还不满足稳定分析对象的准入条件。',
      };
    }

    return {
      title: '暂不可加入分析',
      detail: '先补充信息并重新分析，得到稳定对象后再加入 Insights。',
    };
  }

  if (!isSaved) {
    return {
      title: '保存后可加入分析',
      detail: '加入分析会基于已保存的营养快照进入今日分析篮子，不会直接把聊天结果当分析输入。',
    };
  }

  return {
    title: '可加入今日分析',
    detail: '这条结果已经具备分析准入条件，可直接加入今日 Insights 篮子。',
  };
}

export function getDecisionRoleLabel(itemRole) {
  return ITEM_ROLE_LABELS[itemRole] || itemRole || '待确认';
}

export function getDecisionScopeLabel(productScope) {
  return PRODUCT_SCOPE_LABELS[productScope] || productScope || '待确认';
}

export function getDecisionMatchLevelLabel(matchLevel) {
  return MATCH_LEVEL_LABELS[matchLevel] || matchLevel || '待确认';
}

export function buildDecisionArchiveEntries(decisionCard) {
  if (!decisionCard) {
    return [];
  }

  const normalizedProduct = decisionCard.normalizedProduct || {};
  const entries = [
    ['品类', normalizedProduct.categoryName],
    ['品牌', normalizedProduct.brandName],
    ['商品', normalizedProduct.productName],
    ['角色', getDecisionRoleLabel(normalizedProduct.itemRole)],
    ['范围', getDecisionScopeLabel(normalizedProduct.productScope)],
    ['识别', getDecisionMatchLevelLabel(normalizedProduct.matchLevel)],
  ];

  return entries
    .filter(([, value]) => Boolean(value))
    .map(([label, value]) => ({ label, value }));
}

export function buildDecisionAnalysisAction(
  decisionCard,
  {
    isSaved = false,
    canSaveFromWorkspace = false,
    hasMealDescription = false,
  } = {},
) {
  if (!decisionCard) {
    return {
      label: '分析信息待补齐',
      disabled: true,
      helperText: '当前结果缺少稳定分析字段，暂不展示分析动作。',
    };
  }

  if (!decisionCard.analysisEligible) {
    const helperText = decisionCard.needsClarification
      ? '先补充商品信息，再尝试重新分析。'
      : '当前结果允许保存，但还不满足加入分析条件。';

    return {
      label: '当前不可加入分析',
      disabled: true,
      helperText,
    };
  }

  if (isSaved) {
    return {
      label: '加入今日分析',
      disabled: false,
      helperText: '会把这条已保存结果加入今天的 Insights 分析篮子。',
    };
  }

  if (canSaveFromWorkspace && hasMealDescription) {
    return {
      label: '保存并加入分析',
      disabled: false,
      helperText: '会先保存到收藏夹，再加入今天的分析篮子。',
    };
  }

  return {
    label: '先保存后分析',
    disabled: true,
    helperText: '加入分析依赖已保存的营养快照，当前还不能直接执行。',
  };
}

export function buildDecisionWorkspaceSummary(
  decisionCard,
  {
    isSaved = false,
    canSaveFromWorkspace = false,
    hasMealDescription = false,
  } = {},
) {
  const tone = getDecisionTone(decisionCard);
  const normalizedProduct = decisionCard?.normalizedProduct || {};

  const toneCopy = {
    clarification: {
      eyebrow: '需要补充信息',
      title: '先补全再判断',
      description: '当前结果还不能当作稳定结论，先把关键字段补齐。',
    },
    low_confidence: {
      eyebrow: '低置信提醒',
      title: '可以继续参考，但先别把它当最终答案',
      description: '当前识别和估算已经成形，但仍有较高不确定性，需要谨慎使用动作入口。',
    },
    success: {
      eyebrow: '本次决策',
      title: '可以直接用于点单判断',
      description: '主结论、风险和动作入口都已整理成工作台视图，可直接扫读。',
    },
    neutral: {
      eyebrow: '结果概览',
      title: '等待结构化结果',
      description: '当前结果仍以基础文本为主，结构化字段尚未齐备。',
    },
  }[tone];

  return {
    tone,
    eyebrow: toneCopy.eyebrow,
    title: toneCopy.title,
    description: toneCopy.description,
    confidenceLabel: CONFIDENCE_LABELS[decisionCard?.confidenceLevel] || '待确认',
    archiveEntries: buildDecisionArchiveEntries(decisionCard),
    specBadges: [
      normalizedProduct.sizeOrSpec,
      normalizedProduct.sugarLevel,
      normalizedProduct.milkBase,
      normalizedProduct.temperature,
      normalizedProduct.quantity,
    ].filter(Boolean),
    saveTarget: getSaveTarget(decisionCard),
    analysisMeta: getAnalysisMeta(decisionCard, { isSaved }),
    analysisAction: buildDecisionAnalysisAction(decisionCard, {
      isSaved,
      canSaveFromWorkspace,
      hasMealDescription,
    }),
  };
}
