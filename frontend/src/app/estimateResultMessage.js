import { buildDecisionResultPresentation } from './decisionResultPresentation.js';

function cloneItems(items) {
  return Array.isArray(items) ? items.map((item) => ({ ...item })) : [];
}

function resolveTotalCalories(result) {
  return result?.total ?? result?.totalCalories ?? result?.total_calories;
}

export function buildEstimateMessageFromResult(result, options = {}) {
  const payload = {
    title: result?.title,
    confidence: result?.confidence,
    description: result?.description,
    items: cloneItems(result?.items),
    total: resolveTotalCalories(result),
    suggestion: result?.suggestion ?? null,
    decisionCard: result?.decisionCard ?? null,
  };

  return {
    id: options.id,
    role: 'assistant',
    messageType: 'meal_estimate',
    content: options.content ?? result?.suggestion ?? '',
    payload,
    decisionCard: payload.decisionCard ?? undefined,
    time: options.time ?? '',
    createdAt: options.createdAt,
    isResult: true,
    title: payload.title,
    confidence: payload.confidence,
    description: payload.description,
    items: payload.items,
    total: payload.total,
  };
}

export function buildEstimateResultPresentation(result, options = {}) {
  return buildDecisionResultPresentation({
    title: result?.title,
    confidence: result?.confidence,
    description: result?.description,
    items: cloneItems(result?.items),
    total: resolveTotalCalories(result),
    suggestion: result?.suggestion ?? null,
    content: options.content ?? result?.suggestion ?? '',
    decisionCard: result?.decisionCard ?? null,
  });
}
