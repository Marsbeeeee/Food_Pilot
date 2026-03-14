export function buildFoodLogEditPayload(draft) {
  const ingredients = draft.ingredients.map((ingredient, index) => ({
    name: normalizeRequiredText(ingredient.name, `Ingredient ${index + 1} name`),
    portion: normalizeRequiredText(ingredient.portion, `Ingredient ${index + 1} portion`),
    energy: normalizeEnergyText(ingredient.energy, `Ingredient ${index + 1} energy`),
  }));

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

export function sortFoodLogEntries(logEntries) {
  return [...logEntries].sort((left, right) => (
    resolveSortTimestamp(right).getTime() - resolveSortTimestamp(left).getTime()
  ));
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
