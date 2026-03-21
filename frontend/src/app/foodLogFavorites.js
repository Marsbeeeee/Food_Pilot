export function buildFoodLogEditPayload(draft) {
  const ingredients = draft.ingredients.map((ingredient, index) => {
    const item = {
      name: normalizeRequiredText(ingredient.name, `Ingredient ${index + 1} name`),
      portion: normalizeRequiredText(ingredient.portion, `Ingredient ${index + 1} portion`),
      energy: normalizeEnergyText(ingredient.energy, `Ingredient ${index + 1} energy`),
    };
    if (ingredient.protein) {
      item.protein = ingredient.protein;
    }
    if (ingredient.carbs) {
      item.carbs = ingredient.carbs;
    }
    if (ingredient.fat) {
      item.fat = ingredient.fat;
    }
    return item;
  });

  if (ingredients.length === 0) {
    throw new Error('Add at least one ingredient before saving.');
  }

  return {
    resultTitle: normalizeRequiredText(draft.name, 'Meal name'),
    resultDescription: normalizeRequiredText(draft.description, 'Description'),
    totalCalories: normalizeEnergyText(draft.calories, 'Total calories'),
    ingredients,
  };
}

export function buildFoodLogCollectionStats(logEntries, now = new Date()) {
  const windowStart = new Date(now);
  windowStart.setHours(0, 0, 0, 0);
  windowStart.setDate(windowStart.getDate() - 6);

  let updatedThisWeek = 0;
  let chatLinked = 0;

  logEntries.forEach((entry) => {
    if (entry.sessionId) {
      chatLinked += 1;
    }

    const savedAt = parseSavedAt(entry.savedAt);
    if (savedAt && savedAt >= windowStart) {
      updatedThisWeek += 1;
    }
  });

  return {
    updatedThisWeek,
    chatLinked,
  };
}

export function sortFoodLogEntries(logEntries, sort = 'created_desc') {
  const sorted = [...logEntries];
  if (sort === 'created_asc') {
    return sorted.sort((left, right) => (
      resolveSortTimestamp(left).getTime() - resolveSortTimestamp(right).getTime()
    ));
  }
  if (sort === 'calories_desc') {
    return sorted.sort((left, right) => (
      compareByCalories(left, right, 'desc') || (
        resolveSortTimestamp(right).getTime() - resolveSortTimestamp(left).getTime()
      )
    ));
  }
  if (sort === 'calories_asc') {
    return sorted.sort((left, right) => (
      compareByCalories(left, right, 'asc') || (
        resolveSortTimestamp(left).getTime() - resolveSortTimestamp(right).getTime()
      )
    ));
  }
  if (sort === 'updated_desc') {
    return sorted.sort((left, right) => (
      resolveUpdatedSortTimestamp(right).getTime() - resolveUpdatedSortTimestamp(left).getTime()
    ));
  }

  return sorted.sort((left, right) => (
    resolveSortTimestamp(right).getTime() - resolveSortTimestamp(left).getTime()
  ));
}

export function filterFoodLogEntries(logEntries, filters = {}) {
  const {
    query = '',
    sourceType = 'all',
    hasImage = 'all',
    dateFrom = '',
    dateTo = '',
    sort = 'created_desc',
    caloriePreset = 'any',
    minCalories = '',
    maxCalories = '',
  } = filters;

  const normalizedQuery = normalizeSearchText(query);
  const queryTokens = normalizedQuery ? normalizedQuery.split(' ').filter(Boolean) : [];
  const rangeStart = parseDateBoundary(dateFrom);
  const rangeEndExclusive = parseDateBoundary(dateTo, { nextDay: true });
  const parsedMinCalories = parseCaloriesInput(minCalories);
  const parsedMaxCalories = parseCaloriesInput(maxCalories);
  const hasCustomCalorieRange = parsedMinCalories !== null || parsedMaxCalories !== null;

  const filtered = logEntries.filter((entry) => {
    if (sourceType !== 'all' && entry.sourceType !== sourceType) {
      return false;
    }

    const imageExists = hasImageValue(entry.image);
    if (hasImage === 'with_image' && !imageExists) {
      return false;
    }
    if (hasImage === 'without_image' && imageExists) {
      return false;
    }

    const mealTimestamp = resolveMealTimestamp(entry);
    if (rangeStart && mealTimestamp.getTime() < rangeStart.getTime()) {
      return false;
    }
    if (rangeEndExclusive && mealTimestamp.getTime() >= rangeEndExclusive.getTime()) {
      return false;
    }

    const entryCalories = parseCaloriesInput(entry.calories);
    if (hasCustomCalorieRange) {
      if (!matchesCustomCalorieRange(entryCalories, parsedMinCalories, parsedMaxCalories)) {
        return false;
      }
    } else if (!matchesCaloriePreset(entryCalories, caloriePreset)) {
      return false;
    }

    if (queryTokens.length > 0) {
      const haystack = buildSearchHaystack(entry);
      if (!queryTokens.every((token) => haystack.includes(token))) {
        return false;
      }
    }

    return true;
  });

  return sortFoodLogEntries(filtered, sort);
}

export function formatSavedMoment(value) {
  const timestamp = parseSavedAt(value);
  if (!timestamp) {
    return {
      date: '--',
      time: '--:--',
    };
  }

  return {
    date: timestamp.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    time: timestamp.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    }),
  };
}

export function parseSavedAt(value) {
  if (!value) {
    return null;
  }

  const normalized = value.replace(' ', 'T');
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function resolveSortTimestamp(entry) {
  return parseSavedAt(entry.savedAt) ?? new Date(0);
}

function resolveUpdatedSortTimestamp(entry) {
  return parseSavedAt(entry.updatedAt) ?? resolveSortTimestamp(entry);
}

function resolveMealTimestamp(entry) {
  return parseSavedAt(entry.mealOccurredAt) ?? resolveSortTimestamp(entry);
}

function parseDateBoundary(value, { nextDay = false } = {}) {
  if (!value || typeof value !== 'string') {
    return null;
  }

  const normalized = value.trim();
  if (!normalized) {
    return null;
  }

  const parsed = new Date(`${normalized}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  if (nextDay) {
    const next = new Date(parsed);
    next.setDate(next.getDate() + 1);
    return next;
  }

  return parsed;
}

function hasImageValue(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function buildSearchHaystack(entry) {
  const ingredientNames = Array.isArray(entry.breakdown)
    ? entry.breakdown.map((item) => item?.name ?? '').join(' ')
    : '';
  return normalizeSearchText(
    [entry.name, entry.description, ingredientNames]
      .filter(Boolean)
      .join(' '),
  );
}

function normalizeSearchText(value) {
  if (typeof value !== 'string') {
    return '';
  }
  return value.trim().replace(/\s+/g, ' ').toLocaleLowerCase();
}

function parseCaloriesInput(value) {
  if (typeof value === 'number') {
    return Number.isFinite(value) && value >= 0 ? value : null;
  }
  if (typeof value !== 'string') {
    return null;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }

  const matched = trimmed.match(/-?\d+(?:\.\d+)?/);
  if (!matched) {
    return null;
  }

  const parsed = Number.parseFloat(matched[0]);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
}

function matchesCaloriePreset(entryCalories, caloriePreset) {
  if (caloriePreset === 'any') {
    return true;
  }

  if (entryCalories === null) {
    return false;
  }

  if (caloriePreset === 'under_200') {
    return entryCalories < 200;
  }
  if (caloriePreset === '200_500') {
    return entryCalories >= 200 && entryCalories <= 500;
  }
  if (caloriePreset === '500_800') {
    return entryCalories >= 500 && entryCalories <= 800;
  }
  if (caloriePreset === '800_plus') {
    return entryCalories >= 800;
  }

  return true;
}

function matchesCustomCalorieRange(entryCalories, minCalories, maxCalories) {
  if (entryCalories === null) {
    return false;
  }
  if (minCalories !== null && entryCalories < minCalories) {
    return false;
  }
  if (maxCalories !== null && entryCalories > maxCalories) {
    return false;
  }
  return true;
}

function compareByCalories(left, right, direction = 'asc') {
  const leftCalories = parseCaloriesInput(left?.calories);
  const rightCalories = parseCaloriesInput(right?.calories);
  if (leftCalories === null && rightCalories === null) {
    return 0;
  }
  if (leftCalories === null) {
    return 1;
  }
  if (rightCalories === null) {
    return -1;
  }
  if (direction === 'desc') {
    return rightCalories - leftCalories;
  }
  return leftCalories - rightCalories;
}

function normalizeRequiredText(value, fieldLabel) {
  const normalized = value.trim().replace(/\s+/g, ' ');
  if (!normalized) {
    throw new Error(`${fieldLabel} cannot be empty.`);
  }
  return normalized;
}

function normalizeEnergyText(value, fieldLabel) {
  const normalized = normalizeRequiredText(value, fieldLabel);
  return /\bkcal\b/i.test(normalized) ? normalized : `${normalized} kcal`;
}
