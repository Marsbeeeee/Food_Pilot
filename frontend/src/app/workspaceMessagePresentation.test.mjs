import assert from 'node:assert/strict';
import test from 'node:test';

import { buildWorkspaceMessagePresentation } from './workspaceMessagePresentation.js';

test('buildWorkspaceMessagePresentation returns estimate card copy for Chinese nutrition results', () => {
  const presentation = buildWorkspaceMessagePresentation({
    messageType: 'meal_estimate',
    title: '鸡胸肉牛油果沙拉',
    confidence: 'high',
    description: '蛋白质充足，脂肪主要来自牛油果。',
    items: [
      { name: '鸡胸肉', portion: '150g', energy: '240 kcal' },
      { name: '牛油果', portion: '1/2 个', energy: '180 kcal' },
    ],
    total: '420 kcal',
  });

  assert.deepEqual(presentation, {
    variant: 'meal_estimate',
    title: '鸡胸肉牛油果沙拉',
    confidence: 'high',
    description: '蛋白质充足，脂肪主要来自牛油果。',
    items: [
      { name: '鸡胸肉', portion: '150g', energy: '240 kcal' },
      { name: '牛油果', portion: '1/2 个', energy: '180 kcal' },
    ],
    total: '420 kcal',
    ingredientColumnLabel: '食材',
    portionColumnLabel: '份量',
    energyColumnLabel: '估算热量',
    totalLabel: '估算总热量',
  });
});

test('buildWorkspaceMessagePresentation returns recommendation card copy and fallback title', () => {
  const presentation = buildWorkspaceMessagePresentation({
    messageType: 'meal_recommendation',
    content: '今晚优先选鸡肉沙拉，再配一份南瓜汤，会比炸鸡饭更稳妥。',
    description: '保留饱腹感，同时减少油脂和精制碳水。',
  });

  assert.deepEqual(presentation, {
    variant: 'meal_recommendation',
    title: '推荐建议',
    description: '保留饱腹感，同时减少油脂和精制碳水。',
    content: '今晚优先选鸡肉沙拉，再配一份南瓜汤，会比炸鸡饭更稳妥。',
    eyebrow: '饮食推荐',
    fallbackTitle: '推荐建议',
    badgeLabel: '建议',
    reasonLabel: '为什么这样选',
    contentLabel: '推荐怎么吃',
  });
});

test('buildWorkspaceMessagePresentation keeps text messages as plain bubbles', () => {
  const presentation = buildWorkspaceMessagePresentation({
    messageType: 'text',
    content: '更推荐烤鸡，是因为同等分量下通常更容易控制油脂和总热量。',
  });

  assert.deepEqual(presentation, {
    variant: 'text',
    content: '更推荐烤鸡，是因为同等分量下通常更容易控制油脂和总热量。',
  });
});
