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
  assert.equal(presentation.templateVersionLabel, null);
  assert.equal(presentation.configVersionLabel, null);
  assert.deepEqual(presentation.fallbackPathLabels, []);
  assert.deepEqual(presentation.confidenceReasons, []);
  assert.deepEqual(presentation.appliedRules, []);
  assert.deepEqual(presentation.missingConfiguration, []);
  assert.deepEqual(presentation.missingConfigurationLabels, []);
  assert.ok(presentation.ingredientColumnLabel);
  assert.ok(presentation.portionColumnLabel);
  assert.ok(presentation.energyColumnLabel);
  assert.ok(presentation.proteinColumnLabel);
  assert.ok(presentation.carbsColumnLabel);
  assert.ok(presentation.fatColumnLabel);
  assert.ok(presentation.totalLabel);
});

test('buildWorkspaceMessagePresentation keeps low-confidence estimates as estimate cards when clarification is not required', () => {
  const presentation = buildWorkspaceMessagePresentation({
    messageType: 'meal_estimate',
    payload: {
      decisionCard: {
        inputSummary: '奶茶 去冰',
        normalizedProduct: {
          categoryName: '现制茶饮',
          productName: '奶茶',
          normalizedName: '奶茶',
          productScope: 'single_item',
          itemRole: 'single_item',
          missingFields: [],
          matchLevel: 'category_product',
          temperature: '去冰',
        },
        nutritionEstimate: {
          items: [{ name: '奶茶', portion: '1 杯', energy: '260 kcal' }],
          totalCalories: '260 kcal',
        },
        estimationMeta: {
          sourceType: 'generic_template',
          sourceLabel: '通用饮品 / 现制茶饮',
          templateId: 'generic.tea_drink.v1',
          templateVersion: 'v1',
          hitLevel: 'generic',
          fallbackPath: ['brand_template', 'category_template', 'generic_template'],
          confidenceReasons: ['估算依据：通用模板回退。', '关键配置缺失：糖度，已按默认值估算。'],
          appliedRules: ['冰量/温度：去冰（+12 kcal）'],
          missingConfiguration: ['sugar_level'],
          configVersion: 'task8.v2026-04-08',
          configUpdatedAt: '2026-04-08',
        },
        confidenceLevel: 'low',
        recommendationLevel: 'needs_review',
        riskTags: ['low_confidence'],
        adaptationNote: '当前结果可用作低置信参考。',
        adjustments: ['如果能补充糖度，结果会更稳定。'],
        alternatives: [],
        isPersonalized: false,
        personalizationNote: null,
        needsClarification: false,
        saveContainerKey: 'chat_message:demo',
        containerType: 'chat_message',
        analysisEligible: false,
        saveEligible: true,
      },
    },
  });

  assert.equal(presentation.variant, 'meal_estimate');
  assert.equal(presentation.confidence, 'low');
  assert.equal(presentation.needsClarification, false);
  assert.equal(presentation.templateHitLabel, '通用模板回退');
  assert.equal(presentation.templateVersionLabel, '模板版本：v1');
  assert.equal(presentation.configVersionLabel, '规则版本：task8.v2026-04-08');
  assert.deepEqual(presentation.missingConfiguration, ['sugar_level']);
  assert.deepEqual(presentation.missingConfigurationLabels, ['糖度']);
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
          templateVersion: 'v1',
          hitLevel: 'brand',
          fallbackPath: ['brand_template'],
          confidenceReasons: ['估算依据：品牌模板命中。'],
          appliedRules: ['规格：大份（+20 kcal）'],
          missingConfiguration: [],
          configVersion: 'task8.v2026-04-08',
          configUpdatedAt: '2026-04-08',
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
