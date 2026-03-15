const ESTIMATE_COPY = {
  ingredientColumnLabel: '食材',
  portionColumnLabel: '份量',
  energyColumnLabel: '估算热量',
  totalLabel: '估算总热量',
};

const RECOMMENDATION_COPY = {
  eyebrow: '饮食推荐',
  fallbackTitle: '推荐建议',
  badgeLabel: '建议',
  reasonLabel: '为什么这样选',
  contentLabel: '推荐怎么吃',
};

export function buildWorkspaceMessagePresentation(message) {
  const variant = message?.messageType ?? 'text';

  if (variant === 'meal_estimate') {
    return {
      variant,
      title: message.title,
      confidence: message.confidence,
      description: message.description,
      items: message.items ?? [],
      total: message.total,
      ...ESTIMATE_COPY,
    };
  }

  if (variant === 'meal_recommendation') {
    return {
      variant,
      title: message.title || RECOMMENDATION_COPY.fallbackTitle,
      description: message.description,
      content: message.content,
      ...RECOMMENDATION_COPY,
    };
  }

  return {
    variant: 'text',
    content: message?.content ?? '',
  };
}
