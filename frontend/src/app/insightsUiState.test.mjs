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
  assert.equal(getInsightsAnalyzeButtonText('loading', 'week'), '周趋势分析中...');
  assert.equal(getInsightsAnalyzeButtonText('success', 'week'), '重新分析周趋势');
});

test('mode descriptions are distinct between day and week', () => {
  assert.equal(getInsightsScopeDescription('day'), '聚焦单日摄入、目标差距和当日调整。');
  assert.equal(getInsightsScopeDescription('week'), '聚焦一周趋势、波动和工作日/周末节律。');

  assert.equal(getInsightsAIPanelDescription('day'), '基于当日已选菜品，生成营养摄入分析与改善建议。');
  assert.equal(getInsightsAIPanelDescription('week'), '基于本周已选菜品，生成趋势解读、波动提示与改善建议。');
});

test('idle and loading hints change with mode and selected items', () => {
  assert.equal(getInsightsIdleHint('day', false), '添加饮食记录后，即可生成 AI 营养摄入分析。');
  assert.equal(getInsightsIdleHint('day', true), '点击下方按钮开始生成 AI 分析。');
  assert.equal(getInsightsIdleHint('week', false), '添加饮食记录后，即可生成本周趋势分析。');
  assert.equal(getInsightsIdleHint('week', true), '点击下方按钮开始生成本周趋势分析。');

  assert.equal(getInsightsLoadingHint('day'), '正在分析中，请稍候…');
  assert.equal(getInsightsLoadingHint('week'), '正在分析本周趋势，请稍候…');
});

test('force flag is enabled only for success state', () => {
  assert.equal(shouldForceReanalyze('success'), true);
  assert.equal(shouldForceReanalyze('idle'), false);
  assert.equal(shouldForceReanalyze('loading'), false);
  assert.equal(shouldForceReanalyze('error'), false);
});

test('snapshot lifecycle hint clarifies history-first and reanalyze flow', () => {
  assert.equal(
    getInsightsSnapshotLifecycleHint('day'),
    '页面会优先展示该日期最近一次分析快照。Food Log 变化后不会自动同步，请点击“重新分析”获取最新结果。',
  );
  assert.equal(
    getInsightsSnapshotLifecycleHint('week'),
    '页面会优先展示本周最近一次分析快照。Food Log 变化后不会自动同步，请点击“重新分析周趋势”获取最新结果。',
  );
});

test('snapshot notice escalates when history result is shown or selection mismatches', () => {
  assert.deepEqual(
    getInsightsSnapshotNotice('day', true, false),
    {
      level: 'warning',
      title: '数据可能已变化',
      detail: '当前显示的是历史分析快照，Food Log 可能已变化，请重新分析。',
    },
  );
  assert.deepEqual(
    getInsightsSnapshotNotice('week', false, true),
    {
      level: 'warning',
      title: '数据可能已变化',
      detail: '当前显示的是历史周趋势快照，Food Log 可能已变化，请重新分析周趋势。',
    },
  );
  assert.deepEqual(
    getInsightsSnapshotNotice('day', false, false),
    {
      level: 'info',
      title: '当前结果为快照',
      detail: '结果不会随 Food Log 自动更新。修改记录后，请重新分析。',
    },
  );
});
