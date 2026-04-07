import assert from 'node:assert/strict';
import test from 'node:test';

import { buildWorkspaceMessagePresentation } from './workspaceMessagePresentation.js';

test('buildWorkspaceMessagePresentation returns estimate card shape with extended fields', () => {
  const presentation = buildWorkspaceMessagePresentation({
    messageType: 'meal_estimate',
    title: 'Chicken Avocado Salad',
    confidence: 'high',
    description: 'Protein-forward meal.',
    items: [
      { name: 'Chicken', portion: '150g', energy: '240 kcal' },
      { name: 'Avocado', portion: '1/2', energy: '180 kcal' },
    ],
    total: '420 kcal',
  });

  assert.equal(presentation.variant, 'meal_estimate');
  assert.equal(presentation.title, 'Chicken Avocado Salad');
  assert.equal(presentation.confidence, 'high');
  assert.equal(presentation.total, '420 kcal');
  assert.equal(presentation.items.length, 2);
  assert.equal(presentation.estimates, null);
  assert.equal(presentation.suggestion, null);
  assert.deepEqual(presentation.summaryBadges, []);
  assert.equal(presentation.templateHitLabel, null);
  assert.equal(presentation.templateSourceLabel, null);
  assert.deepEqual(presentation.fallbackPathLabels, []);
  assert.deepEqual(presentation.confidenceReasons, []);
  assert.deepEqual(presentation.appliedRules, []);
  assert.ok(presentation.ingredientColumnLabel);
  assert.ok(presentation.portionColumnLabel);
  assert.ok(presentation.energyColumnLabel);
  assert.ok(presentation.proteinColumnLabel);
  assert.ok(presentation.carbsColumnLabel);
  assert.ok(presentation.fatColumnLabel);
  assert.ok(presentation.totalLabel);
});

test('buildWorkspaceMessagePresentation returns recommendation card and fallback title', () => {
  const presentation = buildWorkspaceMessagePresentation({
    messageType: 'meal_recommendation',
    content: 'Choose grilled chicken salad with pumpkin soup.',
    description: 'Lower fat while keeping satiety.',
  });

  assert.equal(presentation.variant, 'meal_recommendation');
  assert.equal(presentation.content, 'Choose grilled chicken salad with pumpkin soup.');
  assert.equal(presentation.description, 'Lower fat while keeping satiety.');
  assert.ok(presentation.title);
  assert.ok(presentation.eyebrow);
  assert.ok(presentation.badgeLabel);
  assert.ok(presentation.reasonLabel);
  assert.ok(presentation.contentLabel);
});

test('buildWorkspaceMessagePresentation keeps text messages as plain bubbles', () => {
  const presentation = buildWorkspaceMessagePresentation({
    messageType: 'text',
    content: 'Grilling usually uses less oil than deep frying.',
  });

  assert.deepEqual(presentation, {
    variant: 'text',
    content: 'Grilling usually uses less oil than deep frying.',
    decisionCard: null,
  });
});

test('buildWorkspaceMessagePresentation can render estimate from decision card only', () => {
  const presentation = buildWorkspaceMessagePresentation({
    messageType: 'meal_estimate',
    payload: {
      decisionCard: {
        inputSummary: '鸡胸肉沙拉',
        normalizedProduct: {
          brandName: '麦当劳',
          productName: '鸡胸肉沙拉',
          normalizedName: '鸡胸肉沙拉',
          productScope: 'single_item',
          itemRole: 'single_item',
          missingFields: ['product_name'],
          matchLevel: 'brand_only',
        },
        nutritionEstimate: {
          items: [{ name: '鸡胸肉', portion: '150 g', energy: '240 kcal' }],
          totalCalories: '240 kcal',
        },
        estimationMeta: {
          sourceType: 'brand_template',
          sourceLabel: '麦当劳 / 鸡胸肉沙拉',
          templateId: 'brand.mcdonalds.chicken_salad.v1',
          hitLevel: 'brand',
          fallbackPath: ['brand_template'],
          confidenceReasons: ['估算依据：品牌模板命中。'],
          appliedRules: ['规格：大份（+20 kcal）'],
          missingConfiguration: [],
        },
        confidenceLevel: 'low',
        recommendationLevel: 'needs_review',
        riskTags: ['needs_clarification'],
        adaptationNote: '信息不足',
        adjustments: ['补充份量信息'],
        alternatives: [],
        isPersonalized: false,
        personalizationNote: '商品信息不足，暂未进入稳定的个体化判断。',
        needsClarification: true,
        saveContainerKey: 'chat_message:demo',
        containerType: 'chat_message',
        analysisEligible: false,
        saveEligible: false,
      },
    },
  });

  assert.equal(presentation.variant, 'clarification');
  assert.equal(presentation.title, '鸡胸肉沙拉');
  assert.equal(presentation.inputSummary, '鸡胸肉沙拉');
  assert.equal(presentation.confidence, 'low');
  assert.equal(presentation.needsClarification, true);
  assert.equal(presentation.analysisEligible, false);
  assert.equal(presentation.saveEligible, false);
  assert.deepEqual(presentation.summaryBadges, ['麦当劳']);
  assert.deepEqual(presentation.missingFields, ['具体商品名']);
  assert.equal(presentation.matchLevelLabel, '仅识别到品牌');
  assert.deepEqual(presentation.riskTags, ['needs_clarification']);
  assert.deepEqual(presentation.adjustments, ['补充份量信息']);
});
