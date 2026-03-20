import assert from 'node:assert/strict';
import test from 'node:test';

import {
  getInsightsAnalyzeButtonText,
  shouldForceReanalyze,
} from './insightsUiState.ts';

test('button text is "生成 AI 分析" for idle and error states', () => {
  assert.equal(getInsightsAnalyzeButtonText('idle'), '生成 AI 分析');
  assert.equal(getInsightsAnalyzeButtonText('error'), '生成 AI 分析');
});

test('button text is "分析中..." when loading', () => {
  assert.equal(getInsightsAnalyzeButtonText('loading'), '分析中...');
});

test('button text is "重新分析" when success', () => {
  assert.equal(getInsightsAnalyzeButtonText('success'), '重新分析');
});

test('force flag is enabled only for success state', () => {
  assert.equal(shouldForceReanalyze('success'), true);
  assert.equal(shouldForceReanalyze('idle'), false);
  assert.equal(shouldForceReanalyze('loading'), false);
  assert.equal(shouldForceReanalyze('error'), false);
});
