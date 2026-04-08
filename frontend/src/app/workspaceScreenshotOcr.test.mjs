import test from 'node:test';
import assert from 'node:assert/strict';

import {
  resolveWorkspaceScreenshotConfirmationText,
  validateWorkspaceScreenshotFile,
  WORKSPACE_SCREENSHOT_OCR_MAX_BYTES,
} from './workspaceScreenshotOcr.js';

test('validateWorkspaceScreenshotFile blocks missing, unsupported, and oversized files', () => {
  assert.equal(validateWorkspaceScreenshotFile(null), '请先选择一张截图。');
  assert.equal(
    validateWorkspaceScreenshotFile({ type: 'image/gif', size: 100 }),
    '当前仅支持 PNG、JPEG 和 WebP 截图。',
  );
  assert.equal(
    validateWorkspaceScreenshotFile({ type: 'image/png', size: WORKSPACE_SCREENSHOT_OCR_MAX_BYTES + 1 }),
    '截图不能超过 5MB，请压缩后重试。',
  );
  assert.equal(validateWorkspaceScreenshotFile({ type: 'image/png', size: 1024 }), '');
});

test('resolveWorkspaceScreenshotConfirmationText prefers normalized input then primary text', () => {
  assert.equal(
    resolveWorkspaceScreenshotConfirmationText({
      normalizedInput: ' 霸王茶姬   伯牙绝弦  ',
      primaryText: 'ignored',
      candidateTitles: ['候选商品'],
    }),
    '霸王茶姬 伯牙绝弦',
  );
  assert.equal(
    resolveWorkspaceScreenshotConfirmationText({
      primaryText: ' 瑞幸 生椰拿铁 ',
      candidateTitles: ['候选商品'],
    }),
    '瑞幸 生椰拿铁',
  );
  assert.equal(
    resolveWorkspaceScreenshotConfirmationText({
      candidateTitles: [' 书亦 烧仙草  '],
    }),
    '书亦 烧仙草',
  );
});
