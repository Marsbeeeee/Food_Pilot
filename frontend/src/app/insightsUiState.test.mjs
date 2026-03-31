import assert from 'node:assert/strict';
import test from 'node:test';

import {
  getInsightsAIPanelDescription,
  getInsightsAnalyzeButtonText,
  getInsightsIdleHint,
  getInsightsLoadingHint,
  getInsightsSnapshotLifecycleHint,
  getInsightsSnapshotNotice,
  getInsightsScopeDescription,
  shouldForceReanalyze,
} from './insightsUiState.ts';

test('day mode button text uses default states', () => {
  assert.equal(getInsightsAnalyzeButtonText('idle', 'day'), '生成 AI 分析');
  assert.equal(getInsightsAnalyzeButtonText('error', 'day'), '生成 AI 分析');
  assert.equal(getInsightsAnalyzeButtonText('loading', 'day'), '分析中...');
  assert.equal(getInsightsAnalyzeButtonText('success', 'day'), '重新分析');
});

test('week mode button text emphasizes trend analysis states', () => {
  assert.equal(getInsightsAnalyzeButtonText('idle', 'week'), '生成周趋势分析');
  assert.equal(getInsightsAnalyzeButtonText('error', 'week'), '生成周趋势分析');
  assert.equal(getInsightsAnalyzeButtonText('loading', 'week'), '分析周趋势中...');
  assert.equal(getInsightsAnalyzeButtonText('success', 'week'), '重新分析周趋势');
});

test('mode descriptions are distinct between day and week', () => {
  assert.equal(getInsightsScopeDescription('day'), '聚焦单日摄入、目标差距和当日调整。');
  assert.equal(getInsightsScopeDescription('week'), '聚焦一周趋势、波动和工作日 / 周末节律。');

  assert.equal(getInsightsAIPanelDescription('day'), '基于当日已选菜品，生成营养摄入分析与改善建议。');
  assert.equal(getInsightsAIPanelDescription('week'), '基于本周已选菜品，生成趋势解读、波动提示与改善建议。');
});

test('idle and loading hints change with mode and selected items', () => {
  assert.equal(getInsightsIdleHint('day', false), '添加饮食记录后，即可生成 AI 营养摄入分析。');
  assert.equal(getInsightsIdleHint('day', true), '点击下方按钮开始生成 AI 分析。');
  assert.equal(getInsightsIdleHint('week', false), '添加饮食记录后，即可生成本周趋势分析。');
  assert.equal(getInsightsIdleHint('week', true), '点击下方按钮开始生成本周趋势分析。');

  assert.equal(getInsightsLoadingHint('day'), '正在分析中，请稍候...');
  assert.equal(getInsightsLoadingHint('week'), '正在分析本周趋势，请稍候...');
});

test('force flag is enabled only for success state', () => {
  assert.equal(shouldForceReanalyze('success'), true);
  assert.equal(shouldForceReanalyze('idle'), false);
  assert.equal(shouldForceReanalyze('loading'), false);
  assert.equal(shouldForceReanalyze('error'), false);
});

test('snapshot lifecycle hint clarifies split live-data and snapshot flow', () => {
  assert.equal(
    getInsightsSnapshotLifecycleHint('day'),
    '左侧数据会随当前已选菜品立即更新；右侧 AI 建议仍优先展示该日期最近一次分析快照。菜品变化后，如需刷新建议，请点击“重新分析”。',
  );
  assert.equal(
    getInsightsSnapshotLifecycleHint('week'),
    '左侧周数据会随当前已选菜品立即更新；右侧 AI 周趋势仍优先展示最近一次分析快照。菜品变化后，如需刷新建议，请点击“重新分析周趋势”。',
  );
});

test('snapshot notice escalates when history result is shown or selection mismatches', () => {
  assert.deepEqual(
    getInsightsSnapshotNotice('day', true, false),
    {
      level: 'warning',
      title: 'AI 结果可能已过期',
      detail: '左侧数据已按当前已选菜品更新，右侧仍是历史分析快照。请重新分析以刷新 AI 建议。',
    },
  );
  assert.deepEqual(
    getInsightsSnapshotNotice('week', false, true),
    {
      level: 'warning',
      title: 'AI 结果可能已过期',
      detail: '左侧周数据已按当前已选菜品更新，右侧仍是历史周趋势快照。请重新分析周趋势以刷新 AI 建议。',
    },
  );
  assert.deepEqual(
    getInsightsSnapshotNotice('day', false, false),
    {
      level: 'info',
      title: 'AI 结果为快照',
      detail: '左侧数据会实时变化，右侧 AI 建议不会自动更新。修改菜品后，请重新分析。',
    },
  );
});
