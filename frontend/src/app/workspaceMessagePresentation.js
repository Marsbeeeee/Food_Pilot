import { buildDecisionResultPresentation } from './decisionResultPresentation.js';

const RECOMMENDATION_COPY = {
  eyebrow: '楗鎺ㄨ崘',
  fallbackTitle: '鎺ㄨ崘寤鸿',
  badgeLabel: '寤鸿',
  reasonLabel: '涓轰粈涔堣繖鏍烽€?',
  contentLabel: '鎺ㄨ崘鎬庝箞鍚?',
};

export function buildWorkspaceMessagePresentation(message) {
  const variant = message?.messageType ?? 'text';
  const decisionCard = message?.payload?.decisionCard ?? message?.decisionCard ?? null;

  if (variant === 'meal_estimate') {
    return buildDecisionResultPresentation({
      title: message.title,
      confidence: message.confidence,
      description: message.description,
      items: message.items,
      total: message.total,
      estimates: message.estimates ?? null,
      suggestion: message.payload?.suggestion ?? null,
      content: message.content ?? '',
      decisionCard,
    });
  }

  if (variant === 'meal_recommendation') {
    return {
      variant,
      title: message.title || RECOMMENDATION_COPY.fallbackTitle,
      description: message.description,
      content: message.content,
      decisionCard,
      ...RECOMMENDATION_COPY,
    };
  }

  return {
    variant: 'text',
    content: message?.content ?? '',
    decisionCard,
  };
}
