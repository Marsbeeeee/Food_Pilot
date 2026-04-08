import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildDecisionAnalysisAction,
  buildDecisionArchiveEntries,
  buildDecisionWorkspaceSummary,
  getDecisionMatchLevelLabel,
  getDecisionRoleLabel,
  getDecisionScopeLabel,
} from './workspaceDecisionUiState.js';

function createDecisionCard(overrides = {}) {
  return {
    inputSummary: '霸王茶姬 伯牙绝弦 大杯 三分糖',
    normalizedProduct: {
      categoryName: '现制茶饮',
      brandName: '霸王茶姬',
      productName: '伯牙绝弦',
      productScope: 'single_item',
      itemRole: 'single_item',
      matchLevel: 'brand_product',
      sizeOrSpec: '大杯',
      sugarLevel: '三分糖',
      comboItems: [],
      missingFields: [],
    },
    nutritionEstimate: {
      items: [{ name: '奶茶', portion: '1 杯', energy: '310 kcal' }],
      totalCalories: '310 kcal',
    },
    confidenceLevel: 'high',
    recommendationLevel: 'acceptable',
    riskTags: [],
    adaptationNote: '控制糖度更稳妥。',
    adjustments: ['减脂期建议少糖。'],
    alternatives: [],
    isPersonalized: false,
    personalizationNote: null,
    needsClarification: false,
    saveContainerKey: 'chat_message:demo',
    containerType: 'chat_message',
    analysisEligible: true,
    saveEligible: true,
    ...overrides,
  };
}

test('buildDecisionWorkspaceSummary exposes success-state archive and action metadata', () => {
  const summary = buildDecisionWorkspaceSummary(createDecisionCard(), {
    isSaved: false,
    canSaveFromWorkspace: true,
    hasMealDescription: true,
  });

  assert.equal(summary.tone, 'success');
  assert.equal(summary.confidenceLabel, '高置信');
  assert.equal(summary.saveTarget.title, '正式分类容器');
  assert.equal(summary.analysisMeta.title, '保存后可加入分析');
  assert.equal(summary.analysisAction.label, '保存并加入分析');
  assert.equal(summary.analysisAction.disabled, false);
  assert.deepEqual(summary.specBadges, ['大杯', '三分糖']);
});

test('buildDecisionWorkspaceSummary keeps estimable low-confidence results out of clarification tone', () => {
  const summary = buildDecisionWorkspaceSummary(createDecisionCard({
    confidenceLevel: 'low',
    analysisEligible: false,
    saveEligible: true,
    riskTags: ['low_confidence'],
    normalizedProduct: {
      categoryName: '现制茶饮',
      brandName: '',
      productName: '奶茶',
      productScope: 'single_item',
      itemRole: 'single_item',
      matchLevel: 'category_product',
      temperature: '去冰',
      comboItems: [],
      missingFields: [],
    },
  }));

  assert.equal(summary.tone, 'low_confidence');
  assert.equal(summary.confidenceLabel, '低置信');
  assert.equal(summary.saveTarget.title, '正式分类容器');
  assert.equal(summary.analysisMeta.title, '可保存但暂不分析');
});

test('buildDecisionWorkspaceSummary marks clarification cards as blocked for analysis', () => {
  const summary = buildDecisionWorkspaceSummary(createDecisionCard({
    confidenceLevel: 'low',
    needsClarification: true,
    analysisEligible: false,
    saveEligible: false,
    riskTags: ['needs_clarification'],
    normalizedProduct: {
      categoryName: '汉堡',
      brandName: '麦当劳',
      productName: '麦当劳汉堡',
      productScope: 'unknown',
      itemRole: 'unknown',
      matchLevel: 'brand_only',
      comboItems: [],
      missingFields: ['product_name'],
    },
  }));

  assert.equal(summary.tone, 'clarification');
  assert.equal(summary.saveTarget.title, '暂不可保存');
  assert.equal(summary.analysisMeta.title, '暂不可加入分析');
  assert.equal(summary.analysisAction.disabled, true);
});

test('buildDecisionAnalysisAction separates save and analysis eligibility', () => {
  const saveOnlyCard = createDecisionCard({
    analysisEligible: false,
    saveEligible: true,
    normalizedProduct: {
      categoryName: '沙拉',
      brandName: '',
      productName: '鸡胸肉沙拉',
      productScope: 'single_item',
      itemRole: 'single_item',
      matchLevel: 'private_item',
      comboItems: [],
      missingFields: [],
    },
  });

  const action = buildDecisionAnalysisAction(saveOnlyCard, {
    isSaved: false,
    canSaveFromWorkspace: true,
    hasMealDescription: true,
  });

  assert.equal(action.label, '当前不可加入分析');
  assert.equal(action.disabled, true);

  const savedAction = buildDecisionAnalysisAction(createDecisionCard(), {
    isSaved: true,
    canSaveFromWorkspace: true,
    hasMealDescription: true,
  });

  assert.equal(savedAction.label, '加入今日分析');
  assert.equal(savedAction.disabled, false);
});

test('buildDecisionArchiveEntries keeps key catalog tags visible', () => {
  const entries = buildDecisionArchiveEntries(createDecisionCard());
  assert.deepEqual(entries, [
    { label: '品类', value: '现制茶饮' },
    { label: '品牌', value: '霸王茶姬' },
    { label: '商品', value: '伯牙绝弦' },
    { label: '角色', value: '单品' },
    { label: '范围', value: '单品决策' },
    { label: '识别', value: '品牌商品已命中' },
  ]);
});

test('role, scope, and match helpers keep backend enums readable', () => {
  assert.equal(getDecisionRoleLabel('combo_side'), '配餐');
  assert.equal(getDecisionScopeLabel('multi_item'), '套餐 / 多组成项');
  assert.equal(getDecisionMatchLevelLabel('source_ambiguous'), '按来源不明确处理');
});
