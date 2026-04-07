import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildEstimateMessageFromResult,
  buildEstimateResultPresentation,
} from './estimateResultMessage.js';
import { buildWorkspaceMessagePresentation } from './workspaceMessagePresentation.js';

test('direct /estimate results reuse the same presentation contract as workspace estimate messages', () => {
  const result = {
    title: 'Chicken Avocado Bowl',
    confidence: 'high',
    description: 'High protein with moderate fat.',
    items: [
      { name: 'Chicken', portion: '150g', energy: '240 kcal' },
      { name: 'Avocado', portion: '1/2', energy: '180 kcal' },
    ],
    total_calories: '420 kcal',
    suggestion: 'Use less sauce to reduce calories.',
    decisionCard: {
      inputSummary: 'grilled chicken and avocado',
      normalizedProduct: {
        categoryName: 'salad_bowl',
        productName: 'Chicken Avocado Bowl',
        productScope: 'single_item',
        itemRole: 'single_item',
        matchLevel: 'category_product',
        missingFields: [],
      },
      nutritionEstimate: {
        items: [
          { name: 'Chicken', portion: '150g', energy: '240 kcal' },
          { name: 'Avocado', portion: '1/2', energy: '180 kcal' },
        ],
        totalCalories: '420 kcal',
      },
      estimationMeta: {
        sourceType: 'category_template',
        sourceLabel: '轻食 / 鸡肉沙拉',
        templateId: 'category.light_meal.chicken_salad.v1',
        hitLevel: 'category',
        fallbackPath: ['brand_template', 'category_template'],
        confidenceReasons: ['估算依据：品类模板回退。'],
        appliedRules: ['规格：大份（+20 kcal）'],
        missingConfiguration: [],
      },
      confidenceLevel: 'high',
      recommendationLevel: 'recommended',
      riskTags: [],
      adaptationNote: 'High protein with moderate fat.',
      adjustments: ['Use less sauce to reduce calories.'],
      alternatives: [],
      isPersonalized: true,
      personalizationNote: '已结合你的 High protein、2200 kcal 目标 做判断。',
      needsClarification: false,
      saveContainerKey: 'estimate_api:demo',
      containerType: 'estimate_api',
      analysisEligible: true,
      saveEligible: true,
    },
  };

  const directPresentation = buildEstimateResultPresentation(result);
  const workspacePresentation = buildWorkspaceMessagePresentation(
    buildEstimateMessageFromResult(result),
  );

  assert.deepEqual(directPresentation, workspacePresentation);
  assert.equal(directPresentation.variant, 'meal_estimate');
  assert.equal(directPresentation.title, 'Chicken Avocado Bowl');
  assert.equal(directPresentation.analysisEligible, true);
  assert.equal(directPresentation.saveEligible, true);
  assert.equal(directPresentation.templateHitLabel, '品类模板回退');
  assert.equal(directPresentation.templateSourceLabel, '轻食 / 鸡肉沙拉');
  assert.deepEqual(directPresentation.fallbackPathLabels, ['品牌模板命中', '品类模板回退']);
  assert.deepEqual(directPresentation.appliedRules, ['规格：大份（+20 kcal）']);
  assert.deepEqual(directPresentation.summaryBadges, ['salad_bowl']);
  assert.equal(directPresentation.recommendationLabel, '更适合点');
  assert.equal(directPresentation.isPersonalized, true);
});

test('direct /estimate clarification results render the shared clarification state', () => {
  const result = {
    title: '麦当劳汉堡',
    confidence: 'low',
    description: '信息不足',
    items: [],
    total_calories: '未知',
    suggestion: '',
    decisionCard: {
      inputSummary: '麦当劳汉堡',
      normalizedProduct: {
        brandName: '麦当劳',
        productName: '麦当劳汉堡',
        productScope: 'unknown',
        itemRole: 'unknown',
        missingFields: ['product_name'],
        matchLevel: 'brand_only',
      },
      nutritionEstimate: {
        items: [],
        totalCalories: '未知',
      },
      confidenceLevel: 'low',
      recommendationLevel: 'needs_review',
      riskTags: ['needs_clarification'],
      adaptationNote: '请补充具体商品名或规格。',
      adjustments: ['补充品牌下的具体商品名'],
      alternatives: [],
      isPersonalized: false,
      personalizationNote: '商品信息不足，暂未进入稳定的个体化判断。',
      needsClarification: true,
      saveContainerKey: 'estimate_api:clarify',
      containerType: 'estimate_api',
      analysisEligible: false,
      saveEligible: false,
    },
  };

  const presentation = buildEstimateResultPresentation(result, {
    content: '请补充具体商品名或规格。',
  });

  assert.equal(presentation.variant, 'clarification');
  assert.equal(presentation.title, '麦当劳汉堡');
  assert.equal(presentation.needsClarification, true);
  assert.equal(presentation.analysisEligible, false);
  assert.equal(presentation.saveEligible, false);
  assert.deepEqual(presentation.missingFields, ['具体商品名']);
  assert.equal(presentation.matchLevelLabel, '仅识别到品牌');
  assert.deepEqual(presentation.adjustments, ['补充品牌下的具体商品名']);
});
