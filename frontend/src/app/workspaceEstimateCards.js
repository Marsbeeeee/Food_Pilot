const COMPONENT_TITLE_HINTS = [
  '\u6cb9',
  '\u9171',
  '\u8c03\u5473',
  '\u6d47\u5934',
  '\u914d\u6599',
  '\u8089\u997c',
  '\u9762\u5305',
  '\u997c\u5e95',
  '\u852c\u83dc',
  '\u751f\u83dc',
  '\u9999\u6599',
  '\u8c03\u6599',
];

const BEVERAGE_HINTS = [
  '\u6c34',
  '\u996e',
  '\u6c64',
  '\u5496\u5561',
  '\u8336',
  '\u8c46\u6d46',
  '\u53ef\u4e50',
  '\u82cf\u6253',
  '\u6c7d\u6c34',
  '\u5976\u8336',
  '\u62ff\u94c1',
  '\u7f8e\u5f0f',
  '\u679c\u6c41',
];

const MULTI_FOOD_CONNECTOR_RE = /(?:\u642d\u914d|\u4ee5\u53ca|\u8fd8\u6709|\u52a0|\u914d|[+\u3001,\uFF0C\u548C])/g;

const LEADING_CONTEXT_RE = /^(?:\u4eca\u5929|\u4eca\u65e5|\u6628\u5929|\u4eca\u665a|\u521a\u521a|\u6211)?(?:\u65e9\u4e0a|\u4e2d\u5348|\u665a\u4e0a|\u65e9\u9910|\u5348\u9910|\u665a\u9910)?(?:\u5403\u4e86|\u559d\u4e86|\u5403|\u559d)?/;
const LEADING_QUANTITY_RE = /^(?:[\u4e00\u4e8c\u4e24\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u534a\d]+)(?:\u676f|\u7897|\u4efd|\u4e2a|\u74f6|\u7f50|\u7247|\u4e32|\u6839|\u5757|\u76d8|\u76d2)/;

function normalizeText(value) {
  if (!value) {
    return '';
  }

  return String(value)
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[()\uFF08\uFF09]/g, '');
}

function stripParenthetical(value) {
  if (!value) {
    return '';
  }

  return String(value)
    .replace(/\uFF08[^\uFF09]*\uFF09/g, '')
    .replace(/\([^)]*\)/g, '')
    .trim();
}

function includesComponentHint(value) {
  const normalized = normalizeText(value);
  return COMPONENT_TITLE_HINTS.some((hint) => normalized.includes(normalizeText(hint)));
}

function isBeverageText(value) {
  const normalized = normalizeText(value);
  return BEVERAGE_HINTS.some((hint) => normalized.includes(normalizeText(hint)));
}

function isSingletonSelfBlock(block) {
  const items = Array.isArray(block?.items) ? block.items : [];
  if (items.length !== 1) {
    return false;
  }

  const titleNormalized = normalizeText(block?.title);
  const firstItemName = normalizeText(items[0]?.name);
  return Boolean(titleNormalized) && titleNormalized === firstItemName;
}

function isLikelyMentionedByUser(title, mealDescriptionNormalized) {
  if (!title || !mealDescriptionNormalized) {
    return false;
  }

  const normalizedTitle = normalizeText(title);
  if (!normalizedTitle) {
    return false;
  }
  if (mealDescriptionNormalized.includes(normalizedTitle)) {
    return true;
  }

  const stripped = normalizeText(stripParenthetical(title));
  return Boolean(stripped) && mealDescriptionNormalized.includes(stripped);
}

function sanitizeMealSegment(segment) {
  if (!segment) {
    return '';
  }

  return String(segment)
    .trim()
    .replace(LEADING_CONTEXT_RE, '')
    .replace(LEADING_QUANTITY_RE, '')
    .replace(/^(?:\u4e00|\u4e24|\u4e8c)?(?:\u676f|\u7897|\u4efd|\u4e2a|\u74f6|\u7f50)/, '')
    .replace(/^(?:\u4e00\u676f|\u4e00\u7897|\u4e00\u4efd|\u4e00\u4e2a|\u4e00\u74f6|\u4e00\u7f50)/, '')
    .trim();
}

function inferTopLevelFoods(mealDescription) {
  const text = String(mealDescription ?? '').trim();
  if (!text) {
    return [];
  }

  const rawSegments = text
    .split(MULTI_FOOD_CONNECTOR_RE)
    .map((segment) => sanitizeMealSegment(segment))
    .filter(Boolean);

  const deduped = [];
  const seen = new Set();
  for (const segment of rawSegments) {
    const normalized = normalizeText(segment);
    if (!normalized || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    deduped.push({
      title: segment,
      normalized,
      isBeverage: isBeverageText(segment),
    });
  }

  return deduped;
}

function extractKcal(value) {
  if (!value) {
    return 0;
  }
  const matched = String(value).match(/(\d+(?:\.\d+)?)/);
  if (!matched) {
    return 0;
  }
  const parsed = Number.parseFloat(matched[1]);
  return Number.isFinite(parsed) ? parsed : 0;
}

function buildGroupedCard(title, blocks) {
  const items = [];
  let total = 0;
  let confidence = '';
  let description = '';

  for (const block of blocks) {
    total += extractKcal(block?.total);
    if (!confidence && block?.confidence) {
      confidence = String(block.confidence);
    }
    if (!description && block?.description) {
      description = String(block.description);
    }
    if (Array.isArray(block?.items) && block.items.length) {
      items.push(...block.items);
    }
  }

  return {
    title,
    confidence: confidence || undefined,
    description: description || undefined,
    items,
    total: total > 0 ? `${Math.round(total)} kcal` : (blocks[0]?.total ?? '0 kcal'),
  };
}

function groupEstimatesByTopLevelFoods(estimates, topFoods) {
  if (!topFoods.length) {
    return estimates;
  }

  const groups = topFoods.map(() => []);
  const unassigned = [];
  const beverageTargetIndex = topFoods.findIndex((food) => food.isBeverage);
  const primaryFoodIndex = topFoods.findIndex((food) => !food.isBeverage);

  for (const block of estimates) {
    const title = String(block?.title ?? '').trim();
    const normalizedTitle = normalizeText(title);
    const isBeverage = isBeverageText(title);

    let targetIndex = -1;
    let bestScore = -1;

    for (let index = 0; index < topFoods.length; index += 1) {
      const food = topFoods[index];
      let score = 0;
      if (normalizedTitle.includes(food.normalized) || food.normalized.includes(normalizedTitle)) {
        score += 10;
      }
      if (food.isBeverage === isBeverage) {
        score += 2;
      }
      if (score > bestScore) {
        bestScore = score;
        targetIndex = index;
      }
    }

    if (bestScore <= 0) {
      if (isBeverage && beverageTargetIndex >= 0) {
        groups[beverageTargetIndex].push(block);
      } else if (primaryFoodIndex >= 0) {
        groups[primaryFoodIndex].push(block);
      } else {
        unassigned.push(block);
      }
      continue;
    }

    groups[targetIndex].push(block);
  }

  if (unassigned.length > 0) {
    for (const block of unassigned) {
      const leastLoadedIndex = groups.reduce(
        (best, current, index) => (current.length < groups[best].length ? index : best),
        0,
      );
      groups[leastLoadedIndex].push(block);
    }
  }

  for (let index = 0; index < groups.length; index += 1) {
    if (groups[index].length > 0) {
      continue;
    }
    const donorIndex = groups.reduce(
      (best, current, currentIndex) => (current.length > groups[best].length ? currentIndex : best),
      0,
    );
    if (groups[donorIndex].length <= 1) {
      continue;
    }
    groups[index].push(groups[donorIndex].pop());
  }

  return topFoods
    .map((food, index) => buildGroupedCard(food.title, groups[index]))
    .filter((card) => Array.isArray(card.items) && card.items.length > 0);
}

export function resolveEstimateBlocksForRendering({
  estimates,
  mealDescription,
} = {}) {
  if (!Array.isArray(estimates) || estimates.length === 0) {
    return null;
  }

  if (estimates.length === 1) {
    return null;
  }

  const allSingletonSelfBlocks = estimates.every((block) => isSingletonSelfBlock(block));
  if (!allSingletonSelfBlocks) {
    return estimates;
  }

  const topFoods = inferTopLevelFoods(mealDescription);
  if (topFoods.length >= 2) {
    if (estimates.length > topFoods.length) {
      const grouped = groupEstimatesByTopLevelFoods(estimates, topFoods);
      if (grouped.length >= 2) {
        return grouped;
      }
    }
    return estimates;
  }

  const mealDescriptionNormalized = normalizeText(mealDescription);
  if (!mealDescriptionNormalized) {
    return estimates;
  }

  let unmentionedCount = 0;
  let componentHintCount = 0;
  for (const block of estimates) {
    const title = String(block?.title ?? '').trim();
    if (includesComponentHint(title)) {
      componentHintCount += 1;
    }
    if (!isLikelyMentionedByUser(title, mealDescriptionNormalized)) {
      unmentionedCount += 1;
    }
  }

  if (componentHintCount > 0 && unmentionedCount > 0) {
    return null;
  }
  if (unmentionedCount >= Math.ceil(estimates.length / 2)) {
    return null;
  }

  return estimates;
}
